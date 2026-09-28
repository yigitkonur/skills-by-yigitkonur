# Distinguish Build-Time getStaticPaths from On-Demand Endpoint Params

> **Context:** Data Fetching & Endpoints | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Astro supports parameterized endpoint paths like `src/pages/api/products/[id].json.ts`. In static mode, Astro needs to know ahead of time which dynamic routes to build; therefore, static endpoints must export `getStaticPaths()`. In on-demand mode (`prerender = false` or `output: 'server'`), the endpoint resolves any incoming parameter on the fly without a pre-computed list. Exporting `getStaticPaths()` in on-demand mode or omitting it in static mode causes severe build or runtime errors.

## 2. How It Differs From Classic React / Next.js

In Next.js App Router, Route Handlers (`[id]/route.ts`) only use `generateStaticParams()` if static export is configured, but otherwise always resolve params asynchronously (`{ params }: { params: Promise<{ id: string }> }`). In Astro, the separation is explicit: static routes use a synchronous or async `getStaticPaths()`, whereas on-demand routes receive synchronous `params` directly in the `APIContext` object.

## 3. Common Mistakes & Anti-Patterns

Forgetting `getStaticPaths` on static endpoints, or mistakenly expecting `getStaticPaths` props in on-demand endpoints.

### ❌ Bad Practice / Anti-Pattern

```ts
// src/pages/api/[id].json.ts
// Missing prerender = false in a static build, but no getStaticPaths()!
// Build error: [getStaticPaths-required] getStaticPaths() is required for dynamic routes
import type { APIRoute } from 'astro'

export const GET: APIRoute = async ({ params }) => {
  return Response.json({ id: params.id })
}
```

### ✅ Best Practice / Idiomatic

```ts
// 1. Static Endpoint (Build-time generation of /api/0.json, /api/1.json)
// src/pages/api/categories/[id].json.ts
import type { APIRoute, InferGetStaticParamsType } from 'astro'

export function getStaticPaths() {
  return [{ params: { id: 'tech' } }, { params: { id: 'design' } }, { params: { id: 'growth' } }]
}

type Params = InferGetStaticParamsType<typeof getStaticPaths>

export const GET: APIRoute = async ({ params }) => {
  const { id } = params as Params
  const data = await fetchCategoryData(id)
  return Response.json(data)
}

// 2. On-Demand Server Endpoint (Resolved dynamically per request)
// src/pages/api/product/[id].json.ts
export const prerender = false

export const GET: APIRoute = async ({ params }) => {
  const { id } = params
  if (!id) return new Response(null, { status: 400 })

  const product = await queryDatabase(id)
  if (!product) return new Response(null, { status: 404 })

  return Response.json(product)
}
```

## 4. Verification & Audit

Audit your dynamic routes during the build step:

```bash
# Static dynamic routes will list each resolved parameter in build summary
pnpm astro build
```

Verify that on-demand dynamic endpoints resolve runtime queries:

```bash
curl http://localhost:4321/api/product/item-999.json
```
