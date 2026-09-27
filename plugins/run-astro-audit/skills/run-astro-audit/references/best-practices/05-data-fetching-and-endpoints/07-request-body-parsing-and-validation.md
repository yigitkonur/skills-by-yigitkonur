# Safely Parse Request Bodies with Content-Type Verification and Validation

> **Context:** Data Fetching & Endpoints | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Calling `await request.json()` indiscriminately in an on-demand endpoint causes unhandled server exceptions (HTTP 500) if a client or automated bot sends an empty payload, malformed JSON, or the wrong `Content-Type`. Robust server endpoints must verify the incoming header (`application/json` vs `multipart/form-data`), safely catch parsing syntax errors, and validate the shape of the parsed data (e.g., using Zod) before executing business logic.

## 2. How It Differs From Classic React / Next.js

In older Next.js Pages router APIs, Next automatically parsed `req.body` into a JavaScript object via built-in body-parser middleware. In Astro (and Web Standards), `request` is a standard `Request` stream. Its body can only be consumed once via `request.json()`, `request.formData()`, `request.text()`, or `request.arrayBuffer()`. If not handled carefully, consumption throws if attempted multiple times or with invalid payloads.

## 3. Common Mistakes & Anti-Patterns

Blindly awaiting `request.json()` without checking headers or wrapping in error boundaries.

### ❌ Bad Practice / Anti-Pattern

```ts
// src/pages/api/lead.ts
import type { APIRoute } from 'astro'
export const prerender = false

export const POST: APIRoute = async ({ request }) => {
  // ❌ Crashes with uncaught 500 error if request body is empty or malformed
  const data = await request.json()

  // ❌ No validation: Vulnerable to prototype pollution or runtime undefined crashes
  await saveLead(data.email, data.phone)

  return Response.json({ status: 'saved' })
}
```

### ✅ Best Practice / Idiomatic

```ts
// src/pages/api/lead.ts
import type { APIRoute } from 'astro'
import { z } from 'astro/zod' // Or standard zod

export const prerender = false

const LeadSchema = z.object({
  email: z.string().email(),
  phone: z.string().min(10),
})

export const POST: APIRoute = async ({ request }) => {
  const contentType = request.headers.get('content-type') ?? ''

  // 1. Verify JSON content-type
  if (!contentType.includes('application/json')) {
    return Response.json({ error: 'Content-Type must be application/json' }, { status: 415 })
  }

  // 2. Safely parse body
  let rawBody: unknown
  try {
    rawBody = await request.json()
  } catch {
    return Response.json({ error: 'Malformed JSON payload' }, { status: 400 })
  }

  // 3. Validate schema
  const parsed = LeadSchema.safeParse(rawBody)
  if (!parsed.success) {
    return Response.json(
      { error: 'Validation failed', details: parsed.error.flatten() },
      { status: 422 },
    )
  }

  await saveLead(parsed.data.email, parsed.data.phone)
  return Response.json({ success: true }, { status: 201 })
}
```

## 4. Verification & Audit

Test malformed and invalid content-type payloads using curl:

```bash
# Test malformed JSON returns 400, not 500
curl -X POST -H "Content-Type: application/json" -d "{bad-json" http://localhost:4321/api/lead

# Test invalid schema returns 422
curl -X POST -H "Content-Type: application/json" -d '{"email":"invalid"}' http://localhost:4321/api/lead
```

Both tests must return client-error statuses (400, 422) with structured error JSON.
