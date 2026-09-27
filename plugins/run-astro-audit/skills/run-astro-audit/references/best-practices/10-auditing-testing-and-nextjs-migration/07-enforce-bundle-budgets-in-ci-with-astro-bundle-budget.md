# Enforce Automated Asset Size Budgets at Build Time Using Astro Bundle Budget

> **Context:** Auditing & Next.js Migration | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Performance regressions on web projects often happen incrementally: a developer installs an icon library, date formatter, or charting package into a client island, silently bloating client bundles from 20 KB to 250 KB. Enforcing automated bundle size budgets at build time via `@shiftescape/astro-bundle-budget` fails the CI build as soon as emitted JavaScript or CSS assets exceed specified byte thresholds, preventing bundle regressions before deployment.

## 2. How It Differs From Classic React / Next.js

In Next.js, bundle budgets typically require standalone Webpack configuration or external GitHub Actions (`size-limit`, `bundlewatch`). Because Next.js mixes server and client code in monolithic chunks, setting clean boundaries on pure static routes is notoriously difficult. In Astro, the build output is strictly separated; bundle budget integrations inspect the final `dist/` assets during the `astro:build:done` lifecycle hook.

## 3. Common Mistakes & Anti-Patterns

Relying on manual code reviews to catch heavy dependencies. Without automated budget enforcement, an accidental import of `moment.js` or `lodash` inside a client island slips past code review and compromises mobile Core Web Vitals.

### ❌ Bad Practice / Anti-Pattern

```js
// astro.config.mjs - No bundle budgets; build succeeds even with 500KB JS payloads
import { defineConfig } from 'astro/config'
import react from '@astrojs/react'

export default defineConfig({
  integrations: [react()],
  // Zero build-time budget enforcement
})
```

### ✅ Best Practice / Idiomatic

```js
// astro.config.mjs - Enforce strict JS and CSS thresholds during build
import { defineConfig } from 'astro/config'
import react from '@astrojs/react'
import bundleBudget from '@shiftescape/astro-bundle-budget'

export default defineConfig({
  integrations: [
    react(),
    bundleBudget({
      budgets: [
        { type: 'js', budget: 100 }, // Fail build if total client JS exceeds 100KB
        { type: 'css', budget: 50 }, // Fail build if total CSS exceeds 50KB
      ],
    }),
  ],
})
```

## 4. Verification & Audit

Simulate budget enforcement during CI build:

```bash
# Run build; if assets exceed configured thresholds, process exits with code 1
pnpm build
# Output on violation: "[astro-bundle-budget] ERROR: JS budget exceeded (118KB > 100KB)"
```
