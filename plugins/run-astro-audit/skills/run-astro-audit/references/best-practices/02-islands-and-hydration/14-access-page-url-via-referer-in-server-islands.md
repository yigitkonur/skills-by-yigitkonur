# Access Page URL via Referer Header in Server Islands

> **Context:** Islands & Hydration | **Impact:** High | **Target:** Astro 5

## 1. Why We Do This

Server Islands execute in an isolated request context completely decoupled from the parent page request. Inside a component marked with `server:defer`, reading `Astro.url` or `Astro.request.url` does NOT return the URL of the page being visited by the user; instead, it returns an internal endpoint URL (such as `/_server-islands/Avatar`). To read query parameters, search strings, or paths from the host page (especially when the host page was prerendered statically), the server island must inspect the HTTP `Referer` request header.

## 2. How It Differs From Classic React / Next.js

In Next.js, server components execute within the unified page request lifecycle where `searchParams` and route parameters are injected as component props. In Astro 5, Server Islands operate as independent satellite requests triggered by the browser after HTML parsing.

## 3. Common Mistakes & Anti-Patterns

Calling `Astro.url.searchParams.get('filter')` inside a `server:defer` component, expecting the user's browser query parameters, and receiving `null`.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/components/DynamicSearchResults.astro (loaded via server:defer)
// Bug: Astro.url is "/_server-islands/DynamicSearchResults", NOT the page URL!
const query = Astro.url.searchParams.get('q'); // Always returns null!
const results = await searchDatabase(query);
---
<div class="results">
  <p>Search query: {query}</p>
</div>
```

### ✅ Best Practice / Idiomatic

Inspect the HTTP `Referer` header sent by the browser when fetching the server island:

```astro
---
// src/components/DynamicSearchResults.astro (loaded via server:defer)
const referer = Astro.request.headers.get('Referer');
let query = '';

if (referer) {
  const pageUrl = new URL(referer);
  query = pageUrl.searchParams.get('q') || '';
}

const results = await searchDatabase(query);
---
<div class="results">
  <p>Search query: {query}</p>
  <ul>
    {results.map(r => <li>{r.title}</li>)}
  </ul>
</div>
```

## 4. Verification & Audit

In your browser, visit a page with query parameters: `http://localhost:4321/search?q=astro`.
Inspect the server console logs inside the island component:

```bash
console.log('Referer URL:', referer);
```

Confirm that `pageUrl.searchParams.get('q')` resolves accurately to `astro`.
