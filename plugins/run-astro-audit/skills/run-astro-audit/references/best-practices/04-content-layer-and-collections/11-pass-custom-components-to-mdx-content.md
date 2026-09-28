# Map Custom Components and Islands into MDX via the Content Component

> **Context:** Content Layer & Collections | **Impact:** High | **Target:** Astro 5

## 1. Why We Do This

MDX combines Markdown simplicity with component versatility. When rendering MDX entries via `render(entry)`, the resulting `<Content />` component accepts a `components` prop. This allows replacing native HTML element tags (such as `blockquote`, `pre`, or `a`) with custom Astro design system components, or injecting interactive UI islands (React, Preact, Vue, Svelte) directly into editorial prose without modifying raw Markdown source files.

## 2. How It Differs From Classic React / Next.js

In Next.js, using `@mdx-js/react` often requires a root `<MDXProvider>` and making parent wrappers client components (`'use client'`), which forces unnecessary client-side React hydration on the entire article body. In Astro 5, the MDX `<Content />` component compiles strictly to static server-side HTML. Only components explicitly given a `client:*` directive hydrate in the browser, preserving zero-JS baselines.

## 3. Common Mistakes & Anti-Patterns

Importing components inside every single `.mdx` file creates tedious boilerplate across hundreds of posts. Conversely, attempting to override HTML tags using global CSS hacks rather than component props breaks design token consistency and accessibility.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/pages/blog/[id].astro (Raw unstyled rendering)
import { getEntry, render } from 'astro:content';

const post = await getEntry('blog', Astro.params.id);
if (!post) throw new Error('Post not found');

const { Content } = await render(post);
---
<!-- ❌ Renders raw blockquotes and links without design system overrides -->
<article class="prose">
  <Content />
</article>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/pages/blog/[id].astro (Mapping custom components)
import { getEntry, render } from 'astro:content';
import CustomBlockquote from '../../components/CustomBlockquote.astro';
import CodeBlock from '../../components/CodeBlock.astro';
import InteractivePoll from '../../components/InteractivePoll.jsx';

const post = await getEntry('blog', Astro.params.id);
if (!post) throw new Error('Post not found');

const { Content } = await render(post);
---
<article>
  <h1>{post.data.title}</h1>
  <!-- ✅ Overrides standard HTML tags and provides interactive islands -->
  <Content
    components={{
      blockquote: CustomBlockquote,
      pre: CodeBlock,
      InteractivePoll,
    }}
  />
</article>
```

## 4. Verification & Audit

Run the dev server and inspect rendered elements in the browser DOM:

```bash
pnpm astro dev
```

Verify that `<blockquote>` elements are replaced by `<CustomBlockquote>` markup and that client islands hydrate cleanly when scrolled into view.
