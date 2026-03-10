# Async and Advanced Recipes

## Table of Contents

- [What this file is for](#what-this-file-is-for)
- [Validated boundary](#validated-boundary)
- [Safe `run-code` discipline](#safe-run-code-discipline)
- [Wait recipes](#wait-recipes)
- [Popup and new-window flows](#popup-and-new-window-flows)
- [Download flows](#download-flows)
- [Hidden input and file chooser fallbacks](#hidden-input-and-file-chooser-fallbacks)
- [Iframe access](#iframe-access)
- [Page-level inspection recipes](#page-level-inspection-recipes)
- [Known traps](#known-traps)

## What this file is for

Use this reference when the normal CLI loop is not expressive enough:

```text
open → snapshot → interact → snapshot → screenshot
```

This file is for the cases where you need the Playwright `page` object directly through `run-code`.

Typical reasons:

- waiting for async UI to settle,
- waiting for a URL or response,
- capturing popups or downloads,
- interacting with hidden file inputs,
- reading iframe content,
- or making one page-level check that would be awkward with refs alone.

## Validated boundary

The installed CLI exposes:

```text
run-code <code>
```

The reliable pattern observed in this repo is:

```bash
run-code 'async (page) => {
  await page.waitForSelector(".loaded")
  return "done"
}'
```

This file intentionally focuses on **safe Playwright API recipes inside `run-code`** rather than claiming that every advanced browser action has its own dedicated CLI command.

## Safe `run-code` discipline

### Quoting rule

Use single quotes outside and double quotes inside:

```bash
run-code 'async (page) => {
  await page.waitForSelector("[data-ready=true]")
  return "ready"
}'
```

### Re-entry rule

After `run-code`, do not trust old refs.
Even when `run-code` returns a convincing value, re-enter the normal CLI flow before continuing ref-driven work.

```bash
run-code 'async (page) => {
  await page.waitForSelector("[data-ready=true]")
  return "ready"
}'
snapshot
screenshot --filename=after-run-code.png
```

### Return-shape rule

Return strings, numbers, booleans, or plain JSON-style objects/arrays.
Do not try to return DOM nodes or handles.

## Wait recipes

### Wait for visible content

```bash
run-code 'async (page) => {
  await page.waitForSelector("[data-testid=results]", { state: "visible" })
  return "results visible"
}'
snapshot
```

### Wait for loading UI to disappear

```bash
run-code 'async (page) => {
  await page.waitForSelector(".spinner", { state: "hidden" })
  return "spinner gone"
}'
snapshot
```

### Wait for URL change

```bash
run-code 'async (page) => {
  await page.waitForURL("**/dashboard")
  return page.url()
}'
snapshot
```

### Wait for a specific response

```bash
run-code 'async (page) => {
  const response = await page.waitForResponse(r => r.url().includes("/api/profile"))
  return { url: response.url(), status: response.status() }
}'
```

### Wait for page-level readiness

```bash
run-code 'async (page) => {
  await page.waitForFunction(() => window.appReady === true)
  return "appReady"
}'
snapshot
```

## Popup and new-window flows

A popup is easiest to handle atomically inside `run-code`.

### Capture popup title and URL

```bash
run-code 'async (page) => {
  const [popup] = await Promise.all([
    page.waitForEvent("popup"),
    page.locator("a[target=_blank]").first().click()
  ])
  await popup.waitForLoadState()
  return { title: await popup.title(), url: popup.url() }
}'
```

### OAuth-style popup probe

```bash
run-code 'async (page) => {
  const [popup] = await Promise.all([
    page.waitForEvent("popup"),
    page.locator("button.oauth-google").click()
  ])
  await popup.waitForLoadState()
  return { popupTitle: await popup.title(), popupUrl: popup.url() }
}'
```

If the popup changes the main page state, re-enter the CLI loop:

```bash
snapshot
screenshot --filename=after-popup.png
```

## Download flows

Use Playwright's download event from `run-code`.

### Save one file

```bash
run-code 'async (page) => {
  const [download] = await Promise.all([
    page.waitForEvent("download"),
    page.locator("a.download-link").click()
  ])
  const filename = download.suggestedFilename()
  await download.saveAs(`./${filename}`)
  return { filename, url: download.url() }
}'
```

### Save multiple files

```bash
run-code 'async (page) => {
  const links = await page.locator("a.download").all()
  const files = []

  for (const link of links) {
    const [download] = await Promise.all([
      page.waitForEvent("download"),
      link.click()
    ])
    const filename = download.suggestedFilename()
    await download.saveAs(`./${filename}`)
    files.push(filename)
  }

  return files
}'
```

Practical rule: after saving files, verify where they landed before claiming success.

## Hidden input and file chooser fallbacks

The preferred upload workflow for the installed CLI is still:

```bash
click <upload-trigger-ref>
upload /absolute/path/to/file
```

Use `run-code` only when the page hides or customizes the real input enough that the normal modal-driven CLI path becomes awkward.
Keep uploaded test files inside allowed roots even when you are using a fallback.

### Hidden input fallback

```bash
run-code 'async (page) => {
  await page.locator("input[type=file]").setInputFiles(["/absolute/path/to/file"])
  return "uploaded"
}'
snapshot
screenshot --filename=file-selected.png
```

## Iframe access

When the target UI lives inside an iframe, use `run-code` to inspect or operate inside the frame.

```bash
run-code 'async (page) => {
  const frame = page.frameLocator("iframe")
  const text = await frame.locator("button").first().textContent()
  return text
}'
```

If iframe work changes visible page state, follow with:

```bash
snapshot
screenshot --filename=after-iframe-step.png
```

## Page-level inspection recipes

### Read cookies relevant to the current flow

```bash
run-code 'async (page) => {
  return await page.context().cookies()
}'
```

### Emulate dark mode before evidence capture

```bash
run-code 'async (page) => {
  await page.emulateMedia({ colorScheme: "dark" })
  return "dark mode emulated"
}'
screenshot --full-page --filename=dark-mode.png
```

### Combine logs with page truth

```bash
console --clear
network --clear
# reproduce the issue
console error
network
run-code 'async (page) => ({
  url: page.url(),
  title: await page.title()
})'
screenshot --filename=broken-state.png
```

## Known traps

### Trap: turning `run-code` into the default workflow

If the task is just click / fill / select / screenshot, use the CLI directly.
`run-code` is the escape hatch, not the main road.
After the hard step, return to `snapshot` + `eval`/`screenshot` evidence collection.

### Trap: keeping old refs after `run-code`

Any meaningful state change can invalidate refs.
Always recapture with `snapshot`.

### Trap: mixing shell quotes incorrectly

Prefer single quotes around the whole JavaScript function and double quotes inside it.

### Trap: skipping evidence after an advanced step

Even if `run-code` returns a nice value, also capture the new page state when correctness matters:

```bash
snapshot
screenshot --filename=after-advanced-step.png
```
