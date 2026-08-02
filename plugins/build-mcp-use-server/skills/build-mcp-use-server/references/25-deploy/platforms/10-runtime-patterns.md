# Runtime Patterns

*Read this when choosing how to deploy MCP server and views for your target runtime.*

## The three canonical patterns

`server.fetch(request)` is the portable MCP server boundary across all runtimes. Views live in `.mcp-use/build/views/`. The difference is how you deploy the views relative to your server. Pick the pattern matching your runtime:

### 1. Node and filesystem runtimes (Railway, Manufact, Bun, Node Vercel)

Deploy `.mcp-use/build` on the same filesystem as your server. The server reads generated assets from disk and serves them from the same public origin.

**Build:**
```bash
MCP_URL=https://api.example.com/mcp npm run build
```

**Handler:**
```ts
export default server.fetch;
```

**Deploy:** Copy `.mcp-use/build` alongside server code. Server automatically serves:
- `/mcp` → MCP protocol
- `/mcp/_mcp-use/*` → static view assets from disk

**Why:** Simple, no extra infrastructure; server owns the full response path.

### 2. Edge runtime with co-located static assets (Cloudflare Workers, Vercel Edge, Deno Deploy with static binding)

Build once, bind `.mcp-use/build` as static assets via your platform's asset binding. Route nested `/mcp/_mcp-use/*` requests to assets; everything else to `server.fetch`.

**Build:**
```bash
MCP_URL=https://api.example.com/mcp \
MCP_ASSETS_URL=https://api.example.com \
npm run build
```

**Platform routing:**
- `/mcp/_mcp-use/*` → static asset binding (strip prefix; maps to `views/`)
- `/mcp/*` → `server.fetch(request)`
- `/` → `server.fetch(request)` (landing page)

**Cloudflare example:**
```toml
# wrangler.toml
[assets]
directory = ".mcp-use/build"

[routes]
pattern = "<domain>/mcp/_mcp-use/*"
zone_name = "<zone>"
custom_domain = true
```

```ts
export default {
  async fetch(request, env, ctx) {
    // Platform routing sends static requests to asset handler;
    // MCP and landing to handler below
    if (new URL(request.url).pathname.startsWith("/mcp/_mcp-use/")) {
      return env.ASSETS.fetch(request);
    }
    return server.fetch(request);
  }
};
```

**Why:** Static assets don't consume compute; server handles protocol only.

### 3. Edge runtime with external assets (CDN separate from platform)

Build with an external asset origin. Publish view files to your CDN. Server handles MCP only.

**Build:**
```bash
MCP_URL=https://api.example.com/mcp \
MCP_ASSETS_URL=https://cdn.example.com/mcp-assets \
npm run build
```

Build output prints exact destination:
```
https://cdn.example.com/mcp-assets/mcp/_mcp-use/views/<view-name>/
```

**Deploy:** Publish `.mcp-use/build/views/` to CDN at that prefix. Server handles only MCP endpoints.

**CDN configuration:** Ensure asset host allows:
- CORS: `Access-Control-Allow-Origin` for View iframe (typically `*` or your MCP server origin)
- CSP: Headers permitting iframe src + style/script from MCP server origin

**Why:** Distribute assets globally; large view payloads don't hit server; suitable when platform storage is limited or expensive.

## Verification

After every deployment, capture the actual rendered View, not just HTTP status:

```bash
npx --yes mcp-use@beta screenshot \
  --mcp https://api.example.com/mcp \
  --tool <tool-name> \
  --output live-view.png
```

HTTP 200 alone does not validate streamable MCP response or View rendering. Screenshot captures rendered HTML and confirms asset loading.

## Decision tree

| Condition | Pattern |
|-----------|---------|
| Server and filesystem same; simple | **1. Node/filesystem** |
| Server is edge; static assets available | **2. Edge co-located** |
| Assets separate CDN; large views | **3. Edge external CDN** |
| Hybrid: Node server + CDN views | **3. Edge external CDN** (server still pattern 1) |

Cross-reference: `references/25-deploy/01-decision-matrix.md` (platform → pattern mapping) and `references/09-transports/04-runtime-adapters-node-next-fetch.md` (runtime adapter details).
