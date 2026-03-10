# Bootstrap to daisyUI Conversion Workflow

> Systematically migrate Bootstrap projects to daisyUI 5 + Tailwind CSS 4.

---

## Overview

Bootstrap and daisyUI share a similar component philosophy (semantic class names), making migration straightforward. The key differences:
- **Bootstrap** uses its own utility system → **Tailwind CSS** utilities
- **Bootstrap** components use `data-bs-*` attributes → **daisyUI** uses CSS-only or checkbox/radio patterns
- **Bootstrap** grid is 12-column flex → **Tailwind** grid/flex utilities
- **Bootstrap JS** plugins → **daisyUI** CSS-only behavior (no JS needed for most)

---

## Migration Strategy

### Recommended Order
1. **Layout & Grid** — Convert container/row/col to Tailwind
2. **Typography** — Map heading/text classes
3. **Components** — Swap Bootstrap components for daisyUI
4. **Utilities** — Replace Bootstrap utilities with Tailwind
5. **JavaScript** — Remove Bootstrap JS, use CSS-only daisyUI patterns
6. **Theme** — Map Bootstrap variables to daisyUI theme

---

## Layout & Grid Conversion

### Container
```html
<!-- Bootstrap -->
<div class="container">
<div class="container-fluid">
<div class="container-lg">

<!-- daisyUI / Tailwind -->
<div class="max-w-7xl mx-auto px-4">      <!-- container -->
<div class="w-full px-4">                  <!-- container-fluid -->
<div class="max-w-screen-lg mx-auto px-4"> <!-- container-lg -->
```

### Grid System
```html
<!-- Bootstrap: 12-column grid -->
<div class="row">
  <div class="col-md-4">Sidebar</div>
  <div class="col-md-8">Content</div>
</div>

<!-- Tailwind: Flexible grid -->
<div class="grid grid-cols-1 md:grid-cols-12 gap-4">
  <div class="md:col-span-4">Sidebar</div>
  <div class="md:col-span-8">Content</div>
</div>

<!-- Or simpler with fractional widths -->
<div class="flex flex-col md:flex-row gap-4">
  <div class="md:w-1/3">Sidebar</div>
  <div class="md:w-2/3">Content</div>
</div>
```

### Grid Class Mapping

| Bootstrap | Tailwind |
|-----------|----------|
| `row` | `grid grid-cols-12 gap-4` or `flex flex-wrap gap-4` |
| `col` | `col-span-1` (in grid) or `flex-1` |
| `col-1` → `col-12` | `col-span-1` → `col-span-12` |
| `col-md-6` | `md:col-span-6` |
| `col-lg-4` | `lg:col-span-4` |
| `col-auto` | `w-auto` |
| `offset-md-2` | `md:col-start-3` |
| `g-3` (gutter) | `gap-3` or `gap-4` |
| `gy-3` | `gap-y-3` |
| `gx-3` | `gap-x-3` |

### Responsive Breakpoints

| Bootstrap | Tailwind | Min-width |
|-----------|----------|-----------|
| (none / xs) | (none) | 0px |
| `sm` | `sm:` | 576px → 640px |
| `md` | `md:` | 768px |
| `lg` | `lg:` | 992px → 1024px |
| `xl` | `xl:` | 1200px → 1280px |
| `xxl` | `2xl:` | 1400px → 1536px |

> Note: Exact pixel breakpoints differ slightly. Test responsiveness after conversion.

---

## Component-by-Component Migration

### Button

```html
<!-- Bootstrap -->
<button class="btn btn-primary">Click</button>
<button class="btn btn-outline-primary">Outline</button>
<button class="btn btn-primary btn-lg">Large</button>
<button class="btn btn-primary btn-sm">Small</button>
<button class="btn btn-link">Link</button>
<a class="btn btn-primary disabled">Disabled</a>

<!-- daisyUI -->
<button class="btn btn-primary">Click</button>
<button class="btn btn-outline btn-primary">Outline</button>
<button class="btn btn-primary btn-lg">Large</button>
<button class="btn btn-primary btn-sm">Small</button>
<button class="btn btn-link">Link</button>
<button class="btn btn-primary btn-disabled">Disabled</button>
```

| Bootstrap Button | daisyUI Button |
|-----------------|----------------|
| `btn btn-primary` | `btn btn-primary` |
| `btn btn-secondary` | `btn btn-secondary` |
| `btn btn-success` | `btn btn-success` |
| `btn btn-danger` | `btn btn-error` |
| `btn btn-warning` | `btn btn-warning` |
| `btn btn-info` | `btn btn-info` |
| `btn btn-light` | `btn btn-ghost` |
| `btn btn-dark` | `btn btn-neutral` |
| `btn btn-outline-*` | `btn btn-outline btn-*` |
| `btn-lg` | `btn-lg` |
| `btn-sm` | `btn-sm` |
| `btn-block` | `btn btn-block` |
| `btn-close` | Custom or × character |
| `btn-group` | `join` |

### Card

```html
<!-- Bootstrap -->
<div class="card">
  <img src="..." class="card-img-top" alt="...">
  <div class="card-body">
    <h5 class="card-title">Title</h5>
    <p class="card-text">Text</p>
    <a href="#" class="btn btn-primary">Go</a>
  </div>
</div>

<!-- daisyUI -->
<div class="card bg-base-100 shadow">
  <figure><img src="..." alt="..." /></figure>
  <div class="card-body">
    <h2 class="card-title">Title</h2>
    <p>Text</p>
    <div class="card-actions justify-end">
      <button class="btn btn-primary">Go</button>
    </div>
  </div>
</div>
```

| Bootstrap Card | daisyUI Card |
|---------------|-------------|
| `card` | `card bg-base-100 shadow` |
| `card-body` | `card-body` |
| `card-title` | `card-title` |
| `card-text` | `<p>` (no special class needed) |
| `card-img-top` | `<figure>` wrapping `<img>` |
| `card-img-bottom` | `<figure>` after `card-body` |
| `card-header` | Part of `card-body` or custom div |
| `card-footer` | `card-actions` |
| `card-group` | Tailwind `grid` or `flex` |

### Navbar / Navigation

```html
<!-- Bootstrap -->
<nav class="navbar navbar-expand-lg navbar-dark bg-dark">
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
<div class="navbar bg-neutral text-neutral-content">
  <div class="navbar-start">
    <div class="dropdown">
      <div tabindex="0" role="button" class="btn btn-ghost lg:hidden">☰</div>
      <ul tabindex="0" class="menu menu-sm dropdown-content bg-base-100 rounded-box mt-3 w-52 p-2 shadow text-base-content">
        <li><a>Home</a></li>
        <li><a>About</a></li>
      </ul>
    </div>
    <a class="btn btn-ghost text-xl">Brand</a>
  </div>
  <div class="navbar-center hidden lg:flex">
    <ul class="menu menu-horizontal px-1">
      <li><a class="active">Home</a></li>
      <li><a>About</a></li>
    </ul>
  </div>
  <div class="navbar-end">
    <!-- end items -->
  </div>
</div>
```

### Modal

```html
<!-- Bootstrap (requires JS) -->
<button data-bs-toggle="modal" data-bs-target="#myModal">Open</button>
<div class="modal fade" id="myModal">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">Title</h5>
        <button class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body">Content</div>
      <div class="modal-footer">
        <button class="btn btn-primary">Save</button>
      </div>
    </div>
  </div>
</div>

<!-- daisyUI (CSS-only with <dialog>) -->
<button class="btn" onclick="my_modal.showModal()">Open</button>
<dialog id="my_modal" class="modal">
  <div class="modal-box">
    <h3 class="text-lg font-bold">Title</h3>
    <p class="py-4">Content</p>
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

### Alert

```html
<!-- Bootstrap -->
<div class="alert alert-success">Success!</div>
<div class="alert alert-danger">Error!</div>
<div class="alert alert-warning">Warning!</div>
<div class="alert alert-info">Info!</div>

<!-- daisyUI -->
<div role="alert" class="alert alert-success">Success!</div>
<div role="alert" class="alert alert-error">Error!</div>
<div role="alert" class="alert alert-warning">Warning!</div>
<div role="alert" class="alert alert-info">Info!</div>
```

| Bootstrap Alert | daisyUI Alert |
|-----------------|---------------|
| `alert-primary` | `alert alert-info` (closest) |
| `alert-secondary` | `alert` (default/neutral) |
| `alert-success` | `alert alert-success` |
| `alert-danger` | `alert alert-error` |
| `alert-warning` | `alert alert-warning` |
| `alert-info` | `alert alert-info` |
| `alert-dismissible` | Add close button manually |

### Badge

```html
<!-- Bootstrap -->
<span class="badge bg-primary">New</span>
<span class="badge rounded-pill bg-danger">9</span>

<!-- daisyUI -->
<span class="badge badge-primary">New</span>
<span class="badge badge-error">9</span>
```

| Bootstrap Badge | daisyUI Badge |
|-----------------|---------------|
| `badge bg-primary` | `badge badge-primary` |
| `badge bg-secondary` | `badge badge-secondary` |
| `badge bg-success` | `badge badge-success` |
| `badge bg-danger` | `badge badge-error` |
| `badge rounded-pill` | `badge` (already rounded) |

### Table

```html
<!-- Bootstrap -->
<table class="table table-striped table-hover table-bordered">
  <thead class="table-dark">
    <tr><th>Name</th><th>Email</th></tr>
  </thead>
  <tbody>
    <tr><td>John</td><td>john@example.com</td></tr>
  </tbody>
</table>

<!-- daisyUI -->
<div class="overflow-x-auto">
  <table class="table table-zebra">
    <thead>
      <tr><th>Name</th><th>Email</th></tr>
    </thead>
    <tbody>
      <tr><td>John</td><td>john@example.com</td></tr>
    </tbody>
  </table>
</div>
```

| Bootstrap Table | daisyUI Table |
|-----------------|---------------|
| `table` | `table` |
| `table-striped` | `table-zebra` |
| `table-hover` | Add `hover` class to `<tr>` |
| `table-bordered` | Add border utilities |
| `table-sm` | `table-xs` or `table-sm` |
| `table-responsive` | Wrap in `<div class="overflow-x-auto">` |
| `table-dark` | Use theme or `bg-neutral text-neutral-content` |

### Form / Input

```html
<!-- Bootstrap -->
<div class="mb-3">
  <label for="email" class="form-label">Email</label>
  <input type="email" class="form-control" id="email" placeholder="email@example.com">
  <div class="form-text">Helper text</div>
</div>
<div class="form-check">
  <input class="form-check-input" type="checkbox" id="check1">
  <label class="form-check-label" for="check1">Check me</label>
</div>
<div class="form-check form-switch">
  <input class="form-check-input" type="checkbox" id="switch1">
  <label class="form-check-label" for="switch1">Toggle</label>
</div>
<select class="form-select">
  <option>Option 1</option>
</select>

<!-- daisyUI -->
<fieldset class="fieldset">
  <legend class="fieldset-legend">Email</legend>
  <input type="email" class="input" placeholder="email@example.com" />
  <p class="fieldset-label">Helper text</p>
</fieldset>
<fieldset class="fieldset">
  <label class="label">
    <input type="checkbox" class="checkbox" />
    Check me
  </label>
</fieldset>
<fieldset class="fieldset">
  <label class="label">
    <input type="checkbox" class="toggle" />
    Toggle
  </label>
</fieldset>
<select class="select">
  <option>Option 1</option>
</select>
```

| Bootstrap Form | daisyUI Form |
|----------------|-------------|
| `form-control` | `input` |
| `form-label` | `fieldset-legend` or `label` |
| `form-text` | `fieldset-label` |
| `form-select` | `select` |
| `form-check-input` (checkbox) | `checkbox` |
| `form-check-input` (radio) | `radio` |
| `form-check form-switch` | `toggle` |
| `input-group` | `join` |
| `form-floating` | `label` with floating-label pattern |
| `form-range` | `range` |

### Tabs / Nav Tabs

```html
<!-- Bootstrap -->
<ul class="nav nav-tabs">
  <li class="nav-item">
    <a class="nav-link active" data-bs-toggle="tab" href="#tab1">Tab 1</a>
  </li>
  <li class="nav-item">
    <a class="nav-link" data-bs-toggle="tab" href="#tab2">Tab 2</a>
  </li>
</ul>
<div class="tab-content">
  <div class="tab-pane active" id="tab1">Content 1</div>
  <div class="tab-pane" id="tab2">Content 2</div>
</div>

<!-- daisyUI (CSS-only with radio inputs) -->
<div role="tablist" class="tabs tabs-lift">
  <input type="radio" name="my_tabs" role="tab" class="tab" aria-label="Tab 1" checked />
  <div role="tabpanel" class="tab-content bg-base-100 border-base-300 p-6">
    Content 1
  </div>
  <input type="radio" name="my_tabs" role="tab" class="tab" aria-label="Tab 2" />
  <div role="tabpanel" class="tab-content bg-base-100 border-base-300 p-6">
    Content 2
  </div>
</div>
```

### Accordion / Collapse

```html
<!-- Bootstrap (requires JS) -->
<div class="accordion" id="acc">
  <div class="accordion-item">
    <h2 class="accordion-header">
      <button class="accordion-button" data-bs-toggle="collapse" data-bs-target="#c1">
        Item 1
      </button>
    </h2>
    <div id="c1" class="accordion-collapse collapse show" data-bs-parent="#acc">
      <div class="accordion-body">Content 1</div>
    </div>
  </div>
</div>

<!-- daisyUI (CSS-only) -->
<div class="join join-vertical w-full">
  <div class="collapse collapse-arrow join-item border-base-300 border">
    <input type="radio" name="my-accordion" checked />
    <div class="collapse-title font-semibold">Item 1</div>
    <div class="collapse-content">Content 1</div>
  </div>
  <div class="collapse collapse-arrow join-item border-base-300 border">
    <input type="radio" name="my-accordion" />
    <div class="collapse-title font-semibold">Item 2</div>
    <div class="collapse-content">Content 2</div>
  </div>
</div>
```

### Pagination

```html
<!-- Bootstrap -->
<nav>
  <ul class="pagination">
    <li class="page-item"><a class="page-link" href="#">«</a></li>
    <li class="page-item active"><a class="page-link" href="#">1</a></li>
    <li class="page-item"><a class="page-link" href="#">2</a></li>
    <li class="page-item"><a class="page-link" href="#">»</a></li>
  </ul>
</nav>

<!-- daisyUI -->
<div class="join">
  <button class="join-item btn">«</button>
  <button class="join-item btn btn-active">1</button>
  <button class="join-item btn">2</button>
  <button class="join-item btn">»</button>
</div>
```

### Tooltip & Popover

```html
<!-- Bootstrap (requires JS) -->
<button data-bs-toggle="tooltip" title="Tooltip text">Hover me</button>

<!-- daisyUI / Tailwind (CSS-only) -->
<div class="tooltip" data-tip="Tooltip text">
  <button class="btn">Hover me</button>
</div>
```

### Progress Bar

```html
<!-- Bootstrap -->
<div class="progress">
  <div class="progress-bar bg-success" style="width: 75%">75%</div>
</div>

<!-- daisyUI -->
<progress class="progress progress-success w-full" value="75" max="100"></progress>
```

### Breadcrumb

```html
<!-- Bootstrap -->
<nav>
  <ol class="breadcrumb">
    <li class="breadcrumb-item"><a href="#">Home</a></li>
    <li class="breadcrumb-item active">Current</li>
  </ol>
</nav>

<!-- daisyUI -->
<div class="breadcrumbs text-sm">
  <ul>
    <li><a>Home</a></li>
    <li>Current</li>
  </ul>
</div>
```

---

## Utility Class Mapping

| Bootstrap Utility | Tailwind Equivalent |
|-------------------|-------------------|
| `d-flex` | `flex` |
| `d-none` | `hidden` |
| `d-block` | `block` |
| `d-inline` | `inline` |
| `d-grid` | `grid` |
| `d-md-flex` | `md:flex` |
| `justify-content-center` | `justify-center` |
| `justify-content-between` | `justify-between` |
| `align-items-center` | `items-center` |
| `align-self-end` | `self-end` |
| `flex-wrap` | `flex-wrap` |
| `flex-column` | `flex-col` |
| `order-1` | `order-1` |
| `m-3` | `m-3` (similar but different scale) |
| `p-3` | `p-3` |
| `mt-3` | `mt-3` |
| `mx-auto` | `mx-auto` |
| `text-center` | `text-center` |
| `text-start` | `text-left` |
| `text-end` | `text-right` |
| `fw-bold` | `font-bold` |
| `fw-light` | `font-light` |
| `fs-1` → `fs-6` | `text-4xl` → `text-base` |
| `text-muted` | `text-base-content/60` |
| `text-primary` | `text-primary` |
| `bg-primary` | `bg-primary` |
| `bg-light` | `bg-base-200` |
| `bg-dark` | `bg-neutral` |
| `border` | `border` |
| `border-0` | `border-0` |
| `rounded` | `rounded-lg` |
| `rounded-circle` | `rounded-full` |
| `shadow` | `shadow` |
| `shadow-sm` | `shadow-sm` |
| `shadow-lg` | `shadow-lg` |
| `w-100` | `w-full` |
| `h-100` | `h-full` |
| `overflow-auto` | `overflow-auto` |
| `position-relative` | `relative` |
| `position-absolute` | `absolute` |
| `position-fixed` | `fixed` |
| `position-sticky` | `sticky` |
| `top-0` | `top-0` |
| `visually-hidden` | `sr-only` |
| `float-start` | `float-left` |
| `float-end` | `float-right` |
| `gap-3` | `gap-3` |

### Spacing Scale Comparison

Bootstrap uses a 0-5 scale, Tailwind uses a more granular system:

| Bootstrap | Value | Tailwind |
|-----------|-------|----------|
| `*-0` | 0 | `*-0` |
| `*-1` | 0.25rem (4px) | `*-1` |
| `*-2` | 0.5rem (8px) | `*-2` |
| `*-3` | 1rem (16px) | `*-4` |
| `*-4` | 1.5rem (24px) | `*-6` |
| `*-5` | 3rem (48px) | `*-12` |

---

## JavaScript Removal Guide

Most Bootstrap components require JavaScript. daisyUI uses CSS-only patterns:

| Bootstrap JS Feature | daisyUI Alternative |
|---------------------|-------------------|
| Modal toggle (`data-bs-toggle="modal"`) | `<dialog>` element with `showModal()` or checkbox pattern |
| Collapse (`data-bs-toggle="collapse"`) | `<details>/<summary>` or `collapse` with checkbox |
| Dropdown (`data-bs-toggle="dropdown"`) | CSS-only `dropdown` (focus-based) or `<details>` |
| Tab switching (`data-bs-toggle="tab"`) | Radio input `tabs` pattern |
| Tooltip (`data-bs-toggle="tooltip"`) | CSS `tooltip` class with `data-tip` |
| Carousel (`data-bs-ride="carousel"`) | CSS `carousel` with scroll-snap |
| Offcanvas (`data-bs-toggle="offcanvas"`) | `drawer` with checkbox toggle |
| Toast | `toast` with CSS positioning |
| Accordion | `collapse` with radio inputs (for exclusive open) |

**What still needs JS in daisyUI:**
- Theme switching (use `theme-controller` with radio/checkbox)
- Complex carousel auto-play (add minimal JS)
- Form validation (use native HTML5 validation + `validator` component)

---

## Theme Mapping

### Bootstrap CSS Variables → daisyUI Theme

```css
/* Bootstrap */
:root {
  --bs-primary: #0d6efd;
  --bs-secondary: #6c757d;
  --bs-success: #198754;
  --bs-danger: #dc3545;
  --bs-warning: #ffc107;
  --bs-info: #0dcaf0;
  --bs-light: #f8f9fa;
  --bs-dark: #212529;
}

/* daisyUI custom theme */
@plugin "daisyui/theme" {
  --name: "my-bootstrap-theme";
  --color-primary: #0d6efd;
  --color-primary-content: #ffffff;
  --color-secondary: #6c757d;
  --color-secondary-content: #ffffff;
  --color-accent: #0dcaf0;
  --color-accent-content: #000000;
  --color-neutral: #212529;
  --color-neutral-content: #ffffff;
  --color-base-100: #ffffff;
  --color-base-200: #f8f9fa;
  --color-base-300: #e9ecef;
  --color-base-content: #212529;
  --color-info: #0dcaf0;
  --color-info-content: #000000;
  --color-success: #198754;
  --color-success-content: #ffffff;
  --color-warning: #ffc107;
  --color-warning-content: #000000;
  --color-error: #dc3545;
  --color-error-content: #ffffff;
  --radius-selector: 0.25rem;
  --radius-field: 0.375rem;
  --radius-box: 0.5rem;
  --size-selector: 0.25rem;
  --size-field: 0.25rem;
  --border: 1px;
  --depth: 1;
  --noise: 0;
}
```

---

## Migration Checklist

- [ ] Replace Bootstrap CDN/imports with Tailwind CSS + daisyUI
- [ ] Convert grid layout (`row`/`col-*`) to Tailwind grid/flex
- [ ] Convert all Bootstrap utility classes to Tailwind
- [ ] Replace each Bootstrap component with daisyUI equivalent
- [ ] Remove all `data-bs-*` attributes
- [ ] Remove Bootstrap JavaScript bundle
- [ ] Map Bootstrap theme colors to daisyUI custom theme
- [ ] Test responsive behavior at all breakpoints
- [ ] Test all interactive elements (modals, dropdowns, tabs, accordions)
- [ ] Verify form validation still works
- [ ] Check accessibility (ARIA attributes, keyboard navigation)
