# Monorepo Makefile pattern

Monorepos get a root Makefile plus up to three per-app sub-Makefiles — **maximum four total**. The root delegates via `$(MAKE) -C apps/<name> <target>`; each per-app Makefile is fully standalone (so `cd apps/web && make local` works without going through the root). When the monorepo has more than three deployable apps, the agent asks the user to pick the three that get scaffolds.

## Detection

Signals that mark a project as a monorepo:

- `turbo.json` at repo root → Turborepo
- `pnpm-workspace.yaml` at repo root → pnpm workspaces
- `package.json` with `"workspaces": [...]` → Yarn / npm workspaces
- `apps/` directory with two or more sub-projects each carrying their own `package.json`
- `packages/` directory with shared internal libraries (signal of a workspace, but doesn't itself trigger sub-Makefiles)

Detection commands:

```bash
ls turbo.json pnpm-workspace.yaml 2>/dev/null
jq -r '.workspaces' package.json 2>/dev/null
find apps -maxdepth 2 -name package.json 2>/dev/null
find packages -maxdepth 2 -name package.json 2>/dev/null
```

**Threshold for splitting into sub-Makefiles:** any project with **two or more deployable apps** gets a per-app Makefile. A repo with one deployable frontend in `apps/web` and shared libs in `packages/*` is single-Makefile (the root). A repo with `apps/web` (frontend) and `apps/api` (backend) is two-Makefile (root + 2 per-app). A repo with `apps/web`, `apps/admin`, `apps/api` is four-Makefile (root + 3 per-app, the ceiling).

"Deployable" means a target deploys somewhere — Vercel, Railway, etc. Internal libs in `packages/` are not deployable; they're consumed by the apps.

## The 4-Makefile ceiling

Rule: **at most 4 Makefiles per project tree.** Root + up to 3 per-app. Anything beyond is forbidden. Why:

- Five Makefiles is unmaintainable. The user has to know which one to run from where, the root Makefile becomes a wall of `apps/<x> apps/<y> ...` targets, and `make help` becomes useless.
- Three apps is a natural ceiling — most monorepos have a frontend, a backend, and at most one worker / admin / docs site. Beyond that, the structure is usually wrong (split the repo, or move some apps to packages/internal libs).
- A clean 4-file ceiling beats an ambitious-but-incoherent 7.

## The "pick three" rule (more than 3 deployable apps)

When the monorepo has more than three deployable apps, the agent asks the user to pick three. Sample prompt the agent uses:

```
This monorepo has N deployable apps:
  - apps/web       (Next.js, deploys to Vercel)
  - apps/admin     (Next.js, deploys to Vercel)
  - apps/api       (Express, deploys to Railway)
  - apps/worker    (Node, deploys to Railway)
  - apps/docs      (Astro, deploys to Vercel)

I can scaffold Makefiles for at most three. Which three should get sub-Makefiles?
Pick by daily-dev frequency, not alphabetical. The remaining apps will be
documented in AGENTS.md as "no Make scaffold" — deploy via the provider CLI directly.
```

If the user picks fewer than three, that's fine — three is the ceiling, not a quota. The remaining apps get a brief "no Make scaffold for this app" note in `AGENTS.md` (handed off to `agents-md-update.md`):

```markdown
### Apps without Make scaffolds

These apps don't have a per-app `Makefile`; deploy them via the provider CLI:

- `apps/docs` — Astro, deploys to Vercel: `cd apps/docs && vercel deploy --prod --yes --token=$VERCEL_TOKEN`
- `apps/worker` — Node worker on Railway: `cd apps/worker && railway up --ci -s worker`
```

## Root Makefile pattern

The root Makefile delegates everything via `$(MAKE) -C apps/<name> <target>`. It owns the `help` banner and a few aggregate targets (e.g. `make deploy` runs Vercel + Railway in sequence).

```makefile
SHELL       := bash
.SHELLFLAGS := -eu -o pipefail -c
.ONESHELL:
.DELETE_ON_ERROR:
MAKEFLAGS   += --warn-undefined-variables --no-builtin-rules
.DEFAULT_GOAL := help

# ── ANSI palette ──────────────────────────────────────────────
B := \033[1m
D := \033[2m
G := \033[32m
Y := \033[33m
R := \033[31m
C := \033[36m
Z := \033[0m

.PHONY: help local local-web local-api \
        deploy deploy-web deploy-api \
        verify clean

help:
	@printf "$(B)$(notdir $(CURDIR))$(Z)  $(D)— monorepo Make targets$(Z)\n\n"
	@printf "  $(B)$(G)make local-web$(Z)        dev server in apps/web (Next.js, :3456)\n"
	@printf "  $(B)$(G)make local-api$(Z)        dev server in apps/api (Express, :4000)\n"
	@printf "  $(B)$(C)make deploy$(Z)           deploy web (Vercel) + api (Railway)\n"
	@printf "  $(B)$(C)make deploy-web$(Z)       deploy apps/web only\n"
	@printf "  $(B)$(C)make deploy-api$(Z)       deploy apps/api only\n"
	@printf "  $(B)$(C)make verify$(Z)           HTTP-probe both prod URLs\n"
	@printf "  $(B)$(C)make clean$(Z)            stop dev servers + wipe per-app caches\n"
	@printf "\n$(D)Per-app:  cd apps/web && make help  ·  cd apps/api && make help$(Z)\n"

# ── local: default to the frontend ────────────────────────────
local: local-web

local-web:
	@$(MAKE) -C apps/web local

local-api:
	@$(MAKE) -C apps/api local

# ── deploy ────────────────────────────────────────────────────
deploy: deploy-web deploy-api
	@printf "$(B)$(G)deployed web + api$(Z)\n"

deploy-web:
	@$(MAKE) -C apps/web deploy-vercel

deploy-api:
	@$(MAKE) -C apps/api deploy-railway

# ── verify (aggregate) ────────────────────────────────────────
verify:
	@$(MAKE) -C apps/web verify
	@$(MAKE) -C apps/api verify

# ── clean (aggregate) ─────────────────────────────────────────
clean:
	@$(MAKE) -C apps/web clean
	@$(MAKE) -C apps/api clean
```

Notes:
- `local: local-web` defaults to the frontend. The user types `make local` and gets the daily-driver path. For backend-first projects (Scenario E), invert the default.
- Each delegated target uses `$(MAKE) -C apps/<name> <target>`, never `cd apps/<name> && make <target>`. The `-C` form correctly handles failure (no half-state if the recipe errors), works under `-j` parallelism, and is what GNU Make recommends for sub-makes.
- The root Makefile NEVER duplicates per-app target bodies. It delegates only.
- The root's `help` banner mentions the per-app `make help` so users know they can recurse.

## Per-app Makefile structure

Each per-app Makefile is fully standalone — same universal preamble, scenario-appropriate targets only. So `cd apps/web && make local` works without going through the root. Users discover this from the root's help banner.

Each per-app Makefile has its own `PROJECT_NAME`, `PORT`, and `TUNNEL_PORT` (so multiple apps can run dev simultaneously without port collisions):

```makefile
# apps/web/Makefile (Scenario A — frontend-only)
SHELL       := bash
.SHELLFLAGS := -eu -o pipefail -c
.ONESHELL:
.DELETE_ON_ERROR:
MAKEFLAGS   += --warn-undefined-variables --no-builtin-rules
.DEFAULT_GOAL := help

PROJECT_NAME ?= web
PORT         ?= 3456
TUNNEL_PORT  ?= 3457
DEV_CMD      ?= npm run dev
VERCEL_PROJECT ?= acme-web

# (ANSI palette + targets per references/makefile-frontend.md)
```

```makefile
# apps/api/Makefile (Scenario E single-service backend)
SHELL       := bash
.SHELLFLAGS := -eu -o pipefail -c
.ONESHELL:
.DELETE_ON_ERROR:
MAKEFLAGS   += --warn-undefined-variables --no-builtin-rules
.DEFAULT_GOAL := help

PROJECT_NAME    ?= api
PORT            ?= 4000
RAILWAY_SERVICE ?= api

# (ANSI palette + targets per references/makefile-backend.md)
```

Per-app namespacing rules:
- Distinct `PROJECT_NAME` per app (`web`, `api`, `admin`) — used for portless URLs (`web.localhost`, `api.localhost`) so cookies and IndexedDB don't collide.
- Distinct `PORT` per app — recommended dev defaults: `3456` (web), `4321` (admin / second frontend), `4000-4999` (backend), `5174` (Vite-flavored frontend). See `port-hygiene.md` for the squat-list and recommended ports.
- Distinct `TUNNEL_PORT` per app — pick adjacent to `PORT` (e.g. `3457` for `web`, `4001` for `api`) so both can run a tunnel simultaneously.

## Cookie / storage isolation

Loopback URLs share an origin (`localhost:<port>`) per port number, but two apps on the same loopback host with different ports STILL share `localhost`-scoped cookies in some browsers. The portless / Tailscale-tunnel pattern fixes this by giving each app a distinct hostname:

- `web.localhost`, `admin.localhost`, `api.localhost` — distinct origins, distinct cookie jars
- `<short>.<tailnet>.ts.net` per app via `tailscale set --hostname=` — distinct origins on the tailnet

**Loopback isolation rule.** Multiple projects on `localhost` share cookies and IndexedDB, leaking auth state across projects. The fix is a per-project named URL backed by a real cert (portless `<name>.localhost` or Tailscale Serve `<host>.<tailnet>.ts.net`). Per-app `PROJECT_NAME` is what makes that work in monorepos — same machine, distinct origins, distinct storage jars.

## Turborepo special case

Turborepo is auto-detected by Vercel. Verified 2026-05-08 against `https://vercel.com/docs/monorepos/turborepo`:

- Build command auto-detected as `turbo run build`
- Ignored Build Step set to `npx turbo-ignore` (skip rebuild for unchanged apps)
- Remote caching enabled out-of-the-box (no env-var setup required for the team's first project)
- `turbo.json` is the single source of truth for the build pipeline

Don't override unless the user has set up a custom Turborepo build pipeline. The Makefile's `deploy-web` runs `vercel deploy --prod --yes --token=...`; Vercel runs Turborepo on its end. The user's local `turbo.json` is consumed by Vercel's CI; the Makefile doesn't touch it.

If the user has a non-Turborepo monorepo (Nx, Lerna, plain workspaces), the Makefile pattern is identical — only the build command differs, and that's hidden inside the per-app Makefile's `DEV_CMD` and the framework's `package.json#scripts.build`.

## Vercel: one project per app dir

Recommended pattern (verified May 2026 against `https://vercel.com/docs/monorepos`):

- `apps/web` → one Vercel project (e.g. `acme-web`), Root Directory = `apps/web`
- `apps/admin` → second Vercel project (e.g. `acme-admin`), Root Directory = `apps/admin`

Each app's per-app Makefile sets `VERCEL_PROJECT` to its own project name. The `vercel link --yes --project=$(VERCEL_PROJECT)` line in `deploy-vercel` finds the right project from inside `apps/web/`, writing `apps/web/.vercel/project.json`. No collision between apps.

Root Directory is **dashboard-only** — there is no `vercel.json` field, no CLI flag for it. The skill prints this once during scaffold:

```
Set Root Directory in Vercel dashboard for each app project:
  https://vercel.com/<team>/acme-web/settings   → Build → Root Directory = apps/web
  https://vercel.com/<team>/acme-admin/settings → Build → Root Directory = apps/admin
```

The Make target won't fight this — `vercel link --yes --project <name>` finds the project and Vercel respects the dashboard setting at deploy time. See `makefile-frontend.md` for the deeper rationale.

## Anti-patterns

- **Single Makefile owning all apps' targets.** Past 8 targets per app × 3 apps = 24 targets, the help banner is unreadable and the file is unmaintainable. Always split into root + per-app.
- **`cd apps/<name> && make <target>` instead of `$(MAKE) -C apps/<name> <target>`.** The `cd && make` form: (a) doesn't propagate the `MAKEFLAGS` correctly under `-j`, (b) can leave the shell in the wrong dir if the recipe fails, (c) loses the parent's `make`-level error reporting. Always use `$(MAKE) -C`.
- **Hardcoded paths in sub-Makefiles.** Use relative paths (`.`) or `$(CURDIR)`. Never hardcode `/Users/example/dev/repo/apps/web` — the Makefile must work for any clone.
- **Per-app Makefiles that `include` the root preamble.** Tempting (DRY) but breaks the "each Makefile must be standalone" rule. Users running `cd apps/web && make local` would have to chase up to the parent. Each per-app Makefile carries its own preamble verbatim. The minor duplication is the price of standalone-ness.
- **Root Makefile with per-app target bodies.** The root delegates only. If `vercel deploy --prod` appears in the root Makefile, that work belongs in `apps/web/Makefile`.
- **More than 4 Makefiles.** Hard ceiling. Use the "pick three" prompt above when there are more than three deployable apps.
- **Different preamble per Makefile.** All four Makefiles use the same universal preamble (SHELL, ANSI palette, `.ONESHELL`, etc.) from `makefile-base.md`. Inconsistency confuses agents reading the project.

## Cross-references

- `makefile-base.md` — universal preamble used by every Makefile in the tree (root + per-app)
- `makefile-frontend.md` — Scenarios A/C/D body, used inside per-app frontend Makefiles
- `makefile-backend.md` — Scenarios C/E body, used inside per-app backend Makefiles
- `port-hygiene.md` — recommended dev ports (`3456`, `4321`, `5174`), squat-list, per-app namespacing
- `agents-md-update.md` — how to document apps without Make scaffolds in `AGENTS.md`
- `tailscale-funnel-rules.md` — per-app `TUNNEL_PORT` and tunnel isolation between apps
