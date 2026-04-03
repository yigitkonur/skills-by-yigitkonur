# Prompt Chaining for Complex Tasks

> Advanced patterns for multi-step workflows with the daisyUI Blueprint MCP server.
> Each chain shows how steps feed into each other, with error recovery and execution strategy.

---

## Overview

Complex UI tasks rarely complete in a single step. Prompt chaining breaks them into discrete steps where each output becomes the next input. The daisyUI Blueprint MCP supports four primary chains:

| Chain | Steps | Best For |
|-------|-------|----------|
| [Chain 1](#chain-1-figma--components--theme--full-page) | Figma → Components → Theme → Full Page | Design handoff |
| [Chain 2](#chain-2-screenshot--analysis--snippets--assembly) | Screenshot → Analysis → Snippets → Assembly | Visual replication |
| [Chain 3](#chain-3-bootstrap--mapping--rebuild--theme) | Bootstrap → Mapping → Rebuild → Theme | Migration projects |
| [Chain 4](#chain-4-brand-image--theme--layout--components) | Brand Image → Theme → Layout → Components | Brand-first development |

---

## Chain 1: Figma → Components → Theme → Full Page

### When to Use
You have a Figma design file and need to produce a complete daisyUI page.

### Step-by-Step Flow

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Step 1: Figma   │────▶│ Step 2: Map to   │────▶│ Step 3: Extract  │────▶│ Step 4: Assemble │
│  Fetch & Parse   │     │ daisyUI Parts    │     │ Theme Colors     │     │ Full Page        │
└──────────────────┘     └──────────────────┘     └──────────────────┘     └──────────────────┘
```

#### Step 1 — Fetch Figma Design

**Tool:** `daisyui-blueprint-Figma-to-daisyUI`

```json
{
  "url": "https://www.figma.com/design/abc123/MyDesign?node-id=1-2",
  "depth": 5,
  "includeImages": false
}
```

**Output:** Design tree with frames, components, text nodes, colors, layout properties.

**What feeds forward:**
- Component names and hierarchy → Step 2
- Color values (fills, strokes) → Step 3
- Layout properties (auto-layout, spacing) → Step 4

**Error recovery:**
- `401/403` → Check Figma access token
- `404` → Verify the URL and node-id
- Shallow tree → Increase `depth` parameter
- Missing details → Fetch specific node-id for subsections

#### Step 2 — Map to daisyUI Components

**Tool:** `daisyui-blueprint-daisyUI-Snippets`

Analyze the Figma tree and identify which daisyUI components match:

| Figma Frame Name | daisyUI Component | Snippet to Fetch |
|-----------------|-------------------|-----------------|
| "Header" | `navbar` | `components.navbar` + `component-examples.navbar.*` |
| "Hero Section" | `hero` | `components.hero` + `component-examples.hero.*` |
| "Product Card" | `card` | `components.card` + `component-examples.card.*` |
| "Sidebar" | `drawer` + `menu` | `layouts.responsive-collapsible-drawer-sidebar` |

```json
{
  "components": {
    "navbar": true,
    "hero": true,
    "card": true,
    "drawer": true,
    "menu": true
  },
  "component-examples": {
    "navbar.responsive-dropdown-menu-on-small-screen-center-menu-on-large-screen": true,
    "hero.hero-with-figure": true,
    "card.card": true
  }
}
```

**What feeds forward:**
- HTML snippets for each component → Step 4
- Class name references → Step 4

**Error recovery:**
- No matching component → Use raw Tailwind utilities for custom elements
- Multiple possible matches → Fetch all candidates, compare structure

#### Step 3 — Extract Theme from Figma Colors

From the Figma design tree, extract the color tokens:

```
Figma color fills → Map to daisyUI semantic roles → Generate @plugin block
```

| Figma Color Token | Hex Value | daisyUI Role |
|------------------|-----------|-------------|
| `Primary/500` | `#6366f1` | `--color-primary` |
| `Gray/900` | `#111827` | `--color-neutral` |
| `Gray/50` | `#f9fafb` | `--color-base-100` |
| `Success/500` | `#22c55e` | `--color-success` |

Convert to OKLCH and output the theme block (see [image-to-theme-prompt.md](./image-to-theme-prompt.md)).

**What feeds forward:**
- Complete `@plugin "daisyui/theme"` CSS block → Step 4
- `data-theme` attribute value → Step 4

**Error recovery:**
- Missing colors → Use a built-in theme as fallback
- Inconsistent palette → Normalize using OKLCH lightness/chroma adjustments

#### Step 4 — Assemble Full Page

Combine the theme + layout + components:

1. Set the theme: `<html data-theme="figma-design">`
2. Build the page skeleton from the layout snippet
3. Insert component HTML into the correct positions
4. Replace placeholder content with Figma text content
5. Adjust Tailwind utilities for spacing and responsive behavior

**Error recovery:**
- Visual mismatch → Adjust spacing/sizing utilities
- Missing responsive behavior → Add breakpoint classes
- Component doesn't fit → Fall back to raw Tailwind

### Execution Strategy

| Step | Can Parallelize? | Blocking? |
|------|-----------------|-----------|
| Step 1 (Figma fetch) | No — first step | Yes |
| Step 2 (Component mapping) | **Yes** — fetch multiple snippets in one call | Blocks Step 4 |
| Step 3 (Theme extraction) | **Yes** — independent of Step 2 | Blocks Step 4 |
| Step 4 (Assembly) | No — needs Steps 2 + 3 | Final |

**Optimization:** Steps 2 and 3 can run in parallel since they depend only on Step 1's output.

---

## Chain 2: Screenshot → Analysis → Snippets → Assembly

### When to Use
You have a UI screenshot (no source code, no Figma) and need to recreate it.

### Step-by-Step Flow

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ Step 1: Visual   │────▶│ Step 2: Component│────▶│ Step 3: Snippet  │────▶│ Step 4: Build &  │
│ Analysis         │     │ Hierarchy        │     │ Retrieval        │     │ Verify           │
└──────────────────┘     └──────────────────┘     └──────────────────┘     └──────────────────┘
```

#### Step 1 — Visual Analysis

Examine the screenshot and catalog:

- **Layout grid:** How many columns? Sidebar? Header/footer?
- **Component list:** Every distinct UI element
- **Color palette:** Extract 5–8 dominant colors
- **Typography:** Heading scale, body text size
- **Spacing:** Consistent gaps and padding

**Output format:**
```
Layout: 2-column (sidebar + main), top navbar
Components: navbar, sidebar menu, stat cards (×4), data table, line chart placeholder
Colors: dark sidebar (#1e293b), white main (#ffffff), blue primary (#3b82f6)
```

**Error recovery:**
- Low resolution screenshot → Focus on layout structure over fine details
- Complex/busy UI → Break into sections and analyze each independently

#### Step 2 — Component Hierarchy

Build the DOM tree:

```
html[data-theme="..."]
└── body
    ├── drawer (sidebar)
    │   ├── drawer-content
    │   │   ├── navbar
    │   │   ├── stats grid (4 cards)
    │   │   ├── table card
    │   │   └── chart card (placeholder)
    │   └── drawer-side
    │       └── menu (vertical, with icons)
    └── (mobile: dock at bottom)
```

**What feeds forward:** Exact component names and nesting → Step 3.

#### Step 3 — Snippet Retrieval

Fetch all identified components in a single MCP call:

```json
{
  "layouts": {
    "responsive-collapsible-drawer-sidebar": true
  },
  "components": {
    "navbar": true,
    "menu": true,
    "stat": true,
    "table": true,
    "card": true,
    "dock": true
  },
  "component-examples": {
    "stat.stat-with-icons-or-image": true,
    "table.table-with-visual-elements": true,
    "menu.menu-with-icons": true,
    "dock.dock": true
  }
}
```

**Error recovery:**
- Missing component → Search for closest alternative or use raw HTML
- Too many components → Prioritize the most visible/important ones first

#### Step 4 — Build & Verify

1. Start from the layout snippet as the page skeleton
2. Insert component snippets into their positions
3. Replace placeholder content with content from the screenshot
4. Match colors — either pick a built-in theme or create a custom one
5. Verify against the screenshot:
   - [ ] Layout proportions match
   - [ ] Color tones are consistent
   - [ ] Component types are correct
   - [ ] Responsive behavior is sensible

**Error recovery:**
- Color mismatch → Generate a custom theme (Chain 4 Step 1)
- Layout doesn't fit → Switch layout template or use custom grid
- Missing interactive state → Add CSS transitions and hover states

### Execution Strategy

| Step | Can Parallelize? | Duration |
|------|-----------------|----------|
| Step 1 (Visual analysis) | No — requires human/AI review | ~30s |
| Step 2 (Hierarchy) | No — depends on Step 1 | ~15s |
| Step 3 (Snippet fetch) | **Yes** — single batch call | ~5s |
| Step 4 (Assembly) | No — final step | ~60s |

---

## Chain 3: Bootstrap → Mapping → Rebuild → Theme

### When to Use
Migrating an existing Bootstrap 5 project to daisyUI.

### Step-by-Step Flow

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ Step 1: Parse    │────▶│ Step 2: Class    │────▶│ Step 3: Rebuild  │────▶│ Step 4: Theme    │
│ Bootstrap HTML   │     │ Mapping          │     │ with daisyUI     │     │ Customization    │
└──────────────────┘     └──────────────────┘     └──────────────────┘     └──────────────────┘
```

#### Step 1 — Parse Bootstrap HTML

Analyze the provided HTML:

1. List all Bootstrap component classes used (`btn`, `card`, `modal`, `nav`, etc.)
2. List all Bootstrap utility classes (`d-flex`, `mt-3`, `text-center`, etc.)
3. Identify all `data-bs-*` attributes (JavaScript-dependent interactions)
4. Note Bootstrap grid usage (`container`, `row`, `col-*`)
5. List external Bootstrap JS plugins required

**Output format:**
```
Components: navbar, card (×6), modal (×2), table, form, dropdown, badge
Utilities: d-flex, mt-3, mb-4, text-center, fw-bold, bg-light
JS interactions: data-bs-toggle="modal", data-bs-toggle="dropdown", data-bs-dismiss
Grid: container, row, col-md-4 (×3), col-md-6 (×2), col-12
```

**Error recovery:**
- Mixed Bootstrap versions → Focus on the dominant version
- Custom Bootstrap extensions → Flag for manual review

#### Step 2 — Class Mapping

Apply the comprehensive mapping table from [bootstrap-prompt.md](./bootstrap-prompt.md):

| Category | Bootstrap Classes Found | daisyUI Replacement |
|----------|----------------------|-------------------|
| Buttons | `btn btn-primary` | `btn btn-primary` |
| Buttons | `btn btn-danger` | `btn btn-error` |
| Cards | `card`, `card-body`, `card-img-top` | `card bg-base-100 shadow-xl`, `card-body`, `figure > img` |
| Grid | `col-md-4` | `md:col-span-4` or simplified `md:grid-cols-3` |
| Utilities | `d-flex justify-content-between` | `flex justify-between` |
| JS interactions | `data-bs-toggle="modal"` | `onclick="dialog.showModal()"` |

**What feeds forward:** A transformation map for every class and attribute → Step 3.

#### Step 3 — Rebuild with daisyUI

Apply all mappings and restructure HTML where needed:

1. **Direct class swaps** — Simple find-and-replace
2. **Structural changes** — Cards need `<figure>`, modals need `<dialog>`, navbars need `navbar-start/center/end`
3. **Grid conversion** — `row` + `col-*` → `grid grid-cols-*`
4. **JS removal** — Replace `data-bs-*` with CSS-only patterns
5. **Fetch reference snippets** — Call MCP for any component you're unsure about

**Error recovery:**
- Component doesn't convert cleanly → Fetch the daisyUI component reference and rebuild from scratch
- Layout breaks → Verify grid/flex conversion, adjust responsive breakpoints
- Interactive behavior lost → Implement with `<dialog>`, `:checked`, or `<details>`

#### Step 4 — Theme Customization

If the Bootstrap project had customized Sass variables:

```scss
// Bootstrap Sass overrides (before)
$primary: #6366f1;
$secondary: #a855f7;
$success: #22c55e;
$danger: #ef4444;
$font-family-base: 'Inter', sans-serif;
$border-radius: 0.5rem;
```

Convert to a daisyUI custom theme:

```css
/* daisyUI theme (after) */
@plugin "daisyui/theme" {
  name: "migrated";
  default: true;
  --color-primary: oklch(0.55 0.22 270);
  --color-secondary: oklch(0.55 0.25 300);
  --color-success: oklch(0.72 0.19 145);
  --color-error: oklch(0.58 0.22 25);
  --radius-box: 0.5rem;
  --radius-field: 0.5rem;
  --radius-selector: 0.5rem;
  --border: 1px;
  --depth: 1;
  --noise: 0;
}
```

**Error recovery:**
- Missing Sass source → Extract colors from the rendered CSS
- Complex theme with many overrides → Focus on the 5 core semantic colors first

### Execution Strategy

| Step | Can Parallelize? |
|------|-----------------|
| Step 1 (Parse) | No — first step |
| Step 2 (Mapping) | No — depends on Step 1 |
| Step 3 (Rebuild) | **Partially** — independent page sections can be rebuilt in parallel |
| Step 4 (Theme) | **Yes** — can run in parallel with Step 3 (theme is independent of HTML structure) |

**Optimization:** Start theme conversion (Step 4) as soon as you have the color values from Step 1, while Step 2 and 3 proceed sequentially.

---

## Chain 4: Brand Image → Theme → Layout → Components

### When to Use
Building a new site from a brand image or mood board with no existing code.

### Step-by-Step Flow

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ Step 1: Image    │────▶│ Step 2: Generate │────▶│ Step 3: Select   │────▶│ Step 4: Populate │
│ Color Extraction │     │ Theme            │     │ Layout           │     │ Components       │
└──────────────────┘     └──────────────────┘     └──────────────────┘     └──────────────────┘
```

#### Step 1 — Image Color Extraction

Analyze the brand image and extract the color palette (see [image-to-theme-prompt.md](./image-to-theme-prompt.md)):

**Output:**
```
Primary:   #f97316 → oklch(0.72 0.20 50)   (warm orange)
Secondary: #7c3aed → oklch(0.50 0.25 290)  (deep purple)
Accent:    #f9a8d4 → oklch(0.80 0.10 340)  (soft pink)
Neutral:   #1e1b4b → oklch(0.20 0.08 280)  (dark navy)
Base-100:  #fef3c7 → oklch(0.96 0.04 85)   (pale cream)
Mood: warm, inviting, sunset
```

**Error recovery:**
- Monochrome image → Derive hues by shifting the single color's hue angle
- Too many colors → Pick the 3 most dominant and derive the rest

#### Step 2 — Generate Theme

Using the extracted palette, generate both light and dark theme variants:

```css
@plugin "daisyui/theme" {
  name: "brand";
  default: true;
  /* ... full color + structure variables ... */
}

@plugin "daisyui/theme" {
  name: "brand-dark";
  prefersdark: true;
  /* ... dark variant ... */
}
```

**What feeds forward:** Theme name for `data-theme` attribute → Steps 3–4.

**Error recovery:**
- Poor contrast → Adjust content color lightness values
- Colors look different on screen → Verify OKLCH conversion accuracy

#### Step 3 — Select Layout

Choose the right layout for the project type:

| Project Type | Recommended Layout |
|-------------|-------------------|
| Marketing / landing | `top-navbar` + stacked sections |
| Dashboard / admin | `responsive-collapsible-drawer-sidebar` or `responsive-offcanvas-drawer-sidebar` |
| Content / blog | `top-navbar` + `bento-grid-5-sections` |
| Portfolio | `top-navbar` + `bento-grid-8-sections` |

Fetch the layout snippet:

```json
{
  "layouts": { "responsive-collapsible-drawer-sidebar": true },
  "templates": { "dashboard": true }
}
```

**What feeds forward:** Page skeleton HTML → Step 4.

**Error recovery:**
- Layout doesn't match needs → Combine multiple layouts or build custom with Tailwind grid
- Missing sidebar items → Build menu from component snippets

#### Step 4 — Populate Components

Fill the layout with themed components:

1. Identify each content region in the layout
2. Select the appropriate component for each region
3. Fetch component snippets in batch
4. Insert into the layout skeleton
5. Replace placeholder content with actual content

```json
{
  "components": {
    "stat": true,
    "card": true,
    "table": true,
    "menu": true,
    "navbar": true
  },
  "component-examples": {
    "stat.stat-with-icons-or-image": true,
    "card.card-with-no-image": true,
    "table.table-with-visual-elements": true,
    "menu.menu-with-icons-and-badge-responsive": true
  }
}
```

**Error recovery:**
- Component looks off with custom theme → Adjust theme variables (border, depth, radius)
- Content overflow → Adjust card/table sizing with Tailwind utilities
- Missing component type → Check all 47 available components

### Execution Strategy

| Step | Can Parallelize? |
|------|-----------------|
| Step 1 (Extract) | No — first step |
| Step 2 (Theme) | No — depends on Step 1 |
| Step 3 (Layout) | **Yes** — can run in parallel with Step 2 (layout choice is independent of exact theme) |
| Step 4 (Components) | No — needs Steps 2 + 3 |

**Optimization:** Decide on layout (Step 3) while the theme is being generated (Step 2).

---

## Error Recovery Reference

### Common Errors Across All Chains

| Error | Recovery |
|-------|----------|
| **MCP tool returns empty** | Verify parameter names (check available components list) |
| **Component doesn't exist** | Use the closest alternative + raw Tailwind |
| **Theme colors look wrong** | Verify OKLCH conversion; check contrast ratios |
| **Layout breaks on mobile** | Add responsive breakpoint classes; test at 320px, 768px, 1024px |
| **Interactive element doesn't work** | Verify CSS-only mechanism (checkbox toggle, `<dialog>`, `<details>`) |
| **Multiple themes conflict** | Ensure `data-theme` is set at the correct DOM level |

### Retry Strategies

```
Failure → Check error message → Adjust parameters → Retry
   │                                                  │
   └── After 2 retries ──────────────────────────────┘
          │
          ▼
   Fall back to alternative:
   - Different component
   - Different layout
   - Raw Tailwind utilities
   - Built-in theme instead of custom
```

---

## Parallel vs Sequential Decision Guide

| Situation | Strategy |
|-----------|----------|
| Fetching multiple component snippets | **Parallel** — single batch MCP call |
| Theme + Layout selection | **Parallel** — independent decisions |
| Figma fetch + snippet fetch | **Sequential** — snippets depend on Figma analysis |
| Multiple page sections | **Parallel** — if sections don't share state |
| Color extraction + contrast checking | **Sequential** — checking depends on extraction |
| Light theme + dark theme generation | **Parallel** — both derive from same palette |
| Bootstrap parsing + mapping | **Sequential** — mapping depends on parsing |

### Performance Tips

1. **Batch MCP calls:** Always request all needed components, examples, layouts, and themes in a single call.
2. **Parallelize independent steps:** Theme generation and layout selection often don't depend on each other.
3. **Cache component references:** If you've fetched `components.card`, don't fetch it again in the same session.
4. **Start with templates:** The `dashboard` and `login-form` templates provide pre-built pages that need less assembly.

---

## Combining Chains

Chains can be composed for complex projects:

### Full Rebrand Migration

```
Chain 4 (Step 1-2): Brand image → Custom theme
         ↓
Chain 3 (Step 1-3): Bootstrap code → daisyUI rebuild
         ↓
Chain 3 (Step 4): Apply the custom theme from Chain 4
```

### Design-to-Code with Enhancement

```
Chain 1 (Step 1-4): Figma design → daisyUI page
         ↓
Chain 2 (Step 1): Screenshot the result → Visual QA
         ↓
Iterate: Fix any visual discrepancies
```

### Screenshot Inspired New Build

```
Chain 2 (Step 1-2): Screenshot → Component analysis (reference only)
         ↓
Chain 4 (Step 1-4): Brand image → Full build (inspired by screenshot)
```
