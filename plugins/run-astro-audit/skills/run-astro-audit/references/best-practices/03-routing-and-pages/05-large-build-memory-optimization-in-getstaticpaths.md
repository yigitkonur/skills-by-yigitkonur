# Optimize Memory in getStaticPaths for High-Scale Static Builds

> **Context:** Routing & Pages | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

In sites with thousands of dynamic routes (e.g. e-commerce catalogs or large blogs), `getStaticPaths()` holds all returned `props` objects in Node.js heap memory throughout the entire build. Passing huge payloads (e.g. full HTML bodies, embedded relations, raw ASTs) across 10,000+ routes leads to JavaScript heap out-of-memory (`ERR_WORKER_OUT_OF_MEMORY`) crashes.

## 2. How It Differs From Classic React / Next.js

In Next.js SSG, `getStaticProps` runs on-demand per page during compilation, garbage-collecting each page's data immediately after rendering. In Astro, `getStaticPaths()` returns an array of all route definitions upfront before page rendering begins. Large arrays of heavy objects remain in memory during the generation phase.

## 3. Common Mistakes & Anti-Patterns

Passing entire raw database dumps, full uncompressed Markdown content strings, or deep relational graphs inside the `props` of every route entry in `getStaticPaths()`.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/pages/products/[sku].astro
export async function getStaticPaths() {
  // Loading 15,000 products with full descriptions and specifications
  const hugeCatalog = await fetchAllProductSpecs();
  return hugeCatalog.map(product => ({
    params: { sku: product.sku },
    // Anti-pattern: 15,000 full product specs kept in memory simultaneously!
    props: { product }
  }));
}
const { product } = Astro.props;
---
<div>{product.deepSpecifications.details}</div>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/pages/products/[sku].astro
import type { GetStaticPaths } from "astro";
import { getEntry } from "astro:content";

export const getStaticPaths = (async () => {
  // Only fetch lightweight identifiers and minimal routing meta
  const lightweightList = await fetchProductIndex();

  return lightweightList.map(item => ({
    params: { sku: item.sku },
    // Only pass lightweight ID or minimal props
    props: { id: item.id },
  }));
}) satisfies GetStaticPaths;

const { id } = Astro.props;
// Resolve the specific rich record on-demand during individual page render
// Garbage collected immediately after this page finishes rendering
const product = await fetchProductById(id);
---
<main>
  <h1>{product.name}</h1>
  <p>{product.description}</p>
</main>
```

## 4. Verification & Audit

Profile memory usage during large builds with Node memory flags:

```bash
NODE_OPTIONS="--max-old-space-size=4096" pnpm astro build
```

Ensure build memory footprint remains stable and doesn't scale linearly with the total number of generated pages.
