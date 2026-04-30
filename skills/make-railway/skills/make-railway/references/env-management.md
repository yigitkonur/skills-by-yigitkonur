# Env var management

Railway env vars are per-service. The Makefile manages workflow; the CLI manages values.

## Reading

```bash
# Pretty (with sections)
railway variables --service WEB

# Key=value (parse-friendly)
railway variables --service WEB --kv

# Specific key
railway variables --service WEB --kv | grep "^DATABASE_URL=" | cut -d= -f2-
```

## Writing

Single key:

```bash
railway variables --service WEB --set "FEATURE_FLAG=true"
```

Multiple keys at once:

```bash
railway variables --service WEB \
  --set "FOO=bar" \
  --set "BAZ=qux"
```

From a file (one `KEY=VALUE` per line):

```bash
railway variables --service WEB --set-from-env-file .env.production
```

## Deleting

```bash
railway variables --service WEB --remove FEATURE_FLAG
```

## Pulling for local dev

The most common workflow: pull production env into `.env.local` so dev mirrors prod:

```bash
railway variables --service web-noauth --kv > .env.local
```

⚠️ Caution: this pulls **production secrets** into a local file. The file MUST be gitignored. Verify:

```bash
git check-ignore .env.local && echo "✓ gitignored" || echo "✗ NOT gitignored"
```

Pattern: pull only the keys you need:

```bash
# Pull just DATABASE_URL + REDIS_URL for local-against-prod debugging
railway variables --service postgres --kv | grep "DATABASE_PUBLIC_URL"
railway variables --service redis    --kv | grep "REDIS_PUBLIC_URL"
```

## Inter-service refs (Railway env templating)

Railway's env-var dashboard supports `${{ServiceName.VAR}}` references that resolve per-environment:

```
DATABASE_URL = ${{Postgres.DATABASE_URL}}
REDIS_URL    = ${{Redis.REDIS_URL}}
```

These resolve to the Railway-internal URLs (`postgres.railway.internal:5432`), which only work from inside Railway's private network.

For local dev, use the public URLs (different env values):

```
DATABASE_PUBLIC_URL = postgresql://...@shortline.proxy.rlwy.net:NNNNN/railway
REDIS_PUBLIC_URL    = redis://...@interchange.proxy.rlwy.net:NNNNN
```

The CLI reads both:

```bash
# Internal (only works inside Railway)
railway variables --service postgres --kv | grep "^DATABASE_URL="

# Public (works anywhere on the internet)
railway variables --service postgres --kv | grep "^DATABASE_PUBLIC_URL="
```

## The "missing env" diagnostic

Most Railway production failures are missing env vars. Pre-flight check before deploy:

```bash
# Required keys; fail if any missing
REQUIRED="DATABASE_URL REDIS_URL CLERK_SECRET_KEY NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY"
for svc in $WEB_SERVICES; do
  for key in $REQUIRED; do
    val=$(railway variables --service $svc --kv | grep "^$key=" | cut -d= -f2-)
    if [ -z "$val" ]; then
      echo "✗ $svc missing $key"
    fi
  done
done
```

This is the fastest way to catch the "deploy SUCCESS but app crashes at startup" class of bug.

## Secret rotation

When a secret leaks (DB password in a transcript, OAuth token committed):

```bash
# 1. Rotate at the source (DB dashboard, OAuth provider, etc.)
# 2. Update Railway
railway variables --service WEB --set "DATABASE_URL=postgresql://NEW_PASSWORD@..."
# 3. Redeploy if app caches the env at boot
make prod
```

Some env values (`PORT`, `RAILWAY_*`) are managed by Railway and not user-settable. The CLI errors politely if you try.

## Env scoping

Railway has per-environment vars (`production`, `staging`, etc.). Switch:

```bash
railway environment production
railway variables --service web --set "FOO=prod-value"

railway environment staging
railway variables --service web --set "FOO=staging-value"
```

The Makefile assumes the user has the right environment selected. Don't auto-switch from a recipe.

## Common env keys for Next.js + Railway

| Key | Source | Notes |
|---|---|---|
| `PORT` | Railway-managed | Always `process.env.PORT` in code |
| `NODE_ENV` | Set explicitly | `production` for prod services |
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` | Internal URL |
| `REDIS_URL` | `${{Redis.REDIS_URL}}` | Internal URL |
| `RAILWAY_SERVICE_NAME` | Railway-managed | Useful for logging context |
| `RAILWAY_PRIVATE_DOMAIN` | Railway-managed | `<svc>.railway.internal` |
| `RAILWAY_PUBLIC_DOMAIN` | Railway-managed | `<svc>.up.railway.app` (or custom) |
| Build-time vars | Set on the service that builds | Inlined into the build, can't be changed without redeploy |

## Don't bake secrets into the Makefile

Tempting:

```makefile
deploy-staging:
	railway variables --service web --set "API_KEY=sk-..."
	railway up --service web --detach
```

Wrong. The Makefile is committed; secrets aren't. Use `--set-from-env-file` and gitignore the file:

```makefile
push-env:
	@if [ ! -f .env.railway ]; then echo "✗ .env.railway missing"; exit 1; fi
	railway variables --service web --set-from-env-file .env.railway
```
