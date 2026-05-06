# Vercel env management

Vercel scopes env vars to one of three environments: `development`, `preview`, `production`. The CLI manages each.

## The three environments

| Env | When applied | Typical use |
|---|---|---|
| `development` | `vercel dev` (local) and `vercel env pull` | Local dev, mirrors `.env.local` |
| `preview` | All non-main branch deploys + per-PR previews | Staging-like; safe to break |
| `production` | Deploys to the assigned production branch (usually `main`) | Real users; treat as immutable |

A var can be set in 1, 2, or all 3 environments. They don't auto-cascade.

## Pulling env to local

```bash
# Pull the development scope to .env.local
vercel env pull .env.local

# Pull production scope (DANGEROUS — production secrets to local file)
vercel env pull .env.production --environment=production

# Pull preview
vercel env pull .env.preview --environment=preview
```

`.env.local` is in Vercel's default `.gitignore`. Verify after first pull:

```bash
git check-ignore .env.local && echo "✓ gitignored"
```

## Adding env vars

```bash
# Interactive prompt for value
vercel env add API_KEY production
# Enter value: sk-...

# All three environments
vercel env add API_KEY production preview development

# From stdin (scriptable)
echo "sk-..." | vercel env add API_KEY production
```

## Listing

```bash
# All envs, all scopes
vercel env ls

# Filter by environment
vercel env ls production
```

Output shows the key + which environments it's set in. Values are masked.

## Removing

```bash
vercel env rm API_KEY production
# Confirms before removal
```

## Encrypted vs plain

All Vercel env vars are encrypted at rest. The `--sensitive` flag (deprecated in favor of always-encrypted) ensured secrets don't appear in build logs. Modern Vercel always treats values as secrets.

## Build-time vs runtime

| Type | When read | Available in |
|---|---|---|
| Build-time | At `next build` | Server components, API routes (baked into bundle) |
| Runtime | At request handling | Server components, API routes, edge functions |

Next.js `process.env.X` is read at runtime by default. To inline at build (faster reads, but immutable post-deploy):

```ts
// next.config.ts
const nextConfig: NextConfig = {
  env: {
    NEXT_PUBLIC_API_BASE: process.env.API_BASE,  // baked in
  },
};
```

Anything prefixed `NEXT_PUBLIC_` is exposed to client bundles — careful with secrets.

## Vercel-managed env vars

Vercel injects these automatically at deploy:

| Var | Notes |
|---|---|
| `VERCEL` | `1` when running on Vercel |
| `VERCEL_ENV` | `production` / `preview` / `development` |
| `VERCEL_URL` | The deployment-specific URL (e.g., `my-app-abc123.vercel.app`) |
| `VERCEL_BRANCH_URL` | The branch URL (`my-app-git-feature.vercel.app`) |
| `VERCEL_GIT_COMMIT_SHA` | Short git SHA |
| `VERCEL_REGION` | The execution region |

Use `VERCEL_ENV !== 'production'` to differentiate prod from preview in code:

```ts
if (process.env.VERCEL_ENV === 'production') {
  Sentry.init({ dsn: process.env.SENTRY_DSN });
}
```

## Parity with `.env.local`

Pattern: `vercel env pull` after major env changes:

```makefile
env-pull:
	@vercel env pull .env.local --environment=development
	@printf "✓ .env.local updated\n"
```

Run on first checkout, after onboarding new env vars, after secret rotations. Don't run constantly — pulls overwrite the file.

## Secrets rotation

```bash
# 1. Rotate at the source (DB dashboard, OAuth provider)
# 2. Update Vercel
vercel env rm OLD_KEY production
vercel env add NEW_KEY production
# 3. Trigger redeploy (env changes don't auto-redeploy)
vercel --prod --force
```

## Don't commit `.env.production`

Vercel pulls write to local files. The convention:

```gitignore
.env.local
.env.production
.env.preview
.env.*.local
```

Yes to `.env` (committed defaults), no to anything pulled or local-overridden.

## Build-time env injection from Vercel

For values that need to be in the build bundle (e.g., Sentry source-map upload tokens):

1. Set in Vercel env (any environment)
2. Reference in `next.config.ts` or build script
3. They're available during `next build` because Vercel runs the build with all env vars injected

This works for Sentry's `withSentryConfig({ authToken: process.env.SENTRY_AUTH_TOKEN, ... })` — token is read at build, source maps uploaded automatically.

## Multi-tenant secrets

If different tenants need different env values (rare in single-Vercel-project setups), you'd need separate Vercel projects per tenant. Within one project, env is shared per-environment.
