# css-issues/README.md — Format Spec

> This file is the **verbatim contents** to write to `<project>/css-issues/README.md` during Phase 2 of `audit-ui`. Every audit subagent reads this file as their format authority. Do not paraphrase — copy it byte-for-byte.

---

```markdown
# CSS / UI Issues — Visual Audit

Findings from a `/run-agent-browser` sweep of the running site across all routes. Each issue lives in its own markdown file so they can be triaged and fixed individually.

## Directory layout

```
css-issues/
  README.md                         (this file — format spec)
  screenshots/                      (all PNGs land here)
  homepage/
    <context>/                      (section name: bento-grid / hero / nav / footer / ...)
      01-<short-slug>.md
      02-<short-slug>.md
  features/
    <slug>/                         (answer-engine-insights / prompt-volumes / ...)
      <context>/
        01-<short-slug>.md
  pricing/
    <context>/
      01-<short-slug>.md
  customers/  enterprise/  docs/  ...
    <context>/
      01-<short-slug>.md
```

Number each issue file `01-`, `02-`, ... in the order it was discovered for that `[page]/[context]` pair. Slug should be 3–6 words, lowercase, hyphen-separated, describing the issue (e.g. `01-bento-cards-overlap-row2.md`).

## File format

Every issue file follows this exact template:

```markdown
# <Short issue title — what's broken>

- **Page:** <full URL>
- **Section / Context:** <e.g. Bento Grid row 2, Hero terminal mock, Footer column 4>
- **Viewport:** 1440x900  (or 1280x800 / 1024x768 / 768x1024 / 375x812)
- **Severity:** critical | major | minor
- **Detected via:** /run-agent-browser

## Screenshot

![issue](../../screenshots/<filename>.png)

## Observation

What is visibly broken. Describe what you see, not what you think caused it.
Be specific: "the third bento card's text overflows past its right border by ~40px"
beats "card is broken."

## Likely cause

DOM / CSS hypothesis. Cite the file and (best-effort) line range that probably
owns the bug — e.g. `src/components/BentoGrid.tsx:118` (the BentoCard wrapper
uses min-height instead of clamped height, causing row collapse).

## Suggested fix

Concrete change. One or two lines if possible. Examples:
- "Add `overflow-hidden` to the card root, or clip the inline visual's
  absolute-positioned children."
- "Change `min-h-[280px]` → `h-[320px]` on the wide-hero span so it doesn't
  vary with content length."
```

## Severity rubric

- **critical** — content unreadable, broken layout that blocks comprehension, overlap that makes a card unclickable, hero/CTA not visible above the fold on a standard viewport.
- **major** — clearly broken visually (cards overlap, text cut off, misaligned grid) but the page is still usable and the message comes across.
- **minor** — polish issues, spacing slightly off, color contrast slightly weak, hover state missing, animation timing off.

## Viewports to test

For each page, capture at minimum:

| Viewport | Width × Height | Reason |
|---|---|---|
| Desktop XL | 1440 × 900 | Primary design target |
| Desktop M | 1280 × 800 | Where multi-col grids often collapse |
| Tablet | 1024 × 768 | Where bento/feature grids go 2-col |
| Mobile L | 768 × 1024 | Where mega-menus collapse to slide-in panels |
| Mobile S | 375 × 812 | iPhone 13 standard |

A single page does NOT need an issue file per viewport — file an issue once per actual bug. Note viewport(s) where it manifests inside the file body.

## What to look for

- Overlapping elements (cards on top of cards, text on top of visuals)
- Text truncation / overflow
- Misaligned grids, broken column counts
- Inconsistent spacing between sections
- Hover states missing or broken
- Z-index collisions (e.g. dropdown behind content)
- Particle canvases drawing in wrong area or escaping their container
- Reduced-motion behavior (static silhouette where it should be motion)
- Mobile menu open/close glitches
- Image aspect ratios broken (placeholder images loading at wrong size)
- Brand-logo fallback tile showing when the real logo should load
- Contrast issues on dark surfaces (white/40 text on a particle background can be unreadable)
- Horizontal overflow at narrow viewports (page-level x-scroll appearing on mobile)
- Sticky elements (cookie banners, navbars) overlapping content on scroll
- Animation glitches (scroll-reveal elements stuck at opacity:0)
- Placeholder-image debug text leaking into the rendered visual
```

---

## Why this exact format

- **One file per bug** keeps triage parallelizable — the fix-pass operator can take any single file and act on it in isolation, without parsing a 40-bullet document.
- **Required screenshot reference** makes every finding verifiable. A claim about a visual problem without a screenshot is not actionable.
- **`Likely cause` cites a source file path** so the fix-pass operator doesn't have to re-discover where the bug lives. The audit subagent has the codebase open — encode that information once.
- **`Suggested fix` is concrete** because the audit and fix operations are often separated by hours/days. A bug filed without a suggested fix forces the fix-pass operator to redo the diagnosis.
- **Severity is one of three labels** because a five-level rubric collapses to "everything is P2" in practice. Three forces real prioritization.
- **Viewport list is canonical** so cross-page comparisons are possible. If one page is "broken at 768" and another is "broken at 800", you can't compare them.
