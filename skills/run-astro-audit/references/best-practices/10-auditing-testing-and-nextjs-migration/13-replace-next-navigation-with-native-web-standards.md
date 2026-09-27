# Replace next/navigation Hooks with Standard HTML Links and Astro.url

> **Context:** Auditing & Next.js Migration | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Next.js applications rely on client-side routing abstraction packages (`next/link`, `useRouter`, `usePathname`, `useSearchParams`). These abstractions bundle extensive client router runtimes, history managers, and custom event listeners into every page. Astro returns to web standards: navigation is powered by standard HTML `<a>` tags (with optional zero-JS speculative prefetching), while server-rendered routes read incoming URLs directly through the native `Astro.url` Web API.

## 2. How It Differs From Classic React / Next.js

In Next.js, reading current route parameters or queries in client components requires mounting React hooks (`usePathname()`). In Astro, URL inspection happens on the server before HTML is sent. `Astro.url` is a standard browser `URL` instance available directly in any `.astro` frontmatter.

## 3. Common Mistakes & Anti-Patterns

Importing `next/link` or attempting to wrap links in React components just to achieve page navigation. Another mistake is creating client React components solely to read URL search parameters that could have been read in Astro frontmatter.

### ❌ Bad Practice / Anti-Pattern

```tsx
// Next.js: Client component required to read search params and navigate
'use client'
import Link from 'next/link'
import { useSearchParams, useRouter } from 'next/navigation'

export default function SearchHeader() {
  const searchParams = useSearchParams()
  const query = searchParams.get('q') || ''
  const router = useRouter()

  return (
    <nav>
      <Link href="/dashboard">Dashboard</Link>
      <p>Current Search: {query}</p>
      <button onClick={() => router.push('/logout')}>Log Out</button>
    </nav>
  )
}
```

### ✅ Best Practice / Idiomatic

```astro
---
// Astro: Pure server evaluation with native Web URL standards
const query = Astro.url.searchParams.get('q') || '';
const currentPath = Astro.url.pathname;
---
<nav>
  <!-- Standard HTML anchor with optional Astro prefetch directive -->
  <a href="/dashboard" data-astro-prefetch>Dashboard</a>
  <p>Current Search: {query}</p>
  <a href="/logout">Log Out</a>
</nav>
```

## 4. Verification & Audit

Verify that pages render native `<a>` anchors without client router JS wrappers:

```bash
# Verify standard anchor tags in built HTML
grep -E '<a\s+href="/dashboard"' dist/index.html && echo "PASS: Standard HTML anchor tags verified"
```
