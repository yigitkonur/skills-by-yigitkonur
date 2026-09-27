# Stream HTML Chunks Early Using Unblocked Component Rendering

> **Context:** Architecture & Philosophy | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Astro’s SSR engine renders components as a stream of raw HTML chunks via `ReadableStream`. When page rendering starts, the initial `<head>`, critical CSS, and above-the-fold layout markup flush to the client immediately. This gives users immediate visual feedback and allows browsers to preload fonts and assets while backend fetches resolve in parallel.

## 2. How It Differs From Classic React / Next.js

Next.js App Router streaming relies on React Server Components (RSC) and Suspense boundaries that output serialized virtual DOM payloads (`$RC` flight streams) needing client-side React hydration to assemble. Astro streams native, standard HTML chunks directly. No client-side framework runtime is required to decode or render the incoming markup.

## 3. Common Mistakes & Anti-Patterns

Awaiting all data fetches inside the root page frontmatter blocks the entire response pipeline. The server sits idle waiting for slow APIs, unable to flush headers or document head, degrading TTFB.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/pages/dashboard.astro
// Anti-pattern: Top-level awaits block the HTTP response stream
const user = await fetch('https://api.internal/slow-user').then(r => r.json());
const analytics = await fetch('https://api.internal/slow-analytics').then(r => r.json());
---
<html>
  <head><title>Dashboard</title></head>
  <body>
    <!-- Browser receives ZERO bytes until BOTH slow APIs finish -->
    <header>Welcome {user.name}</header>
    <main>Analytics: {analytics.summary}</main>
  </body>
</html>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/pages/dashboard.astro
// Idiomatic: Pass promises to leaf components or template expressions directly
import UserHeader from '../components/UserHeader.astro';
import AnalyticsWidget from '../components/AnalyticsWidget.astro';

// Initiate requests in parallel without blocking top-level rendering
const userPromise = fetch('https://api.internal/slow-user').then(r => r.json());
---
<html>
  <head><title>Dashboard</title></head>
  <body>
    <!-- <head> and layout stream immediately! -->
    <UserHeader userPromise={userPromise} />
    <!-- Leaf component fetches its own data independently -->
    <AnalyticsWidget />
  </body>
</html>
```

```astro
---
// src/components/UserHeader.astro
const { userPromise } = Astro.props;
const user = await userPromise;
---
<header>Welcome {user.name}</header>
```

## 4. Verification & Audit

Verify streaming behavior and TTFB using `curl` with chunked transfer:

```bash
# -N disables buffering, showing chunks as they arrive from the server
curl -N -v https://localhost:4321/dashboard
# Confirm HTTP/1.1 200 OK with 'Transfer-Encoding: chunked' and early <head> arrival
```
