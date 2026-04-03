# Bootstrap to daisyUI Conversion Prompt

> Built-in prompt for the **daisyui-blueprint** MCP server.
> Converts Bootstrap 5 HTML into semantic daisyUI 5 + Tailwind CSS 4 code.

---

## Trigger

User provides Bootstrap HTML and asks:

- *"Convert this Bootstrap code to daisyUI"*
- *"Migrate this from Bootstrap to daisyUI"*
- *"Rewrite this using daisyUI components"*

---

## System Prompt

```
You are a Bootstrap-to-daisyUI migration specialist. Given Bootstrap 5 HTML,
you will rewrite it using daisyUI 5 component classes on Tailwind CSS 4.
Preserve the visual intent and behavior. Use the class mapping reference and
structural rules below.
```

---

## Comprehensive Class Mapping

### Buttons

| Bootstrap 5 | daisyUI 5 | Notes |
|-------------|-----------|-------|
| `btn btn-primary` | `btn btn-primary` | Same naming, different styling engine |
| `btn btn-secondary` | `btn btn-secondary` | |
| `btn btn-success` | `btn btn-success` | |
| `btn btn-danger` | `btn btn-error` | ⚠️ `danger` → `error` |
| `btn btn-warning` | `btn btn-warning` | |
| `btn btn-info` | `btn btn-info` | |
| `btn btn-dark` | `btn btn-neutral` | ⚠️ `dark` → `neutral` |
| `btn btn-light` | `btn btn-ghost` | Closest equivalent |
| `btn btn-link` | `btn btn-link` | |
| `btn btn-outline-primary` | `btn btn-outline btn-primary` | Separate modifier class |
| `btn btn-sm` | `btn btn-sm` | Same |
| `btn btn-lg` | `btn btn-lg` | Same |
| `btn-group` | `join` | Different component name |
| `btn-close` | Custom or `btn btn-ghost btn-sm btn-circle` | No direct equivalent |

### Cards

| Bootstrap 5 | daisyUI 5 | Notes |
|-------------|-----------|-------|
| `card` | `card bg-base-100 shadow-xl` | Add background + shadow explicitly |
| `card-body` | `card-body` | Same |
| `card-title` | `card-title` | Same (use inside `card-body`) |
| `card-text` | `<p>` (plain element) | No special class needed |
| `card-header` | No direct equivalent | Use `div` with `bg-base-200 p-4` inside card |
| `card-footer` | `card-actions` | Different naming, goes inside `card-body` |
| `card-img-top` | `<figure><img /></figure>` | Use `<figure>` wrapper before `card-body` |
| `card-img-overlay` | `card image-full` | Built-in image overlay variant |
| `card-group` | Tailwind `grid` or `flex` | No card-group component |

**Structural difference:**

```html
<!-- Bootstrap -->
<div class="card">
  <img src="..." class="card-img-top" />
  <div class="card-body">
    <h5 class="card-title">Title</h5>
    <p class="card-text">Text</p>
  </div>
</div>

<!-- daisyUI -->
<div class="card bg-base-100 shadow-xl">
  <figure><img src="..." alt="Title" /></figure>
  <div class="card-body">
    <h2 class="card-title">Title</h2>
    <p>Text</p>
    <div class="card-actions justify-end">
      <button class="btn btn-primary">Action</button>
    </div>
  </div>
</div>
```

### Modals

| Bootstrap 5 | daisyUI 5 | Notes |
|-------------|-----------|-------|
| `modal` | `modal` | Same name, very different structure |
| `modal-dialog` | `modal-box` | Content container |
| `modal-content` | (not needed) | `modal-box` handles this |
| `modal-header` | `<h3>` inside `modal-box` | No separate wrapper |
| `modal-body` | Content inside `modal-box` | Just direct children |
| `modal-footer` | `modal-action` | Action button area |
| `modal-backdrop` | `modal-backdrop` | Same concept |
| `data-bs-toggle="modal"` | `<dialog>` + `showModal()` | Uses native `<dialog>` element |
| `data-bs-dismiss="modal"` | `<form method="dialog"><button>` | Native dialog close |

**Structural difference:**

```html
<!-- Bootstrap -->
<button data-bs-toggle="modal" data-bs-target="#myModal">Open</button>
<div class="modal" id="myModal">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">Title</h5>
        <button class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body">Content here</div>
      <div class="modal-footer">
        <button class="btn btn-primary">Save</button>
      </div>
    </div>
  </div>
</div>

<!-- daisyUI -->
<button class="btn" onclick="my_modal.showModal()">Open</button>
<dialog id="my_modal" class="modal">
  <div class="modal-box">
    <h3 class="font-bold text-lg">Title</h3>
    <p class="py-4">Content here</p>
    <div class="modal-action">
      <form method="dialog">
        <button class="btn btn-primary">Save</button>
        <button class="btn">Close</button>
      </form>
    </div>
  </div>
  <form method="dialog" class="modal-backdrop">
    <button>close</button>
  </form>
</dialog>
```

### Navbar

| Bootstrap 5 | daisyUI 5 | Notes |
|-------------|-----------|-------|
| `navbar` | `navbar` | Same name |
| `navbar-brand` | `navbar-start` > link/text | Different structure |
| `navbar-nav` | `menu menu-horizontal` | Uses menu component |
| `nav-item` | `<li>` inside `menu` | Plain list item |
| `nav-link` | `<a>` inside `<li>` | Plain anchor |
| `navbar-toggler` | `btn btn-ghost lg:hidden` + drawer | Uses drawer pattern |
| `navbar-collapse` | `hidden lg:flex` | Tailwind responsive |
| `navbar-expand-lg` | Tailwind responsive classes | No single class |

**Structural difference:**

```html
<!-- Bootstrap -->
<nav class="navbar navbar-expand-lg navbar-light bg-light">
  <div class="container-fluid">
    <a class="navbar-brand" href="#">Brand</a>
    <button class="navbar-toggler" data-bs-toggle="collapse" data-bs-target="#nav">
      <span class="navbar-toggler-icon"></span>
    </button>
    <div class="collapse navbar-collapse" id="nav">
      <ul class="navbar-nav">
        <li class="nav-item"><a class="nav-link active" href="#">Home</a></li>
        <li class="nav-item"><a class="nav-link" href="#">About</a></li>
      </ul>
    </div>
  </div>
</nav>

<!-- daisyUI -->
<div class="navbar bg-base-100 shadow-sm">
  <div class="navbar-start">
    <div class="dropdown">
      <div tabindex="0" role="button" class="btn btn-ghost lg:hidden">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none"
          viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M4 6h16M4 12h8m-8 6h16" />
        </svg>
      </div>
      <ul tabindex="0"
        class="menu menu-sm dropdown-content bg-base-100 rounded-box z-1 mt-3 w-52 p-2 shadow">
        <li><a class="menu-active">Home</a></li>
        <li><a>About</a></li>
      </ul>
    </div>
    <a class="btn btn-ghost text-xl">Brand</a>
  </div>
  <div class="navbar-center hidden lg:flex">
    <ul class="menu menu-horizontal px-1">
      <li><a class="menu-active">Home</a></li>
      <li><a>About</a></li>
    </ul>
  </div>
  <div class="navbar-end">
    <a class="btn btn-primary">Get Started</a>
  </div>
</div>
```

### Forms

| Bootstrap 5 | daisyUI 5 | Notes |
|-------------|-----------|-------|
| `form-control` | `input` / `select` / `textarea` | Component-specific classes |
| `form-label` | `fieldset-legend` or `label` | Part of `fieldset` component |
| `form-select` | `select` | Different class name |
| `form-check` | `checkbox` / `radio` / `toggle` | Component-specific |
| `form-check-input` | `checkbox` / `radio` / `toggle` | Same element, different class |
| `form-check-label` | `label` | |
| `form-floating` | `label` with `floating` | daisyUI floating label component |
| `form-text` | `fieldset-label` | Helper text under inputs |
| `input-group` | `join` | Group inputs together |
| `input-group-text` | `join-item` or `label` inside input | |
| `form-range` | `range` | |
| `form-switch` | `toggle` | |
| `was-validated` | `validator` | Built-in validation component |

**Structural difference:**

```html
<!-- Bootstrap -->
<div class="mb-3">
  <label for="email" class="form-label">Email</label>
  <input type="email" class="form-control" id="email" placeholder="name@example.com">
  <div class="form-text">We'll never share your email.</div>
</div>

<!-- daisyUI -->
<fieldset class="fieldset">
  <legend class="fieldset-legend">Email</legend>
  <input type="email" class="input" placeholder="name@example.com" />
  <p class="fieldset-label">We'll never share your email.</p>
</fieldset>
```

### Alerts

| Bootstrap 5 | daisyUI 5 | Notes |
|-------------|-----------|-------|
| `alert alert-primary` | `alert alert-info` | ⚠️ No `primary` alert; use `info` |
| `alert alert-secondary` | `alert` | Default/neutral |
| `alert alert-success` | `alert alert-success` | Same |
| `alert alert-danger` | `alert alert-error` | ⚠️ `danger` → `error` |
| `alert alert-warning` | `alert alert-warning` | Same |
| `alert alert-info` | `alert alert-info` | Same |
| `alert alert-dark` | `alert` + dark bg utility | No direct equivalent |
| `alert alert-dismissible` | Custom (add close button) | No built-in dismiss |
| `alert-heading` | `<h3>` or `<strong>` | No special class |

### Badges

| Bootstrap 5 | daisyUI 5 | Notes |
|-------------|-----------|-------|
| `badge bg-primary` | `badge badge-primary` | Different prefix pattern |
| `badge bg-danger` | `badge badge-error` | ⚠️ `danger` → `error` |
| `badge rounded-pill` | `badge` (already rounded) | No extra class needed |
| `badge bg-secondary` | `badge badge-secondary` | |

### Layout & Grid

| Bootstrap 5 | daisyUI / Tailwind | Notes |
|-------------|-------------------|-------|
| `container` | `container mx-auto px-4` | Tailwind utility |
| `container-fluid` | `w-full px-4` | Tailwind utility |
| `row` | `grid grid-cols-12 gap-4` or `flex` | Tailwind grid |
| `col` | `col-span-*` | Tailwind grid columns |
| `col-md-6` | `md:col-span-6` | Responsive prefix |
| `col-lg-4` | `lg:col-span-4` | Responsive prefix |
| `col-auto` | `col-auto` or flexbox | Tailwind equivalent |
| `g-3` (gap) | `gap-3` | Tailwind gap (in 0.25rem units) |
| `offset-md-2` | `md:col-start-3` | Grid column start |

**Grid conversion pattern:**

```html
<!-- Bootstrap -->
<div class="container">
  <div class="row">
    <div class="col-md-4">A</div>
    <div class="col-md-4">B</div>
    <div class="col-md-4">C</div>
  </div>
</div>

<!-- Tailwind (daisyUI doesn't have a grid component) -->
<div class="container mx-auto px-4">
  <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
    <div>A</div>
    <div>B</div>
    <div>C</div>
  </div>
</div>
```

### Utilities

| Bootstrap 5 | Tailwind CSS 4 | Notes |
|-------------|----------------|-------|
| `d-flex` | `flex` | |
| `d-none` | `hidden` | |
| `d-block` | `block` | |
| `d-md-flex` | `md:flex` | Responsive prefix |
| `justify-content-center` | `justify-center` | |
| `justify-content-between` | `justify-between` | |
| `align-items-center` | `items-center` | |
| `text-center` | `text-center` | Same |
| `text-start` | `text-left` | |
| `text-end` | `text-right` | |
| `fw-bold` | `font-bold` | |
| `fs-1` through `fs-6` | `text-5xl` through `text-base` | Different scale |
| `mt-3` | `mt-3` | Same scale in Tailwind (0.75rem) |
| `p-3` | `p-3` | Same scale |
| `mx-auto` | `mx-auto` | Same |
| `w-100` | `w-full` | |
| `h-100` | `h-full` | |
| `rounded` | `rounded` | Same |
| `rounded-circle` | `rounded-full` | |
| `shadow` | `shadow` | Same |
| `shadow-lg` | `shadow-lg` | Same |
| `bg-primary` | `bg-primary` | daisyUI semantic color |
| `text-white` | `text-primary-content` | Use daisyUI content colors |
| `border` | `border` | Same |
| `overflow-auto` | `overflow-auto` | Same |
| `position-relative` | `relative` | |
| `position-absolute` | `absolute` | |
| `visually-hidden` | `sr-only` | Screen reader only |

### Other Components

| Bootstrap 5 | daisyUI 5 | Notes |
|-------------|-----------|-------|
| `accordion` | `accordion` (join + collapse) | Different mechanism |
| `breadcrumb` | `breadcrumbs` | Plural in daisyUI |
| `carousel` | `carousel` | Different markup |
| `collapse` | `collapse` | Similar concept |
| `dropdown-toggle` + `dropdown-menu` | `dropdown` + `dropdown-content` | Different structure |
| `list-group` | `menu` or `list` | Closest equivalents |
| `nav-tabs` | `tabs` (role="tablist") | Different structure |
| `pagination` | `join` with `btn` elements | Or pagination radio inputs |
| `progress` | `progress` | Similar |
| `spinner-border` | `loading loading-spinner` | |
| `spinner-grow` | `loading loading-ball` | |
| `table` | `table` | Very similar |
| `table-striped` | `table-zebra` | Different name |
| `table-hover` | `hover:bg-base-300` on `<tr>` | Use a semantic hover fill in v5 |
| `toast` | `toast` | |
| `tooltip` | `tooltip` with `data-tip` or `tooltip-content` | daisyUI has a tooltip component |

---

## Key Structural Differences

### 1. No JavaScript Dependencies

Bootstrap relies on `bootstrap.js` for modals, dropdowns, tooltips, collapses, etc.
daisyUI achieves interactivity through:

- **Native `<dialog>` element** for modals
- **CSS `:checked` state** for toggles, drawers, accordions
- **`<details>/<summary>`** for dropdowns and collapses
- **CSS-only hover** for dropdown menus
- **Popover API** for advanced dropdowns

Remove all `data-bs-*` attributes and `bootstrap.js` imports.

### 2. Theme System vs Utility Colors

Bootstrap uses static utility classes (`bg-primary`, `text-white`).
daisyUI uses **semantic color roles** that adapt to the active theme:

```css
/* Bootstrap: fixed colors */
.bg-primary { background-color: #0d6efd; }

/* daisyUI: theme-aware colors */
.bg-primary { background-color: oklch(var(--color-primary)); }
```

Always prefer daisyUI semantic colors (`primary`, `secondary`, `accent`, `neutral`, `base-100/200/300`, `info`, `success`, `warning`, `error`) over hardcoded values.

### 3. Component Part Nesting

daisyUI components often require specific nesting:

```
card → card-body → card-title / card-actions
modal → modal-box → modal-action
navbar → navbar-start / navbar-center / navbar-end
drawer → drawer-toggle + drawer-content + drawer-side
```

Bootstrap is more flat. Always check the daisyUI component reference for correct nesting.

### 4. Responsive Strategy

| Bootstrap | daisyUI + Tailwind |
|-----------|-------------------|
| `col-md-6` (12-column grid) | `md:col-span-6` (12-col) or `md:w-1/2` (flex) |
| `d-md-none` | `md:hidden` |
| `navbar-expand-lg` | `lg:flex hidden` on nav items |
| Breakpoints: sm/md/lg/xl/xxl | sm/md/lg/xl/2xl |

---

## Things with No Direct Equivalent

| Bootstrap Feature | Recommended Alternative |
|------------------|------------------------|
| Scrollspy | Intersection Observer API (JavaScript) |
| Popovers | Popover API or custom HTML/CSS (tooltip only covers hover/focus hints) |
| Offcanvas | daisyUI `drawer` component |
| Toasts (auto-dismiss) | daisyUI `toast` + JavaScript timer |
| `btn-close` | `btn btn-sm btn-circle btn-ghost` with × text |
| Stretched link | Custom CSS `::after` pseudo-element |
| `visually-hidden-focusable` | `sr-only focus:not-sr-only` |
| `ratio` (aspect ratios) | Tailwind `aspect-video`, `aspect-square` |
| `clearfix` | Not needed (use flexbox/grid) |
| Sass variables | CSS custom properties via `@plugin "daisyui/theme"` |

---

## Migration Checklist

### Before You Start

- [ ] Identify all Bootstrap components used in the project
- [ ] List all `data-bs-*` attributes that need replacement
- [ ] Note any Bootstrap JavaScript plugins in use
- [ ] Check for Bootstrap Sass variable overrides

### CSS / HTML Changes

- [ ] Replace Bootstrap CDN/import with Tailwind CSS + daisyUI
- [ ] Convert the 12-column grid to Tailwind grid/flex
- [ ] Map all Bootstrap component classes to daisyUI equivalents (tables above)
- [ ] Convert utility classes (spacing, display, flex, text)
- [ ] Replace `danger` with `error` everywhere
- [ ] Replace `dark` with `neutral` for button/badge variants
- [ ] Update `form-control` to component-specific classes (`input`, `select`, `textarea`)
- [ ] Convert `btn-group` to `join`
- [ ] Wrap card images in `<figure>` elements

### JavaScript Changes

- [ ] Remove `bootstrap.js` and `@popperjs/core` imports
- [ ] Replace `data-bs-toggle="modal"` with `dialog.showModal()`
- [ ] Replace `data-bs-toggle="collapse"` with checkbox/details pattern
- [ ] Replace `data-bs-toggle="dropdown"` with daisyUI dropdown structure
- [ ] Remove all `data-bs-dismiss` attributes
- [ ] Replace tooltip initialization with CSS-only approach

### Theme Setup

- [ ] Choose a built-in daisyUI theme or create a custom one
- [ ] Add `data-theme="your-theme"` to the `<html>` element
- [ ] Convert any Bootstrap Sass color overrides to daisyUI CSS variables
- [ ] Replace hardcoded colors with semantic color classes

### Testing

- [ ] Verify visual consistency across all pages
- [ ] Test responsive behavior at all breakpoints
- [ ] Test all interactive elements (modals, dropdowns, accordions)
- [ ] Validate form behavior and validation states
- [ ] Check dark mode support if applicable

---

## Complete Migration Example

### Before (Bootstrap 5)

```html
<!DOCTYPE html>
<html>
<head>
  <link href="bootstrap.min.css" rel="stylesheet">
</head>
<body>
  <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
    <div class="container">
      <a class="navbar-brand" href="#">MyApp</a>
      <button class="navbar-toggler" data-bs-toggle="collapse"
        data-bs-target="#navContent">
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="collapse navbar-collapse" id="navContent">
        <ul class="navbar-nav ms-auto">
          <li class="nav-item"><a class="nav-link active" href="#">Home</a></li>
          <li class="nav-item"><a class="nav-link" href="#">About</a></li>
        </ul>
      </div>
    </div>
  </nav>

  <div class="container mt-5">
    <div class="row g-4">
      <div class="col-md-4">
        <div class="card">
          <img src="photo.jpg" class="card-img-top">
          <div class="card-body">
            <h5 class="card-title">Card Title</h5>
            <p class="card-text">Some text here.</p>
            <a href="#" class="btn btn-primary">Go</a>
          </div>
        </div>
      </div>
    </div>

    <div class="alert alert-danger mt-4" role="alert">
      <strong>Error!</strong> Something went wrong.
    </div>
  </div>

  <script src="bootstrap.bundle.min.js"></script>
</body>
</html>
```

### After (daisyUI 5 + Tailwind CSS 4)

```html
<!DOCTYPE html>
<html data-theme="dark">
<head>
  <link href="output.css" rel="stylesheet">
</head>
<body>
  <div class="navbar bg-neutral text-neutral-content">
    <div class="navbar-start">
      <div class="dropdown">
        <div tabindex="0" role="button" class="btn btn-ghost lg:hidden">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none"
            viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M4 6h16M4 12h8m-8 6h16" />
          </svg>
        </div>
        <ul tabindex="0"
          class="menu menu-sm dropdown-content bg-base-100 rounded-box z-1 mt-3 w-52 p-2 shadow">
          <li><a class="menu-active">Home</a></li>
          <li><a>About</a></li>
        </ul>
      </div>
      <a class="btn btn-ghost text-xl">MyApp</a>
    </div>
    <div class="navbar-center hidden lg:flex">
      <ul class="menu menu-horizontal px-1">
        <li><a class="menu-active">Home</a></li>
        <li><a>About</a></li>
      </ul>
    </div>
  </div>

  <div class="container mx-auto px-4 mt-10">
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="card bg-base-100 shadow-xl">
        <figure><img src="photo.jpg" alt="Card image" /></figure>
        <div class="card-body">
          <h2 class="card-title">Card Title</h2>
          <p>Some text here.</p>
          <div class="card-actions justify-end">
            <a href="#" class="btn btn-primary">Go</a>
          </div>
        </div>
      </div>
    </div>

    <div role="alert" class="alert alert-error mt-4">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 shrink-0 stroke-current"
        fill="none" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <span><strong>Error!</strong> Something went wrong.</span>
    </div>
  </div>

  <!-- No JavaScript needed for these components -->
</body>
</html>
```
