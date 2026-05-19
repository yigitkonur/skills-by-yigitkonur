---
name: create-design-md
description: Use skill if you are producing a design.md spec plus per-asset references tree from a live URL, codebase, or HTML snapshot so another agent can reproduce the design.
---

# Create design.md

Given a source — live URL, codebase, or HTML snapshot — produce a `design.md` spec plus a `references/[context]/NN-asset.{md,json}` tree, such that another agent (or human) can reproduce the design's intent **and** concrete values from those files alone.

`design.md` is the headline artifact. The `references/[context]/` tree is the evidence that backs every claim in `design.md` with a paired prose description and machine-readable JSON. Both ship together; one without the other is incomplete.

This skill follows the open **DESIGN.md** format published by Google Labs (frontmatter tokens + markdown body sections) and extends it with a per-asset references tree.

## When to use this skill

- *"Produce a design.md for this dashboard / URL / repo"*.
- *"Generate a design.md and per-asset references for our marketing site"*.
- *"Document the design system of this existing SaaS as a portable spec"*.
- *"Extract this app's visual system into a file another agent can read"*.
- *"Create a design.md from this HTML snapshot / Figma export / Tailwind codebase"*.
- *"Hand off the design system so another team can match the look"* — when the deliverable is a file, not buildable UI.

## Do NOT use this skill when

- The user wants **buildable UI code** from a source. Use `convert-url-to-nextjs`.
- The user wants a **redesign, restyle, or "make it better"** pass. This skill documents what exists; it never recommends changes.
- The source is **Figma-only, screenshot-only, or "vibe"** with no inspectable implementation. The skill needs DOM, CSS, source files, or a parseable snapshot.
- The user wants a **browser-driven audit only** (no file output). Use `audit-ui`.

## Sibling routing

| Need | Route to |
|---|---|
| Buildable Next.js page from the source | `convert-url-to-nextjs` (this skill is documentation-only). |
| Live browser capture (DOM, screenshots, computed styles) needed first | Call `run-agent-browser` from inside this skill's workflow — see `references/source-variants.md`. |
| Visual UI audit across pages (no file output) | `audit-ui`. |

## Two trees, one mental model — load-bearing

The agent reading this skill must distinguish two separate trees:

1. **The skill's own references** — `skills/create-design-md/references/...` — the deep-dive docs *for the agent*. These exist once, in this repo. The agent reads them.
2. **The generated references tree** — `<target>/references/...` — the artifact *the skill produces per run*, alongside `design.md`. These are written fresh each invocation, at the target codebase root or working directory.

The skill's own references describe **how to produce** the generated tree. The generated tree is **what the skill outputs**. Do not conflate them. Every reference to `references/[context]/NN-asset.md` in this SKILL.md is about the **generated** output. Every reference to `references/<topic>.md` is about the **skill's own** docs.

## Output contract — what every run produces

At the target codebase root (or a writable working directory beside the source), produce:

```
design.md                                    # master spec (DESIGN.md format)
references/                                  # paired per-asset evidence
├── tokens/                                   # foundation primitives
│   ├── 01-color-primary.md
│   ├── 01-color-primary.json
│   ├── 02-color-semantic.md
│   ├── 02-color-semantic.json
│   └── ...
├── typography/
│   ├── 01-font-families.md
│   ├── 01-font-families.json
│   ├── 02-type-scale.md
│   ├── 02-type-scale.json
│   └── ...
├── spacing/
│   ├── 01-base-unit.md
│   ├── 01-base-unit.json
│   └── ...
├── radius/
├── elevation/
├── motion/
├── layout/
│   ├── 01-grid.md
│   ├── 01-grid.json
│   ├── 02-breakpoints.md
│   ├── 02-breakpoints.json
│   └── ...
└── components/
    ├── 01-button-primary.md
    ├── 01-button-primary.json
    ├── 02-button-secondary.md
    ├── 02-button-secondary.json
    ├── 03-input-text.md
    ├── 03-input-text.json
    └── ...
```

Rules:
- Every asset has **both** an `.md` (prose) and a `.json` (machine values) — never one without the other.
- File names are `NN-slug.md` / `NN-slug.json` with a zero-padded ordinal; the slug is identical across the pair.
- `[context]` directories are coherent groupings. Suggested canonical set: `tokens`, `typography`, `spacing`, `radius`, `elevation`, `motion`, `layout`, `components`. Add a new `[context]/` directory when the source warrants (e.g. `charts/`, `sidebar/`, `density/`).
- Every asset file is linked at least once from `design.md`.
- The full output tree contract, naming rules, and ordinal conventions: `references/output-tree.md`.

## The design.md spec — what every generated design.md MUST contain

Generated `design.md` follows the open **DESIGN.md** format (Google Labs, 2026): YAML frontmatter (machine-readable tokens) + markdown body (rationale). Section ordering is normative.

**Frontmatter (YAML):**

```yaml
---
version: alpha
name: <product or system name>
description: <one-sentence summary of the design's intent>
colors:
  <token-name>: "<hex>"
typography:
  <token-name>:
    fontFamily: <string>
    fontSize: <dimension>
    fontWeight: <number>
    lineHeight: <dimension|number>
    letterSpacing: <dimension>
rounded:
  <scale-level>: <dimension>
spacing:
  <scale-level>: <dimension|number>
components:
  <component-name>:
    backgroundColor: <hex|"{colors.token}">
    textColor: <hex|"{colors.token}">
    typography: "{typography.token}"
    rounded: "{rounded.token}"
    padding: <dimension>
---
```

**Markdown body sections — in this exact order. All `##`. Omit only when genuinely not applicable.**

1. **`## Overview`** — Brand personality, design language, mood. One paragraph. Answer: *what is this design's intent?*
2. **`## Colors`** — Semantic role of every color token in the frontmatter, with link to `references/tokens/NN-*.{md,json}`.
3. **`## Typography`** — Font families, type scale, weight scale, special patterns, with link to `references/typography/NN-*.{md,json}`.
4. **`## Layout`** — Grid model, spacing scale, breakpoints, density zones, with link to `references/spacing/` and `references/layout/`.
5. **`## Elevation & Depth`** — Strategy (borders-first / shadows / layered), shadow scale, focus rings, with link to `references/elevation/NN-*.{md,json}`.
6. **`## Shapes`** — Border-radius scale and shape language, with link to `references/radius/NN-*.{md,json}`.
7. **`## Motion`** — Transition/animation library, duration hierarchy, easing curves, with link to `references/motion/NN-*.{md,json}`.
8. **`## Components`** — One subsection per component, each linking to its `references/components/NN-*.{md,json}` pair.
9. **`## Accessibility`** — Contrast strategy, focus visibility, keyboard interaction, ARIA conventions.
10. **`## Do's and Don'ts`** — Explicit guardrails. Each rule traces back to a token, scale, or composition decision.
11. **`## References Index`** — Flat list of every generated `references/[context]/NN-*.md` and `.json` file with one-line purpose.

The complete meta-spec (every required field, every section purpose, when to omit): `references/design-md-spec.md`. A complete worked example `design.md`: `references/examples/design-md-example.md`.

## Per-asset file conventions — the `.md` + `.json` pair

Every asset in the generated `references/[context]/` tree is a **paired** `.md` + `.json` with the same `NN-slug` stem. Conventions:

### The `.md` file — prose

| Section | Purpose |
|---|---|
| Header | `# <Asset Name>` and one-sentence purpose. |
| Why | When and why this asset exists in the system. |
| Anatomy / Hierarchy | For components: ASCII diagram of structure. For tokens: place in scale/hierarchy. |
| States | All states (default, hover, focus-visible, active, disabled, loading, error). Write `Not implemented` rather than skipping. |
| Composition | For components: how this is used with siblings. For tokens: which components consume this token. |
| Source evidence | The file path, selector, CSS variable, or DOM selector that proves this value. |
| Cross-references | Other `references/[context]/NN-*.md` files this asset depends on. |

### The `.json` file — values

The JSON is the exact, machine-readable shape that another agent can ingest. The shape follows the DESIGN.md component-property vocabulary at the top level. Mandatory keys per asset type:

**Component asset (`references/components/NN-name.json`):**

```json
{
  "$id": "components/button-primary",
  "name": "Button - Primary",
  "type": "component",
  "anatomy": ["container", "icon", "label", "spinner"],
  "props": {
    "size": ["sm", "md", "lg"],
    "variant": ["solid", "outline", "ghost"],
    "disabled": "boolean"
  },
  "tokens": {
    "backgroundColor": "{colors.primary}",
    "textColor": "{colors.primary-foreground}",
    "rounded": "{rounded.md}",
    "padding": "8px 16px",
    "height": "36px"
  },
  "states": {
    "default": { "backgroundColor": "{colors.primary}" },
    "hover":   { "backgroundColor": "{colors.primary}", "opacity": 0.9 },
    "focus":   { "boxShadow": "0 0 0 3px {colors.ring}/50" },
    "active":  { "transform": "scale(0.98)" },
    "disabled":{ "opacity": 0.5, "pointerEvents": "none" },
    "loading": "not-implemented"
  },
  "transitions": [
    { "property": "background-color", "duration": "150ms", "easing": "ease" }
  ],
  "accessibility": {
    "role": "button",
    "keyboard": ["Enter", "Space"],
    "contrast": "WCAG-AA-verified"
  },
  "source": {
    "file": "src/components/Button.tsx",
    "selector": "button[data-variant=primary]",
    "cssVar": null
  }
}
```

**Token asset (`references/tokens/NN-name.json`):**

```json
{
  "$id": "tokens/color-primary",
  "name": "Primary Color Token",
  "type": "token",
  "tokenType": "color",
  "$value": "#1A1C1E",
  "$description": "Primary brand color for CTAs and active states",
  "mode": {
    "light": "#1A1C1E",
    "dark":  "#EAEEF5"
  },
  "consumers": ["components/button-primary", "components/badge-status"],
  "source": {
    "file": "app/globals.css",
    "selector": ":root",
    "cssVar": "--primary"
  }
}
```

The JSON keys mirror the DESIGN.md component-property vocabulary (`backgroundColor`, `textColor`, `typography`, `rounded`, `padding`, `size`, `height`, `width`) so a downstream agent can match generated `design.md` frontmatter component blocks to their per-asset JSON one-to-one. Token references use the DESIGN.md `{path.to.token}` curly-brace syntax.

For machine-readable interoperability with the W3C Design Tokens Format (DTCG 2025.10), token assets MAY include a `$type` field (`color`, `dimension`, `fontFamily`, `fontWeight`, `duration`, `cubicBezier`, `shadow`, `typography`, etc.) alongside `$value` and `$description`. This keeps each `.json` exportable to DTCG with minimal transformation.

Complete worked examples — one component pair, one token pair:
- Component pair: `references/examples/component-asset-example.md`
- Token pair: `references/examples/token-asset-example.md`

The full per-asset template (every field, when to omit, validation hints): `references/per-asset-template.md`. The full JSON shape per asset type (component / token / typography / spacing / motion / layout): `references/token-format.md`.

## Workflow — phased

Full phased procedure with acceptance criteria for each phase: `references/workflow.md`.

Before producing any `design.md` for a real source, **first re-read the meta-spec section of this SKILL.md above (and `references/design-md-spec.md` if needed) so the output is consistent across runs.** Then:

### Phase 1 — Frame the source and scope

- Restate the scope in one line. Default to a complete extraction unless the user limits it.
- Identify the source mode: live URL / codebase / HTML snapshot. Route per `references/source-variants.md`.
- Decide the **target root**: where `design.md` + `references/` will live. Default to the source codebase root or a writable working copy.

### Phase 2 — Inventory contexts

Walk the source once and inventory which `[context]/` directories the output will need. Start from the canonical set (`tokens`, `typography`, `spacing`, `radius`, `elevation`, `motion`, `layout`, `components`). Add domain-specific contexts where the source demands (e.g. `charts/`, `sidebar/`, `density/`).

Output: a flat list of `[context]` directories the run will create. No file content yet.

### Phase 3 — Per-context asset inventory

For each `[context]/`, list every asset it will contain. For `components/`, this means walking the source's component tree (file by file, selector by selector). For `tokens/`, this means enumerating CSS variables, theme blocks, and `@theme` directives. Assign ordinal numbers `NN-` reflecting reading order within the context.

Output: a list of `references/[context]/NN-slug` stems. No content yet.

### Phase 4 — Per-asset capture

For each stem, produce both `NN-slug.md` and `NN-slug.json`. Resolve every token chain to its literal value (`bg-primary` → `var(--primary)` → `#1A1C1E`). Record source evidence (file path + selector). For states the source does not implement, write `not-implemented` in both files.

Helpful cheatsheet for resolution chains, Tailwind-to-CSS conversions, oklch reading: `references/extraction-cheatsheet.md`.

### Phase 5 — Assemble design.md

With every asset captured, assemble `design.md`:

1. Write YAML frontmatter, pulling tokens from `references/tokens/*.json`, `references/typography/*.json`, `references/radius/*.json`, `references/spacing/*.json`, and component composites from `references/components/*.json`.
2. Write the markdown body in the section order specified above. Each section links to the `references/[context]/NN-*.md` files it describes.
3. Append the **References Index** section last — a flat list of every generated file with a one-line purpose, in the order: `tokens/`, `typography/`, `spacing/`, `radius/`, `elevation/`, `motion/`, `layout/`, `components/`, then any custom contexts.

### Phase 6 — Cross-reference verification

Before claiming done, run the verification rungs in `references/verification.md`. Bar: every asset has both files; every asset is linked from `design.md`; every token in frontmatter has a `references/tokens/` asset; every component listed under `## Components` has a `references/components/` pair; every `references/[context]/NN-*` file in the tree is referenced from `design.md`.

## Source variants

Each variant ends at the same output tree (`design.md` + `references/[context]/NN-*.{md,json}`). Variant-specific guidance: `references/source-variants.md`.

| Source | First step | Evidence basis |
|---|---|---|
| **Live URL** | Invoke `run-agent-browser` to capture DOM, computed styles, screenshots, state coverage. | DOM + computed styles + captured CSS. |
| **Codebase** (repo with `package.json`, component source) | Detect styling stack (Tailwind v3/v4, shadcn/ui, CSS modules, styled-components). Read CSS entry points and component source. | Source files + CSS tokens. |
| **HTML snapshot** (`.html` + adjacent CSS, or SingleFile export) | Treat captured HTML + CSS as the source of truth. Skip framework-specific checks unless the snapshot proves them. | Captured CSS + HTML selectors. |

In all three variants the agent **resolves every token chain to its final literal value**; never stops at a class name or alias. The agent writes `not-implemented` for states/modes the source does not implement; never invents.

## Hard rules

| Rule | Why |
|---|---|
| **Document, don't redesign.** | The skill outputs a spec of what exists. Any suggestion is a separate task. |
| **Pair every asset.** Every `.md` has a `.json`; every `.json` has a `.md`. | The pair is the contract; one without the other is half-finished. |
| **Resolve every token chain to a literal.** `bg-primary` → `var(--primary)` → `#1A1C1E`. | Class names and aliases are useless to a reproducer. |
| **Absence is evidence.** Write `not-implemented` when a state, mode, or variant is absent. | Inventing states is worse than admitting gaps. |
| **Honor scope.** If the user asked for the sidebar, do not document the whole app. | Scope creep poisons the deliverable. |
| **Source over screenshot.** Source + CSS are primary; DOM + computed styles secondary; screenshots validate layout only. | Screenshots lie about pseudo-states. |
| **`design.md` is the headline.** Per-asset files exist to back its claims; not the other way around. | Reproducers read `design.md` first. |
| **Cross-reference everything.** Every claim in `design.md` links to a per-asset file; every per-asset file is linked from `design.md`. | Otherwise drift is undetectable. |

## Verification — before claiming done

Run the checklist in `references/verification.md`. The ultimate test:

> Given only `design.md` plus the `references/[context]/` tree, could a fresh agent reproduce the design's intent and concrete values without guessing? If yes, the output is complete. If "mostly, but they'd need to guess at X" — document X.

## Boundary with `convert-url-to-nextjs`

This skill produces **documentation**. `convert-url-to-nextjs` produces a **buildable Next.js project**. If the user wants shippable UI, route there. If they want a portable spec another agent reads to match the look, stay here. The two skills can share a browser capture step — both call `run-agent-browser` for live evidence.

## Final reminder

`design.md` is the headline artifact and the unit of value. The `references/[context]/NN-*.{md,json}` tree is the evidence that makes the spec auditable. Produce them together, link them tightly, validate before declaring done.
