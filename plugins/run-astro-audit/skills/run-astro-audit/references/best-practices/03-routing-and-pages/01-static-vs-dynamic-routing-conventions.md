# Use Explicit File-Based Route Segments and Decode Dynamic Params

> **Context:** Routing & Pages | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Astro uses a file-based routing system where files in `src/pages/` automatically become URL endpoints. Dynamic routes (`[param].astro`) generate multiple pages at build time in SSG mode. Astro passes URL parameters as raw, un-decoded strings. Explicit parameter names avoid route collisions and ensure predictable static build generation.

## 2. How It Differs From Classic React / Next.js

In Next.js App Router, routes are folders with a `page.tsx` (`app/blog/[slug]/page.tsx`), and dynamic params are automatically URL-decoded in the `params` promise. In Astro, any `.astro`, `.md`, or `.mdx` file in `src/pages/` directly defines the route file (`src/pages/blog/[slug].astro`), and `Astro.params` values are **not** URL-decoded by default. You must invoke `decodeURI()` explicitly when handling special characters.

## 3. Common Mistakes & Anti-Patterns

Developers migrating from Next.js often assume parameters are pre-decoded or try to create dynamic routes in SSG mode without exporting `getStaticPaths()`. Additionally, omitting `[slug].astro` in favor of client-side hash routing breaks SEO and static asset pre-rendering.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/pages/tags/[tag].astro (SSG Mode)
// Missing getStaticPaths() causes build error:
// "getStaticPaths() function is required for dynamic routes."
const { tag } = Astro.params;
// Assumes tag is already decoded ("c%2B%2B" instead of "c++")
const posts = await getPostsByTag(tag);
---
<h1>Tag: {tag}</h1>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/pages/tags/[tag].astro
import type { GetStaticPaths } from "astro";

export const getStaticPaths = (() => {
  return [
    { params: { tag: "astro" } },
    { params: { tag: "javascript" } },
    { params: { tag: encodeURIComponent("c++") } },
  ];
}) satisfies GetStaticPaths;

const { tag } = Astro.params;
// Explicitly decode param if it may contain encoded characters
const decodedTag = tag ? decodeURI(tag) : "";
---
<h1>Tag: {decodedTag}</h1>
```

## 4. Verification & Audit

Run the production build check to ensure all dynamic routes export valid static paths:

```bash
pnpm astro build
```

Verify that the output directory contains the generated static HTML files matching your parameter matrix (e.g. `dist/tags/astro/index.html`).
