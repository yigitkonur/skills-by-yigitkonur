# Export Explicit HTTP Method Handlers Instead of Monolithic Request Switching

> **Context:** Data Fetching & Endpoints | **Impact:** Medium | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Astro dispatches incoming requests to exported named HTTP functions matching the request method: `GET`, `POST`, `PUT`, `DELETE`, `PATCH`, or `ALL`. When developers write a monolithic handler using `switch (request.method)`, they bypass Astro's built-in router benefits. Exporting explicit handlers allows Astro to automatically serve `HEAD` requests by invoking `GET` and stripping the body, and cleanly rejects unsupported HTTP methods with appropriate 404/405 semantics without cluttering handler logic.

## 2. How It Differs From Classic React / Next.js

In Next.js Pages router (`pages/api/handler.ts`), developers were forced to export a default function and write giant `switch (req.method)` statements. In Next.js App Router and Astro, individual uppercase method functions are exported (`export async function GET()`). Astro also offers `export const ALL: APIRoute` as a fallback or catch-all proxy, but named exports remain the idiomatic pattern for RESTful design.

## 3. Common Mistakes & Anti-Patterns

Using a catch-all handler with nested method branching instead of granular function exports.

### ❌ Bad Practice / Anti-Pattern

```ts
// src/pages/api/posts.ts
import type { APIRoute } from 'astro'
export const prerender = false

// Monolithic switch statement: brittle, poor tree-shaking, manual 405 logic
export const ALL: APIRoute = async ({ request }) => {
  switch (request.method) {
    case 'GET':
      return Response.json(await getPosts())
    case 'POST':
      return Response.json(await createPost(request))
    default:
      return new Response('Method Not Allowed', { status: 405 })
  }
}
```

### ✅ Best Practice / Idiomatic

```ts
// src/pages/api/posts.ts
import type { APIRoute } from 'astro'
export const prerender = false

// 1. GET handler: Astro automatically handles HEAD requests for this route
export const GET: APIRoute = async () => {
  const posts = await getPosts()
  return Response.json(posts, { status: 200 })
}

// 2. POST handler: Isolated logic, clean payload parsing
export const POST: APIRoute = async ({ request }) => {
  const body = await request.json()
  const created = await createPost(body)
  return Response.json(created, { status: 201 })
}

// 3. DELETE handler: Granular error boundaries per operation
export const DELETE: APIRoute = async ({ request }) => {
  const { id } = await request.json()
  await deletePost(id)
  return new Response(null, { status: 204 })
}
```

## 4. Verification & Audit

Test HTTP method compliance using curl:

```bash
# Verify HEAD requests are handled automatically without extra code
curl -I http://localhost:4321/api/posts

# Verify unsupported methods (e.g. PUT) are rejected as expected
curl -X PUT -I http://localhost:4321/api/posts
```

Astro should automatically resolve `HEAD` with headers and handle undefined verbs cleanly.
