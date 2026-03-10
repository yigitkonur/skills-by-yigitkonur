---
name: build-daisyui-mcp
description: Use skill if you are building UI with daisyUI components, converting Figma designs or screenshots to daisyUI code, or generating themes using the daisyui-blueprint MCP server.
---

# build-daisyui-mcp

Build production-quality daisyUI 5 interfaces from natural language, Figma designs, screenshots, or existing code using two MCP tools.

## Core rules — never violate

1. **Nested object syntax only** — `{"components": {"button": true}}` — never arrays, never string paths.
2. **Semantic colors always** — `btn-primary`, not `bg-blue-500`. No `dark:` prefix on daisyUI colors.
3. **Batch MCP calls** — one call with all needed snippets. Never one-component-per-call.
4. **Fetch before guessing** — get the component reference to see valid class names and example keys before writing HTML.
5. **CSS-only interactions** — drawers use checkbox toggle, modals use `<dialog>`, dropdowns use `<details>`, tabs use radio inputs. No JavaScript unless explicitly requested.
6. **daisyUI v5 syntax** — `fieldset`/`fieldset-legend` (not `form-control`/`label-text`), `input` (not `input-bordered`), oklch colors.

## Two MCP tools

| Tool | Purpose | When to use |
|------|---------|-------------|
| `daisyui-blueprint-daisyUI-Snippets` | Retrieve component code, layouts, templates, themes | Every daisyUI task |
| `daisyui-blueprint-Figma-to-daisyUI` | Extract Figma design structure | When user provides a Figma URL |

Read `references/tool-api-reference.md` for complete parameter docs, output formats, and token budgets.

## Decision tree — which workflow to use

```
User request arrives →
│
├─ Contains a Figma URL?
│  YES → Figma workflow
│         Read references/workflows/figma-to-code.md
│
├─ Contains a screenshot / image?
│  YES → Screenshot workflow
│         Read references/workflows/screenshot-to-code.md
│
├─ Contains Bootstrap / other framework code?
│  YES → Migration workflow
│         Read references/workflows/bootstrap-conversion.md
│
├─ Contains verbose Tailwind (raw utility classes for a standard component)?
│  YES → Optimization workflow
│         Read references/workflows/tailwind-optimization.md
│
├─ Asks about theming / custom colors / dark mode?
│  YES → Theme workflow
│         Read references/workflows/theme-generation.md
│
├─ Needs a full page (dashboard, login, landing)?
│  YES → Template-first workflow
│         Read references/workflows/component-composition.md
│
├─ Needs a page layout (sidebar, bento grid)?
│  YES → Layout-first workflow
│         Read references/workflows/responsive-layouts.md
│
├─ Needs a specific component or example?
│  YES → Component workflow (see "Component / page building" below)
│
└─ General daisyUI question?
    → Fetch relevant component snippets → compose answer
```

## Workflow 1: Figma → daisyUI code

**Trigger**: User provides a Figma URL.

```
Step 1: FETCH    → Call Figma-to-daisyUI(url, depth=10)
Step 2: ANALYZE  → Identify layout, components, colors, typography, spacing
Step 3: SNIPPETS → Single batched Snippets call with ALL identified components + layout
Step 4: BUILD    → Compose HTML from snippets, map colors to semantic, apply responsive
```

**Do not skip any step.** The Figma tool returns design structure; the Snippets tool returns component code. Both are needed.

Read `references/workflows/figma-to-code.md` for detailed Figma-to-daisyUI mapping tables.

## Workflow 2: Screenshot → daisyUI code

**Trigger**: User provides a screenshot or image of a UI.

```
Step 1: Visually analyze the image — identify grid structure, components, colors
Step 2: Map visual elements to daisyUI components
Step 3: Fetch matching snippets in a single batched call
Step 4: Compose HTML matching the visual layout
Step 5: Add responsive variants (mobile → desktop)
```

Read `references/workflows/screenshot-to-code.md` for full workflow detail.

## Workflow 3: Bootstrap / Tailwind migration

**Trigger**: User provides Bootstrap or raw Tailwind code to convert.

```
Step 1: Identify framework components in source code
Step 2: Map to daisyUI equivalents (see mapping table below)
Step 3: Fetch daisyUI component references to verify class names
Step 4: Replace markup — keep content, replace classes and structure
Step 5: Verify no Bootstrap/Tailwind remnants on semantic elements
```

### Quick migration map

| Bootstrap / Tailwind | daisyUI |
|---------------------|---------|
| `btn btn-outline-primary` | `btn btn-outline btn-primary` |
| `alert alert-danger` | `alert alert-error` |
| `form-control` / `form-group` | `fieldset` + `input` |
| `d-none d-lg-block` | `max-lg:hidden` |
| `table-striped` | `table-zebra` |
| `bg-blue-500 text-white px-4 py-2 rounded` | `btn btn-primary` |
| `rounded-lg shadow-md p-6 bg-white` | `card bg-base-100 shadow-sm` + `card-body` |

Read `references/workflows/bootstrap-conversion.md` and `references/workflows/tailwind-optimization.md` for complete mapping tables.

## Workflow 4: Theme generation

**Trigger**: User asks about custom theme, brand colors, dark mode, or color customization.

```
Step 1: Fetch theme reference → {"themes": {"custom-theme": true, "colors": true}}
Step 2: Map brand colors to 20 semantic variables (oklch format)
Step 3: Generate -content colors with WCAG AA contrast
Step 4: Set shape variables (radius, size, border, depth, noise)
Step 5: Output complete @plugin "daisyui/theme" { ... } CSS block
```

26 required CSS variables: 20 colors + 3 radii + 2 sizes + border + depth + noise.

Read `references/theme-and-colors.md` for oklch conversion reference, all 35 built-in themes, dark theme tips, and design pattern presets.

## Workflow 5: Component / page building

**Trigger**: User wants a specific component, page layout, or full page.

### For a full page — start with template or layout:

```json
{"templates": {"dashboard": true}}
```
or
```json
{"layouts": {"responsive-collapsible-drawer-sidebar": true}}
```

### For specific components — fetch reference first, then examples:

```
Step 1: {"components": {"card": true, "button": true}}
        → See all valid classes and available example names
Step 2: {"component-examples": {"card.pricing-card": true, "button.button-with-icon": true}}
        → Get copy-paste HTML
```

Read `references/workflows/component-composition.md` for 6 full page patterns (dashboard, e-commerce, blog, settings, chat, landing).
Read `references/workflows/responsive-layouts.md` for 5 built-in layouts and 9 responsive patterns.

## Snippets tool — category guide

| Category | Returns | When to use |
|----------|---------|-------------|
| `components` | Class reference + syntax skeleton + example list | To **understand** a component before coding |
| `component-examples` | Ready-to-use HTML code | To **get working code** for a specific variation |
| `layouts` | Full page structure with placeholders | To **start a page layout** (sidebar, bento grid, navbar) |
| `templates` | Complete multi-component page | To **get a full working page** (dashboard, login) |
| `themes` | CSS configuration (not HTML) | To **set up theming** (colors, built-in themes, custom themes) |

### Available layouts

| Key | Use case |
|-----|----------|
| `responsive-collapsible-drawer-sidebar` | Sidebar collapses to icon-only |
| `responsive-offcanvas-drawer-sidebar` | Sidebar slides off-screen on mobile |
| `top-navbar` | Simple navbar + content + footer |
| `bento-grid-5-sections` | 5-area asymmetric grid |
| `bento-grid-8-sections` | 8-area complex grid |

### Available templates

| Key | Contains |
|-----|----------|
| `dashboard` | Drawer sidebar + navbar + stats + cards + CSS-only toggle |
| `login-form` | Side image + floating labels + validation + social auth |

## Calling patterns — performance rules

| Pattern | Calls | Do this? |
|---------|-------|----------|
| Batch multiple components in one call | 1 | ✅ Always |
| Mix categories (components + examples + themes) | 1 | ✅ Excellent |
| Components first → then targeted examples | 2 | ✅ When unsure of example names |
| Layout first → fill with component examples | 2-3 | ✅ For full pages |
| Theme first → then build with semantic colors | 2-3 | ✅ For branded UIs |
| Figma → analyze → snippets → build | 2 | ✅ Always for Figma |
| One component per call | N | ❌ Never |
| All examples for one component | 1 | ❌ Wasteful |

## Required component parts — do not forget

| Component | Required children |
|-----------|-------------------|
| `card` | `card-body` |
| `modal` | `modal-box`, `modal-action` |
| `drawer` | `drawer-toggle` (checkbox), `drawer-content`, `drawer-side`, `drawer-overlay` |
| `navbar` | `navbar-start`, `navbar-center`, `navbar-end` |
| `fieldset` | `fieldset-legend` |
| `collapse` | `collapse-title`, `collapse-content` |
| `stat` | `stat-title`, `stat-value` |

## CSS-only component patterns

| Component | Mechanism | Key pattern |
|-----------|-----------|-------------|
| Drawer | Hidden checkbox | `<input type="checkbox" class="drawer-toggle" />` + `<label for="id">` |
| Modal | Dialog element | `<dialog class="modal">` + `onclick="id.showModal()"` |
| Dropdown | Details element | `<details class="dropdown">` + `<summary>` |
| Tabs | Radio inputs | `<input type="radio" class="tab">` + sibling `.tab-content` |
| Accordion | Radio inputs | `<input type="radio" class="accordion">` + `.accordion-content` |
| Collapse | Checkbox/focus | `<input type="checkbox">` or `<details>` |
| Theme switch | Input + data-theme | `<input class="toggle" data-toggle-theme="dark">` |
| Swap | Checkbox | `<input type="checkbox">` with `.swap-on` / `.swap-off` |

## Responsive patterns — always apply

| Pattern | Classes |
|---------|---------|
| Persistent desktop sidebar | `drawer lg:drawer-open` |
| Hamburger menu (mobile only) | `btn lg:hidden` |
| Desktop-only nav | `hidden lg:flex` |
| Stats: stack → row | `stats-vertical lg:stats-horizontal` |
| Menu: vertical → horizontal | `menu-vertical lg:menu-horizontal` |
| Card: stack → side | `card sm:card-side` |
| Grid progression | `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4` |
| Mobile bottom nav | `dock lg:hidden` |
| Collapsible sidebar | `is-drawer-close:w-14 is-drawer-open:w-64` |

## daisyUI v4 → v5 migration — critical changes

| v4 pattern | v5 replacement |
|-----------|----------------|
| `form-control` | `fieldset` |
| `label` + `label-text` | `fieldset-legend` |
| `label-text-alt` | `fieldset-label` |
| `input-bordered` | `input` (borders default) |
| `select-bordered` | `select` (borders default) |
| `tab-lifted` | `tab-lift` |
| `bordered` (card) | `card-border` |
| HSL theme colors | oklch theme colors |
| `tailwind.config.js` themes | `@plugin "daisyui"` in CSS |
| N/A | New: `fieldset`, `validator`, `filter`, `dock`, `list`, `floating-label`, `hover-3d`, `hover-gallery`, `text-rotate` |
| N/A | New variants: `is-drawer-open:`, `is-drawer-close:`, `user-invalid:` |

## Multi-turn conversation patterns

### Turn 1: Establish structure
Fetch layout/template + relevant component references. Return complete initial HTML.

### Turn 2+: Modify content
If the user asks to change text, colors (within semantic system), or layout adjustments — modify existing code directly. **No MCP call needed.**

### New component needed
If the user requests a component not yet fetched, make a targeted Snippets call for that component only.

### Key principle
Only call MCP tools when you need **new component patterns** you haven't seen. For content/style changes within the existing component set, modify directly.

## Quality checklist — verify before returning code

- [ ] All HTML uses valid daisyUI v5 class names (no invented classes)
- [ ] Semantic colors used everywhere (no `bg-blue-500` on interactive elements)
- [ ] No `dark:` prefix on daisyUI semantic colors
- [ ] All cards have `card-body`
- [ ] All modals use `<dialog>` with `modal-box`
- [ ] All drawers have complete structure (toggle + content + side + overlay)
- [ ] Forms use `fieldset` + `fieldset-legend` (not `form-control`)
- [ ] Responsive breakpoints on layout components (`lg:drawer-open`, etc.)
- [ ] No JavaScript for CSS-only components
- [ ] `input` not `input-bordered` (v5 default)

## Reference routing

| Need | Read |
|------|------|
| Tool parameters, output formats, token budgets | `references/tool-api-reference.md` |
| Component classes, parts, colors, sizes | `references/component-catalog.md` |
| Theme CSS template, oklch, built-in themes | `references/theme-and-colors.md` |
| Common agent mistakes and fixes | `references/common-mistakes.md` |
| Figma → daisyUI code workflow | `references/workflows/figma-to-code.md` |
| Screenshot → daisyUI code workflow | `references/workflows/screenshot-to-code.md` |
| Bootstrap → daisyUI migration | `references/workflows/bootstrap-conversion.md` |
| Tailwind → daisyUI optimization | `references/workflows/tailwind-optimization.md` |
| Custom theme generation | `references/workflows/theme-generation.md` |
| Full page composition patterns | `references/workflows/component-composition.md` |
| Responsive layout patterns | `references/workflows/responsive-layouts.md` |
| Screenshot conversion prompt | `references/prompts/screenshot-prompt.md` |
| Bootstrap conversion prompt | `references/prompts/bootstrap-prompt.md` |
| Tailwind conversion prompt | `references/prompts/tailwind-prompt.md` |
| Image-to-theme extraction prompt | `references/prompts/image-to-theme-prompt.md` |
| Prompt engineering patterns | `references/prompts/prompt-engineering.md` |
| Multi-step prompt chaining | `references/prompts/prompt-chaining.md` |
