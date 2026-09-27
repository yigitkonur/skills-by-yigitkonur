# Render Entry Content via Precompiled rendered Object

> **Context:** Content Layer & Collections | **Impact:** High | **Target:** Astro 5 / Astro 7

## 1. Why We Do This

In Astro 5 and Astro 7, Content Layer loaders precompile Markdown and HTML entries into a cached `rendered` object on each entry (`entry.rendered.html`). Rather than re-running the markdown compilation pipeline or parsing MDAST/HAST repeatedly during template rendering, pages can directly consume `entry.rendered.html` or the modern `<Content />` component extracted from `await render(entry)`. This architectural boundary guarantees zero redundant markdown parsing passes across high-volume collections (>3,000 routes), drastically slashing SSG build times and memory footprint.

## 2. How It Differs From Classic React / Next.js

In Next.js, content rendering frequently involves re-parsing Markdown on every request or re-compiling MDX inside Server Components using `next-mdx-remote` or dynamic AST evaluations. In Astro's Content Layer, parsing is performed strictly once during the datastore sync phase. The serialized HTML and metadata (headings, frontmatter) are persisted in the SQLite datastore and served instantly during page generation without invoking Markdown transformers again.

## 3. Common Mistakes & Anti-Patterns

Attempting to re-invoke custom remark/rehype parsers or markdown AST walkers inside page components or loops, re-compiling the raw markdown source string on every route.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// ❌ Re-compiling markdown string manually in template render loops
import { getEntry } from 'astro:content';
import { unified } from 'unified';
import remarkParse from 'remark-parse';
import remarkHtml from 'remark-html';

const post = await getEntry('articles', Astro.params.slug);
// Redundant markdown compiler invocation!
const processed = await unified()
  .use(remarkParse)
  .use(remarkHtml)
  .process(post.body);
---
<article set:html={processed.toString()} />
```

### ✅ Best Practice / Idiomatic

```astro
---
// ✅ Consuming precompiled rendered object or idiomatic render(entry)
import { getEntry, render } from 'astro:content';

const post = await getEntry('articles', Astro.params.slug);
if (!post) throw new Error('Post not found');

// Option A: Canonical render component
const { Content, headings } = await render(post);

// Option B: Direct access to precompiled rendered HTML from DataStore
const renderedHtml = post.rendered?.html;
---
<article>
  {renderedHtml ? <Fragment set:html={renderedHtml} /> : <Content />}
</article>
```

## 4. Verification & Audit

Verify that templates do not invoke ad-hoc unified/remark compilers during static page generation:

```bash
git grep -n "unified().*use(" src/pages/ src/components/
```

Ensure all content entry rendering utilizes `await render(entry)` from `astro:content` or precompiled `entry.rendered`.
