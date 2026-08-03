# Deploying Next.js MCP to Vercel

*Read this when deploying a Next.js embedded MCP server to Vercel.*

Vercel deploys Next.js apps as usual — connect the repo (or run `npx vercel deploy`) and Vercel builds and hosts the whole app, MCP route included, with no separate MCP deployment step.

MCP-specific notes:

1. **Build:** `withMcpUse` runs `mcp-use build` as a child process every time Next evaluates `next.config` (both `next dev` and `next build`). Views compile to `.mcp-use/build/views/` with a manifest at `.mcp-use/build/manifest.json`; no extra step needed.

2. **Routes:** The MCP endpoint is a standard Next.js Route Handler at `/api/mcp` (an optional catch-all — see references/19-nextjs-drop-in/02-route-and-file-placement.md). Vercel automatically includes it in the deployment.

3. **Serverless bundling:** `withMcpUse` adds `.mcp-use/build/**/*` to Next's `outputFileTracingIncludes` for the route's `basePath`, so Vercel's file tracer bundles the compiled view assets into the deployed function. Without this, view JS/CSS would be missing at runtime even though `next build` succeeded locally.

4. **No built-in `/inspector` route:** the embedded Next.js topology does not mount `@mcp-use/inspector`. Verify the deployed endpoint with the standalone Inspector CLI or `mcp-use client`, not a same-origin `/api/mcp/inspector` path:
```bash
npx @mcp-use/inspector --url https://your-app.vercel.app/api/mcp
```

See references/25-deploy/platforms/02-vercel.md for the non-Next `mcp-use` Vercel Function pattern (`api/mcp.ts` exporting `server.fetch` directly) — useful background for the Vercel Function model this Next.js Route Handler builds on.
