# How to Write Effective Prompts for daisyUI Blueprint

> A practical guide for getting the best results from the daisyUI Blueprint MCP server.

---

## Core Principles

1. **Be specific about what you want** — Name the components, layout, and theme.
2. **Describe the purpose** — "a pricing page" gives more context than "some cards."
3. **Mention constraints** — Responsive behavior, theme, specific components to use.
4. **Iterate** — Start broad, then refine details in follow-up prompts.

---

## Natural Language Patterns That Work

### Pattern 1: Component + Context

> "Create a **[component]** for **[use case]** using daisyUI"

**Examples:**
- "Create a **navbar** for a **SaaS dashboard** using daisyUI"
- "Create a **pricing card** for a **3-tier subscription model** using daisyUI"
- "Create a **login form** with **email and password fields** using daisyUI"
- "Create a **data table** for **user management** using daisyUI"

### Pattern 2: Page Layout

> "Build a **[page type]** with **[layout description]**"

**Examples:**
- "Build a **landing page** with **hero, feature grid, testimonials, and footer**"
- "Build a **dashboard** with **sidebar navigation and stat cards**"
- "Build a **settings page** with **tabbed sections for profile, security, and notifications**"
- "Build a **blog layout** with **main content area and right sidebar**"

### Pattern 3: Conversion

> "Convert this **[source format]** to daisyUI"

**Examples:**
- "Convert this **Bootstrap navbar** to daisyUI"
- "Convert this **Tailwind card** to use daisyUI components"
- "Convert this **Figma design** to daisyUI" (with Figma URL)
- "Convert this **screenshot** to daisyUI code" (with attached image)

### Pattern 4: Theme Generation

> "Generate a **[mood/style]** daisyUI theme"

**Examples:**
- "Generate a **cyberpunk-themed** color palette for daisyUI"
- "Generate a **warm, earthy** daisyUI theme from this brand image"
- "Generate a **professional dark mode** theme for a fintech app"
- "Generate a **playful, colorful** theme for a children's education app"

### Pattern 5: Specific Requirements

> "Create **[thing]** that is **[requirement 1]**, **[requirement 2]**, and **[requirement 3]**"

**Examples:**
- "Create a **card grid** that is **responsive**, **has image overlays**, and **uses the cyberpunk theme**"
- "Create a **form** that is **validated**, **uses floating labels**, and **fits in a modal**"
- "Create a **navigation** that is **collapsible on mobile**, **has dropdown menus**, and **shows active state**"

---

## Good Prompt Examples

### ✅ Excellent Prompts

```
"Create a pricing page with 3 cards using daisyUI. Include a free tier,
a pro tier with a 'Most Popular' badge, and an enterprise tier. Each card
should list 5 features with checkmarks. Use the 'corporate' theme."
```

**Why it works:** Specific component (card), count (3), content structure (5 features), visual element (badge), and theme specified.

---

```
"Build a responsive dashboard with:
- Collapsible sidebar with icon-only mode on mobile
- Top navbar with search input and avatar dropdown
- Stats row showing 4 metrics
- Data table with zebra striping and hover
Use the dark theme."
```

**Why it works:** Clear layout structure, specific component variants, responsive behavior, and theme.

---

```
"Convert this Bootstrap 5 navbar to daisyUI. It has a brand logo on the left,
5 navigation links in the center (with one dropdown), and a sign-in button on
the right. On mobile it should collapse into a hamburger menu."
```

**Why it works:** Source format, layout specifics, interaction behavior, and responsive requirement.

---

```
"Generate a cyberpunk-themed color palette for daisyUI with:
- Neon pink primary
- Electric blue secondary
- Bright yellow accent
- Very dark background (base-100)
- High border radius, no noise, medium depth
Output the full @plugin CSS block."
```

**Why it works:** Color intent for each role, mood variables, output format specified.

---

### ❌ Vague Prompts (and How to Improve)

| Vague Prompt | Better Version |
|-------------|----------------|
| "Make me a website" | "Build a landing page with hero section, 3 feature cards, and footer using daisyUI" |
| "Create a button" | "Show all button variants in daisyUI: primary, secondary, outline, ghost, and sizes" |
| "Make it look good" | "Apply the 'sunset' theme and use soft border radius with shadow depth 1" |
| "Fix the layout" | "Make this card grid responsive: 1 column on mobile, 2 on tablet, 3 on desktop" |
| "Add some colors" | "Create a custom theme with ocean blue primary, teal secondary, coral accent" |

---

## Component-Specific Prompting Tips

### Cards

Mention: size variant, image placement (top/side/overlay), whether it needs badge, action buttons.

```
"Create a horizontal card with image on the left side, title and description
in the body, and a 'Learn More' button in card-actions. Make it responsive —
stacked vertically on mobile."
```

### Navbar

Mention: logo position, menu style (horizontal/dropdown), responsive behavior, theme.

```
"Create a navbar with the brand name on the left, horizontal menu links in
the center (hidden on mobile, replaced by a dropdown hamburger), and a
notification bell icon + avatar on the right."
```

### Tables

Mention: data type, features (zebra, hover, pin-rows), whether it has visual elements.

```
"Create a data table for a user list with columns: avatar, name, email, role
(as a badge), status (as a toggle), and an actions dropdown. Use zebra
striping and pin the header row."
```

### Forms

Mention: fields, validation, layout (vertical/horizontal), submit behavior.

```
"Create a registration form inside a card with: username (with icon),
email (with validation), password (with requirements validator), a terms
checkbox, and a submit button. Use fieldset grouping."
```

### Modals

Mention: trigger, content, actions, close behavior.

```
"Create a confirmation modal triggered by a delete button. The modal should
show a warning icon, confirmation text, and two actions: Cancel (ghost) and
Delete (error color). Close when clicking outside."
```

### Themes

Mention: mood, specific colors, structural variables, light/dark.

```
"Create both light and dark variants of a theme called 'midnight'. Use deep
indigo primary, silver secondary, gold accent. The dark variant should use
very dark blue-gray backgrounds. Sharp corners (small radius), thin borders."
```

---

## Combining Multiple Workflow Types

You can chain different capabilities in a single conversation:

### Example: Full Page from Scratch

```
Step 1: "Generate a warm 'café' theme with brown primary, cream base,
         and gold accent"
Step 2: "Now build a restaurant landing page using that theme with:
         - Navbar with logo and reservation button
         - Hero with background image overlay
         - Menu section with card grid (food items)
         - Testimonial carousel
         - Footer with social links"
Step 3: "Make the food item cards show a badge for 'Chef's Special' items"
```

### Example: Migration + Enhancement

```
Step 1: "Convert this Bootstrap admin dashboard to daisyUI"
         [paste Bootstrap HTML]
Step 2: "Now apply the 'business' built-in theme instead of the default"
Step 3: "Replace the plain table with a daisyUI table that has visual
         elements: avatars in the first column and badges for status"
```

### Example: Design System Extraction

```
Step 1: "Create a custom theme from this brand image" [attach image]
Step 2: "Show me all button variants (primary, secondary, outline, ghost,
         sizes) with this theme"
Step 3: "Now create a component library page showing cards, alerts, badges,
         and form inputs all using this theme"
```

---

## Iterative Refinement Strategies

### Strategy 1: Broad → Specific

Start with the overall layout, then drill into components:

1. "Build a dashboard layout with sidebar and main content area"
2. "Add a stats row with 4 metric cards to the main area"
3. "Add a data table below the stats with user data"
4. "Style the sidebar menu with icons and an active state on the first item"

### Strategy 2: Default → Customized

Start with defaults, then customize:

1. "Create a pricing page with 3 cards"
2. "Change the middle card to have a border and 'Most Popular' badge"
3. "Apply the 'corporate' theme"
4. "Make the CTA buttons on each card use different colors: ghost, primary, accent"

### Strategy 3: Component → Integration

Build components separately, then combine:

1. "Create a responsive navbar with dropdown"
2. "Create a hero section with an image"
3. "Create a 3-column feature card grid"
4. "Now combine the navbar, hero, and card grid into a single landing page"

### Strategy 4: Migration → Enhancement

Convert first, then improve:

1. "Convert this Bootstrap page to daisyUI" [paste code]
2. "Replace hardcoded colors with daisyUI semantic colors"
3. "Add dark mode support with a theme controller toggle in the navbar"
4. "Improve the mobile experience with a bottom dock navigation"

---

## Power User Tips

| Tip | Example |
|-----|---------|
| **Reference built-in themes by name** | "Use the `synthwave` theme" — 35 themes available |
| **Reference specific example names** | "Use the `card.pricing-card` example as a starting point" |
| **Ask for the snippets tool call** | "Show me the MCP call to fetch all form-related components" |
| **Request responsive breakdowns** | "Show the layout at mobile, tablet, and desktop widths" |
| **Ask for theme + component together** | "Create a theme and a navbar that uses it" |
| **Specify HTML-only constraints** | "CSS-only, no JavaScript" — daisyUI's strength |
| **Name your theme** | "Call it `my-brand`" — used in `data-theme="my-brand"` |
| **Request OKLCH values** | "Give me the OKLCH values for this color palette" |

---

## Available Built-in Themes

When you want to skip custom theme creation, reference any of these by name:

```
light · dark · cupcake · bumblebee · emerald · corporate ·
synthwave · retro · cyberpunk · valentine · halloween ·
garden · forest · aqua · lofi · pastel · fantasy ·
wireframe · black · luxury · dracula · cmyk · autumn ·
business · acid · lemonade · night · coffee · winter ·
dim · nord · sunset · caramellatte · abyss · silk
```

Usage: `<html data-theme="synthwave">` or mention in your prompt: *"use the synthwave theme."*

---

## Quick Prompt Templates

Copy and customize these templates:

### Landing Page
```
Build a landing page using daisyUI with:
- Theme: [theme name or "custom with [colors]"]
- Navbar: [logo position, menu items, CTA button]
- Hero: [centered/with image/with form]
- Features: [number] cards in a grid
- [Testimonials/Pricing/Stats section]
- Footer: [style]
Make it fully responsive.
```

### Dashboard
```
Build an admin dashboard using daisyUI with:
- Theme: [theme name]
- Sidebar: [collapsible/fixed, menu items with icons]
- Top bar: [search, notifications, avatar]
- Stats: [number] metric cards
- Main content: [table/chart placeholder/card grid]
- Mobile: [bottom dock/hamburger menu]
```

### Form Page
```
Create a [form type] form using daisyUI with:
- Fields: [list fields with types]
- Validation: [which fields need validation]
- Layout: [single column/two column/steps]
- Submit: [button text, color]
- Container: [card/modal/standalone]
```

### Theme
```
Create a daisyUI custom theme called "[name]" with:
- Primary: [color description or hex]
- Secondary: [color description or hex]
- Accent: [color description or hex]
- Base: [light/dark, mood]
- Style: [rounded/sharp, flat/elevated, clean/textured]
Output the full @plugin CSS block.
```
