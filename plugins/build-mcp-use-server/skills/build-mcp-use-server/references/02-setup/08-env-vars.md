# Environment variables

*Read this to configure server behavior via env vars.*

The CLI and runtime respect a small set of environment variables for port, host, URLs, telemetry, and debugging.

## Standard variables

| Variable | Used by | Default | Purpose |
|----------|---------|---------|---------|
| `PORT` | `mcp-use dev`, `mcp-use start` | 3000 | TCP port. Precedence: flag → env → code (`ServerConfig.port`, `start` only) → 3000. |
| `HOST` | `mcp-use dev`, `mcp-use start` | 127.0.0.1 | Bind address. Precedence: flag → env → code (`ServerConfig.host`, `start` only) → 127.0.0.1. Public: `0.0.0.0`. |
| `NODE_ENV` | `mcp-use start` | set to `production` only if unset | `process.env.NODE_ENV ??= "production"` — never clobbers an explicit `NODE_ENV`. `dev` does not set it. |
| `MCP_URL` | server runtime (OAuth, CSP, View asset/connect URLs) | request origin when available; otherwise unset | Absolute public **origin only** (scheme + host + optional port, no path). OAuth on non-local/`server.fetch` deployments requires a valid value or explicit provider `resource`; pathful/malformed values are rejected by OAuth. |
| `MCP_ASSETS_URL` | `mcp-use build` | server origin | CDN/base URL to rewrite view asset paths to at build time (e.g. serving views from a separate static host). Must be a valid absolute URL or it is ignored. |
| `CSP_URLS` | server runtime (views CSP) | none | Comma-separated domain shortcut applied to all four CSP categories below when a category-specific var is unset. |
| `CSP_CONNECT_DOMAINS` | server runtime (views CSP) | `CSP_URLS`, else none | Comma-separated extra domains allowed in `connect-src`. |
| `CSP_RESOURCE_DOMAINS` | server runtime (views CSP) | `CSP_URLS`, else none | Comma-separated extra domains allowed for resource loads (scripts/styles/images/fonts). |
| `CSP_FRAME_DOMAINS` | server runtime (views CSP) | `CSP_URLS`, else none | Comma-separated extra domains allowed in `frame-src`. |
| `CSP_BASE_URI_DOMAINS` | server runtime (views CSP) | `CSP_URLS`, else none | Comma-separated extra domains allowed in `base-uri`. |
| `MCP_USE_TUNNEL_API` | `mcp-use dev --tunnel` | `https://local.mcp-use.run` | Tunnel broker endpoint; override to point at a self-hosted or alternate tunnel service. |

Set them:

```bash
PORT=4000 npm run dev
HOST=0.0.0.0 npm run dev
MCP_URL=https://my-server.example.com npm run dev
```

Or in `.env`:

```bash
# .env (git-ignored)
PORT=4000
HOST=127.0.0.1
MCP_URL=http://localhost:4000
```

Then:

```bash
source .env && npm run dev
```

## Deploy environment

On `npm run deploy`, pass vars via flag:

```bash
npm run deploy -- --env API_KEY=sk-xxx --env DATABASE_URL=postgres://...
```

Or from file:

```bash
# .env.production (git-ignored)
API_KEY=sk-xxx
DATABASE_URL=postgres://...
```

Then:

```bash
npm run deploy -- --env-file .env.production
```

Secrets never go in `package.json` or git. Use flags or files only.

## Next.js environment

In Next.js (mcp-use/next integration), define in `.env.local`:

```
API_KEY=sk-xxx
DATABASE_URL=postgres://...
```

Access in route handlers:

```typescript
const apiKey = process.env.API_KEY;
```

## Custom server variables

Define in your server entry and access via `process.env`:

```typescript
// index.ts
const apiKey = process.env.API_KEY;
if (!apiKey) {
  throw new Error("API_KEY env var required");
}

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
});

server.tool(
  { name: "call-api", ... },
  async (args, ctx) => {
    const result = await fetch(`https://api.example.com/data`, {
      headers: { "Authorization": `Bearer ${apiKey}` },
    });
    // ...
  }
);
```

## Cloud-specific notes

**Manufact Cloud (`npm run deploy`):**
- Set vars at deploy time via `--env` or `--env-file`
- Secrets persist per deployment; redeploy to rotate
- No `.env` file on deployed instance (use flags only)

**Vercel (Next.js + mcp-use/next):**
- Store secrets in Vercel dashboard or `.env.local` (local dev only)
- See Vercel docs for production secret management

**Cloudflare Workers (mcp-use fetch):**
- Use Wrangler secrets: `wrangler secret put API_KEY`
- Access via `env.API_KEY` (Hono context)

## Security

- Never commit `.env` or `.env.production` (add to `.gitignore`)
- Never log sensitive values (use in server, not in logs)
- Rotate keys after any exposure
