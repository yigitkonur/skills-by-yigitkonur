# Deploying Next.js MCP to Vercel

*Read this when deploying a Next.js embedded MCP server to Vercel.*

Vercel deploys Next.js apps as usual. See references/25-deploy/platforms/02-vercel.md for the complete platform guide, including build environment, function bundling, preview URLs, and domain binding.

MCP-specific notes:

1. **Build:** `withMcpUse` integrates with the Next.js build. Views compile to `.mcp-use/build/` during `next build`; no extra step needed.

2. **Routes:** The MCP endpoint is a standard Next.js Route Handler at `/api/mcp`. Vercel automatically includes it in the deployment.

3. **Verification:** After deploy, test the public MCP endpoint using the inspector or `mcp-use client`:
```bash
npx @mcp-use/inspector --url https://your-app.vercel.app/api/mcp
```

See references/25-deploy/platforms/02-vercel.md for environment variables, secrets, and scaling considerations.
