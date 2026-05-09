# Screenshots, PDF, Video, And Visual Checks

Use this reference for visual evidence, responsive checks, PDFs, videos, and artifact handling in `playwright-cli`.

## Artifact Rules

- `screenshot` defaults to a timestamped `page-{timestamp}.png` when `--filename` is omitted.
- `pdf --filename=...` writes the named PDF.
- `video-start [filename]` starts recording; `video-stop` returns/saves the video artifact.
- Artifact location can be affected by CLI config such as `outputDir`.
- The returned path or Markdown artifact link is the source of truth. Record that exact path in the final answer.

## Screenshots

Viewport screenshot:

```bash
playwright-cli screenshot --filename=current-view.png
```

Full-page screenshot:

```bash
playwright-cli screenshot --full-page --filename=full-page.png
```

Element screenshot:

```bash
playwright-cli screenshot e5 --filename=element.png
```

Generated filename:

```bash
playwright-cli screenshot
```

Use explicit filenames for workflows with multiple captures.

## Naming

Use names that encode state:

| Example | Meaning |
|---|---|
| `homepage-desktop-light.png` | desktop viewport, light mode |
| `login-after-submit.png` | post-submit state |
| `mobile-cart-drawer.png` | mobile viewport with cart open |
| `checkout-error-503.png` | error state after mocked 503 |

## Pair Visuals With State Proof

Screenshots are supporting evidence. Pair them with state:

```bash
playwright-cli screenshot --filename=after-filter.png
playwright-cli eval "() => window.location.href"
playwright-cli snapshot
```

For forms:

```bash
playwright-cli eval "(el) => el.value" e3
playwright-cli screenshot --filename=form-filled.png
```

For diagnosis:

```bash
playwright-cli console error
playwright-cli requests --filter="/api/"
playwright-cli screenshot --filename=diagnosis.png
```

## Responsive Checks

```bash
playwright-cli resize 1280 720
playwright-cli screenshot --full-page --filename=desktop.png

playwright-cli resize 768 1024
playwright-cli screenshot --full-page --filename=tablet.png

playwright-cli resize 375 812
playwright-cli screenshot --full-page --filename=mobile.png
```

Wait for layout-specific content before capture when needed:

```bash
playwright-cli resize 375 812
playwright-cli run-code "async page => {
  await page.waitForSelector('[data-testid=mobile-nav]', { state: 'visible' });
}"
playwright-cli screenshot --full-page --filename=mobile-settled.png
```

## Dark Mode

```bash
playwright-cli run-code "async page => { await page.emulateMedia({ colorScheme: 'dark' }); }"
playwright-cli screenshot --full-page --filename=dark-mode.png

playwright-cli run-code "async page => { await page.emulateMedia({ colorScheme: 'light' }); }"
playwright-cli screenshot --full-page --filename=light-mode.png
```

If the app uses a theme toggle or localStorage, verify the actual state with `eval`.

## PDF

```bash
playwright-cli pdf --filename=page.pdf
```

Use PDF for printable reports or long static documents where a full-page screenshot is unwieldy.

## Video

```bash
playwright-cli video-start flow.webm
# perform the flow
playwright-cli video-chapter "Checkout submit"
playwright-cli video-stop
```

Use video for complex interaction sequences where a static screenshot is insufficient. Return the video artifact path.

## Trace Viewer

Trace capture lives in `references/debugging.md`, but visual review often ends with trace inspection:

```bash
playwright-cli tracing-start
# reproduce
playwright-cli tracing-stop
npx playwright show-trace .playwright-cli/trace.zip
```

Use the path returned by `tracing-stop`; `.playwright-cli/trace.zip` is the common default, not a guarantee.

## Layout Integrity Checks

Horizontal overflow:

```bash
playwright-cli eval "() => document.body.scrollWidth > window.innerWidth"
```

Broken images:

```bash
playwright-cli eval "() => [...document.querySelectorAll('img')].filter(i => !i.complete || i.naturalWidth === 0).length"
```

Element box:

```bash
playwright-cli eval "(el) => el.getBoundingClientRect()" e5
```

Element fully in viewport:

```bash
playwright-cli eval "(el) => {
  const r = el.getBoundingClientRect();
  return r.top >= 0 && r.left >= 0 && r.bottom <= window.innerHeight && r.right <= window.innerWidth;
}" e5
```

## Lazy Content Sweep

```bash
playwright-cli mousewheel 0 100
playwright-cli eval "() => window.scrollY"
playwright-cli screenshot --filename=fold-01.png
playwright-cli mousewheel 0 900
playwright-cli screenshot --filename=fold-02.png
```

If a pinned older build scrolls the wrong axis, swap `dx`/`dy` and verify with `window.scrollY` before continuing.
