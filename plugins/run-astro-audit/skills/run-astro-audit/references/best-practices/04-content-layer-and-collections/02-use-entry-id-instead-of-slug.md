# Query and Route by Entry ID Instead of Legacy Slug

> **Context:** Content Layer & Collections | **Impact:** Critical | **Target:** Astro 5

## 1. Why We Do This

In Astro 4 content collections, Markdown/MDX entries had a generated `slug` property, whereas data collections used an `id` property. This inconsistency created confusing mental overhead and awkward conditionals when querying different collection types. Astro 5 unifies all collections under the Content Layer API: every entry, whether Markdown, JSON, YAML, or API-sourced, uses `entry.id` as its primary unique identifier. The reserved `slug` property has been completely removed.

## 2. How It Differs From Classic React / Next.js

In Next.js, static routes commonly use `[slug]/page.tsx` where file basenames or CMS slug strings are manually extracted and passed through `generateStaticParams()`. In Astro 5, routing parameters map directly to `entry.id` produced by the loader. If URL slug transformations are desired, they can be customized directly in the loader's `generateId` option or mapped cleanly in `getStaticPaths()`.

## 3. Common Mistakes & Anti-Patterns

Accessing `entry.slug` on Astro 5 collection entries returns `undefined`. This silently breaks static route generation in `getStaticPaths`, resulting in pages generating routes with `/undefined/` or failing build validation.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/pages/blog/[slug].astro (Legacy Astro 4 idiom)
import { getCollection } from 'astro:content';

export async function getStaticPaths() {
  const posts = await getCollection('blog');
  return posts.map((post) => ({
    // ❌ post.slug is undefined in Astro 5 Content Layer!
    params: { slug: post.slug },
    props: { post },
  }));
}

const { post } = Astro.props;
---
<h1>{post.data.title}</h1>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/pages/blog/[id].astro (Idiomatic Astro 5)
import { getCollection } from 'astro:content';

export async function getStaticPaths() {
  const posts = await getCollection('blog');
  return posts.map((post) => ({
    // ✅ Use post.id for deterministic routing
    params: { id: post.id },
    props: { post },
  }));
}

const { post } = Astro.props;
---
<h1>{post.data.title}</h1>
```

## 4. Verification & Audit

Audit your codebase for deprecated `.slug` property access on collection entries:

```bash
grep -rn "\.slug\b" src/pages/ src/components/
```

Ensure all references to collection entries use `entry.id` and that `getEntry('collection', id)` queries use valid entry IDs.
