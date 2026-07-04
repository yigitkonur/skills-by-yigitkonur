# TypeScript Path Aliases in `tina/config.ts`

The TinaCMS config supports TypeScript path aliases (`@/*`) so you can import schema fragments cleanly. There's a build-time gotcha to know.

## The pattern

```typescript
// tina/config.ts
import { defineConfig } from 'tinacms'
import { heroBlock } from '@/tina/blocks/hero'
import { ctaBlock } from '@/tina/blocks/cta'
import { seoFields } from '@/tina/shared/seo'

export default defineConfig({
  // ...
  schema: {
    collections: [
      {
        name: 'page',
        // ...
        fields: [
          {
            name: 'blocks',
            type: 'object',
            list: true,
            templates: [heroBlock, ctaBlock],
          },
          { name: 'seo', type: 'object', fields: seoFields },
        ],
      },
    ],
  },
})
```

This makes `tina/config.ts` thin and scannable, with bulky schema definitions extracted into reusable files.

## How it works

TinaCMS bundles `tina/config.ts` with esbuild, which respects `tsconfig.json` `paths` configuration:

```jsonc
// tsconfig.json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./*"],
      "@/tina/*": ["./tina/*"],
      "@/components/*": ["./components/*"]
    }
  }
}
```

If your project already has these aliases configured for Next.js, they work in `tina/config.ts` too.

## What you can alias

Anything inside your project. For TinaCMS work, the most common aliases are:

| Alias | Resolves to | Use |
|---|---|---|
| `@/tina/blocks/*` | `tina/blocks/*` | Block template definitions |
| `@/tina/collections/*` | `tina/collections/*` | Whole collection files |
| `@/tina/shared/*` | `tina/shared/*` | Reusable field groups (SEO, CTA, etc) |
| `@/tina/__generated__/*` | `tina/__generated__/*` | Generated client + types |

## Avoid component aliases in `tina/config.ts`

```typescript
// ❌ DON'T do this in tina/config.ts
import { Hero } from '@/components/blocks/Hero'

// ✅ Instead, import from a Node-safe schema file
import { heroBlock } from '@/tina/blocks/hero'
```

`tina/config.ts` runs in Node.js (esbuild bundle) — importing React components causes `Schema Not Successfully Built` errors. Aliases are fine; what's behind them must be Node-safe.

The exception is **type-only** imports from component files:

```typescript
import type { HeroProps } from '@/components/blocks/Hero'  // ✅ types only
```

## Recommended `tina/` layout

```
tina/
├── config.ts                  ← thin top-level config
├── tina/tina-lock.json
├── blocks/
│   ├── hero.ts                ← block schema only (no React)
│   ├── content.ts
│   └── cta.ts
├── collections/
│   ├── page.ts                ← whole collection definitions
│   ├── post.ts
│   └── global.ts
├── shared/
│   ├── seo.ts                 ← reusable SEO field group
│   └── cta-fields.ts          ← reusable CTA fields
└── queries/                   ← optional custom GraphQL
```

With this layout, `tina/config.ts` becomes:

```typescript
import { defineConfig } from 'tinacms'
import { pageCollection } from '@/tina/collections/page'
import { postCollection } from '@/tina/collections/post'
import { globalCollection } from '@/tina/collections/global'

export default defineConfig({
  branch: process.env.NEXT_PUBLIC_TINA_BRANCH ||
          process.env.VERCEL_GIT_COMMIT_REF ||
          'main',
  clientId: process.env.NEXT_PUBLIC_TINA_CLIENT_ID || '',
  token: process.env.TINA_TOKEN || '',
  build: { outputFolder: 'admin', publicFolder: 'public' },
  media: { tina: { mediaRoot: 'uploads', publicFolder: 'public' } },
  schema: {
    collections: [pageCollection, postCollection, globalCollection],
  },
})
```

Easy to scan, easy to maintain.

## Block file pattern

```typescript
// tina/blocks/hero.ts
import type { Template } from 'tinacms'

export const heroBlock: Template = {
  name: 'hero',
  label: 'Hero Section',
  ui: {
    previewSrc: '/admin/blocks/hero.png',
    defaultItem: { heading: 'Your Heading', subheading: '' },
  },
  fields: [
    { name: 'heading', label: 'Heading', type: 'string', required: true },
    { name: 'subheading', label: 'Subheading', type: 'string' },
    { name: 'background', label: 'Background', type: 'image' },
  ],
}
```

Import it into the page collection:

```typescript
// tina/collections/page.ts
import type { Collection } from 'tinacms'
import { heroBlock } from '@/tina/blocks/hero'
import { contentBlock } from '@/tina/blocks/content'
import { ctaBlock } from '@/tina/blocks/cta'

export const pageCollection: Collection = {
  name: 'page',
  label: 'Pages',
  path: 'content/pages',
  format: 'mdx',
  fields: [
    { name: 'title', type: 'string', isTitle: true, required: true },
    {
      name: 'blocks',
      type: 'object',
      list: true,
      ui: { visualSelector: true },
      templates: [heroBlock, contentBlock, ctaBlock],
    },
  ],
}
```

## When path aliases don't work

If `import { heroBlock } from '@/tina/blocks/hero'` fails:

1. Check `tsconfig.json` has the alias defined
2. Check the file actually exists at the resolved path
3. Run `pnpm tinacms build --verbose` to see esbuild errors

If types resolve but the runtime fails, you may have a mismatch between TS paths and Node module resolution. Try `import { heroBlock } from '../blocks/hero'` (relative) as a fallback to confirm the issue is alias-related.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Aliasing into a file that imports React | `Schema Not Successfully Built` | Keep schema files Node-safe; type-only imports for component types |
| Alias defined in jsconfig.json but not tsconfig.json | esbuild can't resolve | Add to tsconfig.json (or both) |
| Circular alias (`@/tina/config.ts` imports from `@/tina/...` which imports back) | Build hangs or errors | Restructure — put shared types in a leaf file |
