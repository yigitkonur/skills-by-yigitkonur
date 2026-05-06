---
name: make-vercel
description: Use skill if you are authoring a `make deploy` target that ships Next.js to Vercel — covers find-or-create, env scoping, custom domains, function size limits, and when Vercel is wrong.
---

# Make Vercel

Author the `make deploy` target that ships a Next.js project to Vercel. Cover the find-or-create flow, env scoping per environment, monorepo root selection, custom domains, and the workloads where Vercel is the wrong choice.

## How to think about this

Vercel is purpose-built for Next.js. Static + edge + serverless function deploys are basically free, preview deploys per-PR are automatic, custom domains take 5 minutes. The CLI (`vercel`) is small and well-shaped.

Vercel is the wrong choice when the project needs:
- **Long-running processes** — BullMQ workers, SSE that exceeds 5 minutes, WebSocket servers
- **Background queue consumers** — Vercel functions are stateless; consume + ack patterns don't survive
- **Heavy native dependencies** — function bundle size limit is 50MB compressed; Sharp + ffmpeg + native crypto blow past it
- **Frequent stateful jobs** — Vercel cron exists but is paid past the free tier and has 10s timeout in hobby

For those: route to **make-railway** (the decision matrix is in `references/vercel-vs-railway.md`).

The `make deploy` workflow:

1. Pre-flight: `vercel whoami`, project linked
2. Pull env from Vercel into `.env.local` for parity (optional)
3. `vercel --prod` for production deploys; `vercel deploy` for preview
4. HTTP-probe the deployment URL

## Use this skill when

- The user asks for "make deploy", "deploy to Vercel", "Vercel deploy script", "ship this Next.js project".
- Project is pure-static or serverless-Next.js shape.
- The user wants automatic per-PR preview deploys (Vercel's killer feature).

## Do not use this skill when

- The project has BullMQ workers / SSE / WebSocket / any long-running process → route to **make-railway**.
- The user wants raw `vercel` CLI commands → defer to Vercel docs (no first-party "use-vercel" skill exists yet).
- The project is a backend service (Express/Hono) without a frontend → make-railway.

## Workflow

### 1. Pre-flight detection

```bash
# Vercel toolchain
command -v vercel >/dev/null 2>&1 || echo "MISSING: npm install -g vercel"
vercel whoami 2>&1 | head -3              # auth state
[ -d .vercel ] && cat .vercel/project.json | jq -c '{projectId, orgId, projectName}'

# Framework detection (Vercel auto-detects but worth knowing)
cat package.json | jq -r '.dependencies.next // "no-next"'
cat next.config.* 2>/dev/null | head -5

# Monorepo check
[ -f turbo.json ] || [ -f pnpm-workspace.yaml ] && echo "MONOREPO"
```

If pre-flight fails, surface the missing piece. Don't generate Make targets that crash.

### 2. Find-or-create via `vercel link`

`vercel link` is interactive by default — picks an existing project from a list, or creates a new one with framework defaults. To make it CI-friendly:

```bash
# Interactive (devs first time):
vercel link

# Non-interactive (CI / scripts): use the .vercel/project.json from a manual run, OR:
vercel link --confirm --yes  # picks defaults: project name = directory name, framework = auto
```

The `.vercel/` directory holds the link state. **Add to `.gitignore`** (Vercel does this on new projects). Each contributor links separately.

See `references/find-or-create.md` for the full pattern, including listing existing projects (`vercel projects ls`) and naming conventions.

### 3. Generate the Makefile

Use the template in `references/makefile-template.md`. Replace these placeholders:

| Placeholder | What to replace with |
|---|---|
| `PROD_URL` | Production URL — typically the custom domain. Default: `https://<project>.vercel.app`. |
| `PREVIEW_URL_PATTERN` | Used to compute the per-deploy preview URL after `vercel deploy`. Default: parse from CLI output. |

### 4. Wire env vars (per-environment)

Vercel scopes env vars to one of: `development`, `preview`, `production`. The CLI:

```bash
# Pull env for local dev (matches `development` scope)
vercel env pull .env.local

# Add a key to one or more environments
vercel env add API_KEY production         # prompts for value
vercel env add API_KEY preview            # different value for preview
vercel env add API_KEY development        # different value for dev
```

See `references/env-management.md` for the full env workflow including encrypted secrets, scope precedence, and parity with `.env.local`.

### 5. Custom domains

```bash
vercel domains add example.com
vercel alias https://my-project-abc123.vercel.app example.com
```

Or set in dashboard. Domain assignment to production deploys is automatic if configured.

See `references/domains-and-aliases.md`.

### 6. Wire monorepo root if needed

If the Next.js app lives under `apps/web` in a monorepo, set the project root in Vercel:

- Dashboard: Settings → General → Root Directory → `apps/web`
- Or via `vercel.json`:

```json
{
  "buildCommand": "cd apps/web && npm run build",
  "outputDirectory": "apps/web/.next"
}
```

See `references/monorepo.md` for Turborepo/Nx specifics.

### 7. Generate the deploy

```bash
make deploy            # → vercel --prod
make preview           # → vercel deploy
make verify            # → curl probe
```

End-to-end test against a real Vercel project before declaring done.

## Decision rules

- **Vercel auto-detects Next.js.** Don't override `framework`, `buildCommand`, or `installCommand` unless you have a specific reason. Defaults are correct ~99% of the time.
- **Use `vercel --prod` for production.** Bare `vercel deploy` creates a preview (unique URL, not aliased to your domain). Easy to confuse.
- **Pull env via `vercel env pull`, don't hand-type.** This file is `.env.local` by default — already gitignored by `vercel link`.
- **Don't commit `.vercel/`.** That's the per-contributor link state. Vercel adds it to `.gitignore` on new projects; verify it's there.
- **Refuse to deploy from a dirty tree by default.** Vercel will deploy whatever's in your working directory (not just committed code). Surface uncommitted changes as a yellow warning.
- **Refuse to deploy if the workload is wrong for Vercel.** If you detect BullMQ/SSE/WebSocket usage, surface the warning + route to make-railway. See `references/vercel-vs-railway.md`.

## Recovery paths

| Symptom | Cause | Fix |
|---|---|---|
| `vercel: command not found` | CLI not installed | `npm install -g vercel` |
| `Unauthorized` from `vercel whoami` | Not logged in | `vercel login` (browser-based) |
| `vercel link` says "no projects found" | Auth scope wrong | `vercel switch` to the right team/org |
| Build fails: "Cannot find module 'X'" | Dependency in `devDependencies`, Vercel skips by default | Move to `dependencies`, OR set `NPM_CONFIG_PRODUCTION=false` in env |
| Build fails: "Function exceeds 50MB" | Large dep in serverless function bundle | See `references/function-size-limits.md` — usually Sharp/ffmpeg/native crypto |
| Build SUCCESS but deployment URL returns 500 | Runtime error after build | Check Vercel dashboard → Functions → Logs |
| `next.config.ts` `output: "standalone"` set | Vercel doesn't support standalone | Remove `output: "standalone"` — Vercel handles its own bundling |
| Cron job timeout | Hobby tier cron has 10s limit | Upgrade plan, OR move cron to Railway |
| Custom domain returns 404 | DNS not propagated, or alias not assigned | `vercel alias <preview-url> <domain>`; wait 60s for DNS |
| Preview URL gates auth in prod-only logic | `process.env.VERCEL_ENV !== 'production'` not handled | Use `VERCEL_ENV` to differentiate prod/preview/dev in code |
| `Failed to find Server Action` after deploy | `output: "standalone"` set, or framework override breaking action chunking | Remove overrides; let Vercel handle Next.js |

## Customizing the recipe

- **Non-Next frameworks (Astro, Remix, SvelteKit, Vue, Nuxt):** Vercel auto-detects all of these. Same Makefile structure works.
- **Static-only sites (no functions):** Same Makefile; Vercel just doesn't generate functions.
- **API-only project (no UI):** Vercel works but Railway is usually better — APIs benefit from long-running processes for connection pools, etc.
- **Multiple environments:** Vercel handles `production`/`preview`/`development` natively. The Makefile only needs `make deploy` (prod) and `make preview` (per-commit URL).
- **Skipping preview deploys per PR:** Set `git.disableDeploymentsForBranch` in `vercel.json` for branches you don't want auto-built.

## Reference routing

| File | Read when |
|---|---|
| `references/makefile-template.md` | Generating the Make targets — full template with placeholders. |
| `references/find-or-create.md` | `vercel link`, `vercel projects ls`, naming conventions, when to create new vs reuse. |
| `references/env-management.md` | `vercel env pull/add/rm`, env scoping (dev/preview/prod), encrypted secrets, parity with `.env.local`. |
| `references/domains-and-aliases.md` | `vercel domains add`, `vercel alias`, DNS propagation, root vs www, redirect rules. |
| `references/monorepo.md` | Setting Root Directory, Turborepo `vercel.json`, per-app projects vs monorepo project. |
| `references/function-size-limits.md` | The 50MB compressed limit, common offenders, how to check, fixes. |
| `references/vercel-config.md` | `vercel.json` schema for the cases auto-detection misses (rewrites, redirects, headers). |
| `references/vercel-vs-railway.md` | Decision matrix; how to detect when a project's workloads make Vercel wrong. |
| `references/cross-skill-handoffs.md` | When to route to make-local (dev), make-railway (alt prod / workers). |

## Cross-skill handoffs

- For local dev with the same project — **make-local**.
- For workloads Vercel can't handle (workers, long SSE, large functions) — **make-railway**.
- For Railway CLI questions — **use-railway**.

## Guardrails

- Never override Vercel's framework auto-detection unless you have a specific failure to fix.
- Never set `output: "standalone"` in `next.config.*` for Vercel deploys — it's redundant and breaks Vercel's own bundling.
- Never commit secrets to `.env.development` / `.env.preview` / `.env.production` — those are committed files. Use `vercel env add` for the actual values.
- Never deploy a project with detectable BullMQ/long-running-SSE patterns to Vercel without explicitly warning the user. Show the make-railway decision pointer.
- Never `--force` deploy without confirming it overwrites the current production.

## Final checks

Before declaring done:

- [ ] `make deploy` completes end-to-end against a real Vercel project
- [ ] Pre-flight refuses cleanly when `vercel` CLI is missing/unauthenticated/unlinked
- [ ] Production URL responds 200 (or expected redirect)
- [ ] `.vercel/` is in `.gitignore`
- [ ] `vercel env pull .env.local` produces a working local env (not just empty file)
- [ ] If monorepo: Vercel project root is set correctly (Settings or `vercel.json`)
- [ ] No `output: "standalone"` in `next.config.*`
- [ ] If long-running workloads detected: a clear warning + handoff to make-railway documented in the Makefile help
