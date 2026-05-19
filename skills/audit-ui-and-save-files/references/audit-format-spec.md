# css-issues/README.md — Format Spec

> This file is the **verbatim contents** to write to `<project>/css-issues/README.md` during Phase 2 of `audit-ui-and-save-files`. Every audit subagent reads this file as their format authority. Do not paraphrase — copy it byte-for-byte.

---

```markdown
# CSS / UI Issues — Visual Audit

Findings from a `/run-agent-browser` sweep of the running site across all routes. Each issue lives in its own markdown file so they can be triaged and fixed individually. The tree is **dated, context-scoped, and device-scoped** so the same site can be audited again later without overwriting history.

## Directory layout

```
css-issues/
  README.md                                   (this file — format spec)
  [YY-MM-DD]/                                  (one directory per audit run; computed once at run start)
    screenshots/                               (flat per-date directory; per-subagent prefix avoids collisions)
      <prefix>-<slug>-NN-<short-slug>.png
    [context]/                                  (the slice audited: dashboard / homepage / features / signup / ...)
      [device]/                                 (viewport slug: mobile-375 / desktop-1440 / tablet-768 / ...)
        01-<short-slug>.md
        02-<short-slug>.md
```

Number each issue file `01-`, `02-`, ... in the order it was discovered for that `[context]/[device]` pair. Slug should be 3–6 words, lowercase, hyphen-separated, describing the issue (e.g. `01-bento-cards-overlap-row2.md`).

### Canonical path example

```
css-issues/26-05-19/dashboard/mobile-375/03-overflow-on-table-headers.md
```

That path means: audited 2026-05-19, context = dashboard, viewport = iPhone-13 (375 × 812), third bug discovered for that pair.

### Choosing the context slug

Pick one granularity per audit; do not mix:

- **page-level** — `dashboard`, `homepage`, `pricing`, `signup`, `settings-profile`
- **flow-level** — `signup-flow`, `checkout-flow`, `onboarding`
- **component-family** — `tables`, `forms`, `modals`, `navigation`
- **section** — `homepage-hero`, `homepage-bento` (when one page is split across subagents)

### Canonical viewport (device) slugs

| Slug | Width × Height | Used for |
|---|---|---|
| `mobile-375` | 375 × 812 | iPhone-13 baseline; the brutal-truth viewport |
| `mobile-414` | 414 × 896 | iPhone Plus-class |
| `tablet-768` | 768 × 1024 | Where mega-menus collapse to slide-in panels |
| `tablet-1024` | 1024 × 768 | Where bento/feature grids go 2-col |
| `desktop-1280` | 1280 × 800 | Where 12-col grids often collapse to 8/4 |
| `desktop-1440` | 1440 × 900 | Primary design target on most modern sites |
| `desktop-1920` | 1920 × 1080 | Where max-width caps and white space appear |

You MAY add more (e.g. `mobile-360` for Android baseline, `desktop-2560` for 4K) but MUST justify in the handback Observations why the canonical set was insufficient.

## File format

Every issue file follows this exact template:

```markdown
# <Short issue title — what's broken>

- **Page:** <full URL>
- **Section / Context:** <e.g. Bento Grid row 2, Hero terminal mock, Footer column 4>
- **Viewport:** desktop-1440 (1440×900)  <!-- or mobile-375 / tablet-768 / etc. -->
- **Also affects:** mobile-375, tablet-768  <!-- list any other viewports where the same bug manifests; "none" if isolated -->
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

## Fix tracking

- [ ] Fixed by subagent #<TBD>
- **Approved at:** <Phase 5 timestamp, or "not yet approved">
- **Dispatch theme:** <Phase 5 theme name, or "unassigned">
- **Notes:** <Free-form, e.g. "merged with /pricing fix because same Tailwind class">
```

The `## Fix tracking` block is populated in two stages:

1. **At Phase 5 dispatch:** the audit-skill orchestrator writes the assigned subagent number, theme name, and approval timestamp before spawning the fix subagent.
2. **At fix-subagent return:** the fix subagent flips the checkbox to checked and appends a one-line note (e.g. `src changes in src/components/BentoGrid.tsx:118-124`).

If a finding is intentionally not going to be fixed in this round, the orchestrator writes `wontfix — <reason>` instead of dispatching it; the checkbox stays unchecked.

## Severity rubric

- **critical** — content unreadable, broken layout that blocks comprehension, overlap that makes a card unclickable, hero/CTA not visible above the fold on a standard viewport.
- **major** — clearly broken visually (cards overlap, text cut off, misaligned grid) but the page is still usable and the message comes across.
- **minor** — polish issues, spacing slightly off, color contrast slightly weak, hover state missing, animation timing off.

## Viewports to test

For each page, capture at minimum `desktop-1440` and `mobile-375`. The other viewports are visited when the desktop look is clean but a breakpoint between desktop-1440 and mobile-375 is suspect.

A single page does NOT need an issue file per viewport — file an issue once per actual bug. Note other viewports where it manifests in the `Also affects:` field.

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

- **Dated top-level directory** keeps audit history durable. Re-running this skill on the same project a month later does not overwrite the May audit; both live side-by-side and can be diffed.
- **`[context]/[device]/` two-level scoping** makes the dispatch step's theme-clustering trivial. A "mobile-375 overflow" theme grabs `*/mobile-375/*.md`; a "dashboard contrast" theme grabs `dashboard/*/*.md`. Both selectors are single globs because the tree was designed for them.
- **`NN-` ordinal prefix** preserves manual sort order within a `[context]/[device]/` pair. Discovery order is meaningful — the first issue noted is usually the most obvious / most visible.
- **One file per bug** keeps triage parallelizable — the fix-pass operator can take any single file and act on it in isolation, without parsing a 40-bullet document.
- **Required screenshot reference** makes every finding verifiable. A claim about a visual problem without a screenshot is not actionable.
- **`Likely cause` cites a source file path** so the fix-pass operator doesn't have to re-discover where the bug lives. The audit subagent has the codebase open — encode that information once.
- **`Suggested fix` is concrete** because the audit and fix operations are often separated by hours/days. A bug filed without a suggested fix forces the fix-pass operator to redo the diagnosis.
- **`Severity` is one of three labels** because a five-level rubric collapses to "everything is P2" in practice. Three forces real prioritization.
- **`## Fix tracking` block** is the connective tissue between Phase 4 (audit) and Phase 5 (dispatch). Without it, you can't tell which findings are still live and which have been resolved. The block is mandatory; subagents who omit it get pushed back.
- **`Also affects` is explicit** so the dispatch step can cluster cross-viewport bugs into a single theme without re-reading the source files of every finding.
