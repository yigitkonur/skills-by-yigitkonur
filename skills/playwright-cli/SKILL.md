---
name: playwright-cli
description: >
  Complete operational guide for browser automation with @anthropic-ai/playwright-cli.
  Covers session bootstrap, the observe-act loop, element refs, tab management,
  form filling, screenshots, JavaScript evaluation, console/network debugging,
  responsive testing, dark mode, and multi-agent coordination.
  Use this skill whenever you need to: open a browser and navigate to a URL,
  click buttons or links, fill out forms, take screenshots or PDFs, extract data
  from web pages, verify UI changes visually, test responsive layouts, check for
  console errors or network failures, run JavaScript in the page, manage browser
  tabs, record video or traces, handle dialogs, upload files, or coordinate
  multiple agents sharing a single browser session.
  Also use when the user says things like "check the website", "verify the UI",
  "take a screenshot", "test the form", "scrape the page", "automate the browser",
  "open chromium", "visual regression", or "playwright".
---

# Browser Automation with playwright-cli

## How playwright-cli works

`playwright-cli` gives you a headless Chromium browser controlled through bash commands.
Every command that changes the page returns a **snapshot** — a YAML accessibility tree
where each interactive element has a **ref** like `e5`, `e12`. You use these refs to
click, fill, and interact. Refs are ephemeral: they die on any page change and must
be refreshed via `snapshot`.

## Bootstrap (run once before any browser work)

```bash
which playwright-cli || npm install -g @anthropic-ai/playwright-cli@latest
PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=true npx playwright install chromium
playwright-cli session-stop 2>/dev/null    # kill stale sessions
playwright-cli config --browser=chromium
```

After all work is done: `playwright-cli session-stop-all`

## The observe-act loop (your core workflow)

This is how every interaction works. Do not skip steps.

```
open <url>            → page loads, snapshot returned
snapshot              → read the tree, find element refs
screenshot --full-page --filename=step-1.png → see the visual state
[decide what to do based on what you see]
click <ref>  /  fill <ref> "value"  /  other action
snapshot              → get fresh refs (mandatory after every action)
screenshot --filename=step-2.png → confirm the result
[repeat until task is complete]
```

Use `snapshot` for **interaction** (to get refs). Use `screenshot` for **visual judgment**
(to see what the page actually looks like). Both, always.

## The cardinal rule: refs die on ANY page change

After `click`, `open`, `hover`, `reload`, `go-back`, `tab-select`, or any navigation:
run `snapshot` to get fresh refs before interacting with elements.

Stale refs either error or silently target the wrong element. There are no warnings.
The pattern is always: **action -> snapshot -> use new refs**.

## CLI-first principle

Use individual CLI commands (not `run-code` or standalone scripts) for:
- **Tab management**: `tab-new`, `tab-list`, `tab-select`, `tab-close`
- **Navigation**: `open`, `go-back`, `go-forward`, `reload`
- **Observation**: `snapshot`, `screenshot`
- **Simple interaction**: `click`, `fill`, `select`, `check`, `press`
- **DevTools**: `console error`, `network`

Use `run-code` only when you need something the CLI can't do:
- Waiting on conditions (`page.waitForSelector`, `page.waitForResponse`)
- Network interception or request monitoring
- Setting cookies, geolocation, or media emulation
- Complex multi-step page-level operations in a single atomic block

The reason: CLI commands return snapshots and maintain the observe-act discipline.
`run-code` operates outside that loop — you lose the ref-based interaction model.
Do not use `run-code` as a shortcut to avoid the CLI tab/snapshot workflow.

---

## Essential commands

### Navigation
```bash
open <url>                        # navigate to URL
go-back                           # browser back
go-forward                        # browser forward
reload                            # refresh page
```

### Observation
```bash
snapshot                          # get accessibility tree + element refs
screenshot --full-page --filename=name.png   # full-page screenshot
screenshot <ref> --filename=name.png         # element screenshot
```

### Interaction
```bash
click <ref>                       # click element
fill <ref> "text"                 # clear + type into input (replaces content)
fill <ref> "text" --submit        # fill + press Enter (login/search shortcut)
type "text"                       # append to focused element (keyboard testing only)
select <ref> "option-value"       # select dropdown option
check <ref>                       # check checkbox
uncheck <ref>                     # uncheck checkbox
hover <ref>                       # hover over element
dblclick <ref>                    # double-click
drag <source-ref> <target-ref>   # drag and drop
upload /path/to/file              # upload file
```

### Keyboard
```bash
press Enter                       # press a key
press Tab
press ArrowDown
press Control+a                   # key combinations
keydown Shift                     # hold key down
keyup Shift                       # release key
```

### JavaScript evaluation
```bash
eval "() => document.title"                     # run JS in page context
eval "(el) => el.value" <ref>                   # run JS against element
eval "() => window.location.href"               # get current URL
run-code 'async (page) => { ... }'              # full Playwright API access
```

### Tabs
```bash
tab-new                           # open new tab (opens about:blank!)
open <url>                        # then navigate in that tab
tab-list                          # list all tabs with indexes
tab-select <index>                # switch to tab by index (then snapshot!)
tab-close <index>                 # close specific tab (then tab-list!)
```

### Multi-tab workflow (follow this exact sequence)
```bash
# 1. Open first page
open https://example.com
snapshot                          # refs for tab 0
screenshot --filename=tab0.png

# 2. Open second tab — always two steps
tab-new                           # opens about:blank, NOT the URL!
open https://other-site.com       # now navigate
snapshot                          # refs for tab 1
screenshot --filename=tab1.png

# 3. Switch back to first tab
tab-select 0
snapshot                          # MANDATORY — refs from tab 1 are dead
eval "() => window.location.href" # verify you're on the right page

# 4. Close a tab — then reorient
tab-close 1
tab-list                          # MANDATORY — indexes shifted

# 5. Verify remaining tab
snapshot
screenshot --filename=final.png
```
Every `tab-select` MUST be followed by `snapshot`.
Every `tab-close` MUST be followed by `tab-list`.

### Dialogs
```bash
dialog-accept                     # accept alert/confirm/prompt
dialog-accept "text"              # accept prompt with input text
dialog-dismiss                    # dismiss/cancel dialog
```

### DevTools
```bash
console error                     # get console errors (returns FILE PATH)
network                           # get network log (returns FILE PATH)
console --clear                   # clear console log
network --clear                   # clear network log
```

### Session management
```bash
session-stop                      # stop current session
session-stop-all                  # stop all sessions (cleanup)
resize <width> <height>           # resize viewport
```

### Recording
```bash
video-start                       # start recording
video-stop                        # stop and save video
tracing-start                     # start trace
tracing-stop                      # stop and save trace
pdf --filename=page.pdf           # save as PDF
```

---

## Critical gotchas (read these — they prevent most failures)

### 1. `tab-new` opens about:blank, NOT the URL
```bash
# WRONG — page will be blank:
tab-new https://example.com

# CORRECT — two steps:
tab-new
open https://example.com
```

### 2. Snapshots lie about form values
Snapshots show the HTML tree, not current input values. To verify a fill worked:
```bash
fill <ref> "hello@example.com"
eval "(el) => el.value" <ref>       # returns "hello@example.com"
```

### 3. `console` and `network` return FILE PATHS, not content
```bash
console error    # outputs: /path/to/console-errors.log
# You must READ that file to see the actual errors
```

### 4. `close` kills the entire browser session
If you're a sub-agent sharing a browser, use `tab-close <index>` to close YOUR tab.
Never use `close` — it destroys the session for all agents.

### 5. Tab indexes shift after `tab-close` — always run `tab-list`
After closing a tab, remaining tab indexes change. You must run `tab-list`
immediately after every `tab-close` before selecting or closing another tab.
Similarly, after every `tab-select`, run `snapshot` to get fresh refs for the
new active tab. These are not optional — skipping them causes stale index and
stale ref bugs that are silent and hard to debug.

### 6. Multi-tab "Page URL" header can lie
In multi-tab scenarios, the URL shown in command output may be stale.
Use `eval "() => window.location.href"` for the truth.

### 7. `fill` vs `type` — they are not interchangeable
- `fill <ref> "text"` — clears the field first, sets value, targets by ref. Use this 95% of the time.
- `type "text"` — appends to whatever is focused, no ref targeting. Only for keyboard-specific testing.

### 8. Dialog blocks everything
If you see "modal state" error, a dialog (alert/confirm/prompt) is blocking.
Run `dialog-accept` or `dialog-dismiss` before doing anything else.

### 9. `eval` — page context vs element context
```bash
# Page context (no ref) — access window, document, globals:
eval "() => document.title"

# Element context (with ref) — first arg is the element:
eval "(el) => el.textContent" <ref>

# Don't return DOM nodes — return extracted data:
eval "() => [...document.querySelectorAll('a')].map(a => a.href)"
```

### 10. `run-code` quoting
Single quotes outer, double quotes inner:
```bash
run-code 'async (page) => { await page.waitForSelector(".loaded"); return "done"; }'
```

---

## Verification patterns

### Page health check (run after every `open`)
```bash
open <url>
console error           # read the returned file — check for JS errors
network                 # read the returned file — check for 4xx/5xx
```

### Form verification
```bash
fill <ref> "value"
eval "(el) => el.value" <ref>              # verify it stuck
screenshot --filename=form-filled.png      # visual evidence
click <submit-ref>
snapshot                                    # check result page
eval "() => window.location.href"          # confirm navigation
```

### Viewport sweep (responsive testing)
```bash
resize 1280 720  → screenshot --full-page --filename=desktop.png
resize 768 1024  → screenshot --full-page --filename=tablet.png
resize 375 812   → screenshot --full-page --filename=mobile.png
```

### Dark mode toggle
```bash
# Method 1 — system preference (most reliable):
run-code 'async (page) => { await page.emulateMedia({ colorScheme: "dark" }); }'

# Method 2 — class-based:
eval "() => document.documentElement.classList.add('dark')"

# Method 3 — localStorage:
eval "() => { localStorage.setItem('theme', 'dark'); location.reload(); }"
```

### Layout integrity checks
```bash
eval "() => document.body.scrollWidth > window.innerWidth"   # horizontal overflow?
eval "() => [...document.querySelectorAll('img')].filter(i => !i.complete).length"  # broken images?
```

### Computed style verification
```bash
eval "(el) => getComputedStyle(el).color" <ref>
eval "(el) => getComputedStyle(el).fontSize" <ref>
eval "(el) => el.getBoundingClientRect()" <ref>          # position + dimensions
```

### Soft 404 detection (SPAs return 200 for everything)
```bash
eval "() => document.title"
eval "() => document.querySelector('h1')?.textContent"
```

---

## Sub-agent rules (if you are a tab tenant, not the session owner)

Your lifecycle as a sub-agent:
```
tab-new → open <url> → [your work] → tab-close <your-index>
```

- Never create sessions. Never run `close`.
- Only `tab-close <index>` to close YOUR tab when done.
- Your tab shares cookies and localStorage with other agents' tabs.

---

## Reference files

For detailed command documentation, patterns, and advanced recipes:

- **[Command reference](references/command-reference.md)** — Full syntax and options for every command
- **[Form and data extraction](references/form-and-data.md)** — Form filling, eval patterns, data scraping
- **[Session and tabs](references/session-and-tabs.md)** — Session lifecycle, multi-tab coordination, config
- **[Visual testing](references/visual-testing.md)** — Screenshots, responsive testing, dark mode, viewports
- **[Debugging](references/debugging.md)** — Console logs, network monitoring, tracing, run-code recipes
- **[Orchestrator guide](references/orchestrator-guide.md)** — Multi-agent coordination, verification levels, brief templates
