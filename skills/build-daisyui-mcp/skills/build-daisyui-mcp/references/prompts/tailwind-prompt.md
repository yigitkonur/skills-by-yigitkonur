# Tailwind to daisyUI Optimization Prompt

> Built-in prompt for the **daisyui-blueprint** MCP server.
> Identifies verbose Tailwind CSS utility patterns and replaces them with semantic daisyUI component classes.

---

## Trigger

User provides raw Tailwind CSS HTML and asks:

- *"Convert this Tailwind code to use daisyUI components"*
- *"Optimize this with daisyUI"*
- *"Replace these Tailwind utilities with daisyUI classes"*

---

## System Prompt

```
You are a Tailwind-to-daisyUI optimization specialist. Given HTML that uses
raw Tailwind CSS utility classes, identify patterns that correspond to daisyUI
components and replace them. Only replace where daisyUI has a clear semantic
equivalent — do not force conversions. Tailwind utilities for layout, spacing,
and one-off styling should remain as-is.
```

---

## Core Rule

> **Replace only where daisyUI has a semantic equivalent. Don't force it.**

daisyUI adds semantic component classes *on top of* Tailwind. The goal is to:
1. **Reduce verbose utility chains** that describe a common UI pattern
2. **Gain theme support** (colors, radius, depth change with theme)
3. **Improve readability** of the HTML

Tailwind utilities for layout (`grid`, `flex`, `gap`), spacing (`p-*`, `m-*`), and one-off styling should stay.

---

## Pattern Recognition Reference

### Buttons

**Before — Tailwind:**
```html
<button class="px-4 py-2 rounded-lg bg-blue-500 text-white font-medium
  hover:bg-blue-600 active:bg-blue-700 focus:outline-none focus:ring-2
  focus:ring-blue-300 transition-colors">
  Click me
</button>
```

**After — daisyUI:**
```html
<button class="btn btn-primary">Click me</button>
```

**Detection pattern:** Any element with padding + background color + text color + rounded + hover state that functions as a clickable action.

| Tailwind Pattern | daisyUI Equivalent |
|-----------------|-------------------|
| `px-4 py-2 bg-blue-500 text-white rounded` | `btn btn-primary` |
| `px-4 py-2 bg-gray-500 text-white rounded` | `btn btn-neutral` |
| `px-4 py-2 bg-green-500 text-white rounded` | `btn btn-success` |
| `px-4 py-2 bg-red-500 text-white rounded` | `btn btn-error` |
| `px-4 py-2 border border-blue-500 text-blue-500 rounded` | `btn btn-outline btn-primary` |
| `px-4 py-2 bg-transparent text-blue-500 hover:bg-blue-50` | `btn btn-ghost` |
| `px-2 py-1 text-sm bg-blue-500 text-white rounded` | `btn btn-primary btn-sm` |
| `px-6 py-3 text-lg bg-blue-500 text-white rounded` | `btn btn-primary btn-lg` |
| `px-4 py-2 bg-blue-500 text-white rounded-full` | `btn btn-primary btn-circle` or `btn btn-primary rounded-full` |
| `inline-flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded` | `btn btn-primary` (icons via child elements) |

---

### Cards

**Before — Tailwind:**
```html
<div class="rounded-xl border border-gray-200 bg-white shadow-md overflow-hidden">
  <img src="photo.jpg" class="w-full h-48 object-cover" />
  <div class="p-6">
    <h3 class="text-lg font-semibold mb-2">Title</h3>
    <p class="text-gray-600 mb-4">Description text goes here.</p>
    <button class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
      Action
    </button>
  </div>
</div>
```

**After — daisyUI:**
```html
<div class="card bg-base-100 shadow-md">
  <figure><img src="photo.jpg" alt="Title" /></figure>
  <div class="card-body">
    <h3 class="card-title">Title</h3>
    <p>Description text goes here.</p>
    <div class="card-actions justify-end">
      <button class="btn btn-primary">Action</button>
    </div>
  </div>
</div>
```

**Detection pattern:** Rounded container with shadow + padding + heading + text content + optional image.

---

### Navbar / Header

**Before — Tailwind:**
```html
<header class="flex items-center justify-between px-6 py-4 bg-white shadow">
  <a href="/" class="text-xl font-bold">Logo</a>
  <nav class="hidden md:flex gap-6">
    <a href="#" class="text-gray-700 hover:text-blue-500">Home</a>
    <a href="#" class="text-gray-700 hover:text-blue-500">About</a>
    <a href="#" class="text-gray-700 hover:text-blue-500">Contact</a>
  </nav>
  <button class="px-4 py-2 bg-blue-500 text-white rounded">Sign Up</button>
</header>
```

**After — daisyUI:**
```html
<div class="navbar bg-base-100 shadow">
  <div class="navbar-start">
    <a class="btn btn-ghost text-xl">Logo</a>
  </div>
  <div class="navbar-center hidden md:flex">
    <ul class="menu menu-horizontal px-1">
      <li><a>Home</a></li>
      <li><a>About</a></li>
      <li><a>Contact</a></li>
    </ul>
  </div>
  <div class="navbar-end">
    <button class="btn btn-primary">Sign Up</button>
  </div>
</div>
```

**Detection pattern:** Flex container at page top with logo + navigation links + actions.

---

### Alerts / Notifications

**Before — Tailwind:**
```html
<div class="flex items-center gap-3 p-4 rounded-lg bg-red-50 border border-red-200 text-red-700">
  <svg class="w-5 h-5" ...>...</svg>
  <span>Something went wrong. Please try again.</span>
</div>
```

**After — daisyUI:**
```html
<div role="alert" class="alert alert-error">
  <svg class="w-5 h-5" ...>...</svg>
  <span>Something went wrong. Please try again.</span>
</div>
```

**Detection pattern:** Colored banner with icon + text, often with border and background tint.

| Tailwind Color Tone | daisyUI Alert |
|---------------------|---------------|
| `bg-red-50 text-red-700 border-red-200` | `alert alert-error` |
| `bg-green-50 text-green-700 border-green-200` | `alert alert-success` |
| `bg-yellow-50 text-yellow-700 border-yellow-200` | `alert alert-warning` |
| `bg-blue-50 text-blue-700 border-blue-200` | `alert alert-info` |

---

### Badges / Tags

**Before — Tailwind:**
```html
<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs
  font-medium bg-blue-100 text-blue-800">
  New
</span>
```

**After — daisyUI:**
```html
<span class="badge badge-primary">New</span>
```

**Detection pattern:** Small inline element with background tint, rounded, small text.

| Tailwind Pattern | daisyUI Badge |
|-----------------|---------------|
| `bg-blue-100 text-blue-800 rounded-full text-xs px-2.5 py-0.5` | `badge badge-primary` |
| `bg-gray-100 text-gray-800 ...` | `badge badge-ghost` |
| `bg-green-100 text-green-800 ...` | `badge badge-success` |
| `bg-red-100 text-red-800 ...` | `badge badge-error` |
| `border border-blue-500 text-blue-500 ...` | `badge badge-outline badge-primary` |

---

### Modal / Dialog

**Before — Tailwind:**
```html
<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
  <div class="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
    <h3 class="text-lg font-semibold mb-4">Confirm Action</h3>
    <p class="text-gray-600 mb-6">Are you sure you want to proceed?</p>
    <div class="flex justify-end gap-3">
      <button class="px-4 py-2 rounded bg-gray-200 hover:bg-gray-300">Cancel</button>
      <button class="px-4 py-2 rounded bg-blue-500 text-white hover:bg-blue-600">Confirm</button>
    </div>
  </div>
</div>
```

**After — daisyUI:**
```html
<dialog id="confirm_modal" class="modal modal-open">
  <div class="modal-box">
    <h3 class="font-bold text-lg">Confirm Action</h3>
    <p class="py-4">Are you sure you want to proceed?</p>
    <div class="modal-action">
      <form method="dialog">
        <button class="btn">Cancel</button>
        <button class="btn btn-primary">Confirm</button>
      </form>
    </div>
  </div>
  <form method="dialog" class="modal-backdrop">
    <button>close</button>
  </form>
</dialog>
```

**Detection pattern:** Fixed overlay + centered white box + title + content + action buttons.

---

### Toggle / Switch

**Before — Tailwind:**
```html
<label class="relative inline-flex items-center cursor-pointer">
  <input type="checkbox" class="sr-only peer">
  <div class="w-11 h-6 bg-gray-200 rounded-full peer
    peer-checked:bg-blue-600 after:content-[''] after:absolute after:top-0.5
    after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5
    after:transition-all peer-checked:after:translate-x-full"></div>
</label>
```

**After — daisyUI:**
```html
<input type="checkbox" class="toggle toggle-primary" />
```

**Detection pattern:** Complex peer-checked checkbox styling that creates a sliding toggle.

---

### Avatar

**Before — Tailwind:**
```html
<div class="w-12 h-12 rounded-full overflow-hidden ring-2 ring-blue-500 ring-offset-2">
  <img src="user.jpg" class="w-full h-full object-cover" />
</div>
```

**After — daisyUI:**
```html
<div class="avatar">
  <div class="w-12 rounded-full ring ring-primary ring-offset-base-100 ring-offset-2">
    <img src="user.jpg" />
  </div>
</div>
```

---

### Tabs

**Before — Tailwind:**
```html
<div class="flex border-b border-gray-200">
  <button class="px-4 py-2 border-b-2 border-blue-500 text-blue-600 font-medium">Tab 1</button>
  <button class="px-4 py-2 text-gray-500 hover:text-gray-700">Tab 2</button>
  <button class="px-4 py-2 text-gray-500 hover:text-gray-700">Tab 3</button>
</div>
```

**After — daisyUI:**
```html
<div role="tablist" class="tabs tabs-border">
  <a role="tab" class="tab tab-active">Tab 1</a>
  <a role="tab" class="tab">Tab 2</a>
  <a role="tab" class="tab">Tab 3</a>
</div>
```

---

### Loading Spinner

**Before — Tailwind:**
```html
<div class="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
```

**After — daisyUI:**
```html
<span class="loading loading-spinner loading-md text-primary"></span>
```

---

### Progress Bar

**Before — Tailwind:**
```html
<div class="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
  <div class="h-full bg-blue-500 rounded-full" style="width: 70%"></div>
</div>
```

**After — daisyUI:**
```html
<progress class="progress progress-primary w-full" value="70" max="100"></progress>
```

---

### Stats / Metric Cards

**Before — Tailwind:**
```html
<div class="flex flex-col items-center p-6 bg-white rounded-lg shadow">
  <span class="text-sm text-gray-500">Total Revenue</span>
  <span class="text-3xl font-bold">$45,231</span>
  <span class="text-sm text-green-500">↑ 12% from last month</span>
</div>
```

**After — daisyUI:**
```html
<div class="stat">
  <div class="stat-title">Total Revenue</div>
  <div class="stat-value">$45,231</div>
  <div class="stat-desc text-success">↑ 12% from last month</div>
</div>
```

---

### Breadcrumbs

**Before — Tailwind:**
```html
<nav class="flex items-center gap-2 text-sm text-gray-500">
  <a href="#" class="hover:text-gray-700">Home</a>
  <span>/</span>
  <a href="#" class="hover:text-gray-700">Products</a>
  <span>/</span>
  <span class="text-gray-900">Detail</span>
</nav>
```

**After — daisyUI:**
```html
<div class="breadcrumbs text-sm">
  <ul>
    <li><a>Home</a></li>
    <li><a>Products</a></li>
    <li>Detail</li>
  </ul>
</div>
```

---

### Table

**Before — Tailwind:**
```html
<table class="w-full text-left border-collapse">
  <thead>
    <tr class="border-b bg-gray-50">
      <th class="p-3 text-sm font-semibold text-gray-600">Name</th>
      <th class="p-3 text-sm font-semibold text-gray-600">Role</th>
    </tr>
  </thead>
  <tbody>
    <tr class="border-b hover:bg-gray-50">
      <td class="p-3">Alice</td>
      <td class="p-3">Engineer</td>
    </tr>
  </tbody>
</table>
```

**After — daisyUI:**
```html
<div class="overflow-x-auto">
  <table class="table">
    <thead>
      <tr>
        <th>Name</th>
        <th>Role</th>
      </tr>
    </thead>
    <tbody>
      <tr class="hover:bg-base-300">
        <td>Alice</td>
        <td>Engineer</td>
      </tr>
    </tbody>
  </table>
</div>
```

---

## Decision Framework

Use this flowchart to decide whether to convert:

```
Is there a daisyUI component that semantically matches this pattern?
├── YES → Does the conversion reduce class count significantly?
│   ├── YES → Convert ✅
│   └── NO  → Convert anyway for theme support ✅
└── NO  → Keep as Tailwind utilities ❌ (don't force it)
```

### When to Convert

- ✅ Multi-class utility chains that describe a standard UI component (button, card, alert)
- ✅ Color utilities that should respond to theme changes
- ✅ Interactive patterns (toggles, modals, dropdowns) that benefit from daisyUI's CSS-only approach
- ✅ Repeated patterns across the codebase (DRY principle)

### When NOT to Convert

- ❌ One-off layout utilities (`flex`, `grid`, `gap-4`, `p-8`)
- ❌ Custom decorative styling that doesn't map to a component
- ❌ Complex animation utilities (keep as Tailwind `animate-*`)
- ❌ Responsive-only utilities (`hidden md:block`, `lg:text-xl`)
- ❌ Arbitrary values (`w-[347px]`, `bg-[#1a1a2e]`)

---

## Common Pitfalls

| Pitfall | Correct Approach |
|---------|-----------------|
| Converting every `rounded shadow p-4` to `card` | Only use `card` when the element is a distinct content container with title/body/actions |
| Removing all Tailwind classes | daisyUI and Tailwind coexist — keep layout utilities |
| Hardcoding colors after conversion | Use semantic colors (`btn-primary`) so themes work |
| Ignoring the component structure | `card-title` must be inside `card-body`, not directly inside `card` |
| Over-nesting daisyUI components | Keep it flat where possible — not every `div` needs a daisyUI class |

---

## Full Page Before/After Example

### Before — Raw Tailwind

```html
<body class="bg-gray-100 min-h-screen">
  <!-- Header -->
  <header class="flex items-center justify-between px-6 py-3 bg-white shadow">
    <span class="text-xl font-bold text-gray-800">Dashboard</span>
    <div class="flex items-center gap-3">
      <div class="w-8 h-8 rounded-full bg-blue-500 text-white flex items-center
        justify-center text-sm font-bold">JD</div>
    </div>
  </header>

  <!-- Stats -->
  <div class="grid grid-cols-1 md:grid-cols-3 gap-4 p-6">
    <div class="bg-white rounded-lg shadow p-6">
      <p class="text-sm text-gray-500">Users</p>
      <p class="text-2xl font-bold">2,450</p>
      <p class="text-xs text-green-500">+12%</p>
    </div>
    <div class="bg-white rounded-lg shadow p-6">
      <p class="text-sm text-gray-500">Revenue</p>
      <p class="text-2xl font-bold">$18,200</p>
      <p class="text-xs text-red-500">-3%</p>
    </div>
    <div class="bg-white rounded-lg shadow p-6">
      <p class="text-sm text-gray-500">Orders</p>
      <p class="text-2xl font-bold">842</p>
      <p class="text-xs text-green-500">+8%</p>
    </div>
  </div>

  <!-- Alert -->
  <div class="mx-6 p-4 bg-yellow-50 border border-yellow-200 text-yellow-700 rounded-lg
    flex items-center gap-2">
    <span>⚠️</span>
    <span>System maintenance scheduled for tonight at 10 PM.</span>
  </div>

  <!-- Table -->
  <div class="m-6 bg-white rounded-lg shadow overflow-hidden">
    <table class="w-full text-left">
      <thead class="bg-gray-50 border-b">
        <tr>
          <th class="p-3 text-sm font-semibold text-gray-600">Name</th>
          <th class="p-3 text-sm font-semibold text-gray-600">Status</th>
          <th class="p-3 text-sm font-semibold text-gray-600">Action</th>
        </tr>
      </thead>
      <tbody>
        <tr class="border-b">
          <td class="p-3">Alice Johnson</td>
          <td class="p-3">
            <span class="px-2 py-0.5 rounded-full text-xs bg-green-100 text-green-800">Active</span>
          </td>
          <td class="p-3">
            <button class="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600">Edit</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</body>
```

### After — daisyUI Optimized

```html
<body class="bg-base-200 min-h-screen">
  <!-- Header -->
  <div class="navbar bg-base-100 shadow">
    <div class="navbar-start">
      <span class="btn btn-ghost text-xl">Dashboard</span>
    </div>
    <div class="navbar-end">
      <div class="avatar avatar-placeholder">
        <div class="bg-primary text-primary-content w-8 rounded-full">
          <span class="text-sm">JD</span>
        </div>
      </div>
    </div>
  </div>

  <!-- Stats -->
  <div class="grid grid-cols-1 md:grid-cols-3 gap-4 p-6">
    <div class="stat bg-base-100 rounded-box shadow">
      <div class="stat-title">Users</div>
      <div class="stat-value">2,450</div>
      <div class="stat-desc text-success">+12%</div>
    </div>
    <div class="stat bg-base-100 rounded-box shadow">
      <div class="stat-title">Revenue</div>
      <div class="stat-value">$18,200</div>
      <div class="stat-desc text-error">-3%</div>
    </div>
    <div class="stat bg-base-100 rounded-box shadow">
      <div class="stat-title">Orders</div>
      <div class="stat-value">842</div>
      <div class="stat-desc text-success">+8%</div>
    </div>
  </div>

  <!-- Alert -->
  <div class="mx-6">
    <div role="alert" class="alert alert-warning">
      <span>System maintenance scheduled for tonight at 10 PM.</span>
    </div>
  </div>

  <!-- Table -->
  <div class="m-6 bg-base-100 rounded-box shadow overflow-hidden">
    <div class="overflow-x-auto">
      <table class="table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Status</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Alice Johnson</td>
            <td><span class="badge badge-success">Active</span></td>
            <td><button class="btn btn-primary btn-sm">Edit</button></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</body>
```

**What changed:**
- Header → `navbar` (semantic, theme-aware)
- Stats → `stat` component (semantic parts: `stat-title`, `stat-value`, `stat-desc`)
- Alert → `alert alert-warning` (theme-aware colors)
- Table → `table` class (built-in styling, removes manual padding/borders)
- Badge → `badge badge-success` (replaces 6-class utility chain)
- Button → `btn btn-primary btn-sm` (replaces 5-class utility chain)
- Colors → Semantic (`bg-base-100`, `text-success`, `text-error`) instead of hardcoded

**What stayed as Tailwind:**
- Grid layout (`grid grid-cols-1 md:grid-cols-3 gap-4`)
- Spacing (`p-6`, `m-6`, `mx-6`)
- Min-height (`min-h-screen`)
- Overflow (`overflow-hidden`, `overflow-x-auto`)
