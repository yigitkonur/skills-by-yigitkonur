# Screenshots and Visual Testing

How to capture screenshots, test responsive layouts, compare visual states,
and use screenshots as evidence in `playwright-cli`.

---

## Table of Contents

- [Core screenshot rules](#core-screenshot-rules)
- [Screenshot types](#screenshot-types)
- [Naming conventions](#naming-conventions)
- [Responsive testing](#responsive-testing)
- [Dark mode testing](#dark-mode-testing)
- [Before and after comparison](#before-and-after-comparison)
- [PDF capture](#pdf-capture)
- [Layout integrity checks](#layout-integrity-checks)
- [Viewport sweep for lazy content](#viewport-sweep-for-lazy-content)
- [Video recording](#video-recording)
- [Screenshot as evidence](#screenshot-as-evidence)
- [Common screenshot patterns](#common-screenshot-patterns)

---

## Core screenshot rules

1. **Screenshots are evidence, not decoration.** Pair them with `snapshot`
   for refs and `eval` for truth checks.
2. **Always use descriptive filenames.** Answer: what, which step, what conditions.
3. **Take screenshots after the page settles.** Animations, loaders, and
   lazy content can produce misleading captures.
4. **A screenshot alone is rarely enough** for stateful flows. Pair with
   `eval "() => window.location.href"` or `eval "(el) => el.value"`.

---

## Screenshot types

### Viewport screenshot (above the fold)

```bash
screenshot --filename=current-view.png
```

Captures what is visible in the current viewport.

### Full-page screenshot

```bash
screenshot --full-page --filename=full-page.png
```

Captures the entire scrollable page, including content below the fold.

### Element screenshot

```bash
screenshot <ref> --filename=element.png
```

Captures a specific element. Useful for:
- isolated component testing
- capturing a specific form, card, or widget
- comparing individual UI elements before and after changes

### Screenshot without filename

```bash
screenshot
```

The CLI generates a timestamped filename in the `.playwright-cli/` artifact area.
Prefer explicit filenames for organized workflows.

---

## Naming conventions

Good filenames answer: **what**, **at what step**, **under what conditions**.

| Example | What it communicates |
|---------|---------------------|
| `homepage-desktop-light.png` | Desktop viewport, light theme |
| `login-after-submit.png` | Login page, post-submission state |
| `search-before-filter.png` | Search results, before applying filter |
| `search-after-4-stars.png` | After applying 4-star filter |
| `mobile-dark-cart-drawer.png` | Mobile, dark mode, cart drawer open |
| `upload-file-selected.png` | After selecting a file for upload |
| `checkout-step-2.png` | Second step of checkout flow |

---

## Responsive testing

### Resize viewport

```bash
resize 1280 720
screenshot --full-page --filename=desktop.png

resize 768 1024
screenshot --full-page --filename=tablet.png

resize 375 812
screenshot --full-page --filename=mobile.png
```

### Wait for responsive layout to settle

If the UI is async or uses CSS transitions:

```bash
resize 375 812
run-code 'async (page) => {
  await page.waitForSelector("[data-testid=mobile-nav]", { state: "visible" })
  return "mobile layout ready"
}'
screenshot --full-page --filename=mobile-settled.png
```

### Common viewport sizes

| Device class | Width × Height |
|-------------|----------------|
| Desktop HD | 1920 × 1080 |
| Desktop | 1280 × 720 |
| Tablet portrait | 768 × 1024 |
| Tablet landscape | 1024 × 768 |
| Mobile (iPhone) | 375 × 812 |
| Mobile small | 320 × 568 |

### Responsive test matrix

```bash
open https://example.com

resize 1280 720
screenshot --full-page --filename=desktop.png

resize 768 1024
screenshot --full-page --filename=tablet.png

resize 375 812
screenshot --full-page --filename=mobile.png
```

---

## Dark mode testing

### Method 1 — emulate preferred color scheme

```bash
run-code 'async (page) => {
  await page.emulateMedia({ colorScheme: "dark" })
  return "dark mode emulated"
}'
screenshot --full-page --filename=dark-mode.png
```

### Method 2 — toggle CSS class

```bash
eval "() => document.documentElement.classList.add('dark')"
screenshot --full-page --filename=dark-class.png
```

### Method 3 — localStorage theme

```bash
eval "() => { localStorage.setItem('theme', 'dark'); location.reload(); }"
run-code 'async (page) => {
  await page.waitForSelector("body", { state: "visible" })
  return "reloaded"
}'
snapshot
screenshot --full-page --filename=dark-storage.png
```

### Reset to light mode

```bash
run-code 'async (page) => {
  await page.emulateMedia({ colorScheme: "light" })
  return "light mode"
}'
screenshot --full-page --filename=light-mode.png
```

### Full theme matrix

```bash
resize 1280 720
run-code 'async (page) => { await page.emulateMedia({ colorScheme: "light" }); }'
screenshot --full-page --filename=desktop-light.png

run-code 'async (page) => { await page.emulateMedia({ colorScheme: "dark" }); }'
screenshot --full-page --filename=desktop-dark.png

resize 375 812
run-code 'async (page) => { await page.emulateMedia({ colorScheme: "light" }); }'
screenshot --full-page --filename=mobile-light.png

run-code 'async (page) => { await page.emulateMedia({ colorScheme: "dark" }); }'
screenshot --full-page --filename=mobile-dark.png
```

---

## Before and after comparison

### Visual diff workflow

```bash
# BEFORE state
screenshot --full-page --filename=BEFORE-desktop.png
resize 375 812
screenshot --full-page --filename=BEFORE-mobile.png

# Make changes or reproduce flow
resize 1280 720
# [... interaction steps ...]

# AFTER state
screenshot --full-page --filename=AFTER-desktop.png
resize 375 812
screenshot --full-page --filename=AFTER-mobile.png
```

### With wait for hydration

If the page uses lazy rendering or hydration, add waits:

```bash
run-code 'async (page) => {
  await page.waitForSelector("[data-hydrated=true]", { state: "visible" })
  return "hydrated"
}'
screenshot --full-page --filename=AFTER-hydrated.png
```

### Pair with URL proof for stateful flows

```bash
screenshot --filename=after-filter.png
eval "() => window.location.href"
```

---

## PDF capture

```bash
pdf --filename=page.pdf
```

Generates a PDF of the current page. Useful for:
- saving printable reports
- capturing content that screenshots miss (very long pages)
- archiving page state

---

## Layout integrity checks

### Check for horizontal overflow

```bash
eval "() => document.body.scrollWidth > window.innerWidth"
```

Returns `true` if content overflows horizontally (a layout bug).

### Check for broken images

```bash
eval "() => [...document.querySelectorAll('img')].filter(i => !i.complete || i.naturalWidth === 0).length"
```

### Get element bounding box

```bash
eval "(el) => el.getBoundingClientRect()" <ref>
```

### Verify element is visible in viewport

```bash
eval "(el) => {
  const r = el.getBoundingClientRect();
  return r.top >= 0 && r.left >= 0 && r.bottom <= window.innerHeight && r.right <= window.innerWidth;
}" <ref>
```

---

## Viewport sweep for lazy content

Full-page screenshots may miss lazy-loaded or sticky UI behavior.
Use manual fold capture instead:

```bash
screenshot --filename=fold-01.png
mousewheel 0 900
screenshot --filename=fold-02.png
mousewheel 0 900
screenshot --filename=fold-03.png
mousewheel 0 900
screenshot --filename=fold-04.png
```

Verify scroll direction works as expected with a small movement first if
precision matters.

> **Known quirk:** `mousewheel <deltaX> <deltaY>` parameter order may be swapped
> internally by the CLI (e.g. `mousewheel 0 900` scrolls horizontally instead of
> vertically). Always test with a small scroll first and verify with `eval "() =>
> window.scrollY"` before committing to a sweep.

---

## Video recording

### Record a workflow

```bash
video-start
# ... perform actions ...
video-stop
```

The CLI saves the video file. Use this for:
- capturing complex interaction sequences
- debugging flaky behavior
- creating evidence of a complete flow

---

## Screenshot as evidence

### When to trust a screenshot

Trust screenshots most when you have also:

| Check | Command |
|-------|---------|
| Verified the URL | `eval "() => window.location.href"` |
| Verified form values | `eval "(el) => el.value" <ref>` |
| Captured console/network | `console error` / `network` |
| Waited for UI to settle | `run-code` with `waitForSelector` |

### When screenshots are insufficient

- **Dynamic content** — text or numbers that change on reload
- **Invisible state** — cookies, localStorage, session data
- **Timing-sensitive UI** — animations mid-transition

For these, use `eval` to extract the truth value directly.

---

## Common screenshot patterns

### Page health check

```bash
open https://example.com
snapshot
screenshot --filename=initial.png
console error
network
```

### Form state capture

```bash
fill <ref> "test@example.com"
eval "(el) => el.value" <ref>
screenshot --filename=form-filled.png
```

### Post-submission verification

```bash
click <submit-ref>
snapshot
eval "() => window.location.href"
screenshot --filename=after-submit.png
```

### Component isolation

```bash
snapshot
screenshot <card-ref> --filename=product-card.png
screenshot <nav-ref> --filename=navigation-bar.png
```
