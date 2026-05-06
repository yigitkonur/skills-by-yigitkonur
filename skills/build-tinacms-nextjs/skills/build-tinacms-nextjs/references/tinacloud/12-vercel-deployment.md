# Vercel Deployment with TinaCloud

The recommended hosting stack: Vercel + TinaCloud. Setup, env vars, deploy hooks, and the cache caveat.

## Why Vercel

- Native Next.js host (built by the same team)
- Generous free tier
- Per-branch preview deployments (works great with Editorial Workflow)
- Native ISR / `revalidate` support
- Vercel Analytics + Speed Insights for free
- Automatic SSL

## Setup

1. Push project to GitHub
2. Vercel → New Project → Import Repository
3. Framework auto-detected as Next.js
4. Configure environment variables (below)
5. Deploy

## Required env vars

```env
# In Vercel Project Settings → Environment Variables
NEXT_PUBLIC_TINA_CLIENT_ID=<from TinaCloud>
TINA_TOKEN=<from TinaCloud>
NEXT_PUBLIC_TINA_BRANCH=main
```

Scope to **Production** + **Preview** environments. **Development** can be left blank if you use local-only mode.

## Build command

Default `package.json` `build` script handles this:

```json
{
  "scripts": {
    "build": "tinacms build && next build"
  }
}
```

If overriding in Vercel **Project Settings → Build & Development Settings → Build Command**, use:

```
pnpm tinacms build && pnpm next build
```

## Required Vercel packages

```bash
pnpm add @vercel/analytics @vercel/speed-insights
```

In root layout:

```tsx
// app/layout.tsx
import { Analytics } from '@vercel/analytics/next'
import { SpeedInsights } from '@vercel/speed-insights/next'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html>
      <body>
        {children}
        <Analytics />
        <SpeedInsights />
      </body>
    </html>
  )
}
```

## Deploy Hooks for content rebuilds

Static sites need rebuilds on content change. Set up:

1. Vercel **Project Settings → Git → Deploy Hooks → Create Hook**
2. Copy the URL
3. In TinaCloud Project Settings → Webhooks → Add the URL
4. Set target branches to `main` (or your prod branch)

Now content commits trigger Vercel rebuilds.

For ISR / `cacheComponents` setups, the deploy hook is optional — `revalidate: 60` keeps content fresh without a full rebuild.

## Vercel cache caveat

Vercel's data cache stores TinaCloud responses for up to a year. **Add `revalidate` to client queries:**

```tsx
const result = await client.queries.page(
  { relativePath: `${slug}.md` },
  { fetchOptions: { next: { revalidate: 60 } } },
)
```

See `references/rendering/11-vercel-cache-caveat.md` for the full discussion.

## Per-branch preview

Vercel auto-creates preview deployments per branch. With Editorial Workflow:

- Editor's branch → Vercel preview URL
- Wire `previewUrl` in `tina/config.ts`:

```typescript
ui: {
  previewUrl: (context) => ({
    url: `https://my-app-git-${context.branch}.vercel.app`,
  }),
}
```

## Vercel Team Environment Variables

For teams with multiple projects sharing TinaCloud credentials:

1. Vercel Team Settings → Environment Variables
2. Set `NEXT_PUBLIC_TINA_CLIENT_ID` etc. at the team level
3. All projects in the team inherit them

Avoid duplicating creds across projects.

## Edge runtime — DO NOT enable

Don't deploy TinaCMS server functions to Vercel Edge. The TinaCMS backend (self-hosted) is Node.js only. Even for TinaCloud projects, your Next.js routes that call `client.queries.X(...)` should run on Node — not Edge.

If you've added `export const runtime = 'edge'` to a route that uses TinaCMS, remove it.

## Vercel Analytics + Speed Insights

Both are free and zero-config. Add the components and Vercel collects metrics automatically. Worth setting up — surfaces Core Web Vitals issues.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Forgot env vars in Vercel | Deploy fails or admin doesn't load | Add all three vars |
| Wrong build command | "Cannot find module '../tina/__generated__/client'" | Use `tinacms build && next build` |
| No deploy hook + no `revalidate` | Content stale forever | Add one or both |
| `runtime: 'edge'` on a TinaCMS route | Build fails or runtime error | Remove |
| Used `.env.local` instead of Vercel env | Variables not picked up | Set in Vercel UI |
