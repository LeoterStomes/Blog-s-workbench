const ARTIFACT_PRODUCING_TOOLS = new Set([
  'export_file',
  'make_mindmap',
  'generate_presentation',
  'generate_weekly_video',
]);

export function artifactFromToolResult(result, toolName, fallbackFormat = '') {
  if (!result || typeof result !== 'object') return null;

  const hasDownloadUrl = Boolean(result.downloadUrl || result.download_url);
  const explicitlyMarked = result.artifact === true
    || result.isArtifact === true
    || result.type === 'artifact'
    || result.kind === 'artifact';
  if (!ARTIFACT_PRODUCING_TOOLS.has(toolName) && !hasDownloadUrl && !explicitlyMarked) {
    return null;
  }

  const url = result.url || result.downloadUrl || result.download_url;
  const filename = result.filename
    || result.fileName
    || (url ? String(url).split('/').pop() : '');
  const format = result.format
    || fallbackFormat
    || (filename && filename.includes('.') ? filename.split('.').pop() : 'file');
  if (!url || !filename) return null;
  return { url: String(url), filename: String(filename), format: String(format) };
}
