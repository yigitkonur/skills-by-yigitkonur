# Block Renderer

Maps the `__typename` of each block to a React component. Drives the blocks pattern (page builder).

## The renderer

```tsx
'use client'

import { tinaField } from 'tinacms/dist/react'
import { Hero } from './blocks/Hero'
import { Content } from './blocks/Content'
import { CtaBanner } from './blocks/CtaBanner'
import { Features } from './blocks/Features'
import { Faq } from './blocks/Faq'

const blockMap: Record<string, React.ComponentType<any>> = {
  PageBlocksHero: Hero,
  PageBlocksContent: Content,
  PageBlocksCtaBanner: CtaBanner,
  PageBlocksFeatures: Features,
  PageBlocksFaq: Faq,
}

export function BlockRenderer({ blocks }: { blocks: any[] }) {
  if (!blocks) return null

  return (
    <>
      {blocks.map((block, index) => {
        const Component = blockMap[block.__typename]
        if (!Component) {
          if (process.env.NODE_ENV !== 'production') {
            console.warn('Unknown block type:', block.__typename)
          }
          return null
        }
        return (
          <section key={index} data-tina-field={tinaField(block)}>
            <Component {...block} />
          </section>
        )
      })}
    </>
  )
}
```

## `__typename` resolution

Each block template generates a unique `__typename`:

```
{CollectionName}Blocks{TemplateName}    // PascalCase

PageBlocksHero        // page collection, blocks field, hero template
PageBlocksContent
PageBlocksCtaBanner
PostBlocksGallery     // post collection, blocks field, gallery template
```

The collection and template names come from the schema:

```typescript
// Schema:
{
  name: 'page',                          // → "Page"
  fields: [
    {
      name: 'blocks',                    // → "Blocks"
      type: 'object',
      list: true,
      templates: [
        { name: 'hero', ... },           // → "Hero" → PageBlocksHero
      ],
    },
  ],
}
```

If the field is named `sections` instead of `blocks`, the typename becomes `PageSectionsHero`. Match the schema in your renderer.

## Block component pattern

```tsx
// components/blocks/Hero.tsx
import Image from 'next/image'
import { tinaField } from 'tinacms/dist/react'

type HeroProps = {
  __typename?: 'PageBlocksHero'
  heading?: string
  subheading?: string
  backgroundImage?: string
  style?: 'centered' | 'left' | 'split'
  ctaText?: string
  ctaUrl?: string
}

export function Hero(props: HeroProps) {
  return (
    <div className={`hero hero-${props.style || 'centered'}`}>
      {props.backgroundImage && (
        <Image
          src={props.backgroundImage}
          alt=""
          fill
          data-tina-field={tinaField(props, 'backgroundImage')}
        />
      )}
      <h1 data-tina-field={tinaField(props, 'heading')}>{props.heading}</h1>
      <p data-tina-field={tinaField(props, 'subheading')}>{props.subheading}</p>
      {props.ctaText && (
        <a
          href={props.ctaUrl || '#'}
          data-tina-field={tinaField(props, 'ctaText')}
          className="cta-button"
        >
          {props.ctaText}
        </a>
      )}
    </div>
  )
}
```

## Always include a fallback

```tsx
{blocks.map((block, index) => {
  const Component = blockMap[block.__typename]
  if (!Component) return null  // ← graceful fallback
  return /* ... */
})}
```

Without this, an unknown block type crashes the render. Editors can add new block types in the schema before the renderer is updated — the fallback handles that grace period.

## Block-level `data-tina-field`

Wrap each block in a `<section>` with `data-tina-field={tinaField(block)}`:

```tsx
<section key={index} data-tina-field={tinaField(block)}>
  <Component {...block} />
</section>
```

This makes the entire block clickable in edit mode — clicking the section opens that block's form. Then the per-field `data-tina-field` inside the component opens specific fields.

## Typed blockMap

```tsx
import type { ComponentType } from 'react'
import type { PageBlocksHero, PageBlocksContent } from '@/tina/__generated__/types'

const blockMap: {
  PageBlocksHero: ComponentType<PageBlocksHero>
  PageBlocksContent: ComponentType<PageBlocksContent>
  // ...
} = {
  PageBlocksHero: Hero,
  PageBlocksContent: Content,
}
```

Catches mismatches at compile time.

## Multiple block fields per page

If a page has multiple block fields (e.g. `headerBlocks` and `mainBlocks`), use separate renderers:

```tsx
<BlockRenderer blocks={page.headerBlocks} blockMap={headerBlockMap} />
<BlockRenderer blocks={page.mainBlocks} blockMap={mainBlockMap} />
```

`__typename` includes the field name, so `PageHeaderBlocksLogo` differs from `PageMainBlocksHero`.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| `blockMap` keys don't match `__typename` | Block doesn't render | Match `{Collection}{Field}{Template}` exactly |
| No fallback for unknown blocks | Render crashes when editor adds new template | Add `if (!Component) return null` |
| Forgot `data-tina-field` on block wrapper | Click-to-edit per block doesn't work | Add `data-tina-field={tinaField(block)}` on `<section>` |
| Block component without per-field `tinaField` | Click-to-edit per field doesn't work | Add `data-tina-field={tinaField(props, 'fieldName')}` |
| Schema field renamed without updating renderer | Stale `__typename` mappings | Update both together (or use generated types) |
