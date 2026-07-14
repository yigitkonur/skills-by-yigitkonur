---
name: convert-url-to-nextjs
description: "Use if rebuilding a live URL or .html snapshot as a pixel-faithful AS-IS Next.js project."
---

# Convert URL or HTML Snapshot to Next.js — AS-IS Pixel-Faithful Rebuild

## The scenario this skill is built for

A company lost the GitHub repo behind its frontend. The only thing left is the production build at `example.com`. The team wants the same-looking site back in their own stack — as a real, editable Next.js codebase — pixel-faithful to the deployed build, AS IS. The skill's job is to *recover what is already in the world*, not to redesign it. Throughout this workflow, when a judgment call surfaces between visual fidelity to the live deployed build and a more idiomatic Next.js choice, fidelity wins until the user explicitly opts out.

The output is one Next.js template per unique page type the source actually uses, plus a route map saying which live URLs are instances of which type. The user's expected next step after this skill finishes is usually to wire dynamic content (TinaCMS, MDX, or any CMS of their choice) onto those templates.

## When to use this skill

- *"Rebuild this URL as a Next.js site"* (live URL, with or without scope filtering).
- *"I lost my frontend repo and only have the build — recover the deployed site"* (the canonical lost-frontend scenario).
- *"Recover this page — the original repo is gone but the prod URL still works"* (production-only recovery).
- *"Convert this `.html` snapshot / SingleFile export into Next.js"* (offline `.html` + `_files/`, adjacent local CSS, or inline `<style>` only).
- *"Clone / recreate / pixel-perfect / faithful rebuild"* of an existing public page in Next.js.
- *"Mirror this site offline as a Next.js app"* with self-hosted fonts, images, and icons.

## Do NOT use this skill when

- The only source is a screenshot, PDF, Figma, or "vibe" reference — there is no parseable HTML/CSS or live route. This skill needs inspectable implementation to rebuild; with no HTML to crawl, use a generic UI-build path instead.
- The user wants a **redesign, simplification, or "same vibe" rewrite** rather than faithful reconstruction.
- The user wants generic Next.js UI work with no source URL or snapshot grounding.
- The user wants a TinaCMS-backed editorial site from scratch — use `build-tinacms-nextjs`.

## Sibling routing

| Need | Route to |
|---|---|
| Browser capture and the back-to-back verification loop in *this* pipeline | `run-agent-browser` is the helper this skill drives. |
| Design-doc-only output for SaaS/dashboard/admin | a generic design-documentation path. Use this skill only when the deliverable is a buildable Next.js page. |
| New CMS-backed Next.js site | `build-tinacms-nextjs`. This skill is for URL/snapshot reconstruction, not CMS scaffolding. The user typically uses `build-tinacms-nextjs` *after* this skill, to wire content onto the recovered templates. |

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
| Capture | `scripts/capture-url.sh` (read `scripts/capture-url.md`) | Build the route capture skeleton, record expected artifacts, run the supplied browser-capture command. Never write a success signal on failure. |
| Wave 0 | `scripts/extract-styles.sh` (read `scripts/extract-styles.md`) | Detect the page CSS corpus and emit manifests plus custom-property, font, media-query, and keyframe summaries before manual extraction. |
| Verification | `scripts/diff-screenshots.sh` (read `scripts/diff-screenshots.md`) | Compare source vs build screenshots / paired directories and emit `.design-soul/visual/{route}/summary.json`. Do not fabricate diff metrics when tooling is missing. |

## Decide first: which input mode are you in?

| Situation | First action |
|---|---|
| Live URL only — the lost-frontend default | Run the **Capture Wave** on L0, then crawl L1 from the homepage, then run **type extraction**. See `references/type-extraction.md`. |
| Live URL + narrow scope request | Capture only in-scope L0+L1 routes, but still produce the route manifest and per-type cluster before implementing. |
| `.html` + `_files/` folders present | Skip live capture. Treat the snapshot as Wave 0 input directly; if multiple snapshots are present, still run type extraction on them. |
| `.html` + adjacent local `.css` files, no `_files/` | Use **adjacent-asset snapshot mode**. The local CSS and assets are the Wave 0 corpus. |
| `.html` with inline `<style>` only | Use **SingleFile fallback mode**. Extract from inline styles and document reduced confidence. |
| `package.json` + source repo, no live site, no snapshot | **Source-fallback mode**: read source directly. Same grounding/verification rules apply. |
| Request says *extract*, *document*, *design system*, or *tokens* | Stop after the Capture Wave or Waves 0–2 unless the user explicitly asks to build. |
| Request says *rebuild*, *recreate*, *convert*, *clone*, *recover*, or *pixel-perfect* | Run the full pipeline: Capture → Type Extraction → Waves 0–4 → Back-to-back verification → Report back to user. |
| Source spans many routes / templates | The type-extraction phase handles this — cluster L1 URLs into unique types first, finish one type completely, then fan out. |
| Request is ambiguous | Default to grounded extraction first. Do not assume a full rebuild. |

Read `references/input-output-spec.md` for input detection, working-root rules, route normalization, output trees, and ambiguity handling. Read `references/capture-workflow.md` when starting from a live URL.

## Operating contract (load-bearing rules)

1. **Fidelity to the deployed build is the goal.** When a judgment call surfaces between visual fidelity and an "improvement," fidelity wins. Ask the user before deviating.
2. **Capture before extract when the source is live.** Build the L0+L1 route inventory, layout fingerprints, screenshots, runtime metadata, mirrored asset roots, and grounded DOM artifacts before Wave 0. See `references/capture-workflow.md` and `references/type-extraction.md`.
3. **One template per unique page type, not one template per URL.** See `references/type-extraction.md`.
4. **Preserve the strongest offline artifact set.** `_files/` folders, adjacent local CSS, and inline styles are all valid snapshot evidence. Do not discard a snapshot because it does not match one filename convention.
5. **Parse, don't guess.** Every value must trace to captured CSS, HTML, runtime metadata, or documented behavior. See `references/principles-and-rules.md`.
6. **Screenshots are for verification, not invention.** Use full-page and scroll-slice screenshots to detect missed structure and to measure fidelity — not to derive token values when CSS/HTML evidence exists.
7. **Build from extracted values only.** `tokens.ts`, `tailwind.config.ts`, `globals.css`, components, and route data must trace to Capture/Wave 0/Wave 1 artifacts. Mark unverifiable values `UNVERIFIED` rather than substituting defaults.
8. **Self-host everything.** Fonts, images, icons, and other assets must end up local. No CDN fonts. No remote image URLs.
9. **Preserve asset provenance.** Record original source URLs and asset origins. Self-host captured images, fonts, and icons only when the user owns or has permission to use them; otherwise mark replacements `UNVERIFIED` or user-supplied. Workflow guardrail, not legal advice.
10. **Verify back-to-back against the original before claiming a type is done.** See `references/back-to-back-verification.md`.
11. **If something cannot be grounded, mark it `UNVERIFIED`.** Honest gaps are allowed. Invented values are not.

## Do this / not that

| Do this | Not that |
|---|---|
| Treat the live deployed page as ground truth; recover AS IS | "Improve," modernize, or redesign while rebuilding |
| Capture L0 + every L1 link; cluster L1 by layout fingerprint into unique page types | Generate one Next.js route per URL |
| Produce one Next.js template per unique page type | Duplicate similar layouts as bespoke per-route JSX |
| Use CSS Module prefixes, semantic tags, heading outlines, and screenshot coverage together to identify sections | Infer structure from generic `<div>` nesting or above-the-fold screenshots alone |
| Search across the full discovered CSS corpus per page, then deduplicate shared files | Read minified CSS by eye or treat each hashed CSS file as an isolated system |
| Carry exact source values through Capture / Wave 0 → Wave 4 | Round, normalize, or replace values because they look "close enough" |
| Run the back-to-back verification loop at 1440/768/375 per type before declaring done | Declare success from build success or spot-checking only the top viewport |
| Keep deps to the scaffold rules in `references/system-template.md` | Add UI, icon, animation, or font packages for convenience |

## The phased workflow at a glance

| Phase | Goal | Required reference | Primary outputs | Gate |
|---|---|---|---|---|
| 1. Capture (L0 + L1) | Crawl homepage and every same-origin link from it; capture hydrated DOM, screenshots, runtime metadata, and mirrored assets per URL | `references/capture-workflow.md` + `references/input-output-spec.md` | `.design-soul/capture/{route}/dom.html`, `mirror/`, screenshots, `runtime-metadata.json` | per-route capture artifacts present |
| 2. Type extraction (NEW NAMED PHASE) | Cluster L1 URLs into **unique page types** by layout fingerprint; choose a canonical exemplar per type; emit `route-map.json` | `references/type-extraction.md` | `.design-soul/types/route-map.json`, `page-types.md`, per-URL fingerprints | `route-map.json` complete, one exemplar per type |
| 3. Per-type rebuild | For each type, extract tokens (Wave 0), unify family (Wave 1), brief the build (Wave 2), scaffold (Wave 3), render (Wave 4) into **one** Next.js template per type | `references/foundations-agent.md`, `references/sections-agent.md`, `references/section-template.md`, `references/system-template.md`, `references/wave-pipeline.md`, `references/website-patterns.md` | `nextjs-project/app/...` (one template per type) | `wave3/foundation-ready.signal` + per-type Wave 4 build passes |
| 4. Back-to-back verification (NEW NAMED PHASE) | Per type, drive `run-agent-browser` to load the **original** exemplar URL and the **candidate** Next.js URL at the same viewport; compare; pass/iterate/escalate | `references/back-to-back-verification.md` + `scripts/diff-screenshots.md` | `.design-soul/verify/{type}/iterations.json`, screenshots, `summary.md`, `verification-report.md` | all types pass at desktop/tablet/mobile, or user-approved residual drift |
| 5. Report back to the user (NEW NAMED PHASE) | Surface every type found, the L1 URLs it covers, the template path, the verification evidence, the residual drift, and the recommended next step | This SKILL.md — "Report back to the user" section below | `RECOVERY-REPORT.md` at the working root | user has the complete map of what was rebuilt and what is optional from here |

If the user only asked for extraction or documentation, stop after Phase 2 or Wave 1 instead of pushing to build.

## Phase 1: Capture L0 and L1

The crawl is the homepage (L0) plus every same-origin link reachable from it (L1). The capture contract per URL is unchanged from the existing capture workflow.

- Open L0 with `run-agent-browser`. Wait for the page to settle. Capture hydrated `dom.html`, headings, runtime metadata, screenshots at 1440/768/375, and mirror the route's CSS/JS/fonts/images.
- Extract every same-origin in-DOM link from L0 (skip `mailto:`, `tel:`, `javascript:`, `#` anchors, external hosts, and obvious tracking/locale duplicates).
- Repeat the capture contract for each L1 URL. Treat sticky headers, lazy content, and modals as default-state captures unless the user asks otherwise.
- Crawl deeper than L1 only when the user explicitly opts in.

See `references/capture-workflow.md` for the full per-route capture contract, working-root selection, route normalization, and failure recovery. Use `scripts/capture-url.sh` to scaffold the per-route artifact skeleton; the script delegates to the browser command and verifies artifacts before returning success.

## Phase 2: Type extraction — one template per unique page type

This is the discrete named phase that converts the L1 URL set into the small number of **unique page types** the site actually uses. It runs before any rebuild work. Read `references/type-extraction.md` for the full procedure.

### What this phase produces

- `.design-soul/types/fingerprints/{slug}.json` — one layout fingerprint per L1 URL
- `.design-soul/types/route-map.json` — `{ typeId → { exemplarUrl, instances, nextjsTemplate, captureRoots } }`
- `.design-soul/types/page-types.md` — human-readable rationale per cluster (signal evidence, exemplar choice, notable instance differences)

### What goes into a layout fingerprint

Compute these for each L1 URL from the hydrated DOM:

- pathname pattern with slug/numeric segments replaced by `:slug`
- `<body>` and `<main>` class set (sorted, deduplicated)
- top-level section sequence — ordered CSS Module prefixes or semantic tags of the direct children of `<main>`
- direct-child section count
- recognizable widget set — hero, pricing table, FAQ accordion, logo wall, testimonial cards, blog metadata, contact form, legal heading rhythm, etc.
- header/footer shell hash (hashed class names normalized)
- top-N CSS class prefixes across the body

### How clusters form

Two L1 URLs join the same type cluster when **all three** hold:

1. pathname template matches
2. section-sequence overlap ≥ ~70%
3. header/footer shell hash matches OR top class-prefix overlap ≥ ~60%

Homepage is always its own type. A cluster of size 1 is valid. A cluster of 20+ visually diverse instances is a signal to ask the user before continuing.

### Output to the rebuild phase

One Next.js template per type:

- single-instance type → `app/{type-route}/page.tsx`
- multi-instance type → `app/{type-route}/[slug]/page.tsx`

The rebuild phase reads `route-map.json` as its plan. Do not write any Next.js code until this phase has finished and `route-map.json` is on disk.

## Phase 3: Per-type rebuild

For each type in `route-map.json`, run the existing waves against the type's canonical exemplar (and any instance-specific overrides that surfaced in Phase 2):

- **Wave 0** — per-page exploration and deobfuscation. See `references/foundations-agent.md`. Use `scripts/extract-styles.sh` first to inventory the CSS corpus before manual extraction.
- **Wave 1** — unified design soul for the type's family. See `references/sections-agent.md`. Anatomy heuristics live in `references/website-patterns.md`.
- **Wave 2** — self-contained build brief per type. See `references/section-template.md`.
- **Wave 3** — Next.js scaffold and shared design-system foundation. See `references/system-template.md`. Allowed deps and `foundation-ready.signal` gate are defined there.
- **Wave 4** — render the type's template under `app/`. Full orchestration and quality gates live in `references/wave-pipeline.md`.

Think first:

- **Capture:** Which browser helper produces the complete evidence contract for this source? (Use `run-agent-browser`.)
- **Type extraction:** Are any clusters borderline? If yes, ask before committing.
- **Wave 0:** Which CSS corpus is strongest for this type — mirrored live capture, `_files/`, adjacent CSS, inline CSS, or source fallback?
- **Wave 3:** Which types stay static, and which exact interactions justify Client Components?
- **Wave 4:** Has the per-type template been verified against the original at all three viewports?

## Phase 4: Back-to-back verification — original vs candidate

This is the discrete named phase that proves each type's Next.js template is faithful to the deployed source. It runs **per type**, not per URL. Read `references/back-to-back-verification.md` for the full procedure.

### Tool: `run-agent-browser`

This phase explicitly drives `run-agent-browser`. The loop uses, at minimum:

- `open` to load the original URL on the live site, then the candidate URL on `localhost:3000`
- `snapshot -i` to confirm the DOM has settled before each screenshot
- viewport switching (1440 × 900, 768 × 1024, 375 × 812) so original and candidate are captured at the same width
- `screenshot` to write `.design-soul/verify/{type}/original-{viewport}.png` and `candidate-{viewport}.png`
- `get text` and `eval --stdin` heredoc for heading-outline and section-text comparison when pixel noise is high
- `--session-name verify-{type}` so each type runs in a clean named session; `--headed` when the original site fights headless browsers

### Loop shape

```
for each type in route-map.json:
  for each viewport in [1440, 768, 375]:
    capture ORIGINAL → original-{viewport}.png
    capture CANDIDATE → candidate-{viewport}.png
    write iteration entry → iterations.json
    decide pass / iterate / escalate
  on full pass → write summary.md, advance
```

### Acceptable parity

A type passes when, at all three viewports:

- section sequence under `<main>` matches the original
- H1/H2/H3 text content matches verbatim (modulo intentional user copy edits)
- section heights are within ~10% of the original
- visible image positions are within ~5% on the X axis and anchored to the same section
- font family, weight, and approximate size match
- background, primary text, accent, and CTA colors are within ~5 luminance units
- header and footer shells render identically
- responsive breakpoints fire at the same widths as the original

### Pass / iterate / escalate rule

| Outcome | Trigger | Next action |
|---|---|---|
| **pass** | All three viewports satisfy every parity dimension | Write `summary.md`, move to next type |
| **iterate** | Any viewport fails on a recoverable dimension | Fix the candidate template, increment iteration, re-run for that type |
| **escalate** | 5 rounds without a pass, or the same dimension fails 3 rounds in a row, or capture artifacts are missing/corrupted | Pause, summarize the residual diff for the user, ask whether to accept, change strategy, or skip the type |

Use `scripts/diff-screenshots.sh` for an RMSE pre-filter on the desktop pair when ImageMagick is available; never fabricate a metric when it is not.

## Phase 5: Report back to the user

When every type has either passed the verification loop or has user-accepted residual drift, write `RECOVERY-REPORT.md` at the working root and surface the contents to the user in the assistant's final reply.

### The report MUST list

1. **Types found** — every `typeId` from `route-map.json`, including the homepage.
2. **Which L1 URLs each type covers** — the `instances` array per type, plus the canonical exemplar.
3. **Where the candidate templates live** — exact paths under `nextjs-project/app/...` per type.
4. **Where the screenshots live** — for each type and viewport, the original/candidate pair paths under `.design-soul/verify/{type}/`.
5. **Known residual differences (if any)** — per type, the dimensions that did not fully match and why, taken from the type's `summary.md`.
6. **What is still `UNVERIFIED`** — any tokens, fonts, or assets the agent could not ground from captured evidence; the user must decide whether to substitute or hunt down.
7. **The recommended next step** — for most projects, this is *"wire up dynamic content with TinaCMS, MDX, or a CMS of your choice onto the typed templates."* Mention `build-tinacms-nextjs` as the natural follow-on when the user wants a TinaCMS-backed editorial site.
8. **What this skill explicitly did NOT do** — name the boundaries: no L2+ crawl unless asked, no third-party analytics/chat/tag-manager scripts re-added, no auth/dashboard routes, no copy or design "improvements."

The user must walk away knowing exactly what was rebuilt, exactly what is optional from here, and exactly what was deliberately left alone.

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
- **Route structure:** one Next.js template per page type; multi-instance types use a single `[slug]` parameterized route. The route map in `.design-soul/types/route-map.json` is the source of truth.
- **Images:** use local images with known dimensions, meaningful alt text, `sizes`, and `priority` for LCP/hero imagery. Do not add `next.config.js` remote image domains unless a temporary verification-only exception is documented.

## Recovery rules

- **Live site available:** capture L0 + L1 at desktop/tablet/mobile plus scroll slices before any rebuild. Preserve final DOM, script URLs, runtime metadata, mirrored stylesheets, and exposed asset URLs.
- **Next.js / runtime-heavy site:** record `__NEXT_DATA__`, `self.__next_f`, build IDs, chunk URLs, and route-level script/style manifests when present.
- **Missing `_files/` folder:** if HTML references local CSS files, use adjacent-asset snapshot mode; if it only contains inline CSS, use SingleFile mode; otherwise full reconstruction may be blocked unless a live site can be captured.
- **Missing assets / remote-only assets:** download them during extraction and record original → local path mapping.
- **Missing fonts:** inspect captured `@font-face`, CSS `url(...)`, runtime font URLs, and local `.woff2` / `.woff` / `.ttf` / `.otf` files. Verify weight/style coverage and `font-display`; if the original cannot be recovered, document the missing source and mark the substitution `UNVERIFIED`.
- **External JS (analytics, chat widgets):** do not embed third-party scripts blindly. Document them separately and re-add only if the user explicitly wants that behavior.
- **Missing CSS or JS evidence for a value or behavior:** mark it `UNVERIFIED`; avoid inventing the implementation.
- **Incomplete capture:** continue extraction where possible, but do not claim a pixel-faithful rebuild if core layout, type, asset, or below-the-fold evidence is missing.
- **Shared headers, footers, or page-family sections across types:** deduplicate them intentionally into `components/shared/` and import them per template; note route-specific overrides instead of duplicating the shell.

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

# Every type in route-map.json has a verification summary
jq -r '.types[].id' .design-soul/types/route-map.json | while read t; do
  test -f ".design-soul/verify/$t/summary.md" || echo "FAIL: missing verify summary for $t"
done
```

## Verification before claiming completion

- **After Phase 1 (Capture):** route inventory completeness, route normalization, mirrored asset roots, and screenshot coverage at desktop, tablet, mobile, plus scroll slices for long pages.
- **After Phase 2 (Type extraction):** every L1 URL has a fingerprint; every type has an exemplar; `route-map.json` is on disk and internally consistent.
- **After extraction (before Wave 3):** run the grounding test and cross-reference checks from `references/quality-checklist.md`.
- **Before `foundation-ready.signal`:** extracted CSS custom properties and shared tokens are accounted for, dependency set is allowed, fonts/assets are self-hosted, traceability matrix exists, and TypeScript/build are clean.
- **Before Phase 5 (Report back):** every type has passed the back-to-back verification loop at 1440/768/375, or has user-accepted residual drift logged in its `summary.md`.
- If any verification fails, fix it before writing the completion signal or calling the build done.

## Final report contract

- `Verification rung reached`: state the actual rung and evidence — for example `build/type-check only` or `back-to-back original-vs-candidate at 1440/768/375 per type with summary.md`.
- `pixel-perfect`: claim only when the user provided a threshold or exact measured diff gate **and** every type meets it at desktop/tablet/mobile.
- `visual-equivalent`: use when the verification loop supports fidelity but documented drift remains because source evidence is incomplete.
- Build success alone is never a visual fidelity claim.
- Always end with the Phase 5 user-facing report described above. Do not finish without it.

## Reference map

| Need | Read |
|---|---|
| Live-capture prerequisites, working root, route normalization, canonical exemplar selection | `references/capture-workflow.md` |
| Input detection, capture outputs, output trees, ambiguous requests | `references/input-output-spec.md` |
| L0 + L1 crawl, layout fingerprints, type clustering, one-template-per-type output | `references/type-extraction.md` |
| Back-to-back original-vs-candidate verification loop with `run-agent-browser` | `references/back-to-back-verification.md` |
| Hard rules: grounding, section identification, zero invention | `references/principles-and-rules.md` |
| Wave 0 extraction method | `references/foundations-agent.md` |
| Wave 1 design-soul extraction | `references/sections-agent.md` |
| Wave 2 build-brief format | `references/section-template.md` |
| Wave 3 scaffold, token wiring, allowed deps | `references/system-template.md` |
| Full orchestration, Capture Wave, and gates | `references/wave-pipeline.md` |
| Acceptance criteria, visual QA, and failure modes | `references/quality-checklist.md` |
| Section-type and anatomy heuristics | `references/website-patterns.md` |

Read only the references needed for the current phase. Keep the top-level skill focused on decisions, sequencing, and guardrails; keep implementation detail in the reference files.
