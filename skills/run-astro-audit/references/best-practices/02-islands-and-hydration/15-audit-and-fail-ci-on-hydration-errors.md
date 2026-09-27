# Audit and Fail CI on Hydration Errors With Playwright

> **Context:** Islands & Hydration | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Hydration mismatches are insidious: the browser silently recovers by discarding server HTML and re-rendering on the client. Visual regression tests and standard E2E functional tests (e.g. clicking buttons) still pass, leaving hidden performance degradation, layout shifts, and React console warnings in production. Implementing a Playwright test fixture that monitors the browser console for hydration errors guarantees zero hydration regressions in CI.

## 2. How It Differs From Classic React / Next.js

In Next.js, hydration errors trigger an error overlay in local development. In multi-framework Astro environments, islands use React, Vue, Svelte, or Preact simultaneously, each outputting distinct hydration error strings to the browser console. Automated CI console auditing provides universal protection across all framework integrations.

## 3. Common Mistakes & Anti-Patterns

Relying solely on visual snapshot testing or HTTP status 200 checks, allowing subtle SSR vs client timestamp or locale mismatches to escape into production.

### ❌ Bad Practice / Anti-Pattern

```typescript
// tests/e2e/home.spec.ts - Standard test passes even if hydration failed completely
test('homepage loads successfully', async ({ page }) => {
  await page.goto('/')
  await expect(page.locator('h1')).toBeVisible()
  // Hydration failed in console, but test passes!
})
```

### ✅ Best Practice / Idiomatic

Attach a console listener to assert zero hydration mismatch warnings in Playwright:

```typescript
// tests/fixtures/hydration-test.ts
import { test as base, expect } from '@playwright/test'

export const test = base.extend({
  page: async ({ page }, use) => {
    const hydrationErrors: string[] = []

    page.on('console', (msg) => {
      const text = msg.text()
      if (
        text.includes('Hydration failed') ||
        text.includes('Text content did not match') ||
        text.includes('did not match what was rendered on the server') ||
        text.includes('hydration mismatch')
      ) {
        hydrationErrors.push(text)
      }
    })

    await use(page)

    expect(hydrationErrors, `Hydration errors detected:\n${hydrationErrors.join('\n')}`).toEqual([])
  },
})
```

## 4. Verification & Audit

Run Playwright tests across your staging or preview build:

```bash
npx playwright test tests/e2e/ --reporter=list
```

Confirm that any component introducing a mismatch (e.g. un-hydrated dates or `localStorage` reads) immediately breaks the test suite before merging.
