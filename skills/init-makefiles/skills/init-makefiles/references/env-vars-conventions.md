# Env-var conventions — where they live, how they sync, what NOT to leak

This file is the canonical source for env-var handling across all seven scenarios. The agent generating a Makefile uses this to decide which `.env*` files to expect, which provider's CLI to call for `make env-pull`, and how to gate the user against leaking dev secrets to production. The single load-bearing rule: **each provider's runtime owns its own env**. Cross-pollination is the bug, not the feature.

All facts below verified May 2026 against `https://vercel.com/docs/cli/env`, `https://docs.railway.com/reference/variables`, `https://supabase.com/docs/guides/functions/secrets`.

## Per-scenario env-file table

| Scenario | Local dev source | Production source | Sync command in Makefile |
|---|---|---|---|
| **A** frontend | `.env.local` | Vercel env (production scope) | `make env-pull` runs `vercel env pull .env.local` |
| **B** MCP | `.env` | n/a (no deploy target) | none |
| **C** front+back | `.env.local` (frontend) + `.env.api` (api) | Vercel + Railway | `make env-pull` runs both `vercel env pull .env.local` and `railway variable list -s api --kv > .env.api` |
| **D** front+sb | `.env.local` (frontend) + `supabase/.env` (Edge Functions) | Vercel + Supabase secrets | `make env-pull` runs `vercel env pull .env.local` + `make supabase-secrets-list` (read-only inspection) |
| **E** multi-svc | `.env.<service>` per service (e.g. `.env.api`, `.env.worker`) | Railway per service | `make env-pull` runs `railway variable list -s <svc> --kv > .env.<svc>` for each service |
| **F** build | `.env` (if any build-time config needed) | n/a | none |
| **G** mac | `.env` (build-time only — Info.plist injection, signing config) | n/a (Mac apps don't have a "remote env") | none |

The agent generates `make env-pull` only for scenarios where at least one provider has env vars to pull (A, C, D, E). For B, F, G the target is omitted from the help banner.

## The 3 Vercel envs (plus custom)

Vercel env vars are scoped to a target environment:

| Scope | When applied | Typical use |
|---|---|---|
| `development` | `vercel dev`, `vercel env pull .env.local` | Local dev — mirrors `.env.local` |
| `preview` | All non-main branch deploys + per-PR previews | Staging-like, safe to break |
| `production` | Deploys to the production branch (usually `main`) | Real users, treat as immutable |
| `<custom>` | Custom envs created by the project (e.g., `staging`, `qa`) | When the 3 defaults don't fit |

A var can be set in 1, 2, 3, or all envs. They don't auto-cascade — adding to production does NOT add to preview.

CLI uses positional arguments to scope:

```bash
vercel env add API_KEY production              # only production
vercel env add API_KEY production preview      # both production and preview
vercel env add API_KEY                          # interactive — CLI prompts which envs
echo "sk-..." | vercel env add API_KEY production   # scriptable
```

Reference: `https://vercel.com/docs/cli/env` (2026-05-08).

## `vercel env pull` vs `vercel pull` — different files, common confusion

The single most common pre-2025 confusion. Two CLIs, two file paths, two purposes.

| Command | Writes to | Reads | Use case |
|---|---|---|---|
| `vercel env pull .env.local` | `.env.local` (project root) | development scope by default; `--environment=production` overrides | What the framework's dev server reads (`next dev`, `vite dev`) |
| `vercel pull` | `.vercel/.env.<target>.local` | the linked project + target | What `vercel build` and `vercel dev` use internally |

The Makefile uses **`vercel env pull .env.local`** — the file frameworks read directly. `vercel pull` writes a different path that the framework's dev server doesn't read by default.

Concrete generated target:

```makefile
env-pull: _check-vercel-tokens
	@printf "$(D)→ vercel env pull .env.local$(Z)\n"
	@vercel env pull .env.local --environment=development --token=$$VERCEL_TOKEN
	@printf "$(G)✓$(Z) .env.local refreshed\n"
```

To pull a different scope (rare — usually pull development for local dev):

```bash
vercel env pull .env.production --environment=production    # DANGEROUS — pulls real prod secrets to disk
vercel env pull .env.preview --environment=preview
```

The skill never generates a `make env-pull` that writes production-scope to disk. If a user needs production env locally, they pass `--environment=production` manually with intent.

## Vercel sensitive-by-default (post-2025)

As of 2025+, `vercel env add` to production / preview / custom envs defaults to **sensitive** (write-only). The value is encrypted at rest and is NOT visible in:

- the Vercel Dashboard (only the key name and "encrypted" label show)
- `vercel env ls` (key name + scope listed; value masked)
- build logs (the value never prints)

This is the right default for secrets. To override (rare — typically for non-secret values like a feature flag string):

```bash
vercel env add FEATURE_BANNER_TEXT production --no-sensitive
```

Implication for the Makefile:

- `vercel env pull .env.local` from production scope **will fail** for sensitive vars (they're write-only). The user must rotate via `vercel env rm` + `vercel env add`. This is by design.
- For the development scope, sensitivity is opt-in (default is non-sensitive) — so `vercel env pull .env.local --environment=development` works normally.
- The agent prints a one-line note in the post-generation banner: "Production secrets are sensitive-by-default; rotate via `vercel env rm` + `vercel env add`, never read."

Reference: `https://vercel.com/docs/cli/env` (2026-05-08).

## Never blanket-import `.env.local` to production

The temptation: `for KEY in $(grep -v '^#' .env.local | cut -d= -f1); do vercel env add "$KEY" production; done`. **Don't.** This leaks dev secrets (mock keys, local-only DB URLs, fake auth tokens) into production.

Safer pattern: per-key prompt, plus a committed `.env.production.template` (keys-only, no values) so the user can see what's expected without reading any actual secrets.

`.env.production.template` example (committed):

```
# Production env keys. Values live in Vercel (never here).
# Set via: vercel env add <KEY> production
DATABASE_URL=
STRIPE_SECRET_KEY=
RESEND_API_KEY=
NEXT_PUBLIC_API_BASE=
```

The Makefile does NOT generate a "blanket-push" target. For CI-driven secret management (the right way), see `ci-cd-workflow.md` — secrets live in GitHub Actions and are pushed to providers via `gh secret set` flows.

## Railway built-in service variables

Railway sets these automatically on every service deploy. **DO NOT shadow them** in app env. `railway variable list -s <svc>` shows them under "Railway-Managed Variables".

| Var | Notes |
|---|---|
| `RAILWAY_PUBLIC_DOMAIN` | `<service>.up.railway.app` or the user's custom domain |
| `RAILWAY_PRIVATE_DOMAIN` | `<service>.railway.internal` — only resolves inside Railway's private network |
| `RAILWAY_TCP_PROXY_DOMAIN` | TCP proxy hostname (when TCP proxying enabled) |
| `RAILWAY_TCP_PROXY_PORT` | TCP proxy port |
| `RAILWAY_PROJECT_ID` | UUID |
| `RAILWAY_PROJECT_NAME` | The project's slug |
| `RAILWAY_SERVICE_ID` | UUID |
| `RAILWAY_SERVICE_NAME` | The service's name (e.g., `api`, `worker`) |
| `RAILWAY_ENVIRONMENT_ID` | UUID |
| `RAILWAY_ENVIRONMENT_NAME` | `production`, `staging`, etc. |
| `RAILWAY_DEPLOYMENT_ID` | This deployment's UUID |
| `RAILWAY_REPLICA_ID` | UUID (when service has multiple replicas) |
| `RAILWAY_REPLICA_REGION` | Region of this replica |
| `RAILWAY_GIT_COMMIT_SHA` | Commit SHA — set when GitHub deploy |
| `RAILWAY_GIT_BRANCH` | Branch — set when GitHub deploy |
| `PORT` | The port the service must bind on. Bind `0.0.0.0:$PORT`, never `localhost:3000` |

Reference variables (resolved at deploy time, embedded into runtime env):

| Pattern | Example |
|---|---|
| Cross-service | `${{ api.RAILWAY_PUBLIC_DOMAIN }}` → `api.up.railway.app` |
| Shared (project-scoped) | `${{ shared.STRIPE_KEY }}` |
| Database addon | `${{ Postgres.DATABASE_URL }}` |
| Built-in (this service) | `${{ RAILWAY_PUBLIC_DOMAIN }}` |

Reference: `https://docs.railway.com/reference/variables` (2026-05-08).

## Railway `.env.<service>` per-service convention

Multi-service repos (Scenario E) maintain one local `.env` per service:

```
.env.api
.env.worker
.env.cron
```

Each is gitignored. Pull from Railway:

```makefile
env-pull:
	@for svc in api worker cron; do \
	  railway variable list -s $$svc --kv > .env.$$svc; \
	  printf "$(G)✓$(Z) .env.$$svc refreshed from $$svc\n"; \
	done
```

The single-service Scenario C variant uses `.env.api` (or `.env.<RAILWAY_SERVICE>`). Frontend in the same repo gets `.env.local` (Vercel-side). The two never overlap — the frontend reads `NEXT_PUBLIC_API_BASE` from `.env.local`, the backend reads its `DATABASE_URL` etc. from `.env.api`.

## Supabase per-project secret scoping

Supabase secrets are **per-project**, NOT per-environment in any sub-project sense. There is no "dev / preview / prod" inside a single Supabase project — pushed secrets apply to that project's runtime, full stop.

For preview / staging / production separation, use one of two patterns:

1. **Two separate Supabase projects** — one for prod, one for staging/preview. Each has its own ref and secrets. The Makefile's `SUPABASE_PROJECT_REF` is the linked project.
2. **Supabase Branching** — preview deploys auto-create a branch with its own instance and own secrets, lifecycle-managed by the Vercel-Supabase integration (May 2026 default). The Makefile only operates on the linked production project; branches are out of Make's scope.

`supabase/.env` (the local file `make supabase-secrets-push` reads) corresponds to *one* linked project. Switching projects = re-running `supabase link --project-ref <new-ref>` + maintaining a separate `.env`. Don't try to multiplex secrets across projects from one file.

Reference: `https://supabase.com/docs/guides/functions/secrets` (2026-05-08).

## `.gitignore` rules

The skill **never** edits `.gitignore` directly — that's destructive (might collide with the user's existing rules). Instead, the agent prints the recommended block once at generation time, and the user appends:

```gitignore
# init-makefiles recommends:
.env.local
.env.production
.env.preview
.env.*.local
.env.api
.env.worker
.env.cron
.env.<service>
supabase/.env
.vercel/
.railway/
```

Notes:

- `.env` itself is sometimes committed (Scenario B / F where `.env` holds non-secret defaults). The user decides per project.
- `.vercel/project.json` is NOT secret — it's a project ID + org ID. Some teams commit it for deterministic CI; others let `vercel link --yes --project <name>` re-create it. Either is fine.
- `.railway/` IS sensitive in git-worktree setups (it's per-checkout state). Always gitignore it.
- `supabase/config.toml` IS committed — it's the project structure config, not secrets.
- `supabase/migrations/*.sql` ARE committed — schema history.
- `supabase/functions/*/index.ts` ARE committed — function source.
- `supabase/.env` is NEVER committed.

The agent's one-line print at generation:

```
→ .gitignore recommendation printed above. Append the block manually if missing.
```

## Where to keep secrets at rest

Three layers, by purpose:

1. **Master copy** — 1Password, Bitwarden, or the team's vault. The single source of truth. Start here for rotation or recovery.
2. **Provider-native runtime store** — Vercel sensitive vars, Railway sealed vars, Supabase secrets. Each provider holds the values it needs at runtime. The Makefile pulls FROM these, never TO them in the secret-leaking direction.
3. **GitHub Actions secrets** — for CI/CD push-to-main flows. Set via `gh secret set <NAME> --body "$pasted"`. Workflow steps read via `${{ secrets.NAME }}`.

The flow when adding a new secret:

1. Generate / rotate the secret at its source (DB dashboard, OAuth provider, payment vendor).
2. Paste into 1Password (master).
3. Set in the provider's runtime store: `vercel env add NEW_KEY production` / `railway variables --service api --set "NEW_KEY=..."` / `supabase secrets set NEW_KEY=...`.
4. If CI/CD wires this provider: `gh secret set NEW_KEY --body "$value"`.
5. Trigger a redeploy (env changes don't auto-redeploy in most flows).

The Makefile's `env-pull` is **read-only** in this flow. It pulls runtime values into a local `.env*` file for dev parity. It never writes back.

For the CI/CD wiring details, see `ci-cd-workflow.md`.

## Cross-provider boundaries (the load-bearing rule)

| Provider | Owns env for | Never reads from |
|---|---|---|
| Vercel | The frontend at runtime — Edge / Node functions on Vercel | Railway env, Supabase env |
| Railway | Each backend service at runtime | Vercel env, Supabase env |
| Supabase | Edge Functions at runtime + the database itself | Vercel env, Railway env |
| GitHub Actions | The CI runner during deploy | n/a — it's a one-shot env per workflow run |

The frontend on Vercel can call the backend on Railway over HTTPS — but the backend's `DATABASE_URL` lives in Railway env, not Vercel env. The frontend never needs (and must never see) `DATABASE_URL`. Adding `DATABASE_URL` to Vercel env means either (a) DB queries run in a Vercel function, so the URL belongs in Vercel, not Railway, or (b) the URL is leaking. Pick one intentionally.

## DO-NOT list

- DO NOT commit `.env.local`, `.env.<service>`, `supabase/.env`, or any `.env*.local`. Always gitignore.
- DO NOT echo tokens or secrets in Make recipes — even via `printf "$(D)token: $$X$(Z)"`. Recipe stdout is logged in CI; tokens leak to the workflow log forever.
- DO NOT blanket-import `.env.local` into Vercel production via a loop over every key. Per-key, with intent. Or use `.env.production.template` + `gh secret set` flows.
- DO NOT use `vercel pull` to write `.env.local` — wrong file path. The right command is `vercel env pull .env.local`.
- DO NOT cross-pollute envs between providers. Vercel's env is the frontend's; Railway's is the backend's; Supabase's is the Edge Functions' / DB's. Each provider's runtime owns its own env.
- DO NOT shadow Railway built-in variables (`RAILWAY_*`, `PORT`). Setting a custom `PORT` will be silently overridden.
- DO NOT leak `service_role` to the frontend (Supabase). `NEXT_PUBLIC_*` is public; service_role bypasses RLS — full DB access. Server / Edge Functions only.
- DO NOT auto-rotate secrets from the Makefile. Rotation is user-initiated; the Makefile only refreshes local copies via `env-pull`.
- DO NOT generate `make env-pull` for Scenarios B / F / G — they have no provider env to pull.
- DO NOT edit `.gitignore` from a Make recipe. Print the recommended block; let the user append.
- DO NOT set `RAILWAY_API_TOKEN` in any env file (account-scoped, too broad). Always `RAILWAY_TOKEN` (project-scoped). See `makefile-backend.md`.
- DO NOT pull production-scope Vercel envs into a local file casually. `vercel env pull .env.local` defaults to development scope for a reason.

## What this file does NOT cover

| Topic | Reference |
|---|---|
| Universal Makefile preamble + `make help` | `makefile-base.md` |
| Vercel deploy targets, function size limits | `makefile-frontend.md` (sister file) |
| Railway deploy targets, `railway.toml` baseline, multi-service rules | `makefile-backend.md` |
| Supabase target inventory, `--linked` operations | `makefile-supabase.md` |
| GitHub Actions workflow templates, `gh secret set` flow | `ci-cd-workflow.md` |
| Verification rungs (which command claims which rung) | `verification-ladder.md` |

## Citations (verified 2026-05-08)

- `https://vercel.com/docs/cli/env` — Vercel env CLI, sensitive-by-default rule
- `https://vercel.com/docs/projects/environment-variables` — env scoping (development / preview / production / custom)
- `https://docs.railway.com/reference/variables` — Railway built-in service variables, reference variable syntax
- `https://docs.railway.com/cli/variable` — `railway variable list / set / unset` CLI
- `https://supabase.com/docs/guides/functions/secrets` — Supabase Edge Function secrets, per-project scope
- `https://supabase.com/blog/branching-without-git-is-now-the-default` — May 2026 branching model
