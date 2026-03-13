# Testing Strategy: Vue-to-Next.js Migration

> Ensuring behavioral parity at every phase of migration — test the contract, not the framework.

---

## 1. Migration Testing Philosophy

Migration testing exists to answer one question: **does the migrated component behave identically to the original?**

**Core principles:**

- **Test behavioral parity, not implementation details.** A Vue component using `v-model` and a React component using `useState` + `onChange` are equivalent if they produce the same DOM and respond to the same interactions.
- **Test the contract, not the framework internals.** Never assert on Vue reactivity internals or React fiber nodes. Assert on what the user sees and what the network receives.
- **Dual-framework period requires both test libraries.** During coexistence, Vue Test Utils validates the legacy baseline, React Testing Library validates the migrated version. Both must pass for the same behavioral spec.
- **Tests are the migration's safety net, not its deliverable.** Write the minimum tests that catch regressions. Over-testing slows migration velocity without reducing risk.

---

## 2. Testing Ladder

Four levels, ordered from most granular (fastest feedback) to broadest (highest confidence):

| Level | Tool | What It Validates | When to Use |
|---|---|---|---|
| Component parity | React Testing Library + Vue Test Utils | Same DOM output, same interaction results | Every migrated component |
| Visual regression | Chromatic / Percy / Playwright screenshots | CSS drift between Vue `scoped` styles and React CSS Modules | Every styling change |
| Route-level E2E | Playwright / Cypress | Navigation, auth redirects, data freshness across Vue↔Next boundary | Every migrated route |
| Performance baseline | Lighthouse CI / Web Vitals | TTFB, LCP, CLS not regressed | After shell setup + each phase |

**Rule of thumb:** if a component parity test catches it, don't write an E2E for it. Push failures down the ladder.

---

## 3. Component Parity Testing

### Side-by-Side Pattern

The core technique: render the Vue component and the React component with **identical props/state**, then assert **identical DOM output and interaction behavior**.

#### Vue baseline (Vue Test Utils)

```js
// tests/vue/Button.spec.js
import { mount } from '@vue/test-utils';
import Button from '@/components/Button.vue';

describe('Button (Vue baseline)', () => {
  it('renders label and fires click', async () => {
    const onClick = vi.fn();
    const wrapper = mount(Button, {
      props: { label: 'Submit', disabled: false },
      attrs: { onClick },
    });

    expect(wrapper.text()).toBe('Submit');
    expect(wrapper.find('button').attributes('disabled')).toBeUndefined();

    await wrapper.find('button').trigger('click');
    expect(onClick).toHaveBeenCalledOnce();
  });
});
```

#### React migrated (React Testing Library)

```tsx
// tests/react/Button.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Button } from '@/components/Button';

describe('Button (React migrated)', () => {
  it('renders label and fires click', async () => {
    const onClick = vi.fn();
    render(<Button label="Submit" disabled={false} onClick={onClick} />);

    expect(screen.getByRole('button', { name: 'Submit' })).toBeEnabled();

    await userEvent.click(screen.getByRole('button'));
    expect(onClick).toHaveBeenCalledOnce();
  });
});
```

### Key Mapping Patterns to Test

| Vue Pattern | React Equivalent | What to Assert |
|---|---|---|
| `<slot>` / `<slot name="x">` | `children` / named props | Same rendered content in same position |
| `$emit('change', value)` | `onChange(value)` callback | Callback called with identical arguments |
| `v-model` | Controlled input (`value` + `onChange`) | Typing produces same value, caret position preserved |
| `v-if` / `v-show` | Conditional render / `style.display` | Element present/absent or visible/hidden identically |
| `provide` / `inject` | React Context | Descendant components receive same values |

---

## 4. Visual Regression Testing

### Why It Matters

CSS scoped styles → CSS Modules drift is the **#1 silent regression** in Vue-to-React migrations. The component passes all behavioral tests but looks subtly wrong because:

- Class name specificity changed
- CSS property order shifted
- A global style leak was accidentally relied upon

### Tool Options

| Tool | Strength | Tradeoff |
|---|---|---|
| Chromatic | Tight Storybook integration, free for OSS | Requires Storybook for both frameworks |
| Percy | Framework-agnostic snapshot service | Per-snapshot pricing |
| Playwright screenshots | Free, runs in CI, no vendor lock | Manual threshold tuning, no visual diffing UI |

### Setup Pattern: Dual Storybook

Maintain Storybook for both Vue and React with identical stories during migration. Run visual comparison between Vue and React story screenshots — any pixel diff beyond threshold is a regression.

### CSS Ordering Warning

Next.js dev mode and production builds can load CSS in **different orders**. Always verify visual regression against `next build && next start`, not `next dev`. Add this to CI:

```yaml
- run: npm run build
- run: npx start-server-and-test 'npm start' 3000 'npx playwright test --project=visual'
```

---

## 5. Verification Checklist Per Migrated Unit

Run this checklist for **every** migrated component before marking it done:

### Rendering
- [ ] DOM structure matches (same semantic elements, same nesting)
- [ ] Empty state renders identically
- [ ] Loading state renders identically
- [ ] Error state renders identically
- [ ] List rendering with 0, 1, and many items

### Interactions
- [ ] Click handlers fire with correct arguments
- [ ] Keyboard input produces correct state changes
- [ ] Focus management (tab order, focus traps) preserved
- [ ] Hover/active states visually consistent

### Accessibility
- [ ] Label associations (`for`/`id`, `aria-labelledby`) preserved
- [ ] ARIA attributes (`aria-expanded`, `aria-selected`, etc.) identical
- [ ] Keyboard navigation works (Enter, Escape, Arrow keys)
- [ ] Screen reader announcements unchanged (live regions)

### Network
- [ ] Correct number of API requests (no duplicate fetches)
- [ ] Request timing matches (on mount, on interaction, on interval)
- [ ] Cache behavior preserved (stale-while-revalidate, dedup)
- [ ] Error/retry handling produces same UX

### SSR
- [ ] No `window`/`document` usage in Server Components
- [ ] Hydration completes without mismatch warnings
- [ ] `'use client'` boundary placed at correct level
- [ ] Meta tags and SEO output identical (check `view-source:`)

### State
- [ ] Controlled input parity: caret position, selection range
- [ ] IME composition (CJK input) handled correctly
- [ ] Debounced/throttled values fire at same intervals
- [ ] Form submission produces identical payloads

---

## 6. E2E Cross-Boundary Testing

### The Vue↔Next Boundary Problem

During coexistence, users navigate between Next.js pages and proxied Vue pages. The boundary must be invisible. Test it explicitly.

### Playwright Example: Cross-Boundary Navigation

```ts
// e2e/cross-boundary.spec.ts
import { test, expect } from '@playwright/test';

test('navigate from Next route to Vue route and back', async ({ page }) => {
  // Start on a migrated Next.js page
  await page.goto('/dashboard');
  await expect(page.locator('h1')).toHaveText('Dashboard');

  // Navigate to a not-yet-migrated Vue page (proxied)
  await page.click('a[href="/settings/billing"]');
  await expect(page).toHaveURL('/settings/billing');
  await expect(page.locator('.billing-header')).toBeVisible();

  // Navigate back to Next.js
  await page.click('a[href="/dashboard"]');
  await expect(page).toHaveURL('/dashboard');
  await expect(page.locator('h1')).toHaveText('Dashboard');
});

test('auth redirect parity: expired session redirects to login', async ({ page }) => {
  // Clear auth state
  await page.context().clearCookies();

  // Next.js protected route should redirect
  await page.goto('/dashboard');
  await expect(page).toHaveURL(/\/login/);

  // Vue protected route should redirect identically
  await page.goto('/settings/billing');
  await expect(page).toHaveURL(/\/login/);
});

test('deep link parity: direct navigation to nested route', async ({ page }) => {
  await page.goto('/settings/billing/invoices/2024');
  await expect(page.locator('[data-testid="invoice-year"]')).toHaveText('2024');
});
```

### What to Test at the Boundary

| Scenario | Assertion |
|---|---|
| Forward navigation (Next → Vue) | URL correct, content loads, no flash of wrong layout |
| Back navigation (Vue → Next) | Browser back button works, no full page reload |
| Auth redirects | Both frameworks redirect to same login URL with same `returnTo` param |
| Deep links | Direct URL entry resolves correctly on both sides |
| Shared state | Auth token, theme preference, locale survive boundary crossing |

---

## 7. CI Pipeline for Dual-Framework Testing

```yaml
# .github/workflows/migration-tests.yml
jobs:
  vue-tests:
    runs-on: ubuntu-latest
    steps: [checkout, npm ci, npm run test:vue]

  react-tests:
    runs-on: ubuntu-latest
    steps: [checkout, npm ci, npm run test:react]

  e2e-cross-boundary:
    needs: [vue-tests, react-tests]
    steps: [checkout, npm ci, playwright install, npm run build, playwright test]

  performance:
    needs: [e2e-cross-boundary]
    steps: [checkout, npm ci, npm run build, lighthouse-ci-action]

  visual-regression:
    needs: [vue-tests, react-tests]
    steps: [checkout, npm ci, playwright test --project=visual-regression]
```

### Pipeline Gates

| Gate | Threshold | Action on Failure |
|---|---|---|
| Vue tests | 100% pass | Block merge |
| React tests | 100% pass | Block merge |
| E2E cross-boundary | 100% pass | Block merge |
| LCP regression | > 200ms increase | Warn, require justification |
| CLS regression | > 0.05 increase | Block merge |
| Visual diff | > 0.1% pixel change | Require manual approval |

---

## 8. Testing Phases Aligned to Migration

| Migration Phase | Testing Focus | Key Risks |
|---|---|---|
| **Shell setup** | URL parity (every route resolves), SEO parity (`view-source:` comparison), performance baseline capture | Proxy misconfiguration, missing meta tags |
| **Leaf components** | Component parity tests, visual regression snapshots | CSS drift, slot→children mapping errors |
| **Stateful components** | Effect parity (no duplicate API calls in Strict Mode), controlled input parity, timer/interval cleanup | `useEffect` double-fire, stale closures |
| **Routes/pages** | Deep link parity, route guard parity, cache invalidation on navigation | Auth redirect loops, layout shift on transition |
| **Decommission** | Full E2E suite (no more cross-boundary), comprehensive performance audit, remove Vue test infrastructure | Orphaned Vue dependencies, missed proxy routes |

### Phase Transition Criteria

A phase is complete when all parity tests pass, visual regression shows zero unintended diffs, E2E covers all migrated routes, performance gates pass, and no `TODO(migration)` comments remain.

---

## Quick Reference: Test Commands

```bash
npm run test:vue                # Vue baseline tests
npm run test:react              # React migrated tests
npm run test:vue & npm run test:react & wait  # Both in parallel
npm run build && npx start-server-and-test 'npm start' 3000 'npx playwright test'  # E2E
npm run build && npx lhci autorun  # Performance audit
```
