# Default Collection Set

The four collections that cover ~90% of marketing/content sites. Start here, add more only when needed.

## The four

| Collection | Type | Purpose |
|---|---|---|
| `pages` | Folder, blocks pattern | Marketing pages, landing pages |
| `posts` | Folder, MDX body | Blog posts |
| `global` | Singleton | Site name, defaults, global SEO |
| `navigation` | Singleton | Main nav + footer links |

## `pages` collection

```typescript
// tina/collections/page.ts
import type { Collection } from 'tinacms'
import { heroBlock } from '@/tina/blocks/hero'
import { contentBlock } from '@/tina/blocks/content'
import { ctaBannerBlock } from '@/tina/blocks/cta-banner'
import { featuresBlock } from '@/tina/blocks/features'
import { faqBlock } from '@/tina/blocks/faq'
import { seoFields } from '@/tina/shared/seo-fields'

export const pageCollection: Collection = {
  name: 'page',
  label: 'Pages',
  path: 'content/pages',
  format: 'mdx',
  ui: {
    router: ({ document }) => {
      if (document._sys.filename === 'home') return '/'
      return `/${document._sys.filename}`
    },
    filename: {
      readonly: false,
      slugify: (values) =>
        values.title?.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '') || 'untitled',
    },
  },
  defaultItem: () => ({ title: 'New Page', blocks: [] }),
  fields: [
    { name: 'title', label: 'Title', type: 'string', isTitle: true, required: true },
    {
      name: 'blocks',
      label: 'Page Sections',
      type: 'object',
      list: true,
      ui: {
        visualSelector: true,
        itemProps: (item) => ({
          label: item?.heading || item?.title || 'Section',
        }),
      },
      templates: [heroBlock, contentBlock, ctaBannerBlock, featuresBlock, faqBlock],
    },
    {
      name: 'seo',
      label: 'SEO & Social',
      type: 'object',
      ui: { component: 'group' },
      fields: seoFields,
    },
  ],
}
```

## `posts` collection

```typescript
// tina/collections/post.ts
import type { Collection } from 'tinacms'
import { seoFields } from '@/tina/shared/seo-fields'

export const postCollection: Collection = {
  name: 'post',
  label: 'Blog Posts',
  path: 'content/posts',
  format: 'mdx',
  ui: {
    router: ({ document }) => `/blog/${document._sys.filename}`,
    filename: {
      readonly: false,
      slugify: (values) => {
        const date = values.date || new Date().toISOString()
        const slug = values.title?.toLowerCase().replace(/\s+/g, '-') || 'untitled'
        return `${date.split('T')[0]}-${slug}`
      },
    },
    beforeSubmit: async ({ values }) => ({
      ...values,
      modifiedDate: new Date().toISOString(),
    }),
  },
  defaultItem: () => ({
    title: 'New Post',
    date: new Date().toISOString(),
    draft: true,
  }),
  fields: [
    { name: 'title', label: 'Title', type: 'string', isTitle: true, required: true },
    { name: 'date', label: 'Published Date', type: 'datetime', required: true },
    { name: 'excerpt', label: 'Excerpt', type: 'string', ui: { component: 'textarea' } },
    { name: 'coverImage', label: 'Cover Image', type: 'image' },
    { name: 'tags', label: 'Tags', type: 'string', list: true },
    { name: 'draft', label: 'Draft', type: 'boolean', description: 'If checked, post is hidden from production' },
    {
      name: 'body',
      label: 'Body',
      type: 'rich-text',
      isBody: true,
      // Add MDX templates here for embeddable components — see references/field-types/09-rich-text-mdx.md
      templates: [
        // { name: 'Cta', fields: [...] },
        // { name: 'Callout', fields: [...] },
      ],
    },
    {
      name: 'modifiedDate',
      type: 'datetime',
      ui: { component: 'hidden' },
    },
    {
      name: 'seo',
      label: 'SEO & Social',
      type: 'object',
      ui: { component: 'group' },
      fields: seoFields,
    },
  ],
}
```

## `global` singleton

```typescript
// tina/collections/global.ts
import type { Collection } from 'tinacms'

export const globalCollection: Collection = {
  name: 'global',
  label: 'Global Settings',
  path: 'content/global',
  format: 'json',
  ui: {
    global: true,
    allowedActions: { create: false, delete: false },
  },
  fields: [
    { name: 'siteName', label: 'Site Name', type: 'string', required: true },
    { name: 'siteDescription', label: 'Site Description', type: 'string', ui: { component: 'textarea' } },
    { name: 'siteUrl', label: 'Site URL', type: 'string', required: true },
    { name: 'defaultOgImage', label: 'Default Social Image', type: 'image' },
    { name: 'logo', label: 'Logo', type: 'image' },
    { name: 'logoDark', label: 'Logo (Dark Mode)', type: 'image' },
    { name: 'favicon', label: 'Favicon', type: 'image' },
    { name: 'themeColor', label: 'Theme Color', type: 'string', description: 'Hex e.g. #0a0a0a' },
    { name: 'twitterHandle', label: 'Twitter/X Handle', type: 'string', description: 'Without @' },
    { name: 'titleTemplate', label: 'Title Template', type: 'string', description: 'e.g. "%s | Site Name"' },
    { name: 'locale', label: 'Default Locale', type: 'string', description: 'e.g. en_US' },
    {
      name: 'socialLinks',
      label: 'Social Links',
      type: 'object',
      list: true,
      ui: {
        itemProps: (item) => ({ label: item?.platform || 'Social' }),
      },
      fields: [
        { name: 'platform', label: 'Platform', type: 'string',
          options: ['twitter', 'github', 'linkedin', 'youtube', 'instagram', 'mastodon'],
        },
        { name: 'url', label: 'URL', type: 'string' },
      ],
    },
  ],
}
```

The single document lives at `content/global/global.json` (or whatever the singleton file is named).

## `navigation` singleton

```typescript
// tina/collections/navigation.ts
import type { Collection } from 'tinacms'

export const navigationCollection: Collection = {
  name: 'navigation',
  label: 'Navigation',
  path: 'content/navigation',
  format: 'json',
  ui: {
    global: true,
    allowedActions: { create: false, delete: false },
  },
  fields: [
    {
      name: 'mainNav',
      label: 'Main Navigation',
      type: 'object',
      list: true,
      ui: {
        itemProps: (item) => ({ label: item?.label || 'Item' }),
      },
      fields: [
        { name: 'label', label: 'Label', type: 'string', required: true },
        { name: 'url', label: 'URL', type: 'string', required: true },
        {
          name: 'children',
          label: 'Submenu',
          type: 'object',
          list: true,
          ui: {
            itemProps: (item) => ({ label: item?.label || 'Submenu item' }),
          },
          fields: [
            { name: 'label', label: 'Label', type: 'string' },
            { name: 'url', label: 'URL', type: 'string' },
          ],
        },
      ],
    },
    {
      name: 'footerNav',
      label: 'Footer Navigation',
      type: 'object',
      list: true,
      ui: {
        itemProps: (item) => ({ label: item?.heading || 'Column' }),
      },
      fields: [
        { name: 'heading', label: 'Column Heading', type: 'string' },
        {
          name: 'links',
          label: 'Links',
          type: 'object',
          list: true,
          ui: { itemProps: (item) => ({ label: item?.label || 'Link' }) },
          fields: [
            { name: 'label', label: 'Label', type: 'string' },
            { name: 'url', label: 'URL', type: 'string' },
          ],
        },
      ],
    },
    { name: 'footerCopyright', label: 'Copyright Notice', type: 'string' },
  ],
}
```

⚠️ Note: this uses `children` as a field name inside the navigation submenu. **`children` is reserved inside rich-text templates** but works fine inside regular `object` fields. If you see schema errors, rename to `submenu` or `items`.

## Wiring into `tina/config.ts`

```typescript
import { defineConfig } from 'tinacms'
import { pageCollection } from '@/tina/collections/page'
import { postCollection } from '@/tina/collections/post'
import { globalCollection } from '@/tina/collections/global'
import { navigationCollection } from '@/tina/collections/navigation'

export default defineConfig({
  branch: process.env.NEXT_PUBLIC_TINA_BRANCH ||
          process.env.VERCEL_GIT_COMMIT_REF ||
          'main',
  clientId: process.env.NEXT_PUBLIC_TINA_CLIENT_ID || '',
  token: process.env.TINA_TOKEN || '',
  build: { outputFolder: 'admin', publicFolder: 'public' },
  media: { tina: { mediaRoot: 'uploads', publicFolder: 'public' } },
  schema: {
    collections: [pageCollection, postCollection, globalCollection, navigationCollection],
  },
})
```

## When to add more collections

Add a new collection when:

- A document type doesn't fit the existing four
- You need a separate URL path / router
- The schema would otherwise become unwieldy

Common additions:

| Collection | When |
|---|---|
| `authors` | Multi-author blog |
| `categories` | Categorized blog/docs |
| `docs` | Documentation site (separate from blog) |
| `caseStudies` | Marketing site with case studies as a content type |
| `events` | Calendar/events page |
| `team` | Team members (could also be a global field) |
| `notFound` | Custom 404 page (singleton) |

Don't add collections speculatively — they cost editor cognitive load.

## Initial content seed

To make the admin immediately usable, seed at least one document per collection:

```bash
mkdir -p content/pages content/posts content/global content/navigation

# Sample home page
cat > content/pages/home.mdx <<'EOF'
---
title: Welcome
blocks:
  - _template: hero
    heading: Welcome
    subheading: This is a sample home page
seo:
  metaTitle: Welcome
  metaDescription: Sample home page
---
EOF

# Singletons
echo '{"siteName":"My Site","siteUrl":"https://example.com","siteDescription":"A site"}' > content/global/global.json
echo '{"mainNav":[{"label":"Home","url":"/"}],"footerNav":[]}' > content/navigation/navigation.json
```

After seeding, `pnpm dev` and the admin should show all four collections with content.
