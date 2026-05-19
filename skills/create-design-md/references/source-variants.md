# Source Variants — Live URL, Codebase, HTML Snapshot

Each source variant ends at the same output tree: `design.md` + `references/[context]/NN-*.{md,json}` at the target root. The variants differ in **what counts as evidence** and **how to gather it**.

---

## Variant 1 — Live URL

The source is a running web application. Examples:

- `https://app.example.com` — full SaaS dashboard.
- `https://example.com/admin` — admin panel.
- `https://app.example.com/settings` — narrow scope inside a SaaS.

### First step

Invoke `run-agent-browser` (`skills/run-agent-browser/SKILL.md` for full details) to capture:

- DOM (`snapshot -i` for interactive refs, full snapshot for layout).
- Computed styles for every relevant element.
- Screenshots (full-page + viewport).
- Captured CSS (linked stylesheets + inline `<style>`).
- Asset URLs (fonts, images, icons).

Store browser artifacts in a working directory beside the eventual `design.md`. Suggested layout:

```
<target-root>/
├── design.md              # produced in Phase 5
├── references/            # produced in Phases 3-4
└── _capture/              # browser evidence
    ├── routes.json
    ├── <route-slug>/
    │   ├── snapshot.json
    │   ├── computed-styles.json
    │   ├── screenshot.png
    │   └── styles/
    │       ├── inline.css
    │       └── external/*.css
    └── assets/
```

The `_capture/` directory is **evidence**, not deliverable. It supports the Phase 4 capture; it is not linked from `design.md`.

### Evidence basis

Primary → secondary → tertiary, in order:

1. Captured CSS files (linked stylesheets, `<style>` blocks).
2. Inline `style="..."` attributes on the DOM (where the page applies values runtime).
3. Computed styles from the browser (resolves cascade and var() chains).
4. Screenshots (last resort — validate layout, not values).

### Common gotchas

- **Minified CSS** has no trailing `;` before `}`. Reference grep patterns use `[^;}]+` not `[^;]+`.
- **Critical CSS inlining** can hide tokens. Always check inline `<style>` blocks at the top of `<head>` and the linked stylesheet.
- **CSS-in-JS** (styled-components, emotion) renders class names like `css-1a2b3c` that look opaque. Match on the **selector → computed style** pair from the browser.
- **Token chains through `var()`** must be resolved. The browser's computed style already resolves them — use that.

---

## Variant 2 — Codebase

The source is a repository with `package.json` (or another manifest) and component source files. Examples:

- A Next.js shadcn/ui app with `tailwind.config.ts`, `app/globals.css`, `components/ui/`.
- A Vue + SCSS app with design tokens in `src/styles/_variables.scss`.
- An Angular Material app with theme files.

### First step

Detect the **styling stack** before extracting anything. The stack determines where tokens live.

| Signal | Stack |
|---|---|
| `@import "tailwindcss"` in CSS + `@theme {}` blocks | Tailwind v4 (tokens in CSS) |
| `tailwind.config.ts` with `theme.extend` | Tailwind v3 (tokens in JS config) |
| `components/ui/` + `cn()` from `@/lib/utils` | shadcn/ui |
| `class-variance-authority` import | CVA-defined variants |
| `:root { --... }` blocks in `globals.css` / `app.css` | CSS custom properties (always primary evidence) |
| `styled-components`, `@emotion/...` in `package.json` | CSS-in-JS — values live in JS modules |
| SCSS `$variables` + `@mixin` | SCSS — values live in `_variables.scss` and similar |
| `*.module.scss` / `*.module.css` | CSS Modules — extract per-module |

Detection commands and full stack-routing logic: `references/extraction-cheatsheet.md`.

### Evidence basis

1. CSS entry points (`globals.css`, `app.css`, `theme/*.css`, `tailwind.config.*`) — primary.
2. Component source files (every `.tsx`/`.jsx`/`.vue`/`.svelte` in the components directory) — primary for component anatomy and CVA variants.
3. Storybook stories — secondary; cross-reference variant/size coverage when present.
4. The running app via `run-agent-browser` — when source-only resolution is ambiguous, capture the runtime DOM to disambiguate.

### Common gotchas

- **Tailwind v4 missed.** If you look for `tailwind.config.js` and don't find it, check for `@import "tailwindcss"` in CSS. Tokens are in `@theme {}` blocks.
- **oklch read as hsl.** Modern shadcn (2024+) uses `oklch(L C H)` where L=0–1, C=0–0.4, H=0–360. Lightness 0.2 means dark; in hsl that would be `20%`.
- **CVA variants skipped.** The `cva()` call IS the component spec. Extract every `variants.*.*` pair, every `size.*` value, every `defaultVariants`.
- **`cn()` class merging.** With `cn()`, later classes override earlier via `tailwind-merge`. Resolve by playing the cascade.
- **Token chains.** `bg-primary` → `var(--primary)` → `oklch(0.205 0.006 285.88)`. Always to the literal.

---

## Variant 3 — HTML Snapshot

The source is captured HTML + CSS, with no live runtime and no source repo. Examples:

- `index.html` + `_files/` (SingleFile or `wget -p` export).
- `index.html` + adjacent `*.css` files.
- `index.html` with inline `<style>` only.

### First step

Inventory the snapshot:

```bash
find . -maxdepth 3 -type f \( -name "*.html" -o -name "*.css" -o -name "*.svg" \) | head -50
```

Decide the **snapshot mode**:

- **Multi-file** — `.html` + `_files/` or adjacent CSS. Treat each `.css` file as source of truth for selectors and tokens.
- **Inline-only** — `.html` with `<style>` blocks but no external CSS. Treat the inline styles as the corpus.
- **Hybrid** — both. Use both.

### Evidence basis

1. Captured `.css` files — primary.
2. Inline `<style>` blocks — primary alongside external CSS.
3. Inline `style="..."` attributes on DOM elements — secondary.
4. Repeated DOM fragments + their selectors — component evidence.

### Special handling

- **Skip framework-specific checks** — Tailwind, shadcn, CVA. The snapshot may or may not preserve those signals. If `@theme` blocks survive, treat them as Tailwind v4 evidence. If `cva(` survives somewhere in JS, treat as CVA. Otherwise, plain CSS rules.
- **Component evidence is structural.** A "card" is a repeated `<div class="card">...</div>` pattern with consistent inner structure. Document only what the snapshot proves; mark missing states `not-implemented`.
- **Token resolution.** Resolve `var(--card-bg)` chains by reading `:root { --card-bg: ... }`. If the snapshot only has the consumer rule and not the definition, document the chain partial and note the gap.

---

## Routing matrix

| Situation | First action |
|---|---|
| Live URL only | Variant 1 — invoke `run-agent-browser` for capture. |
| Live URL + scope limited to N pages | Variant 1 — capture only the in-scope routes. |
| Repo path (codebase) | Variant 2 — detect stack first. |
| Repo + live URL | Variant 2 + targeted Variant 1 — codebase source is primary; URL capture disambiguates runtime-only values. |
| `.html` + `_files/` | Variant 3 — multi-file mode. |
| `.html` + adjacent CSS | Variant 3 — multi-file mode. |
| `.html` with `<style>` only | Variant 3 — inline-only mode. Document reduced confidence in source-evidence fields. |

---

## Output is identical across variants

Regardless of variant, the deliverable at the target root is identical in shape:

```
design.md
references/
├── tokens/
├── typography/
├── spacing/
├── radius/
├── elevation/
├── motion/
├── layout/
├── components/
└── (optional domain contexts)
```

The variant affects **how** values were extracted (and what the `.md`'s **Source Evidence** sections reference), not **what** the tree looks like.

---

## Cross-skill calls

The skill calls `run-agent-browser` only as a capture helper in Variant 1. It never delegates to `convert-url-to-nextjs` — that's the sibling skill for building, not for documenting. If during execution the user shifts intent from "document" to "rebuild," stop and route to `convert-url-to-nextjs`.
