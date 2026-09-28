# Locate Collection Config in src/content.config.ts and Drop Legacy Type Property

> **Context:** Content Layer & Collections | **Impact:** Critical | **Target:** Astro 5

## 1. Why We Do This

Astro 5 replaces the legacy content collections engine with the Content Layer API. In Astro 4, collections required a hardcoded `src/content/config.ts` file and a `type: 'content' | 'data'` property that coupled all Markdown/MDX files into Vite's module graph. This caused severe memory spikes and slow builds for sites with thousands of entries. Astro 5 moves the configuration to `src/content.config.ts` at the root of `src/` and introduces universal loaders (`loader: glob(...)`), decoupling content from Vite and storing it in a persistent, reactive build-time datastore.

## 2. How It Differs From Classic React / Next.js

In Next.js App Router, developers often parse local Markdown using `fs.readFileSync` and `gray-matter` inside `page.tsx` or utility files, resulting in fragmented data handling, repeated disk I/O across routes, and lack of unified build-time schema validation. Astro 5 provides a single centralized configuration contract where all content sources—filesystem or remote—are normalized into typed collections before page rendering begins.

## 3. Common Mistakes & Anti-Patterns

Leaving the configuration file inside `src/content/config.ts` forces Astro 5 into legacy emulation mode. Furthermore, continuing to declare `type: 'content'` or `type: 'data'` triggers deprecation warnings and prevents loaders from reading directories outside `src/content/`.

### ❌ Bad Practice / Anti-Pattern

```ts
// src/content/config.ts (Legacy Astro 4 structure)
import { defineCollection, z } from 'astro:content'

const blog = defineCollection({
  type: 'content', // ❌ Deprecated in Astro 5; forces legacy Vite bundling
  schema: z.object({
    title: z.string(),
    pubDate: z.date(),
  }),
})

export const collections = { blog }
```

### ✅ Best Practice / Idiomatic

```ts
// src/content.config.ts (Astro 5 Content Layer)
import { defineCollection, z } from 'astro:content'
import { glob } from 'astro/loaders'

const blog = defineCollection({
  // ✅ Explicit loader specifying base directory and pattern
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/data/blog' }),
  schema: z.object({
    title: z.string(),
    pubDate: z.coerce.date(),
  }),
})

export const collections = { blog }
```

## 4. Verification & Audit

Run the sync command to ensure the configuration file is recognized and collections are generated:

```bash
pnpm astro sync
```

Verify that `.astro/types.d.ts` generates types from `src/content.config.ts` without emitting `legacy.collections` deprecation warnings in the terminal.
