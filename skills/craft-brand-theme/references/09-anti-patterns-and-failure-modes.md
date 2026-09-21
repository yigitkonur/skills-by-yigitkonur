# Anti-Patterns, Traps, and Failure Modes

This reference catalogs the hard-won failure modes discovered during real-world platform customization and provides concrete prevention recipes for each.

---

## 1. Catalog of Anti-Patterns

### Anti-Pattern 1: The Ad-Hoc Element Selector Trap
- **The Crime**: Writing component-specific selectors like `form:has(textarea)`, `div.chat-input`, or `button.send-btn` directly in the theme stylesheet.
- **The Consequence**: Modern component systems nest multiple divs and wrappers. Overriding parent border or padding creates double borders, inner divider lines slicing through cards, and broken responsive sizing.
- **The Fix**: Strip all ad-hoc element selectors. Rely 100% on the semantic CSS token contract (`--card`, `--border`, `--ring`, `--primary`).

---

### Anti-Pattern 2: The Screaming Neon Composer
- **The Crime**: Setting `--ring` or `--border` to the brand primary accent color (`#cc0a4d` / `#ff2d78`).
- **The Consequence**: The moment a user clicks the chat prompt box, the entire perimeter ignites in saturated hot pink/red. The user feels as if they triggered a fatal error or a warning alert.
- **The Fix**: Enforce the **Two Reds Principle**. The submit/enter button is the ONLY crimson element. The resting border must be neutral (`#e8ecf2` / `#232e40`), and the focus ring must be an engineered slate neutral (`#526585`).

---

### Anti-Pattern 3: The Accidental Horizontal Divider Line
- **The Crime**: Setting `border-top` or `border-bottom` on textarea wrappers to create separation from the bottom button row.
- **The Consequence**: A bright colored hairline slices horizontally across the card, creating awkward visual fragmentation.
- **The Fix**: In card composers, surface containment is unified. Never add internal divider borders; let spacing (`gap-2`) provide visual separation.

---

### Anti-Pattern 4: The Turkish Glyph Fracture
- **The Crime**: Declaring `@font-face` for `font-weight: 300` pointing to `Light.ttf` or `Light.woff2`.
- **The Consequence**: Light weights in many custom corporate typefaces omit Latin Extended-A code points. Turkish letters (`ğ`, `Ğ`, `ş`, `Ş`, `ı`, `İ`) fracture mid-word and fall back to system Arial, jumping 2px off the baseline and destroying readability.
- **The Fix**: Enforce the **Weight-300 Remap Invariant**. `font-weight: 300` MUST explicitly bind to `Book.woff2` (400), which contains 100% complete Turkish glyph tables.

---

### Anti-Pattern 5: The Static Manifest 404 (Next.js Standalone)
- **The Crime**: Copying `.woff2` font files into `/app/frontend/public/fonts/` while `next-server` is actively running, and assuming they are immediately accessible.
- **The Consequence**: Next.js standalone server indexes the `/public/` directory at boot. New files return `HTTP 404` until the process is restarted.
- **The Fix**: Always issue a graceful process restart (`pkill -9 -f next-server`) immediately after deploying static assets into `/public/`.

---

### Anti-Pattern 6: The Full Inversion Logo Trap
- **The Crime**: Applying `filter: invert(1)` to dark mode logos.
- **The Consequence**: While black text turns white, saturated brand colors (e.g. crimson `#cc0a4d`) invert to radioactive cyan (`#33f5b2`).
- **The Fix**: Use CSS Replaced Content (`html.dark img[src*="..."] { content: url('...'); }`) to swap the data URI cleanly to a white-text SVG while preserving the exact crimson mark.

---

### Anti-Pattern 7: The Pill Radius Slop
- **The Crime**: Leaving default consumer pill buttons (`rounded-full`, 9999px) or oversized 16px corners inside serious diagnostic tools.
- **The Consequence**: The application looks like a toy social app rather than an authoritative enterprise workspace.
- **The Fix**: Lock base radius to strict architectural 4px (`--radius: 0.25rem`).

---

### Anti-Pattern 8: Frosted Glass Legibility Degradation
- **The Crime**: Adding `backdrop-filter: blur(12px); background: rgba(..., 0.7);` to cards or sidebars.
- **The Consequence**: Scrolling code blocks behind a translucent card creates visual clutter, causes WCAG contrast failures on variable text, and introduces GPU stutter.
- **The Fix**: Enforce the **Solid Surface Law**. All primary interactive surfaces must be 100% opaque.
