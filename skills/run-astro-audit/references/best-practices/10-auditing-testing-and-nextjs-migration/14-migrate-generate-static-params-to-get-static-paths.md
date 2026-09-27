# Migrate Next.js generateStaticParams to Astro getStaticPaths with Props Passing

> **Context:** Auditing & Next.js Migration | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

In Next.js App Router, `generateStaticParams()` returns only URL parameter strings (e.g. `[{ id: '1' }]`). Consequently, every generated page component must execute a redundant second fetch or database query to retrieve the actual page data. Astro's `getStaticPaths()` function returns both `params` (for routing) and `props` (for component rendering), allowing all data to be fetched once in batch and passed directly into each route, slashing build times and database pressure.

## 2. How It Differs From Classic React / Next.js

Next.js requires workarounds like `React.cache()` to deduplicate fetches between `generateStaticParams()` and the Server Component page function. In Astro, `getStaticPaths()` executes once at build time; each entry in the returned array directly hydrates `Astro.props` for that static page.

## 3. Common Mistakes & Anti-Patterns

Returning only `params` in Astro's `getStaticPaths()`, then performing another `fetch()` or query inside the page frontmatter for each individual slug, causing N+1 build-time queries.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/pages/blog/[slug].astro - N+1 Query Trap (Next.js mental model)
export async function getStaticPaths() {
  const posts = await fetch('https://api.example.com/posts').then(r => r.json());
  return posts.map(p => ({ params: { slug: p.slug } }));
}

// Inefficient: Re-fetches individual post for every single route at build time!
const { slug } = Astro.params;
const post = await fetch(`https://api.example.com/posts/${slug}`).then(r => r.json());
---
<h1>{post.title}</h1>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/pages/blog/[slug].astro - Single Batch Query with Props Passing
export async function getStaticPaths() {
  const posts = await fetch('https://api.example.com/posts').then(r => r.json());
  return posts.map(post => ({
    params: { slug: post.slug },
    props: { post }, // Pass entire data payload directly
  }));
}

// Zero extra network requests: Read directly from Astro.props
const { post } = Astro.props;
---
<h1>{post.title}</h1>
```

## 4. Verification & Audit

Verify that dynamic routes build cleanly without N+1 query logs:

```bash
# Run build and inspect build output for static route generation
pnpm build
# Astro logs: "▶ src/pages/blog/[slug].astro -> dist/blog/* (X routes generated)"
```
