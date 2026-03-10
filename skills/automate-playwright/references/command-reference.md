# Command Reference

Validated against the installed `playwright-cli` CLI used during this audit. This file intentionally distinguishes between:

- what the built-in help documents,
- what live command behavior confirmed,
- and where the runtime is inconsistent enough that you should prefer a safer workflow.

All commands are invoked as `playwright-cli <command> [args] [options]`.

Refs like `e5` are ephemeral element identifiers returned by `snapshot`. Treat them as disposable and recapture a fresh snapshot after meaningful page changes.
Use `eval` for browser truth when URL, values, or selected state matter more than the surrounding command header.

---

## Table of Contents

- [Navigation](#navigation)
- [Interaction](#interaction)
- [Observation](#observation)
- [JavaScript and Playwright API](#javascript-and-playwright-api)
- [Tabs](#tabs)
- [Sessions and configuration](#sessions-and-configuration)
- [DevTools and recording](#devtools-and-recording)
- [Keyboard and mouse](#keyboard-and-mouse)
- [Behavior notes](#behavior-notes)

---

## Navigation

### open

```text
open [url]
```

Documented help: opens the provided URL.

Observed behavior: navigates successfully and usually prints page metadata plus a snapshot.

### go-back

```text
go-back
```

Navigates browser history backward.

### go-forward

```text
go-forward
```

Navigates browser history forward.

### reload

```text
reload
```

Reloads the current page.

**Practical rule:** after any navigation command, run `snapshot` before using refs again.

---

## Interaction

### click

```text
click <ref> [button] [--modifiers <keys>]
```

Arguments:
- `ref`: exact target element reference from the page snapshot
- `button`: optional mouse button, defaults to left

Observed behavior: may print page metadata and a snapshot when the page state changes.

### fill

```text
fill <ref> <text> [--submit]
```

Arguments:
- `ref`: exact target element reference from the page snapshot
- `text`: text to insert

Observed behavior: fills correctly, but does **not** reliably print a fresh snapshot by itself in the installed CLI.

Use:

```bash
fill <ref> "value"
eval "(el) => el.value" <ref>
```

### type

```text
type <text> [--submit]
```

Targets the currently focused editable element.

Use this only when focus-driven typing is intentional. For most form work, prefer `fill`.

### select

```text
select <ref> <value>
```

Observed behavior: selected the option successfully and printed a fresh snapshot in testing.

The value is the option's `value`, not its visible label.
Inspect first, then select by the concrete value you observed.

Example:

```bash
eval "(el) => [...el.options].map(o => ({ value: o.value, text: o.textContent.trim() }))" <ref>
select <ref> "review-rank"
```

### check

```text
check <ref>
```

Documented help: checks a checkbox or radio button.

Observed behavior: worked for both checkbox and radio inputs.

### uncheck

```text
uncheck <ref>
```

Documented help: unchecks a checkbox or radio button.

Use carefully on radios: browser semantics may make radio unchecking less meaningful than checkbox unchecking, so always verify with `eval`.

### hover

```text
hover <ref>
```

Hover the element.

### dblclick

```text
dblclick <ref> [button] [--modifiers <keys>]
```

Double-click the element.

### drag

```text
drag <startRef> <endRef>
```

Perform drag and drop.

### upload

```text
upload <file> [<file> ...]
```

This is one of the most important corrections in the repo.

**Documented help:** `upload <file>` uploads one or more files.

**Observed runtime behavior:**
- `upload` only works when a file chooser modal state is active;
- it is **not** `upload <ref> ...` on the installed CLI;
- files outside allowed roots are rejected.

Safe workflow:

```bash
click <upload-trigger-ref>
upload /absolute/path/to/file
eval "() => [...document.querySelector('input[type=file]').files].map(f => f.name)"
```

If no file chooser modal is active, `upload` fails.
If the file path is outside an allowed root, `upload` fails.

---

## Observation

### snapshot

```text
snapshot [--filename <path>]
```

Use this to obtain the current accessibility-tree view and fresh refs.

Observed behavior:
- plain `snapshot` prints the current tree;
- `snapshot --filename=...` writes a markdown-style outline file, not YAML despite older repo wording.

### screenshot

```text
screenshot [ref] [--full-page] [--filename <path>]
```

Without `ref`, captures the viewport unless `--full-page` is provided.
With `ref`, captures the target element.

### pdf

```text
pdf [--filename <path>]
```

Save the current page as PDF.

---

## JavaScript and Playwright API

### eval

```text
eval <func> [ref]
```

Two main forms:

```bash
eval "() => document.title"
eval "(el) => el.value" <ref>
```

Rules:
- return primitives or plain JSON-serializable objects;
- do not return DOM nodes;
- use this for truth checks like URL, value, checked state, style, or option values.

### run-code

```text
run-code <code>
```

Help describes the argument as a JavaScript function that receives `page`.

Reliable pattern:

```bash
run-code 'async (page) => {
  await page.waitForSelector(".loaded")
  return "done"
}'
```

Use single quotes outside and double quotes inside.

After `run-code`, assume refs may be stale and run `snapshot`.

---

## Tabs

### tab-list

```text
tab-list
```

Lists tabs with indexes.

### tab-new

```text
tab-new [url]
```

**Important mismatch:** help advertises an optional URL argument, but live testing still opened `about:blank` when a URL was supplied inline.

Safe pattern:

```bash
tab-new
open https://example.com
snapshot
```

### tab-select

```text
tab-select <index>
```

Select the tab, then explicitly refresh your working context:

```bash
tab-select 0
snapshot
eval "() => window.location.href"
```

### tab-close

```text
tab-close [index]
```

Help allows the index to be omitted for the current tab.

In shared or multi-step work, prefer explicit indexes and then re-run `tab-list`.

---

## Sessions and configuration

### install

```text
install [--browser <browser>]
```

Observed help values: `chrome`, `firefox`, `webkit`, `msedge`.

### config

```text
config [--browser <browser>] [--config <path>] [--isolated] [--headed]
```

Observed supported browser values:
- `chrome`
- `firefox`
- `webkit`
- `msedge`

The repo's older `chromium` examples were stale for the installed CLI.

### session-list

```text
session-list
```

List active sessions.

### session-stop

```text
session-stop [name]
```

Stop current or named session.

### session-restart

```text
session-restart [name]
```

Restart current or named session.

### session-stop-all

```text
session-stop-all
```

Stop all sessions.

### session-delete

```text
session-delete [name]
```

Delete session data for current or named session.

### Named session invocation

Use:

```bash
playwright-cli --session=my-session open https://example.com
```

Do **not** copy old `-s=my-session` examples from outdated docs.

---

## DevTools and recording

### console

```text
console [min-level] [--clear]
```

Returns a path to a console artifact file.
The file may contain entries or may be empty, so inspect the returned file before drawing conclusions.

Typical levels seen in help usage: `info`, `warning`, `error` semantics.

### network

```text
network [--static] [--clear]
```

Returns a path to a network artifact file.
The file may contain entries or may be empty.
Use `--static` when you also care about successful asset requests.

### tracing-start / tracing-stop

```text
tracing-start
tracing-stop
```

Trace recording lifecycle.

### video-start / video-stop

```text
video-start
video-stop
```

Video recording lifecycle.

---

## Keyboard and mouse

### press

```text
press <key>
```

Press a key or character.

### keydown / keyup

```text
keydown <key>
keyup <key>
```

Low-level key state control.

### mousemove

```text
mousemove <x> <y>
```

Move pointer to coordinates.

### mousedown / mouseup

```text
mousedown [button]
mouseup [button]
```

**Correction:** older repo docs described coordinate-based forms for these. The installed help only accepts an optional button argument.

### mousewheel

```text
mousewheel <dx> <dy>
```

Scroll mouse wheel.

**Correction:** installed help labels `<dx>` and `<dy>` in a confusing way. Treat the command as a wheel delta pair and test the direction you care about when precision matters.

---

## Behavior notes

### Prefer explicit snapshots over optimistic assumptions
Not every command reliably prints a fresh snapshot. The safest documentation pattern is:

```bash
[action]
snapshot
```

### Prefer `eval` for truth checks
Use `eval` to verify:
- current URL
- input values
- checked state
- selected option values
- uploaded file names

### Prefer artifact paths returned by the CLI
Do not assume where `.playwright-cli/...` files will land based only on your repo layout. Use the returned path, then inspect that file.
Do not overclaim from artifact existence alone: the file may be empty or noisy.
