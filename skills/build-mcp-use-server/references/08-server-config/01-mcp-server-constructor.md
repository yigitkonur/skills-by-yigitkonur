# MCPServer Constructor Options

*Read this when setting up a new MCPServer to understand all available configuration options and their defaults.*

## Constructor

```typescript
const server = new MCPServer<TUser>(config: ServerConfig<TUser>)
```

**Generic parameters:**
- `TUser = never` (default): no authentication; `oauth` field must be omitted
- `TUser = SomeUserType`: OAuth required; callback contexts receive `ctx.auth.user: SomeUserType`

## ServerConfig Options Reference

| Option | Type | Default | Notes |
|--------|------|---------|-------|
| `name` | `string` | (required) | Server identity reported to clients during MCP initialization. |
| `version` | `string` | (required) | Semantic version reported to clients. |
| `title` | `string \| undefined` | (inferred from `name`) | Human-readable display name for UIs. |
| `description` | `string \| undefined` | `undefined` | Implementation description reported in MCP metadata. |
| `instructions` | `string \| undefined` | `undefined` | Server-wide workflow guidance; returned during init. |
| `basePath` | `string` | `"/mcp"` | URL route where MCP endpoint is mounted. Must be absolute pathname (starts with `/`, no `?`, `#`, `//`, or trailing slash except `/`). |
| `host` | `string \| undefined` | `"127.0.0.1"` | Bind host for `listen()` when no CLI/env override. Localhost-class (`127.0.0.1`, `localhost`, `::1`) get automatic Host/Origin validation. Set `"0.0.0.0"` for public access. |
| `port` | `number \| undefined` | `3000` | TCP port for `listen()` when no CLI/env override. Pass `0` for ephemeral. |
| `favicon` | `string \| undefined` | (inferred from `icons[0]`) | Safe path relative to `public/`, HTTP(S) URL, or data URL; served at `/favicon.ico`. Empty string invalid. |
| `icons` | `Icon[] \| undefined` | `undefined` | MCP icons reported to clients; uses SDK `Icon` shape (src, mimeType, sizes, theme). First icon also selects favicon if `favicon` not explicit. |
| `websiteUrl` | `string \| undefined` | `undefined` | Absolute HTTP(S) URL for server docs/homepage. |
| `allowedHosts` | `string[] \| undefined` | `undefined` | Extra hostnames for Host-header DNS-rebinding protection (port-agnostic, additive). Also enables Host validation on `server.fetch`. |
| `allowedOrigins` | `string[] \| undefined` | `undefined` | Extra hostnames for Origin-header validation (port-agnostic, additive to localhost-class). Only applies to non-GET/HEAD. Off when unset. |
| `legacy` | `"stateless" \| "reject"` | `"stateless"` | How to serve 2025-era (non-envelope) legacy requests: stateless with fresh instance, or reject with unsupported-protocol-version. |
| `publicLandingPage` | `boolean` | `false` | Expose landing page without bearer auth when OAuth configured. MCP protocol requests remain protected. |
| `logging` | `LoggingOptions` | (enabled at `info` level) | Request logging control: `{ enabled?: boolean, level?: "info" \| "debug" \| "trace" }`. `MCP_USE_LOG_LEVEL` env overrides. |
| `requestState` | `ServerOptions["requestState"]` | `undefined` | Integrity codec (e.g., `createRequestStateCodec(...).verify`) for `input_required` round-trip state validation. |
| `cors` | `CorsOptions \| undefined` | `undefined` | CORS headers on all routes: off when omitted; `{}` enables with defaults. |
| `oauth` | `OAuthProvider<TUser>` | (none if `TUser = never`) | External OAuth provider; required when `TUser ≠ never`. |

## CORS Configuration Detail

```typescript
interface CorsOptions {
  enabled?: boolean;  // default: true when cors is set
  origin?: string | string[] | ((origin: string | null) => string | null);
  methods?: string[];  // default: ["GET", "HEAD", "POST", "OPTIONS"]
  allowedHeaders?: string[];  // default: common MCP + JSON headers
  credentials?: boolean;  // default: false
}
```

## Port & Host Precedence

For `await server.listen(port?, options?)`:

**Port precedence:**
1. Argument `listen(port)` if number
2. `PORT` environment variable
3. `config.port`
4. `3000`

**Host precedence:**
1. `options.host` argument
2. `HOST` environment variable
3. `config.host`
4. `"127.0.0.1"`

Return value: `{ port: number, url: string }` (e.g., `http://localhost:3000/mcp`).

## Minimal Example

```typescript
import { MCPServer } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  description: "A minimal MCP server",
  // basePath: "/mcp",  // default
  // host: "127.0.0.1",  // default
  // port: 3000,  // default
});

// Register tools, resources, prompts
server.tool({
  name: "example",
  description: "An example tool",
  inputSchema: z.object({ input: z.string() }),
}, async ({ input }, ctx) => ({
  content: [{ type: "text", text: `Got: ${input}` }],
}));

// Start
const { url } = await server.listen();
console.log(`Serving at ${url}`);
```

## Key Instance Properties

| Property | Type | Access |
|----------|------|--------|
| `app` | `Hono<TEnv>` | readonly; add custom routes via `.get()`, `.post()`, etc. |
| `fetch` | `(request: Request) => Promise<Response>` | readonly; web-standard handler for edge runtimes |
| `basePath` | `string` | getter; configured route path |
| `host` | `string \| undefined` | getter; configured host before CLI/env overrides |
| `port` | `number \| undefined` | getter; configured port before CLI/env overrides |
| `branding` | `ServerBranding` | getter; immutable branding with resolved favicon |

See `references/08-server-config/02-network-basepath-and-endpoints.md` for endpoint behavior and `references/09-transports/04-runtime-adapters-node-next-fetch.md` for runtime-specific mounting.
