# Geometry, Spacing Grid, and Shadow Laws

This reference details the mathematical layout grid, strict corner radii laws, elevation shadows, and the solid surface mandate.

---

## 1. The Strict 4px Radii Law

> **Mandate**: In confident, architectural enterprise software, corner radius must not exceed **4px (`--radius: 0.25rem`)**.

```
  CORRECT: Strict 4px Geometry             INCORRECT: Toy-Like Bubbles
 ┌───────────────────────────┐            ╭───────────────────────────╮
 │ Clean Architectural Box   │            │ Oversized 16px Rounding   │
 │ border-radius: 4px;       │            │ border-radius: 16px;      │
 └───────────────────────────┘            ╰───────────────────────────╯
   Serious, technical, precise              Casual, toy-like, juvenile
```

### Why 4px Geometry Outperforms Oversized Rounding
1. **Content Density**: Modern AI platforms and developer tooling present dense information: terminal streams, JSON responses, tabular metrics, and multi-file code trees. Sharp 4px corners maximize usable screen real estate.
2. **Visual Seriousness**: 12px–24px rounded corners and pill-shaped buttons signal consumer lifestyle apps. Serious infrastructure software (Bloomberg, AWS, Datadog, Stripe Dashboard, Zeo) uses disciplined, restrained rounding.
3. **Hierarchy**: In Archestra and shadcn/ui:
   - Base `--radius: 0.25rem` (4px).
   - Inner input elements inherit `calc(var(--radius) - 2px)` (2px).
   - This ensures concentric nesting geometry without corner clipping.

---

## 2. The 4px Modular Spacing Grid

Modern Tailwind CSS v4 and design token systems standardize on a **4px modular baseline**:
- `--spacing: 0.25rem;` (4px base scalar).

Every padding, margin, and gap scales linearly from this baseline:
- `gap-1` / `p-1`: $1 \times 4\text{px} = 4\text{px}$
- `gap-2` / `p-2`: $2 \times 4\text{px} = 8\text{px}$
- `gap-3` / `p-3`: $3 \times 4\text{px} = 12\text{px}$
- `gap-4` / `p-4`: $4 \times 4\text{px} = 16\text{px}$
- `gap-6` / `p-6`: $6 \times 4\text{px} = 24\text{px}$
- `gap-8` / `p-8`: $8 \times 4\text{px} = 32\text{px}$

By declaring `--spacing: 0.25rem;` at the root theme definition, every container in the application snaps cleanly into an 8-point / 4-point grid.

---

## 3. Elevation Shadows vs Signature Offset Shadows

### Resting Elevation Ramp
Elevation shadows in clean design systems are monochromatic, soft, and realistic. They lift surfaces without creating muddy silhouettes.

```css
/* Light Mode Elevation (Soft Marine Tint) */
--shadow-2xs: 0 1px 2px 0 rgba(175, 184, 202, 0.10);
--shadow-xs:  0 1px 3px 0 rgba(175, 184, 202, 0.12);
--shadow-sm:  0 2px 4px 0 rgba(175, 184, 202, 0.15);
--shadow:     0 4px 8px 0 rgba(175, 184, 202, 0.15);
--shadow-md:  0 6px 16px 0 rgba(175, 184, 202, 0.18);
--shadow-lg:  0 12px 24px 0 rgba(175, 184, 202, 0.20);
--shadow-xl:  0 16px 32px 0 rgba(175, 184, 202, 0.22);
--shadow-2xl: 0 24px 48px 0 rgba(175, 184, 202, 0.25);

/* Dark Mode Elevation (Deep Obsidian Alpha) */
--shadow-2xs: 0 1px 2px 0 rgba(0, 0, 0, 0.25);
--shadow-xs:  0 1px 3px 0 rgba(0, 0, 0, 0.30);
--shadow-sm:  0 2px 4px 0 rgba(0, 0, 0, 0.35);
--shadow:     0 4px 8px 0 rgba(0, 0, 0, 0.38);
--shadow-md:  0 6px 16px 0 rgba(0, 0, 0, 0.40);
--shadow-lg:  0 12px 24px 0 rgba(0, 0, 0, 0.45);
--shadow-xl:  0 16px 32px 0 rgba(0, 0, 0, 0.50);
--shadow-2xl: 0 24px 48px 0 rgba(0, 0, 0, 0.60);
```

### The Signature Offset Shadow
For hero elements or specific interactive focal cards, Zeo defines the signature hard-edge shadow:
```css
--shadow-signature: -9px 9px 0 0 #cc0a4d;
```
- **Usage**: Diagnostic cards, documentation hero book covers, execution code windows.
- **Rule**: Must use zero blur radius (`0 0`). It acts as an architectural architectural shadow slab.

---

## 4. The Solid Surface Law: Zero Frosted Glass

> **Mandate**: Core interactive containers (cards, sidebars, popovers, chat composer) must maintain **100% solid opacity**. No `backdrop-filter: blur()`, no translucent glassmorphism.

### Why Frosted Glass is Prohibited in Production Tools
1. **Legibility Degradation**: Translucent surfaces allow background text or complex graphics to bleed through behind active code blocks or chat responses, causing unpredictable WCAG contrast failures.
2. **GPU Rendering Penalties**: High-radius backdrop blur filters force the browser compositor into continuous hardware re-rasterization during scrolling, causing stutter and frame drops on battery-constrained laptops.
3. **Visual Noise**: True editorial confidence is built on solid, opaque physical planes with hairline borders.
