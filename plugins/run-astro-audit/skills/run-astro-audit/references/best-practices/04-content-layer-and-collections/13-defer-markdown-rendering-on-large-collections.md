# Defer Markdown Rendering on Massive Collections with deferRender

> **Context:** Content Layer & Collections | **Impact:** High | **Target:** Astro 5

## 1. Why We Do This

By default, Astro's `glob()` loader eagerly compiles Markdown entries to HTML during content synchronization and stores the rendered HTML in the Content Layer DataStore. While this accelerates incremental builds for small-to-medium sites, storing pre-rendered HTML in memory for collections containing tens of thousands of detailed articles can exhaust Node.js heap memory, resulting in Out-Of-Memory (OOM) build failures. Setting `deferRender: true` defers HTML compilation until a specific page renders the entry via `render(entry)`, drastically shrinking the initial memory footprint.

## 2. How It Differs From Classic React / Next.js

In Next.js, compiling thousands of MDX files often causes severe CPU and memory saturation because each page invocation in `generateStaticParams()` or `page.tsx` parses MDX ad-hoc without centralized memory lifecycle controls. Astro 5 provides `deferRender` as a declarative toggle, giving engineers fine-grained governance over build-time memory vs. compile-time scheduling.

## 3. Common Mistakes & Anti-Patterns

Enabling eager rendering on large enterprise blogs (5,000+ long-form articles) on standard CI runners (e.g. 4 GB / 8 GB memory limits). The runner crashes during `astro sync` with `JavaScript heap out of memory`.

### ❌ Bad Practice / Anti-Pattern

```ts
// src/content.config.ts (Eager rendering exhausts CI heap memory)
import { defineCollection, z } from 'astro:content'
import { glob } from 'astro/loaders'

const knowledgeBase = defineCollection({
  // ❌ Default deferRender: false renders all 15,000 docs eagerly during sync!
  loader: glob({ pattern: '**/*.md', base: './content/docs' }),
  schema: z.object({
    title: z.string(),
  }),
})

export const collections = { knowledgeBase }
```

### ✅ Best Practice / Idiomatic

```ts
// src/content.config.ts (Deferred rendering for massive collections)
import { defineCollection, z } from 'astro:content'
import { glob } from 'astro/loaders'

const knowledgeBase = defineCollection({
  // ✅ Defers compilation until individual routes call render(entry)
  loader: glob({
    pattern: '**/*.md',
    base: './content/docs',
    deferRender: true,
    retainBody: false, // Also drops raw source body from store to save RAM
  }),
  schema: z.object({
    title: z.string(),
  }),
})

export const collections = { knowledgeBase }
```

## 4. Verification & Audit

Run a production build with Node memory inspection to verify memory stabilization:

```bash
node --max-old-space-size=2048 ./node_modules/.bin/astro build
```

Verify that the build completes successfully without triggering heap exhaustion during content synchronization.
