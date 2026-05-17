# CORS and allowedOrigins

This file is the single source for CORS and `allowedOrigins`. Other clusters link here.

CORS and `allowedOrigins` are different mechanisms:

| Mechanism | Protects against | Where the check runs | Affects |
|---|---|---|---|
| `cors` | Cross-origin browser requests | Server CORS preflight + response headers | Browser-initiated fetch |
| `allowedOrigins` | DNS rebinding attacks | Server `Host` header validation | All HTTP requests |

Set both for any HTTP server reachable from a browser.

## CORS

By default, CORS is permissive (`origin: '*'`). Setting `cors` **replaces** the default entirely — no merge. Always include `mcp-session-id` in `exposeHeaders` if you override.

### Default values

```typescript
{
  origin: '*',
  allowMethods: ['GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowHeaders: [
    'Content-Type', 'Accept', 'Authorization',
    'mcp-protocol-version', 'mcp-session-id',
    'X-Proxy-Token', 'X-Target-URL',
  ],
  exposeHeaders: ['mcp-session-id'],
}
```

### Custom CORS

```typescript
const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  cors: {
    origin: ['https://app.example.com'],
    allowMethods: ['GET', 'POST', 'DELETE', 'OPTIONS'],
    allowHeaders: ['Content-Type', 'Authorization', 'mcp-protocol-version', 'mcp-session-id'],
    exposeHeaders: ['mcp-session-id'],
  },
})
```

## allowedOrigins

`allowedOrigins` enables `Host` header validation against DNS rebinding. Accepts full URLs and normalizes to hostnames. Applies globally to all routes.

| Value | Behavior |
|---|---|
| Not set / `undefined` | No validation — all `Host` values accepted |
| `[]` | Same as not set |
| `['https://app.example.com']` | `Host` header must match a configured hostname |

```typescript
const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  allowedOrigins: ['https://app.example.com', 'https://admin.example.com'],
})

// Or load from env:
const flexServer = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  allowedOrigins: process.env.ALLOWED_ORIGINS?.split(','),
})
```

When the `Host` header does not match, the server returns `403 Forbidden` with a JSON-RPC error.

## When `allowedOrigins` is required

| Scenario | Set it? |
|---|---|
| Public HTTP server reachable from a browser | Required |
| Localhost dev server with a browser-based client (Inspector, widget host) | Required |
| Localhost dev server with a CLI client only | Optional |
| stdio server | N/A (no HTTP transport) |
| Behind a reverse proxy with strict origin filtering | Belt-and-suspenders — set anyway |

See `04-dns-rebinding-protection.md` for the attack model and load-from-env patterns.

## Common values

| Deployment | Pattern |
|---|---|
| Reverse-proxied production | `['https://app.example.com']` |
| Multiple trusted fronts | `['https://app.example.com', 'https://admin.example.com']` |
| Internal staging | `['https://staging.example.net']` |
| Local dev with browser host | `['http://localhost:3000']` |

## Loading from env

`mcp-use` does not read `ALLOWED_ORIGINS` automatically. The canonical docs use it as an app-level convention:

| Variable | Effect when you wire it into config |
|---|---|
| `ALLOWED_ORIGINS` | Comma-separated list fed to `allowedOrigins` |
