# JSON-LD Structured Data

Schema.org markup that drives Google rich results — stars, breadcrumbs, FAQ accordions in search results.

## Add per page type

| Schema | Where | Purpose |
|---|---|---|
| `Organization` | Every page | Logo, name, url, social links |
| `WebSite` | Homepage | Sitelinks search box |
| `WebPage` | All pages | Page name, description, dateModified |
| `Article` / `BlogPosting` | Blog posts | Headline, author, dates, image |
| `BreadcrumbList` | Pages with depth > 1 | Breadcrumb trail |
| `FAQPage` | Pages with FAQ blocks | FAQ rich result |

## Inject as `<script type="application/ld+json">`

```tsx
// In a Server Component:
const orgJsonLd = {
  '@context': 'https://schema.org',
  '@type': 'Organization',
  name: global.siteName,
  url: global.siteUrl,
  logo: `${global.siteUrl}${global.logo}`,
  sameAs: global.socialLinks?.map((l: any) => l.url) ?? [],
}

return (
  <>
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(orgJsonLd) }}
    />
    {/* page content */}
  </>
)
```

## `Organization`

```typescript
const orgJsonLd = {
  '@context': 'https://schema.org',
  '@type': 'Organization',
  name: global.siteName,
  url: global.siteUrl,
  logo: `${global.siteUrl}${global.logo}`,
  sameAs: [
    'https://twitter.com/yourhandle',
    'https://github.com/yourorg',
    // ... social links from global
  ],
}
```

Add to root layout so it appears on every page.

## `WebSite` (homepage only)

```typescript
const websiteJsonLd = {
  '@context': 'https://schema.org',
  '@type': 'WebSite',
  name: global.siteName,
  url: global.siteUrl,
  potentialAction: {
    '@type': 'SearchAction',
    target: {
      '@type': 'EntryPoint',
      urlTemplate: `${global.siteUrl}/search?q={search_term_string}`,
    },
    'query-input': 'required name=search_term_string',
  },
}
```

This adds a sitelinks search box in Google results — only effective on the homepage.

## `WebPage` (all pages)

```typescript
const pageJsonLd = {
  '@context': 'https://schema.org',
  '@type': 'WebPage',
  name: page.title,
  description: page.seo?.metaDescription,
  url: `${global.siteUrl}/${slug}`,
  dateModified: page._sys.lastModified,
}
```

## `Article` / `BlogPosting`

```typescript
const articleJsonLd = {
  '@context': 'https://schema.org',
  '@type': 'BlogPosting',
  headline: post.title,
  description: post.excerpt,
  image: [`${global.siteUrl}${post.coverImage}`],
  datePublished: post.date,
  dateModified: post.modifiedDate || post.date,
  author: {
    '@type': 'Person',
    name: post.author?.name,
    url: post.author?.url,
  },
  publisher: {
    '@type': 'Organization',
    name: global.siteName,
    logo: { '@type': 'ImageObject', url: `${global.siteUrl}${global.logo}` },
  },
}
```

## `BreadcrumbList`

```typescript
const breadcrumbsJsonLd = {
  '@context': 'https://schema.org',
  '@type': 'BreadcrumbList',
  itemListElement: [
    { '@type': 'ListItem', position: 1, name: 'Home', item: global.siteUrl },
    { '@type': 'ListItem', position: 2, name: 'Docs', item: `${global.siteUrl}/docs` },
    { '@type': 'ListItem', position: 3, name: post.title, item: `${global.siteUrl}/docs/${post._sys.filename}` },
  ],
}
```

## `FAQPage`

For pages with an FAQ block:

```typescript
const faqJsonLd = {
  '@context': 'https://schema.org',
  '@type': 'FAQPage',
  mainEntity: faqBlock.items?.map((item: any) => ({
    '@type': 'Question',
    name: item.question,
    acceptedAnswer: {
      '@type': 'Answer',
      text: item.answer,
    },
  })),
}
```

## Helper for clean injection

```tsx
function JsonLd({ data }: { data: object }) {
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }}
    />
  )
}

// Use:
<>
  <JsonLd data={orgJsonLd} />
  <JsonLd data={pageJsonLd} />
  {/* page content */}
</>
```

## Validating

After deploy, paste a URL into Google Rich Results Test (https://search.google.com/test/rich-results) — it shows which schema types Google detects and any errors.

## Don't fake reviews / breadcrumbs

Google manually penalizes sites that include schema for things they don't show — fake review aggregates, breadcrumbs that don't exist visually. Schema must reflect what users see.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Missing `@context` | Schema invalid | Always include `'@context': 'https://schema.org'` |
| Relative image URLs | Schema invalid | Use absolute URLs |
| `BlogPosting` without `image` | No rich result | Always include image |
| Multiple top-level types in one script | Some search engines miss them | Use multiple `<script>` tags |
| Schema doesn't match visible content | Manual penalty risk | Match what users see |
