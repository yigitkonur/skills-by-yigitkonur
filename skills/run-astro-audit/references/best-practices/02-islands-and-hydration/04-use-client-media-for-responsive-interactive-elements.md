# Use client:media for Viewport-Specific Interactive Elements

> **Context:** Islands & Hydration | **Impact:** Medium | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Many interactive widgets are only relevant on specific screen sizes (e.g. mobile drawer navigation menus, swipeable touch carousels, or desktop sidebar accordions). Using `client:media="(max-width: 768px)"` ensures that mobile-only component JavaScript is never downloaded or executed on desktop browsers, saving bandwidth and memory.

## 2. How It Differs From Classic React / Next.js

In React/Next.js, conditional rendering based on media queries (e.g. `useMediaQuery()`) still bundles both desktop and mobile component trees into the client bundle, executing JS to determine what not to show. Astro's `client:media` evaluates `window.matchMedia()` at the Astro island boundary _before_ requesting the component script.

## 3. Common Mistakes & Anti-Patterns

Importing a mobile hamburger menu with `client:load` on all devices and hiding it via CSS `display: none` on desktop, forcing desktop users to download unnecessary mobile drawer scripts.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/components/Header.astro - Mobile menu JS downloaded on all screen sizes
import MobileNavDrawer from './MobileNavDrawer.jsx';
---
<header>
  <nav class="desktop-nav">...</nav>
  <!-- Downloaded and hydrated on desktop even though CSS hides it -->
  <div class="block md:hidden">
    <MobileNavDrawer client:load />
  </div>
</header>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/components/Header.astro - Mobile drawer JS downloaded only when media query matches
import MobileNavDrawer from './MobileNavDrawer.jsx';
---
<header>
  <nav class="desktop-nav">...</nav>
  <!-- Zero JS requested on desktop viewports (> 768px) -->
  <MobileNavDrawer client:media="(max-width: 768px)" />
</header>
```

## 4. Verification & Audit

Open Chrome DevTools on a Desktop viewport (e.g. 1440px wide). Clear the Network tab and reload:

```bash
# Verify MobileNavDrawer chunk is NOT requested in Network tab on desktop
```

Resize the browser to mobile viewport (< 768px) or toggle Device Toolbar:
Verify that the `MobileNavDrawer` JavaScript chunk is requested immediately upon crossing the 768px boundary.
