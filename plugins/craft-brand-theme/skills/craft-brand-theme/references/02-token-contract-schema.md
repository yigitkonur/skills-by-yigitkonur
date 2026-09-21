# The Semantic Token Contract Schema

This reference provides the authoritative token mapping between modern component design systems (shadcn/ui, Radix UI, Tailwind CSS v3/v4) and raw CSS custom properties.

---

## 1. Complete Core Token Reference Table

| Token Variable | Semantic Purpose | Where It Appears in UI | Critical Design Guideline |
| :--- | :--- | :--- | :--- |
| `--background` | Canvas floor (Surface 0) | Body background, outer viewport | Must be pure white `#ffffff` or deepest dark `#0e1521`. Never use gray here in high-contrast themes. |
| `--foreground` | Default ink / body text | Prose paragraphs, unstyled labels, general text | Must meet WCAG AA (>= 4.5:1) against `--background`. |
| `--card` | Raised containers (Surface 1) | Cards, panels, execution drawers, chat input cards | Must create optical separation from canvas. In dark mode, must be elevated above `--background` (e.g. `#1c2535` vs `#0e1521`). |
| `--card-foreground` | Ink on raised surfaces | Titles and descriptions inside cards | Usually identical or slightly brighter than `--foreground`. |
| `--popover` | Elevated floating planes (Surface 2) | Dropdown menus, tooltips, select popups, dialogs | In dark mode, match `--card` or elevate +1 step to avoid disappearing into the background. |
| `--popover-foreground` | Ink on floating planes | Menu items, option labels, tooltip text | High contrast against `--popover`. |
| `--primary` | The single primary brand action | "Send", "Submit", "Sign In", active tab indicators | **Brand Law**: Reserve exclusively for primary action triggers. Never bleed onto resting borders. |
| `--primary-foreground` | Ink on primary action button | Text or icon inside primary buttons | Must achieve high contrast (e.g. pure white `#ffffff` on `#cc0a4d` = 6.4:1). |
| `--secondary` | Secondary action surfaces | Ghost buttons, subtle action pills, tag badges | Muted neutral (e.g. `#f4f6f9` light / `#131c2b` dark). Never compete with `--primary`. |
| `--secondary-foreground` | Ink on secondary surfaces | Text on secondary buttons and tags | Dark charcoal in light mode (`#273041`), soft slate in dark mode (`#c9d2e0`). |
| `--muted` | Subdued fills & disabled states | Background of disabled inputs, track of progress bars | Neutral resting tint. |
| `--muted-foreground` | Low-priority metadata | Timestamps, secondary captions, help text, placeholders | Must balance low visual weight with minimum legibility (WCAG AA >= 4.5:1 for normal text). |
| `--accent` | Hover state background | Hovered dropdown item, hovered card, button hover fill | **Critical Pitfall**: In dark mode, must be perceptually distinct from `--popover` and `--card` (e.g. `#232e40` vs `#1c2535` = 1.13:1 contrast) to provide visible feedback! |
| `--accent-foreground` | Ink on hovered elements | Text of hovered menu items and list options | High-contrast ink. |
| `--destructive` | Irreversible / error action | Delete buttons, error banners, danger badges | Brand crimson or semantic red (`#e11d48` / `#cc0a4d`). |
| `--destructive-foreground` | Ink on danger buttons | Text on delete button | Pure white `#ffffff`. |
| `--border` | Structural hairline dividers | Card perimeters, table cell dividers, section borders | **Strict Law**: 100% neutral! Never use brand hue. Light: `#e8ecf2`, Dark: `#232e40`. |
| `--input` | Resting border of input elements | Text fields, checkboxes, radios, select triggers | Usually identical to `--border`. |
| `--ring` | Keyboard & accessibility focus ring | `:focus-visible` ring on inputs, buttons, checkboxes | **Accessibility Law**: Must achieve >= 3.0:1 contrast against canvas (WCAG 2.2). Use slate neutral (`#273041` light / `#526585` dark). |
| `--radius` | Base geometry scalar | Corner rounding across buttons, cards, dialogs | Architectural: `0.25rem` (4px). Smooth: `0.5rem` (8px). Pill: `9999px`. |
| `--spacing` | Base grid layout scalar | Paddings, margins, gaps (`p-4` = 4 * spacing) | Modern standard: `0.25rem` (4px modular scale). |

---

## 2. Sidebar Token Subsystem

Modern AI platforms (Archestra, LibreChat, Open WebUI) isolate the left navigation drawer into a dedicated `--sidebar-*` token scope.

| Sidebar Token | Visual Purpose | Light Mode Calibration | Dark Mode Calibration |
| :--- | :--- | :--- | :--- |
| `--sidebar` | Sidebar background | Soft blue `#f5f8fc` (matches website tray) | Deep marine navy `#131c2b` |
| `--sidebar-foreground` | Navigation link text | Charcoal `#1c2535` | Soft ice `#c9d2e0` |
| `--sidebar-primary` | Active nav indicator / CTA | Crimson `#cc0a4d` | Crimson `#cc0a4d` |
| `--sidebar-primary-foreground`| Text on active nav badge | Pure white `#ffffff` | Pure white `#ffffff` |
| `--sidebar-accent` | Hover state on sidebar link | Subtle tint `#eef2f7` | Raised slate `#1c2535` |
| `--sidebar-accent-foreground` | Text on hovered link | Ink `#0f1a2a` | White `#eef2f7` |
| `--sidebar-border` | Right divider line separating sidebar | Hairline `#e8ecf2` | Deep hairline `#232e40` |
| `--sidebar-ring` | Focus ring on sidebar links | Neutral `#273041` | Slate neutral `#526585` |

---

## 3. Typography & Micro-Layout Tokens

| Token Variable | Purpose | Canonical Values |
| :--- | :--- | :--- |
| `--font-sans` | Primary body, chat prose, general UI | `'Akagi Pro', 'Akagi', -apple-system, BlinkMacSystemFont, sans-serif` |
| `--font-head` | Display headings, titles, buttons, badges | `'Gilroy', -apple-system, BlinkMacSystemFont, sans-serif` |
| `--font-mono` | Data, ports, latencies, code blocks | `ui-monospace, 'JetBrains Mono', 'DM Mono', 'SF Mono', monospace` |
| `--line-height-text` | Body prose reading rhythm | `1.44` (comfort reading standard) |
| `--line-height-head` | Compact heading rhythm | `1.25` (standard) or `1.1` (hero display) |
| `--tracking-normal` | Body prose letter spacing | `0em` |
| `--tracking-tight` | Heading letter spacing | `-0.02em` (crisp optical density for large type) |

---

## 4. Pitfalls & Anti-Patterns by Token

### Pitfall 1: Muddy Accent vs Popover Split-Brain
- **The Bug**: Setting `--accent` identical to `--popover` or `--card` in dark mode (e.g. `--popover: #1c2535; --accent: #1c2535;`).
- **The Consequence**: When a user opens a dropdown or moves their cursor over a menu item, the hovered item has **1.00:1 contrast** (zero visual change). The dropdown appears frozen or broken.
- **The Fix**: In dark mode, ensure `--accent` is at least one step elevated (`--accent: #232e40;`).

### Pitfall 2: The Neon Focus Ring Disconnect
- **The Bug**: Setting `--ring: var(--primary);` (e.g. `#cc0a4d` or bright pink).
- **The Consequence**: When clicking into a search bar or chat composer, the entire card is wrapped in a screaming neon border. It destroys visual calm and violates the "Two Reds" principle.
- **The Fix**: Always calibrate `--ring` to a neutral slate tone that satisfies WCAG 2.2 (>= 3.0:1) without brand hue pollution (`#526585` in dark mode).

### Pitfall 3: Card vs Canvas Vanishing in Dark Mode
- **The Bug**: Setting `--card` equal to `--background` in dark mode (`#0e1521`).
- **The Consequence**: Without elevated card backgrounds, chat composers and dialog boxes blend completely into the page, relying entirely on 1px borders to define boundaries.
- **The Fix**: Elevate `--card` to `#1c2535` against `#0e1521` base ground.

---

## 5. Chart & Data Visualization Tokens

Modern dashboard applications consume a 5-color chart sequence. These must harmonize with the brand palette while remaining distinguishable from each other:

| Token Variable | Light Mode | Dark Mode | Usage |
| :--- | :--- | :--- | :--- |
| `--chart-1` | `#cc0a4d` (Crimson) | `#cc0a4d` (Crimson) | Primary data series, KPI highlights |
| `--chart-2` | `#1c2535` (Deep Ink) | `#ff5c8f` (Soft Pink) | Secondary series |
| `--chart-3` | `#22c55e` (Green) | `#4fae47` (Muted Green) | Success / positive metrics |
| `--chart-4` | `#eab308` (Amber) | `#4a93f5` (Blue) | Warning / neutral metrics |
| `--chart-5` | `#06b6d4` (Cyan) | `#9d8df0` (Lavender) | Tertiary / supplementary |

**Dark mode guidance**: Avoid direct light-mode color carryover. Dark backgrounds require desaturated or shifted hues to maintain readability. `#eab308` (amber) becomes illegible on dark navy — replace with a contrasting blue.

---

## 6. Shadow & Elevation Token Scale

An 8-step elevation shadow ramp provides consistent depth across all components:

| Token Variable | Light Mode Value | Dark Mode Value |
| :--- | :--- | :--- |
| `--shadow-2xs` | `0 1px 2px 0 rgba(175, 184, 202, 0.10)` | `0 1px 2px 0 rgba(0, 0, 0, 0.25)` |
| `--shadow-xs` | `0 1px 3px 0 rgba(175, 184, 202, 0.12)` | `0 1px 3px 0 rgba(0, 0, 0, 0.30)` |
| `--shadow-sm` | `0 2px 4px 0 rgba(175, 184, 202, 0.15)` | `0 2px 4px 0 rgba(0, 0, 0, 0.35)` |
| `--shadow` | `0 4px 8px 0 rgba(175, 184, 202, 0.15)` | `0 4px 8px 0 rgba(0, 0, 0, 0.38)` |
| `--shadow-md` | `0 6px 16px 0 rgba(175, 184, 202, 0.18)` | `0 6px 16px 0 rgba(0, 0, 0, 0.40)` |
| `--shadow-lg` | `0 12px 24px 0 rgba(175, 184, 202, 0.20)` | `0 12px 24px 0 rgba(0, 0, 0, 0.45)` |
| `--shadow-xl` | `0 16px 32px 0 rgba(175, 184, 202, 0.22)` | `0 16px 32px 0 rgba(0, 0, 0, 0.50)` |
| `--shadow-2xl` | `0 24px 48px 0 rgba(175, 184, 202, 0.25)` | `0 24px 48px 0 rgba(0, 0, 0, 0.60)` |
| `--shadow-signature` | `-9px 9px 0 0 #cc0a4d` | `-9px 9px 0 0 #cc0a4d` |

**Light mode shadow tint**: Use warm marine `rgba(175, 184, 202, ...)` rather than pure black. This creates a softer, more sophisticated elevation that harmonizes with blue-gray ink tones.

**Dark mode shadow tint**: Use pure black `rgba(0, 0, 0, ...)` with higher opacity. On dark backgrounds, colored shadows are invisible — only darkness provides depth.

**Signature shadow**: A zero-blur hard-edge offset shadow in brand crimson. Used sparingly on hero elements, code blocks, or featured cards to create architectural visual anchoring.
