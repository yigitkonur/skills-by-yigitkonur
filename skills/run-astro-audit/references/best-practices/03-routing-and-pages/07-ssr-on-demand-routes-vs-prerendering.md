# Control On-Demand Rendering With prerender Flags in Astro 5

> **Context:** Routing & Pages | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Astro 5 unified build output modes by merging `output: 'hybrid'` into `output: 'static'`. By default, all pages are pre-rendered into static HTML. When an adapter (Node, Cloudflare, Vercel) is configured, individual dynamic routes can opt into server-side on-demand rendering using `export const prerender = false`.

## 2. How It Differs From Classic React / Next.js

Next.js uses segment config options like `export const dynamic = 'force-dynamic'` or `'auto'`. In Astro, the boolean `export const prerender = false` is used. Furthermore, on-demand routes in Astro **must not** export `getStaticPaths()`. They resolve dynamic parameters on the fly via `Astro.params`.

## 3. Common Mistakes & Anti-Patterns

Leaving an unused `getStaticPaths()` in a route marked with `prerender = false`, or using `output: 'hybrid'` in `astro.config.mjs` in Astro 5 (which is removed). Another mistake is trying to export dynamic, non-literal `prerender` values based on runtime conditions (removed in Astro 5).

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/pages/users/[id].astro
// ERROR in Astro: getStaticPaths cannot be used on server-rendered routes!
export const prerender = false;

export async function getStaticPaths() {
  return [{ params: { id: "1" } }];
}
const { id } = Astro.params;
---
<h1>User {id}</h1>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/pages/users/[id].astro
// Opt out of build-time prerendering for real-time dynamic data
export const prerender = false;

const { id } = Astro.params;
// Read parameters dynamically per request
const user = await db.users.findUnique({ where: { id } });

if (!user) {
  return Astro.redirect("/404");
}
---
<main>
  <h1>User Profile: {user.name}</h1>
  <p>Last active: {new Date().toLocaleTimeString()}</p>
</main>
```

## 4. Verification & Audit

Audit your Astro configuration and ensure an adapter is installed when `prerender = false` is used:

```bash
pnpm astro check && pnpm astro build
```

In build output logs, verify that prerendered routes display a static indicator (`○`) while on-demand routes display a server indicator (`λ`).
