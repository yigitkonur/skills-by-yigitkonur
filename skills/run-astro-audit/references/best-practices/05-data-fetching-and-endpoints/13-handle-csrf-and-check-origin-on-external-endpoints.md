# Handle CSRF and `security.checkOrigin` on External Endpoints and Webhooks

> **Context:** Data Fetching & Endpoints | **Impact:** Critical | **Target:** Astro 5

## 1. Why We Do This

Starting in Astro 5.0, `security.checkOrigin` defaults to `true` for all on-demand rendered routes. Astro automatically verifies that incoming `POST`, `PUT`, `PATCH`, and `DELETE` requests include an `Origin` header matching the site's deployment URL. While this provides essential out-of-the-box CSRF protection for HTML form submissions, it immediately breaks external webhook endpoints (e.g., Stripe, Shopify, GitHub) and third-party integrations, returning an unhandled `403 Forbidden` response (`Cross-site POST form submissions are forbidden`).

## 2. How It Differs From Classic React / Next.js

Next.js Route Handlers do not enforce origin checking by default; developers must manually verify CSRF tokens. Astro 5 enforces origin validation at the framework level, requiring deliberate architecture for public APIs and webhooks.

## 3. Common Mistakes & Anti-Patterns

Leaving `security.checkOrigin: true` enabled while hosting payment webhooks (causing payment webhooks to fail with 403), or completely disabling `checkOrigin: false` globally without adding granular CSRF protection for user forms.

### ❌ Bad Practice / Anti-Pattern

```typescript
// astro.config.mjs
export default defineConfig({
  output: 'server',
  // Default checkOrigin: true causes all Stripe/GitHub webhooks to fail with 403!
})

// src/pages/api/webhooks/stripe.ts
export const POST: APIRoute = async ({ request }) => {
  // Never reached! Astro rejects the request before executing this handler!
  return new Response(JSON.stringify({ received: true }), { status: 200 })
}
```

### ✅ Best Practice / Idiomatic

```javascript
// astro.config.mjs
import { defineConfig } from 'astro/config'

export default defineConfig({
  output: 'server',
  // Disable global origin check if accepting external webhooks,
  // then enforce cryptographic signatures and middleware CSRF checks
  security: {
    checkOrigin: false,
  },
})
```

```typescript
// src/pages/api/webhooks/stripe.ts
import type { APIRoute } from 'astro'
import Stripe from 'stripe'

export const prerender = false

export const POST: APIRoute = async ({ request }) => {
  const sig = request.headers.get('stripe-signature')
  const body = await request.text()

  try {
    // Authenticate external caller cryptographically via webhook secret
    const event = Stripe.webhooks.constructEvent(body, sig!, process.env.STRIPE_SECRET!)
    return new Response(JSON.stringify({ status: 'success' }), { status: 200 })
  } catch (err) {
    return new Response('Invalid webhook signature', { status: 400 })
  }
}
```

## 4. Verification & Audit

Simulate an external webhook call with a cross-origin header:

```bash
curl -X POST http://localhost:4321/api/webhooks/stripe \
  -H "Origin: https://dashboard.stripe.com" \
  -H "Content-Type: application/json" \
  -d '{"type":"payment_intent.succeeded"}'
# Must verify webhook signature and return 400/200, never framework-level 403 Forbidden
```
