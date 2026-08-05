# SEO obligations — the release gate

The corpus's central SEO finding: **a fluid, heavily cached, streaming app stays fully
crawlable — provided a small set of obligations are explicit rather than assumed.** This
file is the checklist. Any task that changes rendering, caching, routing, or metadata must
clear the relevant items before it can be marked `done`.

Every item is verified on the **deployed production origin**, never inferred from
component code or a hydrated browser view.

## The one new trap: the Cache Components bot path

Under Cache Components, humans get a static shell plus streamed holes. **Known bots skip
the shell and receive a full request-time render.** Crawlability is therefore fine *unless*
shell data is reachable only at build time — in which case humans see a healthy cached page
while bots get an error or an incomplete one.

**Release gate:** every dependency contributing crawl-relevant shell content must resolve
both at prerender time and during an anonymous request-time bot render. A healthy human
shell is not evidence of a successful crawler render — probe the deployed URL with a bot
user agent.

## Rendering strategy × what the crawler receives

| Strategy | Bot payload | Verdict | Failure condition |
|---|---|---|---|
| SSG / prerendered | Complete build-time HTML + metadata, no JS needed | Best default for stable public content | Stale canonical/`noindex`/locale baked into output |
| ISR | Same cached document; later crawls get regenerated content | Positive, with a staleness caveat | Removals/canonical changes stay stale until regeneration |
| Dynamic SSR | Request-time HTML; HTML-limited bots get blocking metadata in `<head>` | Crawlable if the request succeeds in time | Slow upstream; personalized canonical; content only from client effects |
| Dynamic + Suspense streaming | Server-streamed content is crawlable | Neutral-to-positive | Critical content fetched only in a client effect; late `notFound()` after headers sent |
| Cache Components | Bots skip the shell, get a full request-time render | Positive **if** the rerender is valid | A shell input that exists only at build time |
| Client-only / `ssr:false` primary content | Raw HTML lacks the content | Risk — avoid for search-critical content | Headings, product data, canonical, or JSON-LD only after JS runs |

## Streaming metadata and the bot carve-out

Streaming metadata ships by default for dynamically rendered pages: tags append to the
body for DOM-capable clients, while **HTML-limited bots receive blocking metadata in
`<head>`**. `htmlLimitedBots` is a stable override that **replaces** the framework's
default bot list rather than extending it — a narrow custom regex silently moves social and
search crawlers onto the streamed path.

**Default: do not override.** Change it only for a named crawler whose production response
you reproduced, then probe browser, Googlebot, and a social bot.

## Status codes under streaming

Once streaming sends headers, the HTTP status cannot change. A late `notFound()` yields
HTTP 200 plus `noindex` (may be reported as a soft 404); a late redirect can become an
in-document redirect and break social embeds.

- Check existence **before** the body begins when a literal 404 is required.
- Do durable URL migrations before rendering — config or `proxy.ts` — so crawlers get a
  real HTTP redirect.
- `redirect()` → 307 · `permanentRedirect()` → 308 (outside progressive-enhancement Server
  Action submissions, which use 303).

## The checklist

**Search identity**
- [ ] `metadataBase` set to the trusted production origin
- [ ] Every indexable page has one self-canonical URL; canonical never varies per user
- [ ] Static `metadata` for known values; `generateMetadata` only for request-dependent ones
- [ ] `params` / `searchParams` awaited (async in 16)
- [ ] Nested `openGraph` / `twitter` / `robots` objects rebuilt explicitly — merging is shallow
- [ ] Title template semantics verified (`default` present where `template` is used)

**Bot behaviour**
- [ ] Default `htmlLimitedBots` retained unless a named crawler issue was reproduced
- [ ] Three response paths tested: browser UA, Googlebot, an HTML-limited social bot
- [ ] For the HTML-limited path, title/canonical/OG/Twitter/robots/hreflang are in `<head>`

**Crawlable content**
- [ ] Primary headings, article/product text, navigation, canonical result sets are
      server-rendered — never sourced solely from `useEffect` or third-party JS
- [ ] No primary content behind `next/dynamic({ ssr: false })`
- [ ] Under Cache Components, every crawl-relevant shell dependency is request-time reachable
- [ ] Bot path probed directly on the deployed URL
- [ ] Hidden `<Activity>` trees don't duplicate crawl-relevant headings

**Missing pages and redirects**
- [ ] `notFound()` for absent resources; existence checked before streaming when a literal
      404 matters
- [ ] Error/missing routes carry `noindex` and don't inherit an indexable canonical
- [ ] 307 for temporary, 308 for durable moves; migrations happen before render
- [ ] Redirect and canonical change ship together

**Robots and sitemap**
- [ ] `robots.ts` with intentional rules and the production sitemap URL
- [ ] `sitemap.ts` contains only canonical, indexable production URLs
- [ ] `generateSitemaps()` above 50,000 URLs, awaiting the async `id`
- [ ] `/robots.txt`, `/sitemap.xml`, icons, and OG routes excluded from broad `proxy.ts` matchers
- [ ] Preview/outdated deployments keep their `x-robots-tag: noindex`

**Multi-locale**
- [ ] Every public locale has a distinct crawlable URL (prefix `always`/`as-needed` for
      indexable content; a URL-less strategy is for non-indexed apps only)
- [ ] `<html lang>` reflects the served locale, verified in raw HTML per locale
- [ ] `alternates.languages` emitted in metadata **and** sitemap; reciprocal, including self
- [ ] Each locale self-canonicals — never collapse locales onto one canonical

**Structured data and images**
- [ ] JSON-LD rendered as `<script type="application/ld+json">` from a Server Component,
      sanitized (`JSON.stringify(data).replace(/</g,'\\u003c')`), matching visible facts
- [ ] Meaningful `alt` on content images; `alt=""` only for decorative
- [ ] Remote and OG images publicly fetchable (the default loader forwards no auth headers)
- [ ] The LCP image uses exactly one intentional early-load signal
- [ ] OG/Twitter images absolute via `metadataBase`, with dimensions and type

**Deployment**
- [ ] Verified on the production origin, not localhost or a preview
- [ ] After a bundler migration, crawler-visible output compared for equivalence
- [ ] CWV measured at p75 — but never treated as proof of crawlability

## Minimum release evidence

Raw production HTML for one static/ISR page, one dynamic/streamed page, one Cache
Components page, and one localized page · browser + Googlebot + social-bot responses ·
literal status and robots behaviour for a missing resource and for both redirect kinds ·
`/robots.txt`, `/sitemap.xml`, one localized sitemap entry, one OG image response ·
validated JSON-LD and one image alt/LCP inspection.
