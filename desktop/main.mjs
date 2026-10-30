import { app, BrowserWindow, dialog, ipcMain, Menu, shell } from 'electron';
import { spawn } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs';
import { dirname, isAbsolute, join, normalize, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { startWorkbenchServer } from './local-server.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const developmentRoot = resolve(__dirname, '..');
const resourceRoot = app.isPackaged ? process.resourcesPath : developmentRoot;
const frontendRoot = app.isPackaged
  ? join(resourceRoot, 'web')
  : join(resourceRoot, 'astro-blog', 'dist', 'client');
const backendRoot = app.isPackaged
  ? join(resourceRoot, 'backend')
  : join(resourceRoot, 'python-backend');
const backendPort = Number(process.env.WORKBENCH_BACKEND_PORT || 1236);
const sitePort = Number(process.env.WORKBENCH_SITE_PORT || 4410);
const settingsPath = () => join(app.getPath('userData'), 'desktop-settings.json');

let mainWindow = null;
let localServer = null;
let backendProcess = null;
let workspaceRoot = '';
let isQuitting = false;

function readSettings() {
  try {
    return JSON.parse(readFileSync(settingsPath(), 'utf8'));
  } catch {
    return {};
  }
}

function writeSettings(next) {
  mkdirSync(dirname(settingsPath()), { recursive: true });
  writeFileSync(settingsPath(), JSON.stringify(next, null, 2), 'utf8');
}

function ensureWorkspace() {
  const saved = readSettings().workspace;
  workspaceRoot = saved || join(app.getPath('documents'), 'Ray Workbench');
  mkdirSync(workspaceRoot, { recursive: true });
  const settings = readSettings();
  if (settings.workspace !== workspaceRoot) writeSettings({ ...settings, workspace: workspaceRoot });
}

function safeWorkspacePath(relativePath = '') {
  const candidate = resolve(workspaceRoot, normalize(relativePath));
  if (candidate !== resolve(workspaceRoot) && !candidate.startsWith(resolve(workspaceRoot) + sep)) {
    throw new Error('路径超出当前工作区');
  }
  return candidate;
}

function listDirectory(relativePath = '') {
  const target = safeWorkspacePath(relativePath);
  return readdirSync(target, { withFileTypes: true })
    .filter(entry => !entry.name.startsWith('.'))
    .map(entry => {
      const fullPath = join(target, entry.name);
      return {
        name: entry.name,
        path: relative(workspaceRoot, fullPath).split(sep).join('/'),
        directory: entry.isDirectory(),
        size: entry.isFile() ? statSync(fullPath).size : 0,
      };
    })
    .sort((a, b) => Number(b.directory) - Number(a.directory) || a.name.localeCompare(b.name));
}

async function waitForBackend(timeoutMs = 25000) {
  const startedAt = Date.now();
  while (Date.now() - startedAt < timeoutMs) {
    try {
      const response = await fetch(`http://127.0.0.1:${backendPort}/api/health`);
      if (response.ok) return true;
    } catch {
      // Backend is still starting.
    }
    await new Promise(resolveWait => setTimeout(resolveWait, 400));
  }
  return false;
}

async function ensureBackend() {
  if (await waitForBackend(1200)) return;

  const python = process.env.WORKBENCH_PYTHON || 'python';
  backendProcess = spawn(python, [
    '-m', 'uvicorn', 'main:app',
    '--host', '127.0.0.1',
    '--port', String(backendPort),
  ], {
    cwd: backendRoot,
    env: { ...process.env, PYTHONUNBUFFERED: '1' },
    windowsHide: true,
    stdio: ['ignore', 'pipe', 'pipe'],
  });

  backendProcess.stdout?.on('data', data => process.stdout.write(`[gateway] ${data}`));
  backendProcess.stderr?.on('data', data => process.stderr.write(`[gateway] ${data}`));
  backendProcess.on('exit', code => {
    if (code !== 0 && !isQuitting) console.error(`Agent Gateway exited with code ${code}`);
  });

  if (!(await waitForBackend())) {
    throw new Error(`Agent Gateway 未能在端口 ${backendPort} 启动`);
  }
}

function createMenu() {
  Menu.setApplicationMenu(Menu.buildFromTemplate([
    {
      label: '工作台',
      submenu: [
        {
          label: '选择工作区…',
          accelerator: 'CmdOrCtrl+Shift+O',
          click: () => chooseWorkspace(),
        },
        { label: '打开工作区', click: () => shell.openPath(workspaceRoot) },
        { type: 'separator' },
        { role: 'reload', label: '重新载入' },
        { role: 'toggleDevTools', label: '开发者工具' },
        { type: 'separator' },
        { role: 'quit', label: '退出' },
      ],
    },
    {
      label: '编辑',
      submenu: [
        { role: 'undo', label: '撤销' },
        { role: 'redo', label: '重做' },
        { type: 'separator' },
        { role: 'cut', label: '剪切' },
        { role: 'copy', label: '复制' },
        { role: 'paste', label: '粘贴' },
        { role: 'selectAll', label: '全选' },
      ],
    },
    {
      label: '视图',
      submenu: [
        { role: 'resetZoom', label: '实际大小' },
        { role: 'zoomIn', label: '放大' },
        { role: 'zoomOut', label: '缩小' },
        { type: 'separator' },
        { role: 'togglefullscreen', label: '全屏' },
      ],
    },
  ]));
}

async function chooseWorkspace() {
  const result = await dialog.showOpenDialog(mainWindow, {
    title: '选择内容工作区',
    defaultPath: workspaceRoot,
    properties: ['openDirectory', 'createDirectory'],
  });
  if (result.canceled || result.filePaths.length === 0) return null;
  workspaceRoot = result.filePaths[0];
  writeSettings({ ...readSettings(), workspace: workspaceRoot });
  mainWindow?.webContents.send('workspace:changed', workspaceRoot);
  return workspaceRoot;
}

async function createWindow() {
  await ensureBackend();
  localServer = await startWorkbenchServer({
    root: frontendRoot,
    backendPort,
    port: sitePort,
  });

  mainWindow = new BrowserWindow({
    width: 1480,
    height: 960,
    minWidth: 1040,
    minHeight: 700,
    show: false,
    backgroundColor: '#f4f6fb',
    title: 'Ray 内容工作台',
    webPreferences: {
      preload: join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:\/\//i.test(url)) shell.openExternal(url);
    return { action: 'deny' };
  });
  // Migrate away from the old whole-page zoom setting used by early builds.
  mainWindow.webContents.setZoomFactor(1);
  mainWindow.webContents.on('will-navigate', (event, url) => {
    if (!url.startsWith(localServer.url)) event.preventDefault();
  });
  mainWindow.webContents.on('console-message', (_event, level, message, line, sourceId) => {
    if (process.env.WORKBENCH_QA_SCREENSHOT) {
      console.log(`[renderer:${level}] ${message} (${sourceId}:${line})`);
    }
  });
  mainWindow.webContents.on('did-fail-load', (_event, code, description, url) => {
    console.error(`[renderer] load failed ${code} ${description}: ${url}`);
  });
  mainWindow.webContents.on('render-process-gone', (_event, details) => {
    console.error(`[renderer] process gone: ${JSON.stringify(details)}`);
  });
  mainWindow.once('ready-to-show', () => mainWindow.show());
  await mainWindow.loadURL(`${localServer.url}/workbench`);
  mainWindow.webContents.setZoomFactor(1);
  await captureQaScreenshot();
}

async function captureQaScreenshot() {
  const target = process.env.WORKBENCH_QA_SCREENSHOT;
  if (app.isPackaged || !target || !mainWindow) return;
  mainWindow.show();
  mainWindow.focus();
  const qaWidth = Number(process.env.WORKBENCH_QA_WIDTH || 0);
  const qaHeight = Number(process.env.WORKBENCH_QA_HEIGHT || 0);
  if (qaWidth > 0 && qaHeight > 0) mainWindow.setContentSize(qaWidth, qaHeight);
  if (process.env.WORKBENCH_QA_MAXIMIZE === '1') mainWindow.maximize();
  await new Promise(resolveWait => setTimeout(resolveWait, 2500));
  if (process.env.WORKBENCH_QA_OPEN_BLOG === '1') {
    await mainWindow.webContents.executeJavaScript(
      "document.querySelector('.blog-button')?.click()",
      true,
    );
    await new Promise(resolveWait => setTimeout(resolveWait, 1200));
  }
  const qaSection = process.env.WORKBENCH_QA_SECTION;
  if (qaSection) {
    await mainWindow.webContents.executeJavaScript(`(() => {
      const item = [...document.querySelectorAll('.nav-item')]
        .find(element => element.textContent.trim().startsWith(${JSON.stringify(qaSection)}));
      if (!item) return false;
      item.click();
      return true;
    })()`, true);
    await new Promise(resolveWait => setTimeout(resolveWait, 1800));
  }
  if (process.env.WORKBENCH_QA_COLLAPSE_CONTEXT === '1') {
    await mainWindow.webContents.executeJavaScript(
      "document.querySelector('.context-fold-button')?.click()",
      true,
    );
    await new Promise(resolveWait => setTimeout(resolveWait, 500));
  }
  if (process.env.WORKBENCH_QA_OPEN_FIRST_CAPABILITY === '1') {
    await mainWindow.webContents.executeJavaScript(
      "document.querySelector('.capability-card-actions button')?.click()",
      true,
    );
    await new Promise(resolveWait => setTimeout(resolveWait, 500));
  }
  if (process.env.WORKBENCH_QA_OPEN_CAPABILITY_IMPORT === '1') {
    await mainWindow.webContents.executeJavaScript(
      "document.querySelector('.capability-import-button')?.click()",
      true,
    );
    await new Promise(resolveWait => setTimeout(resolveWait, 300));
  }
  if (process.env.WORKBENCH_QA_TOGGLE_FIRST_CAPABILITY === '1') {
    await mainWindow.webContents.executeJavaScript(
      "document.querySelector('.capability-switch input')?.click()",
      true,
    );
    await new Promise(resolveWait => setTimeout(resolveWait, 800));
  }
  const qaFontStep = Number(process.env.WORKBENCH_QA_FONT_STEP || 0);
  const qaFontLabel = qaFontStep >= 0 ? '放大字体' : '缩小字体';
  for (let step = 0; step < Math.abs(qaFontStep); step += 1) {
    await mainWindow.webContents.executeJavaScript(
      `document.querySelector('[aria-label="${qaFontLabel}"]')?.click()`,
      true,
    );
    await new Promise(resolveWait => setTimeout(resolveWait, 250));
  }
  if (process.env.WORKBENCH_QA_OPEN_FIRST_ARTICLE === '1') {
    await mainWindow.webContents.executeJavaScript(
      "document.querySelector('.article-stream-open')?.click()",
      true,
    );
    await new Promise(resolveWait => setTimeout(resolveWait, 2500));
  }
  const qaRecentTaskIndex = Number(process.env.WORKBENCH_QA_RECENT_TASK_INDEX ?? -1);
  if (qaRecentTaskIndex >= 0) {
    await mainWindow.webContents.executeJavaScript(`(() => {
      const tasks = document.querySelectorAll('.recent-task');
      tasks[${qaRecentTaskIndex}]?.click();
      return tasks.length;
    })()`, true);
    await new Promise(resolveWait => setTimeout(resolveWait, 2500));
  }
  if (process.env.WORKBENCH_QA_SCROLL_TASK_TOP === '1') {
    await mainWindow.webContents.executeJavaScript(
      "(() => { const feed = document.querySelector('.task-feed'); if (feed) feed.scrollTop = 0; return !!feed; })()",
      true,
    );
    await new Promise(resolveWait => setTimeout(resolveWait, 500));
  }
  const qaArticleId = process.env.WORKBENCH_QA_ARTICLE_ID;
  if (qaArticleId) {
    const articleUrl = `${localServer.url}/blog/${encodeURIComponent(qaArticleId)}`;
    await mainWindow.webContents.executeJavaScript(`(() => {
      const frame = document.querySelector('.blog-frame');
      if (!frame) return false;
      frame.src = ${JSON.stringify(articleUrl)};
      return true;
    })()`, true);
    await new Promise(resolveWait => setTimeout(resolveWait, 2500));
  }
  const pageState = await mainWindow.webContents.executeJavaScript(`({
    title: document.title,
    text: document.body.innerText.slice(0, 300),
    workbench: !!document.querySelector('.workbench'),
    bodyStyle: (() => {
      const s = getComputedStyle(document.body);
      return { display: s.display, visibility: s.visibility, opacity: s.opacity, inline: document.body.getAttribute('style') };
    })(),
    bodyStart: document.body.outerHTML.slice(0, 1200),
    bodyDisplayRules: (() => {
      const matches = [];
      const visit = rules => {
        for (const rule of rules || []) {
          if (rule.cssRules) visit(rule.cssRules);
          if (rule.selectorText && rule.style?.display === 'none') {
            try { if (document.body.matches(rule.selectorText)) matches.push(rule.selectorText); } catch {}
          }
        }
      };
      for (const sheet of document.styleSheets) {
        try { visit(sheet.cssRules); } catch {}
      }
      return matches;
    })(),
    workbenchText: document.querySelector('.workbench')?.innerText.slice(0, 300) || '',
    workbenchRect: (() => {
      const el = document.querySelector('.workbench');
      if (!el) return null;
      const r = el.getBoundingClientRect();
      const s = getComputedStyle(el);
      return { x: r.x, y: r.y, width: r.width, height: r.height, display: s.display, opacity: s.opacity, visibility: s.visibility };
    })(),
    layoutRect: (() => {
      const el = document.querySelector('.workbench-layout');
      if (!el) return null;
      const r = el.getBoundingClientRect();
      return { width: r.width, height: r.height };
    })(),
    quickColumns: (() => {
      const quickGrid = document.querySelector('.quick-grid');
      return quickGrid ? getComputedStyle(quickGrid).gridTemplateColumns : '';
    })(),
    ancestors: (() => {
      let el = document.querySelector('.workbench');
      const out = [];
      while (el && out.length < 6) {
        const r = el.getBoundingClientRect();
        const s = getComputedStyle(el);
        out.push({ tag: el.tagName, cls: el.className, width: r.width, height: r.height, display: s.display, position: s.position });
        el = el.parentElement;
      }
      return out;
    })(),
    blog: !!document.querySelector('.blog-window'),
    blogTitle: document.querySelector('.blog-frame')?.contentDocument?.title || '',
    blogPath: document.querySelector('.blog-frame')?.contentWindow?.location?.pathname || '',
    blogArticleHeading:
      document.querySelector('.blog-frame')?.contentDocument?.querySelector('.article-hero h1')?.textContent?.trim() || '',
    blogNotFound:
      (document.querySelector('.blog-frame')?.contentDocument?.body?.innerText || '').includes('文章不存在'),
    activeSection: document.querySelector('.nav-item.active')?.textContent?.trim() || '',
    assetCards: document.querySelectorAll('.asset-card').length,
    capabilityCards: document.querySelectorAll('.capability-card').length,
    capabilityDetailOpen: !!document.querySelector('.capability-detail-panel'),
    capabilityImportOpen: !!document.querySelector('.capability-import-panel'),
    capabilityEnabled: [...document.querySelectorAll('.capability-switch input')].slice(0, 4).map(input => input.checked),
    capabilityDisabledCards: document.querySelectorAll('.capability-card.disabled').length,
    assetNotice: document.querySelector('.assets-view .workspace-notice')?.textContent?.trim() || '',
    settingsVisible: !!document.querySelector('.settings-view'),
    articleRows: document.querySelectorAll('.article-stream-item').length,
    articleCoverSrc: document.querySelector('.article-thumb img')?.getAttribute('src') || '',
    articleTotalLabel: document.querySelector('.article-feed-summary')?.textContent?.trim() || '',
    articleError: document.querySelector('.article-feed-view .workspace-notice.error')?.textContent?.trim() || '',
    analysisCards: document.querySelectorAll('.event-thinking').length,
    toolCards: document.querySelectorAll('.event-tool').length,
    contextSourcesVisible: !!document.querySelector('.context-collapsible'),
    contextFoldLabel: document.querySelector('.context-fold-button')?.textContent?.trim() || '',
    textZoomLabel: document.querySelector('.font-zoom span')?.textContent?.trim() || '',
    fontScale: getComputedStyle(document.querySelector('.workbench')).getPropertyValue('--wb-font-scale').trim(),
    contextVisible: (() => {
      const context = document.querySelector('.workbench-context');
      if (!context) return false;
      const rect = context.getBoundingClientRect();
      return rect.right > 0 && rect.left < window.innerWidth && rect.width > 0;
    })(),
    taskScroll: (() => {
      const feed = document.querySelector('.task-feed');
      const workspace = document.querySelector('.task-workspace');
      const main = document.querySelector('.main-scroll');
      const metrics = element => element ? {
        clientHeight: element.clientHeight,
        scrollHeight: element.scrollHeight,
        scrollTop: element.scrollTop,
        overflowY: getComputedStyle(element).overflowY
      } : null;
      return { feed: metrics(feed), workspace: metrics(workspace), main: metrics(main) };
    })(),
    userBubbles: [...document.querySelectorAll('.event-user p')].slice(0, 8).map(element => ({
      length: element.textContent.length,
      width: element.getBoundingClientRect().width,
      height: element.getBoundingClientRect().height,
      scrollWidth: element.scrollWidth,
      whiteSpace: getComputedStyle(element).whiteSpace,
      textWrap: getComputedStyle(element).textWrap
    }))
  })`, true);
  console.log(`[qa] page=${JSON.stringify(pageState)}`);
  console.log(`[qa] zoomFactor=${mainWindow.webContents.getZoomFactor()}`);
  const image = await mainWindow.webContents.capturePage();
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, image.toPNG());
  if (process.env.WORKBENCH_QA_EXIT === '1') app.quit();
}

function registerIpc() {
  ipcMain.handle('desktop:info', () => ({
    appVersion: app.getVersion(),
    electron: process.versions.electron,
    chrome: process.versions.chrome,
    node: process.versions.node,
    backendPort,
  }));
  ipcMain.handle('workspace:get', () => workspaceRoot);
  ipcMain.handle('workspace:choose', () => chooseWorkspace());
  ipcMain.handle('workspace:list', (_event, relativePath = '') => listDirectory(String(relativePath)));
  ipcMain.handle('workspace:read-text', (_event, relativePath) => {
    const target = safeWorkspacePath(String(relativePath));
    const maxBytes = 2 * 1024 * 1024;
    if (statSync(target).size > maxBytes) throw new Error('文本文件不能超过 2 MB');
    return readFileSync(target, 'utf8');
  });
  ipcMain.handle('workspace:open', () => shell.openPath(workspaceRoot));
  ipcMain.handle('workspace:reveal', () => shell.showItemInFolder(workspaceRoot));
  ipcMain.handle('workspace:open-file', (_event, relativePath) => {
    const target = safeWorkspacePath(String(relativePath));
    if (!existsSync(target)) throw new Error('文件不存在');
    return shell.openPath(target);
  });
}

const gotLock = app.requestSingleInstanceLock();
if (!gotLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });

  app.whenReady().then(async () => {
    app.setAppUserModelId('me.ray.workbench');
    ensureWorkspace();
    registerIpc();
    createMenu();
    try {
      await createWindow();
    } catch (error) {
      dialog.showErrorBox('工作台启动失败', error instanceof Error ? error.message : String(error));
      app.quit();
    }
  });
}

app.on('before-quit', () => {
  isQuitting = true;
  backendProcess?.kill();
});

app.on('window-all-closed', () => app.quit());
