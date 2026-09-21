---
name: craft-brand-theme
description: "Craft, reverse-engineer, and deploy pristine brand design themes from any website codebase, CSS file, or DESIGN.md specification. Use when tasked with custom theming, white-labeling, brand identity adaptation, or styling web applications (Archestra, LibreChat, Open WebUI, Supabase, shadcn/ui) without ad-hoc CSS element selectors. Triggers on requests like 'make a theme for X', 'customize the styling', 'match our website theme', 'white-label this app', 'fix theme contrast', 'add custom brand fonts', or 'adapt our design tokens'."
---

# Craft Brand Theme: Architecture & Design System Engine

Synthesize and deploy production-grade brand themes by reverse-engineering design sources, establishing mathematical token contracts, and self-hosting local offline typography with zero ad-hoc CSS selector overrides.

## Non-Negotiable Rules

1. **Inside-Out Theming Only**: Never style UI components from the outside using ad-hoc element selectors (`form:has(...)`, `div > textarea`, `.composer-container`). Rely 100% on the host framework's semantic CSS custom properties (`--background`, `--card`, `--border`, `--ring`, `--primary`).
2. **The "Two Reds" (Accent Restraint) Principle**: Reserve the brand accent color (`#cc0a4d`) exclusively for primary action triggers (Enter/Submit buttons). Resting borders and dividers must remain 100% neutral (`#e8ecf2` / `#232e40`).
3. **The Focus Ring Neutrality Law**: Focus rings (`--ring`) must achieve WCAG 2.2 non-text contrast ($\ge 3.0:1$) against canvas using an engineered slate neutral (`#526585` in dark mode). Never inject saturated brand red/pink into focus outlines.
4. **The Font Law (Zero Remote CDNs)**: Never call `fonts.googleapis.com` or external CDNs. All font binaries (`.woff2`) must be self-hosted locally and served directly from the application origin with `HTTP 200`.
5. **The Turkish Weight-300 Remap Invariant**: In multilingual typography, `font-weight: 300` must explicitly remap to `Book.woff2` (400) to prevent mid-word fallback jumping on Latin Extended-A characters (`ğ, Ğ, ş, Ş, ı, İ`).
6. **Strict 4px Geometry**: Lock base radius to `0.25rem` (4px). Avoid oversized pill buttons or toy-like 16px rounding in serious architectural tooling.
7. **Dual-Mode Visual Verification**: Every theme change must be proven with live headless browser screenshots across both Light and Dark modes before declaring completion.

---

## The 6-Phase Theming Loop

Follow this sequential workflow on every theming engagement:

```
  [1. Target Decomposition] ──► [2. Source Extraction] ──► [3. Mathematical Mapping]
              │                                                        │
              ▼                                                        ▼
  [6. Live Browser Verification] ◄── [5. Invariant Gauntlet] ◄── [4. Sovereign Asset Delivery]
```

### Phase 1: Target Decomposition
Inspect the host application's styling architecture:
- Identify CSS engine: Tailwind CSS v4 (`@theme`), Tailwind CSS v3 (HSL channel vars), or shadcn/ui.
- Trace DOM lifecycle: Find how theme classes (`.theme-<id>`, `.dark`) and root `<head>` styles attach during SSR and SPA client transitions.
- Identify static asset path: Locate the origin directory serving public files (`/app/frontend/public/`).
- *Reference*: Read [01-mental-model-theming-loop.md](references/01-mental-model-theming-loop.md).

### Phase 2: Source Extraction
Extract the brand DNA from the user's input (website source code, `DESIGN.md`, Figma tokens, or public URL):
- **Surface Ramp**: Canvas (Surface 0), Raised Card (Surface 1), Sidebar (Surface 2), Recessed Well (Inset).
- **Ink Ladder**: Heading ink (Level 1), Body prose ink (Level 2), Muted caption ink (Level 3).
- **Brand Accent**: Call-to-action primary color.
- **Typography & Geometry**: Heading family vs Body family, base radius, and spacing scalar.
- *Reference*: Read [03-reverse-engineering-sources.md](references/03-reverse-engineering-sources.md).

### Phase 3: Mathematical Mapping
Map brand values directly into the target application's semantic token contract:
- Construct Light Mode and Dark Mode token declarations.
- Calibrate dark mode `--accent` hover state so dropdown items remain visibly distinct against popover backgrounds.
- Compute WCAG 2.2 contrast ratios for all core combinations.
- *References*: Read [02-token-contract-schema.md](references/02-token-contract-schema.md), [04-color-surface-ink-ladder.md](references/04-color-surface-ink-ladder.md), and [05-wcag-contrast-and-focus-rings.md](references/05-wcag-contrast-and-focus-rings.md).

### Phase 4: Sovereign Asset Delivery
Self-host local typography and brand vector marks:
- Deploy `.woff2` font files to origin `/public/fonts/`.
- Declare local `@font-face` rules with `local()` fallbacks and `font-display: swap;`.
- Enforce the Turkish Weight-300 Remap to guarantee complete 12-glyph repertoire.
- Resolve dark mode SVG vector contrast using CSS Replaced Content (`content: url(...)`).
- Trigger graceful restart of standalone web server (e.g. `pkill -9 -f next-server`) to re-index the static public directory.
- *References*: Read [06-local-font-engine-and-glyph-rules.md](references/06-local-font-engine-and-glyph-rules.md) and [08-dark-mode-vector-asset-parity.md](references/08-dark-mode-vector-asset-parity.md).

### Phase 5: The Invariant Gauntlet
Run the pre-flight checklist against common failure modes:
- Confirm zero ad-hoc component selectors (`form:has(...)`, `textarea:focus`) exist in the stylesheet.
- Confirm input borders and dividers are 100% neutral.
- Confirm submit button is the single brand accent element.
- Confirm focus ring achieves $\ge 3.0:1$ non-text contrast without pink hue bleed.
- *Reference*: Read [09-anti-patterns-and-failure-modes.md](references/09-anti-patterns-and-failure-modes.md).

### Phase 6: Dual-Mode Live Verification
Verify the deployed theme using headless browser automation:
- Probe entrypoint and font URLs over HTTPS for `HTTP 200`.
- Evaluate `document.fonts.values()` to confirm web fonts report `status: "loaded"`.
- Verify `getComputedStyle(document.body).fontFamily` reflects custom font stacks.
- Capture full-viewport screenshots of Light Mode, Dark Mode, and focused input state.
- Close headless browser session cleanly.
- *Reference*: Read [10-browser-verification-playbook.md](references/10-browser-verification-playbook.md).

---

## Decision Trees

### Decision Tree 1: Choosing Focus Ring Token (`--ring`)
```
Is the host mode Dark or Light?
├─ Light Mode ──► Use deep slate charcoal (#273041) (Contrast on white = 11.5:1, passes WCAG 2.2)
└─ Dark Mode
   ├─ If canvas is deep marine (#0e1521):
   │  └─ Compute contrast of slate neutral (#526585): Ratio = 3.10:1 (PASSES WCAG 2.2 non-text >= 3.0:1)
   └─ FORBIDDEN: Setting --ring to brand accent (#cc0a4d) -> Violates Two Reds Rule, causes neon border.
```

### Decision Tree 2: Font Deployment Strategy
```
Does the design specify custom brand typefaces?
├─ No (System fonts requested) ──► Use modern system font stack (-apple-system, BlinkMacSystemFont, Segoe UI)
└─ Yes (Brand fonts requested: e.g. Akagi Pro, Gilroy)
   ├─ NEVER use Google Fonts CDN / remote @import (Violates The Font Law, breaks air-gapped networks)
   ├─ Copy local .woff2 binaries to origin /public/fonts/
   ├─ Audit glyph repertoire for target languages (Turkish 12-glyph test)
   │  └─ If 300 Light cut lacks glyphs ──► Remap weight 300 to Book.woff2 (400)
   └─ Restart Next.js standalone process so origin serves font files with HTTP 200
```

---

## Reference Routing

| Topic | Reference Document | When to Read |
| :--- | :--- | :--- |
| **Foundations** | [01-mental-model-theming-loop.md](references/01-mental-model-theming-loop.md) | Initializing theme design or understanding inside-out vs outside-in philosophy |
| **Tokens** | [02-token-contract-schema.md](references/02-token-contract-schema.md) | Mapping CSS custom properties, shadcn tokens, sidebar variables, chart colors, and shadow scales |
| **Extraction** | [03-reverse-engineering-sources.md](references/03-reverse-engineering-sources.md) | Extracting brand DNA from website code, `DESIGN.md`, live URLs, or Figma tokens |
| **Color & Ink** | [04-color-surface-ink-ladder.md](references/04-color-surface-ink-ladder.md) | Calibrating 4-tier surface elevations, ink contrast ladder, and accent restraint |
| **Contrast** | [05-wcag-contrast-and-focus-rings.md](references/05-wcag-contrast-and-focus-rings.md) | Calculating mathematical luminance, WCAG 2.2 compliance, and slate focus rings |
| **Fonts** | [06-local-font-engine-and-glyph-rules.md](references/06-local-font-engine-and-glyph-rules.md) | Local WOFF2 hosting, `@font-face` injection, and Turkish weight-300 remap |
| **Geometry** | [07-geometry-spacing-shadow-laws.md](references/07-geometry-spacing-shadow-laws.md) | Enforcing strict 4px radii, 4px modular spacing grid, and solid surfaces |
| **Vector Assets**| [08-dark-mode-vector-asset-parity.md](references/08-dark-mode-vector-asset-parity.md) | Dynamic logo swapping via CSS `content: url(...)` and mask-free SVG optimization |
| **Traps** | [09-anti-patterns-and-failure-modes.md](references/09-anti-patterns-and-failure-modes.md) | Diagnosing neon borders, accidental dividers, glyph fractures, `@layer` cascade traps, and FOUC |
| **Verification** | [10-browser-verification-playbook.md](references/10-browser-verification-playbook.md) | Driving headless browser automation, DOM font checks, and visual proof capture |
| **SSR Injection** | [11-ssr-injection-pipeline.md](references/11-ssr-injection-pipeline.md) | Injecting `<style>` into compiled Next.js SSR chunks for zero-FOUC first paint |
| **SPA Hooks** | [12-spa-hook-and-registry-patching.md](references/12-spa-hook-and-registry-patching.md) | Patching client theme hooks, theme registry metadata, and backend Zod schema validation |
| **Containers** | [13-container-patch-architecture.md](references/13-container-patch-architecture.md) | Docker volume mounts, patch orchestration, instance guards, and process restart patterns |
| **Database** | [14-database-branding.md](references/14-database-branding.md) | Persisting logos, theme selection, and font preferences in application databases |
| **Refinement** | [15-iterative-refinement-methodology.md](references/15-iterative-refinement-methodology.md) | The change→restart→screenshot→evaluate→refine loop and two-agent review pattern |

---

## Output Contract

When executing this skill, report progress in this structured sequence:
1. **Source Extraction Summary**: Surface ramp, ink ladder, and brand accent extracted from inputs.
2. **Token Contract Mapping**: Complete Light Mode and Dark Mode CSS variable table.
3. **Contrast Verification Matrix**: Calculated contrast ratios for all critical text and non-text pairings.
4. **Font Engine Deployment**: Local `.woff2` files deployed, `@font-face` rules, and Turkish glyph remap confirmation.
5. **Live Verification Evidence**: Direct links to full-viewport Light Mode, Dark Mode, and focused screenshots.
