# Pre-Deploy Checklist

Run through this before every production deploy. Skipping items is the most common cause of post-deploy outages.

---

## 1. Configuration

- [ ] All env vars documented in a `.env.example` and set in the target platform's secret manager.
- [ ] `NODE_ENV=production` is set.
- [ ] `PORT` is read from env (`process.env.PORT`), not hardcoded.
- [ ] `baseUrl` is set explicitly when widgets are involved (default to `MCP_URL` env). Resolution order: `baseUrl` config → `MCP_URL` env → `http://{host}:{port}`.

## 2. Security

- [ ] `cors` is configured with explicit origins (no `"*"` in production).
- [ ] `allowedOrigins` is set to the production hostnames (DNS rebinding protection).
- [ ] `mcp-session-id` is in both `allowHeaders` and `exposeHeaders`.
- [ ] No secrets in code or in `dist/`. `.env` is in `.gitignore`.
- [ ] OAuth provider configured if the server is publicly addressable.
- [ ] Zod validation on every tool input. No untyped `any` reaching tool bodies.

## 3. Reliability

- [ ] `SIGTERM` and `SIGINT` handlers call `await server.close()` with a hard 10-second timeout.
- [ ] Cleanup order: server → connection pools → external clients → process exit.
- [ ] For multi-replica deploys: `RedisSessionStore` configured. In-memory store is single-replica only.
- [ ] Health endpoint registered explicitly (`server.get("/health", ...)`) before `listen()` — otherwise the Inspector catch-all serves HTML on `GET /health` (see `27-troubleshooting/01-error-catalog.md`).

## 4. Compatibility

- [ ] `mcp-use` at the version you intend (`npm ls mcp-use`).
- [ ] `zod@^4.0.0` declared explicitly in your own `package.json` (`peerDependency` since v1.21.5).
- [ ] `tsconfig.json` has `"module": "node16"`, `"moduleResolution": "node16"`, `"target": "ES2022"`.
- [ ] `package.json` has `"type": "module"` if your code uses ESM `import`.

## 5. Build

- [ ] `npm run build` (or `mcp-use build`) succeeds locally with no warnings you don't understand.
- [ ] `dist/mcp-use.json` exists. Without it, `mcp-use deploy` and `mcp-use start` cannot locate the entry.
- [ ] Generated types are current: `mcp-use generate-types` after every tool registration change.
- [ ] Widget builds succeed (if applicable). `dist/resources/widgets/` populated.

## 6. Pre-deploy validation against staging

- [ ] Deploy to a staging URL first (separate Manufact Cloud project, separate Cloud Run service, separate Fly app).
- [ ] Run the Inspector against the staging URL — every tool callable, schemas correct.
- [ ] `curl -i {url}/health` returns JSON, not HTML.
- [ ] OAuth flow exercised end-to-end if applicable.
- [ ] If using widgets: open in the Inspector, confirm no CSP violations in the browser console.
- [ ] Smoke-test from the production client config (Claude Desktop, Codex, etc.) with the staging URL.

## 7. Git hygiene (Manufact Cloud and similar GitHub-detecting platforms)

- [ ] All changes committed: `git status` is clean.
- [ ] Pushed to the remote: `git log @{u}..HEAD` is empty.
- [ ] `.mcp-use/project.json` tracked in git: `!.mcp-use/project.json` in `.gitignore`. Without this, redeploys assign new subdomains and break custom domains.

## 8. Post-deploy verification

After the deploy succeeds:

1. `curl -s {url}/health | jq .` — should be JSON with `status: "ok"`.
2. Connect with the Inspector — verify capability list, tool list, callable.
3. Call one tool end-to-end.
4. Update production client configs.
5. If a custom domain is configured: verify it still resolves to the new deployment.

---

See also:
- `03-docker.md` for the production Dockerfile.
- `26-anti-patterns/` for what to avoid.
- `27-troubleshooting/01-error-catalog.md` for known failure modes by symptom.
