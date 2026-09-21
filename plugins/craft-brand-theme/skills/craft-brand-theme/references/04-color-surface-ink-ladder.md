# Color, Surface Ramps, and the Ink Ladder

This reference provides the mathematical and perceptual rules governing surface elevations, ink contrast hierarchy, and the "Two Reds" restraint principle.

---

## 1. The 4-Tier Surface Ramp

Surfaces provide spatial hierarchy, guiding the user's eye from the broad page canvas down into focused cards, execution drawers, and floating popovers.

```
       LIGHT MODE                                   DARK MODE
  ┌─────────────────────────┐                 ┌─────────────────────────┐
  │ Surface 0: Canvas       │                 │ Surface 0: Canvas       │
  │ #ffffff                 │                 │ #0e1521 (Deep Marine)   │
  │  ┌────────────────────┐ │                 │  ┌────────────────────┐ │
  │  │ Surface 1: Card    │ │                 │  │ Surface 1: Card    │ │
  │  │ #ffffff (Hairline) │ │                 │  │ #1c2535 (+1 Step)  │ │
  │  │  ┌───────────────┐ │ │                 │  │  ┌───────────────┐ │ │
  │  │  │ Inset Well    │ │ │                 │  │  │ Inset Well    │ │ │
  │  │  │ #efeee9 (Warm)│ │ │                 │  │  │ #0b111e (Dark)│ │ │
  │  │  └───────────────┘ │ │                 │  │  └───────────────┘ │ │
  │  └────────────────────┘ │                 │  └────────────────────┘ │
  └─────────────────────────┘                 └─────────────────────────┘
```

### Surface Level 0: Canvas / Ground
- **Light Mode**: Pure White `#ffffff` or clean editorial paper.
- **Dark Mode**: Deep Marine Navy `#0e1521` (never pure `#000000` unless high-contrast OLED black is specifically required). Marine navy provides atmospheric depth without eye strain.
- **Token**: `--background`

### Surface Level 1: Raised Containers / Cards
- **Light Mode**: `#ffffff`. Optical boundary is defined by a crisp 1px neutral hairline border (`#e8ecf2`), not heavy dropshadows.
- **Dark Mode**: `#1c2535`. Notice that the dark card is **visibly elevated above the canvas** (luminance ratio 1.54:1). This creates unmistakable card geometry even in dim viewing conditions.
- **Token**: `--card`, `--popover`

### Surface Level 2: Navigation & Trays (Sidebar)
- **Light Mode**: Soft Blue `#f5f8fc`. A subtle cool tint creates architectural anchoring for the tool rail while keeping the primary workspace dominant.
- **Dark Mode**: Deep Navigational Marine `#131c2b`. Positioned between Canvas (`#0e1521`) and Raised Cards (`#1c2535`).
- **Token**: `--sidebar`

### Surface Inset: Terminal Wells & Code Panes
- **Light Mode**: Warm Inset `#efeee9`. Depressed into the surface, signaling pre-formatted code or technical output.
- **Dark Mode**: Deep Recessed Obsidian `#0b111e`. Darker than the surrounding card.
- **Token**: `--muted`

---

## 2. The Ink Contrast Ladder

Text hierarchy must follow a disciplined, monotonically decreasing contrast scale. Never use random grays.

```
       INK LADDER (LIGHT)                           INK LADDER (DARK)
  ┌─────────────────────────┐                 ┌─────────────────────────┐
  │ L1: High-Contrast Ink   │                 │ L1: High-Contrast Ink   │
  │ #0f1a2a (15.8:1 on #fff)│                 │ #eef2f7 (16.2:1 on dark)│
  ├─────────────────────────┤                 ├─────────────────────────┤
  │ L2: Body Prose          │                 │ L2: Body Prose          │
  │ #273041 (11.5:1 on #fff)│                 │ #c9d2e0 (11.8:1 on dark)│
  ├─────────────────────────┤                 ├─────────────────────────┤
  │ L3: Muted / Captions    │                 │ L3: Muted / Captions    │
  │ #5a6678 (5.5:1 on #fff) │                 │ #8b96a8 (5.6:1 on dark) │
  └─────────────────────────┘                 └─────────────────────────┘
```

### Level 1: High-Contrast Ink (Display & Headings)
- **Light**: `#0f1a2a` (Near-black marine ink). Contrast against white: **15.8:1**.
- **Dark**: `#eef2f7` (Near-white ice ink). Contrast against `#0e1521`: **16.2:1**.
- **Usage**: H1–H4 titles, card headers, primary metric numbers, active tab text.
- **Token**: `--foreground` (in heading context), `--card-foreground`.

### Level 2: Primary Reading Ink (Body Prose)
- **Light**: `#273041` (Deep slate charcoal). Contrast against white: **11.5:1**.
- **Dark**: `#c9d2e0` (Soft luminescent silver). Contrast against `#1c2535`: **11.8:1**.
- **Usage**: Paragraphs, chat messages, input values, dropdown option items.
- **Token**: `--foreground`, `--secondary-foreground`.

### Level 3: Muted Metadata Ink (Captions & Timestamps)
- **Light**: `#5a6678` (Balanced medium gray). Contrast against white: **5.5:1** (satisfies WCAG AA >= 4.5:1).
- **Dark**: `#8b96a8` (Muted twilight slate). Contrast against `#1c2535`: **5.6:1** (satisfies WCAG AA >= 4.5:1).
- **Usage**: Timestamps, placeholder text, footnote disclosures, secondary badges.
- **Token**: `--muted-foreground`.

---

## 3. The "Two Reds" (Accent Restraint) Principle

> **Core Rule**: An interface must never dilute its primary interactive anchor by splashing the brand accent color across decorative borders, resting inputs, or dividers.

```
  CORRECT (Restrained & Confident)        INCORRECT (Visual Pollution)
 ┌──────────────────────────────────┐    ┌──────────────────────────────────┐
 │ Resting Card (#232e40 border)    │    │ Resting Card (Pink #cc0a4d border│
 │                                  │    │                                  │
 │                                  │    │  Horizontal Pink Divider Line!   │
 │                                  │    │ ──────────────────────────────── │
 │                      ┌─────────┐ │    │                      ┌─────────┐ │
 │                      │ Submit  │ │    │                      │ Submit  │ │
 │                      │ #cc0a4d │ │    │                      │ #cc0a4d │ │
 │                      └─────────┘ │    │                      └─────────┘ │
 └──────────────────────────────────┘    └──────────────────────────────────┘
    Only 1 Crimson element: Button!          Pink everywhere: Card, Border, Divider!
```

### Why Brand Accent Bleed Ruins an Interface
1. **Destroys Affordance**: If resting card borders, input borders, and dividers are all crimson or pink, the user's subconscious cannot immediately identify the clickable button.
2. **Creates "Urgency Fatigue"**: High-chroma saturated hues (reds, crimsons, hot pinks, neon blues) stimulate the visual cortex. Bathing structural layout lines in saturated colors induces subconscious agitation.
3. **Cheapens Brand Perception**: Premium enterprise software (Linear, Stripe, Apple, Zeo) uses calm, monochromatic surfaces with a single high-impact accent anchor.

### Rules of Engagement
- **`--primary`**: Applied to the single primary action button ("Submit", "Sign In", "Send").
- **`--border` & `--input`**: 100% neutral (`#e8ecf2` light / `#232e40` dark). Zero accent tint!
- **`--ring`**: Neutral slate (`#273041` light / `#526585` dark). Never brand red!
- **Card Dividers**: Neutral hairlines only.
