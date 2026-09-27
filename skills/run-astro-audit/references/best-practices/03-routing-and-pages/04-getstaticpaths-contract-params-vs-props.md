# Leverage Props in getStaticPaths To Eliminate Redundant Fetching

> **Context:** Routing & Pages | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

In static (SSG) mode, `getStaticPaths()` runs strictly once at build time. Returning a `props` object alongside `params` in each path entry injects pre-fetched, transformed data directly into `Astro.props` of that generated page. This eliminates redundant database queries or API roundtrips across thousands of static pages.

## 2. How It Differs From Classic React / Next.js

In Next.js Pages router, you had to separate `getStaticPaths` (which only returned params) from `getStaticProps` (which fetched data per page request). In Next.js App Router, `generateStaticParams` only generates route keys, and the page component re-fetches its data (relying on `fetch` caching). In Astro, `getStaticPaths` is a unified pipeline returning both the route keys (`params`) and the page payload (`props`).

## 3. Common Mistakes & Anti-Patterns

Only returning `params` from `getStaticPaths()` and then performing individual queries or finding operations inside the page frontmatter for each route. When generating 1,000 pages, this triggers 1,000 redundant lookups or remote requests instead of fetching once in `getStaticPaths()`.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/pages/blog/[id].astro
export async function getStaticPaths() {
  const posts = await fetch('https://api.example.com/posts').then(r => r.json());
  // BAD: Only returns params; forces each page to re-fetch or re-query
  return posts.map(post => ({ params: { id: post.id } }));
}

const { id } = Astro.params;
// REDUNDANT: Every page triggers a network call during build!
const post = await fetch(`https://api.example.com/posts/${id}`).then(r => r.json());
---
<h1>{post.title}</h1>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/pages/blog/[id].astro
import type { GetStaticPaths } from "astro";

interface Post {
  id: string;
  title: string;
  summary: string;
}

export const getStaticPaths = (async () => {
  // Fetch once for the entire collection at build time
  const posts: Post[] = await fetch('https://api.example.com/posts').then(r => r.json());

  return posts.map(post => ({
    params: { id: post.id },
    props: { post }, // Pass pre-fetched data directly
  }));
}) satisfies GetStaticPaths;

// Data is passed directly with zero build-time re-fetching
const { post } = Astro.props;
---
<article>
  <h1>{post.title}</h1>
  <p>{post.summary}</p>
</article>
```

## 4. Verification & Audit

Audit your dynamic routes for duplicate API calls during `pnpm astro build`. Check that network requests in `getStaticPaths()` occur once per collection rather than once per page execution.
