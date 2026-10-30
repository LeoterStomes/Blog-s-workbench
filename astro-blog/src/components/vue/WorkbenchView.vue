<template>
  <div class="workbench">
    <div class="workbench-glow" />

    <header class="workbench-topbar">
      <div class="topbar-leading">
        <button class="icon-button mobile-only" type="button" aria-label="打开导航" @click="navOpen = true">
          <svg viewBox="0 0 24 24"><path d="M4 6h16M4 12h16M4 18h16" /></svg>
        </button>
        <div class="breadcrumb">
          <span class="breadcrumb-mark">R</span>
          <span>Ray Studio</span>
          <span class="breadcrumb-separator">/</span>
          <strong>内容工作台</strong>
        </div>
      </div>

      <div class="topbar-actions">
        <span class="service-state"><i /> Agent 在线</span>
        <a class="quiet-button" href="/agent">经典助手</a>
        <button class="icon-button context-mobile-only" type="button" aria-label="打开上下文" @click="contextOpen = true">
          <svg viewBox="0 0 24 24"><path d="M4 5h16v14H4zM15 5v14" /></svg>
        </button>
      </div>
    </header>

    <div class="workbench-layout">
      <div v-if="navOpen || contextOpen" class="scrim" @click="closePanels" />

      <aside class="workbench-nav" :class="{ 'panel-open': navOpen }">
        <div class="brand-lockup">
          <div class="brand-orbit"><span>R</span></div>
          <div>
            <p class="brand-name">RAY STUDIO</p>
            <p class="brand-caption">PERSONAL CONTENT OS</p>
          </div>
        </div>

        <button class="new-task-button" type="button" @click="startNewTask">
          <svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14" /></svg>
          <span>新任务</span>
          <kbd>N</kbd>
        </button>

        <nav class="primary-nav" aria-label="工作台导航">
          <button
            v-for="item in navigation"
            :key="item.key"
            type="button"
            class="nav-item"
            :class="{ active: activeSection === item.key }"
            @click="selectSection(item)"
          >
            <span class="nav-icon" v-html="item.icon" />
            <span>{{ item.label }}</span>
            <span v-if="item.badge" class="nav-badge">{{ item.badge }}</span>
          </button>
        </nav>

        <section class="recent-section">
          <div class="section-heading">
            <span>最近任务</span>
            <button type="button" title="刷新" @click="fetchSessions">
              <svg viewBox="0 0 24 24"><path d="M20 11a8 8 0 10-2.34 5.66M20 4v7h-7" /></svg>
            </button>
          </div>
          <div v-if="loadingSessions" class="recent-empty">正在同步...</div>
          <div v-else-if="sessions.length === 0" class="recent-empty">这里会记录你的协作任务</div>
          <button
            v-for="session in sessions.slice(0, 5)"
            :key="session.id"
            type="button"
            class="recent-task"
            :class="{ active: session.id === sessionId }"
            @click="loadTaskSession(session.id)"
          >
            <span class="recent-dot" />
            <span class="recent-copy">
              <strong>{{ session.title || '未命名任务' }}</strong>
              <small>{{ session.preview || '暂无摘要' }}</small>
            </span>
          </button>
        </section>

        <div class="nav-footer">
          <a href="/profile" class="account">
            <span class="account-avatar">{{ userInitial }}</span>
            <span class="account-copy">
              <strong>{{ displayName }}</strong>
              <small>{{ loggedIn ? '个人工作区' : '尚未登录' }}</small>
            </span>
            <svg viewBox="0 0 24 24"><path d="M9 18l6-6-6-6" /></svg>
          </a>
        </div>
      </aside>

      <main class="workbench-main">
        <div class="main-scroll" :class="{ 'task-active': taskEvents.length > 0 }">
          <template v-if="taskEvents.length === 0">
            <section class="intro-block">
              <div class="intro-kicker">
                <span>{{ todayLabel }}</span>
                <span class="kicker-line" />
                <span>让每次创作都有上下文</span>
              </div>
              <h1>把想法，<br /><em>推到发布。</em></h1>
              <p>从选题、检索到写作与检查，在一个持续保留上下文的工作台里完成。</p>
            </section>

            <section class="quick-section" aria-labelledby="quick-title">
              <div class="section-title-row">
                <h2 id="quick-title">开始一项工作</h2>
                <span>选择一个入口，或直接在下方描述任务</span>
              </div>
              <div class="quick-grid">
                <button
                  v-for="action in quickActions"
                  :key="action.label"
                  type="button"
                  class="quick-card"
                  @click="usePrompt(action.prompt)"
                >
                  <span class="quick-number">{{ action.number }}</span>
                  <span class="quick-icon" v-html="action.icon" />
                  <strong>{{ action.label }}</strong>
                  <small>{{ action.description }}</small>
                  <span class="quick-arrow">
                    <svg viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6" /></svg>
                  </span>
                </button>
              </div>
            </section>

            <section class="current-task">
              <div class="task-heading">
                <div>
                  <span class="eyebrow">CURRENT TASK</span>
                  <h2>{{ draft ? '任务草稿' : '等待一个任务' }}</h2>
                </div>
                <span class="task-state" :class="{ ready: draft }">{{ draft ? '待执行' : '空闲' }}</span>
              </div>

              <div v-if="draft" class="draft-preview">
                <p>{{ draft }}</p>
                <div class="draft-actions">
                  <button type="button" class="text-button" @click="draft = ''">清除</button>
                  <button type="button" class="execute-button" @click="runTask">
                    {{ loggedIn ? '开始执行' : '登录后执行' }}
                    <svg viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6" /></svg>
                  </button>
                </div>
              </div>

              <div v-else class="task-empty">
                <div class="task-rail">
                  <span>01</span><i /><span>02</span><i /><span>03</span>
                </div>
                <div class="task-empty-copy">
                  <strong>从问题开始，而不是从空白开始。</strong>
                  <p>Agent 会把资料、工具调用、文章草稿和最终产物组织成一条可追踪的任务线。</p>
                </div>
                <span class="task-placeholder">按 ⌘K 快速聚焦</span>
              </div>
            </section>
          </template>

          <section v-else class="task-workspace">
            <div class="task-heading task-heading-sticky">
              <div>
                <span class="eyebrow">TASK {{ sessionId ? `#${sessionId}` : '' }}</span>
                <h2>{{ taskTitle }}</h2>
              </div>
              <span class="task-state" :class="statusTone">{{ statusLabel }}</span>
            </div>

            <div ref="taskFeedRef" class="task-feed" role="log" aria-live="polite">
              <article
                v-for="event in taskEvents"
                :key="event.id"
                class="task-event"
                :class="`event-${event.type}`"
              >
                <div v-if="event.type === 'user'" class="event-user">
                  <span class="event-avatar">你</span>
                  <p>{{ event.content }}</p>
                </div>

                <div v-else-if="event.type === 'thinking'" class="event-thinking">
                  <span class="event-symbol">AI</span>
                  <div>
                    <div class="event-label">{{ event.status === 'running' ? '正在分析任务' : '任务分析' }}</div>
                    <p>{{ event.content }}</p>
                  </div>
                </div>

                <div v-else-if="event.type === 'tool'" class="event-tool">
                  <span class="tool-status-dot" :class="event.status" />
                  <div class="event-tool-copy">
                    <div class="event-label">{{ event.displayName }}</div>
                    <p>{{ toolDescription(event) }}</p>
                  </div>
                  <span class="tool-state-text">{{ event.status === 'running' ? '执行中' : '已完成' }}</span>
                </div>

                <div v-else-if="event.type === 'artifact'" class="event-artifact">
                  <span class="artifact-icon"><svg viewBox="0 0 24 24"><path d="M5 3h9l5 5v13H5zM14 3v6h5M8 13h8M8 17h6" /></svg></span>
                  <span><strong>{{ event.content }}</strong><small>{{ event.format?.toUpperCase() }} 产物</small></span>
                  <a :href="event.url" :download="event.content" target="_blank">下载</a>
                </div>

                <div v-else-if="event.type === 'text'" class="event-assistant agent-markdown" v-html="renderMarkdown(event.content || '')" />

                <div v-else-if="event.type === 'error'" class="event-error">{{ event.content }}</div>
              </article>

              <div v-if="isRunning" class="stream-pulse">
                <span /><span /><span />
                <small>{{ taskStatus === 'connecting' ? '正在连接 Agent' : '正在处理' }}</small>
              </div>
            </div>
          </section>
        </div>

        <form class="composer" @submit.prevent="runTask">
          <div class="composer-main">
            <label class="attach-button" title="添加资料">
              <svg viewBox="0 0 24 24"><path d="M15 7l-6.6 6.6a2 2 0 102.8 2.8L18 9.6a4 4 0 00-5.7-5.7l-6.5 6.5a6 6 0 108.5 8.5L20 13" /></svg>
              <input type="file" multiple accept=".md,.txt,.pdf,.doc,.docx,.png,.jpg,.webp" @change="attachFiles" />
            </label>
            <textarea
              ref="composerRef"
              v-model="draft"
              rows="1"
              placeholder="描述你想完成的内容任务..."
              @input="resizeComposer"
              :disabled="isRunning"
              @keydown.enter.exact.prevent="runTask"
            />
            <button v-if="isRunning" class="send-button stop-button" type="button" aria-label="终止任务" @click="stopTask">
              <svg viewBox="0 0 24 24"><rect x="6" y="6" width="12" height="12" rx="2" /></svg>
            </button>
            <button v-else class="send-button" type="submit" :disabled="!draft.trim() || !loggedIn" aria-label="执行任务">
              <svg viewBox="0 0 24 24"><path d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" /></svg>
            </button>
          </div>
          <div class="composer-meta">
            <span>{{ isRunning ? 'Agent 正在执行 · 可随时终止' : 'Enter 执行任务 · Shift + Enter 换行' }}</span>
            <span v-if="uploadingFiles">正在上传资料...</span>
            <span v-else-if="attachedFiles.length">{{ attachedFiles.length }} 个资料待接入</span>
            <span v-else>可连接博客、知识库与上传资料</span>
          </div>
        </form>
      </main>

      <aside class="workbench-context" :class="{ 'panel-open': contextOpen }">
        <div class="context-heading">
          <div>
            <span class="eyebrow">WORKSPACE</span>
            <h2>上下文</h2>
          </div>
          <button class="icon-button mobile-only" type="button" aria-label="关闭上下文" @click="contextOpen = false">
            <svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18" /></svg>
          </button>
        </div>

        <div class="context-tabs">
          <button class="active" type="button">输出</button>
          <button type="button">资料</button>
        </div>

        <section class="context-section">
          <div class="context-section-head">
            <span>已连接</span>
            <small>3 个来源</small>
          </div>
          <div class="source-card">
            <span class="source-icon blue"><svg viewBox="0 0 24 24"><path d="M4 5h16v14H4zM8 9h8M8 13h6" /></svg></span>
            <span><strong>博客文章</strong><small>现有内容与分类</small></span>
            <i />
          </div>
          <div class="source-card">
            <span class="source-icon green"><svg viewBox="0 0 24 24"><path d="M12 3l8 4-8 4-8-4 8-4zm8 8l-8 4-8-4m16 5l-8 4-8-4" /></svg></span>
            <span><strong>知识库</strong><small>RAG 语义检索</small></span>
            <i />
          </div>
          <div class="source-card">
            <span class="source-icon amber"><svg viewBox="0 0 24 24"><path d="M8 3h8l4 4v14H4V3h4zm8 0v5h5" /></svg></span>
            <span><strong>当前资料</strong><small>{{ taskFiles.length ? `${taskFiles.length} 个文件` : '等待添加' }}</small></span>
            <i :class="{ muted: taskFiles.length === 0 }" />
          </div>
        </section>

        <section class="context-section model-section">
          <div class="context-section-head">
            <span>执行方式</span>
          </div>
          <div class="mode-card" :class="{ running: isRunning }">
            <span class="mode-mark">A</span>
            <span><strong>Agent 自动执行</strong><small>{{ statusLabel }} · 检索、写作与工具调用</small></span>
            <svg viewBox="0 0 24 24"><path d="M6 9l6 6 6-6" /></svg>
          </div>
          <div v-if="toolEvents.length" class="tool-mini-list">
            <div v-for="tool in toolEvents.slice(-4)" :key="tool.id" class="tool-mini-item">
              <span class="tool-status-dot" :class="tool.status" />
              <span>{{ tool.displayName }}</span>
            </div>
          </div>
        </section>

        <section class="artifact-preview">
          <div class="context-section-head">
            <span>产物预览</span>
            <small>{{ artifacts.length ? `${artifacts.length} 个产物` : outputText ? '实时生成' : '等待生成' }}</small>
          </div>
          <div v-if="artifacts.length" class="artifact-links">
            <a v-for="artifact in artifacts" :key="artifact.id" :href="artifact.url" :download="artifact.content" target="_blank">
              <span><svg viewBox="0 0 24 24"><path d="M5 3h9l5 5v13H5zM14 3v6h5" /></svg></span>
              <strong>{{ artifact.content }}</strong>
              <small>{{ artifact.format?.toUpperCase() }}</small>
            </a>
          </div>
          <div v-else-if="outputText" class="artifact-content agent-markdown" v-html="renderMarkdown(outputText)" />
          <div v-else class="artifact-placeholder">
            <svg viewBox="0 0 24 24"><path d="M5 3h9l5 5v13H5V3zm9 0v6h6M8 13h8M8 17h6" /></svg>
            <strong>[文章预览区域]</strong>
            <p>任务开始后，这里会显示文章草稿、修改差异和可下载产物。</p>
          </div>
        </section>

        <div class="context-footnote">
          <span class="pulse-dot" />
          <span>所有操作都会保留在任务历史中</span>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue';
import { getToken, getUser } from '@lib/auth';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import DOMPurify from 'dompurify';
import { marked } from 'marked';
import { TOOL_NAMES } from '@lib/toolNames';

interface SessionItem {
  id: string;
  title: string;
  preview: string;
}

type TaskStatus = 'idle' | 'connecting' | 'running' | 'done' | 'error' | 'cancelled';
type TaskEventType = 'user' | 'thinking' | 'tool' | 'text' | 'artifact' | 'error';

interface TaskEvent {
  id: number;
  type: TaskEventType;
  content?: string;
  tool?: string;
  displayName?: string;
  status?: 'running' | 'done' | 'error';
  args?: Record<string, unknown>;
  result?: unknown;
  url?: string;
  format?: string;
}

const sessions = ref<SessionItem[]>([]);
const loadingSessions = ref(false);
const loggedIn = ref(false);
const activeSection = ref('overview');
const draft = ref('');
const attachedFiles = ref<File[]>([]);
const taskFiles = ref<{ name: string; url: string }[]>([]);
const navOpen = ref(false);
const contextOpen = ref(false);
const composerRef = ref<HTMLTextAreaElement>();
const taskFeedRef = ref<HTMLElement>();
const user = ref(getUser());
const taskEvents = ref<TaskEvent[]>([]);
const sessionId = ref<string | null>(null);
const taskStatus = ref<TaskStatus>('idle');
const taskTitle = ref('');
const uploadingFiles = ref(false);
const streamCtrl = ref<AbortController | null>(null);
let eventSequence = 0;

const displayName = computed(() => user.value?.nickname || user.value?.username || '访客');
const userInitial = computed(() => displayName.value.slice(0, 1).toUpperCase());
const isRunning = computed(() => taskStatus.value === 'connecting' || taskStatus.value === 'running');
const toolEvents = computed(() => taskEvents.value.filter(event => event.type === 'tool'));
const artifacts = computed(() => taskEvents.value.filter(event => event.type === 'artifact'));
const outputText = computed(() => taskEvents.value
  .filter(event => event.type === 'text')
  .map(event => event.content || '')
  .join('\n\n')
  .trim());
const statusLabel = computed(() => ({
  idle: '空闲',
  connecting: '正在连接',
  running: '执行中',
  done: '已完成',
  error: '执行失败',
  cancelled: '已终止',
}[taskStatus.value]));
const statusTone = computed(() => ({
  ready: taskStatus.value === 'done',
  running: isRunning.value,
  error: taskStatus.value === 'error',
}));
const todayLabel = new Intl.DateTimeFormat('zh-CN', {
  month: 'long',
  day: 'numeric',
  weekday: 'long',
}).format(new Date());

const icon = (path: string) => `<svg viewBox="0 0 24 24">${path}</svg>`;

const navigation = [
  {
    key: 'overview',
    label: '工作台',
    href: '/workbench',
    icon: icon('<path d="M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z"/>'),
  },
  {
    key: 'articles',
    label: '文章',
    href: '/blog',
    icon: icon('<path d="M5 3h9l5 5v13H5zM14 3v6h5M8 13h8M8 17h5"/>'),
  },
  {
    key: 'assets',
    label: '素材库',
    href: '/music',
    icon: icon('<path d="M9 18V5l11-2v13M9 18a3 3 0 11-3-3 3 3 0 013 3zm11-2a3 3 0 11-3-3 3 3 0 013 3z"/>'),
  },
  {
    key: 'profile',
    label: '个人设置',
    href: '/profile',
    icon: icon('<path d="M12 12a4 4 0 100-8 4 4 0 000 8zm-7 9a7 7 0 0114 0"/>'),
  },
];

const quickActions = [
  {
    number: '01',
    label: '研究选题',
    description: '从知识库与网络梳理值得写的角度',
    prompt: '基于我的博客和知识库，调研三个值得写的新选题，并说明受众、切入角度和资料缺口。',
    icon: icon('<path d="M11 18a7 7 0 100-14 7 7 0 000 14zm5-2l5 5"/>'),
  },
  {
    number: '02',
    label: '起草文章',
    description: '带着资料与约束开始第一版',
    prompt: '请先梳理现有资料，再帮我起草一篇结构完整、适合个人博客发布的技术文章。',
    icon: icon('<path d="M4 20h4l11-11-4-4L4 16v4zm9-13l4 4M14 4l3-3 4 4-3 3"/>'),
  },
  {
    number: '03',
    label: '改写旧稿',
    description: '重组结构、语气与表达密度',
    prompt: '请找出一篇适合更新的旧文章，保留核心观点，重写结构并列出主要修改点。',
    icon: icon('<path d="M4 6h16M4 12h10M4 18h13M17 10l3 3-3 3"/>'),
  },
  {
    number: '04',
    label: '发布检查',
    description: '校对事实、链接、SEO 与可读性',
    prompt: '请对准备发布的文章做发布前检查，覆盖事实、标题、摘要、结构、SEO、链接和排版。',
    icon: icon('<path d="M5 12l4 4L19 6"/><circle cx="12" cy="12" r="9"/>'),
  },
];

function selectSection(item: { key: string; href: string }) {
  activeSection.value = item.key;
  if (item.href !== '/workbench') window.location.href = item.href;
  navOpen.value = false;
}

function startNewTask() {
  streamCtrl.value?.abort();
  streamCtrl.value = null;
  sessionId.value = null;
  taskEvents.value = [];
  taskFiles.value = [];
  taskTitle.value = '';
  taskStatus.value = 'idle';
  draft.value = '';
  attachedFiles.value = [];
  navOpen.value = false;
  requestAnimationFrame(() => composerRef.value?.focus());
}

function usePrompt(prompt: string) {
  draft.value = prompt;
  requestAnimationFrame(() => {
    composerRef.value?.focus();
    resizeComposer();
  });
}

function resizeComposer() {
  if (!composerRef.value) return;
  composerRef.value.style.height = 'auto';
  composerRef.value.style.height = `${Math.min(composerRef.value.scrollHeight, 160)}px`;
}

function attachFiles(event: Event) {
  const input = event.target as HTMLInputElement;
  attachedFiles.value = Array.from(input.files || []);
  taskFiles.value = [];
}

function closePanels() {
  navOpen.value = false;
  contextOpen.value = false;
}

function nextEventId() {
  eventSequence += 1;
  return eventSequence;
}

function pushEvent(event: Omit<TaskEvent, 'id'>) {
  taskEvents.value.push({ ...event, id: nextEventId() });
  scrollTaskFeed();
}

function scrollTaskFeed() {
  nextTick(() => {
    if (taskFeedRef.value) taskFeedRef.value.scrollTop = taskFeedRef.value.scrollHeight;
  });
}

function activeThinking() {
  const last = taskEvents.value[taskEvents.value.length - 1];
  return last?.type === 'thinking' && last.status === 'running' ? last : null;
}

function closeThinking(status: 'done' | 'error' = 'done') {
  const thinking = activeThinking();
  if (thinking) thinking.status = status;
}

function toolDescription(event: TaskEvent) {
  const args = event.args || {};
  const values = Object.entries(args)
    .filter(([, value]) => value !== null && value !== undefined && typeof value !== 'object')
    .slice(0, 2)
    .map(([key, value]) => `${key}: ${String(value).slice(0, 50)}`);
  return values.length ? values.join(' · ') : 'Agent 正在调用工作区能力';
}

function artifactFromResult(result: any, fallbackFormat = '') {
  if (!result || typeof result !== 'object') return null;
  const url = result.url || result.downloadUrl || result.download_url;
  const filename = result.filename || result.fileName || result.title || (url ? String(url).split('/').pop() : '');
  const format = result.format || fallbackFormat || (filename ? filename.split('.').pop() : '');
  if (!url || !filename) return null;
  return { url: String(url), filename: String(filename), format: String(format) };
}

async function uploadPendingFiles() {
  if (attachedFiles.value.length === 0) return [];
  uploadingFiles.value = true;
  const uploaded: { name: string; url: string }[] = [];
  try {
    for (const file of attachedFiles.value) {
      const form = new FormData();
      form.append('file', file);
      const response = await fetch('/api/file/upload/agent', {
        method: 'POST',
        headers: { token: getToken() || '' },
        body: form,
      });
      const payload = await response.json();
      if (!response.ok || payload.code !== '200') {
        throw new Error(payload.detail || payload.msg || `无法上传 ${file.name}`);
      }
      uploaded.push({ name: payload.data.name, url: payload.data.url });
    }
    taskFiles.value = uploaded;
    attachedFiles.value = [];
    return uploaded;
  } finally {
    uploadingFiles.value = false;
  }
}

async function ensureSession(title: string) {
  if (sessionId.value) return sessionId.value;
  const response = await fetch('/api/psychological-chat/session/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', token: getToken() || '' },
    body: JSON.stringify({ sessionTitle: title.slice(0, 30) }),
  });
  const payload = await response.json();
  if (!response.ok || payload.code !== '200' || !payload.data) {
    throw new Error(payload.detail || payload.msg || '无法创建任务');
  }
  sessionId.value = String(payload.data.id || payload.data);
  return sessionId.value;
}

async function runTask() {
  const text = draft.value.trim();
  if (!text || isRunning.value) return;
  if (!loggedIn.value) {
    window.location.href = '/auth/login';
    return;
  }

  const token = getToken() || '';
  taskStatus.value = 'connecting';
  taskTitle.value ||= text.slice(0, 48);
  pushEvent({ type: 'user', content: text });
  draft.value = '';
  resizeComposer();

  try {
    const files = await uploadPendingFiles();
    let fullText = text;
    if (files.length > 0) {
      fullText += '\n\n[上传文件]\n' + files
        .map(file => `- ${file.name}: ${window.location.origin}${file.url}`)
        .join('\n');
    }
    const activeSession = await ensureSession(text);
    if (!activeSession) throw new Error('任务会话创建失败');

    pushEvent({ type: 'thinking', content: '', status: 'running' });
    taskStatus.value = 'running';
    streamCtrl.value = new AbortController();
    let activeTextId: number | null = null;
    let closedNormally = false;

    await fetchEventSource('/api/psychological-chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
        token,
      },
      body: JSON.stringify({ sessionId: activeSession, userMessage: fullText }),
      signal: streamCtrl.value.signal,
      openWhenHidden: true,
      async onopen(response) {
        if (!response.ok) {
          const error = new Error(response.status === 401 ? '登录已过期，请重新登录' : 'Agent 服务连接失败');
          (error as any).status = response.status;
          throw error;
        }
      },
      onmessage(message) {
        const eventName = message.event || 'message';
        const raw = message.data || '';

        if (eventName === 'thinking') {
          try {
            const data = JSON.parse(raw);
            const thinking = activeThinking();
            if (thinking) thinking.content = (thinking.content || '') + (data.text || '');
            else pushEvent({ type: 'thinking', content: data.text || '', status: 'running' });
          } catch {
            const thinking = activeThinking();
            if (thinking) thinking.content = (thinking.content || '') + raw;
          }
          scrollTaskFeed();
        } else if (eventName === 'tool_call') {
          closeThinking();
          activeTextId = null;
          try {
            const data = JSON.parse(raw);
            pushEvent({
              type: 'tool',
              tool: data.tool,
              displayName: TOOL_NAMES[data.tool] || data.tool,
              status: 'running',
              args: data.args,
            });
          } catch {
            pushEvent({ type: 'tool', displayName: '工具调用', status: 'running' });
          }
        } else if (eventName === 'tool_result') {
          try {
            const data = JSON.parse(raw);
            const tool = [...toolEvents.value].reverse().find(item => item.tool === data.tool);
            if (tool) {
              tool.status = 'done';
              tool.result = data.result;
              const artifact = artifactFromResult(data.result);
              if (artifact && !artifacts.value.some(item => item.url === artifact.url)) {
                pushEvent({
                  type: 'artifact',
                  content: artifact.filename,
                  url: artifact.url,
                  format: artifact.format,
                });
              }
            }
          } catch {
            // Ignore malformed tool payloads; the next assistant message still renders.
          }
        } else if (eventName === 'message') {
          closeThinking();
          let chunk = raw;
          try { chunk = JSON.parse(raw).text || ''; } catch { /* plain SSE text */ }
          if (!activeTextId) {
            const id = nextEventId();
            activeTextId = id;
            taskEvents.value.push({ id, type: 'text', content: chunk });
          } else {
            const textEvent = taskEvents.value.find(item => item.id === activeTextId);
            if (textEvent) textEvent.content = (textEvent.content || '') + chunk;
          }
          scrollTaskFeed();
        } else if (eventName === 'done') {
          closeThinking();
          closedNormally = true;
          taskStatus.value = 'done';
          streamCtrl.value = null;
          fetchSessions();
        } else if (eventName === 'error') {
          closeThinking('error');
          let message = 'Agent 执行失败';
          try { message = JSON.parse(raw).message || message; } catch { /* ignore */ }
          pushEvent({ type: 'error', content: message });
          taskStatus.value = 'error';
          streamCtrl.value = null;
        }
      },
      onclose() {
        closeThinking();
        if (!closedNormally && taskStatus.value !== 'cancelled' && taskStatus.value !== 'error') {
          taskStatus.value = 'done';
        }
        streamCtrl.value = null;
        fetchSessions();
      },
      onerror(error) {
        throw error;
      },
    });
  } catch (error) {
    if ((error as any)?.name === 'AbortError') return;
    closeThinking('error');
    if (taskStatus.value !== 'cancelled') {
      taskStatus.value = 'error';
      pushEvent({
        type: 'error',
        content: error instanceof Error ? error.message : '任务执行失败',
      });
    }
  }
}

function stopTask() {
  if (!isRunning.value) return;
  taskStatus.value = 'cancelled';
  closeThinking();
  streamCtrl.value?.abort();
  streamCtrl.value = null;
}

async function loadTaskSession(id: string) {
  if (isRunning.value) return;
  taskStatus.value = 'connecting';
  navOpen.value = false;
  try {
    const response = await fetch(`/api/psychological-chat/session/${id}/messages`, {
      headers: { token: getToken() || '' },
    });
    const payload = await response.json();
    if (!response.ok || payload.code !== '200') {
      throw new Error(payload.detail || payload.msg || '任务加载失败');
    }
    sessionId.value = id;
    taskEvents.value = (payload.data || []).map((message: any) => ({
      id: nextEventId(),
      type: message.role === 'user' ? 'user' : 'text',
      content: message.content,
    }));
    const firstUserMessage = taskEvents.value.find(event => event.type === 'user')?.content;
    const selectedSession = sessions.value.find(item => item.id === id);
    taskTitle.value = firstUserMessage || selectedSession?.title || '历史任务';
    taskStatus.value = 'done';
    draft.value = '';
    scrollTaskFeed();
  } catch (error) {
    taskStatus.value = 'error';
    pushEvent({ type: 'error', content: error instanceof Error ? error.message : '任务加载失败' });
  }
}

function renderMarkdown(content: string) {
  return DOMPurify.sanitize(marked.parse(content || '', { breaks: true }) as string);
}

async function fetchSessions() {
  if (!loggedIn.value) return;
  loadingSessions.value = true;
  try {
    const response = await fetch('/api/psychological-chat/session/list', {
      headers: { token: getToken() || '' },
    });
    const payload = await response.json();
    if (response.ok && payload.code === '200') sessions.value = payload.data || [];
  } catch {
    sessions.value = [];
  } finally {
    loadingSessions.value = false;
  }
}

function handleShortcut(event: KeyboardEvent) {
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
    event.preventDefault();
    composerRef.value?.focus();
  }
  if (event.key === 'Escape') closePanels();
}

onMounted(() => {
  const footer = document.querySelector('body > footer');
  if (footer) (footer as HTMLElement).style.display = 'none';
  loggedIn.value = !!getToken() && !!getUser();
  fetchSessions();
  window.addEventListener('keydown', handleShortcut);
});

onUnmounted(() => {
  const footer = document.querySelector('body > footer');
  if (footer) (footer as HTMLElement).style.display = '';
  window.removeEventListener('keydown', handleShortcut);
});
</script>

<style scoped>
.workbench {
  --wb-blue: #5b7bff;
  --wb-blue-deep: #4359d6;
  --wb-green: #22c55e;
  --wb-ink: #171b2e;
  --wb-muted: #777d93;
  --wb-line: rgba(98, 106, 140, 0.14);
  --wb-panel: rgba(255, 255, 255, 0.82);
  --wb-soft: rgba(245, 247, 252, 0.88);
  position: relative;
  min-height: calc(100vh - 64px);
  padding: 18px clamp(14px, 2vw, 30px) 24px;
  overflow: hidden;
  color: var(--wb-ink);
  isolation: isolate;
}

.workbench-glow {
  position: absolute;
  inset: -25% 10% 45%;
  z-index: -1;
  background:
    radial-gradient(circle at 72% 34%, rgba(91, 123, 255, 0.14), transparent 31%),
    radial-gradient(circle at 20% 8%, rgba(34, 197, 94, 0.08), transparent 27%);
  pointer-events: none;
}

.workbench-topbar {
  height: 54px;
  max-width: 1580px;
  margin: 0 auto 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 4px;
}

.topbar-leading,
.topbar-actions,
.breadcrumb,
.service-state {
  display: flex;
  align-items: center;
}

.topbar-leading {
  gap: 10px;
}

.topbar-actions {
  gap: 10px;
}

.breadcrumb {
  gap: 9px;
  font-size: 12px;
  color: var(--wb-muted);
}

.breadcrumb strong {
  color: var(--wb-ink);
  font-weight: 600;
}

.breadcrumb-mark {
  width: 25px;
  height: 25px;
  border-radius: 8px;
  display: grid;
  place-items: center;
  color: white;
  font-size: 12px;
  font-weight: 800;
  background: linear-gradient(145deg, var(--wb-blue), var(--wb-blue-deep));
  box-shadow: 0 5px 14px rgba(91, 123, 255, 0.24);
}

.breadcrumb-separator {
  color: #b8bdcc;
}

.service-state {
  gap: 7px;
  height: 32px;
  padding: 0 11px;
  border: 1px solid var(--wb-line);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.54);
  font-size: 11px;
  color: #5f667a;
  backdrop-filter: blur(12px);
}

.service-state i,
.pulse-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--wb-green);
  box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.1);
}

.quiet-button,
.icon-button,
.new-task-button,
.nav-item,
.quick-card,
.text-button,
.execute-button,
.send-button,
.context-tabs button {
  font: inherit;
}

.quiet-button {
  padding: 8px 12px;
  color: #626a82;
  font-size: 12px;
  border-radius: 9px;
  text-decoration: none;
  transition: 160ms ease;
}

.quiet-button:hover {
  color: var(--wb-blue-deep);
  background: rgba(91, 123, 255, 0.08);
}

.icon-button {
  width: 34px;
  height: 34px;
  border: 1px solid var(--wb-line);
  border-radius: 9px;
  background: rgba(255, 255, 255, 0.68);
  color: #687086;
  display: grid;
  place-items: center;
  cursor: pointer;
}

.icon-button svg,
.primary-nav svg,
.quick-card svg,
.execute-button svg,
.send-button svg,
.section-heading svg,
.source-icon svg,
.account svg,
.mode-card svg {
  width: 17px;
  height: 17px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.7;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.workbench-layout {
  width: 100%;
  max-width: 1580px;
  height: calc(100vh - 138px);
  min-height: 660px;
  max-height: 940px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 224px minmax(480px, 1fr) 292px;
  border: 1px solid rgba(102, 111, 145, 0.12);
  border-radius: 20px;
  overflow: hidden;
  background: var(--wb-panel);
  box-shadow: 0 24px 80px rgba(52, 60, 95, 0.1);
  backdrop-filter: blur(24px);
}

.workbench-nav,
.workbench-context {
  min-width: 0;
  background: rgba(248, 249, 253, 0.76);
}

.workbench-nav {
  display: flex;
  flex-direction: column;
  padding: 20px 14px 14px;
  border-right: 1px solid var(--wb-line);
}

.brand-lockup {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 0 5px 20px;
}

.brand-orbit {
  width: 34px;
  height: 34px;
  border: 1px solid rgba(91, 123, 255, 0.22);
  border-radius: 50%;
  display: grid;
  place-items: center;
  position: relative;
  background: rgba(91, 123, 255, 0.06);
}

.brand-orbit::after {
  content: '';
  position: absolute;
  width: 8px;
  height: 8px;
  right: -1px;
  top: 2px;
  border: 2px solid #f7f8fc;
  border-radius: 50%;
  background: var(--wb-green);
}

.brand-orbit span {
  font-size: 13px;
  font-weight: 800;
  color: var(--wb-blue-deep);
}

.brand-name,
.brand-caption {
  margin: 0;
}

.brand-name {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.14em;
}

.brand-caption {
  margin-top: 3px;
  font-size: 7px;
  letter-spacing: 0.16em;
  color: #9ba1b3;
}

.new-task-button {
  height: 42px;
  padding: 0 12px;
  border: 0;
  border-radius: 11px;
  background: var(--wb-ink);
  color: white;
  display: flex;
  align-items: center;
  gap: 9px;
  cursor: pointer;
  box-shadow: 0 8px 20px rgba(23, 27, 46, 0.16);
  transition: transform 160ms ease, box-shadow 160ms ease;
}

.new-task-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 11px 24px rgba(23, 27, 46, 0.2);
}

.new-task-button svg {
  width: 16px;
  height: 16px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
}

.new-task-button span {
  flex: 1;
  text-align: left;
  font-size: 12px;
  font-weight: 600;
}

.new-task-button kbd {
  padding: 2px 5px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 4px;
  color: rgba(255, 255, 255, 0.48);
  font-size: 9px;
}

.primary-nav {
  display: grid;
  gap: 2px;
  margin-top: 18px;
}

.nav-item {
  width: 100%;
  height: 38px;
  padding: 0 10px;
  border: 0;
  border-radius: 9px;
  background: transparent;
  color: #6d7489;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  cursor: pointer;
  transition: 150ms ease;
}

.nav-item:hover {
  color: var(--wb-ink);
  background: rgba(255, 255, 255, 0.72);
}

.nav-item.active {
  color: var(--wb-blue-deep);
  background: rgba(91, 123, 255, 0.09);
  font-weight: 600;
}

.nav-icon {
  display: grid;
  place-items: center;
}

.nav-icon :deep(svg) {
  width: 16px;
  height: 16px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.7;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.nav-badge {
  margin-left: auto;
  padding: 2px 6px;
  border-radius: 999px;
  background: rgba(91, 123, 255, 0.1);
  color: var(--wb-blue-deep);
  font-size: 9px;
}

.recent-section {
  min-height: 0;
  margin-top: 24px;
  flex: 1;
  overflow: auto;
}

.section-heading,
.context-section-head,
.task-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-heading {
  padding: 0 7px 8px;
  color: #9a9fb0;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.section-heading button {
  border: 0;
  background: transparent;
  color: #a3a8b7;
  cursor: pointer;
}

.recent-empty {
  padding: 14px 8px;
  color: #a1a6b7;
  font-size: 10px;
  line-height: 1.6;
}

.recent-task {
  width: 100%;
  border: 0;
  background: transparent;
  text-align: left;
  display: flex;
  gap: 9px;
  padding: 9px 8px;
  border-radius: 9px;
  color: inherit;
  text-decoration: none;
  transition: background 150ms ease;
}

.recent-task:hover {
  background: rgba(255, 255, 255, 0.8);
}

.recent-task.active {
  background: rgba(91, 123, 255, 0.07);
}

.recent-task.active .recent-dot {
  background: var(--wb-blue);
  box-shadow: 0 0 0 3px rgba(91, 123, 255, 0.1);
}

.recent-dot {
  width: 5px;
  height: 5px;
  margin-top: 6px;
  border-radius: 50%;
  background: #bec3d1;
  flex-shrink: 0;
}

.recent-copy {
  min-width: 0;
  display: grid;
  gap: 3px;
}

.recent-copy strong,
.recent-copy small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recent-copy strong {
  color: #50566b;
  font-size: 10px;
  font-weight: 600;
}

.recent-copy small {
  color: #a0a5b4;
  font-size: 9px;
}

.nav-footer {
  padding-top: 12px;
  border-top: 1px solid var(--wb-line);
}

.account {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 7px;
  border-radius: 10px;
  color: inherit;
  text-decoration: none;
}

.account-avatar {
  width: 30px;
  height: 30px;
  border-radius: 9px;
  display: grid;
  place-items: center;
  background: rgba(91, 123, 255, 0.12);
  color: var(--wb-blue-deep);
  font-size: 11px;
  font-weight: 800;
}

.account-copy {
  min-width: 0;
  display: grid;
  gap: 2px;
  flex: 1;
}

.account-copy strong {
  font-size: 10px;
  color: #53596e;
}

.account-copy small {
  font-size: 8px;
  color: #a3a8b7;
}

.account > svg {
  width: 13px;
  color: #a3a8b7;
}

.workbench-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  background:
    linear-gradient(rgba(255, 255, 255, 0.76), rgba(255, 255, 255, 0.92)),
    radial-gradient(circle at 50% 0%, rgba(91, 123, 255, 0.06), transparent 38%);
}

.main-scroll {
  flex: 1;
  overflow-y: auto;
  padding: clamp(34px, 5vw, 68px) clamp(28px, 5vw, 72px) 34px;
}

.main-scroll.task-active {
  min-height: 0;
  padding: clamp(24px, 3vw, 38px) clamp(24px, 4vw, 56px) 18px;
  overflow: hidden;
}

.intro-block {
  max-width: 660px;
}

.intro-kicker {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #969caf;
  font-size: 9px;
  font-weight: 600;
  letter-spacing: 0.09em;
  text-transform: uppercase;
}

.kicker-line {
  width: 28px;
  height: 1px;
  background: #c8cbd5;
}

.intro-block h1 {
  margin: 21px 0 15px;
  color: var(--wb-ink);
  font-size: clamp(40px, 4.6vw, 64px);
  font-weight: 650;
  line-height: 0.98;
  letter-spacing: -0.055em;
}

.intro-block h1 em {
  color: var(--wb-blue);
  font-style: normal;
}

.intro-block p {
  max-width: 510px;
  margin: 0;
  color: #777e92;
  font-size: 12px;
  line-height: 1.8;
  text-wrap: pretty;
}

.quick-section {
  margin-top: 38px;
}

.section-title-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 13px;
}

.section-title-row h2,
.task-heading h2,
.context-heading h2 {
  margin: 0;
  color: var(--wb-ink);
  font-weight: 650;
}

.section-title-row h2 {
  font-size: 13px;
}

.section-title-row > span {
  color: #a2a7b6;
  font-size: 9px;
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 9px;
}

.quick-card {
  position: relative;
  min-height: 118px;
  padding: 16px;
  border: 1px solid var(--wb-line);
  border-radius: 13px;
  background: rgba(255, 255, 255, 0.66);
  text-align: left;
  cursor: pointer;
  overflow: hidden;
  transition: transform 180ms ease, border-color 180ms ease, box-shadow 180ms ease;
}

.quick-card:hover {
  transform: translateY(-2px);
  border-color: rgba(91, 123, 255, 0.28);
  box-shadow: 0 12px 30px rgba(53, 62, 100, 0.08);
}

.quick-number {
  position: absolute;
  right: 14px;
  top: 12px;
  color: rgba(91, 123, 255, 0.4);
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.1em;
}

.quick-icon {
  width: 29px;
  height: 29px;
  margin-bottom: 12px;
  border-radius: 8px;
  display: grid;
  place-items: center;
  color: var(--wb-blue-deep);
  background: rgba(91, 123, 255, 0.08);
}

.quick-icon :deep(svg) {
  width: 15px;
  height: 15px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.7;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.quick-card strong,
.quick-card small {
  display: block;
}

.quick-card strong {
  color: #3f455a;
  font-size: 11px;
  font-weight: 650;
}

.quick-card small {
  max-width: 82%;
  margin-top: 5px;
  color: #969caf;
  font-size: 9px;
  line-height: 1.55;
  text-wrap: pretty;
}

.quick-arrow {
  position: absolute;
  right: 14px;
  bottom: 14px;
  color: #b3b7c4;
  opacity: 0;
  transform: translateX(-4px);
  transition: 180ms ease;
}

.quick-card:hover .quick-arrow {
  opacity: 1;
  transform: translateX(0);
}

.quick-arrow svg {
  width: 14px;
  height: 14px;
}

.current-task {
  margin-top: 24px;
  padding: 18px;
  border: 1px solid var(--wb-line);
  border-radius: 14px;
  background: rgba(248, 249, 253, 0.68);
}

.eyebrow {
  display: block;
  margin-bottom: 5px;
  color: #a0a5b4;
  font-size: 8px;
  font-weight: 700;
  letter-spacing: 0.13em;
}

.task-heading h2 {
  font-size: 15px;
}

.task-state {
  padding: 4px 8px;
  border-radius: 999px;
  background: #eef0f5;
  color: #9096a7;
  font-size: 8px;
  font-weight: 650;
}

.task-state.ready {
  background: rgba(34, 197, 94, 0.09);
  color: #159849;
}

.task-state.running {
  background: rgba(91, 123, 255, 0.09);
  color: var(--wb-blue-deep);
}

.task-state.error {
  background: rgba(239, 68, 68, 0.09);
  color: #d63d3d;
}

.draft-preview p {
  margin: 16px 0;
  color: #51576b;
  font-size: 12px;
  line-height: 1.75;
  text-wrap: pretty;
}

.draft-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

.text-button,
.execute-button {
  border-radius: 8px;
  cursor: pointer;
}

.text-button {
  padding: 7px 10px;
  border: 0;
  background: transparent;
  color: #8e94a5;
  font-size: 9px;
}

.execute-button {
  padding: 8px 11px;
  border: 0;
  background: var(--wb-blue);
  color: white;
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 9px;
  font-weight: 600;
}

.execute-button svg {
  width: 13px;
  height: 13px;
}

.task-empty {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 18px;
  margin-top: 18px;
}

.task-rail {
  display: flex;
  align-items: center;
  gap: 5px;
}

.task-rail span {
  width: 22px;
  height: 22px;
  display: grid;
  place-items: center;
  border: 1px solid #dfe2e9;
  border-radius: 50%;
  color: #b0b5c2;
  font-size: 7px;
}

.task-rail i {
  width: 13px;
  height: 1px;
  background: #e0e2e9;
}

.task-empty-copy strong {
  display: block;
  color: #4b5166;
  font-size: 10px;
}

.task-empty-copy p {
  max-width: 410px;
  margin: 4px 0 0;
  color: #999faf;
  font-size: 9px;
  line-height: 1.6;
}

.task-placeholder {
  color: #b2b6c2;
  font-size: 8px;
  white-space: nowrap;
}

.task-workspace {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.task-heading-sticky {
  flex-shrink: 0;
  margin-bottom: 16px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--wb-line);
}

.task-heading-sticky h2 {
  max-width: min(620px, 68vw);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-feed {
  min-height: 0;
  flex: 1;
  overflow-y: auto;
  padding: 2px 4px 26px 1px;
}

.task-event {
  margin-bottom: 12px;
  animation: event-enter 220ms ease-out both;
}

@keyframes event-enter {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}

.event-user {
  display: flex;
  justify-content: flex-end;
  align-items: flex-start;
  gap: 9px;
}

.event-user p {
  max-width: 76%;
  margin: 0;
  padding: 11px 14px;
  border-radius: 14px 14px 4px 14px;
  background: var(--wb-ink);
  color: white;
  font-size: 11px;
  line-height: 1.7;
  white-space: pre-wrap;
  text-wrap: pretty;
}

.event-avatar,
.event-symbol {
  width: 26px;
  height: 26px;
  flex-shrink: 0;
  border-radius: 8px;
  display: grid;
  place-items: center;
  font-size: 8px;
  font-weight: 750;
}

.event-avatar {
  order: 2;
  background: rgba(91, 123, 255, 0.1);
  color: var(--wb-blue-deep);
}

.event-thinking {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  max-width: 84%;
  padding: 11px 13px;
  border: 1px solid var(--wb-line);
  border-radius: 12px;
  background: rgba(248, 249, 253, 0.7);
}

.event-symbol {
  background: rgba(91, 123, 255, 0.09);
  color: var(--wb-blue-deep);
}

.event-label {
  color: #6c7387;
  font-size: 9px;
  font-weight: 650;
}

.event-thinking p {
  max-height: 108px;
  margin: 5px 0 0;
  overflow: hidden;
  color: #8f95a6;
  font-size: 9px;
  line-height: 1.65;
  white-space: pre-wrap;
  mask-image: linear-gradient(to bottom, black 68%, transparent 100%);
}

.event-tool {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid var(--wb-line);
  border-radius: 11px;
  background: rgba(255, 255, 255, 0.7);
}

.tool-status-dot {
  width: 7px;
  height: 7px;
  flex-shrink: 0;
  border-radius: 50%;
  background: #c4c8d2;
}

.tool-status-dot.running {
  background: var(--wb-blue);
  box-shadow: 0 0 0 4px rgba(91, 123, 255, 0.1);
  animation: tool-pulse 1.4s ease-in-out infinite;
}

@keyframes tool-pulse {
  50% { opacity: 0.45; }
}

.tool-status-dot.done {
  background: var(--wb-green);
}

.event-tool-copy {
  min-width: 0;
  flex: 1;
}

.event-tool-copy p {
  margin: 3px 0 0;
  overflow: hidden;
  color: #9ca1b0;
  font-size: 8px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tool-state-text {
  color: #9ca1b0;
  font-size: 8px;
}

.event-assistant {
  max-width: 86%;
  padding: 13px 15px;
  border: 1px solid rgba(103, 111, 141, 0.1);
  border-radius: 4px 15px 15px 15px;
  background: rgba(255, 255, 255, 0.74);
  color: #50566b;
  font-size: 11px;
  line-height: 1.75;
}

.event-artifact {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid rgba(34, 197, 94, 0.18);
  border-radius: 11px;
  background: rgba(34, 197, 94, 0.05);
}

.artifact-icon {
  width: 30px;
  height: 30px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  background: rgba(34, 197, 94, 0.09);
  color: #159849;
}

.artifact-icon svg {
  width: 15px;
  height: 15px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.7;
}

.event-artifact > span:nth-child(2) {
  min-width: 0;
  display: grid;
  gap: 2px;
  flex: 1;
}

.event-artifact strong {
  overflow: hidden;
  color: #4d5367;
  font-size: 9px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.event-artifact small {
  color: #96a09f;
  font-size: 8px;
}

.event-artifact a {
  padding: 6px 9px;
  border-radius: 7px;
  background: #159849;
  color: white;
  font-size: 8px;
  text-decoration: none;
}

.event-error {
  padding: 10px 12px;
  border: 1px solid rgba(239, 68, 68, 0.18);
  border-radius: 10px;
  background: rgba(239, 68, 68, 0.05);
  color: #cf4141;
  font-size: 9px;
  line-height: 1.6;
}

.stream-pulse {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 7px 2px;
}

.stream-pulse span {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--wb-blue);
  animation: stream-dot 1.1s ease-in-out infinite;
}

.stream-pulse span:nth-child(2) { animation-delay: 120ms; }
.stream-pulse span:nth-child(3) { animation-delay: 240ms; }

.stream-pulse small {
  margin-left: 5px;
  color: #a1a6b5;
  font-size: 8px;
}

@keyframes stream-dot {
  0%, 100% { opacity: 0.3; transform: translateY(0); }
  50% { opacity: 1; transform: translateY(-2px); }
}

.composer {
  position: relative;
  flex-shrink: 0;
  margin: 0 clamp(22px, 4vw, 54px) 20px;
  padding: 11px 12px 8px;
  border: 1px solid rgba(91, 123, 255, 0.2);
  border-radius: 15px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 12px 40px rgba(50, 60, 100, 0.09);
}

.composer-main {
  display: flex;
  align-items: flex-end;
  gap: 8px;
}

.attach-button {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  border-radius: 8px;
  color: #848b9e;
  cursor: pointer;
  transition: 150ms ease;
}

.attach-button:hover {
  color: var(--wb-blue-deep);
  background: rgba(91, 123, 255, 0.08);
}

.attach-button svg {
  width: 16px;
  height: 16px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.7;
}

.attach-button input {
  display: none;
}

.composer textarea {
  min-height: 32px;
  max-height: 160px;
  flex: 1;
  padding: 7px 2px;
  border: 0;
  outline: 0;
  resize: none;
  background: transparent;
  color: #30364b;
  font: inherit;
  font-size: 12px;
  line-height: 1.5;
}

.composer textarea::placeholder {
  color: #a5aab8;
}

.send-button {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  border: 0;
  border-radius: 9px;
  display: grid;
  place-items: center;
  background: var(--wb-blue);
  color: white;
  cursor: pointer;
  box-shadow: 0 6px 14px rgba(91, 123, 255, 0.24);
}

.send-button:disabled {
  opacity: 0.34;
  cursor: not-allowed;
  box-shadow: none;
}

.send-button.stop-button {
  background: #ef4444;
  box-shadow: 0 6px 14px rgba(239, 68, 68, 0.2);
}

.send-button svg {
  width: 15px;
  height: 15px;
}

.composer-meta {
  display: flex;
  justify-content: space-between;
  padding: 5px 42px 0;
  color: #a3a8b6;
  font-size: 8px;
}

.workbench-context {
  min-height: 0;
  padding: 20px 17px 16px;
  display: flex;
  flex-direction: column;
  border-left: 1px solid var(--wb-line);
}

.context-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.context-heading h2 {
  font-size: 15px;
}

.context-tabs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  margin-top: 16px;
  padding: 3px;
  border-radius: 9px;
  background: #eef0f5;
}

.context-tabs button {
  height: 28px;
  border: 0;
  border-radius: 7px;
  background: transparent;
  color: #989dac;
  font-size: 9px;
}

.context-tabs button.active {
  background: white;
  color: #4b5268;
  box-shadow: 0 2px 6px rgba(56, 64, 96, 0.08);
  font-weight: 600;
}

.context-section {
  margin-top: 22px;
}

.context-section-head {
  margin-bottom: 9px;
  color: #777e92;
  font-size: 9px;
  font-weight: 600;
}

.context-section-head small {
  color: #a4a9b7;
  font-size: 8px;
  font-weight: 400;
}

.source-card,
.mode-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px;
  border: 1px solid rgba(103, 111, 141, 0.1);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.66);
}

.source-card + .source-card {
  margin-top: 6px;
}

.source-icon {
  width: 28px;
  height: 28px;
  display: grid;
  place-items: center;
  border-radius: 8px;
}

.source-icon.blue {
  background: rgba(91, 123, 255, 0.09);
  color: var(--wb-blue-deep);
}

.source-icon.green {
  background: rgba(34, 197, 94, 0.08);
  color: #17934a;
}

.source-icon.amber {
  background: rgba(245, 158, 11, 0.09);
  color: #b77908;
}

.source-icon svg {
  width: 14px;
  height: 14px;
}

.source-card > span:nth-child(2),
.mode-card > span:nth-child(2) {
  min-width: 0;
  display: grid;
  gap: 2px;
  flex: 1;
}

.source-card strong,
.mode-card strong {
  color: #51576b;
  font-size: 9px;
  font-weight: 600;
}

.source-card small,
.mode-card small {
  color: #a0a5b3;
  font-size: 8px;
}

.source-card > i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--wb-green);
}

.source-card > i.muted {
  background: #cdd0d9;
}

.mode-card {
  padding: 11px;
}

.mode-card.running {
  border-color: rgba(91, 123, 255, 0.2);
  box-shadow: inset 0 0 0 1px rgba(91, 123, 255, 0.04);
}

.mode-mark {
  width: 28px;
  height: 28px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  background: var(--wb-ink);
  color: white;
  font-size: 10px;
  font-weight: 700;
}

.mode-card > svg {
  width: 14px;
  color: #9ba0ae;
}

.tool-mini-list {
  display: grid;
  gap: 5px;
  margin-top: 7px;
}

.tool-mini-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 8px;
  color: #8f95a5;
  font-size: 8px;
}

.tool-mini-item .tool-status-dot {
  width: 5px;
  height: 5px;
  box-shadow: none;
}

.artifact-preview {
  min-height: 0;
  margin-top: 22px;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.artifact-placeholder {
  min-height: 156px;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px;
  border: 1px dashed #d7dae2;
  border-radius: 12px;
  background:
    linear-gradient(135deg, rgba(91, 123, 255, 0.025), transparent),
    rgba(255, 255, 255, 0.4);
  text-align: center;
}

.artifact-content {
  min-height: 156px;
  max-height: 310px;
  flex: 1;
  overflow: auto;
  padding: 14px;
  border: 1px solid var(--wb-line);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.6);
  color: #5e6579;
  font-size: 10px;
  line-height: 1.7;
}

.artifact-content :deep(h1),
.artifact-content :deep(h2),
.artifact-content :deep(h3) {
  margin: 0.85em 0 0.4em;
  color: var(--wb-ink);
  line-height: 1.25;
}

.artifact-content :deep(h1) { font-size: 17px; }
.artifact-content :deep(h2) { font-size: 14px; }
.artifact-content :deep(h3) { font-size: 12px; }
.artifact-content :deep(p) { margin: 0.6em 0; }
.artifact-content :deep(ul),
.artifact-content :deep(ol) { padding-left: 18px; }
.artifact-content :deep(pre) {
  overflow-x: auto;
  padding: 10px;
  border-radius: 8px;
  background: #1e2230;
  color: #e7eaf3;
  font-size: 9px;
}

.artifact-links {
  min-height: 140px;
  max-height: 310px;
  overflow-y: auto;
}

.artifact-links a {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 10px;
  border: 1px solid var(--wb-line);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.6);
  color: inherit;
  text-decoration: none;
}

.artifact-links a + a {
  margin-top: 7px;
}

.artifact-links a > span {
  width: 28px;
  height: 28px;
  display: grid;
  place-items: center;
  border-radius: 7px;
  background: rgba(91, 123, 255, 0.08);
  color: var(--wb-blue-deep);
}

.artifact-links svg {
  width: 14px;
  height: 14px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.6;
}

.artifact-links strong {
  min-width: 0;
  overflow: hidden;
  color: #555b70;
  font-size: 8px;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.artifact-links small {
  color: #9ba0af;
  font-size: 7px;
}

.artifact-placeholder > svg {
  width: 24px;
  height: 24px;
  margin-bottom: 10px;
  fill: none;
  stroke: #b4b9c6;
  stroke-width: 1.2;
}

.artifact-placeholder strong {
  color: #9298a8;
  font-size: 9px;
}

.artifact-placeholder p {
  max-width: 190px;
  margin: 6px 0 0;
  color: #adb1bd;
  font-size: 8px;
  line-height: 1.6;
  text-wrap: pretty;
}

.context-footnote {
  padding-top: 11px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #a1a6b5;
  font-size: 8px;
}

.context-footnote .pulse-dot {
  width: 5px;
  height: 5px;
  box-shadow: none;
}

.scrim,
.mobile-only,
.context-mobile-only {
  display: none;
}

@media (max-width: 1180px) {
  .workbench-layout {
    grid-template-columns: 210px minmax(430px, 1fr);
  }

  .workbench-context {
    position: absolute;
    z-index: 40;
    right: 18px;
    top: 82px;
    bottom: 24px;
    width: 292px;
    border: 1px solid var(--wb-line);
    border-radius: 16px;
    box-shadow: 0 20px 60px rgba(39, 46, 75, 0.18);
    transform: translateX(calc(100% + 28px));
    transition: transform 220ms cubic-bezier(0.2, 0.8, 0.2, 1);
  }

  .workbench-context.panel-open {
    transform: translateX(0);
  }

  .context-mobile-only {
    display: grid;
  }
}

@media (max-width: 860px) {
  .workbench {
    padding: 10px 10px 16px;
  }

  .workbench-topbar {
    height: 48px;
    padding: 0 2px;
  }

  .breadcrumb > span:not(.breadcrumb-mark),
  .service-state,
  .quiet-button {
    display: none;
  }

  .mobile-only {
    display: grid;
  }

  .workbench-layout {
    height: calc(100vh - 112px);
    min-height: 620px;
    display: block;
    border-radius: 16px;
  }

  .workbench-nav {
    position: absolute;
    z-index: 50;
    left: 10px;
    top: 66px;
    bottom: 16px;
    width: 232px;
    border: 1px solid var(--wb-line);
    border-radius: 15px;
    box-shadow: 0 20px 60px rgba(39, 46, 75, 0.18);
    transform: translateX(calc(-100% - 20px));
    transition: transform 220ms cubic-bezier(0.2, 0.8, 0.2, 1);
  }

  .workbench-nav.panel-open {
    transform: translateX(0);
  }

  .workbench-context {
    right: 10px;
    top: 66px;
    bottom: 16px;
  }

  .scrim {
    position: fixed;
    inset: 0;
    z-index: 35;
    display: block;
    background: rgba(24, 28, 45, 0.18);
    backdrop-filter: blur(2px);
  }

  .workbench-main {
    height: 100%;
  }

  .main-scroll {
    padding: 35px 24px 24px;
  }

  .intro-block h1 {
    font-size: clamp(38px, 12vw, 55px);
  }

  .composer {
    margin: 0 14px 14px;
  }
}

@media (max-width: 590px) {
  .quick-grid {
    grid-template-columns: 1fr;
  }

  .quick-card {
    min-height: 104px;
  }

  .section-title-row > span,
  .task-placeholder,
  .composer-meta span:last-child {
    display: none;
  }

  .task-empty {
    grid-template-columns: 1fr;
    gap: 11px;
  }

  .task-rail {
    display: none;
  }

  .workbench-context {
    width: calc(100vw - 20px);
  }
}

:global(.dark-mode) .workbench {
  --wb-ink: #eef0f8;
  --wb-muted: #9ca3b8;
  --wb-line: rgba(255, 255, 255, 0.08);
  --wb-panel: rgba(22, 24, 36, 0.9);
  --wb-soft: rgba(27, 30, 44, 0.9);
}

:global(.dark-mode) .workbench-nav,
:global(.dark-mode) .workbench-context {
  background: rgba(25, 28, 41, 0.92);
}

:global(.dark-mode) .workbench-main {
  background:
    linear-gradient(rgba(20, 22, 33, 0.82), rgba(20, 22, 33, 0.94)),
    radial-gradient(circle at 50% 0%, rgba(91, 123, 255, 0.12), transparent 38%);
}

:global(.dark-mode) .quick-card,
:global(.dark-mode) .current-task,
:global(.dark-mode) .source-card,
:global(.dark-mode) .mode-card,
:global(.dark-mode) .composer {
  background: rgba(34, 37, 52, 0.78);
}

:global(.dark-mode) .quick-card strong,
:global(.dark-mode) .task-heading h2,
:global(.dark-mode) .context-heading h2,
:global(.dark-mode) .source-card strong,
:global(.dark-mode) .mode-card strong {
  color: #e7eaf3;
}

:global(.dark-mode) .context-tabs {
  background: rgba(255, 255, 255, 0.05);
}

:global(.dark-mode) .context-tabs button.active {
  background: rgba(255, 255, 255, 0.09);
  color: #e7eaf3;
}

@media (prefers-reduced-motion: reduce) {
  .workbench *,
  .workbench *::before,
  .workbench *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
</style>
