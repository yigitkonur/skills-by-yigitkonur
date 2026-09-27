# Prevent Cumulative Layout Shift (CLS) Across Media and Islands

> **Context:** Performance & Prefetch | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Cumulative Layout Shift (CLS) measures visual stability. A score > 0.1 disrupts user reading and causes accidental clicks. In Astro sites, CLS spikes occur when: (1) images or video elements lack explicit aspect ratio dimensions, (2) hydrated framework islands pop into the DOM asynchronously without reserved space, or (3) web fonts swap without metric-matched fallbacks.

## 2. How It Differs From Classic React / Next.js

In Next.js, `<Image>` enforces width/height constraints to calculate layout boxes automatically. In Astro, while `astro:assets` `<Image />` generates dimensions, standard `<img>` tags and client islands require explicit dimension reservation in markup to avoid sudden DOM shifts when scripts settle.

## 3. Common Mistakes & Anti-Patterns

Rendering unconstrained media elements or unreserved island containers that expand when hydrated.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/components/DynamicFeed.astro
import FeedIsland from './FeedIsland.tsx';
---
<div class="feed-container">
  <!-- Missing width/height causes layout push when image loads -->
  <img src="/banner.webp" alt="Promo banner" />

  <!-- Zero reserved height: Expands by 400px when island mounts, shifting content down -->
  <FeedIsland client:visible />
</div>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/components/DynamicFeed.astro
import FeedIsland from './FeedIsland.tsx';
---
<div class="feed-container">
  <!-- Explicit dimensions allow browser to calculate aspect ratio instantly -->
  <img
    src="/banner.webp"
    alt="Promo banner"
    width="1200"
    height="400"
    class="w-full h-auto aspect-[3/1]"
  />

  <!-- Reserved min-height skeleton wrapper prevents island mounting shift -->
  <div class="min-h-[400px] w-full">
    <FeedIsland client:visible />
  </div>
</div>
```

## 4. Verification & Audit

Run automated layout shift detection in DevTools:

1. Open DevTools -> **Rendering** tab -> check "Layout Shift Regions" (visualized in blue).
2. Reload and scroll the page. Confirm no blue layout shift rectangles trigger during media load or island hydration. Target: CLS < 0.05.
