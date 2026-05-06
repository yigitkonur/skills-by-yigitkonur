# Vercel + TinaCloud (Default)

The recommended stack. Most TinaCMS projects deploy this way.

## Architecture

```
GitHub repo (content + code)
   ↓ push
Vercel (Next.js app + functions)
   ↑ ↓ Editor uses /admin which loads:
TinaCloud (managed CMS backend, auth, search)
   ↕ webhooks
GitHub (commits content via TinaCloud's GitHub App)
```

## Setup

1. Push project to GitHub
2. Vercel: New Project → Import Repository
3. Vercel auto-detects Next.js, sets build command from `package.json`
4. Add env vars (Production + Preview):
   ```env
   NEXT_PUBLIC_TINA_CLIENT_ID=<from app.tina.io>
   TINA_TOKEN=<read-only token>
   NEXT_PUBLIC_TINA_BRANCH=main
   ```
5. Deploy

## Build command

The default from `package.json`:

```json
{
  "scripts": {
    "build": "tinacms build && next build"
  }
}
```

Vercel runs `pnpm build`, which executes both. No override needed.

## Deploy hooks

For static rebuilds on content change:

1. Vercel Project Settings → Git → Deploy Hooks → Create
2. Copy URL
3. TinaCloud Project Settings → Webhooks → paste URL
4. Set target branches to `main`

Alternative: use ISR (`fetchOptions: { next: { revalidate: 60 } }`) and skip the hook.

## Vercel cache caveat

Vercel's data cache stores TinaCloud responses for up to a year. **Always pass `revalidate`:**

```tsx
const result = await client.queries.page(
  { relativePath: `${slug}.md` },
  { fetchOptions: { next: { revalidate: 60 } } },
)
```

See `references/rendering/11-vercel-cache-caveat.md`.

## Required Vercel packages

```bash
pnpm add @vercel/analytics @vercel/speed-insights
```

In `app/layout.tsx`:

```tsx
import { Analytics } from '@vercel/analytics/next'
import { SpeedInsights } from '@vercel/speed-insights/next'

<body>
  {children}
  <Analytics />
  <SpeedInsights />
</body>
```

Free, gives you Core Web Vitals + analytics.

## Per-branch preview deployments

Vercel auto-creates a preview per branch. With Editorial Workflow:

- Editor's branch → Vercel preview URL
- Wire `previewUrl` in `tina/config.ts`

```typescript
ui: {
  previewUrl: (context) => ({
    url: `https://my-app-git-${context.branch}.vercel.app`,
  }),
}
```

## Team Environment Variables

Vercel Team Settings → Environment Variables → set TinaCloud creds at the team level. All projects in the team inherit. No need to duplicate.

## Edge runtime — DO NOT use

Don't add `export const runtime = 'edge'` to routes that use TinaCMS client. The TinaCMS client uses Node-only modules and fails on Edge.

## Verifying

After deploy:

1. Visit `<your-domain>/admin/index.html` — should load TinaCMS admin
2. Login with your TinaCloud account
3. Make an edit, save
4. Vercel → Deployments — should see a new deploy triggered (if deploy hook wired)
5. Visit a page — content should update within 60 seconds (if `revalidate` set)

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Forgot env vars | Admin doesn't load | Set in Vercel project settings |
| Wrong `NEXT_PUBLIC_TINA_BRANCH` | Saves go to wrong branch | Match `main` (or set `VERCEL_GIT_COMMIT_REF` waterfall) |
| Used `runtime: 'edge'` on a TinaCMS route | Build fails | Remove |
| Forgot deploy hook + no `revalidate` | Stale content forever | Add one or both |
| `.env.local` committed | Token leak | Gitignore `.env.local` |
