# Input & Output Specification

How the pipeline detects input formats, what the Capture Wave produces, and what later waves consume.

---

## Input Specification

This skill supports three grounded starting points:

1. **Live website** — the production or staging site is reachable by URL.
2. **Saved browser artifacts** — `.html` + `_files/` folders, adjacent local `.css` files, SingleFile export, wget/HTTrack mirror, or other offline capture.
3. **Source repository** — fallback only when live or saved artifacts are unavailable.

### Preferred Order

| Source availability | Preferred mode | Why |
|---|---|---|
| Live URL available | **Capture-first mode** | Browser-grounded DOM, runtime metadata, full-page screenshots, and below-the-fold evidence are recoverable. |
| No live site, but saved `.html` + `_files/` exist | **Snapshot mode** | Saved artifacts are already close to Wave 0 input. |
| Only `.html` plus adjacent local CSS/assets exist | **Adjacent-asset snapshot mode** | Still grounded. Use the HTML-referenced local corpus as Wave 0 input. |
| Only SingleFile or inline HTML exists | **Inline snapshot mode** | Weaker than full snapshot mode, but still parseable. |
| Only source repo exists | **Source fallback mode** | Use only when runtime artifacts are unavailable. |

### Working Root Selection

Choose one explicit working root before capture or extraction begins.

- If the user already gave a target repo or working directory, use that as the working root.
- If the input is a standalone snapshot directory, use that directory as the source root and create `.design-soul/` and `nextjs-project/` beside it.
- If the input is only a live URL, create or select one recovery working root first, then place `.design-soul/` and `nextjs-project/` inside it.
- Do not scatter outputs across multiple roots. Every later wave assumes one shared root.

### Default Live Scope Heuristics

If the user gives only a root public URL and no route scope, default to the public marketing surface.

Include by default:

- homepage
- pricing, product, platform, solution, company, and contact/demo pages linked from nav/footer
- customer index, testimonial index, or equivalent marketing proof pages
- sitemap-discovered public marketing routes that match the visible site shell

Exclude by default unless the user explicitly asks for them:

- blog, research, changelog, guides, docs, API references
- authenticated app routes, account settings, dashboards
- legal, privacy, terms, status, and vendor microsites
- search, tag, pagination, and feed endpoints

Document all exclusions in `route-manifest.json` or `capture-summary.md`.

### Route Normalization Rules

Normalize routes before building the manifest:

- remove fragments (`#...`)
- treat query variants as the same route unless the query materially changes the page type
- normalize trailing slash differences consistently
- resolve relative links to absolute URLs before deduping
- preserve locale or version prefixes only when they are truly distinct in-scope routes
- keep one canonical pathname per route family entry

### Live Capture Inputs

Minimal live-capture inputs:

- one root URL or one scoped route list
- scope rules (marketing-only, docs-only, or explicit allowlist/denylist when provided)
- browser access capable of:
  - loading hydrated DOM
  - capturing screenshots at multiple viewports
  - scrolling long pages and capturing below-the-fold sections
  - recording network/runtime metadata
  - downloading or mirroring local asset copies

#### Live Capture Signals

Treat these as first-class input evidence:

- final hydrated DOM/HTML per route
- page title, H1, and ordered H2/H3 outline
- desktop/tablet/mobile screenshots
- full-page or scroll-slice screenshots for long pages
- discovered stylesheet, script, font, image, and chunk URLs
- runtime metadata such as `__NEXT_DATA__`, `self.__next_f`, build IDs, route manifests, and visible asset hashes
- route inventory from nav, footer, sitemap, internal links, and explicit user scope

### Saved Snapshot Inputs

Expected directory structure:

```
source-pages/
├── {site}-homepage.html
├── {site}-homepage_files/
│   ├── 06cc9eb5faccd3be.css
│   ├── 8422-c4149e3ed1566f84.js
│   ├── f79251b06e9e...352x352.png
│   └── inter-roman-var.woff2
├── {site}-pricing.html
├── {site}-pricing_files/
├── {site}-contact.html
├── local-shared.css
└── ...
```

### Auto-Detection Logic

On first scan of the input, detect the strongest available input type:

```bash
# Live URL present in the request or manifest
# -> CAPTURE-FIRST

# Saved HTML files
find . -maxdepth 2 \( -name "*.html" -o -name "*.htm" \) | sort

# Existing snapshot folders or adjacent local CSS
for f in *.html; do
  base="${f%.html}"
  if [ -d "${base}_files" ]; then
    echo "SNAPSHOT: $f -> ${base}_files/ ($(ls ${base}_files/*.css 2>/dev/null | wc -l) CSS files)"
  elif grep -qE 'href="[^"]+\.css' "$f"; then
    css_refs=$(grep -oE 'href="[^"]+\.css[^"]*"' "$f" | sed 's/^href="//;s/"$//' | sort -u | wc -l | tr -d ' ')
    echo "ADJACENT-ASSET SNAPSHOT: $f ($css_refs local CSS references)"
  else
    echo "INLINE-SNAPSHOT: $f ($(grep -c '<style' "$f" 2>/dev/null) <style> blocks)"
  fi
done

# Source repo fallback
[ -f "package.json" ] && echo "SOURCE REPO: package.json found"
```

### Auto-Detection Table

| Signal | Input Type | Behavior |
|---|---|---|
| Live `http://` or `https://` URL with no saved capture yet | Live capture | **Primary mode** — run the Capture Wave, preserve browser-grounded artifacts, then feed Wave 0 from those artifacts |
| `.html` files + `_files/` directories | Saved snapshot | **Primary offline mode** — grep minified CSS, decode CSS Module names, extract from companion folders |
| `.html` with local `.css` references, no `_files/` | Saved snapshot (adjacent assets) | **Adjacent-asset mode** — treat referenced CSS files as the page corpus and extract assets relative to the HTML file |
| `.html` with `<style>` blocks only, no `_files/` and no local `.css` files | SingleFile export | **Inline CSS mode** — extract from `<style>` tags within the HTML |
| `package.json` + `src/` directory | Source repository | **Fallback mode** — read component files directly, parse config, follow imports, and document reduced confidence when runtime evidence is missing |

### Key Characteristics of Live Capture

- DOM is **hydrated** — the final page may differ materially from the original HTML response
- important sections may appear **below the fold** or after scroll-triggered reveals
- JS bundles and CSS files may be discovered only after navigation or interaction
- runtime metadata may expose route manifests, build IDs, or framework-specific state
- visual verification requires **full-page or segmented capture**, not a single above-the-fold screenshot
- route inventories are rarely obvious from one page; nav, footer, sitemap, and internal links all matter

### Key Characteristics of Saved Snapshots

- CSS is often **minified** — single-line blobs, 100–400KB each — but adjacent-asset snapshots may keep CSS multi-line and human-readable
- filenames are often **hashed** (`06cc9eb5faccd3be.css`) — no semantic meaning in filenames
- class names often follow the **CSS Module pattern**: `ComponentName_propertyName__hashCode`
- **CSS custom properties** (`--color-*`, `--font-*`, `--ease-*`) form the design system backbone
- HTML preserves **semantic tags**: `<header>`, `<main>`, `<section>`, `<footer>`, `<nav>`
- inline `style=""` attributes frequently reference CSS variables via `var(--token-name)`
- each HTML file usually represents one route or one page type
- the **same CSS file** often appears in multiple `_files/` folders — deduplication is mandatory
- JS bundles contain **behavior logic**: scroll animations, intersection observers, dynamic class toggling

### CSS Corpus Rule

Wave 0 commands should operate on the page's **CSS corpus**, not blindly on `{page}_files/*.css`.

- Primary mode CSS corpus: every CSS file in `{page}_files/`
- Adjacent-asset mode CSS corpus: every local `.css` file referenced from the HTML plus sibling CSS assets you can prove belong to the page
- SingleFile mode CSS corpus: inline `<style>` blocks extracted from the HTML
- Live-capture mode CSS corpus: mirrored stylesheets downloaded into `.design-soul/capture/{route}/mirror/`

If a command in the references mentions `{page}_files/*.css`, substitute the discovered CSS corpus for the current input mode.

Read `references/capture-workflow.md` for the detailed live-capture procedure.

---

## Output Specification

The pipeline produces three output layers. Extraction-only mode stops after the appropriate layer.

### Layer 1: Capture Artifacts (`.design-soul/capture/`)

Produced only when the source starts as a live URL.

```
.design-soul/
├── capture/
│   ├── route-manifest.json                 # URL, pathname, inclusion, page family, notes
│   ├── page-types.md                       # Canonical page-family grouping + exemplar choice
│   ├── asset-discovery.json                # Shared discovered asset/runtime metadata
│   ├── capture-summary.md                  # What was captured, gaps, blocked routes
│   ├── homepage/
│   │   ├── dom.html                        # Final hydrated DOM snapshot
│   │   ├── headings.json                   # title + H1/H2/H3 outline
│   │   ├── runtime-metadata.json           # __NEXT_DATA__, build IDs, script/style URLs, etc.
│   │   ├── assets.json                     # route-level asset URLs
│   │   ├── mirror/                         # Local copies of CSS, JS, fonts, images, chunks
│   │   ├── screenshots/
│   │   │   ├── desktop-full.png
│   │   │   ├── tablet-full.png
│   │   │   ├── mobile-full.png
│   │   │   ├── desktop-segment-01.png
│   │   │   └── ...
│   │   └── done.signal
│   └── {additional-routes}/
```

### Layer 2: Design Documentation (`.design-soul/wave0` → `wave3`)

```
.design-soul/
├── capture/                                # optional; required for live-URL starts
├── wave0/
│   ├── homepage/
│   │   ├── exploration.md
│   │   ├── deobfuscated.css
│   │   ├── behavior-spec.md
│   │   ├── assets/
│   │   └── done.signal
│   └── {additional-pages}/
├── wave1/
│   ├── marketing-landing/
│   │   ├── design-soul.md
│   │   ├── token-values.json
│   │   ├── component-inventory.md
│   │   ├── responsive-map.md
│   │   ├── cross-site-patterns.md
│   │   └── done.signal
│   └── {additional-groups}/
├── wave2/
│   ├── homepage/
│   │   ├── agent-brief.md
│   │   └── done.signal
│   └── {additional-pages}/
└── wave3/
    ├── foundation-brief.md
    ├── traceability-matrix.md
    └── foundation-ready.signal
```

### Layer 3: Buildable Next.js Project (`nextjs-project/` + visual QA)

```
nextjs-project/
├── app/
├── components/
├── lib/
├── styles/
├── public/
│   └── assets/
│       ├── fonts/
│       ├── images/
│       └── icons/
├── tailwind.config.ts
├── postcss.config.js
├── package.json
├── tsconfig.json
└── next.config.js

.design-soul/
└── visual/
    ├── homepage/
    │   ├── source-desktop-full.png
    │   ├── build-desktop-full.png
    │   ├── diff-desktop-full.png
    │   ├── source-desktop-segment-01.png
    │   ├── build-desktop-segment-01.png
    │   ├── diff-desktop-segment-01.png
    │   └── summary.json
    └── {additional-routes}/
```

---

## Request Interpretation Table

How the orchestrator decides which phases to execute based on user intent:

| User Says | Phases Executed | Primary Output |
|---|---|---|
| `Extract the design` | Capture Wave if needed -> 0 -> 1 -> 2 | `.design-soul/` docs |
| `Document this site` | Capture Wave if needed -> 0 -> 1 -> 2 | `.design-soul/` docs |
| `Capture the design DNA` | Capture Wave if needed -> 0 -> 1 -> 2 | `.design-soul/` docs |
| `Rebuild this site` | Capture Wave if needed -> 0 -> 1 -> 2 -> 3 -> 4 | `.design-soul/` + `nextjs-project/` |
| `Recreate this page` | Capture Wave if needed -> 0 -> 1 -> 2 -> 3 -> 4 | `.design-soul/` + `nextjs-project/` |
| `Recover this production site` | Capture Wave if needed -> 0 -> 1 -> 2 -> 3 -> 4 | `.design-soul/` + `nextjs-project/` |
| `Clone this design` | Capture Wave if needed -> 0 -> 1 -> 2 -> 3 -> 4 | `.design-soul/` + `nextjs-project/` |
| `Pixel-perfect copy` | Capture Wave if needed -> 0 -> 1 -> 2 -> 3 -> 4 + visual QA loop | `.design-soul/` + `nextjs-project/` + `.design-soul/visual/` |
| `Just the tokens` | Capture Wave if needed -> 0 -> 1 | `wave0/` + `wave1/` only |
| `Just the design system` | Capture Wave if needed -> 0 -> 1 | `wave0/` + `wave1/` only |
| `Extract and scaffold` | Capture Wave if needed -> 0 -> 1 -> 2 -> 3 | `.design-soul/` + scaffold only |

### Ambiguity Resolution

If the user's intent is unclear:

1. Default to **grounded extraction first** — Capture Wave when needed, then Waves 0–2.
2. If the user has provided only a live URL, do not ask for snapshots first; create the capture artifacts yourself.
3. Never assume a faithful rebuild from a single screenshot or vague styling reference.
4. Never assume route completeness from the homepage alone; build a route manifest first.
