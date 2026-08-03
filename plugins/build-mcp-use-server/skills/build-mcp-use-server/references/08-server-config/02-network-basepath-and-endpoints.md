# Network, basePath, and Endpoints

*Read this to understand how basePath controls routing, how listen vs fetch work, and how OAuth resource URLs are determined.*

## basePath: The MCP Route

`basePath` (default `/mcp`) is the URL path where the MCP endpoint is mounted.

```typescript
const server = new MCPServer({
  name: "api",
  version: "1.0.0",
  basePath: "/mcp",  // default
});

// Endpoints:
// POST /mcp                        → MCP protocol (initialize, tools/list, tools/call, etc.)
// GET/HEAD /mcp (Accept: text/html) → HTML landing page (unauthenticated unless OAuth + publicLandingPage=false)
// GET/HEAD /mcp/_mcp-use/public/*   → Public view/branding assets (dev: `<projectRoot>/public`; prod: `.mcp-use/build/views/public`)
// GET/HEAD /mcp/_mcp-use/views/*    → Built view bundles (production only; dev serves via Vite middleware)
```

The landing page route is the *same* `basePath` route as the MCP protocol handler — it is distinguished by request method (`GET`/`HEAD`) and an `Accept` header that names `text/html` (browser navigation). Any other `GET`/`HEAD` request to `basePath` without an HTML-accepting header falls through to the MCP handler. With `oauth` configured, the landing page requires a bearer token unless `publicLandingPage: true`; MCP protocol requests (`POST`) are always protected. The two `_mcp-use/*` asset routes are always public (no bearer check), including a wildcard CORS header for cross-origin sandboxed view iframes.

**Valid basePath values:**
- `/mcp` (default)
- `/` (root path)
- `/api/mcp`
- Any absolute pathname starting with `/`, no `?`, `#`, `//`, trailing slash (except `/`)

Invalid: `mcp` (no leading `/`), `/mcp/`, `http://`, relative paths.

## listen() vs fetch()

### `server.listen(port?, options?)`

Binds a Node.js HTTP listener on `host:port`.

```typescript
const { port, url } = await server.listen(3000);
// url = "http://localhost:3000/mcp" (when basePath="/mcp")

// With custom host:
await server.listen(3000, { host: "0.0.0.0" });
// Listens on 0.0.0.0:3000; bound to public interface
// (returned `url` still reads "http://localhost:3000/mcp" — it is NOT the resolved bind host)
```

`url` is always built as `http://localhost:${boundPort}${basePath}` — the literal string `"localhost"`, not the actual `host` you passed or resolved. For port `0` (ephemeral), `boundPort` reflects the OS-assigned port. Don't rely on `url` to report the real bind address for `0.0.0.0` or a LAN IP; construct that yourself from `options.host`/`config.host` when it matters.

**Host & port resolution:**
1. **Host:** `options.host` → `HOST` env → `config.host` → `"127.0.0.1"`
2. **Port:** argument → `PORT` env → `config.port` → `3000`

Use `0` for ephemeral port (OS assigns random available port).

**Localhost-class binds (`127.0.0.1`, `localhost`, `::1`):**
- Host validation ON (Host header required)
- Origin validation ON (Origin checked on non-GET/HEAD) if `allowedOrigins` set

**Public binds (`0.0.0.0`):**
- No Host validation by default (platform edge handles routing)
- Origin controlled by `allowedOrigins`

### `server.fetch(request: Request): Promise<Response>`

Web-standard handler; portable across edge runtimes (Vercel, Cloudflare, Deno, etc.). Does not bind a socket.

```typescript
export default server.fetch;  // Vercel, Deno, Workers, etc.
```

**Validation:**
`server.fetch` does not infer a bind host. Host validation is off unless `allowedHosts` is configured. Origin validation runs only when `allowedOrigins` is configured.

## OAuth Resource URL

The OAuth resource URL is the audience your bearer token authorizes access to. It is **NOT** a config option in v2; instead, it is **inferred** or **explicitly configured via the OAuth provider**.

### Local Development

When `oauth` is configured and `server.listen(port)` binds a localhost-class host (`127.0.0.1`, `localhost`, `::1`) with no explicit `resource`/`MCP_URL`, mcp-use derives the resource as `http://localhost:{boundPort}{basePath}` — always the literal hostname `"localhost"`, resolved lazily on the listener callback (so ephemeral port `0` still gets the real bound port).

```typescript
await server.listen(3000);
// Resource URL: http://localhost:3000/mcp
// Clients send bearer token for this audience
```

Listening on a **non**-localhost host (e.g., `host: "0.0.0.0"`) or calling `server.fetch` with `oauth` configured and no explicit `resource`/`MCP_URL` throws: `"OAuth requires an explicit resource or MCP_URL when using server.fetch or listening on a non-local host"`. Configure `resource` on the provider or set `MCP_URL` before deploying.

### Public Deployment

For hosted deploys (Railway, Vercel, Cloudflare, etc.), the resource URL must match the public endpoint. Configure it via your OAuth provider settings (Clerk, Auth0, etc.), not via mcp-use config.

**Example (Clerk):**
```typescript
import { oauthClerkProvider } from "mcp-use/oauth/clerk";

const server = new MCPServer({
  name: "api",
  version: "1.0.0",
  oauth: oauthClerkProvider({
    frontendApiUrl: process.env.CLERK_FRONTEND_API_URL, // required — Clerk's Frontend API host
    // audience?: string        — optional, defaults per provider
    // resource?: URL | string  — optional explicit override; otherwise derived from basePath + MCP_URL/listen()
  }),
});
```

Every provider factory (`oauthClerkProvider`, `oauthAuth0Provider`, `oauthWorkosProvider`, `oauthSupabaseProvider`, `oauthKeycloakProvider`, `oauthBetterAuthProvider`, `oauthCustomProvider`) accepts an optional `resource: URL | string` field (from `OAuthResourceOptions`). When set, it takes precedence over `MCP_URL`/`listen()` inference — but it must resolve to exactly `basePath` on the server's own origin (`validateOAuthResource` rejects a mismatch).

See `../11-auth/02-attaching-a-provider.md` for per-provider resource URL configuration.

## View Assets & MCP_URL Build Variable

Views (MCP Apps) are built once with a compile-time `MCP_URL` environment variable. This variable is NOT a server config option.

`MCP_URL` is consumed as an **origin only** (scheme + host + port) — any path segment you include is ignored by the server's own asset/OAuth resolution. Set it to your server's public origin:

```bash
# Build time — set MCP_URL to your public origin
MCP_URL=https://api.example.com npm run build

# Output: .mcp-use/build/views/
# View HTML embeds https://api.example.com as the server origin,
# then appends basePath + /_mcp-use/views/{view-name}/ itself
```

Views load from `{origin}{basePath}/_mcp-use/views/{view-name}/` at runtime, where `{origin}` comes from `MCP_URL`. For local dev, `mcp-use dev` temporarily supplies `MCP_URL=http://localhost:{port}` while importing/evaluating the entry when the variable is unset, then restores the prior environment. `--tunnel` does not replace it with the public tunnel URL; read that URL from the CLI's `Tunnel:` output or Inspector dev-info API.

For edge runtimes with separate static storage (Cloudflare Workers), also set `MCP_ASSETS_URL` (origin + optional path prefix; falls back to `MCP_URL`'s origin when unset):

```bash
MCP_URL=https://api.example.com \
MCP_ASSETS_URL=https://cdn.example.com \
npm run build
```

See `../09-transports/04-runtime-adapters-node-next-fetch.md` for per-runtime deployment patterns.
