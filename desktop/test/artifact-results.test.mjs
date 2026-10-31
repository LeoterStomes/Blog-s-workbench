import assert from 'node:assert/strict';
import test from 'node:test';

test('article lookups do not become downloadable artifacts', async () => {
  const { artifactFromToolResult } = await import(
    '../../astro-blog/src/lib/artifactResults.mjs'
  );
  const article = {
    id: 'da431f71-article',
    title: 'Python继承完全指南',
    url: '/blog/da431f71-article',
  };

  assert.equal(artifactFromToolResult(article, 'get_article'), null);
  assert.equal(artifactFromToolResult(article, 'search_articles'), null);
  assert.equal(artifactFromToolResult(article, 'list_articles'), null);
});

test('known document-producing tools still create artifacts', async () => {
  const { artifactFromToolResult } = await import(
    '../../astro-blog/src/lib/artifactResults.mjs'
  );

  assert.deepEqual(
    artifactFromToolResult({
      url: '/uploads/export/report.pdf',
      filename: 'report.pdf',
    }, 'export_file'),
    {
      url: '/uploads/export/report.pdf',
      filename: 'report.pdf',
      format: 'pdf',
    },
  );

  assert.equal(
    artifactFromToolResult({
      url: '/uploads/export/slides.pptx',
      filename: 'slides.pptx',
    }, 'generate_presentation')?.format,
    'pptx',
  );
});

test('explicit artifact metadata works for future tools', async () => {
  const { artifactFromToolResult } = await import(
    '../../astro-blog/src/lib/artifactResults.mjs'
  );

  assert.equal(
    artifactFromToolResult({
      artifact: true,
      url: '/uploads/export/result.zip',
      filename: 'result.zip',
    }, 'future_tool')?.format,
    'zip',
  );
});
