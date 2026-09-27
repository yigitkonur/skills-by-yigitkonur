# Explicitly Declare export const prerender = false on Dynamic Endpoints

> **Context:** Data Fetching & Endpoints | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

By default in Astro (both Astro 4 and Astro 5), `output: 'static'` prerenders every route and endpoint at build time into immutable static files (HTML, JSON, XML). An API route like `src/pages/api/subscribe.json.ts` will be called once during `astro build` and written to disk. If that endpoint handles contact forms, authentication, or live database mutations, it will fail silently or reject incoming HTTP POST requests in production. To turn an endpoint into an on-demand runtime server handler, you must explicitly declare `export const prerender = false;` and configure a deployment adapter.

## 2. How It Differs From Classic React / Next.js

In Next.js App Router, Route Handlers (`app/api/route.ts`) containing `POST`, `PUT`, `DELETE`, or accessing dynamic `request` properties automatically opt out of static caching. In Astro, the static build model takes precedence: endpoints remain static build artifacts unless `prerender = false` is explicitly specified (or `output: 'server'` is set globally in `astro.config.mjs`). Note that Astro 5 removed `output: 'hybrid'`, standardizing this behavior under `output: 'static'`.

## 3. Common Mistakes & Anti-Patterns

Omitting `prerender = false` on mutation endpoints or omitting an adapter in static mode.

### ❌ Bad Practice / Anti-Pattern

```ts
// src/pages/api/newsletter.ts
// Missing prerender = false in a static project:
// This endpoint executes ONCE during CI build and becomes a static file!
import type { APIRoute } from 'astro'

export const POST: APIRoute = async ({ request }) => {
  const data = await request.formData()
  const email = data.get('email')
  // Database mutation will never run for production website visitors!
  return new Response(JSON.stringify({ registered: email }), { status: 200 })
}
```

### ✅ Best Practice / Idiomatic

```ts
// src/pages/api/newsletter.ts
import type { APIRoute } from 'astro'

// Explicitly opt out of prerendering so this route handles live HTTP requests
export const prerender = false

export const POST: APIRoute = async ({ request }) => {
  if (request.headers.get('Content-Type') !== 'application/json') {
    return new Response(JSON.stringify({ error: 'Invalid Content-Type' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    })
  }

  const body = await request.json()
  const email = body.email

  // Perform runtime database / email service mutation
  return new Response(JSON.stringify({ success: true, email }), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  })
}
```

## 4. Verification & Audit

Audit your endpoints by inspecting build logs and testing runtime responses:

```bash
# Verify the build output categorizes the endpoint as server (λ / server) not static (○ / prerender)
pnpm astro build

# Verify dynamic POST handling against the preview or staging server
curl -X POST -H "Content-Type: application/json" -d '{"email":"test@example.com"}' http://localhost:4321/api/newsletter
```

Build output must display the route under Server (on-demand) routes, and `astro.config.mjs` must define an adapter.
