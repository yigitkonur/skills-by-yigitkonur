# Command Reference

Complete syntax documentation for every `playwright-cli` command. All commands are invoked as `playwright-cli <command> [args] [options]`.

Refs (e.g. `e5`, `e12`) are ephemeral element identifiers returned by `snapshot`. They are invalidated by any page-changing action (`open`, `click` that navigates, `reload`, `go-back`, `go-forward`, `tab-select`). Always run `snapshot` after any such action before using refs.

---

## Table of Contents

- [Navigation Commands](#navigation-commands) -- open, go-back, go-forward, reload
- [Interaction Commands](#interaction-commands) -- click, fill, type, select, check, uncheck, hover, dblclick, drag, upload, press
- [Observation Commands](#observation-commands) -- snapshot, screenshot, pdf
- [JavaScript Evaluation](#javascript-evaluation) -- eval, run-code
- [Tab Management](#tab-management) -- tab-new, tab-list, tab-select, tab-close
- [Session Management](#session-management) -- session-stop, session-stop-all, session-list, session-delete, session-restart, close, config
- [DevTools / Debugging](#devtools--debugging) -- console, network
- [Keyboard / Mouse (low-level)](#keyboard--mouse-low-level) -- keydown, keyup, mousedown, mouseup, mousemove, mousewheel
- [Dialog Handling](#dialog-handling) -- dialog-accept, dialog-dismiss
- [Recording](#recording) -- video-start, video-stop, tracing-start, tracing-stop
- [Viewport](#viewport) -- resize

---

## Navigation Commands

### open

```
open <url>
```

| Argument | Required | Description |
|----------|----------|-------------|
| `url` | Yes | Full URL to navigate to (include protocol) |

Navigates the current tab to the given URL. Waits for the page to reach a loaded state. Returns a snapshot of the new page.

**All existing refs are invalidated.** You must use refs from the returned snapshot or call `snapshot` again.

---

### go-back

```
go-back
```

No arguments. Navigates back one step in the browser history (equivalent to the browser back button). Returns a snapshot.

**Invalidates all refs.**

---

### go-forward

```
go-forward
```

No arguments. Navigates forward one step in the browser history. Returns a snapshot.

**Invalidates all refs.**

---

### reload

```
reload
```

No arguments. Reloads the current page. Returns a snapshot.

**Invalidates all refs.**

---

## Interaction Commands

### click

```
click <ref> [button] [--modifiers <keys>]
```

| Argument / Option | Required | Description |
|-------------------|----------|-------------|
| `ref` | Yes | Element ref from snapshot (e.g. `e5`) |
| `button` | No | `left` (default), `right`, or `middle` |
| `--modifiers` | No | Comma-separated modifier keys: `Shift`, `Control`, `Meta`, `Alt` |

Clicks the specified element. Returns a snapshot after the click.

**Gotcha:** If the click triggers navigation, all refs are invalidated. Always snapshot after click.

---

### fill

```
fill <ref> "text" [--submit]
```

| Argument / Option | Required | Description |
|-------------------|----------|-------------|
| `ref` | Yes | Element ref of an input, textarea, or contenteditable |
| `text` | Yes | Text to fill (replaces all existing content) |
| `--submit` | No | If present, presses Enter after filling |

Clears the field completely, then types the given text. This **replaces** existing content -- it does not append.

**Gotcha:** Snapshots show the HTML tree, not live input values. To verify fill worked, use `eval "(el) => el.value" <ref>`.

---

### type

```
type "text"
```

| Argument | Required | Description |
|----------|----------|-------------|
| `text` | Yes | Text to type |

Types text into whatever element currently has focus. Does **not** accept a ref -- it always targets the focused element. **Appends** to existing content (does not clear first).

**Gotcha:** `fill` and `type` are not interchangeable. Use `fill` for 95% of cases. Use `type` only when you need append behavior or are testing keyboard input specifically.

---

### select

```
select <ref> "value"
```

| Argument | Required | Description |
|----------|----------|-------------|
| `ref` | Yes | Element ref of a `<select>` element |
| `value` | Yes | The `value` attribute of the `<option>` to select |

Selects a dropdown option by its value. Returns a snapshot.

**Gotcha:** The `value` is the option's `value` attribute, not its visible text. Use `eval` or `snapshot` to inspect available option values if unsure.

---

### check

```
check <ref>
```

| Argument | Required | Description |
|----------|----------|-------------|
| `ref` | Yes | Element ref of a checkbox or radio button |

Checks the element. No-op if already checked. Returns a snapshot.

---

### uncheck

```
uncheck <ref>
```

| Argument | Required | Description |
|----------|----------|-------------|
| `ref` | Yes | Element ref of a checkbox |

Unchecks the element. No-op if already unchecked. Returns a snapshot.

---

### hover

```
hover <ref>
```

| Argument | Required | Description |
|----------|----------|-------------|
| `ref` | Yes | Element ref to hover over |

Moves the mouse over the element, triggering hover states, tooltips, and dropdown menus. Returns a snapshot.

**Gotcha:** Hover can change the DOM (e.g., revealing menus), which may invalidate refs. Snapshot after hover.

---

### dblclick

```
dblclick <ref>
```

| Argument | Required | Description |
|----------|----------|-------------|
| `ref` | Yes | Element ref to double-click |

Double-clicks the element. Returns a snapshot.

---

### drag

```
drag <source-ref> <target-ref>
```

| Argument | Required | Description |
|----------|----------|-------------|
| `source-ref` | Yes | Element ref to drag from |
| `target-ref` | Yes | Element ref to drop onto |

Drags the source element and drops it on the target. Returns a snapshot.

---

### upload

```
upload <ref> <file-path> [<file-path> ...]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `ref` | Yes | Element ref of a file input (`<input type="file">`) |
| `file-path` | Yes | Absolute path(s) to file(s) to upload |

Sets the file(s) on a file input element. Multiple paths can be provided for multi-file inputs.

---

### press

```
press <key>
```

| Argument | Required | Description |
|----------|----------|-------------|
| `key` | Yes | Key or key combination to press |

Presses a single key or key combination. Supported key names include: `Enter`, `Tab`, `Escape`, `Backspace`, `Delete`, `ArrowUp`, `ArrowDown`, `ArrowLeft`, `ArrowRight`, `Home`, `End`, `PageUp`, `PageDown`, `Space`, `F1`-`F12`, and any single character.

Key combinations use `+` as separator: `Control+a`, `Shift+Enter`, `Meta+c`, `Alt+Tab`, `Control+Shift+k`.

**Gotcha:** Key names are case-sensitive. `Enter` works, `enter` may not.

---

## Observation Commands

### snapshot

```
snapshot [--filename=<path>]
```

| Option | Required | Description |
|--------|----------|-------------|
| `--filename` | No | Save snapshot to a YAML file (e.g. `--filename=snap.yaml`) |

Returns the accessibility tree of the current page as YAML. Each interactive element is labeled with a ref (e.g. `e5`). These refs are used by all interaction commands.

Without `--filename`, the snapshot is printed to stdout. With `--filename`, it is saved to disk.

**Gotcha:** Snapshot reflects the DOM tree, not necessarily the current visual state of form inputs. Use `eval "(el) => el.value" <ref>` to read live input values.

---

### screenshot

```
screenshot [ref] [--full-page] [--filename=<path>]
```

| Argument / Option | Required | Description |
|-------------------|----------|-------------|
| `ref` | No | Element ref to screenshot (screenshots only that element) |
| `--full-page` | No | Capture the entire scrollable page, not just the viewport |
| `--filename` | No | Save to specified path (e.g. `--filename=step-1.png`) |

Takes a screenshot. Without `ref`, captures the viewport (or full page with `--full-page`). With `ref`, captures only that element.

Returns the file path of the saved screenshot.

---

### pdf

```
pdf [--filename=<path>]
```

| Option | Required | Description |
|--------|----------|-------------|
| `--filename` | No | Output path (e.g. `--filename=page.pdf`) |

Saves the current page as a PDF. Chromium only.

---

## JavaScript Evaluation

### eval

```
eval "<function>" [ref]
```

Two forms:

**Page context (no ref):**

```
eval "() => <expression>"
```

The function runs in the page's global scope. Has access to `window`, `document`, and all page globals.

**Element context (with ref):**

```
eval "(el) => <expression>" <ref>
```

The function receives the DOM element corresponding to `ref` as its first argument.

| Argument | Required | Description |
|----------|----------|-------------|
| `function` | Yes | JavaScript arrow function as a string |
| `ref` | No | Element ref -- if provided, the element is passed as the first argument |

**Return value:** Must be JSON-serializable. Do not return DOM nodes -- extract the data you need (text, attributes, dimensions) and return that.

**Gotcha:** The function string uses double quotes on the outside. Use single quotes for strings inside, or escaped doubles.

Examples:

```bash
eval "() => document.title"
eval "() => window.location.href"
eval "(el) => el.value" e5
eval "(el) => getComputedStyle(el).color" e12
eval "() => [...document.querySelectorAll('a')].map(a => a.href)"
```

---

### run-code

```
run-code '<async-function>'
```

| Argument | Required | Description |
|----------|----------|-------------|
| `async-function` | Yes | Async function receiving a Playwright `page` object |

Executes arbitrary Playwright API code against the current page. The function receives the Playwright `Page` instance and has full access to the Playwright API.

**Quoting rule:** Use single quotes for the outer wrapper, double quotes inside the function body.

```bash
run-code 'async (page) => { await page.waitForSelector(".loaded"); return "done"; }'
run-code 'async (page) => { await page.emulateMedia({ colorScheme: "dark" }); }'
run-code 'async (page) => { return await page.evaluate(() => performance.now()); }'
```

**Gotcha:** Incorrect quoting is the most common cause of `run-code` failures. Always: single outer, double inner. Never the reverse.

---

## Tab Management

### tab-new

```
tab-new
```

No arguments. Opens a new tab navigated to `about:blank`.

**Gotcha:** `tab-new` does NOT accept a URL argument. It always opens `about:blank`. To open a URL in a new tab, use two commands:

```bash
tab-new
open https://example.com
```

---

### tab-list

```
tab-list
```

No arguments. Lists all open tabs with their index and URL.

---

### tab-select

```
tab-select <index>
```

| Argument | Required | Description |
|----------|----------|-------------|
| `index` | Yes | Zero-based tab index |

Switches the active tab. Returns a snapshot of the selected tab.

**Invalidates all refs** (you are now on a different page context).

---

### tab-close

```
tab-close <index>
```

| Argument | Required | Description |
|----------|----------|-------------|
| `index` | Yes | Zero-based tab index to close |

Closes the specified tab.

**Gotcha:** After closing a tab, all remaining tab indexes shift. Run `tab-list` immediately after to get correct indexes before selecting another tab.

---

## Session Management

### session-stop

```
session-stop
```

No arguments. Stops the current browser session (closes the browser).

---

### session-stop-all

```
session-stop-all
```

No arguments. Stops all running browser sessions. Use for cleanup at the end of all browser work.

---

### session-list

```
session-list
```

No arguments. Lists all active sessions.

---

### session-delete

```
session-delete
```

No arguments. Deletes the current session data.

---

### session-restart

```
session-restart
```

No arguments. Stops and restarts the current session. Useful when the browser gets into a bad state.

---

### close

```
close
```

No arguments. Closes the entire browser instance and terminates the session.

**Gotcha:** This kills the browser for ALL agents sharing the session. Sub-agents should never use `close` -- use `tab-close <index>` to close only your tab.

---

### config

```
config [--browser=<browser>]
```

| Option | Required | Description |
|--------|----------|-------------|
| `--browser` | No | Browser engine: `chromium` (default), `firefox`, `webkit`, `msedge` |

Sets configuration options for the session. Currently the primary option is browser selection. Run before opening any pages.

```bash
playwright-cli config --browser=chromium
playwright-cli config --browser=firefox
playwright-cli config --browser=webkit
playwright-cli config --browser=msedge
```

---

## DevTools / Debugging

### console

```
console [type] [--clear]
```

| Argument / Option | Required | Description |
|-------------------|----------|-------------|
| `type` | No | Filter by log type: `log`, `error`, `warning`, `info`, `debug` |
| `--clear` | No | Clear the console log buffer |

Without `--clear`, returns a **file path** to a log file containing the captured console messages. You must read that file to see the actual content.

```bash
console              # all console messages -> file path
console error        # only errors -> file path
console --clear      # clear the buffer, no output
```

**Gotcha:** This command returns a FILE PATH, not the log content itself. You must read the file at the returned path to see the actual console output.

---

### network

```
network [--static] [--clear]
```

| Option | Required | Description |
|--------|----------|-------------|
| `--static` | No | Include static assets (images, CSS, fonts) which are excluded by default |
| `--clear` | No | Clear the network log buffer |

Without `--clear`, returns a **file path** to a log file containing captured network requests/responses with status codes.

```bash
network              # API/document requests -> file path
network --static     # include static assets -> file path
network --clear      # clear the buffer
```

**Gotcha:** Like `console`, this returns a FILE PATH, not the network data. Read the file to see requests, status codes, and responses.

---

## Keyboard / Mouse (low-level)

These are low-level input primitives. For most tasks, prefer `click`, `fill`, `type`, and `press` instead.

### keydown

```
keydown <key>
```

| Argument | Required | Description |
|----------|----------|-------------|
| `key` | Yes | Key name to press down (e.g. `Shift`, `Control`, `Alt`, `Meta`) |

Dispatches a keydown event. The key remains "held" until `keyup` is called.

---

### keyup

```
keyup <key>
```

| Argument | Required | Description |
|----------|----------|-------------|
| `key` | Yes | Key name to release |

Dispatches a keyup event, releasing a previously held key.

---

### mousedown

```
mousedown <x> <y> [button]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `x` | Yes | X coordinate (pixels from left) |
| `y` | Yes | Y coordinate (pixels from top) |
| `button` | No | `left` (default), `right`, or `middle` |

Dispatches a mousedown event at the given coordinates.

---

### mouseup

```
mouseup <x> <y> [button]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `x` | Yes | X coordinate |
| `y` | Yes | Y coordinate |
| `button` | No | `left` (default), `right`, or `middle` |

Dispatches a mouseup event at the given coordinates.

---

### mousemove

```
mousemove <x> <y>
```

| Argument | Required | Description |
|----------|----------|-------------|
| `x` | Yes | X coordinate to move to |
| `y` | Yes | Y coordinate to move to |

Moves the mouse cursor to the given coordinates without clicking.

---

### mousewheel

```
mousewheel <deltaX> <deltaY>
```

| Argument | Required | Description |
|----------|----------|-------------|
| `deltaX` | Yes | Horizontal scroll amount in pixels (positive = scroll right) |
| `deltaY` | Yes | Vertical scroll amount in pixels (positive = scroll down) |

Dispatches a mouse wheel event.

```bash
mousewheel 0 500      # scroll down 500px
mousewheel 0 -300     # scroll up 300px
mousewheel 200 0      # scroll right 200px
```

**Gotcha:** Positive `deltaY` scrolls **down**, negative scrolls **up**. This matches the browser's native wheel event convention.

---

## Dialog Handling

### dialog-accept

```
dialog-accept [text]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `text` | No | Text to enter into a `prompt()` dialog before accepting |

Accepts the currently open dialog (alert, confirm, or prompt). If `text` is provided and the dialog is a prompt, the text is entered before accepting.

```bash
dialog-accept                  # accept alert or confirm
dialog-accept "my input"       # enter text + accept prompt
```

**Gotcha:** A pending dialog blocks all other commands. If you get "modal state" errors, a dialog needs to be handled first.

---

### dialog-dismiss

```
dialog-dismiss
```

No arguments. Dismisses (cancels) the currently open dialog.

---

## Recording

### video-start

```
video-start
```

No arguments. Starts recording the browser session as a video.

---

### video-stop

```
video-stop
```

No arguments. Stops recording and saves the video file. Returns the path to the saved video.

---

### tracing-start

```
tracing-start
```

No arguments. Starts collecting a Playwright trace (includes screenshots, DOM snapshots, and network activity at each step).

---

### tracing-stop

```
tracing-stop
```

No arguments. Stops tracing and saves the trace file. The trace can be viewed with `npx playwright show-trace <file>`.

---

## Viewport

### resize

```
resize <width> <height>
```

| Argument | Required | Description |
|----------|----------|-------------|
| `width` | Yes | Viewport width in pixels |
| `height` | Yes | Viewport height in pixels |

Resizes the browser viewport. Useful for responsive testing.

```bash
resize 1280 720      # desktop
resize 768 1024      # tablet portrait
resize 375 812       # iPhone X
resize 1920 1080     # full HD
```

---

## Quick Comparison: fill vs type

| | `fill` | `type` |
|---|--------|--------|
| **Targets** | Specific element by ref | Currently focused element (no ref) |
| **Behavior** | Clears field, then sets value | Appends to existing content |
| **Syntax** | `fill <ref> "text"` | `type "text"` |
| **Use when** | Setting form fields (95% of cases) | Testing raw keyboard input |

## Quick Comparison: eval vs run-code

| | `eval` | `run-code` |
|---|--------|------------|
| **Context** | Page JS context (`window`, `document`) | Playwright `Page` API |
| **Quoting** | Double quotes outer | Single quotes outer, double inner |
| **Async** | Synchronous expressions only | Full async/await support |
| **Use when** | Reading DOM state, extracting data | Waiting for conditions, using Playwright API |
