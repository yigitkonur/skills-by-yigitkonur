# Edge Runtime Not Supported

The TinaCMS backend (and any code that imports `@tinacms/datalayer`) requires Node.js. **It does not run on Cloudflare Workers, Vercel Edge Functions, or any V8-isolate runtime.**

## What's blocked

Don't use TinaCMS in:

- Cloudflare Workers
- Vercel Edge Functions
- Vercel Edge Middleware (note: `proxy.ts` runs on Node, NOT Edge — that's fine)
- Deno Deploy (untested)
- AWS Lambda@Edge / CloudFront Functions

## Why

TinaCMS' backend depends on:

- Node-specific module imports (`fs`, `path`, etc.)
- esbuild for schema compilation
- Native `level`-style adapters
- GraphQL server runtime

V8-isolate runtimes don't expose these. **No upstream fix is planned** — TinaCMS is positioned as a Node.js backend.

## What works

- Vercel Functions (Node.js runtime — default)
- Netlify Functions (Node.js)
- AWS Lambda (Node.js)
- Your own Node.js server (Express, Fastify, etc.)
- Docker containers running Node

For Next.js routes that call TinaCMS:

```typescript
// ✅ Default — runs on Node.js
export async function GET() { ... }

// ❌ DO NOT
export const runtime = 'edge'
```

## Specifically: Next.js route handlers

The route at `app/api/tina/[...routes]/route.ts` (self-hosted) MUST run on Node.js. Any other route that imports `@/tina/__generated__/client` and calls `client.queries.X(...)` should also run on Node — the client uses fetch which works on Edge, but Vercel data cache integration works better on Node.

For pages that fetch TinaCMS data, App Router Server Components run on Node by default. Don't override with `runtime = 'edge'`.

## Common false positives

These DO run on Node by default:

- `proxy.ts` (Next.js 16 — Node runtime)
- Server Components (App Router — Node by default)
- Server Actions (Node by default)

These DO run on Edge by default:

- `middleware.ts` (Next.js 15 — **Edge by default**; this is the trap. If you import `@tinacms/datalayer` or any Node-only module from middleware without `export const runtime = 'nodejs'`, the build fails or middleware errors at runtime.)
- Edge Functions explicitly marked with `export const runtime = 'edge'`

If you're unsure, check Vercel's "Functions" tab in the dashboard. Each function shows its runtime.

## Sub-path deployment

Same family of issues — sub-path deployment is also broken (see `references/concepts/03-tinacloud-vs-self-hosted.md`). **Deploy at domain root.**

## Workarounds

### "But I want to use Workers..."

Two patterns:

1. **Hybrid:** Run TinaCMS on Vercel Functions, use Workers for the public-facing site (Workers reads pre-rendered HTML)
2. **Static export:** Pre-render every page at build time (Vercel/CI), serve as static files via Workers

The CMS backend is always Node-hosted; the public site can be wherever.

### "But Edge would be faster for queries..."

It would, but the tradeoff isn't possible. Workarounds:

- Cache aggressively (`"use cache"`, `revalidate`)
- Pre-render via `generateStaticParams`
- Accept Node cold-start latency

## Cloudflare Workers — claims you may see

Some older blog posts and (defunct) skills suggest Cloudflare Workers self-hosting. **They're outdated.** Current TinaCMS doesn't support this. The community has tried — the conclusion is consistent.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| `export const runtime = 'edge'` on a TinaCMS route | Build fails or runtime error | Remove |
| Tried to deploy backend to Cloudflare Workers | Build error | Use Vercel/Netlify Functions |
| Followed an old guide for Workers | Wasted setup time | Use the current Vercel-hosted path |
| Mixed Node + Edge in the same app | Confusing — but works for non-TinaCMS routes | OK for unrelated routes |
