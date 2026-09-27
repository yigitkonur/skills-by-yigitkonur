# Ingest Filesystem Trees with the Built-in glob Loader

> **Context:** Content Layer & Collections | **Impact:** High | **Target:** Astro 5

## 1. Why We Do This

Astro 5 introduces the built-in `glob()` loader in `astro/loaders` to load multi-file collections from any filesystem location. Unlike Astro 4, which restricted content files strictly to subdirectories inside `src/content/`, `glob()` accepts a `base` directory located anywhere in your project (e.g. `src/data/blog`, `docs/`, or shared monorepo packages). It automatically handles Markdown, MDX, Markdoc, JSON, YAML, and TOML files, generating deterministic IDs, validating frontmatter schemas, and hashing contents for incremental builds.

## 2. How It Differs From Classic React / Next.js

In Next.js, reading directory trees requires rolling custom filesystem traversal logic using `fast-glob` or Node's `fs.promises.readdir` inside `getStaticPaths` or route handlers, manually stripping file extensions to construct slugs, and parsing frontmatter per request. Astro's `glob()` loader abstracts this into a declarative build-time primitive that automatically runs once, caches results, and exposes type-safe querying APIs.

## 3. Common Mistakes & Anti-Patterns

Using the deprecated `Astro.glob()` API inside `.astro` components bypasses the Content Layer, preventing schema validation and incremental build caching. Another mistake is hardcoding redundant prefixes in `pattern` instead of specifying a clean `base` directory.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/pages/blog/index.astro (Deprecated Astro.glob)
// ❌ Deprecated in Astro 5; lacks schema enforcement and datastore caching
const posts = await Astro.glob('../../content/blog/*.md');
---
<ul>
  {posts.map((post) => (
    <li><a href={post.url}>{post.frontmatter.title}</a></li>
  ))}
</ul>
```

### ✅ Best Practice / Idiomatic

```ts
// src/content.config.ts (Built-in glob loader)
import { defineCollection, z } from 'astro:content'
import { glob } from 'astro/loaders'

const blog = defineCollection({
  // ✅ Declarative glob loader pointing to any base directory
  loader: glob({
    pattern: '**/*.{md,mdx}',
    base: './src/data/blog',
    generateId: ({ entry }) => entry.replace(/\.[^.]+$/, '').toLowerCase(),
  }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    pubDate: z.coerce.date(),
    draft: z.boolean().default(false),
  }),
})

export const collections = { blog }
```

## 4. Verification & Audit

Verify that no deprecated `Astro.glob()` calls remain in your project:

```bash
grep -rn "Astro\.glob(" src/
```

Run `pnpm astro check` to verify that collections configured with `glob()` pass schema validation and type checking.
