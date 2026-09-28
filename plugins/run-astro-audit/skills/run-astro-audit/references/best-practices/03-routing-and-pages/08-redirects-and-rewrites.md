# Choose Between Configured Redirects, Dynamic Redirects, and Rewrites

> **Context:** Routing & Pages | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Astro supports three distinct URL mapping strategies: configured redirects (`astro.config.mjs`) for permanent site migrations, dynamic redirects (`Astro.redirect()`) for conditional authentication/flow jumps, and rewrites (`Astro.rewrite()`) to serve alternative route content under the original URL without changing the browser address bar.

## 2. How It Differs From Classic React / Next.js

In Next.js, rewrites and redirects are defined in `next.config.js`. In Astro, configured redirects generate static HTML `<meta http-equiv="refresh">` files in static mode, or delegate to adapter host configuration in SSR. Dynamic redirects in Astro must be returned directly at the page frontmatter level because Astro streams HTML chunks as they render.

## 3. Common Mistakes & Anti-Patterns

Calling `Astro.redirect()` inside a child component rather than the top-level page component (which fails due to HTML streaming already being initiated). Another mistake is using redirects instead of `Astro.rewrite()` for language fallbacks or A/B variants, forcing unnecessary roundtrips.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/components/AuthCheck.astro
// BAD: Calling redirect inside a child component during rendering
const { user } = Astro.props;
if (!user) {
  // Silent failure or stream corruption: page headers already sent!
  Astro.redirect("/login");
}
---
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/pages/dashboard.astro
// Always handle dynamic redirects at the top of the root page frontmatter
const session = Astro.cookies.get("session")?.value;
if (!session) {
  return Astro.redirect("/login", 302);
}
---
<h1>Welcome to your Dashboard</h1>
```

```astro
---
// src/pages/es-cu/[...slug].astro
// Use Astro.rewrite() to render Cuban Spanish using default Spanish content
// Browser URL remains /es-cu/articles/intro while rendering /es/articles/intro
return Astro.rewrite(`/es/${Astro.params.slug}`);
---
```

## 4. Verification & Audit

Verify redirect status codes using curl:

```bash
curl -I http://localhost:4321/dashboard
```

Confirm the HTTP response header shows `HTTP/1.1 302 Found` with `Location: /login`. For rewrites, verify the response serves content with status `200` without changing the requested URL.
