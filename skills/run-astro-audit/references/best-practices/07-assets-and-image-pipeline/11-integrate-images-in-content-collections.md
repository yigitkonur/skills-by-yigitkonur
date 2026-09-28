# Validate and Resolve Images in Content Collections Schemas

> **Context:** Assets & Image Pipeline | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Content authors frequently declare cover photos and author headshots in markdown/MDX frontmatter using relative paths (e.g. `cover: "./cover.jpg"`). Using Astro's `image()` schema helper in `astro:content` validates that the image file actually exists on disk during build, resolves the relative path into Vite's module graph, and transforms the frontmatter string into a full `ImageMetadata` object containing intrinsic dimensions and format information for `<Image />`.

## 2. How It Differs From Classic React / Next.js

In Next.js with Contentlayer or gray-matter, frontmatter image fields are parsed merely as raw strings. The developer must manually store files in `/public`, write custom file-system lookup helpers, or construct custom image loaders. Astro integrates frontmatter image resolution directly into the build compiler.

## 3. Common Mistakes & Anti-Patterns

Declaring the frontmatter schema field as `z.string()`. This leaves the property as an unverified string path, breaking automatic dimension inference in `<Image />` and failing to catch broken image links at build time.

### ❌ Bad Practice / Anti-Pattern

Typing frontmatter image paths as generic strings in content schemas:

```typescript
// src/content/config.ts
import { defineCollection, z } from 'astro:content'

// ❌ Anti-Pattern: z.string() fails to validate asset presence and loses ImageMetadata
export const collections = {
  blog: defineCollection({
    schema: z.object({
      title: z.string(),
      cover: z.string(), // Breaks <Image src={post.data.cover} />
    }),
  }),
}
```

### ✅ Best Practice / Idiomatic

Use the context-provided `({ image })` helper to validate and transform images into `ImageMetadata`:

```typescript
// src/content/config.ts
import { defineCollection, z } from 'astro:content'

export const collections = {
  blog: defineCollection({
    schema: ({ image }) =>
      z.object({
        title: z.string(),
        cover: image(), // ✅ Resolves relative file, verifies presence, infers dimensions
        coverAlt: z.string(),
      }),
  }),
}
```

Render directly with `<Image />` without manual dimension extraction:

```astro
---
// src/pages/blog/[slug].astro
import { Image } from 'astro:assets';
const { post } = Astro.props;
---
<Image src={post.data.cover} alt={post.data.coverAlt} />
```

## 4. Verification & Audit

Run Astro's type check to confirm `post.data.cover` is strongly typed as `ImageMetadata`:

```bash
pnpm astro check
```
