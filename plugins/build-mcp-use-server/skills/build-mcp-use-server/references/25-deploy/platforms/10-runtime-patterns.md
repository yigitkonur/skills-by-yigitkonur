# Runtime Patterns

*Read this when choosing how to deploy MCP server and views for your target runtime.*

## The three canonical patterns

`server.fetch(request)` is the portable MCP server boundary across all runtimes. Views live in `.mcp-use/build/views/`. The difference is how you deploy the views relative to your server. Pick the pattern matching your runtime:

### 1. Node and filesystem runtimes (Railway, Manufact, Bun, Node Vercel)

Deploy `.mcp-use/build` on the same filesystem as your server. The server reads generated assets from disk and serves them from the same public origin.

**Build:**
```bash
MCP_URL=https://api.example.com npm run build
```

**Handler:**
```ts
// mcp-use start / npm start (Manufact, Railway, generic Node) needs a
// listen()-capable default export — export the server instance itself:
export default server;

// Vercel Functions and other frameworks that call server.fetch(request)
// directly, or Bun's file-run auto-serve, also accept the same object
// export since it exposes a `fetch` method — see platforms/02-vercel.md
// and platforms/07-bun.md.
```

**Deploy:** Copy `.mcp-use/build` alongside server code. Server automatically serves:
- `/mcp` → MCP protocol
- `/mcp/_mcp-use/*` → static view assets from disk

**Why:** Simple, no extra infrastructure; server owns the full response path.

### 2. Edge runtime with co-located static assets (Cloudflare Workers, Vercel Edge, Deno Deploy with static binding)

Build once, bind `.mcp-use/build` as static assets via your platform's asset binding. Route nested `/mcp/_mcp-use/*` requests to assets; everything else to `server.fetch`.

**Build:**
```bash
MCP_URL=https://api.example.com \
MCP_ASSETS_URL=https://api.example.com \
npm run build
```

**Platform routing:**
- `<basePath>/_mcp-use/views/*` → static binding path `/views/*`
- `<basePath>/_mcp-use/public/*` → static binding path `/views/public/*`
- `<basePath>` → `server.fetch(request)` for both MCP protocol requests and HTML landing-page navigation

**Cloudflare example:**
```toml
# wrangler.toml
name = "my-mcp-worker"
main = "src/index.ts"
compatibility_date = "2026-08-03"

[assets]
directory = ".mcp-use/build"
binding = "ASSETS"
run_worker_first = ["/mcp/_mcp-use/*"]
```

By default Cloudflare maps the public request path directly under `directory`. That does not match mcp-use's layout: a generated URL such as `/mcp/_mcp-use/views/card/assets/card.js` corresponds to the on-disk file `.mcp-use/build/views/card/assets/card.js`, not `.mcp-use/build/mcp/_mcp-use/...`. `run_worker_first` sends the generated prefix through the Worker so it can strip `/mcp/_mcp-use/` before calling `env.ASSETS`.

```ts
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const prefix = "/mcp/_mcp-use/";
    const publicPrefix = `${prefix}public/`;

    if (url.pathname.startsWith(publicPrefix)) {
      url.pathname = `/views/public/${url.pathname.slice(publicPrefix.length)}`;
      return env.ASSETS.fetch(new Request(url, request));
    }

    if (url.pathname.startsWith(prefix)) {
      url.pathname = `/${url.pathname.slice(prefix.length)}`;
      return env.ASSETS.fetch(new Request(url, request));
    }

    return server.fetch(request);
  }
};
```

For a non-default server `basePath`, replace `/mcp` in `prefix` with that exact path.

**Why:** Static assets don't consume compute; server handles protocol only.

### 3. Edge runtime with external assets (CDN separate from platform)

Build with an external asset origin. Publish View files to your CDN. The server handles MCP/landing requests; the CDN handles generated View/public assets.

**Build:**
```bash
MCP_URL=https://api.example.com \
MCP_ASSETS_URL=https://cdn.example.com/mcp-assets \
npm run build
```

The CLI prints that `.mcp-use/build/views/` must be uploaded and reports a non-default `basePath`, but does **not** print a complete CDN destination URL. With the default `/mcp` base path, publish each generated directory at:

```text
.mcp-use/build/views/<view-name>/
  → https://cdn.example.com/mcp-assets/mcp/_mcp-use/views/<view-name>/

.mcp-use/build/views/public/
  → https://cdn.example.com/mcp-assets/mcp/_mcp-use/public/
```

Verify the generated absolute URLs in `.mcp-use/build/manifest.json`; for a non-default `basePath`, substitute that exact path for `/mcp`.

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
