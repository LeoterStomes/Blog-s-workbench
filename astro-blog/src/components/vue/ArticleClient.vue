<template>
  <div class="article-client">
    <div v-if="loading" class="article-state">
      <span class="loading-line" />
      <p>正在加载文章...</p>
    </div>

    <div v-else-if="notFound" class="article-state not-found">
      <span>404</span>
      <h1>文章不存在</h1>
      <a href="/blog">返回博客列表</a>
    </div>

    <template v-else-if="article">
      <header class="article-hero" :class="{ 'has-cover': article.coverImage }">
        <img v-if="article.coverImage" :src="article.coverImage" :alt="article.title" />
        <div class="article-hero-mask" />
        <div class="article-hero-copy">
          <div class="article-tags">
            <span v-if="article.categoryName">{{ article.categoryName }}</span>
            <span v-for="tag in tags" :key="tag">{{ tag }}</span>
          </div>
          <h1>{{ article.title }}</h1>
          <p v-if="article.summary">{{ article.summary }}</p>
          <div class="article-meta">
            <span>{{ publishedLabel }}</span>
            <span>{{ readTime }} 分钟阅读</span>
            <span>{{ article.readCount || 0 }} 阅读</span>
          </div>
        </div>
      </header>

      <div class="article-layout">
        <aside class="article-toc">
          <div class="article-panel">
            <strong>本文目录</strong>
            <nav v-if="toc.length">
              <a v-for="item in toc" :key="item.id" :href="`#${item.id}`" :class="`level-${item.level}`">
                {{ item.text }}
              </a>
            </nav>
            <p v-else>暂无目录</p>
          </div>
        </aside>

        <main class="article-body">
          <article class="article-panel prose" v-html="contentHtml" />
          <CommentSection :articleId="article.id" />
        </main>

        <aside class="article-related">
          <div class="article-panel">
            <strong>相关推荐</strong>
            <a v-for="item in related" :key="item.id" :href="`/blog/${item.id}`">
              <img v-if="item.coverImage" :src="item.coverImage" :alt="item.title" loading="lazy" />
              <span>{{ item.title }}</span>
              <small>{{ item.categoryName || '文章' }}</small>
            </a>
            <p v-if="related.length === 0">暂无相关文章</p>
          </div>
        </aside>
      </div>
    </template>

    <button class="workbench-return" type="button" title="在工作台继续" @click="openWorkbench">
      <svg viewBox="0 0 24 24"><path d="M12 3l8 4-8 4-8-4 8-4zm8 8l-8 4-8-4m16 5l-8 4-8-4" /></svg>
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import DOMPurify from 'dompurify';
import CommentSection from './CommentSection.vue';

interface Article {
  id: string;
  title: string;
  summary?: string;
  content?: string;
  coverImage?: string;
  categoryId?: number;
  categoryName?: string;
  tags?: string;
  publishedAt?: string;
  readCount?: number;
}

interface TocItem {
  id: string;
  text: string;
  level: number;
}

const loading = ref(true);
const notFound = ref(false);
const article = ref<Article | null>(null);
const related = ref<Article[]>([]);
const contentHtml = ref('');
const toc = ref<TocItem[]>([]);

const tags = computed(() => article.value?.tags?.split(',').map(tag => tag.trim()).filter(Boolean) || []);
const readTime = computed(() => Math.max(1, Math.ceil((article.value?.content?.length || 0) / 300)));
const publishedLabel = computed(() => {
  if (!article.value?.publishedAt) return '';
  const date = new Date(article.value.publishedAt);
  return Number.isNaN(date.getTime())
    ? ''
    : new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' }).format(date);
});

function prepareContent(content = '') {
  const sanitized = DOMPurify.sanitize(content);
  const documentNode = new DOMParser().parseFromString(`<div id="content-root">${sanitized}</div>`, 'text/html');
  const headings = [...documentNode.querySelectorAll('h1, h2, h3')];
  toc.value = headings.map((heading, index) => {
    const id = heading.id || `toc-${index + 1}`;
    heading.id = id;
    return {
      id,
      text: heading.textContent?.trim() || '',
      level: Number(heading.tagName.slice(1)),
    };
  });
  contentHtml.value = documentNode.querySelector('#content-root')?.innerHTML || '';
}

async function loadArticle() {
  loading.value = true;
  const articleId = decodeURIComponent(window.location.pathname.split('/').filter(Boolean).pop() || '');
  try {
    const response = await fetch(`/api/knowledge/article/${encodeURIComponent(articleId)}`);
    const payload = await response.json();
    if (!response.ok || payload.code !== '200' || !payload.data) {
      notFound.value = true;
      return;
    }
    article.value = payload.data;
    prepareContent(article.value?.content);

    const relatedResponse = await fetch(
      `/api/knowledge/article/page?status=1&size=4&categoryId=${article.value?.categoryId || ''}`,
    );
    const relatedPayload = await relatedResponse.json();
    related.value = (relatedPayload.data?.records || [])
      .filter((item: Article) => item.id !== article.value?.id)
      .slice(0, 3);
  } catch {
    notFound.value = true;
  } finally {
    loading.value = false;
  }
}

function openWorkbench() {
  const sessionId = localStorage.getItem('agentSessionId');
  if (window.parent !== window) {
    window.parent.postMessage(
      { type: 'ray:open-workbench', sessionId },
      window.location.origin,
    );
    return;
  }
  window.location.href = '/workbench';
}

onMounted(loadArticle);
</script>

<style scoped>
.article-client {
  min-height: 70vh;
  color: #30364b;
}

.article-state {
  min-height: 55vh;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 12px;
  color: #8f95a7;
}

.loading-line {
  width: 42px;
  height: 3px;
  border-radius: 999px;
  background: linear-gradient(90deg, #5b7bff, #b9c5ff, #5b7bff);
  background-size: 200% 100%;
  animation: loading 1.1s linear infinite;
}

@keyframes loading {
  to { background-position: -200% 0; }
}

.not-found span {
  color: #d6dae5;
  font-size: clamp(80px, 12vw, 160px);
  font-weight: 850;
  line-height: 0.8;
}

.not-found h1 {
  margin: 0;
  font-size: 22px;
}

.not-found a {
  color: #5b7bff;
  text-decoration: none;
}

.article-hero {
  position: relative;
  min-height: 430px;
  display: flex;
  align-items: flex-end;
  overflow: hidden;
  background:
    radial-gradient(circle at 70% 20%, rgba(91, 123, 255, 0.18), transparent 35%),
    linear-gradient(145deg, #eef1ff, #f8f9fd);
}

.article-hero > img,
.article-hero-mask {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.article-hero > img {
  object-fit: cover;
}

.article-hero-mask {
  background: linear-gradient(to top, rgba(12, 17, 35, 0.84), rgba(12, 17, 35, 0.08) 72%);
}

.article-hero:not(.has-cover) .article-hero-copy {
  color: #30364b;
}

.article-hero:not(.has-cover) .article-hero-mask {
  display: none;
}

.article-hero-copy {
  position: relative;
  width: min(980px, calc(100% - 48px));
  margin: 0 auto;
  padding: 60px 0 46px;
  color: white;
}

.article-tags {
  display: flex;
  gap: 7px;
  flex-wrap: wrap;
}

.article-tags span {
  padding: 4px 9px;
  border: 1px solid rgba(255, 255, 255, 0.22);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  font-size: 9px;
}

.article-hero:not(.has-cover) .article-tags span {
  border-color: rgba(91, 123, 255, 0.18);
  background: rgba(91, 123, 255, 0.07);
  color: #4f46e5;
}

.article-hero h1 {
  max-width: 820px;
  margin: 16px 0 12px;
  font-size: clamp(36px, 4.6vw, 68px);
  font-weight: 750;
  line-height: 1.08;
  letter-spacing: -0.035em;
  text-wrap: balance;
}

.article-hero p {
  max-width: 720px;
  margin: 0 0 14px;
  color: rgba(255, 255, 255, 0.72);
  font-size: 13px;
  line-height: 1.7;
}

.article-hero:not(.has-cover) p {
  color: #7d8498;
}

.article-meta {
  display: flex;
  gap: 16px;
  color: rgba(255, 255, 255, 0.55);
  font-size: 9px;
}

.article-hero:not(.has-cover) .article-meta {
  color: #969cad;
}

.article-layout {
  width: min(1280px, calc(100% - 40px));
  margin: 0 auto;
  padding: 36px 0 80px;
  display: grid;
  grid-template-columns: 200px minmax(0, 780px) 220px;
  gap: 24px;
  justify-content: center;
}

.article-panel {
  border: 1px solid rgba(102, 111, 145, 0.12);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.84);
  box-shadow: 0 10px 32px rgba(45, 54, 86, 0.06);
  backdrop-filter: blur(14px);
}

.article-toc,
.article-related {
  position: sticky;
  top: 90px;
  align-self: start;
}

.article-toc .article-panel,
.article-related .article-panel {
  padding: 16px;
}

.article-toc strong,
.article-related strong {
  display: block;
  margin-bottom: 12px;
  color: #646b7e;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.article-toc nav {
  display: grid;
  gap: 6px;
}

.article-toc a {
  color: #9096a6;
  font-size: 9px;
  line-height: 1.45;
  text-decoration: none;
}

.article-toc a:hover {
  color: #5b7bff;
}

.article-toc a.level-2 { padding-left: 8px; }
.article-toc a.level-3 { padding-left: 16px; }

.article-toc p,
.article-related p {
  color: #a1a6b4;
  font-size: 9px;
}

.article-body {
  min-width: 0;
}

.article-body > .article-panel {
  padding: clamp(24px, 4vw, 48px);
}

.article-related a {
  display: block;
  color: inherit;
  text-decoration: none;
}

.article-related a + a {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid rgba(102, 111, 145, 0.1);
}

.article-related img {
  width: 100%;
  height: 96px;
  margin-bottom: 8px;
  border-radius: 10px;
  object-fit: cover;
}

.article-related a span {
  display: block;
  color: #555c70;
  font-size: 10px;
  font-weight: 600;
  line-height: 1.5;
}

.article-related a small {
  color: #a2a7b5;
  font-size: 8px;
}

.workbench-return {
  position: fixed;
  left: 24px;
  bottom: 80px;
  z-index: 30;
  width: 46px;
  height: 46px;
  border: 0;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: #5b7bff;
  color: white;
  box-shadow: 0 10px 28px rgba(91, 123, 255, 0.3);
  cursor: pointer;
}

.workbench-return svg {
  width: 20px;
  height: 20px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.7;
}

@media (max-width: 1050px) {
  .article-layout {
    grid-template-columns: minmax(0, 780px);
  }

  .article-toc,
  .article-related {
    display: none;
  }
}

@media (max-width: 640px) {
  .article-hero {
    min-height: 360px;
  }

  .article-hero-copy {
    width: calc(100% - 32px);
  }

  .article-layout {
    width: calc(100% - 24px);
    padding-top: 18px;
  }
}
</style>
