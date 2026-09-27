# Use Native Web Components and Bundled Scripts Over Heavy UI Frameworks

> **Context:** Architecture & Philosophy | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Astro’s `<script>` tags are first-class primitives. They support TypeScript, npm imports, bundling, and automatic deduplication across component instances. Using native Custom Elements (`HTMLElement`) for simple UI widgets (menus, accordions, dialogs) provides full interactivity while shipping zero framework runtime overhead (saving 45KB+ per page).

## 2. How It Differs From Classic React / Next.js

In Next.js, even trivial interactive widgets (such as a dropdown or theme toggle) require a `"use client"` React component with `useState`, forcing the browser to load and execute the React runtime before the button becomes responsive. Astro uses browser-native Custom Elements that become interactive instantly without virtual DOM diffing.

## 3. Common Mistakes & Anti-Patterns

Importing React and `@radix-ui` or similar UI libraries just to create a simple mobile hamburger toggle introduces immense JS bundle bloat for a few lines of class-toggling logic.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/components/MobileMenu.astro
// Anti-pattern: Hydrating React for a simple class toggle
import ReactNavDrawer from './react/ReactNavDrawer.jsx';
---
<!-- Ships React + React-DOM runtime (~45KB gzip) just to toggle 'open' class -->
<ReactNavDrawer client:load />
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/components/MobileMenu.astro
// Idiomatic: Native Custom Element in pure Astro (0 KB framework runtime)
---
<nav-drawer>
  <button type="button" aria-expanded="false" aria-controls="mobile-nav">
    <span class="sr-only">Toggle navigation</span>
    <span class="icon">☰</span>
  </button>
  <nav id="mobile-nav" hidden>
    <a href="/services">Services</a>
    <a href="/about">About</a>
  </nav>
</nav-drawer>

<script>
  // Bundled, type-safe, and executed once per page regardless of instance count
  class NavDrawer extends HTMLElement {
    connectedCallback() {
      const btn = this.querySelector('button');
      const menu = this.querySelector('#mobile-nav');
      btn?.addEventListener('click', () => {
        const expanded = btn.getAttribute('aria-expanded') === 'true';
        btn.setAttribute('aria-expanded', String(!expanded));
        if (menu) menu.hidden = expanded;
      });
    }
  }
  customElements.define('nav-drawer', NavDrawer);
</script>
```

## 4. Verification & Audit

Audit bundle size in build output:

```bash
npx astro build
# Verify that the emitted script chunk for the custom element is under 1KB:
ls -lh dist/_astro/*.js
```
