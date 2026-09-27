# Opt Out Heavy, Dynamic, or State-Mutating Routes From Prefetch

> **Context:** Performance & Prefetch | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Prefetching sends HTTP GET requests in the background. If a route triggers heavy SSR database queries, uncacheable session operations, or accidental state mutations (such as un-idempotent GET handlers or analytics pings), prefetching wastes server resources and can cause unexpected session side effects. Using `data-astro-prefetch="false"` explicitly protects these sensitive links.

## 2. How It Differs From Classic React / Next.js

In Next.js, `<Link prefetch={false}>` is used to disable prefetching on a single link. In Astro, when global prefetching (`prefetchAll: true`) or `<ClientRouter />` is active, every `<a>` tag prefetches by default unless explicitly disabled with `data-astro-prefetch="false"`.

## 3. Common Mistakes & Anti-Patterns

Letting global prefetch trigger background requests to sign-out endpoints, heavy report downloads, or checkout session initialization.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/components/UserDropdown.astro
---
<div class="user-menu">
  <a href="/dashboard/analytics">Deep Analytics (Heavy DB)</a>
  <a href="/checkout/review">Checkout Session</a>
  <!-- Accidentally triggers logout or invalidates auth token on hover! -->
  <a href="/api/auth/signout">Sign Out</a>
</div>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/components/UserDropdown.astro
---
<div class="user-menu">
  <a href="/dashboard/analytics" data-astro-prefetch="false">
    Deep Analytics (Heavy DB)
  </a>
  <a href="/checkout/review" data-astro-prefetch="false">
    Checkout Session
  </a>
  <!-- Explicitly disabled prefetch prevents accidental trigger -->
  <a href="/api/auth/signout" data-astro-prefetch="false">
    Sign Out
  </a>
</div>
```

## 4. Verification & Audit

Audit your codebase for sensitive action endpoints without prefetch opt-out:

```bash
grep -rnE 'href="[^"]*(signout|logout|checkout|download)' src/ | grep -v 'data-astro-prefetch="false"'
```

Verify in the browser Network tab that hovering over "Sign Out" or "Checkout" emits zero HTTP requests.
