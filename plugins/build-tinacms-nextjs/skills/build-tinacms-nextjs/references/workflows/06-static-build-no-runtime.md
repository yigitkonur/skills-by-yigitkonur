# Static Build (no runtime CMS)

Pre-render every page at build time; deploy as static files. No CMS at runtime.

## When this fits

- Site is rarely updated (e.g. once a week)
- Maximum performance (CDN-served static files)
- Air-gapped environments where TinaCloud isn't reachable at runtime
- Maximum reliability (no runtime CMS dependencies)

## Trade-offs

- ✅ Fast (static = CDN cacheable forever)
- ✅ Reliable (no runtime CMS to break)
- ✅ Cheap to host
- ❌ No live editing on deployed env (must rebuild)
- ❌ Editor sees changes only after deploy
- ❌ No `revalidate` / ISR

## Setup

### 1. Build flag

```bash
pnpm tinacms build --local
```

The `--local` flag skips TinaCloud connectivity and uses the local datalayer. The generated client points at the local DB rather than TinaCloud.

### 2. Pre-render every page

```tsx
export async function generateStaticParams() {
  const result = await client.queries.pageConnection({ first: 1000 })
  return result.data.pageConnection.edges?.map((e) => ({ slug: e?.node?._sys.filename ?? '' })) ?? []
}

export const dynamic = 'force-static'   // disable runtime rendering
export const dynamicParams = false      // 404 for unknown slugs
```

Every page known at build time gets pre-rendered. Unknown slugs 404.

### 3. CI build

```yaml
- run: pnpm install --frozen-lockfile
- run: pnpm tinacms build --local --noTelemetry
- run: pnpm next build
```

For CI without TinaCloud creds, `--local` lets the build succeed.

### 4. Deploy

Deploy the `.next/` static output to:

- Vercel (default, serverless functions disabled for these routes)
- Cloudflare Pages
- AWS S3 + CloudFront
- Any static host

For pure-static deployment, use `next export`:

```bash
# next.config.ts
export default { output: 'export' }
```

This emits a fully static directory. Deploy anywhere.

## Editor workflow

Editors edit through the local admin (or a separate admin-only deploy):

```bash
# Locally:
pnpm dev
# Open /admin
# Edit, save → commits to git
# Push → CI rebuilds the static site
# Wait ~minute → live
```

For non-technical editors, give them a streamlined deploy script:

```bash
# scripts/publish.sh
git add content/ && git commit -m "Content update" && git push
echo "Deploy starting; check Vercel in 2 minutes."
```

## Triggering rebuilds

| Trigger | How |
|---|---|
| Editor commits to git | Auto via GitHub → CI |
| Editor saves in admin (TinaCloud) | TinaCloud webhook → Vercel deploy hook |
| Manual | `vercel deploy` or push to a deploy branch |

## When dynamic rendering is needed

Some pages can't be statically pre-rendered:

- User-specific content
- Real-time data (stock prices, etc.)
- Heavy filtering / search

Hybrid: pre-render most pages statically, render dynamic ones at runtime.

```tsx
// Dynamic per-user page:
export const dynamic = 'force-dynamic'

// Static everything else:
export const dynamic = 'force-static'
```

For TinaCMS-driven content, default to static.

## Search

For static-only sites, search is build-time:

- **Pagefind** — generates a static search index from your built site
- **Algolia (via Crawler)** — periodically index your built site

Run after `next build`:

```bash
pnpm next build
pnpm pagefind --site .next
```

## Site updates timing

| Trigger | Time to live |
|---|---|
| Vercel CI build | 1-3 minutes typical |
| Static export + manual upload | 5-30 minutes |
| Cloudflare Pages | 1-5 minutes |

Plan for content edits to take a few minutes to propagate.

## When NOT static-only

- Site has user-specific content
- Real-time updates needed
- Dynamic data (e-commerce inventory)
- Editor expects instant visual editing in production

For these, use ISR + `revalidate` (`references/rendering/10-caching-use-cache.md`).

## Common mistakes

| Mistake | Fix |
|---|---|
| `dynamic = 'force-dynamic'` on TinaCMS pages but expected static | Pages re-render on every request | Use `'force-static'` |
| Forgot `dynamicParams: false` | Unknown slugs still render | Add to disable runtime rendering |
| Static export but `output: 'export'` not set | Half-static half-dynamic | Add to `next.config.ts` |
| Pages > 50000 in `generateStaticParams` | Build times out | Paginate; consider ISR for the long tail |
| Used external media (Cloudinary) without `images.remotePatterns` for next/image | Build fails | Configure remotePatterns |
