# Common Automation Patterns

Tested workflows for login, search, data extraction, downloads,
cookie/storage management, and other common browser automation tasks
in `playwright-cli`.

---

## Table of Contents

- [Login flow](#login-flow)
- [Search and filter flow](#search-and-filter-flow)
- [Data extraction](#data-extraction)
- [Download handling](#download-handling)
- [Cookie and storage management](#cookie-and-storage-management)
- [Network interception](#network-interception)
- [Dialog handling](#dialog-handling)
- [Pagination and state persistence](#pagination-and-state-persistence)
- [E2E verification workflow](#e2e-verification-workflow)

---

## Login flow

> **Steering experience:** Login flows commonly involve redirects. Always verify the final URL with `eval "() => window.location.href"` after login, not just the page title. Some SPAs silently fail login without navigating.

### Standard email/password login

```bash
open https://app.example.com/login
snapshot
fill <email-ref> "admin@example.com"
fill <password-ref> "securepassword123"
click <submit-ref>
snapshot
eval "() => window.location.href"
screenshot --filename=after-login.png
```

### Login with redirect verification

```bash
open https://app.example.com/dashboard
# May redirect to login
eval "() => window.location.href"
snapshot

fill <email-ref> "user@example.com"
fill <password-ref> "password"
click <login-ref>

run-code 'async (page) => {
  await page.waitForURL("**/dashboard")
  return page.url()
}'
snapshot
screenshot --filename=dashboard-after-login.png
```

### OAuth popup login

```bash
run-code 'async (page) => {
  const [popup] = await Promise.all([
    page.waitForEvent("popup"),
    page.locator("button.google-login").click()
  ])
  await popup.waitForLoadState()
  return { title: await popup.title(), url: popup.url() }
}'
snapshot
eval "() => window.location.href"
```

### Save/restore authentication

```bash
state-save auth-state.json              # after login
state-load auth-state.json              # before next run
open https://app.example.com/dashboard
eval "() => window.location.href"
```

---

## Search and filter flow

```bash
# Search with form submission
fill <search-ref> "react hooks" --submit
snapshot
eval "() => window.location.href"

# Apply a filter
click <filter-ref>
snapshot

# Sort results
eval "(el) => [...el.options].map(o => ({ value: o.value, text: o.textContent.trim() }))" <sort-ref>
select <sort-ref> "price-low-to-high"
snapshot

# Verify result count
eval "() => document.querySelectorAll('.result-item').length"
```

---

## Data extraction

```bash
# Text from multiple elements
eval "() => [...document.querySelectorAll('.product-title')].map(el => el.textContent.trim())"

# Structured data
eval "() => [...document.querySelectorAll('.product-card')].map(card => ({
  title: card.querySelector('.title')?.textContent.trim(),
  price: card.querySelector('.price')?.textContent.trim()
}))"

# Table data
eval "() => [...document.querySelectorAll('table tbody tr')].map(row =>
  [...row.querySelectorAll('td')].map(c => c.textContent.trim())
)"

# Links
eval "() => [...document.querySelectorAll('a[href]')].map(a => ({
  text: a.textContent.trim(), href: a.href
})).filter(l => l.text)"
```

### Multi-page scraping

```bash
open "https://example.com/products?page=1"
eval "() => [...document.querySelectorAll('.product')].map(p => p.textContent.trim())"
open "https://example.com/products?page=2"
eval "() => [...document.querySelectorAll('.product')].map(p => p.textContent.trim())"
```

---

## Download handling

> **Steering experience:** Downloads require `run-code` with `waitForEvent("download")` — there is no direct CLI command for downloads. After saving, verify the file exists from outside the browser using bash.

### Save a single file

```bash
run-code 'async (page) => {
  const [download] = await Promise.all([
    page.waitForEvent("download"),
    page.locator("a.download-link").click()
  ])
  const filename = download.suggestedFilename()
  await download.saveAs("./" + filename)
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
    await download.saveAs("./" + filename)
    files.push(filename)
  }
  return files
}'
```

### Verify downloaded files

After downloading, verify the files exist on disk from outside the browser.

---

## Cookie and storage management

```bash
cookie-list                              # list all cookies
cookie-get session_id                    # get specific cookie
cookie-set auth_token "abc123"           # set cookie
cookie-delete session_id                 # delete cookie
cookie-clear                             # clear all

localstorage-list                        # list localStorage
localstorage-get theme                   # get value
localstorage-set theme "dark"            # set value
localstorage-delete theme                # delete key

sessionstorage-list                      # list sessionStorage
sessionstorage-get cart_items            # get value
sessionstorage-set cart_items "[]"       # set value

# Alternative via eval
eval "() => JSON.stringify(localStorage)"
eval "() => document.cookie"
```

---

## Network interception

### Set up a route (mock API)

```bash
route "https://api.example.com/users" --body='{"users":[]}'
```

### List active routes

```bash
route-list
```

### Remove a route

```bash
unroute "https://api.example.com/users"
```

### Advanced mocking via run-code

```bash
run-code 'async (page) => {
  await page.route("**/api/data", route => {
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ items: [{ id: 1, name: "Mock" }] })
    })
  })
  return "route set"
}'
```

---

## Dialog handling

### Accept a dialog (alert, confirm)

```bash
dialog-accept
```

### Dismiss a dialog

```bash
dialog-dismiss
```

### Accept a prompt with text

```bash
dialog-accept "user input value"
```

---

## Pagination and infinite scroll

```bash
# Click-based pagination
open "https://example.com/products"
snapshot
click <next-page-ref>
snapshot
eval "() => document.querySelectorAll('.product').length"

# Infinite scroll — verify scroll direction first
mousewheel 0 100
eval "() => window.scrollY"   # confirm scroll direction is correct
mousewheel 0 2000
run-code 'async (page) => {
  await page.waitForSelector(".feed-item:nth-child(20)", { state: "visible" })
  return "more items loaded"
}'
snapshot
```

---

## State persistence

> **Steering experience:** `state-save` and `state-load` are CLI prompt commands that save and restore cookies + storage. This is the fastest way to skip repeated login flows across multiple test runs.

```bash
state-save logged-in.json       # save cookies + storage
state-load logged-in.json       # restore state
open https://app.example.com    # resume authenticated
snapshot
```

| Use case | Pattern |
|----------|---------|
| Skip login across runs | `state-save` after login, `state-load` before next run |
| Test with specific user state | Pre-build state files for different users |

---

## E2E verification workflow

### Level 1 — Existence

```bash
open <url>
snapshot
screenshot --filename=exists.png
```

### Level 2 — Behavior

```bash
click <ref>
snapshot
eval "(el) => el.value" <ref>
screenshot --filename=behavior.png
```

### Level 3 — Visual matrix

```bash
resize 1280 720
run-code 'async (page) => { await page.emulateMedia({ colorScheme: "light" }); }'
screenshot --full-page --filename=desktop-light.png
run-code 'async (page) => { await page.emulateMedia({ colorScheme: "dark" }); }'
screenshot --full-page --filename=desktop-dark.png
resize 375 812
screenshot --full-page --filename=mobile-light.png
run-code 'async (page) => { await page.emulateMedia({ colorScheme: "dark" }); }'
screenshot --full-page --filename=mobile-dark.png
```

### Level 4 — Full regression

Level 3 + user flow checks + `console error` + `network` + before/after screenshots.


---

## Steering experiences summary

Key patterns discovered through real-world testing:

| Pattern | Why it matters |
|---|---|
| Always `cat` artifact files | `console`, `network`, `snapshot` write files, not stdout |
| Two-step tab: `tab-new` then `open` | `tab-new <url>` frequently opens `about:blank` |
| Test `mousewheel` direction first | Parameter order may be swapped between CLI versions |
| `--clear` is silent | `console --clear` / `network --clear` produce no output |
| Always `install --browser=chrome` | No-op when binary exists, prevents cryptic errors when missing |
| `eval` for truth, not headers | Command headers can show wrong URLs after tab switches |
| Upload = click trigger first | `upload` only works when file chooser dialog is active |
| `snapshot` = file, not inline | Must `cat` the printed file path to read the tree |
| `fill --submit` shortcut | Fills and submits in one command — great for search fields |
| `session-stop` for isolated | Forgetting cleanup leaks browser processes |
