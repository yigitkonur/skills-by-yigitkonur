# Server Configuration

Complete reference for configuring `MCPServer` from the `mcp-use` library — identity, networking, CORS, security, middleware, logging, and environment variables.

---

## 1. ServerConfig Interface

`MCPServer` accepts a `ServerConfig` object at construction time. All fields except `name` and `version` are optional.

| Property | Type | Default | Description |
|---|---|---|---|
| `name` | `string` | — (required) | Server identifier used in MCP protocol handshake |
| `version` | `string` | — (required) | Semantic version reported to clients |
| `title` | `string` | value of `name` | Display name shown in Inspector / MCP clients |
| `description` | `string` | `undefined` | Server description shown during discovery |
| `websiteUrl` | `string` | `undefined` | Public website URL |
| `favicon` | `string` | `undefined` | Favicon path relative to `public/` directory |
| `icons` | `Array<{ src, mimeType, sizes }>` | `undefined` | Icon definitions for client UIs |
| `host` | `string` | `'localhost'` | Bind hostname for the HTTP server |
| `baseUrl` | `string` | `http://{host}:{port}` | Public URL for widget/asset URLs; also read from `MCP_URL` env var |
| `cors` | `CorsConfig` | permissive (`origin: '*'`) | CORS configuration |
| `allowedOrigins` | `string[]` | `undefined` | Enables Host header validation (DNS rebinding protection) |
| `stateless` | `boolean` | auto-detected | Force stateful (`false`) or stateless (`true`) transport mode |
| `sessionIdleTimeoutMs` | `number` | `86400000` (1 day) | Idle session timeout in milliseconds |
| `sessionStore` | `SessionStore` | `InMemorySessionStore` | Pluggable session storage backend |
| `streamManager` | `StreamManager` | `InMemoryStreamManager` | SSE stream manager for push notifications |
| `oauth` | `OAuthProvider` | `undefined` | OAuth provider for authentication |

---

## 2. Server Identity

Identity fields control how your server appears in MCP clients and the Inspector UI.

```typescript
import { MCPServer } from 'mcp-use/server'

const server = new MCPServer({
  name: 'weather-api',
  version: '2.1.0',
  title: 'Weather API Server',
  description: 'Real-time weather data for any location',
  websiteUrl: 'https://weather-api.example.com',
  favicon: 'favicon.ico',
  icons: [{ src: 'icon.svg', mimeType: 'image/svg+xml', sizes: ['512x512'] }],
})
```

- `title` defaults to `name` if omitted — set it for a friendlier display name.
- `favicon` is resolved relative to the `public/` directory.

---

## 3. Network Configuration

### Port Resolution Order

The listening port uses this precedence (first match wins):

1. `server.listen(port)` argument → 2. `--port` CLI flag → 3. `PORT` env var → 4. `3000`

### Base URL Resolution Order

1. `baseUrl` config property → 2. `MCP_URL` env var → 3. `http://{host}:{port}`

```typescript
import { MCPServer } from 'mcp-use/server'

const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  host: '0.0.0.0',                       // bind to all interfaces
  baseUrl: 'https://mcp.example.com',     // public URL for widget assets
})

await server.listen(8080)
```

---

## 4. CORS Configuration

By default, CORS is permissive (`origin: '*'`). The `cors` option **replaces** the default entirely — there is no merge. Include all headers your clients need.

### Default CORS (when `cors` is not set)

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
import { MCPServer } from 'mcp-use/server'

const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  cors: {
    origin: ['https://app.example.com', 'https://admin.example.com'],
    allowMethods: ['GET', 'POST', 'DELETE', 'OPTIONS'],
    allowHeaders: ['Content-Type', 'Authorization', 'mcp-protocol-version'],
    exposeHeaders: ['mcp-session-id'],
  },
})
```

---

## 5. DNS Rebinding Protection

`allowedOrigins` enables Host header validation against DNS rebinding attacks.

| `allowedOrigins` Value | Behavior |
|---|---|
| Not set / `undefined` | No host validation — all `Host` values accepted |
| `[]` (empty array) | No host validation (same as not set) |
| `['https://myapp.com']` | Host header must match a configured hostname |

```typescript
import { MCPServer } from 'mcp-use/server'

const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  allowedOrigins: [
    'https://myapp.com',
    'https://app.myapp.com',
  ],
})

// Or load from environment
const flexServer = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  allowedOrigins: process.env.ALLOWED_ORIGINS?.split(','),
})
```

Accepts full URLs (e.g. `"https://myapp.com"`) and normalizes them to hostnames. Applies globally to all routes.

---

## 6. Content Security Policy

CSP controls which domains widgets can fetch from, load scripts/styles from, and embed. Widgets run in sandboxed iframes — CSP must explicitly allow external resources.

When `baseUrl` is set, your server domain is auto-injected into each widget's `connectDomains`, `resourceDomains`, and `baseUriDomains`.

### Per-Widget CSP

```typescript
import { WidgetMetadata } from 'mcp-use/server'

export const widgetMetadata: WidgetMetadata = {
  description: 'Display weather',
  props: propSchema,
  metadata: {
    csp: {
      connectDomains: ['https://api.weather.com'],
      resourceDomains: ['https://cdn.weather.com'],
      baseUriDomains: ['https://myserver.com'],
      frameDomains: ['https://trusted-embed.com'],
      redirectDomains: ['https://oauth.provider.com'],
    },
  },
}
```

| CSP Field | Description |
|---|---|
| `connectDomains` | Domains for `fetch`, XHR, WebSocket |
| `resourceDomains` | Domains for scripts, styles, images |
| `baseUriDomains` | Domains for base URI |
| `frameDomains` | Domains for iframe embeds |
| `redirectDomains` | Domains for redirects |
| `scriptDirectives` | Custom script CSP directives |
| `styleDirectives` | Custom style CSP directives |

Use the `CSP_URLS` env var to add extra domains globally without per-widget config.

---

## 7. Middleware Integration

`MCPServer` supports Hono and Express middleware. Express middleware is auto-detected by function signature and adapted.

### Hono Middleware

```typescript
import { MCPServer } from 'mcp-use/server'

const server = new MCPServer({ name: 'my-server', version: '1.0.0' })

server.use(async (c, next) => {
  const start = Date.now()
  await next()
  console.log(`${c.req.method} ${c.req.path} — ${Date.now() - start}ms`)
})
```

### Express Middleware

```typescript
import { MCPServer } from 'mcp-use/server'
import morgan from 'morgan'
import rateLimit from 'express-rate-limit'

const server = new MCPServer({ name: 'my-server', version: '1.0.0' })
server.use(morgan('combined'))
server.use(rateLimit({ windowMs: 15 * 60 * 1000, max: 100 }))
```

### Route-Scoped Middleware

```typescript
server.use('/api/admin/*', async (c, next) => {
  const apiKey = c.req.header('x-api-key')
  if (!apiKey || apiKey !== process.env.API_KEY) {
    return c.json({ error: 'Unauthorized' }, 401)
  }
  await next()
})
```

Both types can be mixed in the same `use()` call:

```typescript
server.use(morgan('dev'), async (c, next) => {
  await next()
})
```

---

## 8. Custom HTTP Routes

Add custom endpoints alongside MCP protocol routes. Register before calling `listen()`.

```typescript
import { MCPServer } from 'mcp-use/server'

const server = new MCPServer({ name: 'my-server', version: '1.0.0' })

server.get('/health', (c) => c.json({ status: 'ok' }))

server.post('/webhooks/github', async (c) => {
  const body = await c.req.json()
  return c.json({ received: true })
})

await server.listen()
```

MCP protocol routes (`/mcp`, `/mcp-use/widgets/*`, `/inspector`) are registered internally — do not overwrite them.

---

## 9. Logging Configuration

mcp-use uses a built-in `SimpleConsoleLogger` (since v1.12.0) that works in both Node.js and browser environments.

### Logger API

```typescript
import { Logger } from 'mcp-use/server'

Logger.configure({ level: 'debug', format: 'detailed' })

Logger.setDebug(0) // Production (info level)
Logger.setDebug(1) // Debug mode
Logger.setDebug(2) // Verbose (full JSON-RPC request/response logging)
```

### Log Levels

| Level | Use Case |
|---|---|
| `error` | Error conditions needing attention |
| `warn` | Potential issues |
| `info` | General informational messages (default) |
| `http` | HTTP request/response logging |
| `verbose` | Verbose informational messages |
| `debug` | Detailed debugging information |
| `silly` | Very detailed debug information |

### Log Formats

- **Minimal** (default): `14:23:45 [mcp-use] info: Server mounted at /mcp`
- **Detailed**: `14:23:45 [mcp-use] INFO: Server mounted at /mcp (Streamable HTTP Transport)`

### Custom Logger Instances

```typescript
import { Logger } from 'mcp-use/server'

const logger = Logger.get('my-component')
logger.info('Component initialized')
logger.debug('Processing request', { userId: 123 })
logger.error('Operation failed', new Error('timeout'))
```

---

## 10. Environment Variables

| Variable | Effect | Default |
|---|---|---|
| `PORT` | HTTP server port | `3000` |
| `HOST` | Bind hostname | `localhost` |
| `MCP_URL` | Full public base URL (widget/asset URLs, CSP) | `http://{HOST}:{PORT}` |
| `NODE_ENV` | `production` disables dev features (inspector, type generation) | — |
| `DEBUG` | Verbose debug logging (`1` = debug, `2` = verbose) | — |
| `CSP_URLS` | Comma-separated extra URLs added to widget CSP | — |

OAuth providers read additional zero-config env vars — see the OAuth documentation.

---

## 11. Complete Production Config Example

```typescript
import { MCPServer, RedisSessionStore, RedisStreamManager, Logger } from 'mcp-use/server'
import { createClient } from 'redis'

Logger.configure({ level: 'info', format: 'minimal' })

const redis = createClient({ url: process.env.REDIS_URL })
const pubSubRedis = redis.duplicate()
await redis.connect()
await pubSubRedis.connect()

const server = new MCPServer({
  name: 'production-server',
  version: '1.0.0',
  title: 'My Production Server',
  description: 'Production MCP server with full configuration',
  websiteUrl: 'https://myapp.com',
  favicon: 'favicon.ico',
  host: '0.0.0.0',
  baseUrl: process.env.MCP_URL,
  cors: {
    origin: ['https://myapp.com', 'https://admin.myapp.com'],
    allowMethods: ['GET', 'POST', 'DELETE', 'OPTIONS'],
    allowHeaders: ['Content-Type', 'Accept', 'Authorization', 'mcp-protocol-version', 'mcp-session-id'],
    exposeHeaders: ['mcp-session-id'],
  },
  allowedOrigins: process.env.ALLOWED_ORIGINS?.split(','),
  sessionIdleTimeoutMs: 3600000,
  sessionStore: new RedisSessionStore({ client: redis, prefix: 'mcp:session:', defaultTTL: 3600 }),
  streamManager: new RedisStreamManager({
    client: redis,
    pubSubClient: pubSubRedis,
    prefix: 'mcp:stream:',
    heartbeatInterval: 10,
  }),
})

server.get('/health', (c) => c.json({ status: 'ok', version: '1.0.0' }))

server.use('/api/admin/*', async (c, next) => {
  if (c.req.header('x-api-key') !== process.env.API_KEY) {
    return c.json({ error: 'Unauthorized' }, 401)
  }
  await next()
})

await server.listen()
```
