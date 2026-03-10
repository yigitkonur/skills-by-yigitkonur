# Common Mistakes

> The 10 most common agent mistakes when using daisyUI Blueprint, with ❌ wrong and ✅ correct examples.
>
> See also: `references/component-catalog.md` for valid class names, `references/tool-api-reference.md` for correct tool syntax.

---

## Mistake 1: Array Syntax for Snippets

The #1 cause of "empty response" from the Snippets tool.

### ❌ Wrong

```json
{"snippets": ["components/button", "components/card"]}
```

```json
{"components": ["button", "card"]}
```

### ✅ Correct

```json
{"components": {"button": true, "card": true}}
```

**Why it matters:** The MCP tool uses **nested object syntax only**. Arrays silently fail or return nothing. Every key must have `true` as its value.

**How to prevent:** Always use this pattern: `{"category": {"name": true}}`. Never use arrays for any parameter.

---

## Mistake 2: Inventing Class Names

Agents generate plausible-sounding class names that don't exist in daisyUI.

### ❌ Wrong

```html
<button class="btn btn-rounded btn-medium btn-blue">Click me</button>
<div class="card card-header">
  <h2>Title</h2>
</div>
<input class="input-field input-large" />
<li class="nav-item nav-link">Home</li>
```

### ✅ Correct

```html
<button class="btn btn-primary btn-md">Click me</button>
<div class="card bg-base-100">
  <div class="card-body">
    <h2 class="card-title">Title</h2>
  </div>
</div>
<input class="input input-lg" />
<li><a>Home</a></li>  <!-- inside a <ul class="menu"> -->
```

**Common fabricated classes and their real equivalents:**

| ❌ Fabricated | ✅ Real | Notes |
|-------------|--------|-------|
| `btn-rounded` | (none needed) | Buttons have border-radius by default |
| `btn-medium` | `btn-md` or omit | `md` is default, no suffix needed |
| `btn-blue` | `btn-primary` or `btn-info` | Use semantic color names |
| `btn-red` | `btn-error` | Use semantic color names |
| `btn-green` | `btn-success` | Use semantic color names |
| `card-header` | `card-title` | Goes inside `card-body` |
| `input-field` | `input` | Just `input` |
| `input-large` | `input-lg` | Use standard size suffixes |
| `nav-item` | `<li>` in `menu` | Menu items are plain `<li>` |
| `nav-link` | `<a>` in `menu > li` | Links in menu are plain `<a>` |
| `text-muted` | `text-base-content/60` | Use opacity modifier |
| `container` | `max-w-7xl mx-auto` | No container class in daisyUI |

**How to prevent:** Fetch the component reference first: `{"components": {"button": true}}`. The class table shows every valid class.

---

## Mistake 3: Tailwind Colors on Themed Elements

Using hardcoded Tailwind color utilities instead of semantic daisyUI colors.

### ❌ Wrong

```html
<button class="bg-blue-500 text-white hover:bg-blue-600 px-4 py-2 rounded">
  Submit
</button>
<div class="bg-red-100 text-red-800 border border-red-200 p-4 rounded">
  Error message
</div>
<div class="bg-white shadow-md rounded-lg p-6">
  Card content
</div>
```

### ✅ Correct

```html
<button class="btn btn-primary">Submit</button>
<div class="alert alert-error">Error message</div>
<div class="card bg-base-100 shadow-sm">
  <div class="card-body">Card content</div>
</div>
```

**Why it matters:** Semantic colors (`primary`, `error`, `base-100`) auto-adapt when themes change. Hardcoded colors like `blue-500` stay the same in every theme, breaking dark mode and theme switching.

**Exception:** Decorative non-semantic elements (gradients, illustrations) can use Tailwind colors.

**How to prevent:** For any interactive/structural element, always use daisyUI component classes or semantic color utilities.

---

## Mistake 4: Using `dark:` Prefix

Manually handling dark mode instead of letting daisyUI's theme system do it.

### ❌ Wrong

```html
<div class="bg-white dark:bg-gray-800">
  <h1 class="text-gray-900 dark:text-white">Title</h1>
  <p class="text-gray-600 dark:text-gray-300">Description</p>
  <div class="border-gray-200 dark:border-gray-700">Divider</div>
</div>
```

### ✅ Correct

```html
<div class="bg-base-100">
  <h1 class="text-base-content">Title</h1>
  <p class="text-base-content/70">Description</p>
  <div class="border-base-300">Divider</div>
</div>
```

**Why it matters:** daisyUI's `base-100`, `base-200`, `base-300`, and `base-content` automatically flip between light and dark values based on the active theme. `dark:` prefix creates conflicts and doubles your markup.

**How to prevent:** Never write `dark:` when using daisyUI colors. If you need `dark:`, it's a sign you should use a semantic color instead.

---

## Mistake 5: Building Components from Scratch with Tailwind

Recreating standard UI components with raw Tailwind instead of using daisyUI.

### ❌ Wrong

```html
<div class="rounded-lg shadow-md overflow-hidden bg-white">
  <img src="photo.jpg" class="w-full h-48 object-cover" />
  <div class="p-6">
    <h3 class="text-lg font-semibold text-gray-900 mb-2">Product</h3>
    <p class="text-gray-600 text-sm mb-4">Description of the product</p>
    <div class="flex justify-end">
      <button class="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500">
        Buy Now
      </button>
    </div>
  </div>
</div>
```

### ✅ Correct

```html
<div class="card bg-base-100 shadow-sm">
  <figure><img src="photo.jpg" alt="Product" /></figure>
  <div class="card-body">
    <h2 class="card-title">Product</h2>
    <p>Description of the product</p>
    <div class="card-actions justify-end">
      <button class="btn btn-primary btn-sm">Buy Now</button>
    </div>
  </div>
</div>
```

**Why it matters:** daisyUI components provide:
- **Theme support** — colors adapt automatically
- **Size consistency** — matches other components
- **Accessibility** — focus states, contrast ratios
- **Less code** — 60% fewer classes
- **Maintainability** — change theme, everything updates

**How to prevent:** Before writing raw Tailwind, check if daisyUI has a component for it. Fetch the reference: `{"components": {"card": true}}`.

---

## Mistake 6: Forgetting Required Parts

Components without their required children break visually.

### ❌ Wrong — Card without card-body

```html
<div class="card bg-base-100 shadow-sm">
  <h2>Title</h2>
  <p>Content has no padding and broken layout</p>
</div>
```

### ✅ Correct

```html
<div class="card bg-base-100 shadow-sm">
  <div class="card-body">
    <h2 class="card-title">Title</h2>
    <p>Content with proper padding and flex layout</p>
  </div>
</div>
```

### ❌ Wrong — Modal without modal-box

```html
<dialog class="modal">
  <h3>Title</h3>
  <p>Content escapes the modal boundaries</p>
</dialog>
```

### ✅ Correct

```html
<dialog id="my_modal" class="modal">
  <div class="modal-box">
    <h3 class="text-lg font-bold">Title</h3>
    <p class="py-4">Content properly constrained</p>
    <div class="modal-action">
      <form method="dialog"><button class="btn">Close</button></form>
    </div>
  </div>
</dialog>
```

### ❌ Wrong — Drawer missing parts

```html
<div class="drawer">
  <div>Main content</div>
  <div>Sidebar</div>
</div>
```

### ✅ Correct — All 4 parts present

```html
<div class="drawer lg:drawer-open">
  <input id="drawer" type="checkbox" class="drawer-toggle" />
  <div class="drawer-content">Main content</div>
  <div class="drawer-side">
    <label for="drawer" class="drawer-overlay"></label>
    <ul class="menu bg-base-200 min-h-full w-80 p-4">
      <li><a>Item</a></li>
    </ul>
  </div>
</div>
```

**All required parts:**

| Component | Required children |
|-----------|-------------------|
| `card` | `card-body` |
| `modal` | `modal-box` + `modal-action` |
| `drawer` | `drawer-toggle` + `drawer-content` + `drawer-side` + `drawer-overlay` |
| `navbar` | `navbar-start` / `navbar-center` / `navbar-end` |
| `fieldset` | `fieldset-legend` |
| `collapse` | `collapse-title` + `collapse-content` |
| `stat` | `stat-title` + `stat-value` |

**How to prevent:** Fetch the component reference first. The syntax template shows the required structure.

---

## Mistake 7: JavaScript for CSS-Only Components

Adding JavaScript for interactions that daisyUI handles with pure CSS.

### ❌ Wrong — JS drawer toggle

```html
<button onclick="toggleSidebar()">☰</button>
<div id="sidebar" class="hidden lg:block w-64 bg-gray-100">
  Sidebar content
</div>
<script>
function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('hidden');
}
</script>
```

### ✅ Correct — CSS-only drawer

```html
<div class="drawer lg:drawer-open">
  <input id="sidebar" type="checkbox" class="drawer-toggle" />
  <div class="drawer-content">
    <label for="sidebar" class="btn btn-ghost lg:hidden">☰</label>
    <!-- page content -->
  </div>
  <div class="drawer-side">
    <label for="sidebar" class="drawer-overlay"></label>
    <ul class="menu bg-base-200 min-h-full w-80 p-4">
      <li><a>Item</a></li>
    </ul>
  </div>
</div>
```

**CSS-only mechanism for each component:**

| Component | ❌ Don't use JS | ✅ CSS mechanism |
|-----------|----------------|-----------------|
| Drawer | onclick toggle class | Hidden checkbox + label |
| Modal | onclick show/hide | `<dialog>` + `showModal()` |
| Dropdown | onclick toggle class | `<details>` + `<summary>` |
| Tabs | onclick switch active | Radio inputs |
| Accordion | onclick toggle | Radio inputs |
| Collapse | onclick toggle | Checkbox or `<details>` |
| Swap | onclick toggle | Checkbox |
| Theme switch | onclick set theme | Input with `data-toggle-theme` |

**Note:** `<dialog>.showModal()` is the one acceptable minimal JS call — it's a native browser API, not custom JS.

**How to prevent:** Always fetch the component example to see the CSS-only pattern.

---

## Mistake 8: Fetching Too Many Examples

Requesting all examples for a component when only 1–2 are needed.

### ❌ Wrong — All 18 button examples

```json
{
  "component-examples": {
    "button.button": true,
    "button.button-sizes": true,
    "button.button-with-icon": true,
    "button.button-with-loading-spinner": true,
    "button.buttons-colors": true,
    "button.outline-buttons": true,
    "button.dash-buttons": true,
    "button.soft-buttons": true,
    "button.active-buttons": true,
    "button.disabled-buttons": true,
    "button.buttons-ghost-and-button-link": true,
    "button.square-button-and-circle-button": true,
    "button.button-block": true,
    "button.wide-button": true,
    "button.responsive-button": true,
    "button.neutral-button-with-outline-or-dash-style": true,
    "button.buttons-with-any-html-tags-like-checkbox-radio-etc": true,
    "button.login-with-social-media-auth-buttons": true
  }
}
```

### ✅ Correct — Component reference + targeted example

```json
{
  "components": { "button": true },
  "component-examples": { "button.button-with-icon": true }
}
```

**Why it matters:** Each example is 100–300 tokens. Fetching all 18 button examples wastes ~3K+ tokens on code you won't use. The component reference (200–500 tokens) gives you all class names and the example list to choose from.

**Strategy:**
1. Fetch component reference to see options
2. Pick the 1–3 examples closest to the user's need
3. Adapt the example code to match exact requirements

**How to prevent:** Always start with `components` to see the class list and example names, then fetch only what you need.

---

## Mistake 9: Ignoring Responsive Variants

Creating layouts that only work on one screen size.

### ❌ Wrong — Non-responsive

```html
<!-- Sidebar always visible — breaks mobile -->
<div class="drawer drawer-open">...</div>

<!-- Menu always horizontal — overflows on mobile -->
<ul class="menu menu-horizontal">...</ul>

<!-- 3-column grid at all sizes — too narrow on mobile -->
<div class="grid grid-cols-3 gap-4">...</div>
```

### ✅ Correct — Responsive

```html
<!-- Sidebar: off-canvas on mobile, persistent on desktop -->
<div class="drawer lg:drawer-open">...</div>

<!-- Menu: vertical on mobile, horizontal on desktop -->
<ul class="menu menu-vertical lg:menu-horizontal">...</ul>

<!-- Grid: 1 col mobile → 2 col tablet → 3 col desktop -->
<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">...</div>
```

**Essential responsive patterns:**

| Pattern | Classes |
|---------|---------|
| Sidebar toggle | `drawer lg:drawer-open` |
| Hamburger button | `btn lg:hidden` |
| Desktop-only nav | `hidden lg:flex` |
| Stats reflow | `stats-vertical lg:stats-horizontal` |
| Menu direction | `menu-vertical lg:menu-horizontal` |
| Card side | `card sm:card-side` |
| Grid columns | `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3` |
| Mobile bottom nav | `dock lg:hidden` |
| Steps direction | `steps-vertical lg:steps-horizontal` |

**How to prevent:** Every layout component should have at least one responsive breakpoint. Ask: "What happens on mobile?"

---

## Mistake 10: Using daisyUI v4 Syntax

Using deprecated v4 patterns instead of current v5 syntax.

### ❌ Wrong — v4 patterns

```html
<!-- v4 form grouping -->
<div class="form-control">
  <label class="label">
    <span class="label-text">Email</span>
  </label>
  <input type="email" class="input input-bordered" />
  <label class="label">
    <span class="label-text-alt">Helper text</span>
  </label>
</div>

<!-- v4 bordered input -->
<input class="input input-bordered" />

<!-- v4 tab-lifted -->
<div class="tabs tabs-lifted">...</div>

<!-- v4 bordered card -->
<div class="card bordered">...</div>
```

### ✅ Correct — v5 patterns

```html
<!-- v5 fieldset replaces form-control -->
<fieldset class="fieldset">
  <legend class="fieldset-legend">Email</legend>
  <input type="email" class="input" placeholder="you@example.com" />
  <p class="fieldset-label">Helper text</p>
</fieldset>

<!-- v5 inputs have borders by default -->
<input class="input" />

<!-- v5 tab-lift (not tab-lifted) -->
<div class="tabs tab-lift">...</div>

<!-- v5 card-border (not bordered) -->
<div class="card card-border">...</div>
```

**Complete v4 → v5 migration table:**

| v4 (deprecated) | v5 (current) | Notes |
|-----------------|-------------|-------|
| `form-control` | `fieldset` | New semantic wrapper |
| `label` + `label-text` | `fieldset-legend` | Simpler structure |
| `label-text-alt` | `fieldset-label` | Helper text below input |
| `input-bordered` | `input` | Borders are default in v5 |
| `select-bordered` | `select` | Borders are default in v5 |
| `textarea-bordered` | `textarea` | Borders are default in v5 |
| `tab-lifted` | `tab-lift` | Renamed |
| `bordered` (on card) | `card-border` | Renamed |
| HSL theme colors | oklch theme colors | Format change |
| `tailwind.config.js` themes | `@plugin "daisyui"` in CSS | Configuration moved to CSS |

**New v5-only components (don't exist in v4):**

`fieldset`, `validator`, `filter`, `dock`, `list`, `floating-label`, `hover-3d`, `hover-gallery`, `text-rotate`

**New v5-only variant prefixes:**

`is-drawer-open:`, `is-drawer-close:`, `user-invalid:`

**How to prevent:** If you're unsure about a class name, fetch the component reference. v4 class names won't appear in the v5 reference.
