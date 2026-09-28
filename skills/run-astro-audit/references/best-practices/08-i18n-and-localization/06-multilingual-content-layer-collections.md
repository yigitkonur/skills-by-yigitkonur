# Structure Multilingual Content Layer Collections with Subfolder IDs

> **Context:** i18n & Localization | **Impact:** Critical | **Target:** Astro 5

## 1. Why We Do This

Astro 5 introduced the Content Layer API, standardizing collection entries across local markdown, MDX, and remote headless loaders. In Astro 5 collections, entry identifiers are strictly accessed via `entry.id`, and the legacy `entry.slug` property is deprecated. Organizing multilingual collections into locale subfolders (`src/content/blog/en/post.md`) guarantees clean separation while enabling simple extraction of `lang` and `slug` from `entry.id`.

## 2. How It Differs From Classic React / Next.js

In Next.js, content localization usually relies on external CMS APIs or custom file-system parsing functions (`fs.readdirSync`) with gray-matter. In Astro 5, the built-in Content Layer handles schema validation via Zod, TypeScript generation, and async markdown rendering (`render(entry)`) with zero client-side JavaScript.

## 3. Common Mistakes & Anti-Patterns

A critical breaking pattern when migrating to Astro 5 is attempting to read `entry.slug` or splitting entries into completely separate collections per locale (e.g. `blogEn`, `blogEs`). Creating separate collections duplicates schemas and prevents unified querying.

### ❌ Bad Practice / Anti-Pattern

```ts
// src/pages/[lang]/blog/[...slug].astro - Broken Astro 4 legacy assumption
import { getCollection } from 'astro:content'

export async function getStaticPaths() {
  const posts = await getCollection('blog')
  return posts.map((post) => {
    // RUNTIME ERROR in Astro 5 Content Layer: post.slug is undefined!
    const [lang, ...slug] = post.slug.split('/')
    return { params: { lang, slug: slug.join('/') }, props: post }
  })
}
```

### ✅ Best Practice / Idiomatic

```ts
// src/content.config.ts - Single unified multilingual collection
import { defineCollection } from 'astro:content'
import { z } from 'astro/zod'

export const collections = {
  blog: defineCollection({
    schema: z.object({
      title: z.string(),
      description: z.string(),
      date: z.coerce.date(),
    }),
  }),
}
```

```astro
---
// src/pages/[lang]/blog/[...slug].astro - Astro 5 Content Layer idiom
import { getCollection, render } from "astro:content";

export async function getStaticPaths() {
  const posts = await getCollection("blog");
  return posts.map((post) => {
    // Astro 5 Content Layer uses post.id (e.g. "en/getting-started.md")
    const [lang, ...slugParts] = post.id.replace(/\.[^/.]+$/, "").split("/");
    return {
      params: { lang, slug: slugParts.join("/") || undefined },
      props: { post },
    };
  });
}

const { post } = Astro.props;
const { Content } = await render(post);
---
<article>
  <h1>{post.data.title}</h1>
  <Content />
</article>
```

## 4. Verification & Audit

Run type checking across your content layer:

```bash
npx astro sync && npx astro check
```

Inspect build output to ensure entries under `src/content/blog/en/` and `src/content/blog/es/` cleanly generate matching routes `/en/blog/...` and `/es/blog/...`.
