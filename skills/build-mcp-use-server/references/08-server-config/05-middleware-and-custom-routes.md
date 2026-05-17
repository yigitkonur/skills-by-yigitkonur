# Middleware and custom routes

`MCPServer` wraps a Hono app internally. Both Hono middleware (2-arg `(c, next)`) and Express middleware (3–4 arg `(req, res, next[, err])`) work — Express is auto-detected by signature and adapted.

## Two layering points

| Layer | Method | Runs on |
|---|---|---|
| HTTP layer | `server.use(path?, ...mw)` | All HTTP requests, including custom routes |
| MCP-op layer | `server.use('mcp:tools/call', ...)` | Specific MCP protocol operations |

Use the HTTP layer for cross-cutting concerns (logging, rate limiting, auth headers). Use the MCP-op layer when you need to intercept tool calls, resource reads, or prompt fetches by name.

## HTTP middleware

```typescript
import { MCPServer } from 'mcp-use/server'
import morgan from 'morgan'
import rateLimit from 'express-rate-limit'

const server = new MCPServer({ name: 'my-server', version: '1.0.0' })

// Hono — global
server.use(async (c, next) => {
  console.log(`${c.req.method} ${c.req.path}`)
  await next()
})

// Express — auto-adapted
server.use(morgan('combined'))

// Mix in one call
server.use(morgan('dev'), async (c, next) => {
  await next()
})
```

## Route-scoped middleware

```typescript
server.use('/api/admin/*', async (c, next) => {
  const apiKey = c.req.header('x-api-key')
  if (!apiKey || apiKey !== process.env.API_KEY) {
    return c.json({ error: 'Unauthorized' }, 401)
  }
  await next()
})

server.use('/api', rateLimit({ windowMs: 15 * 60 * 1000, max: 100 }))
```

## MCP-op middleware

Intercept by MCP method name. Useful for op-level audit logging, per-tool auth, or rejecting specific tool calls without modifying the tool itself.

```typescript
server.use('mcp:tools/call', async (ctx, next) => {
  console.log(`Calling tool: ${ctx.params.name}`)
  return next()
})
```

## Custom HTTP routes

Add routes alongside `/mcp` using Hono methods proxied on the instance:

```typescript
server.get('/health', (c) => c.json({ status: 'ok' }))

server.post('/webhooks/github', async (c) => {
  const body = await c.req.json()
  return c.json({ received: true })
})

server.route('/api', subApp)
```

The Hono proxy exposes HTTP routing methods such as `get`, `post`, `put`, `delete`, `patch`, `all`, `use`, and `route`.

Reserved paths — do not overwrite:

- `/mcp` (and `/sse` legacy alias)
- `/mcp-use/widgets/*`
- `/inspector`

Register custom routes **before** calling `listen()` or `getHandler()`.

## Critical: extending vs embedding

**Extending the MCP server's own routes is fine.** Use `server.use()`, `server.get()`, `server.post()`, `server.route()` to add HTTP behavior alongside `/mcp`. The MCP server owns the request lifecycle and exposes Hono's routing surface.

**Embedding the MCP server as middleware inside another framework's app is not supported.** Do not try to mount `MCPServer` inside an Express, Fastify, Next.js, or Hono app you already own. Session lifecycle, SSE plumbing, CSP injection, and OAuth callbacks all assume the MCP server owns the request lifecycle.

If you have an existing app, run the MCP server **side-by-side** on its own port instead. See `02-setup/06-add-to-existing-app.md`.

| Pattern | Supported |
|---|---|
| `server.use(...)`, `server.get(...)`, `server.route(...)` to extend MCPServer | Yes |
| Mounting MCPServer inside your Express/Fastify/Next.js app | No — run side-by-side |
| Two `MCPServer` instances in one process on different ports | Yes (rare) |
| `server.proxy(other)` to compose two MCPServer instances | Yes — see `17-advanced/` |
