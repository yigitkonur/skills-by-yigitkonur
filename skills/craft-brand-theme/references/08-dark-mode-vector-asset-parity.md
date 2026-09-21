# Dark Mode Vector Asset Parity & Dynamic SVG Switching

This reference details how to handle brand logos, icons, and vector marks across Light and Dark modes when the host application lacks native dark-asset switching.

---

## 1. The Dark Mode Logo Dilemma

When integrating a custom theme into an existing platform (such as Archestra, LibreChat, or Open WebUI), you will frequently encounter this upstream limitation:
- The database schema may have `logo` and `logo_dark` columns.
- BUT the React/Next.js frontend components hardcode `<img src={organization.logo} />` across chat welcome screens, navigation bars, and authentication dialogs, completely ignoring `organization.logo_dark`.

### The Visual Disaster
If the brand logo contains dark ink (e.g. `#0f1a2a` text):
- In **Light Mode**: The logo looks crisp on white (`#ffffff`).
- In **Dark Mode**: The dark ink renders against `#0e1521` (deep marine canvas). Contrast is **1.08:1** (completely invisible / black-on-black).

```
   LIGHT MODE (High Contrast)               DARK MODE (Catastrophic Blend)
 ┌──────────────────────────────┐         ┌──────────────────────────────┐
 │                              │         │                              │
 │   [▼] zeo                    │         │   [▼]                        │
 │  Crimson + Deep Ink (#0f1a2a)│         │  Crimson + Invisible Dark Text│
 │  on White Canvas (#ffffff)   │         │  on Deep Navy (#0e1521)      │
 │                              │         │                              │
 └──────────────────────────────┘         └──────────────────────────────┘
```

---

## 2. Why `filter: invert(1)` is a Critical Anti-Pattern

A common junior workaround is adding `dark:invert` or `filter: invert(1)` to dark mode images:

```css
/* FORBIDDEN ANTI-PATTERN */
html.dark img.logo {
  filter: invert(1);
}
```

### Why This Fails
Inversion flips **all color channels**:
- Black `#000000` $\implies$ White `#ffffff` (Good for text).
- **BUT**: Zeo Crimson `#cc0a4d` $\implies$ Neon Cyan/Green `#33f5b2`!
- The brand identity is completely corrupted.

---

## 3. The CSS Replaced-Content Solution

Modern CSS (CSS Image Values and Replaced Content Module Level 3) allows the `content` property to replace the visual resource rendered inside an `<img>` element:

```css
/* =============================================================================
   Dynamic Vector Logo Swapping via CSS Replaced Content
   Swaps light-ink SVG for white-ink SVG in Dark Mode without touching React DOM
   ============================================================================= */

html.dark img[src^="data:image/svg+xml"][src*="<unique-signature-of-light-svg>"] {
  content: url("<data-uri-of-white-ink-dark-svg>");
}
```

### How It Works
1. When `html` has no `.dark` class, the browser displays the normal `src` attribute (Light Mode SVG with `#0F1A2A` text).
2. The moment `html.dark` is toggled, the CSS rule matches and instructs the browser's replaced-element rendering engine to display the dark-optimized SVG (White `#EEF2F7` text) instead.
3. **Zero JavaScript DOM mutation**: Works seamlessly across React re-renders, Next.js route transitions, and SSR page loads.

---

## 4. Constructing Mask-Free, Robust SVGs

Complex SVGs downloaded from graphic design tools frequently include `<mask id="...">`, `<clipPath id="...">`, or `<use xlink:href="...">`.

### Why Mask IDs Fail in Web Apps
1. **ID Collision**: If the same SVG data URI is rendered twice on the page (e.g. in the sidebar AND in the center chat watermark), duplicate `id="mask-0"` tags cause browser rendering engines to break, rendering a black box or blank space.
2. **Data URI Isolation**: Safari and WebKit sometimes fail to resolve internal fragment identifiers (`url(#mask-0)`) inside `data:image/svg+xml` URIs.

### The Canonical Flat SVG Pattern
Convert the vector artwork to flat, direct `<path>` fills with zero masks and zero `<defs>`:

```xml
<!-- Flat, Mask-Free Canonical Logo (Light Mode) -->
<svg xmlns="http://www.w3.org/2000/svg" width="91" height="33" viewBox="0 0 91 33">
  <g fill="none" fill-rule="evenodd">
    <!-- Crimson Triangle Mark -->
    <path fill="#CC0A4D" d="M.674 2.536a5.163 5.163..."/>
    <!-- White Internal Shape -->
    <path fill="#FFFFFF" d="M21.45 19.031h-7.025..."/>
    <!-- High-Contrast Body Ink: #0F1A2A (Light) or #EEF2F7 (Dark) -->
    <path fill="#0F1A2A" d="M64.219 9c3.697 0..."/>
  </g>
</svg>
```

### Python Base64 Generator
```python
import base64

def to_data_uri(svg_content):
    encoded = base64.b64encode(svg_content.encode('utf-8')).decode('ascii')
    return f"data:image/svg+xml;base64,{encoded}"
```
