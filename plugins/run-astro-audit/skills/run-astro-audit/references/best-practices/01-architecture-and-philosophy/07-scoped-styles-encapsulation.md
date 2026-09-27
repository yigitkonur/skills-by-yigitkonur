# Rely on Astro Scoped Styles by Default to Prevent Sitewide CSS Cascading Leaks

> **Context:** Architecture & Philosophy | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Astro automatically scopes `<style>` rules inside `.astro` files by compiling selectors with unique data attributes (e.g. `h1[data-astro-cid-xxxx]`). This guarantees that component styles never leak into surrounding elements or child components. Unlike runtime CSS-in-JS libraries, Astro does this at build time with zero JavaScript runtime overhead.

## 2. How It Differs From Classic React / Next.js

React applications frequently use runtime CSS-in-JS libraries (Styled Components, Emotion) which generate dynamic styles on the client and delay First Contentful Paint (FCP). Alternatively, Next.js requires separate `.module.css` files for scoping. Astro encapsulates styles directly within the single `.astro` component file natively.

## 3. Common Mistakes & Anti-Patterns

Using `<style is:global>` indiscriminately for convenient nested styling corrupts global specificity and leaks typography and layout styles to unrelated pages and components.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/components/ArticleCard.astro
// Anti-pattern: Leaking global styles across the entire application
const { title, summary } = Astro.props;
---
<div class="card">
  <h2>{title}</h2>
  <p>{summary}</p>
</div>

<style is:global>
  /* LEAKS: Restyles ALL h2 and p elements across the entire website! */
  h2 { font-size: 1.5rem; color: #1e2038; margin-bottom: 0.5rem; }
  p { line-height: 1.6; color: #6b7280; }
</style>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/components/ArticleCard.astro
// Idiomatic: Scoped styles are automatically isolated to this component
interface Props {
  title: string;
  summary: string;
}
const { title, summary } = Astro.props;
---
<article class="card">
  <h2>{title}</h2>
  <p>{summary}</p>
</article>

<style>
  /* Scoped by default: compiles to h2[data-astro-cid-xxxx] */
  .card {
    border: 1px solid #e5e7eb;
    padding: 1.5rem;
    border-radius: 4px;
  }
  h2 {
    font-size: 1.5rem;
    color: #1e2038;
    margin-bottom: 0.5rem;
  }
  p {
    line-height: 1.6;
    color: #6b7280;
  }
</style>
```

## 4. Verification & Audit

Inspect generated HTML and CSS bundles after build:

```bash
npx astro build
# Verify HTML elements have data-astro-cid attributes and CSS bundle contains scoped selectors:
grep -rn "data-astro-cid" dist/ | head -n 5
# Check that styles are extracted into static .css files in dist/_astro/
```
