# Debugging and DevTools

## Table of Contents

- [Console Logs](#console-logs)
- [Network Monitoring](#network-monitoring)
- [JavaScript Evaluation (eval)](#javascript-evaluation-eval)
- [run-code (Full Playwright API)](#run-code-full-playwright-api)
- [Tracing](#tracing)
- [Video Recording](#video-recording)
- [Troubleshooting Guide](#troubleshooting-guide)

## Console Logs

### Basic usage
```bash
console              # all console messages → returns FILE PATH
console error        # only errors → returns FILE PATH
console warning      # only warnings → returns FILE PATH
console --clear      # clear the console log
```

### CRITICAL: console returns a FILE PATH, not content
```bash
console error
# Output: /path/to/.playwright-cli/console-errors-2024-01-15.log
# You MUST read that file to see actual errors:
# cat /path/to/.playwright-cli/console-errors-2024-01-15.log
```

This is the #1 console gotcha. The command outputs a file path. You need to read the file to see the actual console messages.

### Reading console output files
The file contains JSON-formatted log entries with:
- `type`: log, error, warning, info, debug
- `text`: the console message
- `url`: source URL
- `lineNumber`: source line
- `timestamp`: when it occurred

### Page health check pattern
```bash
open <url>
console error          # get the file path
# Read the file → check for JS errors
network               # get the file path
# Read the file → check for 4xx/5xx
```

## Network Monitoring

### Basic usage
```bash
network              # all network requests → returns FILE PATH
network --static     # include static resources (CSS, images, fonts)
network --clear      # clear the network log
```

### CRITICAL: network also returns a FILE PATH
Same as console — you must read the returned file to see actual network data.

### Reading network output files
The file contains request/response pairs with:
- `url`: request URL
- `method`: GET, POST, etc.
- `status`: HTTP status code
- `statusText`: status message
- `resourceType`: document, script, stylesheet, image, fetch, xhr
- `responseHeaders`: response headers
- `timing`: request timing information

### Common patterns
```bash
# Check for failed requests after page load
network
# Read file, filter for status >= 400

# Monitor API calls during interaction
network --clear          # start fresh
click <ref>              # trigger some action
network                  # capture what happened
# Read file, look for fetch/xhr requests
```

## JavaScript Evaluation (eval)

### Page context (no ref)
```bash
eval "() => document.title"
eval "() => window.location.href"
eval "() => document.querySelectorAll('.item').length"
eval "() => JSON.parse(localStorage.getItem('settings'))"
```

### Element context (with ref)
```bash
eval "(el) => el.value" <ref>
eval "(el) => el.textContent" <ref>
eval "(el) => el.checked" <ref>
eval "(el) => getComputedStyle(el).color" <ref>
eval "(el) => el.getBoundingClientRect()" <ref>
```

### Key rules
- Returns primitives and plain objects only
- Don't return DOM nodes — extract data first
- Use arrow functions: `"() => expr"` or `"(el) => expr"`
- Page context has no ref argument
- Element context requires a ref as the second argument

### Common gotchas
- `eval "document.title"` — WRONG. Must wrap in arrow function: `eval "() => document.title"`
- Returning a NodeList or HTMLElement — won't serialize. Map to plain data first.
- `eval "(el) => el.value"` without a ref — runs in page context, `el` is undefined

## run-code (Full Playwright API)

### When to use run-code (and when NOT to)

Use `run-code` for things CLI commands can't do:
- Waiting on dynamic conditions (`waitForSelector`, `waitForResponse`)
- Network interception and monitoring
- Setting cookies, geolocation, media emulation
- Complex atomic multi-step operations on the same page

Do NOT use `run-code` as a replacement for:
- `tab-new` / `tab-list` / `tab-select` / `tab-close` — use CLI tab commands
- `snapshot` — run-code doesn't return the accessibility tree with refs
- `screenshot` — use the CLI command for proper file naming
- `open` / `go-back` / `reload` — use CLI navigation commands
- `fill` / `click` / `select` — use CLI interaction commands with refs

The reason: CLI commands return snapshots with element refs and maintain the
observe-act loop. Using `run-code` to bypass this means you lose the ref-based
interaction model and skip mandatory observation steps.

### Basic syntax
```bash
run-code 'async (page) => { ... }'
```

### CRITICAL: Quoting
Single quotes outer, double quotes inner. This is because bash processes the outer quotes.
```bash
# CORRECT:
run-code 'async (page) => { await page.waitForSelector(".loaded"); return "done"; }'

# WRONG (bash interprets the inner quotes):
run-code "async (page) => { await page.waitForSelector('.loaded'); return 'done'; }"
```

### Common recipes

#### Wait for a loading state to finish
```bash
run-code 'async (page) => { await page.waitForSelector(".spinner", { state: "hidden" }); return "loaded"; }'
```

#### Wait for specific network request
```bash
run-code 'async (page) => {
  const response = await page.waitForResponse(r => r.url().includes("/api/data"));
  return { status: response.status(), url: response.url() };
}'
```

#### Intercept and monitor network requests
```bash
run-code 'async (page) => {
  let calls = [];
  page.on("response", r => { if (r.url().includes("api")) calls.push({ url: r.url(), status: r.status() }); });
  await page.reload();
  await page.waitForTimeout(2000);
  return calls;
}'
```

#### Set cookies
```bash
run-code 'async (page) => {
  await page.context().addCookies([{ name: "token", value: "abc123", url: "https://example.com" }]);
  return "cookie set";
}'
```

#### Emulate dark mode
```bash
run-code 'async (page) => { await page.emulateMedia({ colorScheme: "dark" }); }'
```

#### Grant geolocation permission
```bash
run-code 'async (page) => { await page.context().grantPermissions(["geolocation"]); }'
```

#### Set geolocation
```bash
run-code 'async (page) => {
  await page.context().setGeolocation({ latitude: 40.7128, longitude: -74.0060 });
  return "location set to NYC";
}'
```

#### Extract structured data from a table
```bash
run-code 'async (page) => {
  return await page.$$eval("table tbody tr", rows =>
    rows.map(row => [...row.querySelectorAll("td")].map(cell => cell.textContent.trim()))
  );
}'
```

#### Wait for navigation after click
```bash
run-code 'async (page) => {
  await Promise.all([
    page.waitForNavigation(),
    page.click("text=Submit")
  ]);
  return page.url();
}'
```

## Tracing

### Start and stop
```bash
tracing-start         # begin recording
# ... perform actions ...
tracing-stop          # save trace file
```

### What traces capture
- Screenshots at each step
- DOM snapshots
- Network requests
- Console logs
- Action timing

### Viewing traces
The trace file can be opened in the Playwright Trace Viewer (trace.playwright.dev)

## Video Recording

### Start and stop
```bash
video-start           # begin recording
# ... perform actions ...
video-stop            # save video file (WebM format)
```

## Troubleshooting Guide

### "modal state" error
A dialog (alert/confirm/prompt) is blocking all interaction.
```bash
dialog-accept         # or dialog-dismiss
```

### "ref not found" error
Refs are stale — they died after a page change.
```bash
snapshot              # get fresh refs
```

### Blank page after tab-new
You forgot to navigate after creating the tab.
```bash
open <url>            # navigate to intended page
```

### Unexpected behavior
Check the command syntax:
```bash
playwright-cli --help <command>
```

### Console errors you can't see
Remember, `console error` returns a FILE PATH. Read the file.

### Network failures you can't see
Same — `network` returns a FILE PATH. Read the file.

### Session seems stuck
```bash
session-stop          # stop current session
# Re-run bootstrap commands
```

### Multiple agents interfering
Tabs are isolated. If there's interference, it's shared cookies/localStorage.
Check with `eval "() => JSON.parse(localStorage.getItem('key'))"`
