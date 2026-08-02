# Deployment Platform Decision Matrix

*Read this when choosing a deployment platform for your mcp-use v2 server.*

Use this matrix to pick the right platform. All platforms support the stateless, Fetch-API-based mcp-use v2 server model; differences lie in build strategy, asset handling, and Node API availability.

| Platform | Runtime | Build | Assets | Edge | Free | Best For |
|----------|---------|-------|--------|------|------|----------|
| **Manufact Cloud** | Node | Auto-detect; `--no-github` upload | Filesystem | No | Hobby | Quickest deploy; managed; preview URLs |
| **Vercel (Next.js)** | Node | `withMcpUse()`; integrated | Filesystem | No | Yes | Existing Next.js; tightly integrated |
| **Vercel (Functions)** | Node | Manual; catch-all + assets | Bundled | No | Yes | Non-Next on Vercel |
| **Cloudflare Workers** | Edge (V8) | Build + static binding | Static binding | Yes | Yes | Global low-latency; existing Workers |
| **Google Cloud Run** | Node | Docker build; gcloud deploy | Filesystem | No | Free quota | GCP ecosystem; auth via Cloud IAM |
| **Supabase Edge Functions** | Edge (Deno) | Build + static_files config | Co-located | Yes | Yes | Existing Supabase; no Docker |
| **Deno Deploy** | Edge (Deno) | Build + external CDN | External CDN | Yes | Free | Deno community; global edge |
| **Hono** | Node or Edge | Mount `server.fetch` at route | Runtime-dependent | Optional | Varies | Framework flexibility |
| **Bun** | Node | npm scripts; auto-detected | Filesystem | No | Free | Experimental speed; local dev |
| **Railway** | Node | Auto-detect GitHub | Filesystem | No | Free trial | Minimal config; GitHub push-to-deploy |

## Quick Start

**Fastest first deploy?** → Manufact Cloud + `mcp-use deploy`.

**Next.js already deployed?** → Vercel with `withMcpUse()` wrapper.

**Global, edge-only?** → Cloudflare Workers or Supabase Edge.

**GCP ecosystem?** → Google Cloud Run.

**No framework vendor lock-in?** → Hono or Railway.

## Build & Asset Patterns

**Filesystem pattern** (Node: Manufact, Vercel, Railway, Bun, Cloud Run):
- Deploy `.mcp-use/build/` alongside server
- Server reads Views from disk; serves at same public origin
- Build: `MCP_URL=https://api.example.com/mcp npm run build`

**Co-located static pattern** (Workers, Supabase, Deno):
- Platform static binding or config includes generated Views
- Route `/mcp/_mcp-use/*` to assets; other requests to `server.fetch`
- Build: `MCP_URL=... MCP_ASSETS_URL=... npm run build`

**External CDN pattern** (any platform with external storage):
- Views on separate CDN (e.g., S3, Cloudflare R2)
- Build: `MCP_URL=... MCP_ASSETS_URL=https://cdn.example.com/assets mcp-use build`

## After Deploy

Verify rendered View with the screenshot command:

```bash
npx --yes mcp-use@beta screenshot \
  --mcp https://your-deployed-url/mcp \
  --tool <tool-name> \
  --output deployed-view.png
```

This confirms Views render correctly and assets load from the live endpoint.
