# Master the Chronological ClientRouter Lifecycle Events Sequence

> **Context:** Routing & Pages | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Astro's `<ClientRouter />` replaces full-page browser reloads with an orchestrated DOM swap lifecycle. Understanding the exact 5-step sequence allows developers to show progress indicators, carry state between pages, alter DOM trees before render, and initialize scripts reliably without visual glitches.

## 2. How It Differs From Classic React / Next.js

Next.js provides router events (in Pages) or `usePathname` / `useSearchParams` hooks in App Router. Astro dispatches native DOM CustomEvents on the `document` object in strict order:

1. `astro:before-preparation`: Navigation initiated; show progress bars; intercept or wrap `event.loader`.
2. `astro:after-preparation`: HTML fetched and parsed into document object; hide progress bars.
3. `astro:before-swap`: Snapshot taken; inspect/mutate `event.newDocument` before DOM insertion; clean up resources.
4. `astro:after-swap`: DOM replaced and history set; override scroll restore or sync theme classes.
5. `astro:page-load`: Transition complete and new scripts active; run page initialization logic.

## 3. Common Mistakes & Anti-Patterns

Trying to access elements of the incoming page in `astro:before-preparation` (when HTML has not even been fetched yet) or performing teardown work in `astro:page-load` (after the old page is already destroyed).

### ❌ Bad Practice / Anti-Pattern

```javascript
// Trying to access new page elements before preparation completes
document.addEventListener('astro:before-preparation', () => {
  // ERROR: The new page DOM does not exist yet!
  document.querySelector('.new-page-banner').classList.add('visible')
})
```

### ✅ Best Practice / Idiomatic

```javascript
// src/scripts/router-orchestrator.ts
// 1. Show loading indicator
document.addEventListener('astro:before-preparation', () => {
  document.getElementById('nav-spinner')?.classList.add('is-loading')
})

// 2. Hide loading indicator after HTML is fetched and parsed
document.addEventListener('astro:after-preparation', () => {
  document.getElementById('nav-spinner')?.classList.remove('is-loading')
})

// 3. Mutate the incoming document before swap occurs
document.addEventListener('astro:before-swap', (event) => {
  const theme = localStorage.getItem('theme') ?? 'light'
  // Apply theme directly to the incoming document to prevent light flash
  event.newDocument.documentElement.dataset.theme = theme
})

// 4. Adjust scroll immediately after swap
document.addEventListener('astro:after-swap', () => {
  console.log('DOM nodes swapped, scroll restored')
})

// 5. Initialize client widgets after page load
document.addEventListener('astro:page-load', () => {
  console.log('Page ready for interaction')
})
```

## 4. Verification & Audit

Log all lifecycle events in browser console to trace navigation stages:

```javascript
;[
  'astro:before-preparation',
  'astro:after-preparation',
  'astro:before-swap',
  'astro:after-swap',
  'astro:page-load',
].forEach((e) => document.addEventListener(e, () => console.log(`[Lifecycle]: ${e}`)))
```

Verify the events fire in exact sequence on every link click.
