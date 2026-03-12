# Navigation

How to navigate pages, wait for loading, manage browser history, and handle URLs
in `playwright-cli`.

---

## Table of Contents

- [Core navigation commands](#core-navigation-commands)
- [URL handling and quoting](#url-handling-and-quoting)
- [Page loading states](#page-loading-states)
- [Waiting for content](#waiting-for-content)
- [History navigation](#history-navigation)
- [Redirects and SPA navigation](#redirects-and-spa-navigation)
- [Page reload strategies](#page-reload-strategies)
- [Navigation verification](#navigation-verification)
- [Common navigation patterns](#common-navigation-patterns)

---

## Core navigation commands

### open

```bash
open <url>
```

Navigates to the given URL. Usually prints page metadata and a snapshot.

After `open`, always capture a fresh snapshot before interacting:

```bash
open https://example.com
snapshot
screenshot --filename=landing.png
```

### go-back

```bash
go-back
```

Navigates browser history backward. Equivalent to clicking the browser back button.

### go-forward

```bash
go-forward
```

Navigates browser history forward.

### reload

```bash
reload
```

Reloads the current page. Useful when you need a fresh page state or suspect
stale content.

**After any navigation command, run `snapshot` before using refs.** Then `cat` the snapshot file to read the actual tree.

---

## URL handling and quoting

### Quote URLs in zsh

> **Steering experience:** URL quoting issues are subtle — the command may appear to work but navigate to a truncated URL. Always verify with `eval "() => window.location.href"` after `open` to confirm the full URL arrived correctly.

URLs containing `?`, `&`, `#`, or other shell-sensitive characters must be quoted:

```bash
# WRONG — zsh may interpret & or ? before the CLI sees them
open https://www.example.com/search?q=test&page=2

# CORRECT
open "https://www.example.com/search?q=test&page=2"
```

### URLs with special characters

```bash
# Spaces in query params — use URL encoding or quotes
open "https://example.com/search?q=hello%20world"

# Hash fragments
open "https://example.com/docs#section-3"

# Anchored deep links
open "https://app.example.com/dashboard?tab=settings&view=profile"
```

### Verify the URL arrived correctly

```bash
open "https://example.com/search?q=test"
eval "() => window.location.href"
```

The `eval` check is more reliable than the printed page header,
especially after tab switches or redirects.

---

## Page loading states

Different pages require different wait strategies.

### Static pages

Most static pages are ready immediately after `open`:

```bash
open https://example.com
snapshot
```

### SPA / JavaScript-heavy pages

SPAs may render content after initial load. Use `run-code` to wait:

```bash
open https://app.example.com
run-code 'async (page) => {
  await page.waitForSelector("[data-testid=app-loaded]", { state: "visible" })
  return "ready"
}'
snapshot
```

### Pages with loading spinners

Wait for the spinner to disappear:

```bash
open https://dashboard.example.com
run-code 'async (page) => {
  await page.waitForSelector(".loading-spinner", { state: "hidden" })
  return "loaded"
}'
snapshot
screenshot --filename=dashboard-loaded.png
```

### Lazy-loaded content

Content below the fold may not load until scrolled.

> **Steering experience:** The `mousewheel <deltaX> <deltaY>` parameter order may be swapped in some CLI versions. Always test with a small scroll first: `mousewheel 0 100` then `eval "() => window.scrollY"`. If scrollY didn't increase, try `mousewheel 100 0`.

```bash
open https://example.com/long-page
snapshot
mousewheel 0 100
eval "() => window.scrollY"   # verify scroll direction first
mousewheel 0 900
run-code 'async (page) => {
  await page.waitForSelector(".lazy-section", { state: "visible" })
  return "lazy content visible"
}'
snapshot
```

---

## Waiting for content

### Wait for a specific element

```bash
run-code 'async (page) => {
  await page.waitForSelector("#results-container", { state: "visible" })
  return "results visible"
}'
snapshot
```

### Wait for a URL change

```bash
run-code 'async (page) => {
  await page.waitForURL("**/dashboard**")
  return page.url()
}'
snapshot
```

### Wait for a network response

```bash
run-code 'async (page) => {
  const resp = await page.waitForResponse(r => r.url().includes("/api/data"))
  return { url: resp.url(), status: resp.status() }
}'
```

### Wait for JavaScript readiness

```bash
run-code 'async (page) => {
  await page.waitForFunction(() => window.appReady === true)
  return "app ready"
}'
snapshot
```

### Timeout handling

Default waits can hang on slow pages. Set explicit timeouts:

```bash
run-code 'async (page) => {
  await page.waitForSelector(".content", { state: "visible", timeout: 10000 })
  return "done"
}'
```

---

## History navigation

### Navigate back and verify

```bash
open https://example.com/page-1
snapshot
open https://example.com/page-2
snapshot

go-back
snapshot
eval "() => window.location.href"
# Should show page-1
```

### Navigate forward

```bash
go-forward
snapshot
eval "() => window.location.href"
# Should show page-2
```

### Multi-step history

```bash
open https://example.com/a
open https://example.com/b
open https://example.com/c

go-back
go-back
eval "() => window.location.href"
# Should show /a
```

---

## Redirects and SPA navigation

### Detect redirects

```bash
open https://example.com/old-path
eval "() => window.location.href"
# If the page redirected, this shows the final URL
```

### SPA client-side navigation

SPA route changes may not trigger a full page load. After clicking
a navigation link in a SPA:

```bash
click <nav-link-ref>
run-code 'async (page) => {
  await page.waitForURL("**/settings")
  return page.url()
}'
snapshot
```

### Auth redirects

Login pages often redirect after successful auth:

```bash
open https://app.example.com/dashboard
# May redirect to /login
eval "() => window.location.href"
snapshot
# Fill login form, submit
# Then verify redirect back to dashboard
eval "() => window.location.href"
```

---

## Page reload strategies

### Simple reload

```bash
reload
snapshot
```

### Reload and wait for content

```bash
reload
run-code 'async (page) => {
  await page.waitForSelector("[data-ready=true]", { state: "visible" })
  return "ready"
}'
snapshot
```

### Clear cache and reload

```bash
run-code 'async (page) => {
  await page.evaluate(() => {
    caches.keys().then(keys => keys.forEach(k => caches.delete(k)))
  })
  await page.reload()
  return "reloaded"
}'
snapshot
```

---

## Navigation verification

### Verify current URL

```bash
eval "() => window.location.href"
```

### Verify page title

```bash
eval "() => document.title"
```

### Verify page loaded successfully

```bash
eval "() => document.readyState"
# Should return "complete"
```

### Full page health check after navigation

```bash
open https://example.com
snapshot
screenshot --filename=health-check.png
eval "() => document.title"
eval "() => window.location.href"
console error
network
```

---

## Common navigation patterns

```bash
# Open and verify
open https://example.com
snapshot
eval "() => window.location.href"

# Multi-step flow
click <product-link-ref>
snapshot
click <add-to-cart-ref>
snapshot
click <checkout-ref>
snapshot
eval "() => window.location.href"
```
