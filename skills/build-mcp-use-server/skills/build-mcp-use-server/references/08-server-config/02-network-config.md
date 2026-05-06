# Network config — host, port, baseUrl

Three independent knobs:

| Knob | Controls | Used by |
|---|---|---|
| `host` | Bind hostname (which interface the socket binds to) | `server.listen()` |
| Port | TCP port the socket binds to | `server.listen(port?)` |
| `baseUrl` | Public URL printed in widget assets, OAuth metadata, and CSP | Widget / asset URL generation |

`host` and port apply only to HTTP transport. `baseUrl` applies whenever clients fetch widget HTML, JS, or icons.

## Port resolution order

First match wins:

1. `server.listen(port)` argument
2. `--port` CLI flag (e.g. `node dist/server.js --port 8080`)
3. `PORT` env var
4. Default: `3000`

```typescript
await server.listen(3000)        // explicit
await server.listen()             // falls through to CLI / env / default
```

## Host resolution order

1. `host` constructor option at construction time
2. `HOST` env var during `listen()` if present
3. Default: `'localhost'`

```typescript
const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  host: '0.0.0.0',  // bind to all interfaces — required for Docker/containers
})
```

Bind to `localhost` for local dev. Bind to `0.0.0.0` only when you need external reachability (containers, LAN). Because `listen()` reads `HOST`, deployment env can override the constructor host.

## Base URL resolution order

1. `baseUrl` constructor option
2. `MCP_URL` env var
3. `http://{host}:{port}` (auto-generated)

```typescript
const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  host: '0.0.0.0',
  baseUrl: 'https://mcp.example.com',  // public URL behind reverse proxy
})
```

Set `baseUrl` explicitly when:

- The server runs behind a reverse proxy and `host:port` is not the public origin.
- Widgets or OAuth flows must reference a public hostname.
- TLS is terminated upstream (the server speaks HTTP but the public URL is HTTPS).

When `baseUrl` is set, the origin is auto-injected into each widget's CSP `connectDomains`, `resourceDomains`, and `baseUriDomains` (see `18-mcp-apps/server-surface/05-csp-metadata.md`).

## Serverless override

On Vercel, Cloudflare Workers, Supabase Edge, and Deno Deploy, the platform owns the listen socket — `host` and port are ignored. Set `baseUrl` (or `MCP_URL` env var) to the public URL the platform assigns. See `09-transports/05-serverless-handlers.md`.

## Environment variables

| Variable | Effect |
|---|---|
| `PORT` | HTTP server port |
| `HOST` | Bind hostname |
| `MCP_URL` | Full public base URL when `baseUrl` config is not set |
