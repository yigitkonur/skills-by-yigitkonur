---
name: extract-saas-design
description: Use skill if you are extracting design tokens (color, typography, spacing, components) from an existing SaaS dashboard URL, codebase, or HTML snapshot into structured documentation, not rebuilding it.
---

# Extract SaaS Design

Forensically document the visual system of an implemented SaaS dashboard, admin panel, or internal tool into structured markdown. The output is documentation and resolved tokens, not generated UI code.

## When to use this skill

Use when the request matches any of these intents:

- *"Extract the design system from this dashboard URL"* — live SaaS app, admin panel, or internal tool.
- *"Document the design tokens"* / *"pull the visual system"* / *"extract the visual DNA"* from a codebase, repo, or HTML snapshot.
- *"Document color, typography, spacing, radius, shadow tokens"* from `globals.css`, `@theme`, `tailwind.config.*`, or token files.
- *"Document the sidebar / table / command palette / form layout"* — named components from a real implementation.
- *"Audit color, spacing, or accessibility consistency"* against the implemented system, evidence-based.
- *"Capture the dark mode tokens"* / *"document mode switching"* from a working dashboard.
- *"Hand off the design system"* so another team or codebase can match the existing look.
- *"Extract the dashboard's chart palette / density zones / sidebar overrides"*.

Do NOT use this skill when:

- The user asks to **build, port, clone, recover, convert, or ship** a working UI. Route to `convert-url-to-nextjs`.
- The user asks for a **redesign, restyle, "make it better,"** or speculative UX advice. This skill never recommends changes — only documents what exists.
- The source is **Figma-only, screenshot-only, or visual inspiration** with no inspectable implementation (no DOM, no CSS, no code).
- The target is a **marketing/brochure site**, not a SaaS/dashboard/admin product.

## Hard rules (load-bearing)

| Rule | Why it matters |
|---|---|
| **Document, don't rebuild.** Output `.md` documentation in `.design-soul/` only. | Crossing into generated UI code = wrong skill. |
| **Resolve every token chain to its final value.** `bg-primary` → `var(--primary)` → `oklch(0.205 0 0)`. Stop only at the literal. | Class names and aliases are useless to a recreator. |
| **Honor scope.** If the user asked for the sidebar, do not document the whole app. | Scope creep poisons the deliverable. |
| **Absence is evidence.** Write `Hover: not implemented`, `Loading: not implemented`, `Dark mode: not implemented`. | Inventing states is worse than admitting gaps. |
| **Separate canon from noise.** Document the dominant pattern, then list inconsistencies with file refs. | Smoothing over inconsistency hides bugs. |
| **Source over screenshot.** Component source + CSS tokens are primary. DOM/computed styles secondary. Screenshots only validate layout. | Screenshots lie about pseudo-states. |

## Output contract

All artifacts go in `.design-soul/` at the **target codebase root** (not inside this skills repo). Default deliverables, scoped:

| Scope | Files |
|---|---|
| Full extraction / "visual DNA" | `system.md`, numbered foundation docs, one numbered doc per component, `INDEX.md`, `_summary.md` |
| Foundations / tokens only | `system.md` + foundation docs only |
| Specific components | Minimal foundation context + numbered doc per named component |
| Consistency / accessibility audit | Evidence-based findings doc grounded in extracted tokens — no redesign |

Default format is markdown with CSS recreation blocks. Do **not** generate `.tokens.json`, Style Dictionary, or Tokens Studio files unless explicitly requested.

Exact templates and folder layout: `references/documentation/output-format.md`, `references/system-template.md`, `references/component-template.md`.

## Workflow

### 1. Frame the job

Restate scope in one line: what's in, what's out, what counts as ground truth. Default to the smallest extraction that satisfies the request.

### 2. Detect the styling stack (this gates everything)

Run these checks against the target root before anything else:

- **Tailwind v4** — `@import "tailwindcss"` and `@theme {}` blocks in CSS. No `tailwind.config.*`.
- **Tailwind v3** — `tailwind.config.ts/js` with `theme.extend`.
- **shadcn/ui** — `components/ui/` directory, `cn()` from `@/lib/utils`, often `oklch()` colors.
- **CVA** — `class-variance-authority` defines variant/size matrices; the `cva()` call IS the spec.
- **CSS entry point** — `globals.css` or `app.css` is where tokens live.
- **Offline snapshot mode** — plain HTML+CSS, no `package.json`/`src/`. Treat the CSS files as the source of truth; write `not implemented` / `N/A` for framework-specific systems.

Target-root resolution and snapshot vs repo-backed handling: `references/extraction/target-modes.md`.

### 3. Capture evidence

For live URLs or interactive local apps, use `run-agent-browser` to capture DOM, computed styles, screenshots, and state coverage. Use `run-playwright` only when the user explicitly asks for the Playwright CLI or the target project already runs one. Browser tools are evidence capture only — never let them drift into rebuilding.

Store browser artifacts under `.design-soul/evidence/` at the target codebase root: route or page name, viewport, screenshot path, DOM/source path, observed states.

For deterministic token inventories, run helper scripts against the target root:
- `scripts/capture-css-tokens.md` — enumerate CSS custom properties.
- `scripts/audit-spacing-scale.md` — count spacing scale usage.

### 4. Extract foundations (when in scope)

Cover spacing, color, typography, shadows/depth, radius, animation, shared state conventions. For dashboards, also cover sidebar overrides, chart palettes, density zones, and tabular/monospace usage.

| Foundation | Reference |
|---|---|
| Color (incl. `oklch()` reading, dark mode chains) | `references/extraction/color-extraction.md` |
| Typography (font stacks, scale, line-height) | `references/extraction/typography-extraction.md` |
| Spacing (scale detection, density zones) | `references/extraction/spacing-extraction.md` |
| Icons and asset inventory | `references/extraction/icons-and-assets.md` |
| Foundations extraction prompt (sub-pass) | `references/foundations-agent.md` |
| Dashboard-specific patterns (sidebar overrides, chart palettes, density) | `references/dashboard-patterns.md` |
| Layout grid + responsive breakpoints | `references/layout/grid-and-responsive.md` |

### 5. Extract components and patterns (when in scope)

Document each component's anatomy, variants, sizes, states, state transitions, dark-mode differences, and composition. Sidebars, tables, command palettes, and form layouts are **mega-components** — decompose them into sub-parts and modes; do not flatten.

In offline snapshot mode, treat repeated DOM fragments + their selectors as the component evidence. Document only what the snapshot proves; call out gaps explicitly.

| Need | Reference |
|---|---|
| Component extraction prompt (sub-pass) | `references/components-agent.md` |
| Component output template | `references/component-template.md` |

### 6. Translate tokens

| Need | Reference |
|---|---|
| W3C DTCG, CSS custom properties, `oklch()` format | `references/tokens/token-formats.md` |
| shadcn naming pattern, semantic vs primitive layers | `references/tokens/naming-conventions.md` |

### 7. Verify before handoff

Run the verification checklist before declaring done. The bar: a recreator must not need to guess any value or state.

| Need | Reference |
|---|---|
| Pre-handoff verification checklist | `references/quality-checklist.md` |
| Consistency audit checklist | `references/audit/consistency-checklist.md` |
| Accessibility / WCAG contrast review | `references/audit/accessibility-review.md` |

Pay special attention to: disabled, focus-visible, loading, error/invalid, empty state, dark mode, opacity semantics, animation composition.

### 8. Package output

Place all artifacts in `.design-soul/` at the target codebase root using the structure in `references/documentation/output-format.md`. Use `references/system-template.md` for foundations and `references/component-template.md` for components. Do not invent new formats.

## Guardrails

| Do this | Not that |
|---|---|
| Resolve `bg-primary`, `rounded-md`, `p-3` to actual values | Stop at class names or aliases |
| Write `Hover: not implemented` when absent | Invent "best practice" states |
| Decompose sidebar/table/form into sub-parts | Flatten mega-components into one blob |
| Flag inconsistencies with file evidence | Smooth them into a cleaner system |
| Keep audits evidence-based | Drift into redesign or critique |
| Document composition and context | Describe components only in isolation |

## Recovery rules

- **Evidence incomplete:** look for adjacent ground truth (global CSS, theme files, config, Storybook, screenshots). Document the gap explicitly if still unresolved.
- **Codebase too large:** split into foundations + the requested categories or components. Do not widen scope silently.
- **Values conflict across files:** document the dominant pattern, list exceptions with source references.
- **Dark mode / state does not exist:** say so plainly. Absence is part of the extraction.
- **Drifting toward implementation:** stop generating build instructions; return to documentation deliverables.

## Steering notes for agents

These prevent the most common extraction failures.

**Tailwind v4 detection.** Grep for `@import "tailwindcss"` or `@theme` in CSS files — if found, the project uses CSS-native config (no `tailwind.config.js`). If `tailwind.config.ts` exists with `theme.extend`, it's v3. Always check before extracting tokens. Detection commands: `references/foundations-agent.md`.

**oklch color space.** Modern shadcn/ui (2024+) uses `oklch(L C H)`. L=lightness (0–1), C=chroma (0–0.4), H=hue (0–360). Grays have C < 0.01. Always note lightness to distinguish dark/light. Reading guides: `references/extraction/color-extraction.md`, `references/tokens/token-formats.md`.

**CVA and `cn()`.** The `cva()` call IS the component's visual spec — extract every variant/size key-value pair. The `cn()` utility merges classes via `tailwind-merge` where the last class wins. CVA extraction checklist + `cn()` merging guide: `references/component-template.md`.

**Token chain resolution.** Never stop at the Tailwind class. Resolve the full chain: `bg-primary` → `var(--primary)` → `oklch(0.205 ...)`. Some tokens chain through multiple variables — resolve all the way to the literal: `references/extraction/color-extraction.md`.

## Source-of-truth hierarchy

1. Component source + CSS tokens — primary.
2. Live DOM / computed styles + Storybook — secondary.
3. Screenshots — validate layout and state coverage; do not override source values.
4. Figma token sync — document only when the implemented codebase contains token-sync artifacts.

## Boundary with `convert-url-to-nextjs`

This skill produces **documentation**. `convert-url-to-nextjs` produces a **buildable Next.js app** from a snapshot. If the user wants to ship working UI, route there. If they want a handoff doc the other team uses to match the look, stay here.

## Final reminder

This skill is an orchestrator, not a template dump. Keep the main flow tight, route to references for detail, and stay anchored to the implemented UI rather than rebuilding or redesigning it.
