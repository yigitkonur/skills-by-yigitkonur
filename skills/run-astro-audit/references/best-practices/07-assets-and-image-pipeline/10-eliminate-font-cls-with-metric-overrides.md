# Eradicate Font CLS with size-adjust and Metric Overrides

> **Context:** Assets & Image Pipeline | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

When custom web fonts load with `font-display: swap`, the browser initially renders text using a local system fallback (e.g. Arial or Times New Roman). When the custom font file finishes loading, the browser swaps fonts. Because system and web fonts differ in glyph widths, x-heights, and bounding boxes, the entire page reflows, causing severe Cumulative Layout Shift (CLS). Using font metric overrides (`size-adjust`, `ascent-override`, `descent-override`) forces the fallback font to occupy the exact bounding box of the web font.

## 2. How It Differs From Classic React / Next.js

Next.js `next/font` automatically computes font metric overrides and injects `@font-face` rules for fallback fonts behind the scenes. In Astro, Astro 5+ native fonts configuration automatically computes optimized fallbacks (`fallbacks: ["sans-serif"]`), while standard CSS setups configure Capsize or `@font-face` overrides directly in stylesheets.

## 3. Common Mistakes & Anti-Patterns

Using a bare system fallback list (e.g. `font-family: 'Inter', sans-serif`) with `font-display: swap`. When Inter swaps in over default system Arial, paragraphs shift by several vertical pixels, spiking CLS.

### ❌ Bad Practice / Anti-Pattern

Unadjusted system fallback font causes jarring layout shifts upon font arrival:

```css
/* ❌ Anti-Pattern: Uncalibrated system Arial triggers layout shift on swap */
@font-face {
  font-family: 'BrandSans';
  src: url('/fonts/BrandSans.woff2') format('woff2');
  font-display: swap;
}

body {
  font-family: 'BrandSans', Arial, sans-serif;
}
```

### ✅ Best Practice / Idiomatic

Define a metric-adjusted `@font-face` fallback matching the custom font's exact bounding box:

```css
/* ✅ Calibrated fallback font matches BrandSans line-height and letter-spacing */
@font-face {
  font-family: 'BrandSans-Fallback';
  src: local('Arial');
  ascent-override: 90.5%;
  descent-override: 22.4%;
  line-gap-override: 0%;
  size-adjust: 107.5%;
}

@font-face {
  font-family: 'BrandSans';
  src: url('/fonts/BrandSans.woff2') format('woff2');
  font-display: swap;
}

body {
  font-family: 'BrandSans', 'BrandSans-Fallback', sans-serif;
}
```

## 4. Verification & Audit

Throttle network to Slow 3G in Chrome DevTools Performance panel: verify the Layout Shift trace records 0 shifts during the web font swap event.
