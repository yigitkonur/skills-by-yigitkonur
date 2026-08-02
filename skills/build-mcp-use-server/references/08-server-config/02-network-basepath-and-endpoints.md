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
// POST /mcp                  → MCP protocol (initialize, tools/list, tools/call, etc.)
// GET /mcp                   → HTML landing page
// GET /mcp/_mcp-use/*        → View assets (built by `mcp-use build`)
// POST /mcp/oauth/authorize  → OAuth metadata & token endpoints (if oauth configured)
```

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
// url = "http://127.0.0.1:3000/mcp" (when basePath="/mcp")

// With custom host:
await server.listen(3000, { host: "0.0.0.0" });
// Listens on 0.0.0.0:3000; bound to public interface
```

**Host & port resolution:**
1. **Host:** CLI override `--host` → `HOST` env → `options.host` → `config.host` → `"127.0.0.1"`
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

**Localhost-class detection:**
If request Host header matches `127.0.0.1`, `localhost`, or `::1`:
- Host validation ON (same protection as `listen()`)
- Origin validation ON (if `allowedOrigins` set)

Otherwise, Host/Origin validation determined by config (`allowedHosts`, `allowedOrigins`).

## OAuth Resource URL

The OAuth resource URL is the audience your bearer token authorizes access to. It is **NOT** a config option in v2; instead, it is **inferred** or **explicitly configured via the OAuth provider**.

### Local Development

When you call `server.listen(port)`, mcp-use infers the resource as `http://localhost:{port}` (or your custom host). This is the OAuth audience.

```typescript
await server.listen(3000);
// Resource URL: http://127.0.0.1:3000
// Clients send bearer token for this audience
```

### Public Deployment

For hosted deploys (Railway, Vercel, Cloudflare, etc.), the resource URL must match the public endpoint. Configure it via your OAuth provider settings (Clerk, Auth0, etc.), not via mcp-use config.

**Example (Clerk):**
```typescript
import { clerkProvider } from "mcp-use/oauth/clerk";

const server = new MCPServer({
  name: "api",
  version: "1.0.0",
  oauth: clerkProvider({
    secretKey: process.env.CLERK_SECRET_KEY,
    // Clerk's well-known endpoints + issuer are auto-discovered
    // Resource audience is your public server URL (configure in Clerk dashboard)
  }),
});
```

Clerk (and other providers) use DNS discovery to find token endpoints; OAuth resource URL is typically inferred from the issuer or configured per provider.

See `references/11-auth/02-attaching-a-provider.md` for per-provider resource URL configuration.

## View Assets & MCP_URL Build Variable

Views (MCP Apps) are built once with a compile-time `MCP_URL` environment variable. This variable is NOT a server config option.

```bash
# Build time — set MCP_URL to your public endpoint
MCP_URL=https://api.example.com/mcp npm run build

# Output: .mcp-use/build/views/
# View HTML embeds https://api.example.com/mcp as the server endpoint
```

Views load from `{MCP_URL}/_mcp-use/views/{view-name}/` at runtime. For local dev, `mcp-use dev` automatically sets `MCP_URL=http://localhost:PORT/mcp` and restarts on changes.

For edge runtimes with separate static storage (Cloudflare Workers), also set `MCP_ASSETS_URL`:

```bash
MCP_URL=https://api.example.com/mcp \
MCP_ASSETS_URL=https://cdn.example.com \
npm run build
```

See `references/09-transports/04-runtime-adapters-node-next-fetch.md` for per-runtime deployment patterns.
