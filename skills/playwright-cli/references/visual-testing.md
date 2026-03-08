# Visual Testing and Screenshots

## Table of Contents

- [Screenshot Basics](#screenshot-basics)
- [Screenshot Naming Conventions](#screenshot-naming-conventions)
- [Responsive Testing](#responsive-testing)
- [Dark Mode Testing](#dark-mode-testing)
- [Before/After Comparison](#beforeafter-comparison)
- [Layout Integrity Checks](#layout-integrity-checks)
- [Viewport Sweep (fold-by-fold)](#viewport-sweep-fold-by-fold)
- [Lazy-Load Warm-Up](#lazy-load-warm-up)
- [PDF Capture](#pdf-capture)
- [Multi-Agent Screenshot Matrix](#multi-agent-screenshot-matrix)

## Screenshot Basics

### Viewport screenshot (default)
```bash
screenshot --filename=page-current-view.png
```
Captures only the visible viewport area.

### Full-page screenshot
```bash
screenshot --full-page --filename=page-complete.png
```
Captures the entire scrollable page from top to bottom. Stitches by scrolling internally.

### Element screenshot
```bash
screenshot <ref> --filename=element-detail.png
```
Captures only the element's bounding box. Overflow (shadows, dropdowns, tooltips) may be clipped.

### Key gotchas
- Always use `--filename=descriptive-name.png` — default timestamps are meaningless
- Format is always PNG (lossless, larger files)
- `--full-page` starts from top regardless of scroll position
- `--full-page` may miss lazy-loaded content — scroll first to trigger loading
- Element screenshots clip overflow — use viewport screenshot instead for dropdowns/tooltips
- Screenshots capture the instant — they don't wait for animations or network requests

## Screenshot Naming Conventions

Good filenames answer: What is being captured? When in the workflow? Under what conditions?

### Patterns
- Subject-State: `login-form-empty.png`, `login-form-filled.png`, `login-form-error.png`
- Page-Fold: `homepage-fold-01.png`, `homepage-fold-02.png`
- Page-Viewport: `pricing-320w-mobile.png`, `pricing-1280w-laptop.png`
- Step-Action: `step-01-cart-review.png`, `step-02-shipping.png`
- Before-After: `theme-before-toggle.png`, `theme-after-toggle.png`
- Component-Variant: `button-primary-default.png`, `button-primary-hover.png`

### Anti-patterns to avoid
- `screenshot.png` — overwrites every time
- `test.png`, `final.png` — no context
- Default timestamp names — meaningless on review
- Spaces in filenames — use hyphens

## Responsive Testing

### Standard viewport sweep
```bash
resize 1280 720
screenshot --full-page --filename=desktop.png

resize 768 1024
screenshot --full-page --filename=tablet.png

resize 375 812
screenshot --full-page --filename=mobile.png
```

### Comprehensive breakpoint coverage
```bash
resize 320 568    → screenshot --filename=bp-320-mobile-small.png
resize 375 812    → screenshot --filename=bp-375-mobile.png
resize 768 1024   → screenshot --filename=bp-768-tablet.png
resize 1024 768   → screenshot --filename=bp-1024-tablet-landscape.png
resize 1280 800   → screenshot --filename=bp-1280-laptop.png
resize 1920 1080  → screenshot --filename=bp-1920-desktop.png
```

### Viewport size affects everything
- Page screenshots capture exactly what fits in the viewport
- Horizontal overflow will be clipped in viewport mode
- Set viewport BEFORE taking screenshots
- `resize` does not trigger page reload — refs remain valid

## Dark Mode Testing

### Method 1 — System preference emulation (most reliable)
```bash
run-code 'async (page) => { await page.emulateMedia({ colorScheme: "dark" }); }'
screenshot --full-page --filename=page-dark-mode.png

# Reset to light:
run-code 'async (page) => { await page.emulateMedia({ colorScheme: "light" }); }'
```

### Method 2 — CSS class toggle
```bash
eval "() => document.documentElement.classList.add('dark')"
screenshot --full-page --filename=page-dark-class.png

# Reset:
eval "() => document.documentElement.classList.remove('dark')"
```

### Method 3 — Find and click the theme toggle
```bash
snapshot
# Find the theme toggle button in the snapshot
click <theme-toggle-ref>
snapshot
screenshot --full-page --filename=page-dark-toggled.png
```

### Method 4 — localStorage
```bash
eval "() => { localStorage.setItem('theme', 'dark'); location.reload(); }"
snapshot
screenshot --full-page --filename=page-dark-localstorage.png
```

### Full visual matrix (4 combinations)
```
Desktop + Light → screenshot --filename=desktop-light.png
Desktop + Dark  → screenshot --filename=desktop-dark.png
Mobile + Light  → screenshot --filename=mobile-light.png
Mobile + Dark   → screenshot --filename=mobile-dark.png
```

## Before/After Comparison

### Pattern
```bash
# BEFORE changes:
screenshot --full-page --filename=BEFORE-desktop.png
resize 375 812
screenshot --full-page --filename=BEFORE-mobile.png

# ... make changes ...

# AFTER changes:
resize 1280 720
screenshot --full-page --filename=AFTER-desktop.png
resize 375 812
screenshot --full-page --filename=AFTER-mobile.png
```

Read both pairs and report visual differences.

## Layout Integrity Checks

### Horizontal overflow detection
```bash
eval "() => document.body.scrollWidth > window.innerWidth"
# Returns true if content overflows horizontally
```

### Broken images
```bash
eval "() => document.querySelectorAll('img').length"           # total images
eval "() => [...document.querySelectorAll('img')].filter(i => !i.complete).length"  # broken
```

### Computed style verification
```bash
eval "(el) => getComputedStyle(el).color" <ref>
eval "(el) => getComputedStyle(el).fontSize" <ref>
eval "(el) => getComputedStyle(el).display" <ref>
eval "(el) => el.getBoundingClientRect()" <ref>
```

## Viewport Sweep (fold-by-fold)

When `--full-page` misses lazy-loaded or scroll-triggered content:
```bash
screenshot --filename=fold-01.png
mousewheel 0 900
screenshot --filename=fold-02.png
mousewheel 0 900
screenshot --filename=fold-03.png
mousewheel 0 900
screenshot --filename=fold-04.png
```

Use ~900px increments for slight overlap between folds.

## Lazy-Load Warm-Up

Scroll through the page first to trigger all lazy loading, then capture:
```bash
mousewheel 0 2000
mousewheel 0 2000
mousewheel 0 2000
mousewheel 0 -6000    # return to top
screenshot --full-page --filename=page-all-loaded.png
```

## PDF Capture
```bash
pdf --filename=page-printable.pdf
```
- Useful for document-style pages
- Respects print CSS media queries
- Alternative to screenshot for printable content

## Multi-Agent Screenshot Matrix

Dispatch 4 agents simultaneously for full coverage:

| Agent | Viewport | Theme | Filename |
|-------|----------|-------|----------|
| A | resize 1280 720 | light (default) | *-desktop-light.png |
| B | resize 1280 720 | dark (emulateMedia) | *-desktop-dark.png |
| C | resize 375 812 | light (default) | *-mobile-light.png |
| D | resize 375 812 | dark (emulateMedia) | *-mobile-dark.png |
