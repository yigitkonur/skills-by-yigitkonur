# Coerce Frontmatter Timestamps with z.coerce.date

> **Context:** Content Layer & Collections | **Impact:** Medium | **Target:** Astro 5

## 1. Why We Do This

In Markdown frontmatter (YAML) and JSON content files, date fields are serialized as strings (e.g. `"2026-09-26"` or ISO-8601 timestamps). Using Zod's `z.date()` validator expects an existing JavaScript `Date` instance and throws a runtime validation error when receiving strings: `Expected date, received string`. Using `z.coerce.date()` instructs Zod to coerce the incoming string or timestamp into a native JavaScript `Date` object during schema parsing.

## 2. How It Differs From Classic React / Next.js

In Next.js, props passed between server components and client components must be JSON-serializable, so dates are frequently kept as raw strings (`string`) to avoid serialization errors across the client boundary. In Astro, `.astro` components execute strictly on the server; having a strongly typed native `Date` object in `entry.data.pubDate` allows direct invocation of methods like `.toLocaleDateString()` or `.getTime()` without repetitive manual parsing.

## 3. Common Mistakes & Anti-Patterns

Defining date fields as `z.string()` pushes manual `new Date(post.data.pubDate)` parsing onto every page or UI component. Conversely, using `z.date()` causes build failures whenever YAML authors format dates without YAML-native date syntax.

### ❌ Bad Practice / Anti-Pattern

```ts
// src/content.config.ts (Strict z.date causes validation crashes)
import { defineCollection, z } from 'astro:content'
import { glob } from 'astro/loaders'

const blog = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/data/blog' }),
  schema: z.object({
    title: z.string(),
    // ❌ Fails with 'Expected date, received string' when parsing JSON or strings
    pubDate: z.date(),
  }),
})
```

### ✅ Best Practice / Idiomatic

```ts
// src/content.config.ts (Robust date coercion)
import { defineCollection, z } from 'astro:content'
import { glob } from 'astro/loaders'

const blog = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/data/blog' }),
  schema: z.object({
    title: z.string(),
    // ✅ Coerces string, number, or Date into a verified JavaScript Date object
    pubDate: z.coerce.date(),
    updatedDate: z.coerce.date().optional(),
  }),
})

export const collections = { blog }
```

```astro
---
// src/pages/blog/[id].astro
import { getEntry } from 'astro:content';

const post = await getEntry('blog', Astro.params.id);
if (!post) throw new Error('Post not found');
---
<!-- ✅ Native Date methods work directly without repetitive new Date() wraps -->
<time datetime={post.data.pubDate.toISOString()}>
  {post.data.pubDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
</time>
```

## 4. Verification & Audit

Run type checking and schema validation:

```bash
pnpm astro check
```

Inspect terminal output to verify zero `ZodError: Expected date, received string` errors during build.
