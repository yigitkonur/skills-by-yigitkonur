# Prevent Frontmatter Request Waterfalls Using Promise.all

> **Context:** Data Fetching & Endpoints | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Astro component frontmatter (`---`) executes strictly on the server either once at build time (SSG) or per request (SSR). When fetching data from multiple independent remote endpoints, CMS services, or microservices, awaiting them sequentially blocks execution linearly ($T = t_1 + t_2 + t_3$). In SSR mode, this latency directly increases TTFB (Time to First Byte); during static builds, it multiplies overall compilation time across thousands of generated pages. Leveraging `Promise.all` or `Promise.allSettled` dispatches network requests in parallel, reducing latency to the slowest single query ($\max(t_1, t_2, t_3)$).

## 2. How It Differs From Classic React / Next.js

In classic React client components, developers fetch data inside `useEffect` or React Query hooks, where waterfalls often cascade through component subtrees on the client. In Next.js App Router (RSC), developers must also remember parallel fetching, but Astro simplifies this because frontmatter supports top-level `await` directly in the root script fence without wrapping functions in `async` components or server actions.

## 3. Common Mistakes & Anti-Patterns

Sequential `await fetch()` calls for independent datasets are the most common frontmatter performance flaw.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/pages/dashboard.astro
// Serial requests create an unnecessary network waterfall on the server
const userRes = await fetch("https://api.example.com/v1/user/profile");
const user = await userRes.json();

const ordersRes = await fetch("https://api.example.com/v1/orders/recent");
const orders = await ordersRes.json();

const notifsRes = await fetch("https://api.example.com/v1/notifications");
const notifications = await notifsRes.json();
---
<main>
  <h1>Welcome, {user.name}</h1>
</main>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/pages/dashboard.astro
// Parallelize independent queries using Promise.all
const [userRes, ordersRes, notifsRes] = await Promise.all([
  fetch("https://api.example.com/v1/user/profile"),
  fetch("https://api.example.com/v1/orders/recent"),
  fetch("https://api.example.com/v1/notifications"),
]);

if (!userRes.ok || !ordersRes.ok || !notifsRes.ok) {
  throw new Error("Failed to load dashboard data from upstream services");
}

const [user, orders, notifications] = await Promise.all([
  userRes.json(),
  ordersRes.json(),
  notifsRes.json(),
]);
---
<main>
  <h1>Welcome, {user.name}</h1>
  <p>Active orders: {orders.length}</p>
</main>
```

## 4. Verification & Audit

Run a local build with `--verbose` or time request responses under dev:

```bash
# Measure SSR response TTFB before and after Promise.all
curl -w "TTFB: %{time_starttransfer}s | Total: %{time_total}s\n" -o /dev/null -s "http://localhost:4321/dashboard"
```

Ensure timing reflects the maximum single request duration rather than the sum of all endpoints.
