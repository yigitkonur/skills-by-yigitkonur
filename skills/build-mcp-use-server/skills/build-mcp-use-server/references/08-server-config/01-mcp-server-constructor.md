# MCPServer constructor

`MCPServer` accepts a `ServerConfig` at construction. Only `name` and `version` are required.

```typescript
import { MCPServer } from 'mcp-use/server'

const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
})
```

## Full ServerConfig fields

| Field | Type | Default | Purpose |
|---|---|---|---|
| `name` | `string` | — required | MCP handshake identifier |
| `version` | `string` | — required | Semantic version reported to clients |
| `title` | `string` | `name` | Display name in Inspector and clients |
| `description` | `string` | — | Server description shown during discovery |
| `websiteUrl` | `string` | — | Public website URL |
| `favicon` | `string` | — | Path relative to `public/` |
| `icons` | `Array<{ src; mimeType?; sizes?; theme? }>` | — | Light/dark icon variants for client UIs |
| `host` | `string` | `'localhost'` | Bind hostname — see `02-network-config.md` |
| `baseUrl` | `string` | resolved at `listen()` | Public URL for widget/asset URLs — see `02-network-config.md` |
| `cors` | `CorsConfig` | permissive | CORS — see `03-cors-and-allowed-origins.md` |
| `allowedOrigins` | `string[]` | — | Host header validation — see `03-cors-and-allowed-origins.md` |
| `oauth` | `OAuthProvider` | — | OAuth provider; use factory functions — see `11-auth/` |
| `sessionStore` | `SessionStore` | `InMemorySessionStore` | Session persistence — see `10-sessions/` |
| `streamManager` | `StreamManager` | `InMemoryStreamManager` | SSE fan-out — see `10-sessions/` |
| `sessionIdleTimeoutMs` | `number` | `86400000` | Idle session TTL in ms |
| `stateless` | `boolean` | auto-detected | Force transport mode — see `09-transports/04-stateless-mode.md` |

## Adding behavior after construction

The constructor takes config only. Tools, resources, prompts, custom routes, and middleware are registered on the instance after construction:

| Method | Purpose | Reference |
|---|---|---|
| `server.tool(...)` | Register a tool | `04-tools/` |
| `server.resource(...)` | Register a resource | `06-resources/` |
| `server.prompt(...)` | Register a prompt | `07-prompts/` |
| `server.use(...)` | Add middleware | `05-middleware-and-custom-routes.md` |
| `server.get/post/route(...)` | Add custom HTTP routes | `05-middleware-and-custom-routes.md` |
| `server.proxy(target)` | Compose another server | `17-advanced/` |
| `server.listen(port?)` | Start HTTP transport | `09-transports/03-streamable-http.md` |
| `server.getHandler(opts?)` | Build serverless handler | `09-transports/05-serverless-handlers.md` |
| `server.close()` | Graceful listener shutdown after `listen()` | `07-shutdown-and-lifecycle.md` |
| `server.forceClose()` | Immediate listener shutdown after `listen()` | `07-shutdown-and-lifecycle.md` |

There is no constructor `port` or `middleware` field in `mcp-use@1.26.0`. Pass the port to `server.listen(port?)`; register middleware with `server.use(...)` after construction.

## Identity example

```typescript
const server = new MCPServer({
  name: 'weather-api',
  version: '2.1.0',
  title: 'Weather API',
  description: 'Real-time weather data for any location',
  websiteUrl: 'https://weather.example.com',
  favicon: 'favicon.ico',
  icons: [
    { src: 'icon.svg', mimeType: 'image/svg+xml', sizes: ['512x512'], theme: 'light' },
    { src: 'icon-dark.svg', mimeType: 'image/svg+xml', sizes: ['512x512'], theme: 'dark' },
  ],
})
```

`title` defaults to `name`. Set it explicitly for a friendlier display label.

## Deprecated fields

| Field | Status | Replacement |
|---|---|---|
| `autoCreateSessionOnInvalidId` | Deprecated | Server returns 404 per MCP spec; use `sessionStore` for persistence |

**Canonical doc:** https://manufact.com/docs/typescript/server/configuration
