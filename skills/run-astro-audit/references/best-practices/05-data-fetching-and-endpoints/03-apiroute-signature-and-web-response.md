# Type Endpoints with APIRoute and Return Standard Web Responses

> **Context:** Data Fetching & Endpoints | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Astro endpoints adhere strictly to the Web Standards API (`Request` and `Response`). When an endpoint returns a plain JavaScript object or attempts to invoke legacy Node/Express methods (`res.json()`, `res.status()`), Astro throws the error: _"The endpoint did not return a Response."_ Endpoints must always return an instance of Web API `Response` (or `Response.json(...)`). Using Astro's built-in `APIRoute` type ensures complete type safety for route parameters, contextual request metadata (`request`, `cookies`, `locals`), and the required return type.

## 2. How It Differs From Classic React / Next.js

Next.js provides proprietary helpers like `NextResponse.json()` and `NextRequest`. Remix and SvelteKit also wrap standard responses in custom helper utilities. Astro embraces raw Web Standards: `new Response()` or the standard ES2023 `Response.json(data, init)`. There is no framework-specific response class to learn or maintain; code written for Astro endpoints ports directly to Cloudflare Workers, Deno, or Bun.

## 3. Common Mistakes & Anti-Patterns

Returning naked objects or importing proprietary framework response wrappers.

### ❌ Bad Practice / Anti-Pattern

```ts
// src/pages/api/profile.ts
// FAILS: Returning raw object throws "The endpoint did not return a Response"
// Also lacks typing for context arguments
export async function GET(context: any) {
  const user = { id: 1, name: 'Alice' }
  // ❌ Fatal Error in Astro runtime:
  return { user }
}

// ❌ Bad: Importing Next.js or Node-specific helpers
// import { NextResponse } from "next/server";
// return NextResponse.json(user);
```

### ✅ Best Practice / Idiomatic

```ts
// src/pages/api/profile.ts
import type { APIRoute } from 'astro'

export const prerender = false

export const GET: APIRoute = async ({ request, locals, cookies }) => {
  // Access typed context properties directly
  const authToken = cookies.get('session')?.value

  if (!authToken) {
    return Response.json({ error: 'Unauthorized access' }, { status: 401 })
  }

  const profile = {
    id: 1,
    name: 'Alice',
    role: locals.userRole ?? 'member',
  }

  return Response.json(profile, {
    status: 200,
    headers: {
      'Cache-Control': 'private, no-cache, no-store, must-revalidate',
    },
  })
}
```

## 4. Verification & Audit

Run TypeScript compilation and curl the endpoint to verify valid headers and payload:

```bash
# Verify TypeScript signatures match APIRoute contract
pnpm astro check

# Verify Response status and Content-Type header
curl -I http://localhost:4321/api/profile
```

The response headers must contain `content-type: application/json` and valid HTTP status code.
