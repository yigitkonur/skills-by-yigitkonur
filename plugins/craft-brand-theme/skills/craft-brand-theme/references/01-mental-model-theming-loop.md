# The Mental Model & The 6-Phase Theming Loop

> **The Golden Law of Theming**:
> Never style individual UI components from the outside using ad-hoc CSS element selectors. Instead, manipulate the mathematical token environment from the inside. When tokens are pure, every component—dialogs, composers, sidebars, popovers, badges—achieves organic harmony automatically.

---

## 1. The Core Mental Model: Inside-Out vs Outside-In

When junior engineers or hasty agents attempt to customize a third-party application (such as Archestra, LibreChat, Open WebUI, Supabase Studio, or Retool), their instinctive reaction is **Outside-In Theming**:
- Inspecting a specific element in DevTools (e.g. `.chat-input-textarea` or `form:has(textarea)`).
- Writing an ad-hoc CSS selector targeting that specific component.
- Forcing `border: 1px solid #cc0a4d !important;` or `border-radius: 12px;`.

### Why Outside-In Theming Catastrophically Fails
1. **Component Composition Breakage**: Modern UI libraries (shadcn/ui, Radix UI, Headless UI) compose multi-layered DOM nodes (`Card` wraps `BorderWrapper`, which wraps `InputGroup`, which wraps `Textarea`). Forcing styles onto parent wrappers invariably creates unintended secondary borders, broken dividers, clipping, and inner-border conflicts.
2. **State & Pseudo-class Collisions**: An override on `form:has(textarea:focus)` collides with Radix's `:focus-visible` ring logic, destroying accessibility rings and causing screaming, oversized borders.
3. **Modal & Popover Split-Brain**: Styling one component from the outside leaves dialogs, dropdowns, tooltips, and toast notifications looking alien and unstyled.
4. **Maintenance Nightmare**: Upstream application updates immediately break ad-hoc DOM selectors, resulting in visual regressions.

### The Professional Inside-Out Approach
Inside-Out Theming treats the application as an **execution environment powered by a semantic token contract**. Every button, border, card background, text label, and focus state consumes CSS Custom Properties (`var(--primary)`, `var(--background)`, `var(--border)`, `var(--ring)`, `var(--radius)`).

By reverse-engineering the target application's token contract and precisely calibrating the values at the `:root` and `.theme-<id>` scope:
- **100% of the UI transforms simultaneously** without touching a single component selector.
- Modals, popovers, forms, tooltips, and cards automatically share identical geometry, depth, and contrast.
- Focus rings, hover states, and disabled states behave predictably and accessibly.

---

## 2. The 6-Phase Theming Loop

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       THE 6-PHASE THEMING LOOP                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [ Phase 1: Target Decomposition ]                                          │
│     │  Inspect target app CSS architecture (Tailwind v3/v4, Radix, Next.js) │
│     │  Map active theme variables & injection pipeline                      │
│     ▼                                                                       │
│  [ Phase 2: Source Extraction ]                                             │
│     │  Mine brand DNA from website CSS, DESIGN.md, tokens, or SVG assets    │
│     │  Extract surface ramps, ink ladder, font families, and radii          │
│     ▼                                                                       │
│  [ Phase 3: Mathematical Mapping ]                                          │
│     │  Map brand values into target token schema (Zero ad-hoc selectors)    │
│     │  Verify WCAG 2.2 contrast ratios for resting, hover, and focus states │
│     ▼                                                                       │
│  [ Phase 4: Sovereign Asset Delivery ]                                      │
│     │  Deploy local offline font binaries (.woff2) to origin                │
│     │  Enforce Turkish glyph coverage & 300-to-Book remap                   │
│     ▼                                                                       │
│  [ Phase 5: The Invariant Gauntlet ]                                        │
│     │  Audit against brand laws (Two Reds Rule, Strict Radii, Solid Surfaces)│
│     │  Ensure zero neon border pollution on input fields                    │
│     ▼                                                                       │
│  [ Phase 6: Dual-Mode Live Verification ]                                   │
│        Drive headless browser, evaluate computed styles, verify font loads  │
│        Capture full-viewport screenshots in both Light & Dark modes         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Phase 1: Target Decomposition
Before writing a single line of CSS, deconstruct how the target application renders styles:
1. **CSS Engine Identification**:
   - Tailwind CSS v4: Uses `@theme`, CSS-first config, `--spacing: 0.25rem`, standard semantic variables (`--background`, `--card`, `--primary`, `--border`, `--ring`).
   - Tailwind CSS v3: Uses `tailwind.config.js`, HSL/RGB channel variables (`--primary: 340 95% 42%`).
   - Pure CSS Modules / Emotion: Class-based scoping requiring specific root variable attachments.
2. **DOM Application Lifecycle**:
   - How does the app switch themes? Trace `applyThemeOnUI`, class names on `document.documentElement` (e.g. `.theme-custom`, `.dark`), and `data-theme` attributes.
   - Trace server-side rendering (SSR) vs client-side hydration (SPA): Does Next.js inject styles in root `<head>`, or does a client hook run on route changes?
3. **Static File Serving Path**:
   - Determine how origin static assets are served (`/public/fonts/`, `/static/`, or CDN).

---

### Phase 2: Source Extraction
Mine the authoritative brand DNA from the user's provided sources (website codebase, `DESIGN.md`, Figma design tokens, or live URL):
1. **Surface Ramp Extraction**:
   - Surface 0 (Base Canvas/Ground): Default page background.
   - Surface 1 (Raised Containers): Card surfaces, popovers, modals.
   - Surface 2 (Sidebars & Utility Trays): Navbars, tool palettes, collapsible sidebars.
   - Surface Inset (Wells & Code): Terminal panes, code blocks, quote containers.
2. **Ink Contrast Ladder Extraction**:
   - High-contrast ink: Page titles, primary metrics, major section headers.
   - Body prose: Paragraphs, chat bubbles, documentation explanations.
   - Secondary / muted text: Timestamps, captions, metadata tags, secondary labels.
3. **Interactive & Accent Palette**:
   - Brand primary color: Reserved exclusively for primary call-to-action buttons.
   - Destructive / alert color: Error states and dangerous actions.
4. **Typography & Geometry DNA**:
   - Primary typeface families: Heading font vs Body font vs Code font.
   - Base radius: Pill (9999px), rounded (8px), or architectural strict (4px).
   - Base spacing scalar: `0.25rem` (4px grid) vs arbitrary units.

---

### Phase 3: Mathematical Mapping
Map extracted brand values directly into the target application's semantic token schema for both Light and Dark modes.

**The Golden Mapping Rule**:
```css
/* LIGHT MODE */
:root, html, html.theme-<id> {
  --background: <Surface 0>;
  --foreground: <Ink Body>;
  --card: <Surface 1>;
  --card-foreground: <Ink Body>;
  --popover: <Surface 1>;
  --popover-foreground: <Ink Body>;
  --primary: <Brand Primary Accent>;
  --primary-foreground: <High-contrast readable on primary>;
  --secondary: <Surface 2 or Subdued Neutral>;
  --secondary-foreground: <Ink Secondary>;
  --muted: <Subdued Neutral>;
  --muted-foreground: <Ink Muted>;
  --accent: <Subdued Hover Neutral>;
  --accent-foreground: <Ink Body>;
  --border: <Neutral Hairline Border>;
  --input: <Neutral Hairline Border>;
  --ring: <Elevated Neutral Focus Ring>;
  --radius: <Brand Radius>;
  --spacing: <Brand Grid Unit>;
}

/* DARK MODE */
html.dark, html.dark.theme-<id>, .dark {
  /* Semantic flip: Invert surfaces and inks while preserving neutral hairlines */
}
```

---

### Phase 4: Sovereign Asset Delivery
Never rely on client machines having fonts installed, and never make remote calls to third-party CDNs (Google Fonts, Typekit, Adobe Fonts).
1. **Self-Host WOFF2 Files**: Copy optimized `.woff2` binaries directly into the application's origin static directory (`public/fonts/`).
2. **Declare Local `@font-face` Rules**:
   - Use `local()` declarations first to leverage local OS cache if present.
   - Provide relative origin URLs (`/fonts/<family>-<weight>.woff2`).
   - Set `font-display: swap;` for zero FOIT (Flash of Invisible Text).
3. **Enforce Glyph Completeness**:
   - Verify 100% Latin Extended coverage for international text (e.g. Turkish 12-glyph roster).
   - If Light (300) weight lacks code points, remap `font-weight: 300` to Book (400) to eliminate mid-word font fallback.

---

### Phase 5: The Invariant Gauntlet
Run every generated theme through the non-negotiable invariant checklist:
- [ ] **The "Two Reds" Principle**: Is the brand accent color restricted solely to primary interactive buttons?
- [ ] **Zero Border Hue Bleed**: Are input borders and card dividers 100% neutral?
- [ ] **Focus Ring Contrast**: Does the `:focus-visible` ring satisfy WCAG 2.2 non-text contrast (>= 3.0:1) without glowing in neon pink/red?
- [ ] **Solid Surfaces**: Are cards 100% solid opacity (no blurred glassmorphism degrading text readability)?
- [ ] **Geometry Containment**: Are all border radii locked to the brand scale (e.g. strict 4px)?

---

### Phase 6: Dual-Mode Live Verification
Never declare a theme complete until it has been inspected by a headless browser on live rendered HTML:
1. **Automated Font Loading Audit**: Run JavaScript to verify `document.fonts.values()` reports `status: "loaded"`.
2. **Computed Style Inspection**: Check `getComputedStyle(element)` to confirm `--font-sans` and `--font-head` actively resolve.
3. **Full-Viewport Visual Proof**: Capture high-resolution screenshots of both Light and Dark modes.
4. **Focus & Interaction State Proof**: Tab into an input or chat composer to visually verify the focused state before signing off.
