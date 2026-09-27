# Enforce Zero-Runtime Component-Scoped CSS Architecture

> **Context:** Performance & Prefetch | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Astro automatically scopes `<style>` tags at build time by appending unique hash attributes (`data-astro-cid-[hash]`) to DOM elements and CSS selectors. Unlike runtime CSS-in-JS solutions (Emotion, Styled-Components), Astro generates pure, static CSS files with zero client-side JavaScript execution overhead, eliminating hydration delays and runtime style re-calculation.

## 2. How It Differs From Classic React / Next.js

In React/Next.js, styling frequently relies on CSS Modules (`styles.module.css`), inline styles, or runtime CSS-in-JS that serializes style rules into `<head>` on the client. In Astro, regular `<style>` blocks in `.astro` files are scoped by default without modules, classes mangling, or JavaScript footprint.

## 3. Common Mistakes & Anti-Patterns

Importing heavy runtime CSS-in-JS libraries or avoiding Astro `<style>` blocks under the false belief that scoped styling requires external `.module.css` files.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/components/HeroBanner.astro
// Bringing heavy CSS-in-JS into an Astro component adds client JS payload
import styled from 'styled-components'; // Anti-pattern: runtime style engine
---
<!-- Unscoped class or external library overhead -->
<div class="hero-wrapper">
  <h1>Welcome to the Platform</h1>
</div>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/components/HeroBanner.astro
---
<div class="hero">
  <h1>Welcome to the Platform</h1>
  <p>Performant, statically compiled styles.</p>
</div>

<!-- Scoped at build time to [data-astro-cid-*] with zero runtime JS -->
<style>
  .hero {
    padding: 4rem 2rem;
    background: #0f172a;
  }
  h1 {
    font-size: 2.5rem;
    color: #f8fafc;
  }
</style>
```

## 4. Verification & Audit

Run build and inspect emitted HTML to verify static `data-astro-cid-*` scoping without client JS style engines:

```bash
pnpm astro build && grep -rn 'data-astro-cid' dist/
```

In DevTools Elements panel, inspect the rendered component to confirm low-specificity, attribute-scoped CSS selectors (`.hero[data-astro-cid-...]`).
