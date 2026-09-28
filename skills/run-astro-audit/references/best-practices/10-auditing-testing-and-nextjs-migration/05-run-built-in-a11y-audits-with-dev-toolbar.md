# Run Built-In Accessibility and Performance Checks Using Dev Toolbar Audit App

> **Context:** Auditing & Next.js Migration | **Impact:** Medium | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Catching accessibility (a11y) and performance defects during local development prevents costly regressions before code reaches CI or production. The Astro Dev Toolbar includes a built-in "Audit" app that runs non-intrusively in the browser during `astro dev`. It surfaces missing `alt` attributes on images, improper heading hierarchy order, and broken links, visually highlighting the offending DOM nodes directly on the rendered page with a zero-context-switch workflow.

## 2. How It Differs From Classic React / Next.js

In Next.js, developers typically rely on ESLint plugins (`eslint-plugin-jsx-a11y`) or manual browser extensions (Axe DevTools, Lighthouse). While ESLint catches static JSX defects, it cannot evaluate rendered runtime DOM states, dynamic image props, or slot projections. Astro's Dev Toolbar Audit app inspects the final client-side DOM structure produced after template evaluation and island hydration.

## 3. Common Mistakes & Anti-Patterns

Ignoring the Dev Toolbar notifications or disabling the toolbar globally (`devToolbar: { enabled: false }`) in `astro.config.mjs` removes the fastest developer feedback loop for template-level a11y flaws. Another mistake is treating the Audit app as a complete replacement for comprehensive CI tooling like Pa11y or axe-core.

### ❌ Bad Practice / Anti-Pattern

```js
// astro.config.mjs - Disabling dev toolbar globally hides instant a11y audits
import { defineConfig } from 'astro/config'

export default defineConfig({
  devToolbar: {
    // Completely disables Audit and Inspect apps during development
    enabled: false,
  },
})
```

### ✅ Best Practice / Idiomatic

```js
// astro.config.mjs - Keep devToolbar enabled; configure per-user via preferences
import { defineConfig } from 'astro/config'

export default defineConfig({
  // Dev toolbar remains active for real-time Audit and Inspect feedback
  devToolbar: {
    enabled: true,
  },
})
```

```bash
# Toggle per-user if individual developers prefer disabling without modifying git config
astro preferences disable devToolbar
```

## 4. Verification & Audit

Verify the Audit app's findings against dedicated automated accessibility tools in CI:

```bash
# Pair Dev Toolbar manual audits with automated CI axe tests
npx @axe-core/cli http://localhost:4321 --exit
```
