import assert from 'node:assert/strict';
import test from 'node:test';

test('classifies dark and light inline surfaces', async () => {
  const { classifyContentSurface } = await import(
    '../../astro-blog/src/lib/contentContrast.mjs'
  );

  assert.equal(classifyContentSurface('#0f172a'), 'dark');
  assert.equal(classifyContentSurface('rgb(17, 24, 39)'), 'dark');
  assert.equal(classifyContentSurface('#ffffff'), 'light');
  assert.equal(classifyContentSurface('rgba(255, 255, 255, 0.7)'), 'light');
  assert.equal(classifyContentSurface('transparent'), null);
});

test('chooses readable fallback colors for low contrast combinations', async () => {
  const { chooseReadableColor } = await import(
    '../../astro-blog/src/lib/contentContrast.mjs'
  );

  assert.equal(chooseReadableColor('#ffffff', '#e2e8f0'), '#334155');
  assert.equal(chooseReadableColor('#0f172a', '#111827'), '#e8eef8');
  assert.equal(chooseReadableColor('#ffffff', '#1d4ed8'), '#1d4ed8');
});

test('theme adaptive colors keep accent in dark mode and use dark text in light mode', async () => {
  const { adaptiveColorPair } = await import(
    '../../astro-blog/src/lib/contentContrast.mjs'
  );

  assert.deepEqual(adaptiveColorPair('#e2e8f0'), {
    light: '#334155',
    dark: '#e2e8f0',
  });
  assert.deepEqual(adaptiveColorPair('#0f172a'), {
    light: '#0f172a',
    dark: '#e8eef8',
  });
});
