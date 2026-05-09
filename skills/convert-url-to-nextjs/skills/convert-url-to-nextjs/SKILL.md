---
name: convert-url-to-nextjs
description: Use skill if you are converting a live URL, .html snapshot, or SingleFile export into a buildable Next.js App Router project with self-hosted assets and extracted styles.
---

# Convert URL or HTML Snapshot to Next.js

Rebuild a live page or saved HTML snapshot as a faithful Next.js App Router project. Treat the source as **evidence**, not inspiration: capture first when live, extract before build, prove fidelity with screenshots, and never invent a value that the source doesn't ground.

## When to use this skill

- *"Rebuild this URL as a Next.js site"* (live URL, with or without scope filtering).
- *"Convert this `.html` snapshot / SingleFile export into Next.js"* (offline `.html` + `_files/`, adjacent local CSS, or inline `<style>` only).
- *"Recover this page — the original repo is gone but the prod URL still works"* (lost-source recovery from production artifacts).
- *"Clone / recreate / pixel-perfect / faithful rebuild"* of an existing public page in Next.js.
- *"Extract design tokens, fonts, and CSS variables from this URL/snapshot"* without a build (stop after Wave 1).
- *"Mirror this site offline as a Next.js app"* with self-hosted fonts, images, and icons.

## Do NOT use this skill when

- The only source is a screenshot, PDF, Figma, or "vibe" reference — there is no parseable HTML/CSS or live route. Use `extract-saas-design` or a generic UI-build skill instead.
- The user wants a **redesign, simplification, or "same vibe" rewrite** rather than faithful reconstruction.
- The user wants generic Next.js UI work with no source URL or snapshot grounding.
- The user wants a TinaCMS-backed editorial site from scratch — use `build-tinacms-nextjs`.

## Sibling routing

| Need | Route to |
|---|---|
| Browser capture as part of *this* pipeline | `run-agent-browser` (preferred Capture Wave helper). |
| Playwright capture | `run-playwright` only when explicitly requested or `run-agent-browser` is unavailable. |
| Design-doc-only output for SaaS/dashboard/admin | `extract-saas-design`. Use this skill only when the deliverable is a buildable Next.js page. |
| New CMS-backed Next.js site | `build-tinacms-nextjs`. This skill is for URL/snapshot reconstruction, not CMS scaffolding. |

## Setup contract

| Key | Value |
|---|---|
| **Output location** | `nextjs-project/` plus `.design-soul/` beside the capture or snapshot working root. |
| **Naming** | Routes, capture IDs, manifests, asset folders, CSS classes, and tokens use kebab-case. React component files and exported component symbols use PascalCase. |
| **Minified-CSS warning** | Captured/saved CSS is often minified (no trailing `;` before `}`). Reference grep patterns use `[^;}]+` — do not simplify to `[^;]+`, or extraction will silently miss values. |
| **Allowed deps** | Limited to the scaffold rules in `references/system-template.md`. No icon, animation, or font packages added for convenience. |

## Scripts

| Phase | Helper | Use |
|---|---|---|
| Capture Wave | `scripts/capture-url.sh` (read `scripts/capture-url.md`) | Build the route capture skeleton, record expected artifacts, run the supplied browser-capture command. Never write a success signal on failure. |
| Wave 0 | `scripts/extract-styles.sh` (read `scripts/extract-styles.md`) | Detect the page CSS corpus and emit manifests plus custom-property, font, media-query, and keyframe summaries before manual extraction. |
| Wave 4 | `scripts/diff-screenshots.sh` (read `scripts/diff-screenshots.md`) | Compare source vs build screenshots / paired directories and emit `.design-soul/visual/{route}/summary.json`. Do not fabricate diff metrics when tooling is missing. |

## Decide first: which input mode are you in?

| Situation | First action |
|---|---|
| Live URL only | Run the **Capture Wave** first. Inventory routes, group page families, choose canonical exemplars, mirror assets locally, then continue to Wave 0. |
| Live URL + narrow scope request | Capture only in-scope routes, but still produce a route manifest and page-family grouping before implementing. |
| `.html` + `_files/` folders present | Skip the Capture Wave. Start at Wave 0 and treat the snapshot as the primary artifact set. |
| `.html` + adjacent local `.css` files, no `_files/` | Use **adjacent-asset snapshot mode**. The local CSS and assets are the Wave 0 corpus. |
| `.html` with inline `<style>` only | Use **SingleFile fallback mode**. Extract from inline styles and document reduced confidence. |
| `package.json` + source repo, no live site, no snapshot | **Source-fallback mode**: read source directly. Same grounding/verification rules apply. |
| Request says *extract*, *document*, *design system*, or *tokens* | Stop after the Capture Wave or Waves 0–2 unless the user explicitly asks to build. |
| Request says *rebuild*, *recreate*, *convert*, *clone*, *recover*, or *pixel-perfect* | Run the full pipeline: Capture Wave (if needed) → Waves 0–4. |
| Source spans many routes / templates | Inventory routes first, group into page families, finish one family completely, then fan out. |
| Request is ambiguous | Default to grounded extraction first. Do not assume a full rebuild. |

Read `references/input-output-spec.md` for input detection, working-root rules, route normalization, output trees, and ambiguity handling. Read `references/capture-workflow.md` when starting from a live URL.

## Operating contract (load-bearing rules)

1. **Capture before extract when the source is live.** Build the route inventory, page-family manifest, screenshots, runtime metadata, mirrored asset roots, and grounded DOM artifacts before Wave 0. See `references/capture-workflow.md` and `references/wave-pipeline.md`.
2. **Preserve the strongest offline artifact set.** `_files/` folders, adjacent local CSS, and inline styles are all valid snapshot evidence. Do not discard a snapshot because it does not match one filename convention.
3. **Route families before route fan-out.** Identify the shared shell and canonical page types before rebuilding every route. Convincing recovery comes from reusable structure, not bespoke one-off pages.
4. **Parse, don't guess.** Every value must trace to captured CSS, HTML, runtime metadata, or documented behavior. See `references/principles-and-rules.md`.
5. **Screenshots are for verification, not invention.** Use full-page and scroll-slice screenshots to detect missed structure and to measure fidelity — not to derive token values when CSS/HTML evidence exists.
6. **Build from extracted values only.** `tokens.ts`, `tailwind.config.ts`, `globals.css`, components, and route data must trace to Capture/Wave 0/Wave 1 artifacts. Mark unverifiable values `UNVERIFIED` rather than substituting defaults.
7. **Self-host everything.** Fonts, images, icons, and other assets must end up local. No CDN fonts. No remote image URLs.
8. **Preserve asset provenance.** Record original source URLs and asset origins. Self-host captured images, fonts, and icons only when the user owns or has permission to use them; otherwise mark replacements `UNVERIFIED` or user-supplied. Workflow guardrail, not legal advice.
9. **Write signals last.** `done.signal` and `foundation-ready.signal` are written only after verification passes for that wave.
10. **If something cannot be grounded, mark it `UNVERIFIED`.** Honest gaps are allowed. Invented values are not.

## Do this / not that

| Do this | Not that |
|---|---|
| Capture live routes with a browser first; preserve DOM, screenshots, runtime metadata, and mirrored asset roots | Jump straight from a live homepage to hand-built JSX |
| Treat adjacent local CSS and inline styles as first-class snapshot evidence when `_files/` is missing | Reject a usable snapshot because it does not use `_files/` naming |
| Group routes into page families and choose canonical exemplars before implementation | Treat every route as a unique page and duplicate similar layouts |
| Use CSS Module prefixes, semantic tags, heading outlines, and screenshot coverage together to identify sections | Infer structure from generic `<div>` nesting or above-the-fold screenshots alone |
| Search across the full discovered CSS corpus per page, then deduplicate shared files | Read minified CSS by eye or treat each hashed CSS file as an isolated system |
| Carry exact source values through Capture / Wave 0 → Wave 4 | Round, normalize, or replace values because they look "close enough" |
| Run full-page and scroll-slice visual comparison loops before calling a route done | Declare success from build success or spot-checking only the top viewport |
| Keep deps to the scaffold rules in `references/system-template.md` | Add UI, icon, animation, or font packages for convenience |

## Required sequence

| Phase | Goal | Required reference | Primary outputs | Gate |
|---|---|---|---|---|
| Capture Wave | Route inventory, canonical page families, grounded browser artifacts | `references/capture-workflow.md` + `references/input-output-spec.md` + `references/wave-pipeline.md` | `.design-soul/capture/route-manifest.json`, `page-types.md`, `capture/{route}/dom.html`, `mirror/`, screenshots, `runtime-metadata.json` | `.design-soul/capture/done.signal` |
| Wave 0 | Per-page exploration and deobfuscation | `references/foundations-agent.md` | `wave0/{page}/exploration.md`, `deobfuscated.css`, `behavior-spec.md`, `assets/` | `wave0/{page}/done.signal` |
| Wave 1 | Unified design soul by page family | `references/sections-agent.md` | `wave1/{group}/design-soul.md`, `token-values.json`, `responsive-map.md` | `wave1/{group}/done.signal` |
| Wave 2 | Self-contained page build briefs | `references/section-template.md` | `wave2/{page}/agent-brief.md` | `wave2/{page}/done.signal` |
| Wave 3 | Next.js scaffold and design-system foundation | `references/system-template.md` | `nextjs-project/`, `wave3/foundation-brief.md`, `traceability-matrix.md` | `wave3/foundation-ready.signal` |
| Wave 4 | Page builds plus visual QA loops | `references/wave-pipeline.md` + `references/quality-checklist.md` | route files, page components, copied public assets, visual compare artifacts | final verification passes |

If the user only asked for extraction or documentation, stop after the appropriate phase instead of pushing to build.

Think first:
- **Capture Wave:** Which browser helper produces the complete evidence contract for this source?
- **Wave 0:** Which CSS corpus is strongest for this page — mirrored live capture, `_files/`, adjacent CSS, inline CSS, or source fallback?
- **Wave 3:** Which routes stay static, and which exact interactions justify Client Components?
- **Wave 4:** What visual claim can the screenshot evidence actually support?

Anatomy heuristics for identifying section/page types live in `references/website-patterns.md`.

## Asset and style handling rules

- Extract CSS custom properties, `@font-face`, `@media`, `@keyframes`, and transition values before touching the build.
- Treat extracted CSS/HTML/runtime artifacts as the source of truth; Tailwind config is just the build expression that re-expresses those values in the scaffold.
- Treat Wave 1 `token-values.json` as the source of truth for tokens; Wave 3 only re-expresses those exact values in `tokens.ts`, Tailwind config, and `globals.css`.
- Copy fonts to `public/assets/fonts/`, images to `public/assets/images/...`, icons to `public/assets/icons/`, or inline icons only when the source uses inline SVG.
- For captured assets, preserve original URL, local path, capture source, and permission/provenance status in the asset manifest.
- Preserve exact typography, spacing, gradients, shadows, radii, z-index, and breakpoint values.
- Preserve responsive behavior from real source media queries; do not substitute defaults if the capture uses different breakpoints.
- Preserve extracted interaction behavior only if it can be grounded from CSS or documented JS/runtime behavior specs.
- For inline `style=""` attributes or JS-driven states, extract the base CSS and the trigger separately; do not freeze computed runtime values into guessed static styles.

## Next.js output decisions

- **Package policy:** create `package.json` from a current official Next.js App Router scaffold, or verify package compatibility against official Next.js docs at execution time. Do not pin `latest` package versions by guesswork.
- **Static by default:** marketing and brochure pages should be Server Components / static output unless grounded interactions require browser APIs.
- **Client Components only with evidence:** use Client Components for captured behaviors such as menus, accordions, billing toggles, carousels, scroll observers, or form state.
- **Third-party scripts:** do not recreate analytics, chat, tag managers, or embeds unless the user explicitly requests that behavior.
- **Route structure:** preserve the source route structure and generate one App Router route per in-scope route.
- **Images:** use local images with known dimensions, meaningful alt text, `sizes`, and `priority` for LCP/hero imagery. Do not add `next.config.js` remote image domains unless a temporary verification-only exception is documented.

## Recovery rules

- **Live site available:** capture desktop, tablet, and mobile screenshots plus scroll slices before building. Preserve final DOM, script URLs, runtime metadata, mirrored stylesheets, and exposed asset URLs.
- **Next.js / runtime-heavy site:** record `__NEXT_DATA__`, `self.__next_f`, build IDs, chunk URLs, and route-level script/style manifests when present.
- **Missing `_files/` folder:** if HTML references local CSS files, use adjacent-asset snapshot mode; if it only contains inline CSS, use SingleFile mode; otherwise full reconstruction may be blocked unless a live site can be captured.
- **Missing assets / remote-only assets:** download them during extraction and record original → local path mapping.
- **Missing fonts:** inspect captured `@font-face`, CSS `url(...)`, runtime font URLs, and local `.woff2` / `.woff` / `.ttf` / `.otf` files. Verify weight/style coverage and `font-display`; if the original cannot be recovered, document the missing source and mark the substitution `UNVERIFIED`.
- **External JS (analytics, chat widgets):** do not embed third-party scripts blindly. Document them separately and re-add only if the user explicitly wants that behavior.
- **Missing CSS or JS evidence for a value or behavior:** mark it `UNVERIFIED`; avoid inventing the implementation.
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
- **Before `foundation-ready.signal`:** verify extracted CSS custom properties and shared tokens are accounted for, dependency set is allowed, fonts/assets are self-hosted, traceability matrix exists, and TypeScript/build are clean.
- **Before final completion:** compare source vs build at 1280px, 768px, and 375px using full-page and scroll-segment captures; record visual summaries instead of relying on subjective judgment.
- If any verification fails, fix it before writing the completion signal or calling the build done.

## Final report contract

- `Verification rung reached`: state the actual rung and evidence — for example `build/type-check only` or `browser-run visual comparison with summary.json`.
- `pixel-perfect`: claim only when the user provided a threshold or exact measured diff gate **and** desktop/tablet/mobile/full-page artifacts meet it.
- `visual-equivalent`: use when comparison artifacts support fidelity but documented drift remains because source evidence is incomplete.
- Build success alone is never a visual fidelity claim.

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
