---
name: convert-snapshot-nextjs
description: Use skill if you are converting saved HTML snapshots into buildable Next.js pages with self-hosted assets and extracted styles.
---

# Snapshot to Next.js

Convert saved HTML pages — produced by browser "Save As", wget, HTTrack, SingleFile, or any offline capture tool — into pixel-perfect Next.js App Router projects with zero third-party dependencies. This is a forensic CSS parser: it reads every minified rule, decodes every CSS Module class name, resolves every custom property chain, and builds production-ready code from real extracted values. No approximations. No invented tokens.

## Decision tree

```
What do you need?
│
├── Full conversion (HTML → Next.js)
│   ├── Understand the 5-wave pipeline ──────► references/wave-pipeline.md
│   ├── Input formats & auto-detection ──────► references/input-output-spec.md
│   ├── Output structure (both trees) ───────► references/input-output-spec.md
│   ├── Core principles & constraints ───────► references/principles-and-rules.md
│   └── Request interpretation table ────────► references/input-output-spec.md
│
├── Wave 0 — Per-page exploration
│   ├── Agent prompt & methodology ──────────► references/foundations-agent.md
│   ├── Section identification rules ────────► references/principles-and-rules.md
│   ├── CSS Module decoding ─────────────────► Key patterns (below)
│   └── Pattern catalog ─────────────────────► references/website-patterns.md
│
├── Wave 1 — Design soul extraction
│   ├── Agent prompt & methodology ──────────► references/sections-agent.md
│   ├── Page-type grouping rules ────────────► references/wave-pipeline.md
│   └── Quality gates ──────────────────────► references/quality-checklist.md
│
├── Wave 2 — Build brief manufacturing
│   ├── Brief template & format ─────────────► references/section-template.md
│   ├── Completeness requirements ───────────► references/wave-pipeline.md
│   └── Quality gates ──────────────────────► references/quality-checklist.md
│
├── Wave 3 — Next.js scaffold & design system
│   ├── Scaffold template & structure ───────► references/system-template.md
│   ├── Foundation quality gate ─────────────► references/wave-pipeline.md
│   ├── Output project structure ────────────► references/input-output-spec.md
│   └── Quality gates ──────────────────────► references/quality-checklist.md
│
├── Wave 4 — Pixel-perfect page build
│   ├── Agent spawning & acceptance ─────────► references/wave-pipeline.md
│   └── Quality gates ──────────────────────► references/quality-checklist.md
│
├── CSS parsing & extraction
│   ├── CSS Module decoding ─────────────────► Key patterns (below)
│   ├── Minified CSS strategies ─────────────► references/foundations-agent.md
│   ├── Token extraction ───────────────────► references/principles-and-rules.md
│   └── Section identification ─────────────► references/principles-and-rules.md
│
└── Pattern identification
    ├── Website anatomy patterns ────────────► references/website-patterns.md
    └── Section-type mapping ───────────────► references/website-patterns.md
```

## Quick start

### Step 1: Detect input

```bash
for f in source-pages/*.html; do
  base="${f%.html}"
  if [ -d "${base}_files" ]; then
    echo "SNAPSHOT: $f → $(ls ${base}_files/*.css 2>/dev/null | wc -l) CSS files"
  else
    echo "SINGLEFILE: $f ($(grep -c '<style' "$f") style blocks)"
  fi
done
```

| Signal | Mode | What happens |
|--------|------|-------------|
| `.html` + `_files/` dirs | Saved snapshot | Grep minified CSS, decode CSS Module names, extract from companion folders |
| `.html` with `<style>` only | SingleFile export | Extract from inline `<style>` tags |
| `package.json` + `src/` | Source repository | Fallback — read components directly |

### Step 2: Run the pipeline

```
Wave 0 ──► Wave 1 ──► Wave 2 ──► Wave 3 ──► Wave 4
(explore)  (soul)     (briefs)   (scaffold)  (build)
 1/page    1/group    1/page     1 total     1/page
 parallel  parallel   parallel   single      parallel
```

Each wave has a completion gate (`done.signal` files). No wave N+1 starts until ALL wave N signals exist.

| User intent | Waves | Output |
|------------|-------|--------|
| "Extract the design" / "Document this site" | 0 → 1 → 2 | `.design-soul/` only |
| "Rebuild" / "Recreate" / "Clone" / "Pixel-perfect" | 0 → 1 → 2 → 3 → 4 | `.design-soul/` + `nextjs-project/` |
| "Just the tokens" / "Just the design system" | 0 → 1 | `wave0/` + `wave1/` only |
| "Extract and scaffold" | 0 → 1 → 2 → 3 | `.design-soul/` + scaffold (no page builds) |

If intent is unclear, default to Waves 0–2 (extraction only), then ask.

### Step 3: Assign agents per wave

- **Wave 0 agents** MUST read `references/foundations-agent.md` before starting
- **Wave 1 agents** MUST read `references/sections-agent.md` before starting
- **Wave 2 agents** MUST read `references/section-template.md` before writing briefs
- **Wave 3 orchestrator** MUST read `references/system-template.md` before scaffolding
- **All agents** SHOULD consult `references/website-patterns.md` for section-type identification
- **All agents** SHOULD consult `references/quality-checklist.md` before writing `done.signal`

## Key patterns

### CSS Module decoding

The naming convention `ComponentName_propertyName__hashCode` is the primary section identifier:

```
Header_root__x8J2p          → Component: Header,    Element: root
Plans_card__SCfoV            → Component: Plans,     Element: card
CTA_sectionPrefooter__kW_wF → Component: CTA,       Element: sectionPrefooter
CustomerMarquee_logos__abc   → Component: CustomerMarquee, Element: logos
```

Extract the prefix map from any page:

```bash
grep -oE '[A-Z][a-zA-Z]+_[a-zA-Z]+__[a-zA-Z0-9]+' page.html | sed 's/_[a-zA-Z]*__[a-zA-Z0-9]*$//' | sort -u
```

**Filter out utility prefixes** (`Flex_`, `Grid_`, `Container_`, `Spacer_`, `Text_`, `Icon_`) — these appear inside sections but don't define boundaries.

### The grounding rule

Every value must trace to one of these sources — no exceptions:

1. A CSS rule in `_files/*.css` — cite filename + selector
2. A CSS custom property in `:root` or `[data-theme]` — cite filename + selector
3. An inline `style=""` attribute — cite element + attribute
4. A `<style>` block in HTML — cite block context
5. A `@keyframes` or `@media` rule — cite filename + rule name

If a value can't be found: mark it `UNVERIFIED — not found in snapshot CSS/HTML`. Never round, never assume, never invent. The downstream builder implements values **literally**.

### Section identification priority

1. **Semantic HTML tags** — `<header>`, `<section>`, `<footer>`, `<nav>` (most reliable)
2. **CSS Module prefixes** — unique prefix = distinct visual section
3. **Structure heuristics** (fallback) — background color changes, padding shifts, full-width dividers

### Zero dependencies constraint

`package.json` may ONLY contain: `next`, `react`, `react-dom`, `typescript`, `tailwindcss`, `@types/react`, `@types/node`, `postcss`, `autoprefixer`. No component libraries, no animation libraries, no icon packages, no CDN fonts. Everything built from scratch.

### Output trees

The pipeline produces two output trees — see `references/input-output-spec.md` for complete structures:

1. **`.design-soul/`** — Intermediate extraction documentation (Waves 0–3)
2. **`nextjs-project/`** — Buildable Next.js App Router project (Waves 3–4)

## Common pitfalls

| Pitfall | Fix |
|---------|-----|
| Trying to "read" minified CSS visually | Use `grep -oE` with regex. Never scroll through 100KB+ single-line blobs. |
| Ignoring CSS custom properties | `--color-*`, `--font-*`, `--ease-*` ARE the design system. Extract them FIRST. |
| Treating each CSS file independently | 12+ files are one system. Always grep across ALL `_files/*.css` simultaneously. |
| Not decoding CSS Module names | `Plans_card__SCfoV` = "Plans component, card element". The prefix IS the section identifier. |
| Documenting only inline styles | Inline `style=""` is the tip. The vast majority lives in external CSS matched by class names. |
| Assuming section boundaries from `<div>` | Use semantic tags + CSS Module prefix transitions, not `<div>` nesting. |
| Skipping shared section dedup | Document Header/Footer ONCE. Note page-specific variations as overrides. |
| Not deduplicating CSS files | Same hashed file appears in multiple `_files/` folders. Without dedup, counts inflate 2×. |
| Using Tailwind defaults instead of extracted values | Use ONLY values from the source snapshot in `tailwind.config.ts`. Never `bg-blue-500`. |
| Adding component libraries | No `shadcn/ui`, Material UI, Chakra, Radix. The extracted spec IS the component library. |
| Using Google Fonts CDN | Self-host ALL fonts. Download during Wave 0, load via `@font-face`. Zero CDN requests. |
| Guessing mobile layout | Source CSS has explicit `@media` queries. Extract and implement those exact rules. |
| Skipping animation extraction | Every `@keyframes`, `transition`, `IntersectionObserver` pattern is visual DNA. Extract all. |

## Minimal reading sets

### "I need to convert a saved HTML snapshot to Next.js"

- `references/input-output-spec.md`
- `references/wave-pipeline.md`
- `references/principles-and-rules.md`
- `references/foundations-agent.md`

### "I need to extract the design system only (no build)"

- `references/input-output-spec.md`
- `references/foundations-agent.md`
- `references/sections-agent.md`
- `references/quality-checklist.md`

### "I need to understand Wave 0 (per-page exploration)"

- `references/foundations-agent.md`
- `references/principles-and-rules.md`
- `references/website-patterns.md`

### "I need to write build briefs (Wave 2)"

- `references/section-template.md`
- `references/wave-pipeline.md`
- `references/quality-checklist.md`

### "I need to scaffold the Next.js project (Wave 3)"

- `references/system-template.md`
- `references/wave-pipeline.md`
- `references/input-output-spec.md`

### "I need to build pages pixel-perfect (Wave 4)"

- `references/wave-pipeline.md`
- `references/system-template.md`
- `references/quality-checklist.md`

### "I need the full quality checklist"

- `references/quality-checklist.md`
- `references/wave-pipeline.md`

### "I need to identify website patterns and section types"

- `references/website-patterns.md`
- `references/principles-and-rules.md`

## Reference index

| File | Purpose |
|------|---------|
| `references/input-output-spec.md` | Input formats, auto-detection, output tree structures, request interpretation |
| `references/wave-pipeline.md` | Wave 0–4 orchestration, agent spawning, gates, fleet rules |
| `references/principles-and-rules.md` | 7 principles, grounding rule, CSS Module decoding, section identification |
| `references/foundations-agent.md` | Wave 0 agent prompt — CSS parsing, token extraction, deobfuscation methodology |
| `references/sections-agent.md` | Wave 1 agent prompt — unified design soul extraction across pages |
| `references/section-template.md` | Wave 2 template — self-contained page build brief format |
| `references/system-template.md` | Wave 3 template — Next.js scaffold structure, quality gate spec |
| `references/website-patterns.md` | Pattern catalog — CSS Module prefix → section type mapping, website anatomy |
| `references/quality-checklist.md` | Quality gates — extraction completeness, build verification, signal prerequisites |

## Final reminder

This skill is split into focused reference files organized by concern. Do not load everything at once. Start with the smallest relevant reading set above, then expand only when the task requires it. Every reference file is explicitly routed from the decision tree above. Agents that skip their assigned reference file will produce incomplete or incorrectly formatted output, breaking downstream waves.
