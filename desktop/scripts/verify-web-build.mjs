import { readdirSync, readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';

const cssDir = resolve(import.meta.dirname, '../../astro-blog/dist/client/_astro');
const workbenchCss = readdirSync(cssDir)
  .filter(name => name.startsWith('WorkbenchView.') && name.endsWith('.css'))
  .map(name => readFileSync(join(cssDir, name), 'utf8'))
  .join('\n');

if (/body\.app-chromeless\s*\{[^}]*display\s*:\s*none/i.test(workbenchCss)) {
  throw new Error('Scoped CSS incorrectly hides body.app-chromeless');
}

console.log('Workbench CSS scope check passed');
