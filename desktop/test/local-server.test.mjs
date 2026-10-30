import assert from 'node:assert/strict';
import { mkdtemp, mkdir, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { startWorkbenchServer } from '../local-server.mjs';

test('serves workbench HTML with a content security policy', async () => {
  const root = await mkdtemp(join(tmpdir(), 'ray-workbench-'));
  await mkdir(join(root, 'workbench'));
  await writeFile(join(root, 'workbench', 'index.html'), '<h1>workbench</h1>', 'utf8');

  const server = await startWorkbenchServer({
    root,
    backendPort: 9,
    port: 0,
  });

  try {
    const response = await fetch(`${server.url}/workbench`);
    assert.equal(response.status, 200);
    const csp = response.headers.get('content-security-policy') || '';
    assert.match(csp, /default-src 'self'/);
    assert.match(csp, /frame-src 'self'/);
    assert.match(csp, /frame-ancestors 'self'/);
    assert.equal(await response.text(), '<h1>workbench</h1>');
  } finally {
    await server.close();
    await rm(root, { recursive: true, force: true });
  }
});

test('rejects missing static files', async () => {
  const root = await mkdtemp(join(tmpdir(), 'ray-workbench-'));
  const server = await startWorkbenchServer({
    root,
    backendPort: 9,
    port: 0,
  });

  try {
    const response = await fetch(`${server.url}/missing`);
    assert.equal(response.status, 404);
  } finally {
    await server.close();
    await rm(root, { recursive: true, force: true });
  }
});
