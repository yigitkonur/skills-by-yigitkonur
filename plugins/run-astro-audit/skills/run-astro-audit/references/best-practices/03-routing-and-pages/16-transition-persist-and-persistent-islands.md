# Persist Audio, Video, and Interactive Islands with transition:persist

> **Context:** Routing & Pages | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

During client-side routing, Astro replaces DOM trees between pages. The `transition:persist` directive instructs the router to lift an existing element or UI island from the outgoing page and preserve it directly into the incoming page, maintaining playback, internal component state, and focus without interruption.

## 2. How It Differs From Classic React / Next.js

In Next.js, state persistence relies on keeping components inside parent `layout.tsx` files. In Astro, persistent elements can exist anywhere on the page, independent of layout hierarchy. By default, `transition:persist` retains state but re-renders the island with incoming new props. To prevent prop re-rendering, Astro provides `transition:persist-props`.

## 3. Common Mistakes & Anti-Patterns

Expecting `transition:persist` to prevent `<iframe>` reloads (browser security models force iframes to reload when moved in the DOM) or expecting CSS keyframe animations to maintain their playback timestamp (CSS animations restart on swap).

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/components/PodcastPlayer.astro
// Missing matching persist identifier across different components
import Player from "./Player.jsx";
---
<!-- If the component tag or location differs across pages without an explicit ID,
     Astro cannot infer matching identity and replaces the element! -->
<Player client:load transition:persist />
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/components/GlobalPlayer.astro
import AudioPlayer from "./AudioPlayer.jsx";

interface Props {
  currentTrackId?: string;
}
const { currentTrackId } = Astro.props;
---
<!-- 1. Explicit ID ensures matching across any route -->
<!-- 2. transition:persist maintains playback state -->
<!-- 3. Omitting persist-props allows trackId prop to update dynamically -->
<AudioPlayer
  client:load
  transition:persist="main-audio-player"
  trackId={currentTrackId}
/>

<!-- In an interactive chat island where props should NOT reset: -->
<ChatWidget
  client:idle
  transition:persist="support-chat"
  transition:persist-props
/>
```

## 4. Verification & Audit

Start audio playback in the browser. Navigate to another page that renders the same persistent player component.
Verify audio plays continuously without a single hitch, stutter, or volume jump.
