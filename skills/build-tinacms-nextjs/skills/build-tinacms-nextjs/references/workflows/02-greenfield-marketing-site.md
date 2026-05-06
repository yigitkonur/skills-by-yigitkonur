# Greenfield Marketing Site (pages + blocks pattern)

End-to-end playbook for a marketing site with editor-composable pages.

## What you build

- `pages` collection with the blocks pattern (hero, content, cta, features, etc.)
- `global` singleton for site settings
- `navigation` singleton for header/footer
- Visual editing wired up

## Steps

### 1. Scaffold

```bash
pnpm dlx create-next-app@latest my-site --typescript --app --src-dir --tailwind
cd my-site
pnpm dlx @tinacms/cli@latest init
```

### 2. Define block templates

```typescript
// tina/blocks/hero.ts
export const heroBlock = {
  name: 'hero',
  label: 'Hero Section',
  ui: {
    previewSrc: '/admin/blocks/hero.png',
    defaultItem: {
      heading: 'Your Heading Here',
      subheading: 'A compelling subheading.',
      ctaText: 'Get Started',
      ctaUrl: '#',
      style: 'centered',
    },
  },
  fields: [
    { name: 'heading', type: 'string', required: true },
    { name: 'subheading', type: 'string' },
    { name: 'backgroundImage', type: 'image' },
    {
      name: 'style', type: 'string',
      options: [
        { value: 'centered', label: 'Centered' },
        { value: 'split', label: 'Split' },
      ],
    },
    { name: 'ctaText', type: 'string' },
    { name: 'ctaUrl', type: 'string' },
  ],
}
```

Repeat for `content`, `ctaBanner`, `features`, `faq`. Place each in `tina/blocks/`.

### 3. Compose the pages collection

```typescript
// tina/collections/page.ts
import { heroBlock } from '../blocks/hero'
import { contentBlock } from '../blocks/content'
import { ctaBannerBlock } from '../blocks/cta-banner'
import { featuresBlock } from '../blocks/features'
import { faqBlock } from '../blocks/faq'
import { seoFields } from '../shared/seo-fields'

export const pageCollection = {
  name: 'page',
  label: 'Pages',
  path: 'content/pages',
  format: 'mdx',
  ui: {
    router: ({ document }) => {
      if (document._sys.filename === 'home') return '/'
      return `/${document._sys.filename}`
    },
  },
  fields: [
    { name: 'title', type: 'string', isTitle: true, required: true },
    {
      name: 'blocks',
      type: 'object',
      list: true,
      ui: {
        visualSelector: true,
        itemProps: (item) => ({ label: item?.heading || 'Section' }),
      },
      templates: [heroBlock, contentBlock, ctaBannerBlock, featuresBlock, faqBlock],
    },
    {
      name: 'seo',
      label: 'SEO',
      type: 'object',
      ui: { component: 'group' },
      fields: seoFields,
    },
  ],
}
```

### 4. Add global + navigation

See `references/schema/08-default-collection-set.md` for full schemas. Drop into `tina/collections/global.ts` and `tina/collections/navigation.ts`.

### 5. Wire `tina/config.ts`

```typescript
import { defineConfig } from 'tinacms'
import { pageCollection } from './collections/page'
import { globalCollection } from './collections/global'
import { navigationCollection } from './collections/navigation'

export default defineConfig({
  // ... env vars ...
  schema: {
    collections: [pageCollection, globalCollection, navigationCollection],
  },
})
```

### 6. Block components

```tsx
// components/blocks/Hero.tsx
import { tinaField } from 'tinacms/dist/react'

export function Hero(props: any) {
  return (
    <section className={`hero hero-${props.style}`}>
      {props.backgroundImage && (
        <img src={props.backgroundImage} alt="" data-tina-field={tinaField(props, 'backgroundImage')} />
      )}
      <h1 data-tina-field={tinaField(props, 'heading')}>{props.heading}</h1>
      <p data-tina-field={tinaField(props, 'subheading')}>{props.subheading}</p>
      {props.ctaText && (
        <a href={props.ctaUrl} className="cta-button" data-tina-field={tinaField(props, 'ctaText')}>
          {props.ctaText}
        </a>
      )}
    </section>
  )
}
```

Repeat for each block.

### 7. Block renderer

```tsx
// components/blocks/BlockRenderer.tsx
'use client'

import { tinaField } from 'tinacms/dist/react'
import { Hero } from './Hero'
import { Content } from './Content'
// ... etc.

const blockMap = {
  PageBlocksHero: Hero,
  PageBlocksContent: Content,
  PageBlocksCtaBanner: CtaBanner,
  PageBlocksFeatures: Features,
  PageBlocksFaq: Faq,
}

export function BlockRenderer({ blocks }: { blocks: any[] }) {
  return (
    <>
      {blocks?.map((block, i) => {
        const Component = blockMap[block.__typename]
        if (!Component) return null
        return (
          <section key={i} data-tina-field={tinaField(block)}>
            <Component {...block} />
          </section>
        )
      })}
    </>
  )
}
```

### 8. Page route

```tsx
// app/[slug]/page.tsx + client-page.tsx
// Same pattern as references/rendering/01-app-router-pattern.md
```

### 9. Sample home page

```bash
mkdir -p content/pages
cat > content/pages/home.mdx <<'EOF'
---
title: Welcome
blocks:
  - _template: hero
    heading: Welcome to our site
    subheading: We do amazing things
    style: centered
  - _template: features
    heading: Why choose us
    items:
      - icon: /icons/fast.svg
        title: Fast
        description: Very fast
seo:
  metaTitle: Welcome
  metaDescription: Our amazing site
---
EOF
```

### 10. Test + deploy

Same as the blog playbook.

## Common mistakes

| Mistake | Fix |
|---|---|
| Forgot `defaultItem` on blocks | Empty form when adding | Always include |
| Forgot `ui.itemProps` | "Item 0" labels | Add label function |
| `__typename` mismatch in blockMap | Block doesn't render | Match exactly |
| Forgot `ui.router` | Click-to-edit dead | Add to collection |
| Style enums with raw CSS | Design drift | Map to Tailwind/design tokens |
