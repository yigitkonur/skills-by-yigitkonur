# Implement Secure 404 and 500 Error Boundaries in Astro

> **Context:** Routing & Pages | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Proper error routing protects user trust and application security. `src/pages/404.astro` automatically compiles to `404.html`, which static CDNs and edge servers natively serve on missing resources. In SSR on-demand mode, `src/pages/500.astro` intercepts unhandled runtime exceptions and receives an `error` prop to render a graceful fallback.

## 2. How It Differs From Classic React / Next.js

In Next.js App Router, error handling uses `not-found.tsx` and client component `error.tsx` with reset boundaries. In Astro, error boundaries are server-rendered `.astro` pages (`404.astro` and `500.astro`). In SSR mode, `500.astro` runs on the server and receives `Astro.props.error` directly.

## 3. Common Mistakes & Anti-Patterns

Printing the raw `error.stack` inside `500.astro` in production, which leaks internal server directory structures, database schema names, and secret traces to attackers. Another mistake is expecting `500.astro` to render during static builds when a build error occurs (build errors halt the build process).

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/pages/500.astro (SSR Mode)
const { error } = Astro.props;
---
<h1>Server Error</h1>
<!-- DANGEROUS: Leaks stack trace and file paths to the public! -->
<pre>{(error as any)?.stack}</pre>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/pages/500.astro
interface Props {
  error: unknown;
}

const { error } = Astro.props;
const isDev = import.meta.env.DEV;

// Log error safely on the server side
console.error("[SSR 500 Error Handler]:", error);

const displayMessage = error instanceof Error
  ? error.message
  : "An unexpected server error occurred.";
---
<main class="error-container">
  <h1>500 - Server Internal Error</h1>
  <p>We are experiencing technical difficulties. Please try again shortly.</p>

  {isDev && (
    <details class="dev-diagnostics">
      <summary>Development Diagnostics</summary>
      <pre>{displayMessage}</pre>
    </details>
  )}
  <a href="/">Return to Homepage</a>
</main>
```

## 4. Verification & Audit

Test your custom 404 and 500 routes:

```bash
curl -I http://localhost:4321/non-existent-path-for-test-404
```

Confirm the response status is `404 Not Found`. Trigger an intentional throw on an SSR route and verify `500.astro` renders without displaying sensitive server stack traces.
