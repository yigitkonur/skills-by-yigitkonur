# Prefer Hover or Tap Prefetch Strategies Over Eager Loading

> **Context:** Performance & Prefetch | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Astro provides four prefetch triggers: `hover`, `tap`, `viewport`, and `load`. Eager `load` prefetching downloads target HTML immediately after window load, consuming bandwidth for unvisited destinations. `hover` captures user intent on desktop during the 100–300ms cursor dwell before click. `tap` prefetches on `touchstart`/`pointerdown` (50–100ms head start), eliminating false-positive downloads on mobile.

## 2. How It Differs From Classic React / Next.js

React routers and Next.js `<Link>` historically relied on viewport intersection observers by default. In Astro, `hover` is the deliberate default because Astro navigates between full HTML documents. Astro's prefetch client automatically debounces quick mouse swipes and falls back to `tap` under slow connections.

## 3. Common Mistakes & Anti-Patterns

Using `data-astro-prefetch="load"` on multiple navigation menus or footer links, triggering an avalanche of background requests upon initial page mount.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/components/GlobalNavbar.astro
---
<nav class="site-nav">
  <!-- Eager load prefetching on every header link saturates initial bandwidth -->
  <a href="/pricing" data-astro-prefetch="load">Pricing</a>
  <a href="/enterprise" data-astro-prefetch="load">Enterprise</a>
  <a href="/case-studies" data-astro-prefetch="load">Case Studies</a>
  <a href="/docs" data-astro-prefetch="load">Documentation</a>
</nav>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/components/GlobalNavbar.astro
---
<nav class="site-nav">
  <!-- Hover provides 150ms prefetch buffer on desktop without upfront cost -->
  <a href="/pricing" data-astro-prefetch="hover">Pricing</a>
  <a href="/enterprise" data-astro-prefetch="hover">Enterprise</a>
  <!-- Tap strategy captures mobile intent on touch start -->
  <a href="/case-studies" data-astro-prefetch="tap">Case Studies</a>
  <a href="/docs" data-astro-prefetch="hover">Documentation</a>
</nav>
```

## 4. Verification & Audit

Audit your codebase for unwarranted `load` prefetch directives:

```bash
grep -rn 'data-astro-prefetch="load"' src/
```

In DevTools Network tab, ensure no prefetch requests fire until the pointer hovers over a navigation anchor for at least 65ms (Astro intent threshold).
