import { createReadStream, existsSync, statSync } from 'node:fs';
import { createServer, request as httpRequest } from 'node:http';
import { extname, join, normalize, resolve, sep } from 'node:path';

const MIME_TYPES = {
  '.css': 'text/css; charset=utf-8',
  '.gif': 'image/gif',
  '.html': 'text/html; charset=utf-8',
  '.ico': 'image/x-icon',
  '.jpeg': 'image/jpeg',
  '.jpg': 'image/jpeg',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.map': 'application/json; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.mp3': 'audio/mpeg',
  '.mp4': 'video/mp4',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
  '.txt': 'text/plain; charset=utf-8',
  '.webp': 'image/webp',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
};

function proxyRequest(req, res, targetPort, pathname) {
  const headers = { ...req.headers, host: `127.0.0.1:${targetPort}` };
  const proxy = httpRequest({
    hostname: '127.0.0.1',
    port: targetPort,
    path: pathname,
    method: req.method,
    headers,
  }, upstream => {
    res.writeHead(upstream.statusCode || 502, upstream.headers);
    upstream.pipe(res);
  });
  proxy.on('error', error => {
    res.writeHead(502, { 'Content-Type': 'application/json; charset=utf-8' });
    res.end(JSON.stringify({ detail: `本地 Agent Gateway 连接失败：${error.message}` }));
  });
  req.pipe(proxy);
}

function resolveStaticFile(root, pathname) {
  const decoded = decodeURIComponent(pathname);
  const trimmed = decoded.replace(/^\/+/, '');
  const relative = extname(trimmed) ? trimmed : join(trimmed, 'index.html');
  const resolved = resolve(root, normalize(relative));
  const expectedRoot = resolve(root) + sep;
  if (resolved !== resolve(root) && !resolved.startsWith(expectedRoot)) return null;
  return resolved;
}

export function startWorkbenchServer({ root, backendPort, port = 4410 }) {
  if (!existsSync(root)) throw new Error(`前端构建目录不存在：${root}`);

  const server = createServer((req, res) => {
    const url = new URL(req.url || '/', 'http://127.0.0.1');
    const pathname = url.pathname;

    if (pathname.startsWith('/api/') || pathname.startsWith('/uploads/')) {
      proxyRequest(req, res, backendPort, req.url || pathname);
      return;
    }

    const filePath = resolveStaticFile(root, pathname);
    if (!filePath || !existsSync(filePath) || !statSync(filePath).isFile()) {
      res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end('Not found');
      return;
    }

    const headers = {
      'Content-Type': MIME_TYPES[extname(filePath).toLowerCase()] || 'application/octet-stream',
      'Cache-Control': extname(filePath) === '.html' ? 'no-cache' : 'public, max-age=3600',
    };
    if (extname(filePath).toLowerCase() === '.html') {
      headers['Content-Security-Policy'] = [
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline'",
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data: blob: https:",
        "font-src 'self' data:",
        "connect-src 'self'",
        "media-src 'self' blob: https:",
        "frame-src 'self'",
        "object-src 'none'",
        "base-uri 'self'",
        "frame-ancestors 'self'",
      ].join('; ');
    }
    res.writeHead(200, headers);
    createReadStream(filePath).pipe(res);
  });

  return new Promise((resolveServer, reject) => {
    server.once('error', reject);
    server.listen(port, '127.0.0.1', () => {
      const address = server.address();
      resolveServer({
        url: `http://127.0.0.1:${address.port}`,
        close: () => new Promise(resolveClose => server.close(resolveClose)),
      });
    });
  });
}
