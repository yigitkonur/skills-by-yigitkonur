# Master Named Slots, Fallback Content, and Slot Forwarding

> **Context:** Routing & Pages | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Astro uses standard web component slot semantics (`<slot />`, `<slot name="..." />`) rather than React `children` props. Named slots enable multi-zone layouts (e.g. injecting meta tags into `<head>`, action buttons into navbars, and structured articles into `<main>`) with fallback defaults when children are omitted.

## 2. How It Differs From Classic React / Next.js

In React, multi-zone content is passed as object props (`header={<Header />} footer={<Footer />}`). In Astro, you pass child elements marked with `slot="name"`. Named slots must be direct children of the component (or wrapped in `<Fragment slot="name">`). To forward a named slot through nested layouts, both `name` and `slot` attributes must be specified: `<slot name="head" slot="head" />`.

## 3. Common Mistakes & Anti-Patterns

Placing `slot="name"` on deeply nested elements rather than immediate children of the layout component, or expecting slot fallback content to render when an empty slot tag or empty whitespace is passed.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/layouts/BadWrapper.astro
---
<div>
  <!-- Nested layouts without slot forwarding lose the named slot content -->
  <slot name="custom-meta" />
  <slot />
</div>

// src/pages/post.astro
// BAD: slot="custom-meta" is inside a nested div, not an immediate child!
<BadWrapper>
  <div>
    <meta name="author" content="Alex" slot="custom-meta" />
  </div>
  <h1>Title</h1>
</BadWrapper>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/layouts/BaseLayout.astro
---
<html lang="en">
  <head>
    <slot name="head-meta">
      <!-- Fallback content renders ONLY if parent provides no head-meta slot -->
      <meta name="robots" content="index, follow" />
    </slot>
  </head>
  <body>
    <slot />
  </body>
</html>
```

```astro
---
// src/layouts/BlogLayout.astro (Slot Forwarding Pattern)
import BaseLayout from "./BaseLayout.astro";
---
<BaseLayout>
  <!-- Transfer named slot through intermediate layout -->
  <slot name="head-meta" slot="head-meta" />
  <article>
    <slot />
  </article>
</BaseLayout>
```

## 4. Verification & Audit

Inspect the built HTML in `dist/` or inspect browser elements:

```bash
grep -n "<meta name=\"robots\"" dist/index.html
```

Verify that the fallback renders when no slot is provided, and that custom forwarded slots correctly inject content into their intended layout placeholder.
