import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import test from 'node:test';

const requireFromBlog = createRequire(new URL('../../astro-blog/package.json', import.meta.url));
const { marked } = requireFromBlog('marked');

test('normalizes malformed agent table output into a heading and table', async () => {
  const { normalizeAgentMarkdown, wrapMarkdownTables } = await import(
    '../../astro-blog/src/lib/agentMarkdown.mjs'
  );
  const source = [
    '##批次 B ·分类与标题修正|文章（ID前8位） |字段 |现值到目标 |\\',
    '\\|---|---|---|\\',
    '| `da431f71` Python继承完全指南 |分类 |技术改为 python |\\',
    '| `3caebe96` Python的 Lambda语法 |标题 |补空格 |&#x20;',
  ].join('\n');

  const html = wrapMarkdownTables(marked.parse(normalizeAgentMarkdown(source), {
    breaks: true,
    gfm: true,
  }));

  assert.match(html, /<h2>批次 B ·分类与标题修正<\/h2>/);
  assert.match(html, /class="markdown-table-wrap"/);
  assert.match(html, /<table>/);
  assert.match(html, /文章（ID前8位）/);
  assert.match(html, /Python继承完全指南/);
  assert.doesNotMatch(html, /\\---/);
});

test('leaves fenced code blocks untouched', async () => {
  const { normalizeAgentMarkdown } = await import('../../astro-blog/src/lib/agentMarkdown.mjs');
  const source = [
    '```markdown',
    '##无空格标题',
    '| 示例 |表格 |\\',
    '|---|---|',
    '```',
  ].join('\n');

  assert.equal(normalizeAgentMarkdown(source), source);
});
