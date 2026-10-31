import { readdirSync, readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';

const cssDir = resolve(import.meta.dirname, '../../astro-blog/dist/client/_astro');
const workbenchCss = readdirSync(cssDir)
  .filter(name => name.startsWith('WorkbenchView.') && name.endsWith('.css'))
  .map(name => readFileSync(join(cssDir, name), 'utf8'))
  .join('\n');
const workbenchJs = readdirSync(cssDir)
  .filter(name => name.startsWith('WorkbenchView.') && name.endsWith('.js'))
  .map(name => readFileSync(join(cssDir, name), 'utf8'))
  .join('\n');
const allClientJs = readdirSync(cssDir)
  .filter(name => name.endsWith('.js'))
  .map(name => readFileSync(join(cssDir, name), 'utf8'))
  .join('\n');
const allClientCss = readdirSync(cssDir)
  .filter(name => name.endsWith('.css'))
  .map(name => readFileSync(join(cssDir, name), 'utf8'))
  .join('\n');

if (/body\.app-chromeless\s*\{[^}]*display\s*:\s*none/i.test(workbenchCss)) {
  throw new Error('Scoped CSS incorrectly hides body.app-chromeless');
}

if (/\.workbench(?:\s|\[|:)[^{]*\{[^}]*\bzoom\s*:/i.test(workbenchCss)) {
  throw new Error('Font scaling must not zoom the entire workbench layout');
}

if (!/font-size\s*:\s*[^;]*var\(--wb-font-scale\)/i.test(workbenchCss)) {
  throw new Error('Workbench font sizes must use the --wb-font-scale token');
}

if (!/\.workbench-main(?:\s|\[|:)[^{]*\{[^}]*min-height\s*:\s*0/i.test(workbenchCss)) {
  throw new Error('Workbench main column must be allowed to shrink to the layout height');
}

if (!/\.task-feed(?:\s|\[|:)[^{]*\{[^}]*overscroll-behavior\s*:\s*contain/i.test(workbenchCss)) {
  throw new Error('Task feed must own wheel scrolling inside the chat area');
}

if (workbenchJs.includes('event-thinking')) {
  throw new Error('Thinking events must not reuse the generic task-event wrapper');
}

if (!workbenchJs.includes('artifact-html-frame') || !workbenchJs.includes('allow-downloads')) {
  throw new Error('Artifact HTML preview must render inside the dedicated sandboxed frame');
}

if (workbenchJs.includes('allow-same-origin')) {
  throw new Error('Untrusted artifact frames must not receive same-origin privileges');
}

if (!workbenchJs.includes('workflow-overlay') || !workbenchJs.includes('batch_id')) {
  throw new Error('Workflow canvas and correlated tool batches must be present in the built renderer');
}

if (!/\.artifact-preview(?:\s|\[|:)[^{]*\{[^}]*flex-shrink\s*:\s*0/i.test(workbenchCss)) {
  throw new Error('Artifact preview must not collapse over the context footnote in short windows');
}

if (!/\.artifact-content(?:\s|\[|:)[^{]*\{[^}]*font-size\s*:\s*calc\([^;]*12px\)/i.test(workbenchCss)) {
  throw new Error('Task output text must use the enlarged reading size');
}

if (!allClientJs.includes('markdown-table-wrap')) {
  throw new Error('Agent Markdown tables must render inside a responsive scroll container');
}

if (!workbenchJs.includes('workflow-plan-progress') || !workbenchJs.includes('AGENT PLAN')) {
  throw new Error('Workflow UI must render the Agent plan with plan progress');
}

if (!/workflow-card-scan/i.test(workbenchCss) || !/workflow-rail-flow/i.test(workbenchCss)) {
  throw new Error('Running Agent plan nodes must retain their status animations');
}

if (!workbenchJs.includes('confirmation_required') || !workbenchJs.includes('task-state')) {
  throw new Error('Workbench build must include durable task state and write confirmations');
}

if (!allClientJs.includes('content-adaptive-color') || !allClientCss.includes('data-content-surface')) {
  throw new Error('Agent and article HTML must keep readable inline-color fallbacks');
}

if (!/\[data-content-surface=dark\][^{}]*:where\(th,td\)[^{}]*\{[^}]*background-color:transparent/i.test(allClientCss)) {
  throw new Error('Dark table rows must let dark surfaces show through their header and data cells');
}

console.log('Workbench CSS scope check passed');
