# Responsive Layout Patterns

> Build adaptive, mobile-friendly layouts using daisyUI's built-in layout patterns and Tailwind CSS responsive utilities.

---

## Built-in Layouts

daisyUI provides 5 ready-to-use layout patterns. Fetch them with:

```
Tool: daisyui-blueprint-daisyUI-Snippets
Parameters:
  layouts:
    bento-grid-5-sections: true
    bento-grid-8-sections: true
    responsive-collapsible-drawer-sidebar: true
    responsive-offcanvas-drawer-sidebar: true
    top-navbar: true
```

---

### Layout 1: Top Navbar

The simplest layout — navbar at top, content below, optional footer.

```
┌─────────────────────────────────┐
│ navbar                          │
├─────────────────────────────────┤
│                                 │
│         main content            │
│                                 │
├─────────────────────────────────┤
│ footer                          │
└─────────────────────────────────┘
```

**Best for:** Landing pages, blogs, simple apps, marketing sites.

```html
<div class="min-h-screen flex flex-col">
  <!-- Navbar -->
  <div class="navbar bg-base-100 shadow-sm">
    <div class="navbar-start">
      <a class="btn btn-ghost text-xl">Brand</a>
    </div>
    <div class="navbar-center hidden lg:flex">
      <ul class="menu menu-horizontal px-1">
        <li><a>Home</a></li>
        <li><a>About</a></li>
        <li><a>Contact</a></li>
      </ul>
    </div>
    <div class="navbar-end">
      <button class="btn btn-primary btn-sm">Sign Up</button>
    </div>
  </div>

  <!-- Content (grows to fill space) -->
  <main class="flex-1">
    <div class="max-w-7xl mx-auto px-4 py-8">
      <!-- Page content -->
    </div>
  </main>

  <!-- Footer -->
  <footer class="footer footer-center bg-base-200 text-base-content p-4">
    <p>© 2025 Brand. All rights reserved.</p>
  </footer>
</div>
```

---

### Layout 2: Off-canvas Drawer Sidebar

Sidebar is hidden on mobile, slides in as an overlay when toggled. Persistent on desktop.

```
Mobile:                          Desktop:
┌─────────────────┐              ┌────────┬──────────────┐
│ ☰ navbar        │              │        │ navbar       │
├─────────────────┤              │ sidebar│──────────────│
│                 │              │ (menu) │              │
│  main content   │  ← toggle → │        │ main content │
│                 │              │        │              │
└─────────────────┘              └────────┴──────────────┘
```

**Best for:** Dashboards, admin panels, apps with navigation.

```html
<div class="drawer lg:drawer-open">
  <input id="sidebar" type="checkbox" class="drawer-toggle" />

  <!-- Main content -->
  <div class="drawer-content">
    <div class="navbar bg-base-100 lg:hidden">
      <label for="sidebar" class="btn btn-ghost">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </label>
      <span class="text-lg font-bold">Dashboard</span>
    </div>
    <main class="p-4 md:p-6 lg:p-8">
      <!-- Content here -->
    </main>
  </div>

  <!-- Sidebar -->
  <div class="drawer-side">
    <label for="sidebar" aria-label="close sidebar" class="drawer-overlay"></label>
    <aside class="bg-base-100 min-h-full w-64">
      <div class="p-4 text-xl font-bold">Brand</div>
      <ul class="menu p-4">
        <li><a class="active">Dashboard</a></li>
        <li><a>Analytics</a></li>
        <li><a>Settings</a></li>
      </ul>
    </aside>
  </div>
</div>
```

**Key class:** `lg:drawer-open` makes the drawer persistent on large screens.

---

### Layout 3: Collapsible Drawer Sidebar

Always visible sidebar that collapses to icon-only on small screens or when toggled.

```
Collapsed:                       Expanded:
┌───┬────────────────┐           ┌──────────┬──────────────┐
│ 📊│ navbar          │           │ 📊 Dash  │ navbar       │
│ 📈│────────────────│           │ 📈 Stats │──────────────│
│ ⚙️│                │           │ ⚙️ Config│              │
│   │ main content   │           │          │ main content │
│   │                │           │          │              │
└───┴────────────────┘           └──────────┴──────────────┘
```

**Best for:** Complex apps needing always-accessible navigation.

```html
<div class="drawer lg:drawer-open">
  <input id="sidebar" type="checkbox" class="drawer-toggle" />

  <div class="drawer-content">
    <!-- Content -->
  </div>

  <div class="drawer-side">
    <label for="sidebar" class="drawer-overlay"></label>
    <aside class="bg-base-100 min-h-full w-64 is-drawer-open:w-64 is-drawer-close:w-16 transition-all">
      <ul class="menu p-2">
        <li>
          <a>
            <svg class="h-5 w-5"><!-- icon --></svg>
            <span class="is-drawer-close:hidden">Dashboard</span>
          </a>
        </li>
        <li>
          <a>
            <svg class="h-5 w-5"><!-- icon --></svg>
            <span class="is-drawer-close:hidden">Analytics</span>
          </a>
        </li>
      </ul>
    </aside>
  </div>
</div>
```

**Key classes:**
- `is-drawer-open:` — applies when drawer is open
- `is-drawer-close:` — applies when drawer is closed
- `is-drawer-close:hidden` — hides text labels when collapsed

---

### Layout 4: Bento Grid (5 Sections)

Asymmetric grid layout with 5 content areas of varying sizes.

```
┌───────────────┬─────────┐
│               │         │
│    Large      │  Small  │
│    (span 2)   │         │
├───────┬───────┼─────────┤
│       │       │         │
│ Small │ Small │  Tall   │
│       │       │ (span 2)│
└───────┴───────┴─────────┘
```

**Best for:** Feature showcases, portfolio, dashboards with varied content.

```html
<div class="grid grid-cols-1 md:grid-cols-3 gap-4 p-4">
  <!-- Large card spanning 2 columns -->
  <div class="card bg-base-100 shadow md:col-span-2">
    <div class="card-body">
      <h2 class="card-title">Featured Content</h2>
      <p>Primary content area with more space.</p>
    </div>
  </div>

  <!-- Small card -->
  <div class="card bg-base-100 shadow">
    <div class="card-body">
      <h2 class="card-title">Quick Stats</h2>
    </div>
  </div>

  <!-- Two small cards -->
  <div class="card bg-base-100 shadow">
    <div class="card-body">
      <h2 class="card-title">Item A</h2>
    </div>
  </div>
  <div class="card bg-base-100 shadow">
    <div class="card-body">
      <h2 class="card-title">Item B</h2>
    </div>
  </div>

  <!-- Tall card (in 3-column context, this fills the last column) -->
  <div class="card bg-base-100 shadow md:row-span-2">
    <div class="card-body">
      <h2 class="card-title">Tall Content</h2>
      <p>More vertical content here.</p>
    </div>
  </div>
</div>
```

---

### Layout 5: Bento Grid (8 Sections)

More complex asymmetric grid with 8 content areas.

```
┌───────┬───────┬───────┬───────┐
│ Wide          │       │       │
│ (span 2)      │ Small │ Small │
├───────┬───────┼───────┴───────┤
│       │       │  Wide         │
│ Small │ Small │  (span 2)     │
├───────┴───────┼───────┬───────┤
│  Wide         │       │       │
│  (span 2)     │ Small │ Small │
└───────────────┴───────┴───────┘
```

**Best for:** Complex dashboards, data-rich pages, portfolio grids.

```html
<div class="grid grid-cols-2 lg:grid-cols-4 gap-4 p-4">
  <div class="card bg-base-100 shadow col-span-2">
    <div class="card-body"><h2 class="card-title">Section 1</h2></div>
  </div>
  <div class="card bg-base-100 shadow">
    <div class="card-body"><h2 class="card-title">Section 2</h2></div>
  </div>
  <div class="card bg-base-100 shadow">
    <div class="card-body"><h2 class="card-title">Section 3</h2></div>
  </div>
  <div class="card bg-base-100 shadow">
    <div class="card-body"><h2 class="card-title">Section 4</h2></div>
  </div>
  <div class="card bg-base-100 shadow">
    <div class="card-body"><h2 class="card-title">Section 5</h2></div>
  </div>
  <div class="card bg-base-100 shadow col-span-2">
    <div class="card-body"><h2 class="card-title">Section 6</h2></div>
  </div>
  <div class="card bg-base-100 shadow col-span-2">
    <div class="card-body"><h2 class="card-title">Section 7</h2></div>
  </div>
  <div class="card bg-base-100 shadow">
    <div class="card-body"><h2 class="card-title">Section 8</h2></div>
  </div>
</div>
```

---

## Responsive Breakpoint Strategy

### Tailwind Breakpoints

| Prefix | Min-width | Target Devices |
|--------|-----------|----------------|
| (none) | 0px | Phones (portrait) |
| `sm:` | 640px | Phones (landscape), small tablets |
| `md:` | 768px | Tablets (portrait) |
| `lg:` | 1024px | Tablets (landscape), laptops |
| `xl:` | 1280px | Desktops |
| `2xl:` | 1536px | Large monitors |

### Mobile-First Approach (Recommended)

Start with mobile styles, add complexity at larger breakpoints:

```html
<!-- Mobile: 1 col → Tablet: 2 cols → Desktop: 4 cols -->
<div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">

<!-- Mobile: stack → Desktop: side by side -->
<div class="flex flex-col lg:flex-row gap-4">

<!-- Mobile: full width → Desktop: constrained -->
<div class="w-full max-w-7xl mx-auto px-4 md:px-6 lg:px-8">

<!-- Mobile: small text → Desktop: larger text -->
<h1 class="text-2xl md:text-4xl lg:text-5xl font-bold">

<!-- Mobile: compact → Desktop: spacious -->
<section class="py-8 md:py-12 lg:py-20">
```

### Desktop-First Approach

Occasionally useful when the design starts from desktop (Figma files are usually desktop-first):

```html
<!-- Desktop default, simplify for mobile -->
<div class="grid grid-cols-4 md:grid-cols-2 sm:grid-cols-1 gap-4">
```

> **Note:** Tailwind's breakpoints are min-width, so desktop-first requires more overrides. Mobile-first is cleaner.

---

## Common Responsive Patterns

### Pattern 1: Sidebar Collapses to Off-canvas

```html
<!-- Sidebar visible on lg+, off-canvas drawer on smaller -->
<div class="drawer lg:drawer-open">
  <input id="my-drawer" type="checkbox" class="drawer-toggle" />
  <div class="drawer-content">
    <!-- Show hamburger only on mobile -->
    <label for="my-drawer" class="btn btn-ghost lg:hidden">☰</label>
    <main><!-- content --></main>
  </div>
  <div class="drawer-side">
    <label for="my-drawer" class="drawer-overlay"></label>
    <nav class="menu bg-base-100 w-64 min-h-full p-4">
      <!-- nav items -->
    </nav>
  </div>
</div>
```

### Pattern 2: Card Grid Reflow

```html
<!-- 1 → 2 → 3 → 4 columns as screen grows -->
<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6">
  <div class="card bg-base-100 shadow"><!-- card --></div>
  <div class="card bg-base-100 shadow"><!-- card --></div>
  <div class="card bg-base-100 shadow"><!-- card --></div>
  <div class="card bg-base-100 shadow"><!-- card --></div>
</div>
```

### Pattern 3: Navbar → Hamburger Menu

```html
<div class="navbar bg-base-100">
  <div class="navbar-start">
    <!-- Mobile: dropdown hamburger menu -->
    <div class="dropdown">
      <div tabindex="0" role="button" class="btn btn-ghost lg:hidden">☰</div>
      <ul tabindex="0" class="menu menu-sm dropdown-content bg-base-100 rounded-box mt-3 w-52 p-2 shadow z-10">
        <li><a>Home</a></li>
        <li><a>About</a></li>
      </ul>
    </div>
    <a class="btn btn-ghost text-xl">Brand</a>
  </div>
  <!-- Desktop: horizontal menu -->
  <div class="navbar-center hidden lg:flex">
    <ul class="menu menu-horizontal px-1">
      <li><a>Home</a></li>
      <li><a>About</a></li>
    </ul>
  </div>
</div>
```

### Pattern 4: Stats Reflow

```html
<!-- Vertical stack on mobile, horizontal row on desktop -->
<div class="stats stats-vertical lg:stats-horizontal shadow w-full">
  <div class="stat">
    <div class="stat-title">Downloads</div>
    <div class="stat-value">31K</div>
  </div>
  <div class="stat">
    <div class="stat-title">Users</div>
    <div class="stat-value">4,200</div>
  </div>
  <div class="stat">
    <div class="stat-title">Revenue</div>
    <div class="stat-value">$12K</div>
  </div>
</div>
```

### Pattern 5: Steps Reflow

```html
<!-- Vertical on mobile, horizontal on desktop -->
<ul class="steps steps-vertical lg:steps-horizontal w-full">
  <li class="step step-primary">Register</li>
  <li class="step step-primary">Choose Plan</li>
  <li class="step">Payment</li>
  <li class="step">Complete</li>
</ul>
```

### Pattern 6: Table Scroll

```html
<!-- Table scrolls horizontally on small screens -->
<div class="overflow-x-auto">
  <table class="table">
    <!-- tables naturally overflow on mobile, this wrapper adds scroll -->
    <thead>
      <tr>
        <th>Name</th>
        <th>Email</th>
        <th>Role</th>
        <th>Status</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody><!-- rows --></tbody>
  </table>
</div>
```

### Pattern 7: Hero Image Stacking

```html
<!-- Side by side on desktop, stacked on mobile -->
<div class="hero min-h-[60vh] bg-base-200">
  <div class="hero-content flex-col lg:flex-row gap-8">
    <img src="hero.jpg" class="max-w-sm rounded-lg shadow-2xl w-full lg:w-auto" />
    <div>
      <h1 class="text-3xl md:text-5xl font-bold">Headline</h1>
      <p class="py-6">Description text</p>
      <button class="btn btn-primary">Get Started</button>
    </div>
  </div>
</div>
```

### Pattern 8: Bottom Navigation (Mobile Only)

```html
<!-- Show dock only on mobile, replace with sidebar/navbar on desktop -->
<div class="dock lg:hidden">
  <button>🏠</button>
  <button class="dock-active">🔍</button>
  <button>👤</button>
  <button>⚙️</button>
</div>

<!-- Desktop navigation shown via drawer/navbar with lg:flex/lg:drawer-open -->
```

### Pattern 9: Footer Column Reflow

```html
<!-- Stack vertically on mobile, 3 columns on desktop -->
<footer class="footer bg-base-200 text-base-content p-10">
  <nav>
    <h6 class="footer-title">Services</h6>
    <a class="link link-hover">Branding</a>
    <a class="link link-hover">Design</a>
  </nav>
  <nav>
    <h6 class="footer-title">Company</h6>
    <a class="link link-hover">About us</a>
    <a class="link link-hover">Contact</a>
  </nav>
  <nav>
    <h6 class="footer-title">Legal</h6>
    <a class="link link-hover">Terms of use</a>
    <a class="link link-hover">Privacy policy</a>
  </nav>
</footer>
```

> daisyUI's `footer` component handles the responsive column layout automatically.

---

## Responsive Utilities Cheat Sheet

### Show / Hide

```html
<div class="hidden md:block">Desktop only</div>
<div class="block md:hidden">Mobile only</div>
<div class="hidden lg:flex">Flex on lg+</div>
```

### Conditional Layout

```html
<!-- Column on mobile, row on desktop -->
<div class="flex flex-col md:flex-row">

<!-- 1 column on mobile, 3 on desktop -->
<div class="grid grid-cols-1 lg:grid-cols-3">

<!-- Full width on mobile, half on desktop -->
<div class="w-full lg:w-1/2">
```

### Conditional Spacing

```html
<div class="p-2 md:p-4 lg:p-8">        <!-- Progressive padding -->
<div class="gap-2 md:gap-4 lg:gap-6">  <!-- Progressive gap -->
<div class="my-4 md:my-8 lg:my-16">    <!-- Progressive margin -->
```

### Conditional Typography

```html
<h1 class="text-xl md:text-3xl lg:text-5xl">  <!-- Progressive heading size -->
<p class="text-sm md:text-base">               <!-- Adjust body text -->
```

### Conditional Component Size

```html
<button class="btn btn-sm md:btn-md">    <!-- Smaller button on mobile -->
<input class="input input-sm md:input-md"> <!-- Smaller input on mobile -->
```

---

## Testing Responsive Layouts

### Browser DevTools

1. Open DevTools (F12)
2. Toggle device toolbar (Ctrl+Shift+M / Cmd+Shift+M)
3. Test at these widths: 375px, 640px, 768px, 1024px, 1280px, 1536px

### Checklist

- [ ] Sidebar collapses on mobile (if using drawer)
- [ ] Navigation shows hamburger on mobile
- [ ] Cards stack to single column on mobile
- [ ] Tables have horizontal scroll on mobile
- [ ] Text sizes are readable at all breakpoints
- [ ] Buttons are touch-friendly (min 44px height on mobile)
- [ ] No horizontal overflow (check for x-scroll)
- [ ] Spacing feels proportional at each breakpoint
- [ ] Modals fit within viewport on mobile
- [ ] Bottom dock visible only on mobile (if used)


## Steering experiences — learned from real agent usage

### Grid vs. flexbox decision

**Problem:** Agent defaults to flexbox for everything, causing uneven column widths in card grids and stat rows.

**Fix:** Use this decision rule:

| Layout need | Use | Why |
|---|---|---|
| Equal-width columns (stats, cards, features) | `grid grid-cols-N` | Grid enforces equal widths regardless of content |
| Variable-width items (tags, badges, nav items) | `flex flex-wrap` | Flexbox lets items size to content |
| Two-column with fixed sidebar | `grid grid-cols-[280px_1fr]` or drawer | Fixed + fluid split |
| Centered single column | `max-w-* mx-auto` | No grid/flex needed |
| Stack that reflows | `flex flex-col md:flex-row` | Responsive direction change |

### Drawer responsive patterns

**Problem:** Agent uses `hidden lg:block` to show/hide the sidebar instead of daisyUI's built-in responsive drawer pattern.

**Fix:** Use daisyUI's `lg:drawer-open` class:

```html
<!-- ✅ daisyUI responsive drawer -->
<div class="drawer lg:drawer-open">
  <input id="drawer" type="checkbox" class="drawer-toggle" />
  <div class="drawer-content">
    <!-- Always visible: hamburger only on mobile -->
    <label for="drawer" class="btn btn-ghost lg:hidden">☰</label>
    <main class="p-6"><!-- content --></main>
  </div>
  <div class="drawer-side">
    <label for="drawer" class="drawer-overlay"></label>
    <aside class="bg-base-200 min-h-full w-80 p-4">
      <ul class="menu"><!-- nav items --></ul>
    </aside>
  </div>
</div>

<!-- ❌ Don't manually hide/show -->
<aside class="hidden lg:block w-80"><!-- breaks mobile toggle --></aside>
```

### Breakpoint consistency

**Problem:** Agent mixes breakpoint prefixes inconsistently: some elements use `sm:`, others jump to `lg:`, creating layout breakage at medium widths.

**Fix:** Pick a consistent breakpoint strategy per page:

| Pattern | Breakpoints | Use case |
|---|---|---|
| Mobile-first two-step | `md:` and `lg:` | Most dashboards and apps |
| Mobile-first three-step | `sm:`, `md:`, `lg:` | Content-heavy pages with many columns |
| Single breakpoint | `lg:` only | Simple layouts (sidebar + content) |

Verify by scanning all responsive classes in the output — every `sm:` should have a corresponding flow at default size, every `lg:` should have a `md:` or default fallback.
