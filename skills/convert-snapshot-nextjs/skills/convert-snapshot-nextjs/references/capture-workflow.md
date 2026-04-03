# Capture Workflow

Concrete execution guide for the Capture Wave. Read this when the source starts as a live URL or partially recovered production site.

---

## Prerequisites

You need:

- one browser automation tool that can:
  - open a URL
  - return the current URL and title
  - evaluate JS in the page
  - save screenshots
  - inspect or export DOM
- shell access for `curl`, `find`, and basic text processing

Preferred browser tools:

- `agent-browser` when available
- equivalent Playwright/CDP workflow if your environment does not provide `agent-browser`

If no browser automation tool is available, live capture mode is blocked. Fall back to saved snapshots or install/enable a browser driver first.

---

## Working Root Selection

Before writing any capture artifacts, choose the working root:

1. **If you are already inside the target repo or recovery workspace**: write `.design-soul/` and `nextjs-project/` at that repo root.
2. **If you only have a live URL and no project root exists yet**: create `<domain>-recovery/` in the current working directory and use that as the working root.

Example:

- `https://www.browserbase.com/` → `browserbase-com-recovery/`
- `https://example.ai/` → `example-ai-recovery/`

All paths below are relative to that working root.

---

## Default Live Scope Heuristic

If the user gave only a root marketing URL and did not define scope:

- include the homepage
- include pricing, contact, demo, product, platform, solution, customer, enterprise, and other primary public marketing routes linked from header/footer
- include one representative route for each obvious public page family
- exclude blog, docs, changelog, legal, privacy, terms, careers, status, auth, app, dashboard, and locale duplicates by default

Only override this default when:

- the user explicitly asks for those sections, or
- those routes are the obvious main product surface rather than auxiliary content

When in doubt, record the route as discovered but excluded with a reason instead of silently dropping it.

---

## Route Inventory Procedure

Build `route-manifest.json` by combining these sources:

1. header navigation links
2. footer links
3. `sitemap.xml` when available
4. obvious in-page internal links on captured public routes
5. explicit user-provided routes

Normalize every candidate route before deduplication:

- strip `#hash`
- strip query strings unless they materially change the route
- normalize trailing slash consistently
- collapse duplicate locale or tracking variants

For each route, record:

```json
{
  "url": "https://example.com/pricing",
  "pathname": "/pricing",
  "included": true,
  "pageFamily": "pricing",
  "canonical": true,
  "sourceHints": ["header", "footer", "sitemap"],
  "notes": ["public marketing route"]
}
```

If the same route is found from multiple sources, merge the `sourceHints` instead of duplicating the row.

---

## Canonical Page-Family Selection

Choose at least one canonical exemplar per family before broad fan-out.

Use this priority:

1. richest route in the family
2. route with the fullest section vocabulary
3. route directly linked from primary navigation
4. route most likely to define the shared shell for siblings

Typical family examples:

- `home`
- `marketing-landing`
- `pricing`
- `contact`
- `customers-index`

Document the rationale in `page-types.md`.

---

## Per-Route Capture Contract

Each captured route directory must contain:

```text
.design-soul/capture/{route}/
├── dom.html
├── headings.json
├── runtime-metadata.json
├── assets.json
├── mirror/
│   ├── css/
│   ├── js/
│   ├── fonts/
│   └── images/
├── screenshots/
│   ├── desktop-full.png
│   ├── tablet-full.png
│   ├── mobile-full.png
│   ├── desktop-segment-01.png
│   └── ...
└── done.signal
```

### Required contents

- `dom.html` — final hydrated DOM after the route settles
- `headings.json` — title, H1, ordered H2/H3 outline
- `runtime-metadata.json` — framework/runtime evidence when present
- `assets.json` — discovered asset URLs grouped by type
- `mirror/` — locally downloaded CSS/JS/fonts/images needed by Wave 0
- `screenshots/` — desktop, tablet, mobile, plus scroll slices for long pages

The `mirror/` directory is the default `{asset_root}` for Wave 0 in live-capture mode. Do not leave asset mirroring implicit.

---

## Concrete Capture Loop

For each canonical route:

1. open the route and verify URL/title
2. let the page settle
3. capture:
   - final DOM
   - title and heading outline
   - stylesheet, script, font, and image URLs
   - runtime metadata such as `__NEXT_DATA__`, `self.__next_f`, build IDs, chunk URLs, or route manifests when exposed
4. download route-discovered CSS/JS/fonts/images into `mirror/`
5. capture screenshots at desktop, tablet, and mobile
6. if the page is longer than one viewport, capture scroll slices until the footer is visible
7. write route notes and create `done.signal`

If a route uses sticky headers, lazy content, accordions, or tabbed sections, capture the default settled state first. Only capture alternate states when the user explicitly needs them or the default state hides critical content.

---

## Browser-Tool-Agnostic Evidence Requirements

The tool does not matter as much as the evidence. A successful live capture must let a later Wave 0 agent answer:

- what route was captured?
- what did the settled DOM contain?
- what headings and sections were visible?
- which stylesheets/scripts/assets powered the route?
- what local mirrored files should be parsed as `{asset_root}`?
- what did the route look like above and below the fold?

If your browser tool cannot provide one of these, the capture is incomplete.

---

## Failure Recovery

- **No sitemap:** continue with nav/footer/internal-link discovery
- **Huge sitemap:** filter through the default scope heuristic before capture
- **No runtime metadata exposed:** continue with DOM, scripts, and mirrored assets
- **Asset URL found but download fails:** record the original URL and mark the asset missing in `assets.json`
- **Page keeps changing after load:** capture the default settled state after a consistent wait and document the instability
- **No mirrored assets were created:** do not proceed to Wave 0; fix the Capture Wave handoff first
