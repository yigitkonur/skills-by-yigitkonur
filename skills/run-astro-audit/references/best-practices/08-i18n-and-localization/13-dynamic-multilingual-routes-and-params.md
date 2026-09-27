# Generate Param-Driven Static Paths for Multilingual Dynamic Routes

> **Context:** i18n & Localization | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Copying and pasting template code across duplicate route folders (`src/pages/en/blog/[slug].astro`, `src/pages/es/blog/[slug].astro`) introduces layout drift, increases maintenance cost, and duplicates component bug fixes. Using a parameterized dynamic route (`src/pages/[lang]/blog/[...slug].astro`) collapses all language rendering into a single, unified template driven by `getStaticPaths()`.

## 2. How It Differs From Classic React / Next.js

In Next.js App Router, `app/[locale]/blog/[slug]/page.tsx` uses `generateStaticParams()`. In Astro, `getStaticPaths()` returns an array of objects containing both `params` (URL parameters) and `props` (pre-computed page data). This pattern allows Astro to fetch and pass the exact Markdown/MDX entry directly as a prop during compilation, eliminating redundant runtime database queries.

## 3. Common Mistakes & Anti-Patterns

A frequent anti-pattern is creating duplicate `.astro` files for every language. Another mistake is calling `getCollection()` inside the component body instead of `getStaticPaths()`, causing unnecessary collection scans on every rendered route.

### ❌ Bad Practice / Anti-Pattern

```
// Maintenance nightmare: duplicate route files per language
src/pages/
├── en/
│   └── blog/
│       └── [slug].astro  <-- Identical template
├── es/
│   └── blog/
│       └── [slug].astro  <-- Identical template
└── fr/
    └── blog/
        └── [slug].astro  <-- Identical template
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/pages/[lang]/blog/[...slug].astro - Single unified dynamic route
import { getCollection, render } from "astro:content";

export async function getStaticPaths() {
  const posts = await getCollection("blog");

  return posts.map((post) => {
    // Extract language and slug from file path in Content Layer
    const [lang, ...slugParts] = post.id.replace(/\.[^/.]+$/, "").split("/");
    return {
      params: {
        lang,
        slug: slugParts.join("/") || undefined,
      },
      props: { post },
    };
  });
}

const { post } = Astro.props;
const { Content } = await render(post);
---
<article>
  <h1>{post.data.title}</h1>
  <time datetime={post.data.date.toISOString()}>
    {post.data.date.toLocaleDateString(Astro.params.lang)}
  </time>
  <Content />
</article>
```

## 4. Verification & Audit

Run a production build and inspect generated route files:

```bash
npx astro build
```

Verify the build summary table: confirm that `/[lang]/blog/[...slug]` successfully emits static HTML files across all localized subpaths (`/en/blog/...`, `/es/blog/...`, `/fr/blog/...`).
