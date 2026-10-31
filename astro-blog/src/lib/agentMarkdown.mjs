const FENCED_CODE_PATTERN = /(```[\s\S]*?```|~~~[\s\S]*?~~~)/g;

function normalizeMarkdownBlock(content) {
  let normalized = content.replace(/\r\n?/g, '\n');

  // Models sometimes concatenate an ATX heading and its table header line.
  normalized = normalized.replace(
    /^(#{1,6})[ \t]*([^|\n]+?)[ \t]*(\|[^\n]*\|)[ \t]*\\?[ \t]*$/gm,
    (_match, marks, title, headerRow) => `${marks} ${title.trim()}\n${headerRow.trim()}`,
  );

  // CommonMark requires whitespace after the heading marker.
  normalized = normalized.replace(/^(#{1,6})(?=[^\s#])/gm, '$1 ');

  // Remove backslash continuations after table rows.
  normalized = normalized.replace(/^([^\n]*\|)\\+[ \t]*$/gm, '$1');

  // Remove a stray escape before table delimiter rows such as \|---|---|.
  normalized = normalized.replace(/^\\+(?=\|?[ \t:|-]+$)/gm, '');

  return normalized;
}

export function normalizeAgentMarkdown(content) {
  if (!content) return '';
  return String(content)
    .split(FENCED_CODE_PATTERN)
    .map((block, index) => (index % 2 === 1 ? block : normalizeMarkdownBlock(block)))
    .join('');
}

export function wrapMarkdownTables(html) {
  return String(html || '').replace(
    /<table(?:\s[^>]*)?>[\s\S]*?<\/table>/gi,
    table => `<div class="markdown-table-wrap" role="region" aria-label="数据表格" tabindex="0">${table}</div>`,
  );
}
