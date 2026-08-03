# Pre-Deploy Checklist

*Read this before every production deploy.*

Skip these and you will have post-deploy outages. Work through all sections.

## 1. Build & Types

- [ ] `npm run build` succeeds locally with no unhandled errors.
- [ ] `.mcp-use/build/` exists with Views subdirectory (if using views).
- [ ] `npm run typecheck` passes; types current (run after tool registration changes).

## 2. Configuration

- [ ] All environment variables documented in `.env.example` (no actual secrets in repo).
- [ ] Environment variables set in platform's secret manager (deploy flags or platform dashboard).
- [ ] `NODE_ENV=production` set at deploy time, not hardcoded.
- [ ] `PORT` read from `process.env.PORT`, not hardcoded.

## 3. Security

- [ ] No hardcoded secrets, API keys, or database URLs in source code.
- [ ] `.env*` files in `.gitignore` (except `.env.example`).
- [ ] Zod validation on every tool input schema; no `z.any()`.
- [ ] OAuth provider configured if server is publicly accessible.
- [ ] CORS configured with explicit origins (no `"*"` in production).

## 4. Server Code

- [ ] Server entry `export default`s something. For Manufact Cloud / `mcp-use start` / Cloud Run / Railway (any Node CLI-managed listener), export the `MCPServer` instance itself (`export default server;`) — the CLI's `start` command requires the default export to expose a `.listen()` method and throws otherwise. For serverless/edge platforms, expose the same Web boundary through the platform's documented shape: Vercel can `export default server`; Cloudflare exports an object whose `fetch` wrapper calls `server.fetch`; Deno calls `Deno.serve((request) => server.fetch(request))`; Hono mounts `server.fetch(c.req.raw)`.
- [ ] Server does NOT call `listen()` if deploying to serverless/edge (Vercel, Cloudflare, Supabase, Deno Deploy).
- [ ] Server DOES call `listen()` — or is started via `mcp-use start` / `npm start`, which calls it for you — if deploying to a Node-based platform (Manufact, Cloud Run, Railway).
- [ ] Health endpoint registered at the root level (not nested under the MCP `basePath`): `server.get("/health", (c) => c.json({ ok: true }))`.

## 5. Staging Smoke Test

Before production deploy:

- [ ] Deploy to staging environment first (separate service/app/project).
- [ ] **Every server:** connect to the exact staging MCP URL, list tools, and complete one relevant tool call via Inspector, `mcp-use client`, or the verified curl flow.
- [ ] **Views only:** render the View with `npx mcp-use@beta screenshot --mcp <staging-mcp-url> --tool <name> --output test.png`.
- [ ] **Views only:** no CSP violations, missing assets, or runtime errors in the iframe/browser console.

## 6. Git (if using GitHub deploy)

- [ ] `git status` clean; all changes committed.
- [ ] Latest commit pushed to origin (not just local).
- [ ] Platform has GitHub App access (check one-time during first deploy).

## 7. Post-Deploy Verification

After platform reports success:

- [ ] Health endpoint responds: `curl -s <deployed-origin>/health | jq .`
- [ ] **Every server:** exact deployed MCP URL connects, tools list successfully, and one relevant tool call succeeds.
- [ ] **Views only:** live screenshot renders expected content, and asset/CSP console checks are clean.
- [ ] Production client configurations updated with new URL if it changed.

---

See also:
- `03-docker.md` for production Dockerfile patterns.
- `references/24-production/` for hardening and scaling guidance.
- `references/27-troubleshooting/01-error-catalog.md` for debugging.
