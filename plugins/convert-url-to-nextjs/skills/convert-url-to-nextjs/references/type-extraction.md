# Type Extraction — From L0 + L1 Crawl to One Template per Unique Page Type

This is the named phase that sits between the Capture Wave and the Next.js build. It exists because most marketing sites have far fewer **page types** than they have URLs. Producing one Next.js template per unique type is what makes the rebuild faithful **and** maintainable. Producing one template per URL duplicates work and drifts away from the source's real shell.

Read this when the user has handed you only a live URL (the lost-frontend scenario) or a partial recovery, and you need to decide how many templates to build before any rendering work begins.

---

## What "L0" and "L1" mean here

| Level | Meaning | How it is discovered |
|---|---|---|
| **L0** | The root URL the user gave you — usually the homepage | The literal URL in the prompt |
| **L1** | Every URL directly reachable from L0 by following an in-domain link in the rendered DOM | Hydrated DOM crawl of L0 |

Out of scope by default: L2+ (links discovered only from L1 pages). Crawling deeper is opt-in; ask the user before doing it.

Same-origin only. Skip:

- external links (different hostname, including `www.` vs apex mismatch when one is the canonical)
- `mailto:`, `tel:`, `javascript:`, `#` anchors
- pagination/query-only variants (`?page=2`, `?utm_source=...`) unless the path itself changes
- locale duplicates beyond one canonical locale unless the user asked for the full localized set
- auth-walled routes, app/dashboard routes, and anything that 401/403s

Record every excluded link with the reason in `route-manifest.json` instead of silently dropping it.

---

## Why type-extraction, not URL fan-out

The lost-frontend goal is to land a buildable Next.js codebase that looks pixel-faithful to the deployed build. Two things make per-URL fan-out the wrong default:

1. **A 30-route marketing site usually has 4–8 real page types.** The other 22+ URLs are instances of those types (different products, different customer stories, different blog posts). One template per type with route data covers them.
2. **The user's next move after this skill is usually wiring up dynamic content** (TinaCMS, MDX, a headless CMS, or hand-curated route data). That step is easier when templates are typed, not duplicated.

Output of this phase: a small set of typed Next.js templates plus a route map that says which L1 URL is an instance of which type. The user later attaches real content.

---

## Phased flow inside type-extraction

```
[Crawl L0]
  └── extract every same-origin link  →  L1 URL list
[Capture each L1 URL]
  └── hydrated DOM, headings, layout fingerprint, screenshots (1440/768/375)
[Cluster L1 URLs by layout fingerprint]
  └── unique page types  →  one Next.js template each
[Choose canonical exemplar per type]
  └── richest URL in the cluster anchors the template
[Write `route-map.json`]
  └── { l1Url → typeId } plus per-type capture pointers
```

The Capture Wave (see `references/capture-workflow.md`) produces the per-URL artifacts. This phase is the clustering step that turns those artifacts into a typed template list.

---

## L1 capture contract

For every L1 URL kept in scope, capture (via `run-agent-browser` or the equivalent helper named in `references/capture-workflow.md`):

- final hydrated `dom.html`
- `headings.json` — title, H1, ordered H2/H3 outline
- `layout-fingerprint.json` — see schema below
- `screenshots/{desktop,tablet,mobile}-full.png` at 1440, 768, 375 widths
- a scroll-slice screenshot set for pages longer than one viewport
- `runtime-metadata.json` when the site exposes `__NEXT_DATA__`, `self.__next_f`, route manifests, or build IDs

Keep the L0 capture too. The homepage is treated as its own type by default — the homepage rarely shares layout with the L1 pages it links to.

---

## Layout fingerprint — the clustering signal

A layout fingerprint is a small, deterministic snapshot of the page's structural DNA. Two URLs whose fingerprints overlap on most of the signals below are almost always instances of the same page type.

Compute the fingerprint from the **hydrated DOM** (after JS settles), not from the raw HTML response.

### Signal set

| # | Signal | How to derive | Why it matters |
|---|---|---|---|
| 1 | **Pathname pattern** | Tokenize the pathname; replace numeric/slug segments with `:slug` placeholders (`/blog/intro-to-x` → `/blog/:slug`) | Pages under the same path template are usually the same type |
| 2 | **`<body>` and `<main>` class set** | Sorted, deduplicated class list from `<body>` and `<main>` (or whatever root the framework actually uses) | Frameworks often stamp a per-type class on the root |
| 3 | **Top-level section sequence** | The ordered list of `data-*` attributes, semantic tags, or CSS Module prefixes for each direct child of `<main>` (e.g. `Hero_, FeatureGrid_, LogoCloud_, CTA_, Footer_`) | The "skeleton" of a page type is its section order |
| 4 | **Direct-child section count** | Count of direct children of `<main>` | A landing page with 7 sections rarely matches a docs page with 2 |
| 5 | **Recognizable widget set** | Boolean flags for: pricing table, hero with CTA, FAQ accordion, logo wall, testimonial cards, blog metadata (author/date/reading-time), legal heading rhythm, contact form, etc. | One signal catches "this is a pricing page" even when DOM differs subtly |
| 6 | **Header/footer shell hash** | Hash of the rendered `<header>` and `<footer>` inner DOM (with hashed class names normalized) | Confirms the shared shell — pages with the same shell often share family |
| 7 | **CSS class fingerprint** | Top-N most frequent CSS Module prefixes across the page body (e.g. `Pricing_, Plan_, FAQ_`) | Distinguishes pages that share a shell but have different bodies |

Store the fingerprint as a JSON object per L1 URL under `.design-soul/types/fingerprints/{slug}.json`. Keep the raw values — do not pre-bucket them.

### Example fingerprint

```json
{
  "url": "https://example.com/customers/acme",
  "pathname": "/customers/:slug",
  "rootClasses": ["customers-story", "marketing-shell"],
  "sectionSequence": [
    "Hero_",
    "QuoteCallout_",
    "MetricRow_",
    "CaseBody_",
    "RelatedCustomers_",
    "PrefooterCTA_"
  ],
  "directChildCount": 6,
  "widgets": {
    "hero": true,
    "pricingTable": false,
    "faqAccordion": false,
    "logoWall": false,
    "testimonialQuote": true,
    "blogMeta": false,
    "contactForm": false
  },
  "headerHash": "h:9a1c…",
  "footerHash": "f:b7d4…",
  "topClassPrefixes": ["Hero_", "Customers_", "QuoteCallout_", "MetricRow_", "PrefooterCTA_"]
}
```

---

## Clustering rule

Two L1 URLs go into the **same** type cluster when **all three** are true:

1. **Pathname template matches** — same `/blog/:slug`, `/customers/:slug`, etc. (or both are top-level marketing URLs with distinct paths)
2. **Section-sequence overlap ≥ ~70%** — measured as the longest common subsequence of `sectionSequence` divided by the longer of the two
3. **Header/footer shell hash matches OR top class-prefix overlap ≥ ~60%**

Two URLs whose pathnames are identical templates but whose section sequences disagree by more than 30% are **different types** (e.g. a `/products/pro` landing vs `/products/team` landing that share `/products/:slug` but have different blocks). Do not merge them just because the URL pattern looks the same.

A homepage is **always** its own type. Do not cluster `/` with anything else, even if its shell matches a marketing-landing type.

A type cluster of size 1 is valid. Many small sites legitimately have a unique `/pricing`, `/about`, `/contact` that share no body with anything else.

---

## Naming each type

For each cluster, name the type with a short kebab-case id. Use the strongest signal:

- pathname template → `customer-story` (`/customers/:slug`)
- visible role → `pricing`, `contact`, `marketing-landing`, `blog-post`, `legal`, `homepage`
- widget signature → `hero-with-pricing-table` only if no clearer name exists

Familiar default name set (extend as needed):

| Type id | Typical signal |
|---|---|
| `homepage` | the L0 URL itself |
| `marketing-landing` | product / platform / solution pages with hero + features + CTA |
| `pricing` | pricing-card widget present |
| `contact` | contact form widget present |
| `customer-story` | testimonial quote + metric row + case body |
| `customers-index` | listing of customer cards |
| `blog-post` | blog-meta widget (author/date/reading-time) |
| `blog-index` | listing of blog cards |
| `legal` | legal heading rhythm (long H2/H3 list, dense paragraphs) |
| `auth` | login/signup form |
| `dashboard` | persistent sidebar + content pane (only if the user explicitly scopes in app routes) |

---

## Choosing the canonical exemplar per type

Per cluster, pick one URL as the **canonical exemplar**. The exemplar is the URL whose capture artifacts the rebuild reads first.

Priority order:

1. richest section vocabulary in the cluster
2. URL most often linked from L0 (the homepage's choice signal is meaningful)
3. URL with the most complete asset capture (no missing fonts/images)
4. shortest pathname in the cluster (`/blog/intro` over `/blog/2023/12/intro-to-x`)

Document the rationale per type in `.design-soul/types/page-types.md`. Do not silently pick one.

---

## `route-map.json` — the deliverable

Write `.design-soul/types/route-map.json` after clustering. This file is the single source of truth for the next phase.

```json
{
  "rootUrl": "https://example.com",
  "types": [
    {
      "id": "homepage",
      "exemplarUrl": "https://example.com/",
      "instances": ["https://example.com/"],
      "nextjsTemplate": "app/page.tsx",
      "captureRoots": [".design-soul/capture/homepage/"]
    },
    {
      "id": "pricing",
      "exemplarUrl": "https://example.com/pricing",
      "instances": ["https://example.com/pricing"],
      "nextjsTemplate": "app/pricing/page.tsx",
      "captureRoots": [".design-soul/capture/pricing/"]
    },
    {
      "id": "customer-story",
      "exemplarUrl": "https://example.com/customers/acme",
      "instances": [
        "https://example.com/customers/acme",
        "https://example.com/customers/globex",
        "https://example.com/customers/initech"
      ],
      "nextjsTemplate": "app/customers/[slug]/page.tsx",
      "captureRoots": [
        ".design-soul/capture/customers/acme/",
        ".design-soul/capture/customers/globex/",
        ".design-soul/capture/customers/initech/"
      ]
    }
  ],
  "excluded": [
    {"url": "https://example.com/blog", "reason": "user-scoped marketing surface only"},
    {"url": "https://twitter.com/example", "reason": "external link"}
  ]
}
```

Two follow-on artifacts written next to it:

- `.design-soul/types/page-types.md` — human-readable rationale per cluster (signal evidence, exemplar choice, notable instance differences)
- `.design-soul/types/fingerprints/{slug}.json` — one per L1 URL, the raw fingerprint that drove clustering

---

## Output of this phase — what the rebuild phase consumes

When the type-extraction phase is complete, the rebuild phase reads `route-map.json` and **builds one Next.js template per type**:

- `homepage` → `app/page.tsx`
- one static template per single-instance type → `app/pricing/page.tsx`, `app/contact/page.tsx`, `app/about/page.tsx`
- one parameterized template per multi-instance type → `app/customers/[slug]/page.tsx`, `app/blog/[slug]/page.tsx`

Each template uses the exemplar's extracted tokens, sections, and assets. Instances that diverge from the exemplar are noted in `page-types.md` and surfaced to the user at the end (Phase 5 / report back) so the user knows where to attach per-instance content overrides — typically via a CMS the user wires up later.

---

## What to escalate to the user before continuing

Pause and ask once if any of these are true:

- the L1 list is unexpectedly large (50+ URLs) and the user did not scope it
- a single type cluster has 20+ instances and they look visually diverse (probably two different sub-types)
- a type cluster of 1 has the same shell as another cluster's exemplar (might be a forgotten merge)
- the L0 homepage has zero same-origin L1 links (unusual — probably JS-rendered nav not yet hydrated; re-capture with more settle time)
- you cannot reliably compute a layout fingerprint for any L1 URL (blocked by hard auth wall, CAPTCHA, or hostile bot detection)

Each of these is a §1 contradiction — name it in one line, decide once, proceed.

---

## What this phase does NOT do

- it does not write any Next.js code
- it does not extract tokens (that is Wave 0; see `references/foundations-agent.md`)
- it does not run visual verification (that is Phase 4; see `references/back-to-back-verification.md`)
- it does not crawl deeper than L1 without explicit user consent
