# Detect: seo-metadata

**Corpus lineage:** seo-metadata/00-overview-feature-inventory.md,
seo-metadata/02-fluidity-crawlability.md, seo-metadata/07-pitfalls-anti-patterns.md,
seo-metadata/08-version-lockin-seo-vercel-practitioner.md

**The headline finding in this domain:** under Cache Components, human browsers get a
static shell with fallbacks, but known bots skip the shell entirely and receive a full
request-time render. Crawlability is therefore *fine* unless a shell dependency is only
reachable at build time — then humans see a fast, healthy cached page while bots get an
error or incomplete content. This is a release gate, not an ordinary code finding — see
`references/gating/seo-obligations.md` for the full checklist this domain's findings must
align with. Do not duplicate that checklist here; cite it.

## Applicability gate

| Feature / config key | Introduced | Requires | Removed-in | Gate rule |
|---|---|---|---|---|
| Cache Components crawler full-render path | stable, current 16.3 docs | `cacheComponents: true` (owned by `rendering-strategy-caching`) | n/a | NOT APPLICABLE if the capability probe shows `cacheComponents` absent — crawlability then follows the classic SSG/ISR/dynamic/Suspense table instead. If `present`, every finding under "Cache Components bot path" below is live; the release gate in `references/gating/seo-obligations.md` applies. |
| `export const metadata: Metadata` / `generateMetadata` | v13.2.0 | Server Component | n/a | Always applicable. A segment cannot export both — BLOCKED (build error) if it does. |
| `params: Promise<…>` / `searchParams: Promise<…>` | breaking async change v16.0.0 | Next.js ≥16 | n/a | On an install ≥16, sync destructuring (`params.slug` without `await`) is a type/runtime error — **critical**. Below 16, sync access is the correct, current API — do not flag it. Probe the installed version first. |
| `ResolvingMetadata` | v13.2.0 | `generateMetadata`'s second argument | n/a | Always applicable; informational if unused where parent OG images should be extended, not replaced. |
| automatic `fetch` memoization + `React.cache` dedup | framework default (fetch); React 19 (`cache()`) | React ≥19 for `cache()`, Server Components only | n/a | `fetch` dedup needs no gate. `React.cache` is BLOCKED on React <19 — this primitive is owned by `data-fetching-patterns`; this domain only checks whether `generateMetadata` and the page share one wrapped data function. |
| streaming metadata | v15.2.0 | dynamically rendered route | n/a | Default-on ≥15.2.0. NOT APPLICABLE (no streaming occurs) for prerendered/ISR pages — metadata resolves at build time there. |
| `htmlLimitedBots` (`RegExp`, `next.config.ts`) | v15.2.0 | — | n/a | Probed key (`references/gating/capability-probe.md`). `absent` below 15.2.0 → NOT APPLICABLE. `present` and custom-set → **overrides, never extends**, the framework default list; treat any custom value as a finding unless documented and tested. |
| `metadataBase: URL` | Metadata API, v13.2.0 window | root layout (or per-origin route group) | n/a | Missing while any relative canonical/OG/Twitter URL field exists → build error or malformed output — **critical**. |
| `title.default` / `title.template` / `title.absolute` | Metadata API | — | n/a | `template` without a sibling `default` is a documented misconfiguration — **major** (silent fallback/type issue). |
| `alternates.canonical` / `alternates.languages` | Metadata API | — | n/a | Always applicable. Personalized/session-derived canonical is a **major** finding regardless of version. |
| `openGraph` / `twitter` / `robots` | Metadata API | — | n/a | Nested objects **shallowly merge** across segments — a child redefining one nested key silently erases parent siblings. |
| `viewport: Viewport` export / `generateViewport` | v14.0.0 | Server Component; cannot coexist with `themeColor`/`colorScheme`/`viewport` inside `metadata` | n/a | `themeColor`/`colorScheme`/`viewport` nested inside the `metadata` object on an install ≥14 → deprecated location, **minor** — migrate to the `viewport` export, per `references/gating/version-matrix.md`. |
| `app/sitemap.ts` / `generateSitemaps()` | v13.3.0; locale alternates v14.2.0; `id` Promise v16.0.0 | — | n/a | Missing on an indexable content/e-commerce archetype → **major**. `id` accessed synchronously on an install ≥16 → **critical** (type error). Above 50,000 URLs with no `generateSitemaps()` split → **major**. |
| `app/robots.ts` | v13.3.0; `other` field v16.3.0 | — | n/a | Missing on an indexable archetype → **major**. `other` used with no target-engine documentation → **minor**, unvalidated pass-through. |
| `app/manifest.ts`, icon/OG file conventions | v13.3.0; generated params are Promises in v16 | — | n/a | Sync param access in `opengraph-image`/`icon`/`generateImageMetadata` on install ≥16 → **critical**. Otherwise informational file-convention gaps. |
| `ImageResponse` | moved `next/server` → `next/og` in v14.0.0 | — | n/a | Import from `next/server` on any current install → **critical**, stale module path, per `references/gating/version-matrix.md`. |
| native JSON-LD `<script type="application/ld+json">` | current recommended pattern | Server Component | n/a | Rendered via `next/script`, a Client Component, or a `useEffect` → **major** — docs explicitly say JSON-LD is structured data, not executable code. |
| `notFound()` / `redirect()` (307) / `permanentRedirect()` (308) | v13.0.0 | `next/navigation` | n/a | Called after streaming has plausibly begun where a literal status code is required → **major** (soft-404 / broken social embed), not critical — the framework's documented `noindex` fallback still fires. |

## Detection commands

Read-only only. Prefer `rg`; fall back to `grep -rn` if needed. Every command maps 1:1 to a
gate row or a pitfall signature.

```bash
# 1. Both metadata and generateMetadata exported from the same file — build error
rg -n -U 'export const metadata[^\n]*\n(?s).{0,400}?export (async )?function generateMetadata' --glob 'app/**/{page,layout}.tsx' <target-repo-root>
```

```bash
# 2. Sync params/searchParams destructuring inside generateMetadata (install >=16 finding)
rg -n -B3 'function generateMetadata' --glob 'app/**/*.tsx' <target-repo-root> | rg -B3 '\bparams\.\w+' | rg -v 'await params'
```

```bash
# 3. metadataBase presence in the root layout
rg -n 'metadataBase' --glob 'app/layout.tsx' <target-repo-root> || echo "metadataBase not found in app/layout.tsx"
```

```bash
# 4. Personalized/dynamic canonical — cookies/headers/session feeding alternates.canonical
rg -n -B8 'alternates' --glob '*.{ts,tsx}' <target-repo-root> | rg -B8 'canonical' | rg 'cookies\(\)|headers\(\)|session'
```

```bash
# 5. Custom htmlLimitedBots override — replaces, never extends, the default bot list
rg -n 'htmlLimitedBots' --glob 'next.config.*' <target-repo-root>
```

```bash
# 6. Client-only or ssr:false primary content — invisible to non-JS render passes
rg -n "next/dynamic\(.*ssr:\s*false" --glob '*.{ts,tsx}' <target-repo-root>
```

```bash
# 7. Missing sitemap.ts / robots.ts on an indexable app
test -f <target-repo-root>/app/sitemap.ts || echo "app/sitemap.ts missing"
test -f <target-repo-root>/app/robots.ts || echo "app/robots.ts missing"
```

```bash
# 8. Stale ImageResponse import path — moved to next/og in v14
rg -n "from ['\"]next/server['\"]" --glob '*.{ts,tsx}' <target-repo-root> | rg -B0 -A0 '' | xargs -I{} true; rg -n -B1 "ImageResponse" --glob '*.{ts,tsx}' <target-repo-root> | rg "next/server"
```

```bash
# 9. JSON-LD injected via next/script or a client effect instead of a native server script tag
rg -n "ld\+json" --glob '*.{ts,tsx}' <target-repo-root> -B5 | rg "next/script|useEffect"
```

```bash
# 10. Broad proxy.ts matcher not excluding metadata-file routes
rg -n -A10 'export const config' --glob 'proxy.ts' <target-repo-root> | rg -v 'robots.txt|sitemap.xml|favicon|opengraph-image|twitter-image'
```

```bash
# 11. Cache Components bot-path candidate — build-time-only local reads inside a cached/static
# scope; a MATCH IS NOT ITSELF A FINDING — it is a candidate requiring a live bot-UA probe
# against the deployed origin per references/gating/seo-obligations.md.
rg -n "readFileSync\(|require\(['\"]\..*\.json['\"]\)" --glob 'app/**/*.{ts,tsx}' <target-repo-root>
```

```bash
# 12. Late notFound()/redirect() — called from a component nested below a Suspense boundary
# in the same route tree (heuristic: file imports Suspense AND calls notFound/redirect)
rg -n -l 'Suspense' --glob 'app/**/*.tsx' <target-repo-root> | xargs -I{} sh -c "rg -Hn 'notFound\(\)|redirect\(|permanentRedirect\(' {}"
```

```bash
# 13. Live bot-path verification for a Cache Components shell (run against the deployed origin,
# not localhost) — the actual release-gate check, not a repo grep
curl -s -A "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)" https://<deployed-origin>/<route> | rg -E '<title|og:title|<h1'
```

## Domain severity rubric

- **critical**
  - Both `metadata` and `generateMetadata` exported from the same route segment — build error.
  - `metadata`/`generateMetadata` placed in a Client Component (`'use client'` above the export) — content invisible to non-JS render passes.
  - Sync `params`/`searchParams` access (no `await`) on an install ≥16, including generated `opengraph-image`/`icon`/`generateSitemaps` `id` — type/runtime error.
  - `ImageResponse` imported from `next/server` — stale module path.

- **major**
  - Missing `metadataBase` while relative canonical/OG/Twitter URLs exist.
  - Primary/crawl-critical content sourced only from `next/dynamic({ ssr: false })` or a client `useEffect` — invisible to Google's rendered-HTML index pass.
  - Custom `htmlLimitedBots` that narrows/replaces the default list without including it — moves social/search bots onto the streamed body path.
  - Missing `sitemap.ts` or `robots.ts` on an indexable archetype.
  - Personalized/session-derived canonical URL.
  - `notFound()`/`redirect()` invoked after the stream has plausibly begun where a literal status is required — soft-404 or broken social embed risk.
  - JSON-LD rendered via `next/script` or a client effect instead of a native server `<script>` tag.
  - A confirmed (bot-UA-probed) Cache Components shell dependency that resolves for humans but errors or serves incomplete content for a bot request.

- **minor**
  - `themeColor`/`colorScheme`/`viewport` nested inside the `metadata` object instead of the `viewport` export — deprecated location, still functional on most installs.
  - `title.template` set with no sibling `title.default`.
  - `robots.other` used with no target-engine documentation.
  - Hand-written hreflang entries not derived from a shared locale list (cross-reference `instant-i18n-locale-switching`).
  - Above 50,000 sitemap URLs with no `generateSitemaps()` split.

- **informational**
  - Private/authenticated routes correctly `noindex` and absent from the sitemap — this is the correct pattern, not a finding.
  - A deliberately overridden `htmlLimitedBots` value with an adjacent comment naming the tested crawler and reproduction.
  - A grep match for build-time-only reads under Cache Components, pending the live bot-UA probe — do not promote to `major`/`critical` from static analysis alone.

## False-positive filters

- **Private/authenticated routes with `noindex` and no sitemap entry are correct, not a finding.** The SEO obligations checklist requires this; do not propose adding them to the sitemap.
- **A documented `htmlLimitedBots` override is informational, not a finding.** Only file a finding when the override lacks a rationale comment or wasn't tested against the three UA classes (browser, Googlebot, an HTML-limited social bot).
- **Test files are excluded** — `*.test.tsx`, `*.spec.tsx`, `__tests__/**`, `e2e/**`.
- **Comments/docstrings are not live usage** — a `next/server` string inside a comment explaining a past bug is not command-8's finding.
- **`ssr:false` on genuinely non-SEO-critical interactive widgets** (a chat launcher, an in-page map) is not a finding — only primary headings, article/product text, canonical-bearing content, or JSON-LD sourced this way qualifies.
- **A `notFound()`/`redirect()` call at the very top of a route file, before any await of slow data or any Suspense boundary, is not the late-call pitfall** — command 12 is a heuristic; open the file and confirm the call is reachable only after streaming has plausibly started.
- **A build-time-read match under Cache Components (command 11) is a candidate, never a finding on its own.** File it `informational` until command 13's live bot-UA probe against the deployed origin confirms a failure or incomplete render — never claim `major`/`critical` from the grep alone.
- **A repo with no multi-locale plan has no hreflang obligation** — do not propose `alternates.languages` on a genuinely single-locale site.

## Evidence format — what each finding file must contain

Every finding the audit subagent writes under `findings/seo-metadata/` must include:
- `file:line` (exact)
- literal matched text (copied from the `rg`/`grep`/`curl` output)
- which gate row or pitfall signature it maps to
- severity
- one-line why-this-matters (drawn from the corpus prose above)
- suggested fix recipe section name from `references/fix/seo-metadata.md`
- for any Cache Components bot-path finding: the `cacheComponents` probe verdict and whether command 13's live bot-UA probe was run (a `major`/`critical` verdict requires it — a grep-only candidate stays `informational`)

## Pitfall signatures

| Failure signature | Cause | Fix direction | Recipe section |
|---|---|---|---|
| Title/canonical/JSON-LD absent from raw HTML; content appears only after `useEffect` | Metadata exported from a Client Component, or SEO content fetched/rendered client-only | Keep `page.tsx`/`layout.tsx` server-side; export metadata there | Gold-standard root layout metadata |
| Promise property-access/type error, wrong slug/canonical, build failure | `const slug = params.slug` instead of `const { slug } = await params` on install ≥16 | Await `params`/`searchParams`; update the `Props` type to `Promise<...>` | `generateMetadata` with async params + dedup |
| Compile/build error | Both `metadata` and `generateMetadata` exported from one segment | Choose one; move static fields to a parent layout if the child needs `generateMetadata` | Gold-standard root layout metadata |
| A child `openGraph.title` erases parent `description`/`images`; child `robots` erases parent Googlebot directives | Nested metadata objects are shallowly merged, not deep-merged | Import a shared nested object, or explicitly extend `(await parent).openGraph?.images` | `generateMetadata` with async params + dedup |
| Build error for URL-based metadata, or malformed output | Relative canonical/OG URL with no `metadataBase` | Set `metadataBase: new URL('https://production-origin')` in the root layout | Gold-standard root layout metadata |
| Template has no effect on its own segment; build/type issue on children | Misused `title.template`/`title.default` pairing | Define `{ default, template }` in a layout; plain title in child pages; `title.absolute` to bypass | Gold-standard root layout metadata |
| Social bot receives streamed body metadata and misses tags | Custom `htmlLimitedBots` regex contains only the new crawler, silently dropping the framework default list | Retain the default; add the new agent alongside it, never replace wholesale | Streaming metadata & `htmlLimitedBots` |
| Browser preview looks correct; Twitter/Slack/LinkedIn preview is blank | Testing only browser UA or default `curl`, never an HTML-limited bot UA | Test browser, Googlebot, and an HTML-limited bot (e.g. Twitterbot) independently | Streaming metadata & `htmlLimitedBots` |
| HTTP 200 + not-found UI; Search Console/link checkers report soft 404 | `notFound()` called after streaming headers were already sent | Check resource existence before the body begins streaming when a literal 404 is required | Existence-before-streaming ordering |
| Client meta-redirect instead of HTTP 307/308; social bot gets no/wrong embed | `redirect()` called from inside a slow, already-streaming `generateMetadata` | Perform canonical/migration redirects in `next.config.ts` or `proxy.ts` before rendering | Existence-before-streaming ordering |
| Untrusted string closes the JSON script and injects markup | Plain `JSON.stringify(data)` with no sanitization | `.replace(/</g, '\\u003c')` at minimum, plus project-approved sanitization | JSON-LD component with sanitization |
| Module error from a stale import; blank image; build exceeds 500 KB | `ImageResponse` imported from `next/server`; `display: grid` used; oversized fonts/assets | `import { ImageResponse } from 'next/og'`; flexbox only; trim assets | Dynamic OG image via `ImageResponse` |
| Metadata is correct but the social preview shows no image | OG route disallowed in `robots.txt`, authenticated, or private-network-only | Allow the route in `robots.ts`; confirm public fetchability with the target UA | `robots.ts` + metadata-file exclusions |
| `/robots.txt`, `/sitemap.xml`, or an icon/OG URL redirects or auths unexpectedly | Broad `proxy.ts` matcher intercepting metadata file routes | Exclude metadata file routes from the matcher | `robots.ts` + metadata-file exclusions |
| Human browser gets a fast static shell; Googlebot request errors or gets incomplete content | Cache Components bots skip the shell and rerender fully at request time; a shell dependency exists only at build time | Ensure every shell dependency is request-time-reachable; verify with a bot-UA probe on the deployed origin | (this domain's release gate — see `references/gating/seo-obligations.md`) |

## Cross-domain interactions

1. If the capability probe shows `cacheComponents` absent, downgrade every Cache Components bot-path finding to NOT APPLICABLE — crawlability then follows the classic SSG/ISR/dynamic/Suspense table in `references/gating/seo-obligations.md` instead.
2. `<html lang>` correctness and reciprocal `alternates.languages` are primarily owned by `instant-i18n-locale-switching` — file there when a locale-routing layer exists. This domain only flags the single-locale/no-i18n case where visible content language and `<html lang>` disagree.
3. OG source-image sizing/optimization belongs to `image-optimization`; this domain only flags reachability/robots-blocking of the OG endpoint itself.
4. Durable canonical/URL migrations and their 308 redirects interact with `vercel-platform-deployment`'s `proxy.ts`/`next.config.ts` ownership — sequence redirect-map changes there, not as an ad hoc in-render fix here.

## Reference pointer

Fix recipes for this domain live in `references/fix/seo-metadata.md`.
