# Validate and Optimize Frontmatter Assets Using the image Schema Helper

> **Context:** Content Layer & Collections | **Impact:** High | **Target:** Astro 5

## 1. Why We Do This

Editorial content commonly references local cover images, author avatars, and infographic assets in frontmatter. Defining image properties as plain strings (`z.string()`) bypasses Astro's image optimization engine and leaves broken file paths undetected until runtime 404s occur. By passing the `{ image }` context parameter into the collection schema callback, Astro validates that referenced image files exist on disk at build time and resolves them into typed `ImageMetadata` objects with intrinsic dimensions (`width`, `height`, `format`).

## 2. How It Differs From Classic React / Next.js

In Next.js Markdown pipelines, image paths in frontmatter are typically static public strings (e.g. `/assets/cover.png`). Next.js's `<Image>` requires explicit `width` and `height` properties or manual `getStaticProps` probes via image-size libraries to prevent Cumulative Layout Shift (CLS). In Astro 5, the `image()` schema validator automatically extracts metadata at build time, allowing Astro's `<Image />` component to render optimized WebP/AVIF formats with exact aspect ratios.

## 3. Common Mistakes & Anti-Patterns

Using `cover: z.string()` and rendering with a native HTML `<img>` tag forces the browser to download uncompressed raw originals and causes severe layout shifts. In custom loaders, omitting `filePath` on `DataEntry` causes `image()` to treat relative paths as public URLs instead of asset imports.

### ❌ Bad Practice / Anti-Pattern

```ts
// src/content.config.ts (Unvalidated string path)
import { defineCollection, z } from 'astro:content'
import { glob } from 'astro/loaders'

const blog = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/data/blog' }),
  schema: z.object({
    title: z.string(),
    // ❌ Plain string; does not verify file existence or extract dimensions
    cover: z.string(),
  }),
})
```

### ✅ Best Practice / Idiomatic

```ts
// src/content.config.ts (Validated ImageMetadata helper)
import { defineCollection, z } from 'astro:content'
import { glob } from 'astro/loaders'

const blog = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/data/blog' }),
  // ✅ Access the image helper from schema callback context
  schema: ({ image }) =>
    z.object({
      title: z.string(),
      cover: image(),
      coverAlt: z.string(),
      pubDate: z.coerce.date(),
    }),
})

export const collections = { blog }
```

```astro
---
// src/pages/blog/[id].astro (Zero-CLS responsive image rendering)
import { getEntry } from 'astro:content';
import { Image } from 'astro:assets';

const post = await getEntry('blog', Astro.params.id);
if (!post) throw new Error('Post not found');
---
<article>
  <!-- ✅ Astro optimizes format, calculates dimensions, and prevents CLS -->
  <Image
    src={post.data.cover}
    alt={post.data.coverAlt}
    widths={[400, 800, 1200]}
    sizes="(max-width: 800px) 100vw, 800px"
    loading="eager"
  />
  <h1>{post.data.title}</h1>
</article>
```

## 4. Verification & Audit

Run the build process to verify asset resolution:

```bash
pnpm astro build
```

If an image path referenced in frontmatter does not exist on disk, the build terminates with `[astro:content] Image does not exist` pointing directly to the offending file.
