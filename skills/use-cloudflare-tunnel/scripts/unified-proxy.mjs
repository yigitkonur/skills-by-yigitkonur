#!/usr/bin/env node
// scripts/unified-proxy.mjs
// Lightweight reverse proxy: serves static SPA files + proxies API prefixes to backend
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

function parseArgs() {
  const args = process.argv.slice(2);
  const options = {
    port: 8099,
    host: '0.0.0.0',
    staticDir: '',
    apiHost: '127.0.0.1',
    apiPort: 55721,
    apiPrefixes: ['/api/', '/auth/', '/rest/', '/functions/'],
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === '--port' || arg === '-p') options.port = parseInt(args[++i], 10);
    else if (arg === '--static' || arg === '-s') options.staticDir = path.resolve(args[++i]);
    else if (arg === '--api-port') options.apiPort = parseInt(args[++i], 10);
    else if (arg === '--api-host') options.apiHost = args[++i];
    else if (arg === '--api-prefixes') options.apiPrefixes = args[++i].split(',').map(s => s.trim());
    else if (arg === '--help' || arg === '-h') {
      console.log(`
Usage: node unified-proxy.mjs [options]

Options:
  -p, --port <port>          Port for unified proxy to listen on (default: 8099)
  -s, --static <dir>         Directory containing static web build (HTML/JS/CSS)
      --api-port <port>      Local backend API port to proxy to (default: 55721)
      --api-host <host>      Local backend API host (default: 127.0.0.1)
      --api-prefixes <list>  Comma-separated URL prefixes to route to API (default: /api/,/auth/,/rest/,/functions/)
`);
      process.exit(0);
    }
  }
  return options;
}

const opts = parseArgs();

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.mjs': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.webp': 'image/webp',
  '.ttf': 'font/ttf',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
};

function serveFile(res, filePath, contentType) {
  try {
    const data = fs.readFileSync(filePath);
    res.writeHead(200, {
      'Content-Type': contentType,
      'Access-Control-Allow-Origin': '*',
      'Cache-Control': 'no-cache',
    });
    res.end(data);
  } catch (err) {
    res.writeHead(500, { 'Content-Type': 'text/plain' });
    res.end('Internal Server Error: ' + err.message);
  }
}

const server = http.createServer((req, res) => {
  // Always handle CORS preflight
  if (req.method === 'OPTIONS') {
    res.writeHead(204, {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, PATCH, OPTIONS',
      'Access-Control-Allow-Headers': '*',
    });
    res.end();
    return;
  }

  const parsedUrl = new URL(req.url, `http://${req.headers.host || '127.0.0.1'}`);
  const pathname = parsedUrl.pathname;

  // 1. Check if route matches backend API prefixes
  const isApi = opts.apiPrefixes.some(prefix => pathname.startsWith(prefix));
  if (isApi) {
    const proxyReq = http.request(
      {
        host: opts.apiHost,
        port: opts.apiPort,
        path: req.url,
        method: req.method,
        headers: {
          ...req.headers,
          host: `${opts.apiHost}:${opts.apiPort}`,
        },
      },
      (proxyRes) => {
        res.writeHead(proxyRes.statusCode, {
          ...proxyRes.headers,
          'access-control-allow-origin': '*',
          'access-control-allow-methods': 'GET, POST, PUT, DELETE, PATCH, OPTIONS',
          'access-control-allow-headers': '*',
        });
        proxyRes.pipe(res);
      }
    );

    proxyReq.on('error', (err) => {
      console.error(`[Proxy Error] API target unavailable for ${pathname}:`, err.message);
      res.writeHead(502, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: `Backend API unavailable at ${opts.apiHost}:${opts.apiPort}` }));
    });

    req.pipe(proxyReq);
    return;
  }

  // 2. Static file serving (if static directory configured)
  if (opts.staticDir && fs.existsSync(opts.staticDir)) {
    const safePath = path.normalize(pathname).replace(/^(\.\.[\/\\])+/, '');
    const filePath = path.join(opts.staticDir, safePath);

    // Exact static file match
    if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
      const ext = path.extname(filePath).toLowerCase();
      const contentType = MIME_TYPES[ext] || 'application/octet-stream';
      return serveFile(res, filePath, contentType);
    }

    // Static asset with file extension that was not found
    if (path.extname(pathname)) {
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      res.end('Static Asset Not Found');
      return;
    }

    // SPA Fallback: serve index.html for client-side navigation routes
    const indexPath = path.join(opts.staticDir, 'index.html');
    if (fs.existsSync(indexPath)) {
      return serveFile(res, indexPath, 'text/html; charset=utf-8');
    }
  }

  res.writeHead(404, { 'Content-Type': 'text/plain' });
  res.end(`Not Found. Neither API route matching [${opts.apiPrefixes.join(', ')}] nor static asset found.`);
});

server.listen(opts.port, opts.host, () => {
  console.log(`[Unified Proxy] Listening on http://${opts.host}:${opts.port}`);
  if (opts.staticDir) console.log(`[Unified Proxy] Serving static SPA from: ${opts.staticDir}`);
  console.log(`[Unified Proxy] Forwarding API prefixes [${opts.apiPrefixes.join(', ')}] -> http://${opts.apiHost}:${opts.apiPort}`);
});
