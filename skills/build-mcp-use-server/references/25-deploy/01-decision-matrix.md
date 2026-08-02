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
| **Supabase Edge Functions** | Edge + co-located static files | Asset route, otherwise `server.fetch` | Function `static_files` | You deploy through a current Supabase CLI without Docker or Storage |
| **Deno Deploy** | Edge + external or co-located assets | Web Fetch handler | Publish at `MCP_ASSETS_URL` | You can deploy generated Views to the build-reported asset path |
| **Bun** | Node-compatible filesystem | Expose `server.fetch` at the MCP route | Deployed with the server | Your host runs Bun and preserves the nested `_mcp-use` route |
| **Hono** | Host-dependent | Mount `server.fetch` at `/mcp` and `/mcp/*` | Host-dependent | You already use Hono and can preserve the nested asset subtree |
| **Railway** | Node/filesystem | Bind `0.0.0.0:$PORT`; deploy with `railway up` | Deployed with the server | You want the documented Railway filesystem pattern |

Fly.io is intentionally absent: no v2 ground-truth deployment page exists.

## Pick the Asset Topology

### Filesystem runtime

Use for Manufact Cloud, Railway, Bun, Cloud Run, and Node Vercel Functions:

```bash
MCP_URL=https://api.example.com/mcp mcp-use build
```

Deploy `.mcp-use/build` with the server. Forward the MCP route and its `_mcp-use` subtree to the same handler.

### Edge with co-located assets

Use for Workers and Edge Functions:

```bash
MCP_URL=https://api.example.com/mcp \
MCP_ASSETS_URL=https://api.example.com \
mcp-use build
```

Route `<basePath>/_mcp-use/*` to the platform's static binding and all other requests to `server.fetch(request)`.

### Edge with external assets

```bash
MCP_URL=https://api.example.com/mcp \
MCP_ASSETS_URL=https://cdn.example.com/mcp-assets \
mcp-use build
```

Publish `.mcp-use/build/views/` at the exact destination printed by the build. Configure the asset origin for the View iframe's CORS and CSP requirements.

## Verify the Rendered View

```bash
mcp-use screenshot \
  --mcp https://api.example.com/mcp \
  --tool <tool-name> \
  --output live-view.png
```

Do not treat an HTTP 200 alone as deployment proof; render the View from the public endpoint.
