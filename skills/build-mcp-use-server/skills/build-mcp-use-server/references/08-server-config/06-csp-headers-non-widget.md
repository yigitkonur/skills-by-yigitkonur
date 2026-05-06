# CSP for non-widget HTTP responses

This file covers Content-Security-Policy on **plain HTTP responses** from custom routes (`server.get`, `server.post`, etc.).

For **widget CSP** (`connectDomains`, `resourceDomains`, `frameDomains` in `WidgetMetadata`), see `18-mcp-apps/server-surface/05-csp-metadata.md`. The two are independent.

## When you need CSP on plain routes

| Custom route returns | CSP needed? |
|---|---|
| JSON (e.g. `/health`, `/api/*`) | No — JSON responses are not rendered as documents |
| HTML (e.g. a status page, an OAuth consent screen) | Yes |
| Static assets (JS, CSS, images) | Optional — usually controlled at CDN/edge |

`/mcp` itself returns JSON-RPC. No CSP needed there.

## Setting CSP on custom HTML routes

Use Hono middleware to set headers per route:

```typescript
import { MCPServer } from 'mcp-use/server'

const server = new MCPServer({ name: 'my-server', version: '1.0.0' })

server.get('/status', (c) => {
  c.header('Content-Security-Policy', [
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data:",
    "connect-src 'self'",
  ].join('; '))
  return c.html('<html><body><h1>Status: OK</h1></body></html>')
})
```

## Common policies

| Use case | Policy |
|---|---|
| Static status page | `default-src 'self'` |
| Page with inline styles | `default-src 'self'; style-src 'self' 'unsafe-inline'` |
| OAuth consent page calling external IdP | `default-src 'self'; connect-src 'self' https://idp.example.com` |

## Global CSP via middleware

To apply the same CSP to a custom HTML route group:

```typescript
server.use('/status/*', async (c, next) => {
  await next()
  if (c.res.headers.get('content-type')?.includes('text/html')) {
    c.res.headers.set('Content-Security-Policy', "default-src 'self'")
  }
})
```

Do not blanket-apply CSP to `/mcp` or `/mcp-use/widgets/*` — those routes have their own policy logic.

## Hardening headers

CSP pairs with other security headers. Scope iframe-blocking headers to custom pages, not MCP/widget routes:

```typescript
server.use('/status/*', async (c, next) => {
  await next()
  c.res.headers.set('X-Content-Type-Options', 'nosniff')
  c.res.headers.set('X-Frame-Options', 'DENY')
  c.res.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin')
  c.res.headers.set('Strict-Transport-Security', 'max-age=63072000; includeSubDomains')
})
```

Do not set `X-Frame-Options: DENY` on widget routes — widgets are designed to load inside iframes. Scope these headers to your custom routes only.
