# Environment variables

*Read this to configure server behavior via env vars.*

The CLI and runtime respect a small set of environment variables for port, host, URLs, telemetry, and debugging.

## Standard variables

| Variable | Used by | Default | Purpose |
|----------|---------|---------|---------|
| `PORT` | `mcp-use dev`, `mcp-use start` | 3000 | TCP port. Precedence: flag → env → 3000. |
| `HOST` | `mcp-use dev`, `mcp-use start` | 127.0.0.1 | Bind address. Precedence: flag → env → 127.0.0.1. Public: `0.0.0.0`. |
| `NODE_ENV` | `mcp-use start` | forced to `production` | Always production on start. Dev does not set it. |
| `MCP_URL` | Dev / Inspector client | http://127.0.0.1:PORT/mcp | URL clients use to reach the server. Auto-set by dev if not present. |

Set them:

```bash
PORT=4000 npm run dev
HOST=0.0.0.0 npm run dev
MCP_URL=https://my-server.example.com/mcp npm run dev
```

Or in `.env`:

```bash
# .env (git-ignored)
PORT=4000
HOST=127.0.0.1
MCP_URL=http://localhost:4000/mcp
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
