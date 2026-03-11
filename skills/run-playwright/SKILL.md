---
name: run-playwright
description: Use skill if you are automating a browser with @anthropic-ai/playwright-cli for navigation, forms, screenshots, tab flows, debugging, or small run-code steps.
---

# Playwright CLI

Automate browsers from the terminal using `playwright-cli`. The CLI gives you a browser session
controlled through commands, an accessibility-tree snapshot system with disposable element refs,
and artifact files for screenshots, console logs, and network captures.

## Decision tree

```
What do you need?
│
├── Navigate to a URL or wait for content
│   ├── open / go-back / go-forward / reload ────► Quick start (below)
│   ├── Wait for element or URL change ──────────► references/navigation.md
│   ├── Handle SPA / lazy-loaded content ────────► references/navigation.md
│   └── Verify current URL or page state ────────► references/navigation.md
│
├── Fill forms or interact with inputs
│   ├── fill / type / select / check ────────────► Quick start (below)
│   ├── Upload files ────────────────────────────► references/forms.md
│   ├── Date pickers and autocomplete ───────────► references/forms.md
│   ├── Multi-step wizard forms ─────────────────► references/forms.md
│   └── Verify form values ─────────────────────► references/forms.md
│
├── Take screenshots or test visuals
│   ├── Viewport / full-page / element ──────────► references/screenshots.md
│   ├── Responsive testing (resize) ─────────────► references/screenshots.md
│   ├── Dark mode testing ───────────────────────► references/screenshots.md
│   └── Before/after comparison ─────────────────► references/screenshots.md
│
├── Manage tabs or sessions
│   ├── tab-new / tab-list / tab-select ─────────► references/tabs.md
│   ├── Named sessions ─────────────────────────► references/tabs.md
│   ├── Popup / OAuth window handling ───────────► references/tabs.md
│   └── Multi-agent coordination ────────────────► references/tabs.md
│
├── Debug or diagnose issues
│   ├── Console / network artifact logs ─────────► references/debugging.md
│   ├── Tracing and video recording ─────────────► references/debugging.md
│   ├── Troubleshooting common errors ───────────► references/debugging.md
│   └── eval for browser truth checks ───────────► references/debugging.md
│
├── Select elements or extract data
│   ├── Ref system and snapshot anatomy ─────────► references/selectors.md
│   ├── eval for data extraction ────────────────► references/selectors.md
│   ├── CSS selector fallback ───────────────────► references/selectors.md
│   ├── Iframe and shadow DOM access ────────────► references/selectors.md
│   └── run-code for complex selection ──────────► references/selectors.md
│
└── Common automation workflows
    ├── Login / auth flows ──────────────────────► references/patterns.md
    ├── Search / filter / sort flows ────────────► references/patterns.md
    ├── Data extraction and scraping ────────────► references/patterns.md
    ├── Download handling ───────────────────────► references/patterns.md
    ├── Cookie and storage management ───────────► references/patterns.md
    └── E2E verification workflow ───────────────► references/patterns.md
```

## Quick start

```bash
# Install (once)
which playwright-cli || npm install -g @anthropic-ai/playwright-cli@latest
playwright-cli install --browser=chrome
playwright-cli config --browser=chrome --isolated
```

### The core loop: observe → act → observe

```bash
open https://example.com
snapshot
screenshot --filename=step-1.png
# [decide what to do based on snapshot refs]
click <ref>
snapshot
screenshot --filename=step-2.png
# [repeat]
```

**Rule:** after any meaningful UI change, run `snapshot` before reusing refs.

### Essential commands

```bash
# Navigation
open <url>
go-back | go-forward | reload

# Observation
snapshot                                    # get page tree + refs
screenshot --filename=view.png              # viewport capture
screenshot --full-page --filename=full.png   # full page
screenshot <ref> --filename=element.png     # single element

# Interaction
click <ref>
fill <ref> "text"
fill <ref> "text" --submit
select <ref> "value"
check <ref> | uncheck <ref>
hover <ref> | dblclick <ref>
press Enter | type "text"

# Truth checks
eval "() => window.location.href"
eval "(el) => el.value" <ref>

# Tabs
tab-new | tab-list | tab-select <index> | tab-close <index>

# Diagnostics
console error | network

# Escape hatch (Playwright API)
run-code 'async (page) => { ... }'
```

### Verify a form fill

```bash
snapshot
fill <email-ref> "user@example.com"
eval "(el) => el.value" <email-ref>
click <submit-ref>
snapshot
eval "() => window.location.href"
screenshot --filename=after-submit.png
```

## How refs work

Refs like `e5` are ephemeral element identifiers from `snapshot`. They are the
primary way to target elements:

```bash
snapshot    # produces refs: e0, e1, e2, ...
click e0   # click the first interactive element
fill e1 "hello"
```

Refs die when page state changes (navigation, re-render, tab switch, `run-code`).
If in doubt, re-snapshot. Refs are cheap.

## Full command reference

### Navigation

```bash
open <url>                    # navigate to URL
go-back                       # browser back
go-forward                    # browser forward
reload                        # reload page
```

### Interaction

```bash
click <ref>                   # click element
fill <ref> "text"             # set field value
fill <ref> "text" --submit    # fill and submit
type "text"                   # type into focused element
select <ref> "value"          # select dropdown option
check <ref>                   # check checkbox or radio
uncheck <ref>                 # uncheck checkbox
hover <ref>                   # hover element
dblclick <ref>                # double-click
drag <source> <target>        # drag and drop
upload /path/to/file          # upload (after file chooser)
```

### Keyboard and mouse

```bash
press Enter                   # press key
keydown Shift | keyup Shift   # hold/release key
mousemove <x> <y>             # move pointer
mousedown | mouseup           # mouse button control
mousewheel <dx> <dy>          # scroll
resize <w> <h>                # resize viewport
```

### Observation and capture

```bash
snapshot                      # get accessibility tree + refs
snapshot --filename=state.md  # save snapshot to file
screenshot --filename=v.png   # viewport screenshot
screenshot --full-page --filename=f.png
screenshot <ref> --filename=e.png
pdf --filename=page.pdf       # save as PDF
```

### JavaScript

```bash
eval "() => document.title"           # page context
eval "(el) => el.value" <ref>         # element context
run-code 'async (page) => { ... }'    # Playwright API
```

### Tabs and sessions

```bash
tab-new                               # open new tab
tab-list                              # list tabs
tab-select <index>                    # switch tab
tab-close [index]                     # close tab
playwright-cli --session=name <cmd>   # named session
playwright-cli session-list           # list sessions
playwright-cli session-stop [name]    # stop session
playwright-cli session-stop-all       # stop all
playwright-cli session-delete [name]  # delete data
```

### Diagnostics

```bash
console [level]               # get console logs (returns file)
console --clear               # clear console
network                       # get network logs (returns file)
network --static              # include static assets
network --clear               # clear network logs
tracing-start | tracing-stop  # record trace
video-start | video-stop      # record video
```

### Storage and cookies

```bash
state-save <file.json>        # save cookies/storage
state-load <file.json>        # load saved state
cookie-list | cookie-get <n>  # inspect cookies
cookie-set <n> <v>            # set cookie
cookie-delete <n>             # delete cookie
cookie-clear                  # clear all cookies
localstorage-list | localstorage-get <k>
localstorage-set <k> <v> | localstorage-delete <k>
sessionstorage-list | sessionstorage-get <k>
sessionstorage-set <k> <v> | sessionstorage-delete <k>
```

### Dialogs and network

```bash
dialog-accept [text]          # accept alert/confirm/prompt
dialog-dismiss                # dismiss dialog
route <pattern> --body='{}'   # mock network request
route-list                    # list active routes
unroute [pattern]             # remove route
```

## CLI-first principle

Prefer direct CLI commands. Use `run-code` only when the CLI cannot express
the step cleanly (waits, popups, downloads, iframe access, media emulation).

After `run-code`, re-enter the normal loop:

```bash
run-code 'async (page) => {
  await page.waitForSelector(".loaded")
  return "done"
}'
snapshot
screenshot --filename=after-run-code.png
```

## Verified gotchas

1. **`tab-new <url>` is unreliable** — always use `tab-new` then `open <url>`.
2. **Quote URLs in zsh** — `open "https://example.com/s?q=test&page=2"`.
3. **Snapshots ≠ live form state** — verify values with `eval "(el) => el.value"`.
4. **`upload` is modal-driven** — click upload trigger first, then `upload /path`.
5. **`check` works for radios** — prefer over `click` for idempotent selection.
6. **Console/network return files** — artifact may be empty, always inspect.
7. **`run-code` invalidates refs** — re-snapshot immediately after.
8. **Artifact paths are runtime outputs** — use returned path, don't guess.
9. **`select` needs option value** — not visible label, inspect with `eval` first.
10. **Page header can be stale** — use `eval "() => window.location.href"` for truth.

## Sub-agent rules (shared-session work)

If you are a tab tenant inside a shared browser session:

```text
tab-new → open <url> → [work] → tab-close <index>
```

- Never `close` the browser — only `tab-close` your tab.
- Re-run `snapshot` after every `tab-select`.
- Re-check tab order with `tab-list` before closing.
- Use explicit `tab-close <index>`, not bare `tab-close`.
- Keep uploads inside allowed roots.

## Common pitfalls

| Pitfall | Fix |
|---------|-----|
| Refs not found | Re-run `snapshot` — refs die on page changes |
| `tab-new <url>` opens blank page | Use `tab-new` then `open <url>` separately |
| URL shows wrong value after tab switch | Use `eval "() => window.location.href"` instead of header |
| `fill` value not visible | Verify with `eval "(el) => el.value" <ref>` |
| `select` fails silently | Use option `value`, not visible label — inspect options first |
| `upload` fails | Must click upload trigger first to activate file chooser |
| Upload path denied | File must be inside allowed roots |
| zsh eats URL characters | Quote URLs: `open "https://example.com/s?q=test"` |
| Snapshots don't show live values | Use `eval` for input values, checked state, URLs |
| `console`/`network` seem empty | They return artifact files — open and inspect the file |
| `run-code` breaks refs | Always `snapshot` after `run-code` |
| Stale session/profile flags | Use `--session=name`, not `-s=name` or `--persistent` |
| Public site console noise | Telemetry/anti-bot logs are not your app's bugs |
| `close` kills shared session | Use `tab-close` in multi-agent work |
| Screenshot timing | Wait for UI to settle before screenshot |

## Minimal reading sets

### "I need to navigate and verify a page"

- `references/navigation.md`
- `references/selectors.md` (eval section)

### "I need to fill and submit a form"

- `references/forms.md`
- `references/selectors.md` (eval section)

### "I need to test responsive layouts or visual changes"

- `references/screenshots.md`
- `references/navigation.md` (resize section)

### "I need to work with multiple tabs or agents"

- `references/tabs.md`

### "I need to debug a page problem"

- `references/debugging.md`
- `references/selectors.md` (eval section)

### "I need to extract data from a page"

- `references/selectors.md`
- `references/patterns.md` (data extraction section)

### "I need to automate a login or complete workflow"

- `references/patterns.md`
- `references/forms.md`
- `references/navigation.md`

### "I need to handle popups, downloads, or iframes"

- `references/selectors.md` (iframe / run-code sections)
- `references/tabs.md` (popup section)
- `references/patterns.md` (download section)

## Cleanup

When all browser work is done:

```bash
playwright-cli session-stop-all
```

## Reference files

- **[Navigation](references/navigation.md)** — open, history, page loading, URL handling, waits
- **[Forms](references/forms.md)** — fill, type, select, check, upload, date pickers, verification
- **[Screenshots](references/screenshots.md)** — viewport, full-page, element, responsive, dark mode, comparison
- **[Tabs](references/tabs.md)** — tab management, sessions, popups, dialogs, multi-agent coordination
- **[Debugging](references/debugging.md)** — console, network, tracing, troubleshooting, eval truth checks
- **[Selectors](references/selectors.md)** — ref system, snapshots, eval extraction, CSS fallback, iframes
- **[Patterns](references/patterns.md)** — login, search, data extraction, downloads, cookies, E2E verification
