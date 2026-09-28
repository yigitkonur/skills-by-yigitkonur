# Replace React Server Components with Zero-Runtime Native Astro Components

> **Context:** Auditing & Next.js Migration | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

React Server Components (RSC) in Next.js execute on the server but still serialize React Virtual DOM descriptors into an RSC wire payload (flight stream). If any child component on the page is marked `'use client'`, the browser must download the React runtime, React DOM, and the flight parser. Native `.astro` components compile strictly to raw HTML strings. They have zero runtime cost, produce no virtual DOM serialization, and run top-level `await` asynchronously in their frontmatter.

## 2. How It Differs From Classic React / Next.js

In Next.js, Server Components are functions that return JSX (`export default async function Page() { return <main>...</main> }`). In Astro, the component logic lives in the component script fence (`---`), while the template below is standard HTML. There is no `return` statement, no JSX factory overhead, and no virtual DOM reconciliation.

## 3. Common Mistakes & Anti-Patterns

Wrapping entire pages in React components using `@astrojs/react` instead of writing `.astro` pages. Porting an async Next.js `page.tsx` as a React component into Astro causes SSR serialization issues or forces unnecessary React runtime download.

### ❌ Bad Practice / Anti-Pattern

```tsx
// src/components/NextStylePage.tsx - Ported verbatim from Next.js
// Forces React runtime and virtual DOM generation on every request
export default async function NextStylePage({ data }: { data: any }) {
  const posts = await fetch('https://api.example.com/posts').then((r) => r.json())
  return (
    <div className="container">
      {posts.map((post: any) => (
        <article key={post.id}>
          <h2>{post.title}</h2>
        </article>
      ))}
    </div>
  )
}
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/pages/index.astro - Native Astro: Zero runtime, direct top-level await
interface Post {
  id: number;
  title: string;
}

const response = await fetch('https://api.example.com/posts');
const posts: Post[] = await response.json();
---
<div class="container">
  {posts.map((post) => (
    <article>
      <h2>{post.title}</h2>
    </article>
  ))}
</div>
```

## 4. Verification & Audit

Verify that the generated page contains raw HTML without React flight payload scripts (`<script>self.__next_f.push(...)</script>`):

```bash
# Ensure no React flight/RSC streaming scripts appear in built output
grep -i '__next_f' dist/index.html && echo "FAIL: RSC flight payload detected" || echo "PASS: Pure HTML"
```
