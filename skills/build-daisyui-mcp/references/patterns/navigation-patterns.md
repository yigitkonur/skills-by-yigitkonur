# daisyUI 5 — Navigation Patterns

> **Purpose**: Complete reference for building navigation UIs — navbar, drawer sidebar, dock, dropdown, menu, breadcrumbs, tabs, and steps.

---

## Navbar

### Basic Navbar

```html
<div class="navbar bg-base-100 shadow-sm">
  <div class="navbar-start">
    <a class="btn btn-ghost text-xl">MyApp</a>
  </div>
  <div class="navbar-center hidden lg:flex">
    <ul class="menu menu-horizontal px-1">
      <li><a>Home</a></li>
      <li><a>About</a></li>
      <li><a>Contact</a></li>
    </ul>
  </div>
  <div class="navbar-end">
    <a class="btn btn-primary">Login</a>
  </div>
</div>
```

### Responsive Navbar with Mobile Dropdown

```html
<div class="navbar bg-base-100 shadow-sm">
  <div class="navbar-start">
    <!-- Mobile hamburger menu -->
    <details class="dropdown lg:hidden">
      <summary class="btn btn-ghost">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none"
             viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M4 6h16M4 12h8m-8 6h16" />
        </svg>
      </summary>
      <ul class="dropdown-content menu bg-base-100 rounded-box z-10 w-52 p-2 shadow">
        <li><a>Home</a></li>
        <li><a>About</a></li>
        <li><a>Contact</a></li>
      </ul>
    </details>
    <a class="btn btn-ghost text-xl">MyApp</a>
  </div>
  <div class="navbar-center hidden lg:flex">
    <ul class="menu menu-horizontal px-1">
      <li><a>Home</a></li>
      <li><a>About</a></li>
      <li><a>Contact</a></li>
    </ul>
  </div>
  <div class="navbar-end">
    <a class="btn btn-primary">Login</a>
  </div>
</div>
```

### Navbar with Search & User Menu

```html
<div class="navbar bg-base-100 shadow-sm">
  <div class="navbar-start">
    <a class="btn btn-ghost text-xl">MyApp</a>
  </div>
  <div class="navbar-center">
    <input type="text" class="input input-sm w-64" placeholder="Search..." />
  </div>
  <div class="navbar-end gap-2">
    <button class="btn btn-ghost btn-circle">
      <div class="indicator">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none"
             viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        <span class="badge badge-xs badge-primary indicator-item"></span>
      </div>
    </button>
    <details class="dropdown dropdown-end">
      <summary class="btn btn-ghost btn-circle avatar">
        <div class="w-10 rounded-full">
          <img alt="User" src="https://img.daisyui.com/images/stock/photo-1534528741775-53994a69daeb.webp" />
        </div>
      </summary>
      <ul class="dropdown-content menu bg-base-100 rounded-box z-10 w-52 p-2 shadow">
        <li><a>Profile</a></li>
        <li><a>Settings</a></li>
        <li><a>Logout</a></li>
      </ul>
    </details>
  </div>
</div>
```

---

## Drawer Sidebar

CSS-only sidebar using checkbox toggle.

### Responsive Drawer (Hidden on Mobile, Persistent on Desktop)

```html
<div class="drawer lg:drawer-open">
  <input id="sidebar" type="checkbox" class="drawer-toggle" />

  <!-- Main content -->
  <div class="drawer-content">
    <div class="navbar bg-base-100 lg:hidden">
      <label for="sidebar" class="btn btn-ghost drawer-button">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none"
             viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M4 6h16M4 12h8m-8 6h16" />
        </svg>
      </label>
    </div>
    <div class="p-4">
      <!-- Page content here -->
    </div>
  </div>

  <!-- Sidebar -->
  <div class="drawer-side">
    <label for="sidebar" aria-label="close sidebar" class="drawer-overlay"></label>
    <ul class="menu bg-base-200 text-base-content min-h-full w-64 p-4">
      <li class="menu-title">Navigation</li>
      <li><a class="menu-active">Dashboard</a></li>
      <li><a>Users</a></li>
      <li><a>Settings</a></li>
    </ul>
  </div>
</div>
```

### Collapsible Icon-Only Sidebar

Uses daisyUI's custom variants `is-drawer-open:` and `is-drawer-close:`:

```html
<div class="drawer lg:drawer-open">
  <input id="sidebar" type="checkbox" class="drawer-toggle" />
  <div class="drawer-content">
    <!-- content -->
  </div>
  <div class="drawer-side">
    <label for="sidebar" class="drawer-overlay"></label>
    <aside class="bg-base-200 min-h-full is-drawer-close:w-14 is-drawer-open:w-64 transition-all">
      <ul class="menu p-2">
        <li>
          <a>
            <svg class="size-5"><!-- icon --></svg>
            <span class="is-drawer-close:hidden">Dashboard</span>
          </a>
        </li>
        <li>
          <a>
            <svg class="size-5"><!-- icon --></svg>
            <span class="is-drawer-close:hidden">Users</span>
          </a>
        </li>
      </ul>
    </aside>
  </div>
</div>
```

### Right-Side Drawer

```html
<div class="drawer drawer-end">
  <input id="right-drawer" type="checkbox" class="drawer-toggle" />
  <div class="drawer-content">
    <label for="right-drawer" class="btn btn-primary">Open Right Drawer</label>
  </div>
  <div class="drawer-side">
    <label for="right-drawer" class="drawer-overlay"></label>
    <div class="bg-base-200 min-h-full w-80 p-4">
      <!-- Right panel content -->
    </div>
  </div>
</div>
```

### Required Drawer Parts

| Part | Class | Purpose |
|------|-------|---------|
| Toggle | `drawer-toggle` | Hidden checkbox that controls open/close state |
| Content | `drawer-content` | Main page content area |
| Side | `drawer-side` | Sidebar container |
| Overlay | `drawer-overlay` | Click-to-close overlay behind sidebar |

---

## Dock (New in v5 — Replaces `btm-nav`)

Bottom navigation bar for mobile:

```html
<div class="dock">
  <button>
    <svg class="size-[1.2em]"><!-- home icon --></svg>
    <span class="dock-label">Home</span>
  </button>
  <button class="dock-active">
    <svg class="size-[1.2em]"><!-- search icon --></svg>
    <span class="dock-label">Search</span>
  </button>
  <button>
    <svg class="size-[1.2em]"><!-- settings icon --></svg>
    <span class="dock-label">Settings</span>
  </button>
</div>
```

### Dock Sizes

```html
<div class="dock dock-xs"><!-- Extra small --></div>
<div class="dock dock-sm"><!-- Small --></div>
<div class="dock dock-md"><!-- Medium (default) --></div>
<div class="dock dock-lg"><!-- Large --></div>
<div class="dock dock-xl"><!-- Extra large --></div>
```

### Mobile-Only Dock

```html
<div class="dock lg:hidden">
  <!-- Only visible on mobile -->
</div>
```

---

## Dropdown

CSS-only dropdown using `<details>`:

```html
<details class="dropdown">
  <summary class="btn m-1">Click me</summary>
  <ul class="dropdown-content menu bg-base-100 rounded-box z-10 w-52 p-2 shadow">
    <li><a>Option 1</a></li>
    <li><a>Option 2</a></li>
    <li><a>Option 3</a></li>
  </ul>
</details>
```

### Dropdown Positions

```html
<details class="dropdown dropdown-end"><!-- Align right --></details>
<details class="dropdown dropdown-top"><!-- Open upward --></details>
<details class="dropdown dropdown-left"><!-- Open left --></details>
<details class="dropdown dropdown-right"><!-- Open right --></details>
```

### Hover Dropdown

```html
<div class="dropdown dropdown-hover">
  <div tabindex="0" role="button" class="btn">Hover me</div>
  <ul tabindex="0" class="dropdown-content menu bg-base-100 rounded-box z-10 w-52 p-2 shadow">
    <li><a>Item 1</a></li>
    <li><a>Item 2</a></li>
  </ul>
</div>
```

---

## Menu

### Vertical Menu (Default)

```html
<ul class="menu bg-base-200 rounded-box w-56">
  <li class="menu-title">Navigation</li>
  <li><a>Home</a></li>
  <li><a class="menu-active">Dashboard</a></li>
  <li class="menu-disabled"><a>Disabled</a></li>
</ul>
```

### Horizontal Menu

```html
<ul class="menu menu-horizontal bg-base-200 rounded-box">
  <li><a>Home</a></li>
  <li><a>About</a></li>
  <li><a>Contact</a></li>
</ul>
```

### Menu with Submenu (Collapsible)

```html
<ul class="menu bg-base-200 rounded-box w-56">
  <li><a>Home</a></li>
  <li>
    <details>
      <summary>Settings</summary>
      <ul>
        <li><a>Profile</a></li>
        <li><a>Account</a></li>
        <li><a>Privacy</a></li>
      </ul>
    </details>
  </li>
  <li><a>About</a></li>
</ul>
```

### Menu with Icons

```html
<ul class="menu bg-base-200 rounded-box w-56">
  <li>
    <a>
      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none"
           viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
      </svg>
      Home
    </a>
  </li>
</ul>
```

---

## Breadcrumbs

```html
<div class="breadcrumbs text-sm">
  <ul>
    <li><a>Home</a></li>
    <li><a>Documents</a></li>
    <li>Current Page</li>
  </ul>
</div>
```

---

## Tabs

### CSS-Only Tabs with Content

```html
<div role="tablist" class="tabs tabs-lift">
  <input type="radio" name="tab" role="tab" class="tab" aria-label="Tab 1" checked />
  <div role="tabpanel" class="tab-content bg-base-100 border-base-300 p-6">
    Tab 1 content
  </div>

  <input type="radio" name="tab" role="tab" class="tab" aria-label="Tab 2" />
  <div role="tabpanel" class="tab-content bg-base-100 border-base-300 p-6">
    Tab 2 content
  </div>

  <input type="radio" name="tab" role="tab" class="tab" aria-label="Tab 3" />
  <div role="tabpanel" class="tab-content bg-base-100 border-base-300 p-6">
    Tab 3 content
  </div>
</div>
```

### Tab Styles

```html
<div role="tablist" class="tabs tabs-border"><!-- Border style --></div>
<div role="tablist" class="tabs tabs-lift"><!-- Lifted style --></div>
<div role="tablist" class="tabs tabs-box"><!-- Box style --></div>
```

### Tab Sizes

```html
<div role="tablist" class="tabs tabs-lift tabs-xs"><!-- Extra small --></div>
<div role="tablist" class="tabs tabs-lift tabs-sm"><!-- Small --></div>
<div role="tablist" class="tabs tabs-lift tabs-md"><!-- Medium --></div>
<div role="tablist" class="tabs tabs-lift tabs-lg"><!-- Large --></div>
```

---

## Steps

```html
<ul class="steps">
  <li class="step step-primary">Register</li>
  <li class="step step-primary">Choose Plan</li>
  <li class="step">Payment</li>
  <li class="step">Confirm</li>
</ul>
```

### Vertical Steps

```html
<ul class="steps steps-vertical">
  <li class="step step-primary">Register</li>
  <li class="step step-primary">Processing</li>
  <li class="step">Complete</li>
</ul>
```

### Responsive Steps

```html
<ul class="steps steps-vertical lg:steps-horizontal">
  <!-- Vertical on mobile, horizontal on desktop -->
</ul>
```

---

## Common Navigation Mistakes

| Mistake | Fix |
|---------|-----|
| Using `btm-nav` class | Removed in v5 — use `dock` |
| Using `tabs-lifted` | Renamed to `tabs-lift` in v5 |
| Using `tabs-bordered` | Renamed to `tabs-border` in v5 |
| Using `tabs-boxed` | Renamed to `tabs-box` in v5 |
| Missing `drawer-overlay` | Always include for click-to-close behavior |
| Missing `drawer-toggle` checkbox | Required for CSS-only drawer state |
| Using `active` class on menu | Use `menu-active` in v5 |
| Using `disabled` class on menu | Use `menu-disabled` in v5 |
| Adding `z-index` to dropdown content | Use Tailwind `z-10` or higher on `dropdown-content` |
| Adding JS for tab switching | Use radio inputs with `tab` class — pure CSS |


## Steering experiences — learned from real agent usage

### Drawer toggle sibling rule

**Problem:** Agent places the drawer toggle checkbox (`<input class="drawer-toggle">`) inside `.drawer-content` or `.drawer-side`. It must be a direct child of the `.drawer` container, sibling to both `.drawer-content` and `.drawer-side`.

```html
<!-- ✅ Correct: checkbox is sibling to drawer-content and drawer-side -->
<div class="drawer lg:drawer-open">
  <input id="nav-drawer" type="checkbox" class="drawer-toggle" />
  <div class="drawer-content">
    <label for="nav-drawer" class="btn btn-ghost drawer-button lg:hidden">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
      </svg>
    </label>
    <!-- page content -->
  </div>
  <div class="drawer-side">
    <label for="nav-drawer" aria-label="close sidebar" class="drawer-overlay"></label>
    <ul class="menu bg-base-200 min-h-full w-80 p-4">
      <li><a class="menu-active">Dashboard</a></li>
      <li><a>Analytics</a></li>
    </ul>
  </div>
</div>
```

### Icon-only collapsed sidebar

**Problem:** Agent tries to build an icon-only collapsed sidebar using `hidden`/`block` on text labels. daisyUI v5 has built-in drawer variants for this.

**Fix:** Use `is-drawer-open:` and `is-drawer-close:` variants:

```html
<div class="drawer lg:drawer-open">
  <input id="sidebar" type="checkbox" class="drawer-toggle" />
  <div class="drawer-content"><!-- main content --></div>
  <div class="drawer-side">
    <label for="sidebar" class="drawer-overlay"></label>
    <ul class="menu bg-base-200 min-h-full w-20 is-drawer-open:w-64 p-4 transition-all">
      <li>
        <a>
          <svg><!-- icon --></svg>
          <span class="is-drawer-close:hidden">Dashboard</span>
        </a>
      </li>
    </ul>
  </div>
</div>
```

### Active state on menu items

**Problem:** Agent uses custom CSS or Tailwind utilities for active menu states instead of daisyUI's built-in `active` class.

```html
<!-- ✅ Use daisyUI's active class -->
<ul class="menu">
  <li><a class="menu-active">Dashboard</a></li>
  <li><a>Settings</a></li>
</ul>

<!-- ❌ Don't use custom active styling -->
<ul class="menu">
  <li><a class="bg-primary text-white rounded-lg">Dashboard</a></li>
</ul>
```

### Responsive navbar with drawer

**Problem:** Agent builds a navbar and sidebar as separate, uncoordinated components. They should share the same drawer toggle.

**Fix:** The navbar hamburger button and the drawer share the same checkbox `id`/`for`:

```html
<div class="drawer lg:drawer-open">
  <input id="app-drawer" type="checkbox" class="drawer-toggle" />
  <div class="drawer-content flex flex-col">
    <!-- Navbar at top of content area -->
    <div class="navbar bg-base-100 shadow-sm">
      <div class="flex-none lg:hidden">
        <label for="app-drawer" class="btn btn-square btn-ghost">
          <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
          </svg>
        </label>
      </div>
      <div class="flex-1"><h1 class="text-xl font-bold px-2">App Name</h1></div>
    </div>
    <!-- Page content below navbar -->
    <main class="flex-1 p-6">
      <!-- content here -->
    </main>
  </div>
  <div class="drawer-side">
    <label for="app-drawer" class="drawer-overlay"></label>
    <aside class="bg-base-200 min-h-full w-80">
      <ul class="menu p-4">
        <li><a class="menu-active">Dashboard</a></li>
        <li><a>Reports</a></li>
      </ul>
    </aside>
  </div>
</div>
```
