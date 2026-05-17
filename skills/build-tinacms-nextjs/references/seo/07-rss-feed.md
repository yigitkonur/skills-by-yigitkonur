# RSS Feed

Generate an RSS feed at `/feed.xml` from your TinaCMS content.

## The pattern

```typescript
// app/feed.xml/route.ts
import { client } from '@/tina/__generated__/client'

export async function GET() {
  const global = (await client.queries.global({ relativePath: 'global.json' })).data.global
  const posts = await client.queries.postConnection({
    sort: 'date',
    last: 50,                    // most recent 50
    filter: { draft: { eq: false } },
  })

  const items =
    posts.data.postConnection.edges
      ?.map((edge) => edge?.node)
      .filter(Boolean)
      .map((post) => `
        <item>
          <title><![CDATA[${post!.title}]]></title>
          <link>${global.siteUrl}/blog/${post!._sys.filename}</link>
          <pubDate>${new Date(post!.date!).toUTCString()}</pubDate>
          <description><![CDATA[${post!.excerpt ?? ''}]]></description>
          <guid>${global.siteUrl}/blog/${post!._sys.filename}</guid>
        </item>
      `)
      .join('') ?? ''

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
      <channel>
        <title>${global.siteName}</title>
        <link>${global.siteUrl}</link>
        <description>${global.siteDescription}</description>
        <language>${global.locale?.split('_')[0] || 'en'}</language>
        <atom:link href="${global.siteUrl}/feed.xml" rel="self" type="application/rss+xml" />
        ${items}
      </channel>
    </rss>`

  return new Response(xml.trim(), {
    headers: { 'Content-Type': 'application/xml; charset=utf-8' },
  })
}
```

Visit `/feed.xml` to verify.

## Atom feed alternative

For Atom-format readers:

```typescript
const xml = `<?xml version="1.0" encoding="UTF-8"?>
  <feed xmlns="http://www.w3.org/2005/Atom">
    <title>${global.siteName}</title>
    <link href="${global.siteUrl}" />
    <link rel="self" href="${global.siteUrl}/atom.xml" />
    <updated>${new Date().toISOString()}</updated>
    <id>${global.siteUrl}/</id>
    ${items.map((post) => `
      <entry>
        <title><![CDATA[${post.title}]]></title>
        <link href="${global.siteUrl}/blog/${post.filename}" />
        <id>${global.siteUrl}/blog/${post.filename}</id>
        <updated>${new Date(post.date).toISOString()}</updated>
        <summary><![CDATA[${post.excerpt ?? ''}]]></summary>
      </entry>
    `).join('')}
  </feed>`
```

Most projects pick one (RSS or Atom). RSS is more common.

## Including full body content

For full-content RSS (some readers prefer this over excerpts):

```typescript
const items = posts.map((post) => `
  <item>
    <title><![CDATA[${post.title}]]></title>
    <link>${global.siteUrl}/blog/${post._sys.filename}</link>
    <pubDate>${new Date(post.date).toUTCString()}</pubDate>
    <description><![CDATA[${post.excerpt ?? ''}]]></description>
    <content:encoded><![CDATA[${flattenRichTextToHtml(post.body)}]]></content:encoded>
    <guid>${global.siteUrl}/blog/${post._sys.filename}</guid>
  </item>
`)
```

Add `xmlns:content="http://purl.org/rss/1.0/modules/content/"` to the `<rss>` opening tag.

`flattenRichTextToHtml` is your helper — convert AST to HTML. For complex MDX, you may need a server-side render of `<TinaMarkdown>` (more complex; consider just providing excerpt).

## Discoverability link

Add to your root layout's `<head>`:

```tsx
// app/layout.tsx
export default function Root({ children }: { children: React.ReactNode }) {
  return (
    <html>
      <head>
        <link rel="alternate" type="application/rss+xml" title="RSS" href="/feed.xml" />
      </head>
      <body>{children}</body>
    </html>
  )
}
```

Browsers and feed readers auto-discover via this link.

## Caching

```typescript
export const revalidate = 3600  // regenerate hourly
```

RSS feeds don't need to be perfectly fresh — hourly is fine.

## Validating

Paste the feed URL into https://validator.w3.org/feed/ to validate.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Missing CDATA on titles | XML invalid | Wrap in `<![CDATA[...]]>` |
| Relative URLs | Reader can't fetch | Use absolute |
| No filter for drafts | Drafts in feed | Filter `draft: { eq: false }` |
| Empty `pubDate` | Some readers skip the item | Always include |
| Missing `<guid>` | Duplicate entries on update | Use the URL or unique identifier |
| Forgot `Content-Type: application/xml` | Some readers reject | Set the header |
