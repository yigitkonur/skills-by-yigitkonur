# vercel.json reference

Most Next.js projects don't need this file — Vercel auto-detects everything. Add it for the cases auto-detection misses.

## When to use

| Need | `vercel.json` field |
|---|---|
| Custom build command | `buildCommand` |
| Custom output directory | `outputDirectory` |
| Override framework detection | `framework` |
| Redirects | `redirects` (or `next.config.ts` if Next.js) |
| Headers (CORS, security) | `headers` |
| Rewrites (proxy routes) | `rewrites` |
| Crons | `crons` |
| Per-function memory/duration | `functions` |
| Disable preview deploys per branch | `git.deploymentEnabled` |

## Minimal example

```json
{
  "framework": "nextjs"
}
```

That's enough for Vercel to know the project type. Most cases need nothing more.

## Common patterns

### CORS headers for API routes

```json
{
  "headers": [
    {
      "source": "/api/(.*)",
      "headers": [
        { "key": "Access-Control-Allow-Origin", "value": "*" },
        { "key": "Access-Control-Allow-Methods", "value": "GET,POST,OPTIONS" },
        { "key": "Access-Control-Allow-Headers", "value": "Content-Type,Authorization" }
      ]
    }
  ]
}
```

### Security headers (app-wide)

```json
{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Frame-Options", "value": "DENY" },
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" },
        { "key": "Permissions-Policy", "value": "camera=(), microphone=(), geolocation=()" }
      ]
    }
  ]
}
```

For Next.js, prefer `next.config.ts async headers()` — same result, lives with the app code.

### Redirects

```json
{
  "redirects": [
    { "source": "/old", "destination": "/new", "permanent": true },
    { "source": "/blog/:slug", "destination": "/posts/:slug", "permanent": true }
  ]
}
```

### Rewrites (proxy)

```json
{
  "rewrites": [
    { "source": "/api/external/:path*", "destination": "https://api.acme.com/:path*" }
  ]
}
```

The user sees `/api/external/foo`; Vercel proxies to `api.acme.com/foo`. CORS and TLS handled.

### Per-function configuration

```json
{
  "functions": {
    "api/heavy.ts": {
      "memory": 3008,
      "maxDuration": 60
    }
  }
}
```

`memory`: 128MB - 3008MB. Higher → more $.
`maxDuration`: 10s (Hobby), 60s (Pro), 300s (Enterprise) for serverless. Edge: 25s max.

### Vercel cron

```json
{
  "crons": [
    { "path": "/api/cron/cleanup", "schedule": "0 3 * * *" }
  ]
}
```

Schedule is standard cron (UTC). The path is hit via GET. Verify the request:

```ts
// app/api/cron/cleanup/route.ts
import { NextResponse } from 'next/server';

export async function GET(req: Request) {
  if (req.headers.get('authorization') !== `Bearer ${process.env.CRON_SECRET}`) {
    return new NextResponse('Unauthorized', { status: 401 });
  }
  // ... do work
  return NextResponse.json({ ok: true });
}
```

`CRON_SECRET` is auto-set by Vercel; check it on every cron-invoked route.

⚠️ Hobby tier: max 10s per cron + max 2 crons per project. For more, upgrade to Pro or use Railway Cron.

### Disable preview deploys per branch

```json
{
  "git": {
    "deploymentEnabled": {
      "main": true,
      "develop": false,
      "feature/*": false
    }
  }
}
```

Useful for monorepos where you only want main deploys, not every PR.

## Schema validation

Vercel CLI validates `vercel.json` on every deploy. Errors surface immediately:

```bash
vercel deploy --prebuilt
# Error: Invalid header configuration in `vercel.json`: ...
```

The CLI's validation is comprehensive; trust the error messages.

## Don't fight auto-detection

If Vercel's auto-detected `framework`, `buildCommand`, `outputDirectory` are wrong, that's usually a project-shape issue (e.g., monorepo without Root Directory set). Fix the underlying issue first; reach for `vercel.json` overrides as last resort.

## Per-environment vercel.json

Not supported. `vercel.json` is global. Use `process.env.VERCEL_ENV` in code to differentiate per-env behavior.
