# Screenshot/Image to daisyUI Code Workflow

> Convert any UI screenshot or mockup image into production-ready daisyUI + Tailwind CSS code.

---

## Quick Reference

| Step | Action | Tool |
|------|--------|------|
| 1 | Receive screenshot from user | — |
| 2 | Visually analyze the image | Vision/Analysis |
| 3 | Identify UI component patterns | — |
| 4 | Fetch component snippets | `daisyui-blueprint-daisyUI-Snippets` |
| 5 | Fetch component examples | `daisyui-blueprint-daisyUI-Snippets` (component-examples) |
| 6 | Assemble page HTML | — |
| 7 | Fine-tune colors and spacing | — |

---

## Step 1: Receive the Screenshot

Accept images in any format. Ask the user:
- **What page/section is this?** (helps prioritize which components to match)
- **Is this mobile, tablet, or desktop?** (determines base breakpoint)
- **Any specific interactions?** (dropdowns, modals, tabs — not visible in screenshots)

---

## Step 2: Visual Analysis

Systematically scan the screenshot in this order:

### Top-to-Bottom Scan
1. **Top section** — Navigation bar? Header? Breadcrumbs?
2. **Hero/Banner area** — Large hero section? Image overlay?
3. **Main content** — Cards? Tables? Forms? Text content?
4. **Sidebar** — Side navigation? Filters? Widgets?
5. **Bottom section** — Footer? Dock? Pagination?

### Identify Layout Structure
```
┌─────────────────────────────────────────┐
│  Navbar (full width)                     │
├────────┬────────────────────────────────┤
│        │                                │
│ Sidebar│    Main Content Area           │
│  (nav) │    (cards, tables, forms)      │
│        │                                │
├────────┴────────────────────────────────┤
│  Footer (full width)                     │
└─────────────────────────────────────────┘
```

### Catalog Visual Elements

For each element, note:
- **Type**: Button, input, card, badge, etc.
- **Variant**: Filled, outline, ghost
- **Size**: xs, sm, md, lg
- **Color**: primary, secondary, neutral, etc.
- **State**: Active, disabled, loading, hover

---

## Step 3: Map to daisyUI Components

### Pattern Recognition Guide

| What You See | daisyUI Component | Fetch Snippet |
|-------------|-------------------|---------------|
| Horizontal bar with logo + links + avatar | `navbar` | `components.navbar` |
| Vertical list of nav links with icons | `menu` | `components.menu` |
| Box with image, title, text, button | `card` | `components.card` |
| Small colored label/tag | `badge` | `components.badge` |
| Round profile picture | `avatar` | `components.avatar` |
| Clickable button | `button` | `components.button` |
| Text input with label | `input` + `label` or `fieldset` | `components.input`, `components.fieldset` |
| Dropdown selector | `select` or `dropdown` | `components.select` |
| On/off switch | `toggle` | `components.toggle` |
| Checkbox with label | `checkbox` | `components.checkbox` |
| Radio button group | `radio` | `components.radio` |
| Popup/overlay dialog | `modal` | `components.modal` |
| Slide-over panel | `drawer` | `components.drawer` |
| Tab navigation | `tab` | `components.tab` |
| Data table with rows | `table` | `components.table` |
| Notification banner | `alert` | `components.alert` |
| Corner notification | `toast` + `alert` | `components.toast` |
| Number statistics | `stat` | `components.stat` |
| Expandable section | `collapse` / `accordion` | `components.accordion` |
| Star rating | `rating` | `components.rating` |
| Progress bar | `progress` | `components.progress` |
| Circular progress | `radial-progress` | `components.radial-progress` |
| Step indicator | `steps` | `components.steps` |
| Breadcrumb trail | `breadcrumbs` | `components.breadcrumbs` |
| Page numbers | `pagination` (join + button) | `components.join` |
| Image carousel | `carousel` | `components.carousel` |
| Chat bubbles | `chat` | `components.chat` |
| Timeline / history | `timeline` | `components.timeline` |
| Bottom mobile nav | `dock` | `components.dock` |
| Content skeleton | `skeleton` | `components.skeleton` |
| Loading spinner | `loading` | `components.loading` |
| Divider line | `divider` | `components.divider` |
| Footer with columns | `footer` | `components.footer` |
| Hero banner | `hero` | `components.hero` |

---

## Step 4: Fetch Component Snippets

Fetch base component definitions for all identified components:

```
Tool: daisyui-blueprint-daisyUI-Snippets
Parameters:
  components:
    navbar: true
    card: true
    button: true
    badge: true
    # ... all identified components
```

This returns class names, modifiers, parts, and available variants for each component.

---

## Step 5: Fetch Component Examples

For complex components, also fetch specific examples that match what you see:

```
Tool: daisyui-blueprint-daisyUI-Snippets
Parameters:
  component-examples:
    # Navbar with dropdown and responsive hamburger
    navbar.responsive-dropdown-menu-on-small-screen-center-menu-on-large-screen: true

    # Card with image and badge
    card.card-with-badge: true

    # Table with visual elements
    table.table-with-visual-elements: true

    # Input with icon and validation
    input.email-input-with-icon-and-validator: true
```

### Example Selection Guide

| Screenshot Shows | Best Example to Fetch |
|------------------|-----------------------|
| Navbar with hamburger menu on mobile | `navbar.responsive-dropdown-menu-on-small-screen-center-menu-on-large-screen` |
| Navbar with search bar | `navbar.navbar-with-search-input-and-dropdown` |
| Card with side image | `card.card-with-image-on-side` |
| Card that stacks on mobile | `card.responsive-card-vertical-on-small-screen-horizontal-on-large-screen` |
| Pricing card | `card.pricing-card` |
| Table with avatars and badges | `table.table-with-visual-elements` |
| Tabs with content panels | `tab.radio-tabs-lift-tab-content` |
| Sidebar that collapses | `drawer.responsive-sidebar-is-always-visible-on-large-screen-can-be-toggled-on-small-screen` |
| Menu with icons and badges | `menu.menu-with-icons-and-badge-responsive` |
| Collapsible sidebar with icons only when closed | `drawer.icon-only-drawer-sidebar-when-its-closed-using-is-drawer-close-and-is-drawer-open-variants` |
| Login form | `fieldset.login-form-with-fieldset` |
| Chat with avatars and timestamps | `chat.chat-with-image-header-and-footer` |
| Stat cards | `stat.stat-with-icons-or-image` |
| Steps / wizard | `steps.with-custom-content-in-step-icon` |
| Hero with form | `hero.hero-with-form` |
| Footer with newsletter | `footer.footer-with-a-form` |

---

## Step 6: Assemble the Page

### Assembly Strategy

1. **Start with the layout shell:**
   ```html
   <!-- If page has sidebar -->
   <div class="drawer lg:drawer-open">
     <input id="drawer" type="checkbox" class="drawer-toggle" />
     <div class="drawer-content">
       <!-- navbar + main content here -->
     </div>
     <div class="drawer-side">
       <!-- sidebar menu here -->
     </div>
   </div>

   <!-- If page is simple (no sidebar) -->
   <div class="min-h-screen bg-base-200">
     <!-- navbar -->
     <!-- content -->
     <!-- footer -->
   </div>
   ```

2. **Add the navbar:**
   Place at top of `drawer-content` or page root.

3. **Build content sections:**
   Use Tailwind grid/flex to match the screenshot's layout.

4. **Insert daisyUI components:**
   Replace placeholder sections with actual component HTML from snippets.

5. **Add content:**
   Fill in text, images, icons matching the screenshot.

### Spacing Estimation from Screenshots

Since exact pixel values aren't available from screenshots, use this heuristic:

| Visual Spacing | Tailwind Class | Pixels |
|----------------|----------------|--------|
| Tight/none | `gap-1`, `p-1` | 4px |
| Small | `gap-2`, `p-2` | 8px |
| Normal | `gap-4`, `p-4` | 16px |
| Comfortable | `gap-6`, `p-6` | 24px |
| Spacious | `gap-8`, `p-8` | 32px |
| Very spacious | `gap-12`, `p-12` | 48px |

---

## Step 7: Fine-Tune Colors

### Map Screenshot Colors to daisyUI Semantic Colors

| Observed Color Usage | daisyUI Semantic Name |
|---------------------|----------------------|
| Main brand / CTA button color | `primary` |
| Supporting / secondary actions | `secondary` |
| Highlight / accent color | `accent` |
| Dark backgrounds / text containers | `neutral` |
| Page background (lightest) | `base-100` |
| Card/section background | `base-200` |
| Divider / border backgrounds | `base-300` |
| Main text color | `base-content` |
| Informational elements (blue-ish) | `info` |
| Success states (green-ish) | `success` |
| Warning states (yellow/orange) | `warning` |
| Error states (red-ish) | `error` |

### When Colors Don't Fit Semantic Names

Use Tailwind's utility classes:
```html
<!-- Custom background -->
<div class="bg-[#1a1a2e]">

<!-- Custom text color -->
<span class="text-[#e94560]">

<!-- Custom with opacity -->
<div class="bg-[#1a1a2e]/80">
```

Or generate a custom theme — see `05-theme-generation-workflow.md`.

---

## Tips for Accuracy

### Do's
- ✅ Identify the **overall page layout** before individual components
- ✅ Use daisyUI **semantic classes** over raw Tailwind when a component exists
- ✅ Fetch **component-examples** for the closest matching pattern
- ✅ Ask the user about **interactive behavior** not visible in screenshots
- ✅ Use **responsive patterns** even if only one breakpoint is shown
- ✅ Match the **visual hierarchy** (heading sizes, color weight, spacing)

### Don'ts
- ❌ Don't recreate every pixel — match the **spirit** of the design
- ❌ Don't use raw Tailwind for things daisyUI already handles (buttons, cards, etc.)
- ❌ Don't guess at hover/active states — use daisyUI defaults or ask
- ❌ Don't hardcode widths — use responsive/fluid sizing
- ❌ Don't ignore the theme — map colors semantically for easy theme switching

### Handling Ambiguous Elements

| Ambiguity | Resolution Strategy |
|-----------|-------------------|
| Is it a card or just a bordered div? | If it has title + content + actions → `card`. Otherwise → `div` with border |
| Dropdown or select? | Native OS dropdown → `select`. Custom styled dropdown → `dropdown` |
| Is the sidebar persistent or toggleable? | Desktop: likely persistent. Check for a hamburger icon → toggleable on mobile |
| Tabs or segmented buttons? | Content changes below → `tab`. Just filtering → `filter` or `join` + radio |
| Modal or page? | Has overlay/backdrop → `modal`. Inline content → regular section |
| Badge or button? | Clickable → `btn btn-xs`. Label only → `badge` |

---

## Common Page Patterns

### Dashboard Screenshot
```
Components needed: drawer, navbar, menu, stat, card, table, button, avatar, badge
Layout: responsive-offcanvas-drawer-sidebar or responsive-collapsible-drawer-sidebar
Template: dashboard
```

### E-commerce Product Page
```
Components needed: navbar, carousel, card, badge, rating, button, breadcrumbs, footer, tab
Layout: top-navbar
```

### Blog / Article Page
```
Components needed: navbar, breadcrumbs, card, avatar, badge, pagination, footer, divider
Layout: top-navbar
```

### Settings / Admin Page
```
Components needed: navbar, drawer, menu, tab, fieldset, input, select, toggle, checkbox, button
Layout: responsive-collapsible-drawer-sidebar
```

### Landing Page
```
Components needed: navbar, hero, card, stat, steps, carousel, footer, button
Layout: top-navbar
```

### Chat Application
```
Components needed: drawer, navbar, chat, avatar, input, button, badge, menu, divider
Layout: responsive-offcanvas-drawer-sidebar
```


## Steering experiences — learned from real agent usage

### Non-daisyUI elements in screenshots

**Problem:** Agent sees a chart, map, or video player in a screenshot and tries to recreate it with daisyUI stat/progress/radial-progress components. The result looks nothing like the original.

**Fix:** Identify non-daisyUI elements early in the scan phase:
1. Charts/graphs → mark as `<!-- TODO: [Chart.js/Recharts] chart -->`
2. Maps → mark as `<!-- TODO: [Leaflet/Mapbox] map -->`
3. Code blocks → mark as `<!-- TODO: syntax-highlighted code block -->`
4. Video/audio → mark as `<!-- TODO: HTML5 video/audio player -->`

Wrap each in a `card` or sized `div` with `bg-base-200` placeholder:

```html
<div class="card bg-base-100 card-border">
  <div class="card-body">
    <h3 class="card-title">Monthly Revenue</h3>
    <div class="h-64 w-full bg-base-200 rounded-lg flex items-center justify-center">
      <!-- TODO: integrate Recharts area chart -->
      <span class="text-base-content/40">Chart placeholder</span>
    </div>
  </div>
</div>
```

### Shell identification before component catalog

**Problem:** Agent jumps straight to cataloging individual components from a screenshot without first identifying the overall page structure. This leads to a bottom-up build that doesn't fit together.

**Fix:** Always identify the page shell FIRST:
1. Is there a sidebar? → drawer layout
2. Is there a top navbar only? → top-navbar layout
3. Is it a centered single-column? → likely a template (login, landing)
4. Is it a dashboard with sidebar + top bar? → drawer + navbar

Then check if a `template` or `layout` matches before building from scratch.

### Batch strategy for screenshot conversion

When converting a screenshot, batch MCP fetches by what you see:

```
Step 1: Identify shell → fetch matching template/layout (1 call)
Step 2: List all visible components → fetch components reference for class validation (1 call, ~6-8 items)
Step 3: Fetch examples for complex components only (1 call, ~4-6 items)
```

Target: ≤3 MCP calls total for a full-page screenshot conversion.
