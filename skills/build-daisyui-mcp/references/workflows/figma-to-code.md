# Figma Design to daisyUI Code Workflow

> Convert any Figma design into production-ready daisyUI + Tailwind CSS code using the MCP tools.

---

## Quick Reference

| Step | Action | Tool |
|------|--------|------|
| 1 | Get Figma URL | — |
| 2 | Fetch design structure | `daisyui-blueprint-Figma-to-daisyUI` |
| 3 | Analyze returned data | — |
| 4 | Map to daisyUI components | — |
| 5 | Fetch component snippets | `daisyui-blueprint-daisyUI-Snippets` |
| 6 | Assemble HTML | — |
| 7 | Add responsive breakpoints | — |

---

## Step 1: Get the Figma URL

Accept one of these URL formats from the user:

```
# Full file URL
https://www.figma.com/design/abc123/My-Design

# Specific node URL (preferred — more focused)
https://www.figma.com/design/abc123/My-Design?node-id=1-2

# Prototype URL (also works)
https://www.figma.com/proto/abc123/My-Design?node-id=1-2
```

**Tips:**
- If the user provides a full file URL, ask if they want a specific frame/page converted
- Node-specific URLs produce more focused, accurate results
- Right-click any frame in Figma → "Copy link" to get a node-specific URL

---

## Step 2: Fetch the Design Structure

Call the Figma-to-daisyUI tool:

```
Tool: daisyui-blueprint-Figma-to-daisyUI
Parameters:
  url: <figma_url>
  depth: 3-5         # Start low for overview
  includeImages: false  # Set true only if you need image references
```

### Depth Strategy

| Depth | Use Case | When to Use |
|-------|----------|-------------|
| 1-2 | High-level page structure | Initial exploration of complex files |
| 3-5 | Component-level detail | **Default — start here** |
| 6-8 | Granular element detail | When you need exact text, icons, spacing |
| 9-10 | Full tree | Small components or when precision matters |

**Iterative approach:** Start with depth 3. If the returned structure lacks detail for a specific section, re-fetch with a higher depth targeting that node's URL.

---

## Step 3: Analyze the Returned Structure

The tool returns a JSON tree. Key properties to examine:

### Layout Properties
```
layoutMode: "HORIZONTAL" → flex-row (Tailwind: flex flex-row)
layoutMode: "VERTICAL"   → flex-col (Tailwind: flex flex-col)
layoutMode: "NONE"       → absolute positioning or static

primaryAxisAlignItems:
  "MIN"    → justify-start
  "CENTER" → justify-center
  "MAX"    → justify-end
  "SPACE_BETWEEN" → justify-between

counterAxisAlignItems:
  "MIN"    → items-start
  "CENTER" → items-center
  "MAX"    → items-end
```

### Spacing Properties
```
itemSpacing: 16    → gap-4 (divide by 4 for Tailwind units)
paddingTop: 24     → pt-6
paddingBottom: 24  → pb-6
paddingLeft: 16    → px-4
paddingRight: 16   → px-4
```

### Visual Properties
```
fills[0].color → background-color
  Map to nearest daisyUI semantic color (primary, secondary, etc.)
  Or use Tailwind arbitrary: bg-[#hexcolor]

cornerRadius: 8  → rounded-lg
cornerRadius: 16 → rounded-2xl
cornerRadius: 9999 → rounded-full

effects (drop shadow) → shadow-sm / shadow-md / shadow-lg
```

### Text Properties
```
fontSize: 14 → text-sm
fontSize: 16 → text-base
fontSize: 18 → text-lg
fontSize: 24 → text-2xl
fontSize: 32 → text-3xl

fontWeight: 400 → font-normal
fontWeight: 500 → font-medium
fontWeight: 600 → font-semibold
fontWeight: 700 → font-bold
```

---

## Step 4: Map Figma Elements to daisyUI Components

### Decision Tree

```
Figma Frame Analysis
│
├── Has horizontal nav at top with logo + links?
│   └── → navbar component
│
├── Has side panel with navigation links?
│   └── → drawer component (+ menu for links)
│
├── Has image + text + action area in a contained box?
│   └── → card component
│
├── Has a grid of similar contained items?
│   └── → card components in Tailwind grid
│
├── Has tab-like navigation switching content?
│   └── → tab component
│
├── Has a data table with rows/columns?
│   └── → table component
│
├── Has form inputs grouped together?
│   └── → fieldset + input/select/textarea/checkbox/toggle
│
├── Has a floating overlay with content?
│   └── → modal component
│
├── Has a floating small message/notification?
│   └── → toast + alert components
│
├── Has a large hero section with CTA?
│   └── → hero component
│
├── Has step indicators / progress flow?
│   └── → steps component
│
├── Has metrics/numbers displayed prominently?
│   └── → stat component
│
├── Has a scrollable horizontal image/card list?
│   └── → carousel component
│
├── Has message bubbles (chat-like)?
│   └── → chat component
│
├── Has star/heart rating display?
│   └── → rating component
│
├── Has breadcrumb navigation trail?
│   └── → breadcrumbs component
│
├── Has pagination controls?
│   └── → pagination component (join + button)
│
└── Has a page footer with links?
    └── → footer component
```

### Common Figma-to-daisyUI Mappings

| Figma Pattern | daisyUI Component | Key Classes |
|---------------|-------------------|-------------|
| Top bar with logo + menu | `navbar` | `navbar`, `navbar-start`, `navbar-center`, `navbar-end` |
| Side navigation | `drawer` + `menu` | `drawer`, `drawer-toggle`, `drawer-side`, `menu` |
| Content card | `card` | `card`, `card-body`, `card-title`, `card-actions` |
| Action button | `button` | `btn`, `btn-primary`, `btn-outline`, etc. |
| Form group | `fieldset` + inputs | `fieldset`, `fieldset-legend`, `input`, `label` |
| Popup dialog | `modal` | `modal`, `modal-box`, `modal-action` |
| Image slider | `carousel` | `carousel`, `carousel-item` |
| Bottom bar | `dock` | `dock` |
| Loading state | `skeleton` / `loading` | `skeleton`, `loading loading-spinner` |
| User avatar | `avatar` | `avatar` |
| Badge/tag | `badge` | `badge`, `badge-primary` |
| Toggle switch | `toggle` | `toggle`, `toggle-primary` |
| Expandable section | `collapse` / `accordion` | `collapse`, `collapse-title`, `collapse-content` |
| Progress indicator | `progress` / `radial-progress` | `progress`, `progress-primary` |
| Tooltip hover text | `tooltip` | — (use Tailwind or custom) |
| Divider line | `divider` | `divider` |
| Keyboard shortcut | `kbd` | `kbd` |
| Timeline / history | `timeline` | `timeline` |

---

## Step 5: Fetch Component Snippets

Once you've identified which daisyUI components are needed, fetch their snippets:

```
Tool: daisyui-blueprint-daisyUI-Snippets

# Example: Building a dashboard
Parameters:
  components:
    navbar: true
    drawer: true
    card: true
    stat: true
    table: true
    button: true
    avatar: true
    menu: true
  layouts:
    responsive-offcanvas-drawer-sidebar: true
  templates:
    dashboard: true
```

**Snippet categories to request:**

| Category | When to Use |
|----------|-------------|
| `components` | Base component class definitions and available modifiers |
| `component-examples` | Complete HTML examples with common patterns |
| `layouts` | Page-level layout structures (drawer sidebars, navbars) |
| `templates` | Full page templates (dashboard, login) |
| `themes` | Theme setup (built-in list, custom theme, colors) |

**Always fetch both `components` AND `component-examples` for complex components:**

```
Parameters:
  components:
    card: true
  component-examples:
    card.card: true
    card.card-with-image-on-side: true
    card.responsive-card-vertical-on-small-screen-horizontal-on-large-screen: true
```

---

## Step 6: Assemble HTML

### Assembly Order

1. **Outer layout** — Start with the page-level structure (drawer, navbar)
2. **Content sections** — Add major content areas with Tailwind grid/flex
3. **Components** — Place daisyUI components into the sections
4. **Fine-tune** — Adjust spacing, colors, sizing

### Layout Translation

```html
<!-- Figma: Vertical frame with 24px gap, 16px padding -->
<div class="flex flex-col gap-6 p-4">
  <!-- children -->
</div>

<!-- Figma: Horizontal frame, space-between, center aligned -->
<div class="flex flex-row justify-between items-center">
  <!-- children -->
</div>

<!-- Figma: 3-column grid layout -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  <!-- cards -->
</div>

<!-- Figma: Fixed width container centered -->
<div class="max-w-6xl mx-auto px-4">
  <!-- content -->
</div>
```

### Color Mapping Strategy

1. **Primary action color** → `primary`
2. **Secondary/supporting color** → `secondary`
3. **Accent/highlight color** → `accent`
4. **Dark neutral/text** → `neutral`
5. **Background tones** → `base-100` (lightest), `base-200`, `base-300` (darkest bg)
6. **Status colors** → `info`, `success`, `warning`, `error`

```html
<!-- Map Figma colors to daisyUI semantic colors -->
<button class="btn btn-primary">Main CTA</button>
<button class="btn btn-secondary">Secondary Action</button>
<div class="bg-base-200 p-4">Content area</div>
<span class="text-base-content/60">Muted text</span>
```

---

## Step 7: Add Responsive Breakpoints

### Figma Auto-Layout to Responsive Rules

| Figma Behavior | Tailwind Responsive Pattern |
|----------------|----------------------------|
| Frame wraps children | `flex flex-wrap` |
| Sidebar collapses on small | `hidden lg:block` or use `drawer` |
| Cards stack vertically on mobile | `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3` |
| Font size changes | `text-sm md:text-base lg:text-lg` |
| Padding changes | `p-2 md:p-4 lg:p-8` |
| Content max-width | `max-w-sm md:max-w-2xl lg:max-w-6xl` |

### Breakpoint Reference (Tailwind defaults)

| Prefix | Min-width | Typical Use |
|--------|-----------|-------------|
| (none) | 0px | Mobile-first base |
| `sm:` | 640px | Large phones / small tablets |
| `md:` | 768px | Tablets |
| `lg:` | 1024px | Laptops |
| `xl:` | 1280px | Desktops |
| `2xl:` | 1536px | Large screens |

---

## Troubleshooting

### "The Figma URL returns no data"
- Verify the URL is a valid Figma design URL (not a prototype preview link)
- Check if the node-id exists (frame may have been deleted)
- Try the file-level URL without node-id first

### "Design structure is too shallow"
- Increase `depth` parameter (try 7-10)
- Fetch a specific node URL instead of the full file

### "Can't identify the right daisyUI component"
- Look at the component's behavior, not just appearance
- Check if it's interactive (hover, click, toggle) — this narrows the component type
- When in doubt, use a `card` for contained content and `div` + Tailwind utilities for layout

### "Colors don't match exactly"
- Use daisyUI semantic colors where possible for theme consistency
- For exact colors, use Tailwind arbitrary values: `bg-[#1a2b3c]`
- Consider creating a custom theme (see `05-theme-generation-workflow.md`)

### "Layout doesn't match at all breakpoints"
- Figma designs are typically for one breakpoint — infer the rest
- Ask the user which breakpoint the Figma represents (usually desktop)
- Apply mobile-first progressive enhancement

---

## Complete Example

### Figma Design: Dashboard with Sidebar

**Step 1:** User provides: `https://www.figma.com/design/xyz/Dashboard?node-id=1-100`

**Step 2:** Fetch with depth 5

**Step 3:** Analysis reveals:
- Root frame: HORIZONTAL layout
  - Left frame: VERTICAL, 240px wide, dark background → **drawer/sidebar**
  - Right frame: VERTICAL, fills remaining space
    - Top bar: HORIZONTAL, logo + search + avatar → **navbar**
    - Stats row: HORIZONTAL, 4 equal children with numbers → **stat**
    - Content: VERTICAL, table + chart → **table** + custom

**Step 4-5:** Fetch snippets:
```
components: drawer, navbar, stat, table, menu, avatar, button
layouts: responsive-offcanvas-drawer-sidebar
templates: dashboard
```

**Step 6:** Assemble:
```html
<div class="drawer lg:drawer-open">
  <input id="sidebar" type="checkbox" class="drawer-toggle" />
  <div class="drawer-content">
    <!-- Navbar -->
    <div class="navbar bg-base-100 shadow-sm">
      <div class="navbar-start">
        <label for="sidebar" class="btn btn-ghost lg:hidden">☰</label>
      </div>
      <div class="navbar-end">
        <div class="avatar placeholder">
          <div class="bg-neutral text-neutral-content w-8 rounded-full">
            <span class="text-xs">JD</span>
          </div>
        </div>
      </div>
    </div>
    <!-- Stats -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 p-6">
      <div class="stat bg-base-100 rounded-box shadow">
        <div class="stat-title">Revenue</div>
        <div class="stat-value">$34K</div>
        <div class="stat-desc">↗ 12% from last month</div>
      </div>
      <!-- ... more stats -->
    </div>
    <!-- Table -->
    <div class="p-6">
      <div class="card bg-base-100 shadow">
        <div class="card-body">
          <table class="table">
            <!-- ... table content -->
          </table>
        </div>
      </div>
    </div>
  </div>
  <!-- Sidebar -->
  <div class="drawer-side">
    <label for="sidebar" class="drawer-overlay"></label>
    <ul class="menu bg-base-200 min-h-full w-60 p-4">
      <li><a class="active">Dashboard</a></li>
      <li><a>Analytics</a></li>
      <li><a>Settings</a></li>
    </ul>
  </div>
</div>
```

**Step 7:** Responsive — drawer is off-canvas on mobile (`lg:drawer-open`), stats reflow from 4 columns to 1.


## Steering experiences — learned from real agent usage

### Depth strategy

**Problem:** Agent uses default depth and gets either too little detail (depth 1-2) or too much noise (depth 10+) from Figma files.

**Fix:** Use this depth guide based on what you're extracting:

| Figma content | Recommended depth | Why |
|---|---|---|
| Single component (button, card) | 3–4 | Components are shallow |
| Section (hero, footer, nav) | 5–6 | Sections have nested content |
| Full page | 7–8 | Pages have deep nesting |
| Design system / component library | 3–4 per component | Iterate, don't go deep on everything |

### Node-specific URLs

**Problem:** Agent fetches an entire Figma file when only one frame is needed, resulting in massive response data.

**Fix:** Always use node-specific URLs when possible:
- Full file: `https://www.figma.com/design/abc123/My-Design` → returns everything
- Specific frame: `https://www.figma.com/design/abc123/My-Design?node-id=1-2` → returns just that node

Ask the user for the specific frame URL if they provide a full-file URL.

### Property mapping — Figma to daisyUI

When analyzing the Figma node tree, map properties like this:

| Figma property | daisyUI equivalent |
|---|---|
| `fills` with solid color | Semantic color class or theme variable |
| `cornerRadius: 8-16` | `rounded-lg` or `rounded-xl` (daisyUI components have built-in radius) |
| `layoutMode: "HORIZONTAL"` | `flex` (or daisyUI component with horizontal layout) |
| `layoutMode: "VERTICAL"` | `flex flex-col` (or card, stat, etc.) |
| `itemSpacing` | `gap-*` utility |
| `padding` | `p-*` utility (or component's built-in padding) |
| Component with "Button" in name | `btn` + appropriate variant |
| Component with "Input"/"Field" | `input` + `fieldset` wrapper |
| Component with "Card" | `card` + `card-body` |
