---
name: build-daisyui-mcp
description: Use skill if you are building UI with daisyUI components, converting Figma designs or screenshots to daisyUI code, or generating themes using the daisyui-blueprint MCP server.
---

# build-daisyui-mcp

Use this skill as the operating layer for daisyUI 5 work with the `daisyui-blueprint` MCP tools. Keep `SKILL.md` lean: choose the correct workflow, fetch only the references you need, and keep bulky detail in `references/`.

## Use this skill for

- Building or refactoring UI with daisyUI 5 + Tailwind v4
- Converting a Figma frame or screenshot into daisyUI code
- Choosing the right snippet category: `components`, `component-examples`, `layouts`, `templates`, or `themes`
- Generating or adapting a custom daisyUI theme from brand colors, images, or existing UI

## Do not use this skill for

- Pure Tailwind work with no daisyUI goal
- UI libraries other than daisyUI
- Generic design discussion that does not need daisyUI code, snippets, or themes

## Non-negotiable rules

1. **Nested object syntax only** for `daisyui-blueprint-daisyUI-Snippets`. Arrays fail.
2. **Fetch before guessing.** If you do not know a valid class or example key, fetch the component reference first.
3. **Batch requests.** Get all needed snippets in one call; do not fetch one component at a time.
4. **Use the right category.** `components` is reference data, not copy-paste HTML. `component-examples` is working markup. `themes` returns CSS, not HTML.
5. **Start page work from `layouts` or `templates`** when possible. Do not assemble full pages from many isolated component guesses.
6. **For Figma, always follow** `FETCH → ANALYZE → GET SNIPPETS → BUILD`. Never skip analysis.
7. **Use semantic daisyUI colors** (`primary`, `secondary`, `accent`, `neutral`, `base-*`, `info`, `success`, `warning`, `error`) and `*-content` variants on themed surfaces.
8. **Do not use `dark:` for daisyUI semantic colors.** Themes already adapt them.
9. **Prefer CSS-only daisyUI interaction patterns** unless app-specific behavior truly requires custom JS:
   - drawer → checkbox toggle
   - modal → `<dialog>`
   - dropdown → `<details>`
   - tabs/steppers → daisyUI radio/tab patterns
10. **Stay on daisyUI v5 syntax** (`fieldset`, `dock`, `tabs-lift`, `card-border`, no `input-bordered`, no `form-control`).
11. **Load only the 1–3 references needed for the active task.** Do not dump the entire skill into context.

```jsonc
// ✅ Correct
{
  "components": { "button": true, "card": true },
  "component-examples": { "card.card": true }
}

// ❌ Wrong
{ "components": ["button", "card"] }
{ "snippets": ["components/button"] }
```

## Choose the right tool or snippet category first

| Need | Use | Key rule |
|---|---|---|
| Validate classes, parts, modifiers, or discover example names | `components` | Start here when unsure |
| Copy-paste markup for a known pattern | `component-examples` | Fetch only the 1–3 best matches |
| Get a page shell with placeholders | `layouts` | Best starting point for dashboards, sidebars, app shells |
| Start from a full page | `templates` | Use for login/dashboard/full-page acceleration |
| Get theme variables or color-system reference | `themes` | Returns CSS/config, not component HTML |
| Extract structure from a Figma design | `daisyui-blueprint-Figma-to-daisyUI` | Returns a node tree only; always follow with snippets |

**Mix categories in one call** when you already know what you need:

```json
{
  "layouts": { "responsive-collapsible-drawer-sidebar": true },
  "components": { "navbar": true, "card": true, "table": true },
  "component-examples": {
    "navbar.responsive-dropdown-menu-on-small-screen-center-menu-on-large-screen": true,
    "table.table-with-visual-elements": true
  },
  "themes": { "colors": true }
}
```

## Route to the correct workflow

| Request shape | Do this first | Then load |
|---|---|---|
| Setup or install daisyUI / Tailwind v4 | Read setup docs | `references/integration/tailwind-v4-setup.md` |
| MCP server missing or Figma auth/setup issue | Fix tool setup before composing UI | `references/tool-api-reference.md` |
| Migrating from daisyUI v4 | Read migration docs before writing code | `references/integration/v4-to-v5-migration.md` |
| Single component or section | Fetch `components` first, then targeted `component-examples` | `references/component-catalog.md`, `references/common-mistakes.md` |
| Full page, dashboard, auth screen, landing page | Start from `layouts` or `templates` | `references/workflows/component-composition.md`, `references/workflows/responsive-layouts.md` |
| Figma URL present | Run the Figma workflow below | `references/workflows/figma-to-code.md`, `references/tool-api-reference.md` |
| Screenshot or image mockup | Run the screenshot workflow below | `references/workflows/screenshot-to-code.md`, `references/common-mistakes.md` |
| Brand colors, image-to-theme, dark mode, theme request | Run the theme workflow below | `references/workflows/theme-generation.md`, `references/theming/custom-themes.md` |
| Form-heavy UI | Load form patterns before composing | `references/patterns/form-patterns.md` |
| Navbar, menu, drawer, tabs, dock, breadcrumbs | Load navigation patterns before composing | `references/patterns/navigation-patterns.md` |
| Bootstrap or raw Tailwind conversion | Use the relevant conversion workflow | `references/workflows/bootstrap-conversion.md`, `references/workflows/tailwind-optimization.md` |

## Workflow — component or page composition

1. **Decide scope first.**
   - Single component/section → fetch component reference, then examples.
   - Full page/app shell → fetch a layout or template first.
2. **Fetch reference data before markup** for any component whose valid classes you do not know.
3. **Fetch only targeted examples** for complex pieces like responsive navbars, drawers, tables, pricing cards, or form patterns.
4. **Compose from the outside in**:
   - page shell
   - navigation
   - main content blocks
   - detail components
5. **Apply semantic colors and responsive utilities** after structure is correct.
6. **If the page is branded**, do theme work before final polish so semantic colors resolve correctly.

Load only what you need:

- `references/workflows/component-composition.md`
- `references/workflows/responsive-layouts.md`
- `references/component-catalog.md`

## Workflow — Figma to daisyUI

This sequence is mandatory.

1. **FETCH**
   - Call `daisyui-blueprint-Figma-to-daisyUI`
   - Prefer a node-specific Figma URL
   - Start with `depth: 3-5`
   - Use `includeImages: false` unless image references are required
2. **ANALYZE**
   - layout direction and alignment
   - spacing and padding
   - component candidates
   - typography scale
   - corner radius, shadows, and color roles
3. **GET SNIPPETS**
   - Batch all identified components in one call
   - If example names are unknown, fetch `components` first, then the exact `component-examples`
4. **BUILD**
   - Map Figma structure to daisyUI components + Tailwind layout classes
   - Use semantic colors instead of hardcoded hex on UI surfaces
   - Add responsive breakpoints explicitly
5. **RECOVER IF NEEDED**
   - If the node tree is too shallow, re-fetch with higher depth
   - If the file is large/noisy, switch to a more specific node URL

Load only what you need:

- `references/workflows/figma-to-code.md`
- `references/tool-api-reference.md`
- `references/component-catalog.md` when class lookup is needed

## Workflow — screenshot or mockup to daisyUI

1. **Scan top-to-bottom**: navbar/header, hero, sidebar, main content, footer/dock.
2. **Identify the page shell first** before individual components.
3. **Catalog visible patterns**:
   - component type
   - likely variant
   - size
   - semantic color role
   - visible state
4. **Fetch components and only the best-matching examples.**
5. **Assemble the shell first**, then fill details and tune spacing/color.
6. **If an interaction is not visible**, choose the most likely CSS-only daisyUI pattern and state the assumption.

Load only what you need:

- `references/workflows/screenshot-to-code.md`
- `references/component-catalog.md`
- `references/common-mistakes.md`

## Workflow — theme generation

1. **Determine the source**: brand palette, image, existing website, or Figma tokens.
2. **Map source colors to daisyUI semantics**:
   - `primary`, `secondary`, `accent`
   - `neutral`
   - `base-100`, `base-200`, `base-300`, `base-content`
   - `info`, `success`, `warning`, `error`
3. **Generate matching `*-content` colors** with accessible contrast.
4. **Output `@plugin "daisyui/theme"` CSS in OKLCH.**
5. **Validate with semantic component usage**; do not leave UI surfaces on raw Tailwind colors.
6. **If building branded UI**, theme first, then fetch templates/components so the markup stays semantic.

Load only what you need:

- `references/workflows/theme-generation.md`
- `references/theming/custom-themes.md`
- `references/tool-api-reference.md` for `themes` usage

## Recovery rules — if the agent starts drifting

- **Snippets tool returns nothing** → check nested object syntax first.
- **You do not know an example key** → fetch the component reference before guessing.
- **Generated classes look plausible but unverified** → check `references/component-catalog.md` or the component response.
- **You are making too many MCP calls** → batch them and mix categories.
- **A full page is forming from unrelated snippets** → restart from a `layout` or `template`.
- **The MCP server or Figma tool errors on setup/auth** → check `references/tool-api-reference.md`, especially MCP config and `FIGMA` requirements.
- **Markup uses `bg-blue-500`, `text-white`, or `dark:` on themed UI** → replace with semantic color classes or a theme.
- **You added JS for a standard drawer/modal/dropdown** → switch back to the CSS-only daisyUI mechanism.
- **You see v4 terms** like `form-control`, `input-bordered`, `label-text`, `tabs-lifted`, or `btm-nav` → convert to v5 and load migration docs if needed.
- **You start copying bulky examples into this skill** → stop and route to the relevant reference instead.

## Minimal reference packs

| Task | Load |
|---|---|
| Single component/section | `references/component-catalog.md`, `references/common-mistakes.md` |
| Full page/layout | `references/workflows/component-composition.md`, `references/workflows/responsive-layouts.md` |
| Figma conversion | `references/workflows/figma-to-code.md`, `references/tool-api-reference.md` |
| Screenshot conversion | `references/workflows/screenshot-to-code.md`, `references/common-mistakes.md` |
| Theme generation | `references/workflows/theme-generation.md`, `references/theming/custom-themes.md` |
| Forms | `references/patterns/form-patterns.md`, `references/component-catalog.md` |
| Navigation | `references/patterns/navigation-patterns.md`, `references/component-catalog.md` |
| Setup or migration | `references/integration/tailwind-v4-setup.md`, `references/integration/v4-to-v5-migration.md` |
| Bootstrap/Tailwind conversion | `references/workflows/bootstrap-conversion.md`, `references/workflows/tailwind-optimization.md` |

## Exit checklist

Before finishing, confirm:

- correct snippets syntax
- correct category choice
- batched MCP calls
- valid daisyUI v5 classes
- semantic colors or a proper theme
- layout/template used for page-level work when appropriate
- mandatory Figma sequence followed for Figma tasks
- only necessary references were loaded
