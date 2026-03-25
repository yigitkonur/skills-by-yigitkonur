# daisyUI v5 — Definitive Component Catalog

> **Purpose**: The single lookup table for every daisyUI 5 component — classes, parts, colors, sizes, mechanisms, and gotchas. Use this before writing any markup.

---

## Class Naming Conventions

Every daisyUI class belongs to exactly one type:

| Type | Purpose | Pattern | Example |
|------|---------|---------|---------|
| **COMPONENT** | Required base class on the root element | `{name}` | `btn`, `card`, `modal`, `drawer` |
| **PART** | Child element within a component | `{component}-{part}` | `card-body`, `card-title`, `modal-box` |
| **STYLE** | Visual variant applied to component | `{component}-{style}` | `btn-outline`, `btn-dash`, `btn-soft`, `btn-ghost`, `btn-link` |
| **BEHAVIOR** | Functional/state change | `{component}-{behavior}` | `modal-open`, `drawer-open`, `menu-dropdown-show` |
| **COLOR** | Semantic color modifier | `{component}-{color}` | `btn-primary`, `alert-error`, `badge-success` |
| **SIZE** | Size variant (xs/sm/md/lg/xl) | `{component}-{size}` | `btn-lg`, `input-sm`, `card-xl` |
| **PLACEMENT** | Positional modifier | `{component}-{position}` | `modal-top`, `drawer-end`, `toast-start` |
| **DIRECTION** | Layout direction modifier | `{component}-{direction}` | `menu-horizontal`, `stats-vertical`, `join-vertical` |
| **MODIFIER** | Miscellaneous shape/width/layout | `{component}-{mod}` | `btn-wide`, `btn-block`, `btn-square`, `card-side` |
| **VARIANT** | Conditional utility prefix (daisyUI-specific) | `{variant}:{utility}` | `is-drawer-open:w-64`, `is-drawer-close:w-14`, `user-invalid:validator` |

### Key Rules

1. **Base class is always the component name** — `btn`, `card`, `modal`
2. **Modifiers stack on the base** — `btn btn-primary btn-lg btn-outline`
3. **Parts are hyphenated children** — `card-body`, `card-title`, `card-actions`
4. **`md` is the implicit default** — you never need to write `-md` explicitly
5. **Never invent classes** — there is no `btn-rounded`, `input-bordered` (v5), or `form-control` (v4)

### Semantic Colors Available

| Color | CSS Variable | Purpose |
|-------|-------------|---------|
| `primary` | `--color-primary` | Main brand action |
| `secondary` | `--color-secondary` | Secondary brand |
| `accent` | `--color-accent` | Accent/highlight |
| `neutral` | `--color-neutral` | Unsaturated UI elements |
| `info` | `--color-info` | Informational |
| `success` | `--color-success` | Success state |
| `warning` | `--color-warning` | Warning state |
| `error` | `--color-error` | Error/danger state |

### Style Variants Cross-Reference

| Style | Class Pattern | Available On |
|-------|--------------|-------------|
| Outline | `{component}-outline` | btn, badge, alert |
| Dash | `{component}-dash` | btn, badge, alert, card |
| Soft | `{component}-soft` | btn, badge, alert |
| Ghost | `{component}-ghost` | btn, input, select, textarea, file-input |
| Link | `btn-link` | btn only |
| Glass | `glass` | Any element |

---

## Navigation Components

### Navbar

| Property | Details |
|----------|---------|
| **Component class** | `navbar` |
| **Parts** | `navbar-start`, `navbar-center`, `navbar-end` |
| **Styles** | — (use Tailwind bg/text utilities for color) |
| **Colors** | No component-level color classes. Apply `bg-primary text-primary-content`, `bg-neutral text-neutral-content`, etc. |
| **Sizes** | — |
| **Required children** | At least one of `navbar-start`, `navbar-center`, `navbar-end` |
| **CSS-only mechanism** | — |
| **Gotchas** | No built-in color classes — use Tailwind utilities. Combine with `dropdown` inside `navbar-start` for responsive mobile menus. |

---

### Menu

| Property | Details |
|----------|---------|
| **Component class** | `menu` |
| **Parts** | `menu-title`, `menu-dropdown`, `menu-dropdown-toggle` |
| **Styles** | `menu-active` (on `<a>` for active item) |
| **Colors** | — (items inherit; use Tailwind utilities for active/hover) |
| **Sizes** | `menu-xs`, `menu-sm`, `menu-md`, `menu-lg`, `menu-xl` |
| **Direction** | `menu-horizontal`, `menu-vertical` (default) |
| **Required children** | `<ul>` with `<li>` items containing `<a>` |
| **CSS-only mechanism** | `<details><summary>` for collapsible submenus |
| **Gotchas** | Submenu uses native `<details>/<summary>` — no JS needed. `menu-active` goes on the `<a>`, not the `<li>`. Responsive pattern: `menu menu-vertical lg:menu-horizontal`. |

---

### Breadcrumbs

| Property | Details |
|----------|---------|
| **Component class** | `breadcrumbs` |
| **Parts** | — |
| **Styles** | — |
| **Colors** | — |
| **Sizes** | — (use Tailwind `text-sm`, `text-xs` etc.) |
| **Required children** | `<ul>` with `<li>` items; last `<li>` has no `<a>` (current page) |
| **CSS-only mechanism** | — |
| **Gotchas** | Separator is CSS-generated between `<li>` items. Use `max-w-xs` on `<li>` for truncation. |

---

### Tab

| Property | Details |
|----------|---------|
| **Component class** | `tabs` (container), `tab` (each tab) |
| **Parts** | `tab-content` (panel below a radio tab) |
| **Styles** | `tabs-border` (underline), `tabs-lift` (raised), `tabs-box` (boxed) |
| **Colors** | Custom via `[--tab-bg:theme(colors.primary)]` on `.tabs` |
| **Sizes** | `tabs-xs`, `tabs-sm`, `tabs-md`, `tabs-lg`, `tabs-xl` |
| **Modifiers** | `tab-active` (active state on link-based tabs) |
| **Required children** | `<a class="tab">` or `<input type="radio" class="tab">` + `<div class="tab-content">` |
| **CSS-only mechanism** | Radio inputs — `<input type="radio" class="tab">` paired with sibling `<div class="tab-content">` |
| **Gotchas** | Radio-based tabs need `name` attribute shared across group + `checked="checked"` on default. Link-based tabs use `tab-active` class. v5 renamed `tabs-lifted` → `tabs-lift`. Scrollable: wrap in `overflow-x-auto`. |

---

### Pagination

| Property | Details |
|----------|---------|
| **Component class** | `join` (container) — pagination has no dedicated class |
| **Parts** | `join-item` (on each `btn`) |
| **Styles** | Inherits from `btn` — `btn-outline`, etc. |
| **Colors** | Inherits from `btn` — `btn-primary`, etc. |
| **Sizes** | Inherits from `btn` — `btn-xs`, `btn-sm`, `btn-lg`, `btn-xl` |
| **Modifiers** | `btn-active` (current page), `btn-disabled` (unavailable) |
| **Required children** | `<div class="join">` with `<button class="join-item btn">` children |
| **CSS-only mechanism** | Radio inputs: `<input type="radio" class="join-item btn" aria-label="1">` |
| **Gotchas** | No `pagination` class exists — it's composed from `join` + `btn`. Equal-width prev/next: add explicit `w-28` or similar. |

---

### Dock

| Property | Details |
|----------|---------|
| **Component class** | `dock` |
| **Parts** | `dock-label` |
| **Styles** | `dock-active` (on active button) |
| **Colors** | — (use Tailwind `bg-*` / `text-*` utilities) |
| **Sizes** | `dock-xs`, `dock-sm`, `dock-md`, `dock-lg`, `dock-xl` |
| **Required children** | `<button>` elements with icon + optional `<span class="dock-label">` |
| **CSS-only mechanism** | — |
| **Gotchas** | New in v5 — no v4 equivalent. Fixed to bottom of viewport. Active item uses `dock-active` class on the `<button>`. |

---

### Link

| Property | Details |
|----------|---------|
| **Component class** | `link` |
| **Parts** | — |
| **Styles** | `link-hover` (underline only on hover) |
| **Colors** | `link-primary`, `link-secondary`, `link-accent`, `link-neutral`, `link-info`, `link-success`, `link-warning`, `link-error` |
| **Sizes** | — |
| **Required children** | Text content |
| **CSS-only mechanism** | — |
| **Gotchas** | `link-hover` removes the default underline and only shows it on hover. Without `link-hover`, links are always underlined. |

---

### Steps

| Property | Details |
|----------|---------|
| **Component class** | `steps` (container) |
| **Parts** | `step` (each step) |
| **Styles** | — |
| **Colors** | `step-primary`, `step-secondary`, `step-accent`, `step-neutral`, `step-info`, `step-success`, `step-warning`, `step-error` |
| **Sizes** | — |
| **Direction** | `steps-horizontal` (default), `steps-vertical` |
| **Required children** | `<ul class="steps">` with `<li class="step">` items |
| **CSS-only mechanism** | — |
| **Gotchas** | Color class on a step colors it AND the line before it. Use `data-content` attribute for custom step icon text (e.g., `data-content="✓"`). Responsive: `steps-vertical lg:steps-horizontal`. Scrollable: wrap in `overflow-x-auto`. |

---

## Data Display Components

### Table

| Property | Details |
|----------|---------|
| **Component class** | `table` |
| **Parts** | — |
| **Styles** | — |
| **Colors** | — |
| **Sizes** | `table-xs`, `table-sm`, `table-md`, `table-lg`, `table-xl` |
| **Modifiers** | `table-zebra` (striped rows), `table-pin-rows` (sticky header), `table-pin-cols` (sticky first column) |
| **Behavior** | `table-row-active` (on `<tr>`), `hover` (on `<tr>` for hover highlight) |
| **Required children** | `<table class="table">` with `<thead>`, `<tbody>`, `<tr>`, `<th>`, `<td>` |
| **CSS-only mechanism** | — |
| **Gotchas** | Always wrap in `<div class="overflow-x-auto">` for horizontal scroll. Active row: `table-row-active` on `<tr>`. No component-level color classes — use Tailwind utilities on rows/cells. |

---

### Stat

| Property | Details |
|----------|---------|
| **Component class** | `stats` (container), `stat` (individual metric) |
| **Parts** | `stat-title`, `stat-value`, `stat-desc`, `stat-figure`, `stat-actions` |
| **Styles** | — |
| **Colors** | — (use Tailwind `text-primary`, `bg-primary`, etc. on parts) |
| **Sizes** | — |
| **Direction** | `stats-horizontal` (default), `stats-vertical` |
| **Required children** | `<div class="stats">` containing `<div class="stat">` with at least `stat-title` + `stat-value` |
| **CSS-only mechanism** | — |
| **Gotchas** | Responsive pattern: `stats-vertical lg:stats-horizontal`. Center items: add `place-items-center` to `.stat`. The `stat-figure` appears to the right by default. |

---

### Card

| Property | Details |
|----------|---------|
| **Component class** | `card` |
| **Parts** | `card-body`, `card-title`, `card-actions` |
| **Styles** | `card-border` (border), `card-dash` (dashed border) |
| **Colors** | — (use Tailwind `bg-primary text-primary-content`, etc.) |
| **Sizes** | `card-xs`, `card-sm`, `card-md`, `card-lg`, `card-xl` |
| **Modifiers** | `card-side` (horizontal layout), `image-full` (overlay image) |
| **Required children** | `card-body` is required inside `card` |
| **CSS-only mechanism** | — |
| **Gotchas** | **Always include `card-body`** — skipping it breaks padding/layout. v5 uses `card-border` (not `bordered`). Use `<figure>` for images above the body. Responsive: `card sm:card-side` for horizontal on tablet+. |

---

### List

| Property | Details |
|----------|---------|
| **Component class** | `list` |
| **Parts** | `list-row` |
| **Styles** | — |
| **Colors** | — |
| **Sizes** | — |
| **Modifiers** | `list-col-wrap` (third column wraps to next row), `list-col-grow` (third column grows instead of second) |
| **Required children** | `<ul class="list">` with `<li class="list-row">` containing up to 3 child `<div>` elements |
| **CSS-only mechanism** | — |
| **Gotchas** | New in v5. Three-column layout by default: first = avatar/icon, second = text (grows), third = action. Apply `list-col-grow` on the `<ul>` to make the third column grow instead. |

---

### Avatar

| Property | Details |
|----------|---------|
| **Component class** | `avatar` |
| **Parts** | — |
| **Styles** | — |
| **Colors** | — |
| **Sizes** | — (use Tailwind `w-*` / `h-*` on the inner div) |
| **Modifiers** | `avatar-group` (overlapping group), `avatar-placeholder` (text initials), `avatar-online` (green dot), `avatar-offline` (gray dot) |
| **Required children** | `<div class="avatar">` → inner `<div class="w-{size} rounded-full">` → `<img>` |
| **CSS-only mechanism** | — |
| **Gotchas** | Size is controlled by Tailwind width on the **inner** div, not the `.avatar` wrapper. Presence state goes on the wrapper: `<div class="avatar avatar-online">`. Placeholder state also lives on the wrapper: `<div class="avatar avatar-placeholder">`. Ring: add `ring ring-primary ring-offset-base-100 ring-offset-2` to the inner div. Shapes: use `rounded-full`, `rounded-xl`, or `mask mask-squircle`. Group: `<div class="avatar-group -space-x-6">`. |

---

### Badge

| Property | Details |
|----------|---------|
| **Component class** | `badge` |
| **Parts** | — |
| **Styles** | `badge-outline`, `badge-dash`, `badge-soft` |
| **Colors** | `badge-primary`, `badge-secondary`, `badge-accent`, `badge-neutral`, `badge-info`, `badge-success`, `badge-warning`, `badge-error`, `badge-ghost` |
| **Sizes** | `badge-xs`, `badge-sm`, `badge-md`, `badge-lg`, `badge-xl` |
| **Required children** | Text or icon content |
| **CSS-only mechanism** | — |
| **Gotchas** | Empty badge (dot indicator): `<span class="badge badge-xs badge-primary"></span>`. In buttons: `<button class="btn">Inbox <span class="badge">+99</span></button>`. Neutral outline/dash: `badge-neutral badge-outline`. |

---

### Chat

| Property | Details |
|----------|---------|
| **Component class** | `chat` |
| **Parts** | `chat-image`, `chat-header`, `chat-bubble`, `chat-footer` |
| **Styles** | — |
| **Colors** | `chat-bubble-primary`, `chat-bubble-secondary`, `chat-bubble-accent`, `chat-bubble-neutral`, `chat-bubble-info`, `chat-bubble-success`, `chat-bubble-warning`, `chat-bubble-error` |
| **Sizes** | — |
| **Placement** | `chat-start` (left-aligned), `chat-end` (right-aligned) |
| **Required children** | `chat-bubble` with text content; `chat-start` or `chat-end` on the `.chat` wrapper |
| **CSS-only mechanism** | — |
| **Gotchas** | Color goes on `chat-bubble`, not on `chat` — e.g., `chat-bubble chat-bubble-primary`. The `chat-image` wraps an `avatar` component. `chat-header` and `chat-footer` are optional metadata lines. |

---

### Countdown

| Property | Details |
|----------|---------|
| **Component class** | `countdown` |
| **Parts** | — |
| **Styles** | — |
| **Colors** | — |
| **Sizes** | — (use Tailwind `text-*` for font size) |
| **Required children** | `<span class="countdown">` → `<span style="--value:N;"></span>` |
| **CSS-only mechanism** | CSS `--value` custom property (0–99) drives animated digit transitions |
| **Gotchas** | `--value` accepts integers 0–99 only. Update via JS: `el.style.setProperty("--value", n)`. For clock format, compose multiple `countdown` spans with `:` separators. |

---

### Diff

| Property | Details |
|----------|---------|
| **Component class** | `diff` |
| **Parts** | `diff-item-1`, `diff-item-2`, `diff-resizer` |
| **Styles** | — |
| **Colors** | — |
| **Sizes** | — (use Tailwind `aspect-*` on `.diff`) |
| **Required children** | Two `diff-item` divs (`diff-item-1` and `diff-item-2`) each containing an `<img>` or text content |
| **CSS-only mechanism** | Native CSS resize + overlay |
| **Gotchas** | `diff-resizer` adds the draggable handle — omit for static comparison. Use `aspect-16/9` or similar on the `.diff` container. Works with text content too, not just images. |

---

### Kbd

| Property | Details |
|----------|---------|
| **Component class** | `kbd` |
| **Parts** | — |
| **Styles** | — |
| **Colors** | — |
| **Sizes** | `kbd-xs`, `kbd-sm`, `kbd-md`, `kbd-lg`, `kbd-xl` |
| **Required children** | Key text content (e.g., `Ctrl`, `A`, `⌘`) |
| **CSS-only mechanism** | — |
| **Gotchas** | For key combinations, use separate `<kbd>` elements joined by ` + ` text. Arrow keys: use `▲▼◀▶` characters. |

---

### Timeline

| Property | Details |
|----------|---------|
| **Component class** | `timeline` |
| **Parts** | `timeline-start`, `timeline-middle`, `timeline-end`, `timeline-box` |
| **Styles** | — |
| **Colors** | — (use Tailwind `bg-primary` etc. on `<hr>` connectors) |
| **Sizes** | — |
| **Direction** | Horizontal (default), `timeline-vertical` |
| **Modifiers** | `timeline-snap-icon` (align icons to start) |
| **Required children** | `<ul class="timeline">` → `<li>` with `timeline-start`/`timeline-middle`/`timeline-end` sections and `<hr>` connectors between items |
| **CSS-only mechanism** | — |
| **Gotchas** | `<hr>` elements between `<li>` items form the connecting lines — color them with `bg-primary` etc. `timeline-box` adds a bordered box around content. Alternating sides: swap placement of content between `timeline-start` and `timeline-end` per item. Responsive: `timeline-vertical lg:timeline-horizontal`. |

---

### Calendar

| Property | Details |
|----------|---------|
| **Component class** | `cally` (for Cally web component), `pika-single` (Pikaday), `react-day-picker` (React Day Picker) |
| **Parts** | — |
| **Styles** | — |
| **Colors** | — (inherits theme colors) |
| **Sizes** | — |
| **Required children** | Third-party library setup (Cally, Pikaday, or React Day Picker) |
| **CSS-only mechanism** | — |
| **Gotchas** | daisyUI provides **styling only** — you must include a third-party calendar library for functionality. Cally uses `<calendar-date>` web component. Pikaday uses a script + input. All integrate with daisyUI theme colors automatically. |

---

## Action Components

### Button

| Property | Details |
|----------|---------|
| **Component class** | `btn` |
| **Parts** | — |
| **Styles** | `btn-outline`, `btn-dash`, `btn-soft`, `btn-ghost`, `btn-link` |
| **Colors** | `btn-primary`, `btn-secondary`, `btn-accent`, `btn-neutral`, `btn-info`, `btn-success`, `btn-warning`, `btn-error` |
| **Sizes** | `btn-xs`, `btn-sm`, `btn-md`, `btn-lg`, `btn-xl` |
| **Modifiers** | `btn-wide`, `btn-block` (full width), `btn-square` (1:1 ratio), `btn-circle` (round) |
| **Behavior** | `btn-active` (forced active state), `btn-disabled` (forced disabled look) |
| **Required children** | Text, icon, or both |
| **CSS-only mechanism** | Works on `<button>`, `<a>`, `<input type="checkbox">`, `<input type="radio">`, `<input type="submit">` |
| **Gotchas** | `btn-ghost` + `btn-link` are styles, not colors. Multiple modifiers stack: `btn btn-primary btn-lg btn-outline`. Disabled: prefer HTML `disabled` attribute over `btn-disabled` class. Loading: `<span class="loading loading-spinner"></span>` inside the button. Responsive: `btn-sm lg:btn-lg`. |

---

### Dropdown

| Property | Details |
|----------|---------|
| **Component class** | `dropdown` |
| **Parts** | `dropdown-content` |
| **Styles** | — |
| **Colors** | — |
| **Sizes** | — |
| **Placement** | `dropdown-top`, `dropdown-bottom` (default), `dropdown-left`, `dropdown-right` |
| **Direction** | `dropdown-start`, `dropdown-center`, `dropdown-end` |
| **Behavior** | `dropdown-hover` (open on hover), `dropdown-open` (force open) |
| **Required children** | A trigger element (`<div tabindex="0" role="button" class="btn">`) + `<ul class="dropdown-content menu">` |
| **CSS-only mechanism** | Focus/blur (default), `<details>/<summary>`, or Popover API (`popovertarget`) |
| **Gotchas** | Trigger needs `tabindex="0"` and `role="button"`. `dropdown-content` needs `tabindex="0"` too. Always add `z-1` (or higher) to `dropdown-content` to avoid stacking issues. Card-as-dropdown: replace `<ul>` with `<div class="card dropdown-content">`. |

---

### Modal

| Property | Details |
|----------|---------|
| **Component class** | `modal` |
| **Parts** | `modal-box`, `modal-action`, `modal-backdrop`, `modal-toggle` |
| **Styles** | — |
| **Colors** | — |
| **Sizes** | — (use `w-11/12 max-w-5xl` etc. on `modal-box`) |
| **Placement** | `modal-top`, `modal-bottom`, `modal-middle` |
| **Required children** | `<dialog class="modal">` → `<div class="modal-box">` with content + `<div class="modal-action">` |
| **CSS-only mechanism** | `<dialog>` element with `showModal()`/`close()` (recommended). Also supports checkbox: `<input type="checkbox" class="modal-toggle">` + `<label class="modal">` |
| **Gotchas** | **Use `<dialog>` element** — it's the recommended v5 approach. Open: `document.getElementById('id').showModal()`. Close: `<form method="dialog"><button>Close</button></form>`. Backdrop click close: add `<form method="dialog" class="modal-backdrop"><button>close</button></form>` **after** `modal-box`. Responsive: `modal-bottom sm:modal-middle`. Corner close button: absolute-positioned inside `modal-box`. |

---

### Swap

| Property | Details |
|----------|---------|
| **Component class** | `swap` |
| **Parts** | `swap-on`, `swap-off`, `swap-indeterminate` |
| **Styles** | `swap-rotate` (rotation animation), `swap-flip` (flip animation) |
| **Colors** | — |
| **Sizes** | — |
| **Modifiers** | `swap-active` (force active state via class, no checkbox) |
| **Required children** | `<label class="swap">` → `<input type="checkbox">` + `<div class="swap-on">` + `<div class="swap-off">` |
| **CSS-only mechanism** | Checkbox toggles between `swap-on` and `swap-off` visibility |
| **Gotchas** | Without `swap-rotate` or `swap-flip`, the swap is an instant cut. Activate via class (JS): add/remove `swap-active` instead of using a checkbox. Common use: theme toggle, hamburger menu, volume icon. |

---

### Theme Controller

| Property | Details |
|----------|---------|
| **Component class** | `theme-controller` (applied to an input element) |
| **Parts** | — |
| **Styles** | — |
| **Colors** | — |
| **Sizes** | — |
| **Required children** | `<input>` (checkbox, radio, or toggle) with `class="theme-controller"` and `value="{theme-name}"` |
| **CSS-only mechanism** | Checkbox/radio input changes `data-theme` on `<html>` |
| **Gotchas** | `value` attribute **must** match a configured theme name. Works with: checkbox (toggle 2 themes), radio (select from many), toggle, swap. For dropdown selector: place radio inputs inside `dropdown-content`. |

---

## Form Components

### Input

| Property | Details |
|----------|---------|
| **Component class** | `input` |
| **Parts** | — |
| **Styles** | `input-ghost` |
| **Colors** | `input-primary`, `input-secondary`, `input-accent`, `input-neutral`, `input-info`, `input-success`, `input-warning`, `input-error` |
| **Sizes** | `input-xs`, `input-sm`, `input-md`, `input-lg`, `input-xl` |
| **Required children** | Self-closing `<input>` element |
| **CSS-only mechanism** | — |
| **Gotchas** | **v5 inputs have borders by default** — no `input-bordered` needed (that's v4). Icon pattern: `<label class="input"><svg>…</svg><input /></label>`. Text label inside: `<label class="input"><span class="label">Email</span><input /></label>`. Joined with button: wrap in `<div class="join">`. Supports `type="text|email|password|search|tel|url|number|date|time|datetime-local"`. |

---

### Textarea

| Property | Details |
|----------|---------|
| **Component class** | `textarea` |
| **Parts** | — |
| **Styles** | `textarea-ghost` |
| **Colors** | `textarea-primary`, `textarea-secondary`, `textarea-accent`, `textarea-neutral`, `textarea-info`, `textarea-success`, `textarea-warning`, `textarea-error` |
| **Sizes** | `textarea-xs`, `textarea-sm`, `textarea-md`, `textarea-lg`, `textarea-xl` |
| **Required children** | `<textarea>` element |
| **CSS-only mechanism** | — |
| **Gotchas** | Borders are default in v5. Disable resize: add Tailwind `resize-none`. Wrap in `fieldset` for label + helper text. |

---

### Select

| Property | Details |
|----------|---------|
| **Component class** | `select` |
| **Parts** | — |
| **Styles** | `select-ghost` |
| **Colors** | `select-primary`, `select-secondary`, `select-accent`, `select-neutral`, `select-info`, `select-success`, `select-warning`, `select-error` |
| **Sizes** | `select-xs`, `select-sm`, `select-md`, `select-lg`, `select-xl` |
| **Required children** | `<select class="select">` with `<option>` children |
| **CSS-only mechanism** | — |
| **Gotchas** | Borders are default in v5 — no `select-bordered`. Placeholder: `<option disabled selected>Pick one</option>`. Wrap in `fieldset` for label + helper text. |

---

### Checkbox

| Property | Details |
|----------|---------|
| **Component class** | `checkbox` |
| **Parts** | — |
| **Styles** | — |
| **Colors** | `checkbox-primary`, `checkbox-secondary`, `checkbox-accent`, `checkbox-neutral`, `checkbox-info`, `checkbox-success`, `checkbox-warning`, `checkbox-error` |
| **Sizes** | `checkbox-xs`, `checkbox-sm`, `checkbox-md`, `checkbox-lg`, `checkbox-xl` |
| **Required children** | `<input type="checkbox" class="checkbox">` |
| **CSS-only mechanism** | Native checkbox |
| **Gotchas** | With label: `<label class="label"><input type="checkbox" class="checkbox"> Accept terms</label>`. Indeterminate: set via JS `el.indeterminate = true`. Custom color: use `checkbox-*` color classes on the input. |

---

### Radio

| Property | Details |
|----------|---------|
| **Component class** | `radio` |
| **Parts** | — |
| **Styles** | — |
| **Colors** | `radio-primary`, `radio-secondary`, `radio-accent`, `radio-neutral`, `radio-info`, `radio-success`, `radio-warning`, `radio-error` |
| **Sizes** | `radio-xs`, `radio-sm`, `radio-md`, `radio-lg`, `radio-xl` |
| **Required children** | `<input type="radio" class="radio">` — all in same group share `name` attribute |
| **CSS-only mechanism** | Native radio input |
| **Gotchas** | All radios in a group **must** share the same `name`. With label: `<label class="label"><input type="radio" class="radio"> Option</label>`. |

---

### Toggle

| Property | Details |
|----------|---------|
| **Component class** | `toggle` |
| **Parts** | — |
| **Styles** | — |
| **Colors** | `toggle-primary`, `toggle-secondary`, `toggle-accent`, `toggle-neutral`, `toggle-info`, `toggle-success`, `toggle-warning`, `toggle-error` |
| **Sizes** | `toggle-xs`, `toggle-sm`, `toggle-md`, `toggle-lg`, `toggle-xl` |
| **Required children** | `<input type="checkbox" class="toggle">` |
| **CSS-only mechanism** | Native checkbox styled as switch |
| **Gotchas** | Icons inside: use `[--tglbg:…]` CSS variable. Indeterminate: set via JS. With label: wrap in `<label class="label">` or `fieldset`. Can be combined with `theme-controller`. |

---

### Range

| Property | Details |
|----------|---------|
| **Component class** | `range` |
| **Parts** | — |
| **Styles** | — |
| **Colors** | `range-primary`, `range-secondary`, `range-accent`, `range-neutral`, `range-info`, `range-success`, `range-warning`, `range-error` |
| **Sizes** | `range-xs`, `range-sm`, `range-md`, `range-lg`, `range-xl` |
| **Required children** | `<input type="range" class="range">` with `min`, `max`, `value` attributes |
| **CSS-only mechanism** | Native range input |
| **Gotchas** | Step markers: add `step` attribute + a sibling `<div>` with tick labels. No fill track color by default with custom colors — use component color classes. |

---

### File Input

| Property | Details |
|----------|---------|
| **Component class** | `file-input` |
| **Parts** | — |
| **Styles** | `file-input-ghost` |
| **Colors** | `file-input-primary`, `file-input-secondary`, `file-input-accent`, `file-input-neutral`, `file-input-info`, `file-input-success`, `file-input-warning`, `file-input-error` |
| **Sizes** | `file-input-xs`, `file-input-sm`, `file-input-md`, `file-input-lg`, `file-input-xl` |
| **Required children** | `<input type="file" class="file-input">` |
| **CSS-only mechanism** | — |
| **Gotchas** | Borders are default in v5. Wrap in `fieldset` for label + helper text (`fieldset-label` for "Max 2MB" etc.). |

---

### Rating

| Property | Details |
|----------|---------|
| **Component class** | `rating` |
| **Parts** | — |
| **Styles** | — |
| **Colors** | — (use Tailwind `bg-orange-400`, `bg-green-500` on individual radio inputs) |
| **Sizes** | `rating-xs`, `rating-sm`, `rating-md`, `rating-lg`, `rating-xl` |
| **Modifiers** | `rating-hidden` (on first radio — allows zero/deselect), `rating-half` (half-star support) |
| **Required children** | `<div class="rating">` → `<input type="radio">` per star, each with `class="mask mask-star-2 bg-{color}"` |
| **CSS-only mechanism** | Radio inputs — selecting one deselects others |
| **Gotchas** | Star shape via `mask` classes: `mask-star` (thin), `mask-star-2` (bold), `mask-heart`. Half stars: add `rating-half` to container + use `mask-half-1`/`mask-half-2` (10 inputs for 5 stars). Zero rating: first input gets `rating-hidden` class. Read-only: add `pointer-events-none`. |

---

### Fieldset

| Property | Details |
|----------|---------|
| **Component class** | `fieldset` |
| **Parts** | `fieldset-legend`, `fieldset-label` |
| **Styles** | `fieldset-bg` (adds background), `fieldset-border` (adds border) |
| **Colors** | — |
| **Sizes** | — |
| **Required children** | `<fieldset class="fieldset">` → `<legend class="fieldset-legend">` + form element(s) + optional `<label class="fieldset-label">` |
| **CSS-only mechanism** | — |
| **Gotchas** | **v5 replacement for v4 `form-control`**. `fieldset-legend` replaces `label-text`. `fieldset-label` replaces `label-text-alt` (helper/description text). Can contain multiple inputs or `join` groups. |

---

### Label

| Property | Details |
|----------|---------|
| **Component class** | `label` (standard) or `floating-label` (floating pattern) |
| **Parts** | — |
| **Styles** | — |
| **Colors** | — |
| **Sizes** | — (inherits from paired input size) |
| **Required children** | `<label class="label">Text</label>` or `<label class="floating-label"><span>Label</span><input class="input" /></label>` |
| **CSS-only mechanism** | Floating label uses `:placeholder-shown` and `:focus` pseudo-classes |
| **Gotchas** | Floating label: the `<input>` **must** have a `placeholder` attribute for the float animation to work. Floating label adapts to input sizes (`input-sm`, `input-lg`). Standard `label` can go before or after the input. |

---

### Filter

| Property | Details |
|----------|---------|
| **Component class** | `filter` |
| **Parts** | `filter-reset` |
| **Styles** | — |
| **Colors** | — |
| **Sizes** | — (use `btn-sm`, `btn-xs` etc. on child inputs) |
| **Required children** | `<div class="filter">` (or `<form>`) → `<input type="radio" class="btn" aria-label="Tag">` items + `<input class="filter-reset" aria-label="All">` |
| **CSS-only mechanism** | Radio inputs (single select) or checkbox inputs in a `<form>` (multi-select with reset) |
| **Gotchas** | New in v5. Radio mode: only one active at a time. Checkbox mode: multiple selections, use `<form>` + `<input type="reset" class="filter-reset">` for the "All" button. `aria-label` on inputs provides the visible text. |

---

### Validator

| Property | Details |
|----------|---------|
| **Component class** | `validator` |
| **Parts** | `validator-hint` |
| **Styles** | — |
| **Colors** | — |
| **Sizes** | — |
| **Variant prefix** | `user-invalid:validator` — applies validator styles only after user interaction |
| **Required children** | `<input class="input validator" required>` + sibling `<p class="validator-hint">Error message</p>` |
| **CSS-only mechanism** | Uses `:user-invalid` CSS pseudo-class (triggers after user interacts with input) |
| **Gotchas** | New in v5. Add `validator` class to the input itself. `validator-hint` is a sibling, not a child. Works with: `input`, `select`, `checkbox`, `toggle`. Combine with HTML validation attributes: `required`, `minlength`, `pattern`, `type="email"`, `min`, `max`. The `user-invalid:` variant ensures hints don't show before the user has interacted. |

---

## Feedback Components

### Alert

| Property | Details |
|----------|---------|
| **Component class** | `alert` |
| **Parts** | — |
| **Styles** | `alert-outline`, `alert-dash`, `alert-soft` |
| **Colors** | `alert-info`, `alert-success`, `alert-warning`, `alert-error` |
| **Sizes** | — |
| **Required children** | `<div role="alert" class="alert">` with `<span>` message text. Add `role="alert"` for accessibility. |
| **CSS-only mechanism** | — |
| **Gotchas** | Always include `role="alert"` for screen readers. Icons are optional but recommended — place SVG before the message `<span>`. Title + description: nest a `<div>` with `<h3>` + `<div>` inside the alert. Action buttons: add a `<div>` with buttons at the end. Only 4 semantic colors (info/success/warning/error) — no primary/secondary/accent. |

---

### Loading

| Property | Details |
|----------|---------|
| **Component class** | `loading` |
| **Parts** | — |
| **Styles** | `loading-spinner`, `loading-dots`, `loading-ring`, `loading-ball`, `loading-bars`, `loading-infinity` |
| **Colors** | Uses Tailwind text colors: `text-primary`, `text-secondary`, `text-accent`, `text-neutral`, `text-info`, `text-success`, `text-warning`, `text-error` |
| **Sizes** | `loading-xs`, `loading-sm`, `loading-md`, `loading-lg`, `loading-xl` |
| **Required children** | `<span class="loading loading-spinner"></span>` (self-closing span) |
| **CSS-only mechanism** | CSS animations |
| **Gotchas** | **Must specify a style** — `loading` alone renders nothing. Pick one: `loading-spinner`, `loading-dots`, `loading-ring`, `loading-ball`, `loading-bars`, `loading-infinity`. Color via `text-*` Tailwind utilities (not `loading-primary`). Common in buttons: `<button class="btn"><span class="loading loading-spinner"></span> Loading</button>`. |

---

### Progress

| Property | Details |
|----------|---------|
| **Component class** | `progress` |
| **Parts** | — |
| **Styles** | — |
| **Colors** | `progress-primary`, `progress-secondary`, `progress-accent`, `progress-neutral`, `progress-info`, `progress-success`, `progress-warning`, `progress-error` |
| **Sizes** | — (use Tailwind `w-*` for width) |
| **Required children** | `<progress class="progress" value="40" max="100"></progress>` |
| **CSS-only mechanism** | Native `<progress>` element |
| **Gotchas** | Indeterminate (animated): omit `value` attribute — `<progress class="progress"></progress>`. Width via Tailwind `w-56`, `w-full`, etc. Update via JS: `element.value = 75`. |

---

### Radial Progress

| Property | Details |
|----------|---------|
| **Component class** | `radial-progress` |
| **Parts** | — |
| **Styles** | — |
| **Colors** | Uses Tailwind text colors: `text-primary`, `text-success`, etc. |
| **Sizes** | CSS custom property `--size` (e.g., `8rem`, `12rem`) |
| **Required children** | `<div class="radial-progress" style="--value:70;" role="progressbar">70%</div>` |
| **CSS-only mechanism** | CSS custom properties: `--value` (0–100), `--size`, `--thickness` |
| **Gotchas** | `--value` range: 0–100 integer. Default size/thickness if not specified. Custom: `style="--value:85; --size:8rem; --thickness:4px;"`. Color: `text-primary` on the div. Text inside shows the percentage. Add `role="progressbar"` for accessibility. Update via JS: `el.style.setProperty("--value", n)`. |

---

### Skeleton

| Property | Details |
|----------|---------|
| **Component class** | `skeleton` |
| **Parts** | — |
| **Styles** | — |
| **Colors** | — |
| **Sizes** | — (use Tailwind `h-*`, `w-*`) |
| **Required children** | `<div class="skeleton h-4 w-full"></div>` |
| **CSS-only mechanism** | CSS shimmer animation |
| **Gotchas** | Shape via Tailwind: `rounded-full` for circles, default for rectangles. Size via `h-*` and `w-*`. Compose multiple skeletons to match your actual UI layout. Can contain child content for overlay effect. |

---

### Toast

| Property | Details |
|----------|---------|
| **Component class** | `toast` |
| **Parts** | — |
| **Styles** | — |
| **Colors** | — (uses child `alert` colors) |
| **Sizes** | — |
| **Placement (horizontal)** | `toast-start`, `toast-center`, `toast-end` (default) |
| **Placement (vertical)** | `toast-top`, `toast-middle`, `toast-bottom` (default) |
| **Required children** | `<div class="toast">` → one or more `<div class="alert">` elements |
| **CSS-only mechanism** | Fixed positioning via CSS |
| **Gotchas** | Toast is just a **positioned container** — put `alert` components inside for actual notifications. Combine vertical + horizontal: `toast toast-top toast-center`. Multiple alerts stack vertically. Default position: bottom-right. |

---

### Tooltip

| Property | Details |
|----------|---------|
| **Component class** | `tooltip` |
| **Parts** | `tooltip-content` |
| **Styles** | — |
| **Colors** | `tooltip-primary`, `tooltip-secondary`, `tooltip-accent`, `tooltip-neutral`, `tooltip-info`, `tooltip-success`, `tooltip-warning`, `tooltip-error` |
| **Sizes** | — |
| **Placement** | `tooltip-top`, `tooltip-bottom`, `tooltip-left`, `tooltip-right` |
| **Behavior** | `tooltip-open` (force visible) |
| **Required children** | Wrapper element with trigger content inside |
| **CSS-only mechanism** | Hover / focus visibility |
| **Gotchas** | For simple text, use `data-tip="Message"` on the wrapper. For richer markup, add a child with `class="tooltip-content"`. Wrap the trigger element: `<div class="tooltip" data-tip="Copied"><button class="btn">Copy</button></div>`. Use placement classes on the wrapper, not the child. |

---

### Status

| Property | Details |
|----------|---------|
| **Component class** | `status` |
| **Parts** | — |
| **Styles** | — |
| **Colors** | `status-primary`, `status-secondary`, `status-accent`, `status-neutral`, `status-info`, `status-success`, `status-warning`, `status-error` |
| **Sizes** | `status-xs`, `status-sm`, `status-md`, `status-lg`, `status-xl` |
| **Behavior** | `status-bounce` (bounce animation), `status-ping` (ping/pulse animation) |
| **Required children** | `<span class="status status-success"></span>` (empty span) |
| **CSS-only mechanism** | — |
| **Gotchas** | Renders a small colored dot. Use as `indicator-item` inside an `indicator` for positioned status dots. Two animations available: `status-bounce` and `status-ping`. |

---

## Content Structure Components

### Accordion / Collapse

| Property | Details |
|----------|---------|
| **Component class** | `collapse` |
| **Parts** | `collapse-title`, `collapse-content` |
| **Styles** | `collapse-arrow` (arrow icon), `collapse-plus` (plus/minus icon) |
| **Colors** | — (use Tailwind utilities) |
| **Sizes** | — |
| **Modifiers** | `collapse-open` (force open), `collapse-close` (force close), `collapse-icon-start` (icon on left) |
| **Required children** | `collapse-title` + `collapse-content` |
| **CSS-only mechanism** | Three options: (1) `<details>/<summary>` — recommended, (2) `<input type="checkbox">` — multiple open, (3) `<input type="radio" name="group">` — accordion (only one open) |
| **Gotchas** | `<details>` is simplest but doesn't support accordion (one-at-a-time) — use radio inputs for that. Group with `join`: `<div class="join join-vertical">`. `collapse-arrow` and `collapse-plus` are mutually exclusive. No `accordion` component class — it's `collapse` with radio inputs sharing a `name`. |

---

### Carousel

| Property | Details |
|----------|---------|
| **Component class** | `carousel` |
| **Parts** | `carousel-item` |
| **Styles** | — |
| **Colors** | — |
| **Sizes** | — |
| **Modifiers** | `carousel-center` (snap center), `carousel-end` (snap end), `carousel-vertical` |
| **Required children** | `<div class="carousel">` → `<div class="carousel-item">` children |
| **CSS-only mechanism** | CSS scroll-snap |
| **Gotchas** | Default snaps to start. Full-width items: `carousel-item w-full`. Half-width: `carousel-item w-1/2`. Vertical: `carousel-vertical`. Prev/next buttons: use anchor links `<a href="#slide2">`. Indicator dots: anchor links pointing to `id` on each item. No autoplay built-in — use JS. |

---

### Divider

| Property | Details |
|----------|---------|
| **Component class** | `divider` |
| **Parts** | — |
| **Styles** | — |
| **Colors** | `divider-primary`, `divider-secondary`, `divider-accent`, `divider-neutral`, `divider-info`, `divider-success`, `divider-warning`, `divider-error` |
| **Sizes** | — |
| **Direction** | `divider-horizontal` (for use between flex-row items) |
| **Placement** | `divider-start` (text at start), `divider-end` (text at end) |
| **Required children** | `<div class="divider">` with optional text content |
| **CSS-only mechanism** | — |
| **Gotchas** | Default is vertical (between block elements). For side-by-side layouts use `divider-horizontal`. Empty `<div class="divider"></div>` renders just a line. Responsive: `divider lg:divider-horizontal`. |

---

### Drawer

| Property | Details |
|----------|---------|
| **Component class** | `drawer` |
| **Parts** | `drawer-toggle`, `drawer-content`, `drawer-side`, `drawer-overlay` |
| **Styles** | — |
| **Colors** | — |
| **Sizes** | — |
| **Modifiers** | `drawer-end` (open from right side) |
| **Behavior** | `lg:drawer-open` (always visible on large screens) |
| **Variant prefixes** | `is-drawer-open:*`, `is-drawer-close:*` (conditional styles based on drawer state) |
| **Required children** | `<input type="checkbox" class="drawer-toggle">` + `<div class="drawer-content">` + `<div class="drawer-side">` containing `<label class="drawer-overlay">` + sidebar content |
| **CSS-only mechanism** | Hidden checkbox controls drawer open/close state |
| **Gotchas** | `drawer-toggle` is a **hidden checkbox** — not a button. Toggle button: `<label for="drawer-id" class="btn lg:hidden">☰</label>`. Responsive sidebar: `lg:drawer-open` keeps it visible on desktop. Icon-only collapsed sidebar: `is-drawer-close:w-16 is-drawer-open:w-64`. Always include `drawer-overlay` for the backdrop. |

---

### Footer

| Property | Details |
|----------|---------|
| **Component class** | `footer` |
| **Parts** | `footer-title` |
| **Styles** | — |
| **Colors** | — |
| **Sizes** | — |
| **Direction** | `sm:footer-horizontal` (horizontal on sm+) |
| **Placement** | `footer-center` (centered content) |
| **Required children** | `<footer class="footer">` with `<nav>` sections containing `<h6 class="footer-title">` + links |
| **CSS-only mechanism** | — |
| **Gotchas** | Default layout is vertical (columns stack). Use `sm:footer-horizontal` for side-by-side columns. Centered footer: `footer footer-center`. Copyright: separate `<footer class="footer footer-center">` below. |

---

### Hero

| Property | Details |
|----------|---------|
| **Component class** | `hero` |
| **Parts** | `hero-content`, `hero-overlay` |
| **Styles** | — |
| **Colors** | — |
| **Sizes** | — (use Tailwind `min-h-screen`, `min-h-96`, etc.) |
| **Required children** | `<div class="hero">` → `<div class="hero-content">` with heading + text + CTA |
| **CSS-only mechanism** | — |
| **Gotchas** | Background image: use inline `style="background-image: url(…)"` on `.hero`. Overlay: `hero-overlay` adds a dark semi-transparent layer over the background. Side image: use flex inside `hero-content`: `<div class="hero-content flex-col lg:flex-row">`. |

---

### Indicator

| Property | Details |
|----------|---------|
| **Component class** | `indicator` (container) |
| **Parts** | `indicator-item` (the positioned badge/dot) |
| **Styles** | — |
| **Colors** | — (use child component colors: `badge-primary`, `status-success`, etc.) |
| **Sizes** | — |
| **Placement** | `indicator-top` (default), `indicator-middle`, `indicator-bottom` × `indicator-start`, `indicator-center`, `indicator-end` (default) |
| **Required children** | `<div class="indicator">` → `<span class="indicator-item">` + the target element |
| **CSS-only mechanism** | — |
| **Gotchas** | Default position: top-right. Combine vertical + horizontal: `indicator-item indicator-bottom indicator-start`. Multiple indicators: multiple `indicator-item` elements with different placement classes. Common children: `badge`, `status`, `btn`. |

---

### Join

| Property | Details |
|----------|---------|
| **Component class** | `join` |
| **Parts** | `join-item` |
| **Styles** | — |
| **Colors** | — |
| **Sizes** | — |
| **Direction** | `join-vertical` |
| **Required children** | `<div class="join">` → elements with `class="join-item"` |
| **CSS-only mechanism** | — |
| **Gotchas** | Removes intermediate border-radius — first/last items keep their rounded corners. Mix element types: `input`, `select`, `btn` all work as `join-item`. Radio toggle buttons: `<input type="radio" class="btn join-item" aria-label="A">`. Responsive: `join join-vertical sm:join-horizontal` (note: there is no `join-horizontal` — horizontal is the default). Custom border-radius: override with Tailwind `rounded-*`. |

---

### Mask

| Property | Details |
|----------|---------|
| **Component class** | `mask` |
| **Parts** | — |
| **Styles/Shapes** | `mask-squircle`, `mask-heart`, `mask-hexagon`, `mask-hexagon-2`, `mask-decagon`, `mask-pentagon`, `mask-diamond`, `mask-square`, `mask-circle`, `mask-star`, `mask-star-2`, `mask-triangle`, `mask-triangle-2`, `mask-triangle-3`, `mask-triangle-4` |
| **Colors** | — |
| **Sizes** | — (use Tailwind `w-*`/`h-*`) |
| **Modifiers** | `mask-half-1`, `mask-half-2` (for half-star ratings) |
| **Required children** | `<img class="mask mask-{shape}">` or any element |
| **CSS-only mechanism** | CSS `mask-image` property |
| **Gotchas** | 15 shape options. `mask-star` = thin, `mask-star-2` = bold. `mask-half-1`/`mask-half-2` used exclusively in `rating-half` for half-star inputs. Triangles: `mask-triangle` (up), `mask-triangle-2` (down), `mask-triangle-3` (left), `mask-triangle-4` (right). |

---

### Stack

| Property | Details |
|----------|---------|
| **Component class** | `stack` |
| **Parts** | — |
| **Styles** | — |
| **Colors** | — |
| **Sizes** | — |
| **Direction** | `stack-top` (default), `stack-start`, `stack-end` |
| **Required children** | `<div class="stack">` → 2+ child elements (cards, images, divs) |
| **CSS-only mechanism** | CSS transforms for depth offset |
| **Gotchas** | First child is on top (front). Add `shadow-md` to children for depth effect. Works with cards, images, or any elements. |

---

### Mockup — Browser

| Property | Details |
|----------|---------|
| **Component class** | `mockup-browser` |
| **Parts** | `mockup-browser-toolbar` |
| **Styles** | — |
| **Colors** | — |
| **Sizes** | — |
| **Required children** | `<div class="mockup-browser">` → `<div class="mockup-browser-toolbar"><div class="input">URL</div></div>` + content area |
| **CSS-only mechanism** | — |
| **Gotchas** | Add `border border-base-300` for visible frame. The toolbar `input` div shows the URL bar (not a real input). Content area below toolbar needs its own background. |

---

### Mockup — Code

| Property | Details |
|----------|---------|
| **Component class** | `mockup-code` |
| **Parts** | — |
| **Styles** | — |
| **Colors** | — |
| **Sizes** | — |
| **Required children** | `<div class="mockup-code">` → `<pre data-prefix="$"><code>…</code></pre>` |
| **CSS-only mechanism** | — |
| **Gotchas** | `data-prefix` attribute sets the line prefix character (`$`, `>`, `~`, line numbers, etc.). Color lines with `text-warning`, `text-success`, `text-error` on `<pre>`. Highlighted line: add `bg-warning` or similar. Long lines scroll horizontally. Omit `data-prefix` for no prefix. |

---

### Mockup — Phone

| Property | Details |
|----------|---------|
| **Component class** | `mockup-phone` |
| **Parts** | `mockup-phone-camera`, `mockup-phone-display` |
| **Styles** | — |
| **Colors** | — |
| **Sizes** | — |
| **Required children** | `<div class="mockup-phone">` → `<div class="mockup-phone-camera"></div>` + `<div class="mockup-phone-display">content</div>` |
| **CSS-only mechanism** | — |
| **Gotchas** | The camera notch uses `mockup-phone-camera`. Put the visible screen content directly inside `mockup-phone-display`; `artboard`, `artboard-demo`, and `phone-*` classes are v4-era patterns and should not be used in v5. Custom colors can be applied to the `mockup-phone` container or the display content. |

---

### Mockup — Window

| Property | Details |
|----------|---------|
| **Component class** | `mockup-window` |
| **Parts** | — |
| **Styles** | — |
| **Colors** | — |
| **Sizes** | — |
| **Required children** | `<div class="mockup-window">` → content area div |
| **CSS-only mechanism** | — |
| **Gotchas** | Add `border border-base-300` for visible frame. Traffic-light dots are CSS-generated. Content area needs its own background color. |

---

### Hover 3D

| Property | Details |
|----------|---------|
| **Component class** | `hover-3d` |
| **Parts** | — |
| **Styles** | — |
| **Colors** | — |
| **Sizes** | — |
| **Required children** | `<div class="hover-3d">` → any child element (typically a card) |
| **CSS-only mechanism** | CSS perspective + `:hover` transforms |
| **Gotchas** | New in v5. Pure CSS effect — no JS. Works best on card-sized elements. The child element tilts toward the cursor on hover. |

---

### Hover Gallery

| Property | Details |
|----------|---------|
| **Component class** | `hover-gallery` |
| **Parts** | — |
| **Styles** | — |
| **Colors** | — |
| **Sizes** | — |
| **Required children** | `<div class="hover-gallery">` → `<label>` items each containing `<input type="radio" name="hover-gallery">` + `<img>` + `<span>` |
| **CSS-only mechanism** | Radio inputs + CSS `:checked` / `:hover` |
| **Gotchas** | New in v5. Supports up to 10 items. Radio inputs must share the same `name`. First item should be `checked` by default. Hovering text reveals corresponding image. |

---

### Text Rotate

| Property | Details |
|----------|---------|
| **Component class** | `text-rotate` |
| **Parts** | — |
| **Styles** | — |
| **Colors** | — |
| **Sizes** | — |
| **Required children** | `<span class="text-rotate" style="--n:3;"><span>Word1</span><span>Word2</span><span>Word3</span></span>` |
| **CSS-only mechanism** | CSS animation driven by `--n` custom property |
| **Gotchas** | New in v5. `--n` CSS variable **must** equal the number of `<span>` children. Animation loops automatically. Each `<span>` child is one frame in the rotation. |

---

### FAB (Floating Action Button)

| Property | Details |
|----------|---------|
| **Component class** | `fab` |
| **Parts** | `fab-close`, `fab-main-action` |
| **Styles** | `fab-flower` (radial spread pattern) |
| **Colors** | — (use child `btn` colors) |
| **Sizes** | — (use child `btn` sizes) |
| **Required children** | `<div class="fab">` → `<button class="btn btn-primary btn-circle btn-lg">` |
| **CSS-only mechanism** | Checkbox for speed-dial toggle: `<input type="checkbox">` inside `.fab` |
| **Gotchas** | Fixed position bottom-right by default. Speed dial: add `<input type="checkbox">` + multiple `<button class="btn btn-circle">` children. `fab-close` button shows when speed dial is open. `fab-flower` spreads buttons radially instead of vertically. `fab-main-action` stays visible as the primary action. |

---

## Quick Lookup: All Components at a Glance

| # | Component | Base Class | Has Parts | Has Colors | Has Sizes | CSS-Only Mechanism |
|---|-----------|-----------|-----------|-----------|-----------|-------------------|
| 1 | Navbar | `navbar` | ✅ | — | — | — |
| 2 | Menu | `menu` | ✅ | — | ✅ | `<details>` |
| 3 | Breadcrumbs | `breadcrumbs` | — | — | — | — |
| 4 | Tab | `tabs` + `tab` | ✅ | — | ✅ | Radio inputs |
| 5 | Pagination | `join` + `btn` | ✅ | ✅ | ✅ | Radio inputs |
| 6 | Dock | `dock` | ✅ | — | ✅ | — |
| 7 | Link | `link` | — | ✅ | — | — |
| 8 | Steps | `steps` + `step` | ✅ | ✅ | — | — |
| 9 | Table | `table` | — | — | ✅ | — |
| 10 | Stat | `stats` + `stat` | ✅ | — | — | — |
| 11 | Card | `card` | ✅ | — | ✅ | — |
| 12 | List | `list` | ✅ | — | — | — |
| 13 | Avatar | `avatar` | — | — | — | — |
| 14 | Badge | `badge` | — | ✅ | ✅ | — |
| 15 | Chat | `chat` | ✅ | ✅ | — | — |
| 16 | Countdown | `countdown` | — | — | — | CSS `--value` |
| 17 | Diff | `diff` | ✅ | — | — | CSS resize |
| 18 | Kbd | `kbd` | — | — | ✅ | — |
| 19 | Timeline | `timeline` | ✅ | — | — | — |
| 20 | Calendar | `cally` | — | — | — | Third-party |
| 21 | Button | `btn` | — | ✅ | ✅ | — |
| 22 | Dropdown | `dropdown` | ✅ | — | — | Focus / `<details>` / Popover |
| 23 | Modal | `modal` | ✅ | — | — | `<dialog>` / Checkbox |
| 24 | Swap | `swap` | ✅ | — | — | Checkbox |
| 25 | Theme Controller | `theme-controller` | — | — | — | Checkbox / Radio |
| 26 | Input | `input` | — | ✅ | ✅ | — |
| 27 | Textarea | `textarea` | — | ✅ | ✅ | — |
| 28 | Select | `select` | — | ✅ | ✅ | — |
| 29 | Checkbox | `checkbox` | — | ✅ | ✅ | Native checkbox |
| 30 | Radio | `radio` | — | ✅ | ✅ | Native radio |
| 31 | Toggle | `toggle` | — | ✅ | ✅ | Native checkbox |
| 32 | Range | `range` | — | ✅ | ✅ | Native range |
| 33 | File Input | `file-input` | — | ✅ | ✅ | — |
| 34 | Rating | `rating` | — | — | ✅ | Radio inputs |
| 35 | Fieldset | `fieldset` | ✅ | — | — | — |
| 36 | Label | `label` / `floating-label` | — | — | — | `:placeholder-shown` |
| 37 | Filter | `filter` | ✅ | — | — | Radio / Checkbox |
| 38 | Validator | `validator` | ✅ | — | — | `:user-invalid` |
| 39 | Alert | `alert` | — | ✅ | — | — |
| 40 | Loading | `loading` | — | — | ✅ | CSS animation |
| 41 | Progress | `progress` | — | ✅ | — | Native `<progress>` |
| 42 | Radial Progress | `radial-progress` | — | — | — | CSS `--value` |
| 43 | Skeleton | `skeleton` | — | — | — | CSS animation |
| 44 | Toast | `toast` | — | — | — | CSS fixed positioning |
| 45 | Status | `status` | — | ✅ | ✅ | — |
| 46 | Collapse | `collapse` | ✅ | — | — | `<details>` / Checkbox / Radio |
| 47 | Carousel | `carousel` | ✅ | — | — | CSS scroll-snap |
| 48 | Divider | `divider` | — | ✅ | — | — |
| 49 | Drawer | `drawer` | ✅ | — | — | Checkbox |
| 50 | Footer | `footer` | ✅ | — | — | — |
| 51 | Hero | `hero` | ✅ | — | — | — |
| 52 | Indicator | `indicator` | ✅ | — | — | — |
| 53 | Join | `join` | ✅ | — | — | — |
| 54 | Mask | `mask` | — | — | — | CSS `mask-image` |
| 55 | Stack | `stack` | — | — | — | CSS transforms |
| 56 | Mockup Browser | `mockup-browser` | ✅ | — | — | — |
| 57 | Mockup Code | `mockup-code` | — | — | — | — |
| 58 | Mockup Phone | `mockup-phone` | ✅ | — | — | — |
| 59 | Mockup Window | `mockup-window` | — | — | — | — |
| 60 | Hover 3D | `hover-3d` | — | — | — | CSS perspective |
| 61 | Hover Gallery | `hover-gallery` | — | — | — | Radio + CSS |
| 62 | Text Rotate | `text-rotate` | — | — | — | CSS `--n` animation |
| 63 | FAB | `fab` | ✅ | — | — | Checkbox |
| 64 | Tooltip | `tooltip` | ✅ | ✅ | — | Hover / focus |

---

## Critical Reminders

### ❌ Never Do → ✅ Do Instead

| ❌ Never | ✅ Instead |
|---------|-----------|
| `bg-red-500` for errors | `bg-error` or `btn-error` |
| `dark:bg-gray-800` | daisyUI colors auto-adapt to themes |
| `text-white` on colored buttons | Use `-content` variants or omit (auto) |
| Invent classes like `btn-rounded` | Check this catalog first |
| `form-control` (v4) | `fieldset` (v5) |
| `input-bordered` (v4) | Borders are default in v5 |
| `label-text` (v4) | `fieldset-legend` (v5) |
| `label-text-alt` (v4) | `fieldset-label` (v5) |
| `tabs-lifted` (v4) | `tabs-lift` (v5) |
| `bordered` on card (v4) | `card-border` (v5) |
| Skip `card-body` in a card | Always include `card-body` |
| `loading` without a style class | Always add `loading-spinner`, `loading-dots`, etc. |
| `loading-primary` | Use `text-primary` for loading color |


## Steering experiences — learned from real agent usage

### When to use this file vs. MCP tool

**Problem:** Agent reads the full component-catalog.md (1100+ lines) into context when a quick MCP call to `components` would suffice.

**Fix:** Use this decision guide:

| Situation | Use | Why |
|---|---|---|
| Need to validate 1–3 class names | MCP `components` tool | Faster, lighter, always current |
| Need to browse all available components | This file (component-catalog.md) | Full inventory in one read |
| Need to find the right example key | MCP `components` tool | Example keys are listed in the response |
| Need to compare modifier options | MCP `components` tool | Structured response with all options |
| Offline or MCP server unavailable | This file (component-catalog.md) | Static reference that's always available |
| Need cross-component pattern guidance | This file + relevant pattern reference | Patterns span multiple components |

### Component-to-category mapping

Quick lookup for which MCP category to use:

| Component | `components` (reference) | `component-examples` (markup) |
|---|---|---|
| Simple (badge, divider, loading) | Usually sufficient | Only if specific variant needed |
| Medium (card, alert, stat) | For class validation | For complex variants |
| Complex (drawer, navbar, table) | For class validation | Almost always needed |
| Layout (hero, footer) | For modifier check | For responsive patterns |
