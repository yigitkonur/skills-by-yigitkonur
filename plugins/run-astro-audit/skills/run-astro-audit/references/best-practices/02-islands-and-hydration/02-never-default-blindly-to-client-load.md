# Never Default Blindly to Client Load

> **Context:** Islands & Hydration | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

`client:load` is a high-priority directive that downloads, parses, and executes island JavaScript immediately upon initial page load, competing directly with critical HTML/CSS parsing and blocking the main thread. Defaulting to `client:load` ruins Total Blocking Time (TBT) and Interaction to Next Paint (INP). Most UI widgets (accordions, tabs, newsletter forms, modal dialogs) do not need immediate sub-millisecond interactivity and should use `client:idle` or `client:visible`.

## 2. How It Differs From Classic React / Next.js

Single-Page Applications and Next.js hydrate every interactive component as soon as bundles finish downloading. Astro grants fine-grained scheduling control. `client:load` should be strictly reserved for critical, above-the-fold interactive elements (e.g. an instant search bar or primary navigation toggle).

## 3. Common Mistakes & Anti-Patterns

Slapping `client:load` on every framework component across the entire page (chat widgets, feedback popups, reviews, tabs) as a habit carried over from React.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/pages/index.astro - Blindly hydrating non-critical widgets on page load
import NewsletterSignup from '../components/NewsletterSignup.jsx';
import ReviewCarousel from '../components/ReviewCarousel.jsx';
import FaqAccordion from '../components/FaqAccordion.jsx';
---
<main>
  <!-- Triggers immediate JS download & main thread blockage on initial paint -->
  <NewsletterSignup client:load />
  <ReviewCarousel client:load />
  <FaqAccordion client:load />
</main>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/pages/index.astro - Scheduling hydration based on priority and visibility
import HeaderNav from '../components/HeaderNav.jsx';
import NewsletterSignup from '../components/NewsletterSignup.jsx';
import ReviewCarousel from '../components/ReviewCarousel.jsx';
import FaqAccordion from '../components/FaqAccordion.jsx';
---
<header>
  <!-- Immediately interactive primary navigation -->
  <HeaderNav client:load />
</header>
<main>
  <!-- Defer until main thread is idle (requestIdleCallback) -->
  <NewsletterSignup client:idle={{ timeout: 500 }} />
  <!-- Defer until scrolled into viewport -->
  <ReviewCarousel client:visible={{ rootMargin: '200px' }} />
  <FaqAccordion client:visible />
</main>
```

## 4. Verification & Audit

Run Lighthouse in Chrome DevTools or CLI and inspect the Performance score and Total Blocking Time:

```bash
npx lighthouse-ci collect --url="http://localhost:4321"
```

Audit the Performance trace for long tasks during initial load. Components not immediately needed above the fold must not execute within the initial `window.onload` window.
