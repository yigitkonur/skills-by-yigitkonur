# Greenfield Blog (Next.js + TinaCloud + MDX)

End-to-end playbook: from `create-next-app` to a deployed blog.

## Step-by-step

### 1. Scaffold

```bash
pnpm dlx create-next-app@latest my-blog --typescript --app --src-dir --tailwind --eslint
cd my-blog
pnpm dlx @tinacms/cli@latest init
```

When prompted: `public` for assets directory; yes to sample blog collection.

### 2. Define the post collection

```typescript
// tina/config.ts
import { defineConfig } from 'tinacms'

export default defineConfig({
  branch: process.env.NEXT_PUBLIC_TINA_BRANCH ||
          process.env.VERCEL_GIT_COMMIT_REF || 'main',
  clientId: process.env.NEXT_PUBLIC_TINA_CLIENT_ID || '',
  token: process.env.TINA_TOKEN || '',
  build: { outputFolder: 'admin', publicFolder: 'public' },
  media: { tina: { mediaRoot: 'uploads', publicFolder: 'public' } },
  schema: {
    collections: [
      {
        name: 'post',
        label: 'Blog Posts',
        path: 'content/posts',
        format: 'mdx',
        ui: {
          router: ({ document }) => `/blog/${document._sys.filename}`,
        },
        fields: [
          { name: 'title', type: 'string', isTitle: true, required: true },
          { name: 'date', type: 'datetime', required: true },
          { name: 'excerpt', type: 'string', ui: { component: 'textarea' } },
          { name: 'coverImage', type: 'image' },
          { name: 'tags', type: 'string', list: true, ui: { component: 'tags' } },
          { name: 'draft', type: 'boolean' },
          { name: 'body', type: 'rich-text', isBody: true,
            templates: [
              {
                name: 'Cta',
                fields: [
                  { name: 'heading', type: 'string' },
                  { name: 'href', type: 'string' },
                ],
              },
              {
                name: 'Callout',
                fields: [
                  { name: 'tone', type: 'string', options: ['info', 'warn', 'success'] },
                  { name: 'children', type: 'rich-text' },
                ],
              },
            ],
          },
        ],
      },
    ],
  },
})
```

### 3. Create a sample post

```bash
mkdir -p content/posts
cat > content/posts/hello-world.mdx <<'EOF'
---
title: Hello World
date: '2026-05-08T00:00:00.000Z'
excerpt: My first blog post.
draft: false
---

# Hello

This is the first post.

<Cta heading="Read more" href="/blog" />

<Callout tone="info">
  This is a callout box.
</Callout>
EOF
```

### 4. Render the blog list

```tsx
// app/blog/page.tsx
import { client } from '@/tina/__generated__/client'
import Link from 'next/link'

export default async function BlogIndex() {
  const result = await client.queries.postConnection({
    sort: 'date',
    filter: { draft: { eq: false } },
    first: 50,
  })

  const posts = result.data.postConnection.edges?.map((e) => e?.node).filter(Boolean) ?? []

  return (
    <main>
      <h1>Blog</h1>
      {posts.map((post) => (
        <article key={post!._sys.filename}>
          <Link href={`/blog/${post!._sys.filename}`}>
            <h2>{post!.title}</h2>
          </Link>
          <time dateTime={post!.date}>{new Date(post!.date!).toLocaleDateString()}</time>
          <p>{post!.excerpt}</p>
        </article>
      ))}
    </main>
  )
}
```

### 5. Render individual posts

```tsx
// app/blog/[slug]/page.tsx
import { client } from '@/tina/__generated__/client'
import PostClient from './client-page'

export async function generateStaticParams() {
  const result = await client.queries.postConnection()
  return result.data.postConnection.edges
    ?.map((e) => ({ slug: e?.node?._sys.filename ?? '' }))
    .filter((p) => p.slug) ?? []
}

export default async function PostPage({
  params,
}: {
  params: Promise<{ slug: string }>
}) {
  const { slug } = await params
  const result = await client.queries.post(
    { relativePath: `${slug}.mdx` },
    { fetchOptions: { next: { revalidate: 60 } } },
  )
  return (
    <PostClient
      query={result.query}
      variables={result.variables}
      data={result.data}
    />
  )
}
```

```tsx
// app/blog/[slug]/client-page.tsx
'use client'

import { useTina, tinaField } from 'tinacms/dist/react'
import { TinaMarkdown } from 'tinacms/dist/rich-text'
import { mdxComponents } from '@/components/MdxComponents'

export default function PostClient(props: any) {
  const { data } = useTina(props)
  const post = data.post

  return (
    <article>
      <h1 data-tina-field={tinaField(post, 'title')}>{post.title}</h1>
      <time dateTime={post.date}>{new Date(post.date).toLocaleDateString()}</time>
      <div data-tina-field={tinaField(post, 'body')}>
        <TinaMarkdown content={post.body} components={mdxComponents} />
      </div>
    </article>
  )
}
```

### 6. MDX components

```tsx
// components/MdxComponents.tsx
import type { Components } from 'tinacms/dist/rich-text'
import { TinaMarkdown } from 'tinacms/dist/rich-text'

export const mdxComponents: Components<any> = {
  Cta: (props) => (
    <a href={props.href} className="cta-button">{props.heading}</a>
  ),
  Callout: (props) => (
    <div className={`callout callout-${props.tone}`}>
      {props.children && <TinaMarkdown content={props.children} components={mdxComponents} />}
    </div>
  ),
}
```

### 7. SEO

```tsx
// app/blog/[slug]/page.tsx (above the component)
import type { Metadata } from 'next'

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params
  const result = await client.queries.post({ relativePath: `${slug}.mdx` })
  const post = result.data.post

  return {
    title: post.title,
    description: post.excerpt,
    openGraph: {
      title: post.title,
      description: post.excerpt,
      images: post.coverImage ? [{ url: post.coverImage }] : [],
    },
  }
}
```

### 8. Test locally

```bash
pnpm dev
# Visit http://localhost:3000/blog
# Visit http://localhost:3000/admin/index.html
```

Edit a post, save → see it persist in `content/posts/`.

### 9. Deploy

1. Push to GitHub
2. Vercel: Import Repository
3. Sign up at app.tina.io, create project, get Client ID + Token
4. Add Vercel env vars:
   ```env
   NEXT_PUBLIC_TINA_CLIENT_ID=<...>
   TINA_TOKEN=<...>
   NEXT_PUBLIC_TINA_BRANCH=main
   ```
5. Deploy

### 10. Verify production

- `/blog` shows posts
- `/admin` allows login
- Editor saves persist to GitHub via TinaCloud

## Optional: visual editing

Add a Draft Mode route:

```typescript
// app/api/preview/route.ts
import { draftMode } from 'next/headers'
import { redirect } from 'next/navigation'

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const slug = searchParams.get('slug') || '/'
  ;(await draftMode()).enable()
  redirect(slug)
}
```

Now editors can click-to-edit on the live page.

## Common mistakes

| Mistake | Fix |
|---|---|
| Forgot `format: 'mdx'` | Body parses as plain markdown — JSX doesn't work |
| Forgot `revalidate` | Stale content on Vercel |
| Forgot `sort: 'date'` | Posts in unpredictable order |
| Forgot to filter drafts | Draft posts visible publicly |
| Skipped `generateMetadata` | SEO score drops |
