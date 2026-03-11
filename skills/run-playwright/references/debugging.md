# Debugging and Diagnostics

How to capture console logs, inspect network requests, record traces,
troubleshoot common issues, and diagnose page problems in `playwright-cli`.

---

## Table of Contents

- [What debug commands return](#what-debug-commands-return)
- [Console logs](#console-logs)
- [Network logs](#network-logs)
- [Tracing](#tracing)
- [eval for truth checks](#eval-for-truth-checks)
- [run-code for diagnostics](#run-code-for-diagnostics)
- [Error diagnosis workflow](#error-diagnosis-workflow)
- [Troubleshooting guide](#troubleshooting-guide)
- [Public site noise](#public-site-noise)

---

## What debug commands return

Key correction: `console` and `network` return **artifact file paths**,
not inline text. Those files may contain useful entries or may be empty.

You must:
1. Run the command.
2. Open the returned file path.
3. Inspect the file content before claiming the page is clean or broken.

Artifact paths are implementation details — use the path the CLI returns,
do not guess based on repo layout.

---

## Console logs

### Basic usage

```bash
console
console error
console warning
console --clear
```

### Workflow: capture errors around an action

```bash
console --clear
# Reproduce the issue
click <button-ref>
snapshot
console error
```

Then open the returned file path and inspect its content.

### Filter by level

| Command | What it captures |
|---------|-----------------|
| `console` | All console output |
| `console error` | Only error-level messages |
| `console warning` | Only warnings |
| `console info` | Only info messages |

### Clear and re-capture

```bash
console --clear
# Perform actions
console error
# Inspect the artifact file
```

### What console logs look like

On a typical site, console output can include:
- JavaScript errors (uncaught exceptions, type errors)
- Network-related failures (405, 400, 429 responses logged to console)
- Framework warnings (React, Next.js hydration warnings)
- Browser-internal messages (GPU warnings, ReadPixels)
- Telemetry or analytics noise

**Do not automatically treat all console errors as bugs.** Interpret them
in context of the flow you are testing.

---

## Network logs

### Basic usage

```bash
network
network --static
network --clear
```

### Workflow: capture network around an action

```bash
network --clear
# Reproduce the issue
click <submit-ref>
snapshot
network
```

### Include static assets

```bash
network --static
```

Use `--static` when you need to check for broken images, CSS, or JavaScript files.

### What to look for in network logs

| Indicator | What it means |
|-----------|---------------|
| 4xx status | Client error (bad request, unauthorized, not found) |
| 5xx status | Server error |
| Missing requests | Expected API call not made |
| CORS errors | Cross-origin request blocked |
| Rate limiting (429) | Being throttled |
| Redirects (3xx) | Unexpected navigation |

### Network request details

To get more details about specific requests:

```bash
run-code 'async (page) => {
  const response = await page.waitForResponse(r => r.url().includes("/api/data"))
  return {
    url: response.url(),
    status: response.status(),
    headers: response.headers()
  }
}'
```

---

## Tracing

### Record a trace

```bash
tracing-start
# ... perform actions ...
tracing-stop
```

The trace file can be viewed in the Playwright Trace Viewer for detailed
step-by-step analysis including:
- screenshots at each action
- DOM snapshots
- network requests
- console logs

### When to use tracing

Use tracing when:
- A bug is hard to reproduce
- You need a detailed timeline of events
- You want to share evidence of a flow with someone else
- Debugging complex multi-step interactions

---

## eval for truth checks

`eval` is the most reliable way to verify browser state.

### Page context checks

```bash
eval "() => document.title"
eval "() => window.location.href"
eval "() => document.readyState"
eval "() => document.querySelectorAll('.item').length"
eval "() => document.cookie"
```

### Element context checks

```bash
eval "(el) => el.value" <ref>
eval "(el) => el.textContent" <ref>
eval "(el) => el.checked" <ref>
eval "(el) => el.disabled" <ref>
eval "(el) => el.getAttribute('aria-label')" <ref>
eval "(el) => getComputedStyle(el).display" <ref>
eval "(el) => getComputedStyle(el).color" <ref>
eval "(el) => el.getBoundingClientRect()" <ref>
```

### Why eval is more trustworthy than command headers

In several real tests, `eval "() => window.location.href"` was more
reliable than the URL shown in command output headers, especially
after tab switches or unusual navigation.

Use `eval` when correctness matters — not the surrounding metadata.

---

## run-code for diagnostics

### Inspect page performance

```bash
run-code 'async (page) => {
  const timing = await page.evaluate(() => JSON.stringify(performance.timing))
  return JSON.parse(timing)
}'
```

### Check for JavaScript errors

```bash
run-code 'async (page) => {
  const errors = []
  page.on("pageerror", err => errors.push(err.message))
  await page.waitForTimeout(2000)
  return errors
}'
```

### Inspect cookies

```bash
run-code 'async (page) => {
  return await page.context().cookies()
}'
```

### Check localStorage

```bash
eval "() => JSON.stringify(localStorage)"
```

### Check sessionStorage

```bash
eval "() => JSON.stringify(sessionStorage)"
```

### Inspect network responses programmatically

```bash
run-code 'async (page) => {
  const responses = []
  page.on("response", r => {
    if (r.status() >= 400) {
      responses.push({ url: r.url(), status: r.status() })
    }
  })
  await page.reload()
  await page.waitForLoadState("networkidle")
  return responses
}'
```

---

## Error diagnosis workflow

### Step 1: Capture the current state

```bash
snapshot
screenshot --filename=current-state.png
eval "() => window.location.href"
```

### Step 2: Check for errors

```bash
console error
network
```

### Step 3: Reproduce and capture

```bash
console --clear
network --clear
# Reproduce the issue step by step
click <problem-button-ref>
snapshot
screenshot --filename=after-click.png
console error
network
```

### Step 4: Combine all evidence

```bash
run-code 'async (page) => ({
  url: page.url(),
  title: await page.title(),
  readyState: await page.evaluate(() => document.readyState)
})'
screenshot --filename=diagnosis-final.png
```

### Full diagnosis template

```bash
# 1. Initial state
open <url>
snapshot
screenshot --filename=step-0-initial.png
console --clear
network --clear

# 2. Reproduce
click <trigger-ref>
snapshot
screenshot --filename=step-1-after-action.png

# 3. Collect evidence
console error
network
eval "() => window.location.href"
eval "() => document.title"

# 4. Final state
screenshot --filename=step-2-final.png
```

---

## Troubleshooting guide

### "Ref not found"

Refs are stale. Re-snapshot:

```bash
snapshot
```

### Upload fails with modal-state error

Click the file chooser trigger before calling `upload`:

```bash
click <upload-trigger-ref>
upload /absolute/path/to/file
```

### Command did not print a snapshot

Not all commands auto-print. Always follow with `snapshot`.

### URL or page header seems wrong

Use `eval "() => window.location.href"` for truth.

### Page appears blank

```bash
run-code 'async (page) => {
  await page.waitForSelector("body > *", { state: "visible", timeout: 10000 })
  return "content visible"
}'
snapshot
```

### Click does nothing

Re-snapshot and retry with fresh ref.

### Form submission hangs

```bash
click <submit-ref>
run-code 'async (page) => {
  await page.waitForResponse(r => r.url().includes("/api/submit"))
  return "response received"
}'
```

---

## Public site noise

Production sites emit console/network noise (telemetry, anti-bot, GPU warnings, 429s) — these are **not** your app's bugs. Tie any bug claim back to the actual flow you reproduced.
