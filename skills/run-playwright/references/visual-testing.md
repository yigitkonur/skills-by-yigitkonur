# Visual Testing and Screenshots

## Table of Contents

- [Core screenshot rules](#core-screenshot-rules)
- [Naming conventions](#naming-conventions)
- [Responsive testing](#responsive-testing)
- [Dark mode testing](#dark-mode-testing)
- [Before and after comparison](#before-and-after-comparison)
- [Layout integrity checks](#layout-integrity-checks)
- [Viewport sweep](#viewport-sweep)
- [When to trust screenshots](#when-to-trust-screenshots)

## Core screenshot rules

Use screenshots as evidence, not decoration.
Use them as one leg of the proof loop alongside `snapshot` for refs and `eval` for browser truth.

### Viewport screenshot

```bash
screenshot --filename=page-current-view.png
```

### Full-page screenshot

```bash
screenshot --full-page --filename=page-full.png
```

### Element screenshot

```bash
screenshot <ref> --filename=element.png
```

### Practical rules

- always use descriptive filenames;
- take a screenshot **after** the page is in the state you want to evaluate;
- pair screenshots with `snapshot` when you still need refs;
- do not assume screenshot timing implies app readiness;
- for stateful flows, pair the screenshot with `eval` if URL, selected state, or entered data matters.

## Naming conventions

Good filenames answer:
- what is this,
- at what step,
- under what conditions?

Examples:
- `search-before-filter.png`
- `search-after-4-stars.png`
- `desktop-light-homepage.png`
- `mobile-dark-cart-drawer.png`
- `upload-selected-file.png`

## Responsive testing

```bash
resize 1280 720
screenshot --full-page --filename=desktop.png

resize 768 1024
screenshot --full-page --filename=tablet.png

resize 375 812
screenshot --full-page --filename=mobile.png
```

If the UI is async, wait first:

```bash
run-code 'async (page) => {
  await page.waitForSelector("[data-testid=page-ready]", { state: "visible" })
  return "ready"
}'
screenshot --full-page --filename=desktop-ready.png
```

## Dark mode testing

### Method 1 — emulate preferred color scheme

```bash
run-code 'async (page) => { await page.emulateMedia({ colorScheme: "dark" }); }'
screenshot --full-page --filename=dark.png
```

### Method 2 — class toggle

```bash
eval "() => document.documentElement.classList.add('dark')"
screenshot --full-page --filename=dark-class.png
```

### Method 3 — local storage + reload

```bash
eval "() => { localStorage.setItem('theme', 'dark'); location.reload(); }"
snapshot
screenshot --full-page --filename=dark-storage.png
```

## Before and after comparison

```bash
screenshot --full-page --filename=BEFORE-desktop.png
resize 375 812
screenshot --full-page --filename=BEFORE-mobile.png

# make changes or reproduce flow

resize 1280 720
screenshot --full-page --filename=AFTER-desktop.png
resize 375 812
screenshot --full-page --filename=AFTER-mobile.png
```

Add waits first if hydration or lazy rendering would otherwise make the comparison unfair.
For commerce/search/filter/sort flows, also capture the post-action URL with `eval "() => window.location.href"` so the screenshot is not your only proof.

## Layout integrity checks

```bash
eval "() => document.body.scrollWidth > window.innerWidth"
eval "() => [...document.querySelectorAll('img')].filter(i => !i.complete).length"
eval "(el) => el.getBoundingClientRect()" <ref>
```

## Viewport sweep

Use manual fold capture when full-page screenshots miss lazy-loaded or sticky UI behavior:

```bash
screenshot --filename=fold-01.png
mousewheel 0 900
screenshot --filename=fold-02.png
mousewheel 0 900
screenshot --filename=fold-03.png
```

Note: low-level mouse command docs can be inconsistent. If scroll direction matters for a critical test, verify with one small movement first.

## When to trust screenshots

Trust screenshots most when you have also:
- verified the URL with `eval` if navigation matters,
- verified form values with `eval` if data entry matters,
- captured `console` / `network` artifacts if correctness matters,
- taken the screenshot only after the desired UI state actually settled.

A screenshot alone is rarely enough for stateful flows.
