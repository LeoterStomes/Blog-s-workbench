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

console.log('Workbench CSS scope check passed');
