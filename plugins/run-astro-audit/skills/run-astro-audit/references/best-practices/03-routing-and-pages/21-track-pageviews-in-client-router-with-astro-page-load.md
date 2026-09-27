# Track Pageviews Reliably Under ClientRouter With `astro:page-load`

> **Context:** Routing & Pages | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

When `<ClientRouter />` is enabled, Astro transforms navigation into soft client-side transitions. Standard analytics tags (Google Analytics 4, Google Tag Manager, Plausible, PostHog) that execute only on initial HTML parse will completely miss all subsequent page visits. Furthermore, firing analytics on early router events like `astro:before-preparation` or `astro:after-swap` creates race conditions where `document.title` and canonical metadata still reflect the old page. Firing on `astro:page-load` guarantees that the new DOM, document title, and URL are fully committed.

## 2. How It Differs From Classic React / Next.js

In Next.js App Router, analytics are tracked via `usePathname()` and `useSearchParams()` hooks within a client component or layout effect. In Astro, vanilla analytics scripts must listen to the custom document lifecycle event `astro:page-load` to capture both initial loads and soft transitions.

## 3. Common Mistakes & Anti-Patterns

Relying on default snippet auto-tracking (which loses ~70% of SPA pageviews) or firing tracking tags on `astro:after-swap` before `<title>` is updated.

### ❌ Bad Practice / Anti-Pattern

```html
<!-- src/components/Analytics.astro -->
<!-- Fails: Standard snippet only fires on initial load; blind to SPA navigations -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || []
  function gtag() {
    dataLayer.push(arguments)
  }
  gtag('js', new Date())
  gtag('config', 'G-XXXXX') // Misses all client-side page transitions!
</script>
```

### ✅ Best Practice / Idiomatic

```astro
<!-- src/components/Analytics.astro -->
<script is:inline define:vars={{ gaId: "G-XXXXX" }}>
  window.dataLayer = window.dataLayer || [];
  function gtag() { window.dataLayer.push(arguments); }
  gtag('js', new Date());
  // Disable automatic page_view to prevent double counting on initial load
  gtag('config', gaId, { send_page_view: false });

  // Listen to astro:page-load for initial load and all SPA transitions
  document.addEventListener('astro:page-load', () => {
    gtag('event', 'page_view', {
      page_title: document.title,
      page_location: window.location.href,
      page_path: window.location.pathname,
    });
  });
</script>
```

## 4. Verification & Audit

Open DevTools Console, navigate between 3 pages via client router, and verify analytics payloads:

```javascript
// Check dataLayer events in console
window.dataLayer.filter((item) => item[0] === 'event' && item[1] === 'page_view')
// Must contain 1 event per visited route with accurate page_path and page_title
```
