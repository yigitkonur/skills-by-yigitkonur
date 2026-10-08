#!/usr/bin/env node
// scripts/unified-proxy.mjs
// Lightweight reverse proxy: serves static SPA files + proxies API prefixes & WebSockets to backend
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

function getCorsHeaders(req) {
  const origin = req.headers.origin || '*';
  return {
    'Access-Control-Allow-Origin': origin,
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, PATCH, OPTIONS',
    'Access-Control-Allow-Headers': req.headers['access-control-request-headers'] || '*',
    'Access-Control-Allow-Credentials': 'true',
  };
}

function serveFile(res, filePath, contentType, req) {
  try {
    const data = fs.readFileSync(filePath);
    res.writeHead(200, {
      'Content-Type': contentType,
      'Cache-Control': 'no-cache',
      ...getCorsHeaders(req),
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
    res.writeHead(204, getCorsHeaders(req));
    res.end();
    return;
  }

  // Safe URL parsing against fixed base to prevent Host header DoS crash
  const parsedUrl = new URL(req.url, 'http://127.0.0.1');
  const pathname = parsedUrl.pathname;

  // 1. Check if route matches backend API prefixes
  const isApi = opts.apiPrefixes.some(prefix => pathname.startsWith(prefix));
  if (isApi) {
    const proxyHeaders = {
      ...req.headers,
      host: `${opts.apiHost}:${opts.apiPort}`,
      'x-forwarded-for': req.headers['x-forwarded-for'] 
        ? `${req.headers['x-forwarded-for']}, ${req.socket.remoteAddress}` 
        : req.socket.remoteAddress,
      'x-forwarded-proto': req.headers['x-forwarded-proto'] || (req.socket.encrypted ? 'https' : 'http'),
      'x-forwarded-host': req.headers.host || `${opts.host}:${opts.port}`,
    };

    const proxyReq = http.request(
      {
        host: opts.apiHost,
        port: opts.apiPort,
        path: req.url,
        method: req.method,
        headers: proxyHeaders,
      },
      (proxyRes) => {
        res.writeHead(proxyRes.statusCode, {
          ...proxyRes.headers,
          ...getCorsHeaders(req),
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
    const resolvedDir = path.resolve(opts.staticDir);
    const resolvedFile = path.resolve(resolvedDir, '.' + path.normalize(pathname));

    // Strict path containment check against directory traversal
    if (!resolvedFile.startsWith(resolvedDir + path.sep) && resolvedFile !== resolvedDir) {
      res.writeHead(403, { 'Content-Type': 'text/plain' });
      res.end('Forbidden');
      return;
    }

    // Exact static file match
    if (fs.existsSync(resolvedFile) && fs.statSync(resolvedFile).isFile()) {
      const ext = path.extname(resolvedFile).toLowerCase();
      const contentType = MIME_TYPES[ext] || 'application/octet-stream';
      return serveFile(res, resolvedFile, contentType, req);
    }

    // Static asset with file extension that was not found
    if (path.extname(pathname)) {
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      res.end('Static Asset Not Found');
      return;
    }

    // SPA Fallback: serve index.html for client-side navigation routes
    const indexPath = path.join(resolvedDir, 'index.html');
    if (fs.existsSync(indexPath)) {
      return serveFile(res, indexPath, 'text/html; charset=utf-8', req);
    }
  }

  res.writeHead(404, { 'Content-Type': 'text/plain' });
  res.end(`Not Found. Neither API route matching [${opts.apiPrefixes.join(', ')}] nor static asset found.`);
});

// WebSocket Upgrade Proxying (Supabase Realtime, Vite HMR, FastAPI WebSockets)
server.on('upgrade', (req, socket, head) => {
  const parsedUrl = new URL(req.url, 'http://127.0.0.1');
  const pathname = parsedUrl.pathname;
  const isApi = opts.apiPrefixes.some(prefix => pathname.startsWith(prefix));

  if (isApi) {
    const proxyHeaders = {
      ...req.headers,
      host: `${opts.apiHost}:${opts.apiPort}`,
      'x-forwarded-for': req.headers['x-forwarded-for'] 
        ? `${req.headers['x-forwarded-for']}, ${req.socket.remoteAddress}` 
        : req.socket.remoteAddress,
      'x-forwarded-proto': req.headers['x-forwarded-proto'] || (req.socket.encrypted ? 'https' : 'http'),
      'x-forwarded-host': req.headers.host || `${opts.host}:${opts.port}`,
    };

    const proxyReq = http.request({
      host: opts.apiHost,
      port: opts.apiPort,
      path: req.url,
      method: req.method,
      headers: proxyHeaders,
    });

    proxyReq.on('upgrade', (proxyRes, proxySocket, proxyHead) => {
      let rawHeaders = `HTTP/${proxyRes.httpVersion} ${proxyRes.statusCode} ${proxyRes.statusMessage}\r\n`;
      for (let i = 0; i < proxyRes.rawHeaders.length; i += 2) {
        rawHeaders += `${proxyRes.rawHeaders[i]}: ${proxyRes.rawHeaders[i + 1]}\r\n`;
      }
      rawHeaders += '\r\n';
      socket.write(rawHeaders);
      if (proxyHead && proxyHead.length) socket.write(proxyHead);
      proxySocket.pipe(socket);
      socket.pipe(proxySocket);
    });

    proxyReq.on('error', (err) => {
      console.error(`[WebSocket Proxy Error] Failed for ${pathname}:`, err.message);
      socket.destroy();
    });

    proxyReq.end();
  } else {
    socket.destroy();
  }
});

server.listen(opts.port, opts.host, () => {
  console.log(`[Unified Proxy] Listening on http://${opts.host}:${opts.port}`);
  if (opts.staticDir) console.log(`[Unified Proxy] Serving static SPA from: ${opts.staticDir}`);
  console.log(`[Unified Proxy] Forwarding API & WebSockets [${opts.apiPrefixes.join(', ')}] -> http://${opts.apiHost}:${opts.apiPort}`);
});
