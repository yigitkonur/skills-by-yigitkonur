---
name: convert-url-to-nextjs
description: Use skill if you are converting live websites or saved HTML snapshots into grounded Next.js pages with browser capture, self-hosted assets, extracted styles, and screenshot-led fidelity verification.
---

# Capture / Snapshot to Next.js

Convert live sites or saved HTML snapshots into grounded Next.js App Router builds. Treat the source as evidence, not inspiration: capture first when the source is live, extract before build, then prove the rebuilt page matches with visual QA artifacts.

## Use this skill when

- Input is a live URL, a saved snapshot (`.html` + companion assets), a SingleFile export, or an unpacked offline site capture.
- The user wants to rebuild, recreate, convert, clone, recover, or extract a site into Next.js.
- Fidelity matters more than speed or creative redesign.
- The source repo is partially or fully lost, but production pages or browser artifacts still exist.

## Do not use this skill when

- The only source is a single screenshot, PDF export, Figma design, or loose design idea with no accessible live route or parseable HTML/CSS artifacts.
- The task is general Next.js UI coding with no reconstruction or grounded extraction requirement.
- The goal is a redesign, simplification, or `same vibe` rewrite instead of faithful reconstruction.

## Setup

| Key | Value |
|---|---|
| **Output location** | `nextjs-project/` plus `.design-soul/` beside the capture or snapshot working root |
| **Naming** | Route folders, capture identifiers, manifests, asset folders, CSS classes, and token names use kebab-case. React component files and exported component symbols use PascalCase. |
| **Minified CSS warning** | Captured or saved CSS may be minified (no trailing `;` before `}`). All grep patterns in references use `[^;}]+` to handle this — do not simplify to `[^;]+`. |

## Start with these decisions

| Situation | Action |
|---|---|
| Only a live URL exists | Run the Capture Wave first. Inventory routes, group page families, choose canonical exemplars, mirror route assets locally, then continue to Wave 0. |
| Live URL plus a narrow scope request | Capture only the in-scope routes, but still build a route manifest and page-family grouping before implementation. |
| `.html` + `_files/` folders present | Skip the Capture Wave. Start at Wave 0 and treat the snapshot as the primary artifact set. |
| `.html` with adjacent/local `.css` files but no `_files/` | Use adjacent-asset snapshot mode. Treat the referenced local CSS and assets as the Wave 0 corpus. |
| `.html` with inline `<style>` blocks but no `_files/` or local `.css` files | Use SingleFile fallback mode. Extract from inline styles and document reduced confidence. |
| `package.json` + source repo but no live site or snapshot | Fallback mode only. Read source directly, but keep the same grounding and verification rules. |
| Request says `extract`, `document`, `design system`, or `tokens` | Stop after the Capture Wave or Waves 0–2 unless the user explicitly asks for a build. |
| Request says `rebuild`, `recreate`, `convert`, `clone`, `recover`, or `pixel-perfect` | Run the full pipeline: Capture Wave (if needed) → Waves 0–4. |
| Source spans many routes or templates | Inventory routes first, group them into page families, finish one family completely, then fan out. |
| Request is ambiguous | Default to grounded extraction first. Do not assume a full rebuild. |

Read `references/input-output-spec.md` for input detection, working-root rules, route normalization, output trees, and ambiguity handling. Read `references/capture-workflow.md` when the source starts from a live URL.

## Operating contract

1. **Capture before extract when the source is live.** Build the route inventory, page-family manifest, screenshots, runtime metadata, mirrored asset roots, and grounded DOM artifacts before Wave 0. Read `references/capture-workflow.md` and `references/wave-pipeline.md`.
2. **Preserve the strongest offline artifact set.** `_files/` folders, adjacent local CSS, and inline styles are all valid snapshot evidence. Do not discard a snapshot because it does not match one filename convention.
3. **Route families before route fan-out.** Identify the shared shell and canonical page types before rebuilding every route. A convincing recovery comes from reusable structure, not bespoke one-off pages.
4. **Parse, don't guess.** Every value must trace to captured CSS, HTML, runtime metadata, or documented behavior. Read `references/principles-and-rules.md`.
5. **Screenshots are for verification, not invention.** Use screenshots and scroll slices to detect missed structure and measure fidelity; do not derive exact token values from pixels when CSS/HTML evidence exists.
6. **Build from extracted values only.** `tokens.ts`, `tailwind.config.ts`, `globals.css`, components, and route data must trace to Capture/Wave 0/Wave 1 artifacts. Mark incomplete values `UNVERIFIED` instead of substituting defaults.
7. **Self-host everything.** Fonts, images, icons, and other assets must end up local. No CDN fonts. No remote image URLs.
8. **Write signals last.** `done.signal` and `foundation-ready.signal` are written only after verification passes.
9. **If something cannot be grounded, mark it `UNVERIFIED`.** Honest gaps are allowed. Invented values are not.

## Do this / not that

| Do this | Not that |
|---|---|
| Capture live routes with a browser first and preserve DOM, screenshots, runtime metadata, and mirrored asset roots | Jump straight from a live homepage to hand-built JSX |
| Treat adjacent local CSS and assets as first-class snapshot evidence when `_files/` is missing | Reject a usable snapshot because it does not use the `_files/` naming convention |
| Group routes into page families and choose canonical exemplars before implementation | Treat every route as a unique page and duplicate similar layouts |
| Use CSS Module prefixes, semantic tags, heading outlines, and screenshot coverage together to identify sections | Infer structure from generic `<div>` nesting or above-the-fold screenshots alone |
| Search across the full discovered CSS corpus for the page, then deduplicate shared files | Read minified CSS by eye or treat each hashed CSS file as an isolated system |
| Carry exact source values through Capture/Wave 0 → Wave 4 | Round, normalize, or replace values because they look `close enough` |
| Run full-page and scroll-slice visual comparison loops before calling a route done | Declare success from build success or spot-checking only the top viewport |
| Keep the build dependency set limited to the scaffold rules in `references/system-template.md` | Add UI, icon, animation, or font packages for convenience |

## Required sequence

| Phase | Goal | Required reference | Primary outputs | Gate |
|---|---|---|---|---|
| Capture Wave | Route inventory, canonical page families, grounded browser artifacts | `references/capture-workflow.md` + `references/input-output-spec.md` + `references/wave-pipeline.md` | `.design-soul/capture/route-manifest.json`, `page-types.md`, `capture/{route}/dom.html`, `mirror/`, screenshots, runtime-metadata.json | `.design-soul/capture/done.signal` |
| Wave 0 | Per-page exploration and deobfuscation | `references/foundations-agent.md` | `wave0/{page}/exploration.md`, `deobfuscated.css`, `behavior-spec.md`, `assets/` | `wave0/{page}/done.signal` |
| Wave 1 | Unified design soul by page family | `references/sections-agent.md` | `wave1/{group}/design-soul.md`, `token-values.json`, `responsive-map.md` | `wave1/{group}/done.signal` |
| Wave 2 | Self-contained page build briefs | `references/section-template.md` | `wave2/{page}/agent-brief.md` | `wave2/{page}/done.signal` |
| Wave 3 | Next.js scaffold and design-system foundation | `references/system-template.md` | `nextjs-project/`, `wave3/foundation-brief.md`, `traceability-matrix.md` | `wave3/foundation-ready.signal` |
| Wave 4 | Page builds plus visual QA loops | `references/wave-pipeline.md` + `references/quality-checklist.md` | route files, page components, copied public assets, visual compare artifacts | final verification passes |

If the user only asked for extraction or documentation, stop after the appropriate phase instead of pushing to build.

## Asset and style handling rules

- Extract CSS custom properties, `@font-face`, `@media`, `@keyframes`, and transition values before touching the build.
- Treat Wave 1 `token-values.json` as the source of truth for tokens; Wave 3 only re-expresses those exact values in `tokens.ts`, Tailwind config, and `globals.css`.
- Copy fonts to `public/assets/fonts/`, images to `public/assets/images/...`, and icons to `public/assets/icons/` or inline them only when the source uses inline SVG.
- Preserve exact typography, spacing, gradients, shadows, radii, z-index, and breakpoint values.
- Preserve responsive behavior from real source media queries; do not substitute defaults if the capture uses different breakpoints.
- Preserve extracted interaction behavior, but only if it can be grounded from CSS or documented JS/runtime behavior specs.
- For inline `style=""` attributes or JS-driven states, extract the base CSS and the trigger separately; do not freeze computed runtime values into guessed static styles.

## Recovery rules

- **Live site available:** capture desktop, tablet, and mobile screenshots plus scroll slices before building. Preserve final DOM, script URLs, runtime metadata, mirrored stylesheets, and exposed asset URLs.
- **Next.js / runtime-heavy site:** record `__NEXT_DATA__`, `self.__next_f`, build IDs, chunk URLs, and route-level script/style manifests when present.
- **Missing `_files/` folder:** if the HTML references local CSS files, use adjacent-asset snapshot mode; if it only contains inline CSS, use SingleFile mode; otherwise full reconstruction may be blocked unless a live site can be captured.
- **Missing assets or remote-only assets:** download them during extraction and record original → local path mapping.
- **Missing fonts:** inspect captured network artifacts and stylesheet URLs. Download font files to `public/assets/fonts/` and create `@font-face` declarations. If the original font cannot be recovered, mark the substitution clearly.
- **External JS (analytics, chat widgets):** do not embed third-party scripts blindly. Document them separately and only re-add them if the user explicitly wants that behavior.
- **Missing CSS or JS evidence for a value or behavior:** mark it `UNVERIFIED` and avoid inventing the implementation.
- **Incomplete capture:** continue extraction where possible, but do not claim a pixel-perfect rebuild if core layout, type, asset, or below-the-fold evidence is missing.
- **Shared headers, footers, or page-family sections across routes:** deduplicate them intentionally; note route-specific overrides rather than re-documenting the whole component each time.

## CLI-verifiable acceptance criteria

Every conversion must pass these checks before declaring success:

```bash
# Install deps in nextjs-project/ first
npm install

# Type-check passes
npx tsc --noEmit

# Production build succeeds
npm run build

# No UNVERIFIED comments remain in shipped app code
grep -r 'UNVERIFIED' app/ components/ lib/ styles/ && echo "FAIL: unverified values" || echo "PASS"

# No external URLs leak into components or styles
grep -rE 'https?://' components/ styles/ | grep -v '// original:' && echo "FAIL: external URLs" || echo "PASS"
```

## Verification before claiming completion

- **After the Capture Wave:** verify route inventory completeness, route normalization, canonical page-family selection, mirrored asset roots, and screenshot coverage at desktop, tablet, mobile, plus scroll slices for long pages.
- **After extraction (before Wave 3):** run the grounding test and cross-reference checks from `references/quality-checklist.md`.
- **Before `foundation-ready.signal`:** verify extracted CSS custom properties and shared tokens are accounted for, allowed dependency set, self-hosted fonts/assets, traceability matrix, and clean TypeScript/build checks.
- **Before final completion:** compare source vs build at 1280px, 768px, and 375px using full-page and scroll-segment captures; record visual summaries instead of relying on subjective judgment.
- If any verification fails, fix it before writing the completion signal or calling the build done.

## Reference map

| Need | Read |
|---|---|
| Live-capture prerequisites, working root, route normalization, canonical exemplar selection | `references/capture-workflow.md` |
| Input detection, capture outputs, output trees, ambiguous requests | `references/input-output-spec.md` |
| Hard rules: grounding, section identification, zero invention | `references/principles-and-rules.md` |
| Wave 0 extraction method | `references/foundations-agent.md` |
| Wave 1 design-soul extraction | `references/sections-agent.md` |
| Wave 2 build-brief format | `references/section-template.md` |
| Wave 3 scaffold, token wiring, allowed deps | `references/system-template.md` |
| Full orchestration, Capture Wave, and gates | `references/wave-pipeline.md` |
| Acceptance criteria, visual QA, and failure modes | `references/quality-checklist.md` |
| Section-type and anatomy heuristics | `references/website-patterns.md` |

Read only the references needed for the current phase. Keep the top-level skill focused on decisions, sequencing, and guardrails; keep implementation detail in the reference files.
