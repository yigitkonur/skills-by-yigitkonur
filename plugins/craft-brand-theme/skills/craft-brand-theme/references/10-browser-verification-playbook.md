# Headless Browser Verification Playbook

This reference provides the step-by-step procedure for verifying themes, font loading, computed styles, and interaction states using headless browser automation.

---

## 1. The Verification Hierarchy

Never declare a theme done based on code inspection alone. Verification must ascend through 4 empirical layers:

```
  Layer 4: Full-Viewport Visual Screenshots (Light + Dark + Focused)
     ▲
  Layer 3: DOM Computed Styles & Loaded Font Array Verification
     ▲
  Layer 2: Font Binary HTTP 200 Origin Verification
     ▲
  Layer 1: HTML & Static CSS HTTP Status Probes
```

---

## 2. Step-by-Step Verification Script Recipes

### Step 1: Origin Endpoint & Font Probes (cURL)
```bash
# 1. Verify HTML entrypoint returns 200 OK
curl -ILs https://ai.zeo.org/chat | grep "HTTP/"

# 2. Verify font binaries serve with correct MIME and HTTP 200
curl -ILs https://ai.zeo.org/fonts/AkagiPro-Book.woff2 | grep -E "HTTP/|content-type|content-length"
curl -ILs https://ai.zeo.org/fonts/Gilroy-Bold.woff2 | grep -E "HTTP/|content-type|content-length"
```

---

### Step 2: Automated Font & Style Inspection (via agent-browser)
Launch the browser, navigate to the application, and evaluate the rendered DOM:

```bash
# 1. Open the target page
agent-browser open https://ai.zeo.org/chat

# 2. Inspect computed typography and font-face loading status
agent-browser eval '({
  bodyFont: getComputedStyle(document.body).fontFamily,
  buttonFont: document.querySelector("button") ? getComputedStyle(document.querySelector("button")).fontFamily : null,
  headingFont: document.querySelector("h1, h2, h3") ? getComputedStyle(document.querySelector("h1, h2, h3")).fontFamily : null,
  fontsLoaded: Array.from(document.fonts.values())
    .filter(f => f.status === "loaded")
    .map(f => ({ family: f.family, weight: f.weight }))
})'
```

**Expected Success Signal**:
- `bodyFont` contains `'Akagi Pro'` or `'Akagi'`.
- `buttonFont` contains `'Gilroy'`.
- `fontsLoaded` lists `Akagi Pro` and `Gilroy` with `status: "loaded"`.

---

### Step 3: Dual-Mode Visual Proof Capture
Capture both Light and Dark modes to guarantee identical visual weight and zero contrast regressions:

```bash
# 1. Capture Light Mode view
agent-browser eval '
  document.documentElement.classList.remove("dark");
  localStorage.setItem("archestra-theme-mode", "light");
'
agent-browser screenshot /tmp/theme_verified_light.png

# 2. Toggle Dark Mode and capture
agent-browser eval '
  document.documentElement.classList.add("dark");
  localStorage.setItem("archestra-theme-mode", "dark");
'
agent-browser screenshot /tmp/theme_verified_dark.png
```

---

### Step 4: Focused Interaction State Verification
Inspect the focus state of the primary input or chat composer to guarantee zero neon border pollution:

```bash
# Focus the composer textarea
agent-browser eval '
  const textarea = document.querySelector("textarea");
  if (textarea) textarea.focus();
'

# Capture focused state screenshot
agent-browser screenshot /tmp/theme_verified_dark_focused.png
```

---

## 3. The 10-Point Final Sign-Off Checklist

Before handoff, systematically verify every item:
- [ ] 1. **Zero Ad-Hoc Selectors**: No `form:has(...)`, `div > textarea`, or component overrides in CSS.
- [ ] 2. **Neutral Hairlines**: All resting borders and card dividers are 100% neutral (`#e8ecf2` / `#232e40`).
- [ ] 3. **The Two Reds Principle**: Only the primary action button uses the brand accent color.
- [ ] 4. **Accessible Focus Ring**: Focus ring satisfies WCAG 2.2 non-text contrast ($\ge 3.0:1$) with slate neutrality (`#526585`).
- [ ] 5. **Hover Affordance**: Hover state (`--accent`) is perceptually distinct from card background in dark mode.
- [ ] 6. **Zero Remote Fonts**: No Google Fonts or CDN requests in network waterfall.
- [ ] 7. **Turkish Glyph Integrity**: Font renders `ğ, Ğ, ş, Ş, ı, İ` with zero baseline jumping or per-glyph fallback.
- [ ] 8. **Strict Radii**: All interactive containers adhere to 4px (`--radius: 0.25rem`).
- [ ] 9. **Dark Mode Vector Parity**: Logo text is crisp white on dark mode, not black-on-black.
- [ ] 10. **Clean Exit**: Headless browser session closed (`agent-browser close`).
