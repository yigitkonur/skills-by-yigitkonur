# Return Standardized Structured Error Payloads with Semantic HTTP Statuses

> **Context:** Data Fetching & Endpoints | **Impact:** Medium | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Returning HTTP 200 OK with `{ success: false, error: "Not found" }` is an anti-pattern that breaks client-side HTTP idioms like `response.ok`, prevents proper HTTP caching, and confuses monitoring tools and API consumers. Conversely, letting unhandled exceptions bubble up causes the server adapter to emit raw 500 HTML error pages instead of JSON. Endpoints must catch business errors and return semantic HTTP statuses (400, 401, 403, 404, 422, 500) paired with predictable JSON error payloads.

## 2. How It Differs From Classic React / Next.js

In Next.js Route Handlers or Server Actions, error handling conventions vary widely across versions. In Astro endpoints, handlers have full control over the Web Standard `Response` object. Returning `new Response(JSON.stringify(errorBody), { status, headers })` or `Response.json(errorBody, { status })` gives developers total precision over status codes, status text, and response headers.

## 3. Common Mistakes & Anti-Patterns

Masking HTTP errors behind 200 status codes, or allowing thrown errors to return raw HTML 500 pages.

### ❌ Bad Practice / Anti-Pattern

```ts
// src/pages/api/account.ts
import type { APIRoute } from 'astro'
export const prerender = false

export const GET: APIRoute = async ({ request }) => {
  // ❌ Anti-pattern: HTTP 200 returned for a missing user!
  // Client code `if (res.ok)` incorrectly evaluates to true.
  const user = await findUser(request)
  if (!user) {
    return Response.json({ success: false, message: 'User not found' })
  }

  return Response.json({ success: true, user })
}
```

### ✅ Best Practice / Idiomatic

```ts
// src/pages/api/account.ts
import type { APIRoute } from 'astro'
export const prerender = false

interface ApiErrorPayload {
  error: {
    code: string
    message: string
    details?: unknown
  }
}

export const GET: APIRoute = async ({ request, locals }) => {
  try {
    const userId = new URL(request.url).searchParams.get('id')

    if (!userId) {
      return Response.json(
        { error: { code: 'BAD_REQUEST', message: "Missing required 'id' parameter" } },
        { status: 400 },
      )
    }

    const user = await findUser(userId)

    if (!user) {
      return Response.json(
        { error: { code: 'NOT_FOUND', message: `User '${userId}' does not exist` } },
        { status: 404 },
      )
    }

    return Response.json(user, { status: 200 })
  } catch (err) {
    console.error('Unhandled API error:', err)
    return Response.json(
      { error: { code: 'INTERNAL_SERVER_ERROR', message: 'An unexpected error occurred' } },
      { status: 500 },
    )
  }
}
```

## 4. Verification & Audit

Verify HTTP status codes against failure scenarios using curl:

```bash
# Verify 400 when query parameter is omitted
curl -s -w "\nHTTP Status: %{http_code}\n" http://localhost:4321/api/account

# Verify 404 for non-existent record
curl -s -w "\nHTTP Status: %{http_code}\n" "http://localhost:4321/api/account?id=unknown"
```

The terminal output must display `HTTP Status: 400` and `HTTP Status: 404` with structured JSON error bodies.
