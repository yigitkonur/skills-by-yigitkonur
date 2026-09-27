# Eliminate Total Blocking Time (TBT) and Optimize INP Under 200ms

> **Context:** Performance & Prefetch | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Interaction to Next Paint (INP) measures responsiveness to clicks, taps, and keypresses. While Astro's Zero-JS architecture provides 0ms Total Blocking Time (TBT) by default, loading un-deferred framework islands with `client:load` saturates the main browser thread during initial hydration, causing input delays and failing the 200ms INP threshold.

## 2. How It Differs From Classic React / Next.js

In Next.js, hydration occurs across the entire page hierarchy, making main-thread contention inevitable on complex pages. In Astro's Islands Architecture, each island hydrates independently. Developers can precisely defer hydration using `client:visible` or `client:idle`, ensuring the main thread remains responsive when users interact with the page.

## 3. Common Mistakes & Anti-Patterns

Marking every island with `client:load`, causing all framework bundles to execute simultaneously upon page load.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/pages/pricing.astro
import CurrencySelector from '../components/CurrencySelector.tsx';
import FAQAccordion from '../components/FAQAccordion.tsx';
import ContactForm from '../components/ContactForm.tsx';
---
<!-- Unthrottled hydration blocks the main thread during user interaction -->
<header>
  <CurrencySelector client:load />
</header>
<section>
  <FAQAccordion client:load />
</section>
<footer>
  <ContactForm client:load />
</footer>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/pages/pricing.astro
import CurrencySelector from '../components/CurrencySelector.tsx';
import FAQAccordion from '../components/FAQAccordion.tsx';
import ContactForm from '../components/ContactForm.tsx';
---
<!-- Defer hydration based on user visibility and idle cycles -->
<header>
  <!-- Non-blocking idle hydration for above-the-fold accessory -->
  <CurrencySelector client:idle />
</header>
<section>
  <!-- Hydrates only when scrolled into view -->
  <FAQAccordion client:visible={{ rootMargin: '200px' }} />
</section>
<footer>
  <!-- Hydrates strictly when visible at the bottom -->
  <ContactForm client:visible />
</footer>
```

## 4. Verification & Audit

Run Chrome DevTools Performance Profiler during page load while clicking navigation tabs:

- Verify Long Tasks (>50ms) are eliminated during initial load.
- Confirm INP in DevTools Performance panel is below 200ms under 4x CPU throttling.
