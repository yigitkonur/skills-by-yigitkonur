# Migrate Next.js Route Handlers to Native Astro API Endpoints

> **Context:** Auditing & Next.js Migration | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Migrating Next.js API Routes (Pages Router `NextApiHandler` or App Router Route Handlers) to Astro establishes clean, standards-compliant server endpoints. Astro endpoints use the web-standard `Request` and `Response` APIs. Crucially, Astro allows static prerendering of endpoints (`export const prerender = true`), generating static JSON, RSS, or XML files at build time without requiring an active server runtime or serverless invocation costs.

## 2. How It Differs From Classic React / Next.js

Next.js App Router Route Handlers return `NextResponse` and run within the Next.js edge or Node server runtime. In Astro, endpoints are defined in `src/pages/` with `.ts` or `.js` extensions, exporting named HTTP method handlers (`GET`, `POST`, `PUT`, `DELETE`). The context parameter provides typed access to `request`, `params`, `cookies`, `locals`, and `redirect()`.

## 3. Common Mistakes & Anti-Patterns

Using Node.js-specific `req` and `res` objects from Express or Next.js Pages router. Another mistake is deploying a full serverless function for read-only static data feeds (like product search indices or RSS) when Astro can prerender them to static disk files at build time.

### ❌ Bad Practice / Anti-Pattern

```ts
// Next.js Pages Router: Node-specific response helper
// pages/api/feed.ts
import type { NextApiRequest, NextApiResponse } from 'next'

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  // Requires Node server runtime for simple static data
  res.status(200).json({ status: 'ok', items: [1, 2, 3] })
}
```

### ✅ Best Practice / Idiomatic

```ts
// Astro: Web-standard APIRoute with static prerendering support
// src/pages/api/feed.json.ts
import type { APIRoute } from 'astro'

// Prerenders this endpoint at build time into dist/api/feed.json!
export const prerender = true

export const GET: APIRoute = async ({ request, url }) => {
  const items = [1, 2, 3]
  return new Response(JSON.stringify({ status: 'ok', items }), {
    status: 200,
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'public, max-age=3600',
    },
  })
}
```

## 4. Verification & Audit

Verify that the prerendered endpoint produces a static JSON file in `dist/`:

```bash
# Verify static JSON file was written during build
pnpm build
test -f dist/api/feed.json && echo "PASS: Static API endpoint generated at dist/api/feed.json"
```
