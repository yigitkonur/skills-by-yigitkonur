# Use client:visible With rootMargin for Below-the-Fold Islands

> **Context:** Islands & Hydration | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

`client:visible` uses an `IntersectionObserver` internally to defer downloading and hydrating component JavaScript until the element enters the viewport. However, plain `client:visible` triggers hydration exactly when the component boundary crosses into view. If a user quickly scrolls down, they experience an unresponsive element or a layout shift while the script downloads. By adding `rootMargin: '200px'`, hydration begins smoothly before the user reaches the element.

## 2. How It Differs From Classic React / Next.js

In Next.js, implementing viewport-triggered hydration requires third-party libraries (e.g. `react-intersection-observer` wrapping dynamic imports) or suspense boundaries. Astro natively provides `client:visible={{ rootMargin }}` built into the compiler with zero boilerplate.

## 3. Common Mistakes & Anti-Patterns

Omitting `rootMargin` on complex interactive widgets (e.g. heavy image sliders, map widgets, or complex tab panels), causing visible hydration delay or Cumulative Layout Shift (CLS) on mobile devices.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/components/Testimonials.astro - Late hydration right as element hits viewport
import TestimonialSlider from './TestimonialSlider.jsx';
---
<section class="testimonials">
  <h2>Customer Stories</h2>
  <!-- Hydrates only when 0px away from viewport; user clicks before JS loads -->
  <TestimonialSlider client:visible items={items} />
</section>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/components/Testimonials.astro - Pre-hydrates 200px before viewport entry
import TestimonialSlider from './TestimonialSlider.jsx';
---
<section class="testimonials">
  <h2>Customer Stories</h2>
  <!-- Pre-hydrates 200px in advance, ensuring instant responsiveness upon scroll -->
  <TestimonialSlider client:visible={{ rootMargin: '200px' }} items={items} />
</section>
```

## 4. Verification & Audit

Open Chrome DevTools Network panel, set throttling to "Fast 4G", reload the page at the top, and scroll down smoothly:
Verify that the `TestimonialSlider` chunk request initiates approximately 200px before the component enters the visible viewport area.
