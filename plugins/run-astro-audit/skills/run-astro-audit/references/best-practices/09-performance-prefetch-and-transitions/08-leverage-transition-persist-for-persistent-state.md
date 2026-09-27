# Leverage transition:persist for Persistent Media and Island State

> **Context:** Performance & Prefetch | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

During View Transitions, Astro destroys old DOM nodes and replaces them with incoming page HTML. For audio/video players, map canvas elements, and complex interactive islands (such as a floating support chat or audio player), destroying and re-creating elements causes audio stutters, video resets, and hydration performance overhead. `transition:persist` retains the live DOM node across navigations.

## 2. How It Differs From Classic React / Next.js

In Next.js, persistent UI requires nested layout hierarchies (`layout.tsx`). If an element is located outside the shared layout, it unmounts. In Astro, `transition:persist` allows any element or island anywhere in the DOM tree to seamlessly persist between pages as long as a matching transition identifier exists.

## 3. Common Mistakes & Anti-Patterns

Re-mounting media players or complex islands on every page transition, causing flash of unstyled content (FOUC), audio dropouts, and redundant re-hydration.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/components/PodcastPlayer.astro
// Re-hydrates from scratch on every page navigation
import AudioIsland from './AudioIsland.tsx';
---
<div class="fixed bottom-0 w-full bg-slate-900">
  <AudioIsland client:load />
</div>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/components/PodcastPlayer.astro
// transition:persist keeps the DOM node and island state alive
import AudioIsland from './AudioIsland.tsx';
---
<div class="fixed bottom-0 w-full bg-slate-900">
  <AudioIsland
    client:load
    transition:persist="podcast-audio"
    transition:persist-props
  />
</div>
```

## 4. Verification & Audit

Verify that persistent islands maintain playback during client navigation:

1. Start audio or video playback in your persistent player.
2. Click an internal link to navigate to a sibling page.
3. Verify via DevTools Media tab that audio playback never stops and the HTML audio element's `currentTime` continues incrementing smoothly without re-initialization.
