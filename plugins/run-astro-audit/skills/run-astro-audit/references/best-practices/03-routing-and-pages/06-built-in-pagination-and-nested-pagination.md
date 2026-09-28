# Implement Standard and Nested Collection Pagination with paginate()

> **Context:** Routing & Pages | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Astro provides a native `paginate()` helper in `getStaticPaths()` that automatically partitions arrays into static pages (`/page/1`, `/page/2`) and injects a typed `Page<T>` object containing slice data and navigation URLs (`url.prev`, `url.next`, `url.first`, `url.last`).

## 2. How It Differs From Classic React / Next.js

In Next.js, pagination requires manual math (`slice((page-1)*limit, page*limit)`), manual generation of page count arrays in `generateStaticParams`, and manual URL link assembly. In Astro, `paginate()` handles chunking, current/total pages, boundary metadata, and URL assembly natively.

## 3. Common Mistakes & Anti-Patterns

Manually slicing arrays in `getStaticPaths()` instead of using `paginate()`, or naming the route parameter anything other than `[page].astro`. In nested pagination (e.g. `[tag]/[page].astro`), forgetting to pass `{ params: { tag } }` inside `paginate()` causes routes to lose their parent category context.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/pages/blog/[page].astro
// Manual slicing reinventing the wheel and losing typed metadata
export async function getStaticPaths() {
  const posts = await getPosts();
  const pageSize = 10;
  const totalPages = Math.ceil(posts.length / pageSize);
  return Array.from({ length: totalPages }, (_, i) => ({
    params: { page: String(i + 1) },
    props: { posts: posts.slice(i * pageSize, (i + 1) * pageSize) }
  }));
}
---
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/pages/blog/[tag]/[page].astro
import type { GetStaticPaths, Page } from "astro";

export const getStaticPaths = (async ({ paginate }) => {
  const allTags = ["tech", "design", "business"];
  const allPosts = await getBlogPosts();

  // For nested pagination, flatMap over categories and pass params to paginate()
  return allTags.flatMap(tag => {
    const filtered = allPosts.filter(p => p.tag === tag);
    return paginate(filtered, {
      params: { tag },
      pageSize: 10,
    });
  });
}) satisfies GetStaticPaths;

const { page } = Astro.props;
const { tag } = Astro.params;
---
<h1>Category: {tag} - Page {page.currentPage} of {page.lastPage}</h1>
<ul>
  {page.data.map(post => <li>{post.title}</li>)}
</ul>
<nav aria-label="Pagination">
  {page.url.prev && <a href={page.url.prev}>Previous</a>}
  {page.url.next && <a href={page.url.next}>Next</a>}
</nav>
```

## 4. Verification & Audit

Verify the generated paginated files and test boundary conditions:

```bash
pnpm astro build && ls -la dist/blog/tech/1/index.html dist/blog/tech/2/index.html
```

Check that `page.url.prev` is undefined on page 1 and `page.url.next` is undefined on the last page.
