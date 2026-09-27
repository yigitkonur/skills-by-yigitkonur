# Unit Test `.astro` Components Headlessly With the Astro Container API

> **Context:** Auditing, Testing & Next.js Migration | **Impact:** High | **Target:** Astro 4.9+ / Astro 5

## 1. Why We Do This

Historically, testing `.astro` components required slow end-to-end browser runners (Playwright/Cypress) because `.astro` files compile to server render functions rather than Virtual DOM nodes, making them incompatible with React Testing Library and JSDOM. The official Astro Container API (`experimental_AstroContainer` from `astro/container`) enables fast, isolated unit testing directly inside Vitest. It supports passing props, default and named slots, and request contexts headlessly at microsecond speeds.

## 2. How It Differs From Classic React / Next.js

React unit tests mount Virtual DOM trees using `@testing-library/react`. Astro components produce raw HTML strings via server-side execution. The Container API exposes this pipeline directly to unit test runners without launching an HTTP server or browser.

## 3. Common Mistakes & Anti-Patterns

Spinning up a full browser instance or local dev server just to test basic prop rendering, conditional CSS classes, and slot fallbacks in `.astro` components.

### ❌ Bad Practice / Anti-Pattern

```typescript
// tests/e2e/card.spec.ts (Overkill for a simple presentational unit test)
import { test, expect } from '@playwright/test'

test('renders card title and slots', async ({ page }) => {
  // Heavy: Requires compiling full app, starting HTTP server, and launching Chromium!
  await page.goto('/card-preview')
  await expect(page.locator('.card-title')).toHaveText('Enterprise SEO')
})
```

### ✅ Best Practice / Idiomatic

```typescript
// src/components/__tests__/Card.test.ts
import { experimental_AstroContainer as AstroContainer } from 'astro/container'
import { describe, it, expect } from 'vitest'
import Card from '../Card.astro'

describe('Card.astro Unit Test', () => {
  it('renders title and slot contents correctly', async () => {
    const container = await AstroContainer.create()
    const html = await container.renderToString(Card, {
      props: { title: 'Enterprise SEO', variant: 'highlight' },
      slots: { default: '<p>Comprehensive organic growth strategy.</p>' },
    })

    expect(html).toContain('Enterprise SEO')
    expect(html).toContain('highlight')
    expect(html).toContain('Comprehensive organic growth strategy.')
  })
})
```

## 4. Verification & Audit

Configure Vitest with `getViteConfig()` from `astro/config` and run the component test suite:

```bash
npx vitest run src/components/__tests__/Card.test.ts
# Must pass in under 500ms without starting a web server or Chromium instance
```
