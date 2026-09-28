# Understand Layout Component Semantics vs Next.js Persistent Trees

> **Context:** Routing & Pages | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Astro layouts are standard `.astro` components that provide common page scaffolding (`<html>`, `<head>`, navigation, and `<slot />`). Understanding that Astro layouts do not act as persistent client component trees prevents subtle bugs when expecting client state (like form inputs or audio playback) to survive navigation automatically.

## 2. How It Differs From Classic React / Next.js

In Next.js App Router, `layout.tsx` wraps sibling pages and persists across client-side route navigations; its React state does not unmount. In Astro, layouts are rendered on the server per page. During navigation, the new page's layout renders anew, and client DOM is replaced unless explicitly opted into persistence via `transition:persist`.

## 3. Common Mistakes & Anti-Patterns

Assuming an interactive search input or audio bar located inside an Astro layout will stay loaded and retain user typed input across navigation without explicit view transition directives.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/layouts/MainLayout.astro
// Assuming search island or player retains state between page changes
import AudioPlayer from '../components/AudioPlayer.jsx';
---
<html>
  <body>
    <header>
      <!-- State will reset on every page navigation! -->
      <AudioPlayer client:load />
    </header>
    <main>
      <slot />
    </main>
  </body>
</html>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/layouts/MainLayout.astro
import { ClientRouter } from "astro:transitions";
import AudioPlayer from '../components/AudioPlayer.jsx';

interface Props {
  title: string;
}
const { title } = Astro.props;
---
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>{title}</title>
    <!-- Enable client-side routing -->
    <ClientRouter />
  </head>
  <body>
    <header>
      <!-- transition:persist keeps the player alive and playing across pages -->
      <AudioPlayer client:load transition:persist="global-audio-player" />
    </header>
    <main>
      <slot />
    </main>
  </body>
</html>
```

## 4. Verification & Audit

Test page transitions in your browser: play audio or type text into a persisted component, then click any link. Verify in DevTools that the element is not remounted and playback continues seamlessly.
