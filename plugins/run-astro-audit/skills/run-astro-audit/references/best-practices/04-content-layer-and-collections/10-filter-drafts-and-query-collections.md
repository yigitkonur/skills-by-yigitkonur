# Filter Drafts and Sort Entries Directly in getCollection

> **Context:** Content Layer & Collections | **Impact:** High | **Target:** Astro 5

## 1. Why We Do This

Marketing websites and content hubs routinely keep draft articles, internal notes, or future-dated announcements in progress. To prevent unpublished content from leaking into production builds or RSS feeds, `getCollection()` accepts an optional predicate function that filters entries before they enter static route generation or listing pages. Sorting by publication timestamp in `getStaticPaths` or index pages ensures a predictable, chronologically ordered content feed.

## 2. How It Differs From Classic React / Next.js

In Next.js, developers frequently forget to filter drafts inside `generateStaticParams()`, causing secret drafts to be built and deployed as public HTML endpoints. In Astro, passing the filter predicate directly to `getCollection('blog', ({ data }) => !data.draft)` filters items upstream, ensuring neither static paths nor index listings expose draft entries.

## 3. Common Mistakes & Anti-Patterns

Generating static routes for all collection entries without checking `data.draft` publishes internal drafts to production. Another anti-pattern is retrieving all entries into memory and doing post-hoc array filtering across every component instead of leveraging the predicate parameter.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/pages/blog/[id].astro (Leaking drafts to production)
import { getCollection } from 'astro:content';

export async function getStaticPaths() {
  // ❌ Retrieves all entries including drafts; generates public URLs for drafts!
  const posts = await getCollection('blog');
  return posts.map((post) => ({
    params: { id: post.id },
    props: { post },
  }));
}
---
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/pages/blog/[id].astro (Safe production draft filtering)
import { getCollection, render } from 'astro:content';

export async function getStaticPaths() {
  // ✅ Filter out drafts in production while allowing preview in development
  const posts = await getCollection('blog', ({ data }) => {
    return import.meta.env.PROD ? !data.draft : true;
  });

  return posts.map((post) => ({
    params: { id: post.id },
    props: { post },
  }));
}

const { post } = Astro.props;
const { Content } = await render(post);
---
<article>
  <h1>{post.data.title}</h1>
  <Content />
</article>
```

```astro
---
// src/pages/blog/index.astro (Sorted chronological listing)
import { getCollection } from 'astro:content';

const posts = (await getCollection('blog', ({ data }) => !data.draft))
  .sort((a, b) => b.data.pubDate.getTime() - a.data.pubDate.getTime());
---
<section>
  {posts.map((post) => (
    <article>
      <h2><a href={`/blog/${post.id}`}>{post.data.title}</a></h2>
      <time>{post.data.pubDate.toLocaleDateString()}</time>
    </article>
  ))}
</section>
```

## 4. Verification & Audit

Run a production build and verify that draft slugs are excluded from output routes:

```bash
pnpm astro build
```

Inspect `dist/` or the build output summary to confirm no draft files were rendered.
