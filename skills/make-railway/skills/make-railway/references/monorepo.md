# Monorepo deploys

Railway builds whatever's at the project root by default. For monorepos with multiple apps, you need either:

1. One Railway project per app (recommended)
2. One Railway project with per-service root directory overrides

## Option 1: project-per-app (cleaner)

Each app gets its own Railway project, linked to a subdirectory:

```
my-monorepo/
├── apps/
│   ├── web/        ← Railway project A, linked here
│   ├── api/        ← Railway project B, linked here
│   └── admin/      ← Railway project C, linked here
└── packages/
```

Setup per app:

```bash
cd apps/web
railway init   # or railway link to existing
make prod
```

Each subdirectory has its own `railway.json` / `Dockerfile` / `Makefile`.

**Pros:** Clean separation, simpler env management per app.
**Cons:** Cross-app refs (web → api URL) need manual env wiring.

## Option 2: single project, per-service root override

One Railway project, each service has a custom root directory:

```
my-monorepo/
├── apps/
│   ├── web/
│   ├── api/
│   └── admin/
└── packages/
```

In Railway dashboard → Service `web` → Settings → Root Directory: `apps/web`. Same for `api` (`apps/api`), `admin` (`apps/admin`).

Each service still builds with the project-root-relative `Dockerfile` (or per-app Dockerfile under `apps/web/Dockerfile`).

**Pros:** Single project, shared envs at the service group level.
**Cons:** Complex; can't easily test per-app deploys.

## The Makefile pattern

For option 1 (recommended), put the Makefile in each app's directory:

```
apps/web/Makefile     # WEB_SERVICES := web
apps/api/Makefile     # WEB_SERVICES := api
apps/admin/Makefile   # WEB_SERVICES := admin
```

Each `make prod` operates on its own subdir. Run from the right directory.

For an umbrella `make prod-all` at repo root:

```makefile
# my-monorepo/Makefile
APPS := web api admin

prod-all:
	@for app in $(APPS); do \
	  printf "→ deploying $$app\n"; \
	  $(MAKE) -C apps/$$app prod & \
	done; \
	wait
```

## Shared dependencies

If apps share a `packages/shared` workspace, the Dockerfile must:

1. Copy the entire monorepo (not just the app subdir)
2. Run `npm install` from the monorepo root (resolves workspaces)
3. Build the specific app

```Dockerfile
FROM node:24-alpine
WORKDIR /app

# Copy whole monorepo (npm workspaces need full context)
COPY package.json package-lock.json ./
COPY packages ./packages
COPY apps ./apps

RUN npm ci --workspaces --include-workspace-root

# Build the specific app
WORKDIR /app/apps/web
RUN npm run build

CMD ["npm", "start"]
```

For Turborepo / Nx, lean on their cached-build features:

```Dockerfile
RUN npx turbo build --filter=web
```

## Nixpacks + monorepo

Nixpacks struggles with monorepos. Auto-detection picks the wrong app, env scoping is unclear. **Always use Dockerfile for monorepos.**

## Per-app env

Each Railway service has its own env. With option 1 (project-per-app), envs are isolated by default. With option 2, services share the env namespace within the project — careful naming required:

```
WEB_DATABASE_URL = ...
API_DATABASE_URL = ...
ADMIN_DATABASE_URL = ...
```

Or use Railway env-var references to a shared `Postgres` service:

```
DATABASE_URL = ${{Postgres.DATABASE_URL}}    # all three apps share
```

## Deploy order

When apps depend on each other (e.g., `web` calls `api`), deploy in dependency order:

```makefile
prod-all:
	@$(MAKE) -C apps/api prod
	@$(MAKE) -C apps/admin prod
	@$(MAKE) -C apps/web prod
```

Sequential, not parallel — `web` shouldn't deploy until `api` is up.

## Worktree consideration

If contributors use git worktrees, each worktree is a separate filesystem path. Each needs its own `railway link`. The `.railway/` directory is in `.gitignore` for this reason — never commit it.
