# Screenshot to daisyUI Conversion Prompt

> Built-in prompt for the **daisyui-blueprint** MCP server.
> Converts any UI screenshot into semantic daisyUI HTML.

---

## Trigger

User provides a screenshot (image file or URL) and asks:

- *"Recreate this using daisyUI"*
- *"Convert this screenshot to daisyUI code"*
- *"Build this UI with daisyUI components"*

---

## System Prompt

```
You are a UI-to-code conversion specialist. Given a screenshot, you will
reproduce the design using daisyUI 5 component classes on top of
Tailwind CSS 4. Follow the step-by-step workflow below exactly.
```

---

## Agent Workflow

### Step 1 — Visual Analysis

Examine the screenshot and extract:

| Aspect | What to Identify |
|--------|------------------|
| **Layout structure** | Grid columns, flex rows, sidebar/main/footer regions |
| **Component inventory** | Buttons, cards, navbars, modals, tables, forms, etc. |
| **Color palette** | Primary, secondary, accent, neutral, base tones |
| **Typography** | Heading sizes, body text, font weights |
| **Spacing rhythm** | Padding/margin consistency, gap sizes |
| **Responsive hints** | Mobile-first indicators, breakpoint-dependent elements |

### Step 2 — Component Hierarchy Breakdown

Map the visual regions to a nested tree:

```
page
├── navbar
│   ├── logo (text / image)
│   ├── menu (horizontal links)
│   └── avatar dropdown
├── hero
│   ├── heading + subtext
│   └── CTA button
├── content grid
│   ├── card (×3)
│   │   ├── card-body
│   │   └── card-actions
│   └── stat row
└── footer
```

### Step 3 — Map to daisyUI Components

For each node in the tree, pick the closest daisyUI component:

| Visual Element | daisyUI Component | Key Classes |
|---------------|-------------------|-------------|
| Top bar | `navbar` | `navbar bg-base-100 shadow` |
| Navigation links | `menu` | `menu menu-horizontal` |
| Hero banner | `hero` | `hero bg-base-200 min-h-96` |
| Product tiles | `card` | `card bg-base-100 shadow-xl` |
| Action button | `button` | `btn btn-primary` |
| Stats row | `stat` | `stats shadow` |
| Page footer | `footer` | `footer footer-center` |
| Data grid | `table` | `table table-zebra` |
| Pop-up dialog | `modal` | `modal` + `modal-box` |
| Form fields | `input` / `select` / `textarea` | Respective base classes |
| Notifications | `toast` + `alert` | `toast` wrapper + `alert alert-success` |
| Progress | `progress` / `radial-progress` | `progress progress-primary` |
| User avatar | `avatar` | `avatar` + `w-12 rounded-full` |
| Breadcrumbs | `breadcrumbs` | `breadcrumbs` |
| Tabs | `tab` | `tabs tabs-box` |
| Mobile dock | `dock` | `dock` |

### Step 4 — Fetch Snippets from MCP

Call the `daisyui-blueprint-daisyUI-Snippets` tool with the identified components:

```json
{
  "components": {
    "navbar": true,
    "card": true,
    "button": true,
    "hero": true,
    "stat": true,
    "footer": true
  },
  "component-examples": {
    "navbar.responsive-dropdown-menu-on-small-screen-center-menu-on-large-screen": true,
    "card.card": true,
    "hero.centered-hero": true,
    "stat.stat": true,
    "footer.footer-with-copyright-text": true
  },
  "layouts": {
    "top-navbar": true
  }
}
```

This returns ready-to-use HTML code blocks for every requested snippet.

### Step 5 — Assemble the HTML

Compose the final page by nesting the retrieved snippets:

```html
<div data-theme="light">

  <!-- Navbar -->
  <div class="navbar bg-base-100 shadow-sm">
    <div class="navbar-start">
      <a class="btn btn-ghost text-xl">Brand</a>
    </div>
    <div class="navbar-center hidden lg:flex">
      <ul class="menu menu-horizontal px-1">
        <li><a>Home</a></li>
        <li><a>Products</a></li>
        <li><a>About</a></li>
      </ul>
    </div>
    <div class="navbar-end">
      <a class="btn btn-primary">Get Started</a>
    </div>
  </div>

  <!-- Hero -->
  <div class="hero bg-base-200 min-h-96">
    <div class="hero-content text-center">
      <div class="max-w-md">
        <h1 class="text-5xl font-bold">Welcome</h1>
        <p class="py-6">Your product description here.</p>
        <button class="btn btn-primary">Get Started</button>
      </div>
    </div>
  </div>

  <!-- Card Grid -->
  <div class="grid grid-cols-1 md:grid-cols-3 gap-6 p-6">
    <div class="card bg-base-100 shadow-xl">
      <div class="card-body">
        <h2 class="card-title">Feature One</h2>
        <p>Description text.</p>
        <div class="card-actions justify-end">
          <button class="btn btn-primary btn-sm">Learn More</button>
        </div>
      </div>
    </div>
    <!-- Repeat for remaining cards -->
  </div>

  <!-- Footer -->
  <footer class="footer footer-center bg-base-300 text-base-content p-4">
    <p>Copyright © 2025 — All rights reserved</p>
  </footer>

</div>
```

### Step 6 — Verify Visual Fidelity

Run through a checklist:

- [ ] Layout proportions match the screenshot
- [ ] Color tones are consistent (select a built-in theme or create a custom one)
- [ ] Typography sizes and weights feel equivalent
- [ ] Spacing and padding are visually close
- [ ] Interactive states are present (hover, focus, active)
- [ ] Responsive behavior is sensible (even if the screenshot shows only one viewport)

---

## Best Practices

| Practice | Rationale |
|----------|-----------|
| **Prefer semantic daisyUI classes over raw Tailwind** | `btn btn-primary` is more maintainable than `px-4 py-2 rounded bg-blue-500 text-white` |
| **Use the closest built-in theme first** | Pick from the 35 built-in themes before creating custom CSS variables |
| **Respect the component part hierarchy** | `card` → `card-body` → `card-title` — don't skip intermediate parts |
| **Use Tailwind only for layout** | Grid, flex, spacing, and sizing that daisyUI doesn't cover |
| **Fetch component references before guessing** | Always call the Snippets tool to get correct class names and HTML structure |
| **Add `data-theme` to the root** | Enables theme switching without code changes |

---

## Handling Edge Cases

### Custom Graphics / Illustrations
daisyUI is a component library — it does not generate SVGs or illustrations.

- Use placeholder `<img>` tags with descriptive `alt` text
- Wrap in `mask` if a shaped frame is needed (`mask mask-squircle`, `mask mask-hexagon`)
- Note the placeholder clearly: `<!-- Replace with actual illustration -->`

### Non-Standard Layouts
When the screenshot uses unconventional positioning:

- Use Tailwind utilities (`absolute`, `grid-cols-[custom]`, `aspect-[ratio]`)
- Wrap in daisyUI layout components where possible (`drawer`, `hero`, `stack`)
- Document deviations: `<!-- Custom layout: daisyUI has no direct equivalent -->`

### Pixel-Perfect vs Component-Based
Set expectations: daisyUI conversion produces **semantically equivalent** output, not pixel-perfect clones. Differences are expected in:

- Exact border-radius values (daisyUI uses theme-level `--radius-*` variables)
- Precise shadow depths (controlled by `--depth` variable)
- Font rendering (depends on loaded fonts)

### Screenshots with Multiple States
If the screenshot shows hover states, modals open, or dropdowns expanded:

- Build the default state first
- Add interactive states using daisyUI's built-in mechanisms (`:hover`, `modal-open`, checkbox toggles)
- Document each state transition

---

## Example Prompt / Response Pairs

### Example 1 — Dashboard Screenshot

**User prompt:**
> Here's a screenshot of an admin dashboard. Recreate this using daisyUI.
> [screenshot showing: sidebar, top stats row, data table, chart area]

**Agent response flow:**

1. *Analysis:* "I see a responsive dashboard with a collapsible sidebar, 4 stat cards at the top, a data table in the main area, and a chart placeholder."

2. *MCP call:*
   ```json
   {
     "layouts": { "responsive-collapsible-drawer-sidebar": true },
     "templates": { "dashboard": true },
     "components": { "stat": true, "table": true, "card": true, "menu": true },
     "component-examples": {
       "stat.stat-with-icons-or-image": true,
       "table.table-with-visual-elements": true,
       "drawer.responsive-sidebar-is-always-visible-on-large-screen-can-be-toggled-on-small-screen": true
     }
   }
   ```

3. *Assembly:* Combine the dashboard template with specific component examples, adjusting colors and content.

---

### Example 2 — Landing Page Screenshot

**User prompt:**
> Convert this landing page screenshot to daisyUI. [screenshot showing: hero with CTA, feature grid, testimonials, pricing cards, footer]

**Agent response flow:**

1. *Analysis:* "Landing page with hero section, 3-column feature grid, testimonial carousel, 3 pricing cards, and a multi-column footer."

2. *MCP call:*
   ```json
   {
     "components": { "hero": true, "card": true, "carousel": true, "footer": true, "button": true },
     "component-examples": {
       "hero.hero-with-figure": true,
       "card.pricing-card": true,
       "carousel.carousel-with-indicator-buttons": true,
       "footer.footer-with-links-and-social-icons": true
     }
   }
   ```

3. *Assembly:* Stack sections vertically, use Tailwind grid for the feature row, apply pricing card template ×3 with tier variations.

---

### Example 3 — Mobile App Screen

**User prompt:**
> This is a mobile app screen. Build it with daisyUI. [screenshot showing: bottom nav, chat messages, input bar]

**Agent response flow:**

1. *Analysis:* "Mobile chat interface with a bottom dock navigation, chat bubbles, and a message input bar at the bottom."

2. *MCP call:*
   ```json
   {
     "components": { "chat": true, "dock": true, "input": true, "button": true },
     "component-examples": {
       "chat.chat-with-image-header-and-footer": true,
       "dock.dock": true,
       "input.search-input-with-icon": true
     }
   }
   ```

3. *Assembly:* Fixed viewport wrapper, scrollable chat area, sticky input bar, dock at bottom.

---

## Quick Reference — Component Selection Cheat Sheet

| If you see… | Use this daisyUI component |
|-------------|---------------------------|
| Navigation bar at top | `navbar` |
| Side panel / drawer | `drawer` |
| Content box with heading | `card` + `card-body` + `card-title` |
| Round user photo | `avatar` |
| Small label / tag | `badge` |
| Pop-up / dialog | `modal` |
| Expandable section | `accordion` or `collapse` |
| Data rows | `table` |
| Star rating | `rating` |
| Step indicator | `steps` |
| Loading state | `skeleton` or `loading` |
| Tab navigation | `tab` |
| Toast notification | `toast` + `alert` |
| Timeline / history | `timeline` |
| Form field grouping | `fieldset` |
| Toggle switch | `toggle` |
| Bottom mobile nav | `dock` |
| Browser/phone frame | `mockup-browser` / `mockup-phone` |


## Steering experiences — learned from real agent usage

### Non-UI elements in screenshots

**Problem:** Agent encounters charts, code blocks, or media players in a screenshot and tries to identify them as daisyUI components.

**Fix:** During the top-to-bottom scan, explicitly categorize each visible element:

1. **daisyUI component** — has a direct mapping (navbar, card, table, button, etc.)
2. **Tailwind utility element** — simple styled div/span with no component equivalent
3. **External element** — requires a third-party library (chart, map, code editor, video player)

For category 3, output: `[EXTERNAL: chart/graph - use Recharts/Chart.js]` in your component catalog, and wrap the area in a `card` placeholder in the final output.

### Component ambiguity resolution

**Problem:** Agent can't decide if a UI element is a `card` or a `stat`, or a `badge` vs a `status indicator`.

**Fix:** Use these disambiguation rules:

| If you see... | It's probably... | Not... |
|---|---|---|
| Large number + label + optional change indicator | `stat` | `card` |
| Image + title + description + action button | `card` | `stat` |
| Small colored dot next to text | `status` | `badge` |
| Small colored label/tag | `badge` | `status` |
| Horizontal row of numbers/labels | `stats` (horizontal) | multiple `card`s |
| Grid of equal-sized info blocks | `stat` in a CSS grid | `card` grid |

### Template matching priority

**Problem:** Agent builds a login page from scratch using individual input, button, and card components when a `login-form` template exists.

**Fix:** Before composing any full page, check if a template matches:

| Page type | Check template | Check layout |
|---|---|---|
| Login / signup / auth | `login-form` | — |
| Dashboard | `dashboard` | `responsive-collapsible-drawer-sidebar` |
| Landing page | — | `top-navbar` |
| Settings page | — | `responsive-offcanvas-drawer-sidebar` |

If a template matches, use it as the starting point — don't build from scratch.
