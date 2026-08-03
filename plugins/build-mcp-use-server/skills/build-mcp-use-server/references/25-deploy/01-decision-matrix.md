# Deployment Decision Matrix

*Read this when choosing a deployment target and View-asset topology.*

All documented targets use the stateless Web Fetch boundary. Choose by runtime and how the target publishes `.mcp-use/build/views/`.

| Target | Runtime pattern | Handler or command | View assets | Choose it when |
|---|---|---|---|---|
| **Manufact Cloud** | Managed Node/filesystem | `mcp-use deploy` | Deployed with the server | You want managed builds, logs, GitHub or source upload, and branch previews |
| **Vercel Function** | Node serverless | Export the `MCPServer` from `api/mcp.ts` | Function bundle; include nested asset paths | You want a non-Next Vercel Function |
| **Vercel + Next.js** | Next.js App Router | `withMcpUse()` + `createNextHandler()` | Integrated into the Next.js build | The MCP server lives inside a Next.js app |
| **Cloudflare Workers** | Edge + co-located static binding | Asset route, otherwise `server.fetch` | Workers static-assets binding | You can publish `.mcp-use/build` through a Worker binding |
| **Google Cloud Run** | Node container/filesystem | `mcp-use start` in a container | Built into the container | You need a Cloud Run service, optionally protected by Cloud IAM |
| **Supabase Edge Functions** | Deno/Edge + external Storage for views | `Deno.serve((req) => server.fetch(req))` | Supabase Storage bucket (external CDN) | You deploy through a current Supabase CLI; Views require a Storage bucket |
| **Deno Deploy** | Edge + external assets | `Deno.serve((req) => server.fetch(req))` | Publish under `MCP_ASSETS_URL` using the manifest paths | You can operate a generic Deno deployment and external asset host |
| **Bun** | Node-compatible filesystem | `export default server` (Bun auto-serves objects with `.fetch`) | Deployed with the server | Your host runs Bun and preserves the nested `_mcp-use` route |
| **Hono** | Host-dependent | Mount `server.fetch` at `/mcp` and `/mcp/*` | Host-dependent | You already use Hono and can preserve the nested asset subtree |
| **Railway** | Generic Node/filesystem | `export default server`; `npm start` | Deployed with the server | Railway can build `.mcp-use/build` and run the generated start script |

Fly.io is intentionally absent: no v2 ground-truth deployment page exists.

## Pick the Asset Topology

### Filesystem runtime

Use for Manufact Cloud, Railway, Bun, Cloud Run, and Node Vercel Functions:

```bash
MCP_URL=https://api.example.com mcp-use build
```

Deploy `.mcp-use/build` with the server. Forward the MCP route and its `_mcp-use` subtree to the same handler.

### Edge with co-located assets

Use for Workers and Edge Functions:

```bash
MCP_URL=https://api.example.com \
MCP_ASSETS_URL=https://api.example.com \
mcp-use build
```

Route `<basePath>/_mcp-use/*` through the platform's static binding and all other requests to `server.fetch(request)`. Map generated public paths to the binding's on-disk layout — for `.mcp-use/build` as the asset root, `<basePath>/_mcp-use/views/...` becomes `/views/...` and `<basePath>/_mcp-use/public/...` becomes `/views/public/...`.

### Edge with external assets

```bash
MCP_URL=https://api.example.com \
MCP_ASSETS_URL=https://cdn.example.com/mcp-assets \
mcp-use build
```

Publish `.mcp-use/build/views/<name>/` at `${MCP_ASSETS_URL}<basePath>/_mcp-use/views/<name>/`, and publish `.mcp-use/build/views/public/` at `${MCP_ASSETS_URL}<basePath>/_mcp-use/public/`. Preserve the directory structure and verify the generated absolute URLs in `.mcp-use/build/manifest.json`; the CLI prints the local upload directory and non-default `basePath`, not a complete destination URL. Configure the asset origin for the View iframe's CORS and CSP requirements.

## Verify the Rendered View

```bash
mcp-use screenshot \
  --mcp https://api.example.com/mcp \
  --tool <tool-name> \
  --output live-view.png
```

Do not treat an HTTP 200 alone as deployment proof; render the View from the public endpoint.
