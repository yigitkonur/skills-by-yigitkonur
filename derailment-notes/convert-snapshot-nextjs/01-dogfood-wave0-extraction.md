# Derailment Test: convert-snapshot-nextjs — Wave 0 (Extraction)

Date: 2025-07-15
Skill under test: convert-snapshot-nextjs
Test task: Convert Acme SaaS dark-theme homepage snapshot (7 sections, 3 CSS files, inline SVGs)
Method: Follow SKILL.md → foundations-agent.md steps literally

---

## Friction points

### CSS Variable Extraction

**F-01 — `[^;]+` regex corrupts values on minified CSS** (P0)
Minified CSS omits trailing `;` before `}`: `:root{--bg:#0a0a0a;--text:#fff}`.
`grep -ohE '--[a-z-]+:[^;]+' *.css` matches past `}` into the next rule, returning `#fff}.hero{display:flex`.
Fix: Replace `[^;]+` with `[^;}]+` globally (57 patterns across 3 reference files).

**F-02 — `grep -A1 ':root'` fails on single-line minified CSS** (P0)
Instructions say `grep -A1 ':root'` but minified CSS is one line — `-A1` returns the entire file.
Fix: Use block extraction `grep -oE ':root\{[^}]+\}'` instead.

**F-03 — No warning that CSS may be minified** (P1)
Instructions assume multi-line CSS. No mention that snapshots often contain minified stylesheets.
Fix: Add minified CSS warning to SKILL.md Setup section.

### Color Extraction

**F-04 — Dark theme extraction with `grep -A5` also fails on minified** (P1)
Same root cause as F-02 for `[data-theme="dark"]` and `prefers-color-scheme: dark` patterns.
Fix: Block extraction patterns for all theme variants.

**F-05 — No deduplication guidance for color values** (P2)
Multiple CSS files may define the same custom property. No instruction to deduplicate.
Fix: Add `| sort -u` to extraction pipelines.

### Typography Extraction

**F-06 — Font family not found in CSS variables** (P1)
Fonts were set via `font-family` property, not CSS variables. Instructions only grep for `--font-*` variables.
Fix: Add fallback grep for `font-family:[^;}]+` when no font variables found.

**F-07 — Missing font recovery path** (P1)
When Google Fonts `<link>` exists but no local font files, instructions don't say what to do.
Fix: Add missing-resource recovery section to SKILL.md.

### Spacing & Layout

**F-08 — `gap` property extracted but not contextualized** (P2)
`grep -ohE 'gap:[^;}]+'` returns `gap:1rem`, `gap:2rem` etc. but no guidance on mapping to design tokens.
Fix: Acceptable as-is; the sections agent handles this mapping.

### Shadow & Border Radius

**F-09 — Multiple `box-shadow` values conflated** (P2)
Some elements have multi-layer shadows. Grep returns them as one string. No parsing guidance.
Fix: Acceptable for MVP; values are copy-pasted into Tailwind config.

### Transform & Animation

**F-10 — `transform` grep catches `text-transform`** (P1)
`grep -ohE 'transform:[^;}]+'` matches both `transform: translateY(-1px)` and `text-transform: uppercase`.
Fix: Pipe through `grep -v 'uppercase\|capitalize\|lowercase'`.

### Grep Flag Issues

**F-11 — `--color-*` patterns interpreted as grep flags** (P0)
`grep -oE '--color-bg'` — the `--` is parsed as end-of-options, `color-bg` becomes the pattern.
Fix: Use `grep -oE -e '--color-bg'` (-e flag).

**F-12 — No output location specified** (P1)
Instructions don't say where to create the Next.js project directory.
Fix: Add to Setup section: `{page}-nextjs/` sibling to snapshot dir.

---

## What worked well

1. The section inventory step (listing all semantic sections) was clear and actionable
2. Image/asset cataloguing instructions were precise
3. The two-pass approach (global tokens → per-section) is sound

## Priority summary

| Priority | Count | Friction points |
|---|---|---|
| P0 | 3 | F-01, F-02, F-11 |
| P1 | 5 | F-03, F-04, F-06, F-07, F-10, F-12 |
| P2 | 3 | F-05, F-08, F-09 |
