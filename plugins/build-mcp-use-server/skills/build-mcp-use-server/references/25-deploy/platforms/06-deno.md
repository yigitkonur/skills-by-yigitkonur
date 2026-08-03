# Deno Deploy

*Read this when deploying an MCP server to Deno Deploy (edge runtime).*

## When to choose Deno Deploy

- Edge runtime with Web-standard `Request`/`Response`
- No persistent filesystem; stateless handler-per-request pattern
- External asset storage required for generated Views (CDN or object bucket)
- You are prepared to validate the current Deno Deploy project/runtime configuration independently; mcp-use has no first-party Deno Deploy guide

## Handler wiring

Deno Deploy is an edge runtime. Call `Deno.serve` with a wrapper that forwards the Web-standard `Request` to `server.fetch` (this is the same forwarding pattern the framework's grounded Supabase Edge Functions guide uses, since Supabase Edge Functions also run on Deno):

```ts
import { MCPServer } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({ name: "my-server", version: "1.0.0" });
server.tool(
  { name: "example", description: "...", inputSchema: z.object({}) },
  () => ({ content: [{ type: "text", text: "ok" }] }),
);

Deno.serve((request) => server.fetch(request));
```

Don't pass `server.fetch` directly as the `Deno.serve` handler — Deno's handler signature carries a second `info` argument that doesn't match Hono's `env` parameter; wrap it in a one-argument closure as shown. Do not call `server.listen()` here; `Deno.serve` owns the HTTP boundary.

## Build & deploy commands

```bash
# Build with public MCP endpoint and external asset CDN
MCP_URL=https://<project>.deno.dev \
MCP_ASSETS_URL=https://<cdn-origin> \
npm run build
```

Deploy `server.ts` through your current Deno Deploy project configuration. This file documents the mcp-use fetch boundary and asset layout, not a pinned Deno deployment CLI surface (no first-party mcp-use Deno Deploy guide exists). Upload the assets to the CDN/object store separately.

The CLI prints that `.mcp-use/build/views/` must be uploaded and reports a non-default `basePath`, but it does **not** print a complete destination URL. With the default base path, publish:

```text
.mcp-use/build/views/<view-name>/
  → https://<cdn-origin>/mcp/_mcp-use/views/<view-name>/

.mcp-use/build/views/public/
  → https://<cdn-origin>/mcp/_mcp-use/public/
```

Preserve the directory hierarchy and inspect `.mcp-use/build/manifest.json` to verify the generated absolute asset URLs before upload.

## Env & assets

- **MCP_URL (build-time):** Public Deno Deploy origin (required for view embedding; no path)
- **MCP_ASSETS_URL (build-time):** External CDN origin for `.mcp-use/build/views/`
- **Runtime access:** Configure environment/network/file access through the current Deno Deploy project controls; this guide does not assert a deployment-CLI permission flag set
- **Asset host:** Must satisfy the View iframe's CORS and CSP requirements

## Gotchas

- **No filesystem:** Server cannot read `.mcp-use/build/views/` from disk — assets must be external
- **Asset host CORS:** View iframes require origin + CSP domain whitelisting on CDN
- **Verify after deploy:** Always run `mcp-use@beta screenshot` against live deployment before advertising
- **Session state:** Deno Deploy is stateless (fresh instance per request, same as the framework's own per-request server model); maintain application state externally (DB, KV store). `RequestContext.requestState` is a distinct mechanism — it reads opaque state the *client* echoes back across an `input_required` round, not a general session-persistence API; don't reach for it as a substitute for external storage.
