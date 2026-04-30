---
name: make-railway
description: Use skill if you are authoring a `make prod` target that deploys a Next.js or Node project to Railway with parallel multi-service deploys, env wiring, and optional git-hook CI/CD.
---

# Make Railway

Author the `make prod` target that ships any Next.js / Node project to Railway, plus the git-hook scaffolding for local CI/CD without GitHub Actions. The deploy contract: parallel multi-service uploads, terminal-status poll, annotated deploy messages, public-URL probe.

## How to think about this

Railway is the right home for **anything with a long-running process**: Next.js apps with BullMQ workers, SSE keep-alives that exceed Vercel's serverless 5-minute window, background queue consumers, DB-tier services. Vercel handles pure-static + serverless edge — Railway handles everything Vercel can't.

The `make prod` workflow is opinionated:

1. **Pre-flight** the toolchain (`railway whoami`, `railway status`) and refuse early with an actionable hint if anything's missing.
2. **Annotate** the deploy message with `branch@sha[+dirty]` so the Railway deploy log doubles as a forensic trail.
3. **Parallel upload** every service (web + worker + cron) in one pass — Railway's `--detach` makes this safe.
4. **Poll** until every service exits BUILDING/DEPLOYING and lands at SUCCESS or FAILED.
5. **Probe** the public URLs to confirm HTTP reachability post-deploy.

For CLI command reference, defer to the **`use-railway`** skill. This skill covers the *workflow* — how to compose a deploy contract, when to find vs create, how to handle the multi-service case.

## Use this skill when

- The user asks for "make prod", "deploy to Railway", "Railway deploy script", "git hooks for CI/CD without GitHub Actions".
- Project has Docker, BullMQ workers, SSE/WebSocket keep-alives, or any long-running process.
- The team wants a one-command production deploy from any contributor's machine.

## Do not use this skill when

- The user wants to deploy a pure-static Next.js app or marketing site → route to **make-vercel** (it has tighter Next.js integration and free preview deploys per PR).
- The user is asking how to use a specific `railway` CLI command → route to **use-railway**.
- The user wants GitHub Actions CI/CD — that's a different shape; this skill covers local git-hook CI/CD as the explicit alternative.

## Workflow

### 1. Pre-flight detection

Before generating Make targets, capture project state:

```bash
# Railway toolchain
command -v railway >/dev/null 2>&1 || echo "MISSING: brew install railway"
railway whoami 2>&1 | head -3                # auth state
railway status 2>&1 | head -3                # project link

# What services exist (find-or-create planning)
railway service status --all 2>&1

# Dockerfile vs Nixpacks
ls Dockerfile docker-compose.yml 2>/dev/null

# Worker pattern detection
grep -rE "ZEO_ROLE|BullMQ|Worker\\(|new Worker\\b" src/ 2>/dev/null | head -3

# Existing env vars on the primary service
railway variables --service <name> --kv 2>&1 | grep -iE "DATABASE_URL|REDIS_URL|PORT" | head
```

If pre-flight fails, surface the exact missing piece. Don't generate Make targets that crash on first run.

### 2. Decide the service shape

Use the decision tree in `references/service-topology.md`. Common shapes:

- **Single web service** — most projects start here
- **Web + worker** — Next.js app + BullMQ background processor (zeo-radar pattern)
- **Web + worker + cron** — add a cron service for scheduled jobs
- **Multi-tenant** — `app-prod`, `app-staging`, `app-noauth` from the same image

The decision shapes the Makefile: one service in `WEB_SERVICES :=`, or many.

### 3. Find-or-create services

Railway's CLI doesn't have a single "find or create" verb. The workflow:

```bash
# Find: check if a named service exists
EXISTS=$(railway service status --all 2>&1 | awk '{print $1}' | grep -x "MY_SERVICE" || true)
if [ -z "$EXISTS" ]; then
  railway service create --name MY_SERVICE
fi
```

See `references/find-or-create.md` for the full pattern, including handling both interactive (TTY) and CI (non-TTY) cases.

### 4. Generate the Makefile

Use the template in `references/makefile-template.md`. Replace these placeholders:

| Placeholder | What to replace with |
|---|---|
| `WEB_SERVICES` | Space-separated Railway service names (`web` or `web worker` or `web worker cron`) |
| `URL_PROD_PRIMARY` | Primary public URL (`https://app.example.com` or `https://<svc>.up.railway.app`) |
| `URL_PROD_SECONDARY` | Optional second URL (when there's auth + noauth deploys) |

### 5. Wire env vars (find-or-update pattern)

Railway env vars are per-service. The Makefile should NOT hard-code values — those are secrets. Instead, document the required keys and provide an interactive setup target:

```makefile
env-pull:
	@for svc in $(WEB_SERVICES); do \
	  printf "→ pulling env from $$svc\n"; \
	  railway variables --service $$svc --kv > .env.railway.$$svc; \
	done

env-push:
	@printf "Use: railway variables --service NAME --set KEY=VAL\n"
	@printf "or:  railway variables --service NAME --set-from-env <FILE>\n"
```

See `references/env-management.md` for the full env workflow including secret rotation, public/private URLs, and inter-service refs (`RAILWAY_PRIVATE_DOMAIN` for in-tailnet, `DATABASE_PUBLIC_URL` for local-dev).

### 6. Wire git-hook CI/CD (the optional but recommended layer)

Three hooks cover the entire pre-push lifecycle. See `references/git-hooks.md` for the full installer.

```makefile
install-hooks:
	@bash scripts/install-hooks.sh
```

Hooks installed:

- **`pre-commit`** — format + lint-staged (fast, blocks broken commits)
- **`pre-push`** — typecheck + lint + test (slow, blocks broken pushes)
- **`post-merge`** — auto-`npm install` if package.json changed (silent fix-up)

The `make install-hooks` target makes them idempotent and discoverable. Hooks live in `scripts/git-hooks/` (committed) and are symlinked into `.git/hooks/` (not committed).

### 7. Generate the actual deploy

End-to-end test:

```bash
make prod   # should pre-flight, upload in parallel, poll until SUCCESS, print URLs
make verify # should HTTP-probe every URL_PROD_*
```

If parts fail, the recovery paths in this SKILL.md cover the common cases.

## Decision rules

- **Pre-flight refuses, never crashes.** `command -v railway` + `railway whoami` + `railway status` all succeed before any state-changing operation. Each failure prints a one-line actionable hint.
- **Parallel deploys, sequential polling.** `railway up --detach -s name` for each service in a `&`-backgrounded loop, then `wait` to join. Then poll status until terminal.
- **Annotate every deploy.** `-m "branch@sha[+dirty]"` makes the Railway deploy log a forensic trail. `+dirty` means the working tree had uncommitted changes — surface this to the user as a yellow warning.
- **Don't kill the deploy on a dirty tree.** Warn, but proceed. Sometimes the user knows what they're doing.
- **Don't silently push secrets.** `railway variables --set` requires explicit user intent. Never `--set` from a Makefile recipe.
- **Don't try to recover from failed builds inside the Makefile.** A failed build needs human eyes on `railway logs --service NAME --tail 100`. Print that hint and exit non-zero.

## Recovery paths

| Symptom | Cause | Fix |
|---|---|---|
| `railway: command not found` | CLI not installed | `brew install railway` (or `npm install -g @railway/cli`) |
| `Unauthorized` from `railway whoami` | Not logged in | `railway login` (opens browser; manual step) |
| `Project not linked` | No `.railway/` in repo | `railway link` (interactive picker) — if non-TTY, `railway link --project <id>` |
| One service hangs in BUILDING for 10+ min | Build genuinely slow, OR Dockerfile has an infinite step | `railway logs --service NAME --tail 100` — usually a Prisma/migration step blocking |
| `Bind for 0.0.0.0:PORT failed: port is already allocated` (deploy log) | Multiple replicas, or app hard-codes a port | Make sure app reads `process.env.PORT` and binds `0.0.0.0`, not `localhost` |
| Deploy SUCCESS but URL returns 502 | App crashed at startup | `railway logs --service NAME` — usually missing env var or migration |
| Deploy SUCCESS but DB queries fail | App pointing at `RAILWAY_PRIVATE_DOMAIN` from a different service group | Use `${{Postgres.DATABASE_URL}}` reference in env, not literal URLs |
| `make verify` returns 404 on the URL | Service exists but no domain assigned | `railway domain` (interactive) or `railway domain --service NAME --port 3000` |
| Worker service deploys but never picks up jobs | `ZEO_ROLE` env not set, or wrong start command | Web service: default `CMD`. Worker: override `CMD` in `railway.toml` or via Settings → Custom Start Command |
| Multi-service deploy: web+worker version skew | Deployed simultaneously, web hits worker before worker rolls | Deploy worker first, wait for SUCCESS, then deploy web. BullMQ dedup handles the crossover |
| Public URL probe times out | DNS hasn't propagated yet (custom domain) | Wait 60s for Railway's edge to pick up; `make verify` again. Built-in `*.up.railway.app` should be instant |

## Customizing the recipe

- **Non-Next frameworks (Express, Hono, Fastify, plain Node):** structure unchanged. The `WEB_SERVICES` list still applies. Pick a Dockerfile or let Nixpacks auto-detect.
- **Backend-only project (no UI):** drop the `URL_PROD_*` probes; the deploy is the contract.
- **Monorepo with multiple apps:** generate one `make prod-<app>` per app, each with its own `WEB_SERVICES`. Or one umbrella `make prod` that fans out — see `references/monorepo.md`.
- **Worker-only deploy:** same pattern, just `WEB_SERVICES := worker`.
- **Cron via Railway Cron:** create the service, set the schedule in the Railway UI (no CLI), point the start command at your cron entrypoint. See `references/cron-services.md`.
- **GitHub Actions CI/CD instead of git hooks:** out-of-scope here; see GitHub's docs. The git-hook approach is for teams that want zero-CI-vendor lock-in.

## Reference routing

| File | Read when |
|---|---|
| `references/makefile-template.md` | Generating the Make targets — full template with every placeholder annotated. |
| `references/find-or-create.md` | Detecting existing services, creating new ones, handling TTY vs non-TTY contexts. |
| `references/service-topology.md` | Picking the service shape: single web, web+worker, multi-tenant, etc. |
| `references/env-management.md` | Setting env vars, pulling them locally for `.env.local`, secret rotation, public vs private DB URLs. |
| `references/dockerfile-vs-nixpacks.md` | Choosing build mode, Dockerfile recipes for Next.js + Prisma, when standalone output breaks server actions. |
| `references/port-binding.md` | The `process.env.PORT` rule, `0.0.0.0` binding, why `localhost` binding fails on Railway. |
| `references/cross-service-refs.md` | `RAILWAY_PRIVATE_DOMAIN` vs `DATABASE_PUBLIC_URL`, in-cluster networking, env var references. |
| `references/migration-strategy.md` | When `prisma migrate deploy` runs, baselining a `db push`-provisioned legacy DB, idempotent boot scripts. |
| `references/git-hooks.md` | The pre-commit/pre-push/post-merge installer + hook scripts; idempotence guarantees. |
| `references/monorepo.md` | Multi-app monorepos: per-app service mapping, shared Dockerfile vs per-app Dockerfile, root vs subdir builds. |
| `references/cron-services.md` | Railway Cron setup, schedule syntax, why CLI doesn't manage schedules. |
| `references/observability.md` | `railway logs` + `railway logs --tail`, structured logging, when to wire Sentry/PostHog. |
| `references/cross-skill-handoffs.md` | When to defer to `use-railway` (CLI), `make-local` (dev), `make-vercel` (alt prod). |

## Cross-skill handoffs

- For raw `railway` CLI questions (`railway logs`, `railway scale`, `railway run`, `railway connect <db>`, `railway ssh`) — defer to **use-railway**.
- For local dev with the same project — **make-local**.
- For deciding Vercel vs Railway — **make-vercel** (the decision matrix lives there).

## Guardrails

- Never `--set` env vars from a Makefile recipe. Document the keys; let the user run the command.
- Never push to production without `railway whoami` + `railway status` + a clean working-tree warning shown.
- Never poll forever. Cap polling at ~10 minutes (80 × 8s); past that, surface the deploy URL and exit non-zero so the user can investigate.
- Never assume single-service. The Makefile must use a `WEB_SERVICES :=` list and a `for svc in $(WEB_SERVICES)` loop, even if there's only one service today.
- Never silently overwrite `.git/hooks/*`. The installer must back up existing hooks (`*.bak`) and warn.

## Final checks

Before declaring done:

- [ ] `make prod` completes end-to-end against a real Railway project (with the user's auth)
- [ ] Pre-flight refuses cleanly when railway CLI is missing/unauthenticated/unlinked
- [ ] Deploy message includes `branch@sha[+dirty]` annotation visible in Railway dashboard
- [ ] Polling exits in under 10 minutes; if longer, prints the deploy log URL and exits non-zero
- [ ] `make verify` HTTP-probes every URL with 2xx/3xx as success
- [ ] Worker service (if present) starts with the right `ZEO_ROLE`-style env or override
- [ ] Git hooks install cleanly (`make install-hooks`); pre-existing hooks are backed up to `*.bak`
- [ ] `make prod` runs cleanly on a clean working tree (no `+dirty`)
