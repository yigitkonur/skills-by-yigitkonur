# Isolate Secrets and Database Calls in Frontmatter Without Leaking to Client Bundles

> **Context:** Architecture & Philosophy | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

The component script enclosed by triple-dash fences (`---`) executes exclusively on the server (during static build or on-demand SSR). Astro’s compiler strips all frontmatter code from the final response sent to the browser. Database connections, ORM queries, and private authorization keys in frontmatter can never be inspected by the browser.

## 2. How It Differs From Classic React / Next.js

In Next.js App Router, placing sensitive credentials in a component that is later imported into or rendered by a `"use client"` tree can cause build errors or accidentally bundle secrets into public client chunks. In Astro, `.astro` files cannot be hydrated on the client; their frontmatter code is physically stripped by `@astrojs/compiler`.

## 3. Common Mistakes & Anti-Patterns

A common mistake is inadvertently exposing server secrets to the browser by passing them into client scripts via `define:vars` or `data-*` attributes on rendered elements.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/components/UserOrders.astro
// Anti-pattern: Leaking private API keys or full DB records into client script
import { DB } from '../lib/db';
const user = await DB.users.findUnique({ where: { id: Astro.props.userId } });
const STRIPE_SECRET = process.env.STRIPE_SECRET_KEY;
---
<div class="orders">
  <h3>Your Orders</h3>
  <!-- DANGEROUS: define:vars serializes private server values into the client DOM -->
  <script define:vars={{ secretKey: STRIPE_SECRET, userSSN: user.ssn }}>
    console.log("Client script initialized with:", secretKey, userSSN);
  </script>
</div>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/components/UserOrders.astro
// Idiomatic: Only extract and render non-sensitive presentation fields
import { DB } from '../lib/db';
import { getSecret } from 'astro:env/server'; // Astro 5 type-safe server secret

const stripeKey = getSecret('STRIPE_SECRET_KEY'); // Guaranteed server-only
const orders = await DB.orders.findMany({
  where: { userId: Astro.props.userId },
  select: { id: true, total: true, status: true } // Minimize data payload
});
---
<div class="orders">
  <h3>Your Orders</h3>
  <ul>
    {orders.map((order) => (
      <li>Order #{order.id}: {order.status} (${order.total})</li>
    ))}
  </ul>
</div>
<!-- Client scripts receive ZERO server secrets -->
```

## 4. Verification & Audit

Audit your production output to verify no secrets are leaked:

```bash
npx astro build
# Grep production client assets for secret patterns or environment variable names:
grep -rn "sk_live_" dist/client/ dist/_astro/ || echo "No secrets found in client bundle."
```
