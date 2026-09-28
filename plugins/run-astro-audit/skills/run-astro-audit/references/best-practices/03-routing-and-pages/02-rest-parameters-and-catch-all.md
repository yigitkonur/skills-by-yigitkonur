# Use Rest Parameters For Multi-Level Catch-All Routes

> **Context:** Routing & Pages | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

When creating documentation sites, CMS hierarchies, or nested taxonomies, URLs have variable segment depths (e.g. `/docs/quickstart`, `/docs/deep/nested/page`). Rest parameters (`[...path].astro`) capture arbitrary segments into a single parameter string. Returning `{ params: { path: undefined } }` allows the rest parameter route to match the parent/root page without requiring a separate `index.astro`.

## 2. How It Differs From Classic React / Next.js

In Next.js App Router, optional catch-all routes require double brackets `[[...slug]]/page.tsx` to match the root route. In Astro, rest parameters use single triple-dots (`[...slug].astro`). You match the root URL by explicitly setting `slug: undefined` in `getStaticPaths()`.

## 3. Common Mistakes & Anti-Patterns

Using empty string `""` or `"/"` instead of `undefined` in `getStaticPaths()` causes invalid routing paths or build failures. Another trap in SSR is using multiple rest parameters in a single file path (e.g. `[...a]/[...b].astro`), which Astro strictly rejects because route resolution becomes ambiguous.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/pages/docs/[...slug].astro
export async function getStaticPaths() {
  return [
    // BAD: Passing empty string or slash fails to match root properly
    { params: { slug: "" }, props: { title: "Docs Root" } },
    { params: { slug: "/getting-started" }, props: { title: "Start" } },
  ];
}
const { slug } = Astro.params;
---
<h1>Path: {slug}</h1>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/pages/docs/[...slug].astro
import type { GetStaticPaths } from "astro";

export const getStaticPaths = (async () => {
  return [
    // Setting rest param to undefined matches the root "/docs"
    { params: { slug: undefined }, props: { title: "Documentation Overview" } },
    { params: { slug: "guides/install" }, props: { title: "Installation Guide" } },
    { params: { slug: "api/v2/client" }, props: { title: "API Reference" } },
  ];
}) satisfies GetStaticPaths;

const { slug } = Astro.params;
const { title } = Astro.props;
---
<article>
  <h1>{title}</h1>
  <p>Current segment: {slug ?? "(root)"}</p>
</article>
```

## 4. Verification & Audit

Verify that the root path and subpaths build correctly without 404s:

```bash
pnpm astro build && ls -la dist/docs/index.html dist/docs/guides/install/index.html
```

Test with curl or browser to confirm that both `/docs` and `/docs/guides/install` serve status `200`.
