# Standard Markdown vs MDX Compilation Performance at Scale

> **Context:** Content Layer & Collections | **Impact:** High | **Target:** Astro 5 / Astro 7

## 1. Why We Do This

Standard Markdown (`.md`) processed through Astro's native Sätteri Rust processor (`@astrojs/markdown-satteri`) compiles orders of magnitude faster than MDX (`.mdx`). Sätteri leverages pulldown-cmark and oxc in Rust to transform Markdown into MDAST and HAST in linear time with minimal memory overhead. In contrast, MDX treats every file as a JSX component, requiring full Babel/ESLint parsing, JSX transform, and injection into the Vite/Rollup module graph. On enterprise websites with thousands of articles, guides, and glossary terms, defaulting to MDX causes immense RAM spikes and slow builds. Pure Markdown (`.md`) must be the strict default for long-form content collections, reserving `.mdx` only for pages that genuinely require interactive embedded React or Astro components.

## 2. How It Differs From Classic React / Next.js

In Next.js, content sites frequently adopt MDX ubiquitously without profiling compilation cost, relying on runtime compilation or heavy webpack loaders that saturate CPU cores. In Astro, the Content Layer architecture decouples raw content loading from the component bundler. Standard Markdown bypasses Vite's module graph entirely, pre-rendering directly to HTML in the SQLite DataStore.

## 3. Common Mistakes & Anti-Patterns

Using `.mdx` file extensions for pure prose or articles that contain only standard markdown text, tables, and images, forcing the full JSX compiler overhead without any interactive components.

### ❌ Bad Practice / Anti-Pattern

```ts
// src/content.config.ts
import { defineCollection, z } from 'astro:content'
import { glob } from 'astro/loaders'

export const collections = {
  // ❌ Forcing all 3,000 articles through MDX JSX compiler pipeline
  articles: defineCollection({
    loader: glob({ pattern: '**/*.mdx', base: './src/content/articles' }),
    schema: z.object({ title: z.string() }),
  }),
}
```

### ✅ Best Practice / Idiomatic

```ts
// src/content.config.ts
import { defineCollection, z } from 'astro:content'
import { glob } from 'astro/loaders'

export const collections = {
  // ✅ Defaulting to high-performance Sätteri Rust markdown compiler
  articles: defineCollection({
    loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/articles' }),
    schema: z.object({ title: z.string() }),
  }),
}
```

## 4. Verification & Audit

Check the ratio of `.md` to `.mdx` files in content collections:

```bash
find src/content/articles/ -name "*.md" | wc -l
find src/content/articles/ -name "*.mdx" | wc -l
```

Profile build performance with Sätteri:

```bash
pnpm exec astro build --verbose
```
