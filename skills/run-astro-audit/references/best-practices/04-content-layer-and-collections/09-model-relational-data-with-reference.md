# Model Cross-Collection Relations with reference and Resolve with getEntries

> **Context:** Content Layer & Collections | **Impact:** High | **Target:** Astro 5

## 1. Why We Do This

Content models often contain relationships, such as articles linked to author profiles, categories, or related articles. Astro provides the `reference()` schema helper to define type-safe foreign-key relationships across collections. At build time, Astro validates that referenced identifiers match valid collection keys. In templates, the `getEntry()` and `getEntries()` helpers cleanly resolve reference objects into full collection entries.

## 2. How It Differs From Classic React / Next.js

In Next.js Markdown setups, developers typically duplicate author objects across dozens of frontmatter files, or manually maintain custom lookup tables and join logic in helper utilities. Astro's `reference()` formalizes a relational content model: authors exist in one normalized collection (e.g. `authors.json`), and articles refer to them by ID, guaranteeing data consistency without duplication.

## 3. Common Mistakes & Anti-Patterns

Storing plain unvalidated strings for foreign keys (e.g. `author: z.string()`) allows broken references when author IDs change. Another trap is attempting to access author fields directly on `post.data.author` without resolving the reference first via `getEntry()`.

### ❌ Bad Practice / Anti-Pattern

```ts
// src/content.config.ts (Unvalidated foreign keys)
import { defineCollection, z } from 'astro:content'
import { glob } from 'astro/loaders'

const blog = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/data/blog' }),
  schema: z.object({
    title: z.string(),
    // ❌ Plain string; no validation that this author exists in 'authors' collection
    authorId: z.string(),
  }),
})
```

### ✅ Best Practice / Idiomatic

```ts
// src/content.config.ts (Type-safe relational reference)
import { defineCollection, reference, z } from 'astro:content'
import { glob, file } from 'astro/loaders'

const authors = defineCollection({
  loader: file('src/data/authors.json'),
  schema: z.object({
    id: z.string(),
    name: z.string(),
    bio: z.string(),
  }),
})

const blog = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/data/blog' }),
  schema: z.object({
    title: z.string(),
    // ✅ Validates relationship against the 'authors' collection
    author: reference('authors'),
    relatedPosts: z.array(reference('blog')).default([]),
  }),
})

export const collections = { authors, blog }
```

```astro
---
// src/pages/blog/[id].astro (Resolving references at page render)
import { getEntry, getEntries, render } from 'astro:content';

const post = await getEntry('blog', Astro.params.id);
if (!post) throw new Error('Post not found');

// ✅ Resolve single reference and array references
const author = await getEntry(post.data.author);
const relatedPosts = await getEntries(post.data.relatedPosts);
const { Content } = await render(post);
---
<article>
  <h1>{post.data.title}</h1>
  <p>By {author.data.name} — {author.data.bio}</p>
  <Content />
</article>
```

## 4. Verification & Audit

Run type checking to ensure all references point to valid collections and that references are resolved before property access:

```bash
pnpm astro check
```

Astro will emit a build error if a referenced ID does not exist in the target collection.
