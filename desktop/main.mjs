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
  localServer = await startWorkbenchServer({ root: frontendRoot, backendPort, port: sitePort });

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
  mainWindow.webContents.on('will-navigate', (event, url) => {
    if (!url.startsWith(localServer.url)) event.preventDefault();
  });
  mainWindow.once('ready-to-show', () => mainWindow.show());
  await mainWindow.loadURL(`${localServer.url}/workbench`);
  await captureQaScreenshot();
}

async function captureQaScreenshot() {
  const target = process.env.WORKBENCH_QA_SCREENSHOT;
  if (app.isPackaged || !target || !mainWindow) return;
  mainWindow.show();
  mainWindow.focus();
  await new Promise(resolveWait => setTimeout(resolveWait, 2500));
  if (process.env.WORKBENCH_QA_OPEN_BLOG === '1') {
    await mainWindow.webContents.executeJavaScript(
      "document.querySelector('.blog-button')?.click()",
      true,
    );
    await new Promise(resolveWait => setTimeout(resolveWait, 1200));
  }
  const pageState = await mainWindow.webContents.executeJavaScript(`({
    title: document.title,
    text: document.body.innerText.slice(0, 300),
    workbench: !!document.querySelector('.workbench'),
    blog: !!document.querySelector('.blog-window'),
    blogTitle: document.querySelector('.blog-frame')?.contentDocument?.title || ''
  })`, true);
  console.log(`[qa] page=${JSON.stringify(pageState)}`);
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
