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

- [ ] Server entry exports `default` (for Node: `export default server.fetch`).
- [ ] Server does NOT call `listen()` if deploying to serverless/edge (Vercel, Cloudflare, Supabase).
- [ ] Server DOES call `listen()` if deploying to Node-based platform (Manufact, Cloud Run, Railway).
- [ ] Health endpoint registered before `listen()` if needed: `server.get("/health", (c) => c.json({ status: "ok" }))`.

## 5. Staging Smoke Test

Before production deploy:

- [ ] Deploy to staging environment first (separate service/app/project).
- [ ] Inspector connects and lists all tools.
- [ ] One tool called end-to-end; result correct.
- [ ] Views render (if applicable): `npx mcp-use@beta screenshot --mcp <staging-url>/mcp --tool <name> --output test.png`.
- [ ] No CSP violations or 404s in browser console.

## 6. Git (if using GitHub deploy)

- [ ] `git status` clean; all changes committed.
- [ ] Latest commit pushed to origin (not just local).
- [ ] Platform has GitHub App access (check one-time during first deploy).

## 7. Post-Deploy Verification

After platform reports success:

- [ ] Health endpoint responds: `curl -s <deployed-url>/mcp/health | jq .`
- [ ] Inspector connects and lists tools.
- [ ] One full tool call succeeds.
- [ ] If Views used: screenshot from live endpoint shows rendered content (not broken links).
- [ ] Production client configurations updated with new URL if it changed.

---

See also:
- `03-docker.md` for production Dockerfile patterns.
- `references/24-production/` for hardening and scaling guidance.
- `references/27-troubleshooting/01-error-catalog.md` for debugging.
