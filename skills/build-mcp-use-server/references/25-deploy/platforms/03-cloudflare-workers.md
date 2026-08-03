# Cloudflare Workers

*Read this when deploying an mcp-use server to Cloudflare Workers.*

Cloudflare Workers operate in a V8 edge isolate environment, not Node. Serve generated View files through a Workers static-assets binding.

## Routing

Generated asset URLs live under `<basePath>/_mcp-use/`, while files on disk live directly under `.mcp-use/build/views/`. A Workers static-assets binding does **not** strip that prefix automatically. Intercept `/mcp/_mcp-use/*` in the Worker, rewrite it from `/mcp/_mcp-use/views/...` or `/mcp/_mcp-use/public/...` to `/views/...` or `/views/public/...`, then call `env.ASSETS.fetch(...)`. Route every other request to `server.fetch`.

## Build and Deploy

Build with the public MCP URL and asset origin:

```bash
MCP_URL=https://<worker>.<account>.workers.dev \
MCP_ASSETS_URL=https://<worker>.<account>.workers.dev \
npm run build

npx wrangler deploy
```

Configure `.mcp-use/build` as the asset directory in `wrangler.toml` (use the current TOML table syntax and set an explicit binding; set `compatibility_date` to the date you configure this, not a stale copy-pasted value):

```toml
name = "my-mcp-worker"
main = "src/index.ts"
compatibility_date = "2026-08-03"

[assets]
directory = ".mcp-use/build"
binding = "ASSETS"
run_worker_first = ["/mcp/_mcp-use/*"]
```

`run_worker_first` ensures generated asset URLs reach the Worker for the required prefix rewrite. Requests for exact static paths under `/views/...` can still be served through `env.ASSETS` after rewriting.

## Handler

Use the Web-standard Fetch boundary and keep the Workers export as an object with a `fetch(request, env, ctx)` method. The wrapper below rewrites the public generated asset route to the asset binding's on-disk layout; all other requests go to `server.fetch`:

```typescript
import { MCPServer } from "mcp-use";

interface Env {
  ASSETS: {
    fetch(request: Request): Promise<Response>;
  };
}

const server = new MCPServer({
  name: "cloudflare-mcp",
  version: "1.0.0",
});

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
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
  },
};
```

For a non-default `basePath`, replace `/mcp` in `prefix` with that exact path. Do not call `server.listen()` in a Worker.

## Verify

```bash
npx --yes mcp-use@beta screenshot \
  --mcp https://<worker>.<account>.workers.dev/mcp \
  --tool <tool-name> \
  --output cloudflare-live-view.png
```

A successful MCP request is not enough: confirm that the rendered View loads its generated assets.
