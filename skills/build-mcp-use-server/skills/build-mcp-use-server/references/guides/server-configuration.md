# Server Configuration

Complete reference for configuring `MCPServer` from the `mcp-use` library — identity, networking, transport, session management, CORS, security, middleware, and environment variables.

---

## 1. ServerConfig Interface

`MCPServer` accepts a `ServerConfig` object at construction time. All fields except `name` and `version` are optional.

| Property | Type | Default | Description |
|---|---|---|---|
| `name` | `string` | — (required) | Server identifier used in MCP protocol handshake |
| `version` | `string` | — (required) | Semantic version reported to clients |
| `title` | `string` | `name` | Display name shown in Inspector / MCP clients |
| `description` | `string` | `undefined` | Server description shown during discovery |
| `websiteUrl` | `string` | `undefined` | Public website URL |
| `favicon` | `string` | `undefined` | Favicon path relative to `public/` directory |
| `icons` | `Array<{ src: string; mimeType?: string; sizes?: string[]; theme?: "light" \| "dark" }>` | `undefined` | Icon definitions for client UIs; `theme` distinguishes light/dark variants |
| `host` | `string` | `'localhost'` | Bind hostname |
| `baseUrl` | `string` | `http://{host}:{port}` | Public URL for widget/asset URLs; also read from `MCP_URL` env var |
| `cors` | `CorsConfig` | permissive (`origin: '*'`) | CORS configuration (replaces defaults entirely — no merge) |
| `allowedOrigins` | `string[]` | `undefined` | Enables Host header validation (DNS rebinding protection) |
| `stateless` | `boolean` | auto-detected | Force stateless or stateful transport mode |
| `sessionIdleTimeoutMs` | `number` | `86400000` (1 day) | How long idle sessions are kept in memory |
| `sessionStore` | `SessionStore` | `InMemorySessionStore` | Pluggable session storage backend |
| `streamManager` | `StreamManager` | `InMemoryStreamManager` | SSE stream manager for push notifications |
| `oauth` | `OAuthProvider` | `undefined` | OAuth provider for authentication. Use factory functions: `oauthAuth0Provider`, `oauthSupabaseProvider`, `oauthKeycloakProvider`, `oauthCustomProvider` |
| `autoCreateSessionOnInvalidId` | `boolean` | — | **Deprecated.** Server now returns 404 for invalid session IDs per MCP spec. Use `sessionStore` for persistence. |

**Port resolution order:** `listen(port)` argument → `--port` CLI flag → `PORT` env var → `3000`

**Base URL resolution order:** `baseUrl` config → `MCP_URL` env var → `http://{host}:{port}`

---

## 2. Basic Configuration Example

```typescript
import { MCPServer } from 'mcp-use/server'

const server = new MCPServer({
  // ── Required ──────────────────────────────────────────────
  name: 'my-server',
  version: '1.0.0',

  // ── Identity (shown in Inspector / MCP clients) ───────────
  title: 'My Server',                   // Display name (defaults to name)
  description: 'What this server does', // Shown during discovery
  websiteUrl: 'https://myserver.com',
  favicon: 'favicon.ico',               // Relative to public/ dir
  icons: [
    {
      src: 'icon.svg',
      mimeType: 'image/svg+xml',
      sizes: ['512x512'],
      theme: 'light',  // optional: "light" | "dark"
    }
  ],

  // ── Network ────────────────────────────────────────────────
  host: 'localhost',                    // Bind hostname (default: 'localhost')
  baseUrl: 'https://mcp.example.com',   // Public URL for widget/asset URLs
                                        // Overrides host:port; also read from MCP_URL env var

  // ── CORS ───────────────────────────────────────────────────
  cors: {
    origin: ['https://myapp.com'],
    allowMethods: ['GET', 'POST', 'OPTIONS'],
  },

  // ── DNS Rebinding Protection ───────────────────────────────
  allowedOrigins: ['https://myapp.com'],  // Enables Host header validation

  // ── Transport ─────────────────────────────────────────────
  stateless: false,                     // See "Stateless Mode" below

  // ── Sessions ──────────────────────────────────────────────
  sessionIdleTimeoutMs: 3600000,        // 1 hour (default: 86400000 = 1 day)
  sessionStore: new InMemorySessionStore(),   // See "Session Storage" below
  streamManager: new InMemoryStreamManager(), // See "Stream Manager" below

  // ── Auth ─────────────────────────────────────────────────
  // Use provider factory functions: oauthAuth0Provider, oauthSupabaseProvider,
  // oauthKeycloakProvider, oauthCustomProvider — see Authentication guide
  oauth: oauthAuth0Provider({ domain: 'my-tenant.auth0.com', audience: 'https://my-api.com' }),
})

await server.listen(3000)
```

---

## 3. Environment Variables

The server reads the following environment variables at runtime:

| Variable | Effect | Default |
|---|---|---|
| `PORT` | HTTP server port | `3000` |
| `HOST` | Bind hostname | `localhost` |
| `MCP_URL` | Full public base URL (overrides `baseUrl` config; used for widget/asset URLs) | `http://{HOST}:{PORT}` |
| `NODE_ENV` | `production` disables dev features (inspector, type generation) | — |
| `DEBUG` | Enables verbose debug logging | — |
| `CSP_URLS` | Comma-separated extra URLs added to widget CSP `resource_domains` | — |
| `REDIS_URL` | URL for Redis client (used by `RedisSessionStore` and `RedisStreamManager`) | — |
| `ALLOWED_ORIGINS` | Comma-separated list fed to the `allowedOrigins` config option | — |

OAuth providers also read zero-config env vars — see the OAuth docs for the full list.

---

## 4. Transport & Sessions

### Stateless Mode

The server supports two transport modes:

| Mode | Sessions | SSE | Best for |
|---|---|---|---|
| **Stateful** | Yes | Yes | Long-lived clients, notifications, sampling |
| **Stateless** | No | No | Edge functions, serverless, simple request/response |

**Auto-detection (default):**

- **Deno / edge runtimes** → always stateless
- **Node.js** → detected per-request from the `Accept` header:
  - `Accept: application/json, text/event-stream` → stateful (SSE)
  - `Accept: application/json` only → stateless

```typescript
// Force stateless mode (ignores Accept header)
const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  stateless: true,
})

// Force stateful mode
const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  stateless: false,
})
```

Leave `stateless` unset in most cases. Auto-detection lets the same server handle both SSE-capable and HTTP-only clients transparently.

### Session Storage

Session metadata (client capabilities, log level, etc.) is stored in a pluggable `SessionStore`. Three backends are available:

**In-memory (default)**

```typescript
import { MCPServer, InMemorySessionStore } from 'mcp-use/server'

const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  sessionStore: new InMemorySessionStore(), // default — no config needed
})
```

Sessions are lost on server restart. Suitable for single-instance production servers.

**Filesystem (development)**

```typescript
import { MCPServer, FileSystemSessionStore } from 'mcp-use/server'

const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  sessionStore: new FileSystemSessionStore({
    path: '.mcp-use/sessions.json', // default
    debounceMs: 100,                // write debounce (default: 100ms)
    maxAgeMs: 86400000,             // session TTL (default: 24h)
  }),
})
```

Sessions survive HMR reloads, so clients don't need to re-initialize when you save a file during development.

`FileSystemSessionStore` is not designed for production or distributed deployments. Use Redis for those scenarios.

**Redis (production)**

```
npm install redis
```

```typescript
import { MCPServer, RedisSessionStore } from 'mcp-use/server'
import { createClient } from 'redis'

const redis = createClient({ url: process.env.REDIS_URL })
await redis.connect()

const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  sessionStore: new RedisSessionStore({
    client: redis,
    prefix: 'mcp:session:',   // default
    defaultTTL: 3600,         // seconds (default: 3600 = 1 hour)
  }),
})
```

Sessions persist across server restarts and are shared across all instances, enabling horizontal scaling.

### Session Timeout

Control how long idle sessions are kept in memory:

```typescript
const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  sessionIdleTimeoutMs: 3600000, // 1 hour (default: 86400000 = 1 day)
})
```

---

## 5. Distributed Stream Management

The `streamManager` controls active SSE connections and is responsible for routing server-to-client push notifications. By default, SSE streams are in-memory, meaning notifications only reach clients connected to the same server instance. For distributed deployments with multiple server instances behind a load balancer, use `RedisStreamManager` to fan-out notifications via Redis Pub/Sub:

```
npm install redis
```

```typescript
import { MCPServer, RedisSessionStore, RedisStreamManager } from 'mcp-use/server'
import { createClient } from 'redis'

// Redis Pub/Sub requires a dedicated client — it cannot be shared
const redis = createClient({ url: process.env.REDIS_URL })
const pubSubRedis = redis.duplicate()

await redis.connect()
await pubSubRedis.connect()

const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  sessionStore: new RedisSessionStore({ client: redis }),
  streamManager: new RedisStreamManager({
    client: redis,             // for session availability checks
    pubSubClient: pubSubRedis, // dedicated Pub/Sub client (required)
    prefix: 'mcp:stream:',    // default
    heartbeatInterval: 10,    // seconds (default: 10)
  }),
})
```

**How it works:**

1. Client connects to Server A → SSE stream created, Server A subscribes to `mcp:stream:{sessionId}` in Redis
2. Client's next request hits Server B (load balancer)
3. Server B sends a notification → publishes to Redis channel
4. Server A receives the Redis message → pushes to the SSE stream → client gets the notification

---

## 6. CORS Configuration

The `cors` option takes a `CorsConfig` object. Setting `cors` **replaces** the default CORS configuration entirely — there is no merge. If you override `cors`, include all headers your clients need (e.g. `mcp-session-id` in `exposeHeaders`).

Default CORS configuration:

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

Custom CORS example:

```typescript
const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  cors: {
    origin: ['https://app.example.com'],
    allowMethods: ['GET', 'POST', 'DELETE', 'OPTIONS'],
    allowHeaders: ['Content-Type', 'Authorization', 'mcp-protocol-version'],
    exposeHeaders: ['mcp-session-id'],
  },
})
```

---

## 7. Security Configuration

### DNS Rebinding Protection

Use `allowedOrigins` to enable Host header validation and protect against DNS rebinding attacks.

**Behavior:**

- `allowedOrigins` not set (default) → no host validation, all `Host` values accepted
- `allowedOrigins: []` → no host validation (same as not set)
- `allowedOrigins: ['https://myapp.com']` → Host header must match one of the configured hostnames; applies globally to all routes

`allowedOrigins` accepts full URLs (e.g. `"https://myapp.com"`) and normalizes them to hostnames for validation.

```typescript
// Default: no host validation (development)
const devServer = new MCPServer({
  name: 'dev-server',
  version: '1.0.0',
})

// Production: restrict to known hostnames
const prodServer = new MCPServer({
  name: 'prod-server',
  version: '1.0.0',
  allowedOrigins: [
    'https://myapp.com',
    'https://app.myapp.com',
  ],
})

// Load from environment
const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  allowedOrigins: process.env.ALLOWED_ORIGINS?.split(','),
})
```

### Input Validation

Always validate tool inputs using Zod schemas. The schema is enforced automatically before your handler runs:

```typescript
import { error, text } from 'mcp-use/server'
import { z } from 'zod'

server.tool({
  name: 'process_input',
  schema: z.object({
    email: z.string().email().describe('Email address'),
    url: z.string().url().describe('URL to process'),
  }),
}, async ({ email, url }) => {
  // Inputs are already validated by Zod at this point
  return text(`Processing ${email} and ${url}`)
})
```

---

## 8. Middleware Configuration

`MCPServer` supports both **Hono middleware** and **Express middleware**. Express middleware is automatically detected and adapted to work with Hono. You can add middleware using `server.use()` or `server.app.use()`.

Express middleware is detected by function signature (3-4 parameters) and pattern matching for Express-specific code patterns (e.g., `res.send`, `req.body`). Hono middleware uses 2 parameters and Hono-specific patterns (e.g., `c.req`, `c.json`). Both types can be mixed in the same application.

### Using Middleware

```typescript
import { MCPServer } from 'mcp-use/server'
import morgan from 'morgan'
import rateLimit from 'express-rate-limit'

const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
})

// Hono middleware
server.use(async (c, next) => {
  console.log(`${c.req.method} ${c.req.path}`)
  await next()
})

// Express middleware (automatically adapted)
server.use(morgan('combined'))
server.use('/api', rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 100,
}))

// Mix both types
server.use(morgan('dev'), async (c, next) => {
  await next()
})
```

### Route-Scoped Middleware

```typescript
import { MCPServer } from 'mcp-use/server'
import rateLimit from 'express-rate-limit'

const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
})

// Hono middleware for specific routes
server.use('/api/admin/*', async (c, next) => {
  const apiKey = c.req.header('x-api-key')
  if (!apiKey || apiKey !== process.env.API_KEY) {
    return c.json({ error: 'Unauthorized' }, 401)
  }
  await next()
})

// Express middleware for specific routes (automatically adapted)
server.use('/api', rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 100,
}))

// Custom HTTP endpoint
server.get('/health', (c) => c.json({ status: 'ok' }))
```

MCP protocol routes (`/mcp`, `/mcp-use/widgets/*`, `/inspector`) are registered by the server internally. Add your custom routes before calling `listen()` or `getHandler()`.

---

## 9. Custom HTTP Routes

Add HTTP endpoints alongside your MCP protocol routes. Register before calling `listen()`.

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

## 10. Content Security Policy (CSP)

CSP controls which domains widgets can fetch from, load scripts/styles from, and embed. Widgets run in sandboxed iframes — CSP must explicitly allow external resources.

Use the `CSP_URLS` env var to add extra domains globally without per-widget config.

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

---

## 11. Server Composition (`proxy`)

Added in **v1.21.0**. Use `MCPServer.proxy(target)` to aggregate tools, resources, and prompts from another server instance into the primary server. Useful for splitting a large server into logical modules or composing third-party servers.

```typescript
import { MCPServer } from 'mcp-use/server'

// Sub-server module (no listen())
const weatherServer = new MCPServer({ name: 'weather', version: '1.0.0' })
weatherServer.tool({ name: 'get-weather', ... }, async ({ city }) => { ... })

const analyticsServer = new MCPServer({ name: 'analytics', version: '1.0.0' })
analyticsServer.tool({ name: 'track-event', ... }, async (args) => { ... })

// Primary server composes both
const server = new MCPServer({ name: 'main', version: '1.0.0' })
server
  .proxy(weatherServer)
  .proxy(analyticsServer)

await server.listen(3000)
// Clients see get-weather + track-event as if they were registered directly
```

---

## 12. Complete Production Config Example

```typescript
import { MCPServer, RedisSessionStore, RedisStreamManager } from 'mcp-use/server'
import { createClient } from 'redis'

const redis = createClient({ url: process.env.REDIS_URL })
const pubSubRedis = redis.duplicate()
await redis.connect()
await pubSubRedis.connect()

const server = new MCPServer({
  name: 'production-server',
  version: '1.0.0',
  description: 'Production MCP server with full configuration',
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
