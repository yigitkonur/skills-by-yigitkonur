# Isolate Global Styles and Use the :global() Pseudo-Selector

> **Context:** Performance & Prefetch | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

`<style is:global>` completely opts out of Astro's CSS scoping. Adding `is:global` inside arbitrary leaf components or nested pages leaks styles across the entire application, breaking encapsulation and causing unintended CSS cascade collisions that bloat critical rendering paths.

## 2. How It Differs From Classic React / Next.js

In Next.js, importing a global stylesheet inside a component (`import './style.css'`) throws an error—global CSS is only permitted in `layout.tsx`. In Astro, `is:global` is permitted anywhere, making it easy for undisciplined developers to accidentally pollute the global scope from within reusable components.

## 3. Common Mistakes & Anti-Patterns

Using `<style is:global>` inside a blog post or CMS container component to style rich text, polluting all headings and paragraphs across the site.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/components/ArticleBody.astro
---
<article class="prose-content">
  <slot />
</article>

<!-- LEAK: Unscoped is:global styles all h2 and p tags across the entire site! -->
<style is:global>
  h2 {
    font-size: 2rem;
    color: #e11d48;
  }
  p {
    line-height: 1.8;
  }
</style>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/components/ArticleBody.astro
---
<article class="prose-content">
  <slot />
</article>

<!-- SCOPED: Uses :global() nested within the scoped component root -->
<style>
  .prose-content :global(h2) {
    font-size: 2rem;
    color: #e11d48;
  }
  .prose-content :global(p) {
    line-height: 1.8;
  }
</style>
```

## 4. Verification & Audit

Audit your components for unauthorized `<style is:global>` usages outside root layouts:

```bash
grep -rn '<style is:global>' src/components/
```

Ensure any component styling dynamic child slots strictly prefixes rules with a scoped parent selector and `:global(...)`.
