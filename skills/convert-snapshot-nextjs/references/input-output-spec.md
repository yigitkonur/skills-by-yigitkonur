# Input & Output Specification

How the pipeline detects input formats and what it produces at each stage.

---

## Input Specification

This skill is designed for **saved HTML snapshots** — the kind produced by browser "Save As", wget, HTTrack, SingleFile, or any offline snapshot tool.

### Expected Directory Structure

```
source-pages/
├── {site}-homepage.html              # Full HTML (minified, often 1-2MB)
├── {site}-homepage_files/            # Companion assets folder
│   ├── 06cc9eb5faccd3be.css          # Minified CSS (hashed filenames, 12+ files)
│   ├── 8422-c4149e3ed1566f84.js      # JS bundles (minified)
│   ├── f79251b06e9e...352x352.png    # Images / SVGs / favicons
│   └── Inter-roman.var.woff2         # Font files
├── {site}-pricing.html
├── {site}-pricing_files/
├── {site}-features.html
├── {site}-features_files/
└── ...
```

### Auto-Detection Logic

On first scan of the input directory, detect the input type:

```bash
# Step 1: Find all HTML files
find . -maxdepth 2 -name "*.html" -o -name "*.htm" | sort

# Step 2: Classify each
for f in *.html; do
  base="${f%.html}"
  if [ -d "${base}_files" ]; then
    echo "SNAPSHOT: $f → ${base}_files/ ($(ls ${base}_files/*.css 2>/dev/null | wc -l) CSS files)"
  else
    echo "SINGLEFILE: $f ($(grep -c '<style' "$f" 2>/dev/null) <style> blocks)"
  fi
done
[ -f "package.json" ] && echo "SOURCE REPO: package.json found"
```

### Auto-Detection Table

| Signal | Input Type | Behavior |
|--------|-----------|----------|
| `.html` files + `_files/` directories | Saved snapshot | **Primary mode** — grep minified CSS, decode CSS Module names, extract from companion folders |
| `.html` with `<style>` blocks only, no `_files/` | SingleFile export | **Inline CSS mode** — extract from `<style>` tags within the HTML |
| `package.json` + `src/` directory | Source repository | **Fallback mode** — read component files directly, parse `tailwind.config.*`, follow imports |

### Key Characteristics of Saved Snapshots

- CSS is **MINIFIED** — single-line blobs, 100–400KB each, 12+ files per page
- Filenames are **hashed** (`06cc9eb5faccd3be.css`) — no semantic meaning in filenames
- Class names follow the **CSS Module pattern**: `ComponentName_propertyName__hashCode`
- **CSS custom properties** (`--color-*`, `--font-*`, `--ease-*`) form the design system backbone
- HTML preserves **semantic tags**: `<header>`, `<main>`, `<section>`, `<footer>`, `<nav>`
- Inline `style=""` attributes frequently reference CSS variables via `var(--token-name)`
- Each HTML file represents **one page type** (homepage, pricing, features, about, etc.)
- **Same CSS file** often appears in multiple `_files/` folders — deduplication is mandatory
- JS bundles contain **behavior logic**: scroll animations, intersection observers, dynamic class toggling

---

## Output Specification

The pipeline produces TWO output trees. Extraction-only mode (Waves 0–2) produces the first. Full reconstruction (Waves 0–4) produces both.

### Tree 1: Design Documentation (`.design-soul/`)

```
.design-soul/                                    ← Intermediate extraction docs
├── wave0/                                       ← Per-page deep exploration
│   ├── homepage/
│   │   ├── exploration.md                       # Section inventory + CSS token map + behavior map
│   │   ├── deobfuscated.css                     # Full CSS with semantic class names
│   │   ├── behavior-spec.md                     # JS behaviors as declarative specs
│   │   ├── assets/                              # Downloaded fonts, images, icons, videos
│   │   │   ├── fonts/
│   │   │   ├── images/
│   │   │   └── icons/
│   │   └── done.signal                          # Empty file = this agent completed
│   ├── pricing/
│   │   ├── exploration.md
│   │   ├── deobfuscated.css
│   │   ├── behavior-spec.md
│   │   ├── assets/
│   │   └── done.signal
│   └── {additional-pages}/
├── wave1/                                       ← Design soul per page-type group
│   ├── landing/
│   │   ├── design-soul.md                       # Unified visual DNA for this group
│   │   ├── token-values.json                    # Machine-readable tokens (all traced)
│   │   ├── component-inventory.md               # Every repeating UI element
│   │   ├── responsive-map.md                    # Breakpoint behavior per component
│   │   ├── cross-site-patterns.md               # Patterns shared across pages in group
│   │   └── done.signal
│   └── {additional-groups}/
├── wave2/                                       ← Build briefs per page
│   ├── homepage/
│   │   ├── agent-brief.md                       # Self-contained build instructions
│   │   └── done.signal
│   ├── pricing/
│   │   ├── agent-brief.md
│   │   └── done.signal
│   └── {additional-pages}/
└── wave3/                                       ← Design system foundation docs
    ├── foundation-brief.md                      # How Wave 4 agents use the design system
    ├── traceability-matrix.md                   # Token → Wave 2 brief → Wave 0 source
    └── foundation-ready.signal                  # ONLY written after quality gate passes
```

### Tree 2: Buildable Next.js Project (`nextjs-project/`)

```
nextjs-project/                                  ← Buildable project (Waves 3–4 only)
├── app/                                         # App Router page routes
│   ├── layout.tsx                               # Root layout with fonts + global styles
│   ├── page.tsx                                 # Homepage
│   ├── pricing/page.tsx                         # Pricing page
│   └── {additional-routes}/page.tsx
├── components/
│   ├── shared/                                  # Shared components (header, footer, CTA)
│   │   ├── Header.tsx
│   │   ├── Footer.tsx
│   │   └── ...
│   └── pages/                                   # Page-specific components
│       ├── homepage/
│       │   ├── Hero.tsx
│       │   ├── FeatureGrid.tsx
│       │   └── ...
│       └── pricing/
│           ├── PlanCards.tsx
│           ├── ComparisonTable.tsx
│           └── ...
├── lib/
│   ├── tokens.ts                                # Typed design tokens from REAL CSS
│   └── animations.ts                            # Animation utilities from extracted @keyframes
├── styles/
│   └── globals.css                              # @font-face declarations + CSS custom properties
├── public/
│   └── assets/                                  # Self-hosted fonts, images, icons
│       ├── fonts/
│       ├── images/
│       └── icons/
├── tailwind.config.ts                           # Extended with REAL extracted values
├── postcss.config.js                            # Standard PostCSS with Tailwind + autoprefixer
├── package.json                                 # ONLY: next, react, react-dom, typescript, tailwindcss
├── tsconfig.json                                # strict: true
└── next.config.js                               # Minimal Next.js config
```

---

## Request Interpretation Table

How the orchestrator decides which waves to execute based on user intent:

| User Says | Waves Executed | Primary Output |
|-----------|---------------|----------------|
| "Extract the design" | 0 → 1 → 2 | `.design-soul/` documentation only |
| "Document this site" | 0 → 1 → 2 | `.design-soul/` documentation only |
| "Capture the design DNA" | 0 → 1 → 2 | `.design-soul/` documentation only |
| "Rebuild this site" | 0 → 1 → 2 → 3 → 4 | `.design-soul/` + `nextjs-project/` |
| "Recreate this page" | 0 → 1 → 2 → 3 → 4 | `.design-soul/` + `nextjs-project/` |
| "Clone this design" | 0 → 1 → 2 → 3 → 4 | `.design-soul/` + `nextjs-project/` |
| "Reconstruct from snapshot" | 0 → 1 → 2 → 3 → 4 | `.design-soul/` + `nextjs-project/` |
| "Pixel-perfect copy" | 0 → 1 → 2 → 3 → 4 | `.design-soul/` + `nextjs-project/` |
| "Just the tokens" | 0 → 1 | `wave0/` + `wave1/` only |
| "Just the design system" | 0 → 1 | `wave0/` + `wave1/` only |
| "Extract and scaffold" | 0 → 1 → 2 → 3 | `.design-soul/` + `nextjs-project/` scaffold (no page builds) |

### Ambiguity Resolution

If the user's intent is unclear:
1. Default to **Waves 0–2** (extraction only) — it's safe and non-destructive
2. Ask: "I've extracted the design documentation. Would you also like me to rebuild it as a Next.js project? (That would run Waves 3–4)"
3. Never assume reconstruction unless the user explicitly says "build", "rebuild", "recreate", "html to nextjs", "page to react", "convert this design", or "make a nextjs version"
