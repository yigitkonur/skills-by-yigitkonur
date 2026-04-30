# Vercel monorepo deploys

Vercel supports monorepos via the **Root Directory** setting. The Vercel project lives at a subdirectory of the repo.

## Setup

Dashboard → Project Settings → General → Root Directory → `apps/web`

Vercel then:
- Runs `npm install` from the monorepo root
- Builds in `apps/web/` (output: `apps/web/.next`)
- Serves the result

Alternative: set in `vercel.json` at the **monorepo root**:

```json
{
  "buildCommand": "cd apps/web && npm run build",
  "outputDirectory": "apps/web/.next",
  "installCommand": "npm install",
  "framework": "nextjs"
}
```

The dashboard setting is preferred — it's clearer and lets each project pick a different root.

## One project per app

The cleanest pattern for monorepos:

```
my-monorepo/
├── apps/
│   ├── web/        ← Vercel project A (root: apps/web)
│   ├── admin/      ← Vercel project B (root: apps/admin)
│   └── docs/       ← Vercel project C (root: apps/docs)
└── packages/
    └── shared/     ← shared workspace, built per-app
```

Each app gets its own Vercel project, deploy URL, env, custom domain. Shared code lives in workspace packages.

## Turborepo integration

Vercel auto-detects Turborepo. Cache hits from Turbo's remote cache speed up builds dramatically:

```bash
# In CI / Vercel build env:
export TURBO_TOKEN=...        # from https://vercel.com/account/tokens
export TURBO_TEAM=acme        # your team slug
```

In `turbo.json`:

```json
{
  "remoteCache": { "signature": true }
}
```

Vercel's build picks this up automatically — no extra config in dashboard.

## Per-PR preview deploys

Vercel auto-creates preview deploys per branch + per PR. For monorepos, this triggers builds **for every project linked to the repo**, even if the changed files only affect one app.

Limit to changed apps via `vercel.json`:

```json
{
  "git": {
    "deploymentEnabled": {
      "main": true,
      "develop": false
    }
  }
}
```

Or use Turborepo's "ignore step" — Vercel runs your `ignoreCommand` and skips the deploy if it returns 0:

```json
{
  "ignoreCommand": "npx turbo-ignore"
}
```

`turbo-ignore` checks if the current app's source changed since the last successful build. If not, returns 0 → Vercel skips the deploy. Saves preview minutes.

## Workspaces (npm/yarn/pnpm)

Vercel's `npm install` runs from the monorepo root, respecting workspaces. Nothing special to configure.

For pnpm:

```json
// package.json at monorepo root
{
  "packageManager": "pnpm@9.0.0"
}
```

Vercel auto-detects from `packageManager` field. Or add `corepack enable` to install command if needed.

## Build cache scope

Vercel caches per-project. Two projects from the same monorepo don't share cache — even if they install the same node_modules.

Turborepo's remote cache *does* share — that's the whole point. Use it.

## Env vars per app

Each Vercel project has its own env. If `apps/web` and `apps/admin` need the same `DATABASE_URL`:

```bash
# Set on web
vercel env add DATABASE_URL production --project apps-web

# Set on admin separately
vercel env add DATABASE_URL production --project apps-admin
```

Or use a shared .env in the workspace root and load via dotenv (less common in Vercel-deployed projects).

## Next.js specific

`apps/web/next.config.ts` works as expected. The `transpilePackages` field is useful for shared packages:

```ts
const nextConfig: NextConfig = {
  transpilePackages: ['@acme/shared-ui'],
};
```

Without it, `next build` will fail to compile workspace packages that ship TS source.

## Common monorepo deploy failures

| Symptom | Fix |
|---|---|
| `Module not found: Can't resolve '@acme/shared'` | Add `transpilePackages: ['@acme/shared']` to `next.config.ts` |
| `npm ERR! ENOENT package.json` (when Vercel runs install at app dir) | Make sure Root Directory is set; install runs from monorepo root, not app dir |
| Cache misses on every deploy | Verify Turborepo remote cache: `TURBO_TOKEN` + `TURBO_TEAM` set in Vercel env |
| Preview deploys for every commit, even unrelated changes | Add `ignoreCommand: "npx turbo-ignore"` to `vercel.json` |
| Build succeeds but routes 404 | `outputDirectory` mismatch — check it's `apps/web/.next` (not `.next`) |

## Don't use a single Vercel project for multiple apps

Vercel projects map 1:1 to deployment URLs. You can't have `acme.com` and `admin.acme.com` from the same project — that's two projects.

Some teams work around this with subpath routing (`acme.com/admin/...`) and a single Next.js app that handles both. Cleaner for small projects; doesn't scale.
