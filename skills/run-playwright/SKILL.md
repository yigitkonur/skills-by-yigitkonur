---
name: run-playwright
description: Use skill if you are controlling a live browser with @anthropic-ai/playwright-cli for navigation, forms, screenshots, tab workflows, or interactive debugging from the terminal.
---

# Playwright CLI

Use `@anthropic-ai/playwright-cli` to drive a live browser from the terminal. Keep this file focused on trigger logic, workflow, guardrails, and reference routing. Use `references/` for detailed commands, edge cases, and larger patterns.

> **Invocation model — read this first.** `playwright-cli` is a command-per-invocation CLI backed by persistent session state. Run each action from the shell as its own command, for example `playwright-cli tab-list`, `playwright-cli open https://example.com`, `playwright-cli snapshot`. There is no required `>` prompt workflow in the shipped CLI.

## Trigger boundary

Use this skill when the task requires a real browser session and interactive CLI control:
- open pages, navigate, and verify what actually rendered
- fill forms, upload files, submit flows, and prove the result
- manage tabs, popups, or session state during a live run
- collect screenshots, console logs, network logs, or traces as evidence
- use short `run-code` snippets only when the CLI lacks a direct command

Do not use this skill when:
- the job is writing or reviewing Playwright test code instead of driving the CLI
- plain HTTP fetching or static scraping is enough
- the site needs Browserbase-style hosted browsing, anti-bot bypass, or remote browser routing; prefer `run-agent-browser`

## Non-negotiable rules

1. **Prefer the current browser context when it already has the right state.** Do not reset sessions or reinstall tools just because a browser exists.
2. **Prefer a new tab over a new window.** Use a popup or new window only when the site forces one, such as OAuth or `target=_blank` flows.
3. **Keep a running tab map** in your notes: `index -> purpose -> expected URL/state`. Refresh it after every `tab-new`, `tab-close`, `tab-select`, or popup event.
4. **Verify the active tab before every action.** Use `tab-list`, `tab-select` if needed, `eval "() => window.location.href"`, then `snapshot`.
5. **Follow observe -> act -> verify.** Never chain blind actions across unknown state.
6. **Treat refs as disposable.** Re-snapshot after navigation, SPA rerender, submission, tab switch, popup handling, or `run-code`.
7. **Use CLI commands first.** Reach for `run-code` only for waits, popups, downloads, iframes/shadow DOM, or missing primitives; then immediately re-enter the snapshot loop.
8. **Treat screenshots as evidence, not default observation.** Use `snapshot` for structure, `eval` for truth, screenshots for visual proof.
9. **Clean up only what you created.** Close transient tabs and temporary sessions, but do not destroy shared or pre-existing contexts.

## Recommended workflow

### 1) Attach or bootstrap

Only bootstrap when the CLI or browser support is missing:

```bash
which playwright-cli || npm install -g @anthropic-ai/playwright-cli@latest
playwright-cli install --browser=chrome   # always run — ensures browser binary exists
```

> **Steering experience:** Always run `playwright-cli install --browser=chrome` even if the CLI is already installed. It is a no-op when the binary exists, but skipping it causes cryptic "browser not found" errors when the binary is missing. This is a one-second check that prevents a five-minute debug session.

When you need an isolated session (parallel work, risky experiments), add to bootstrap:

```bash
playwright-cli config --isolated
playwright-cli session-list
```

- If an existing session or tab already contains the needed login or state, inspect it first instead of resetting everything.
- Start a named session or isolated browser only when you need clean-room state, parallel isolation, or risky experimentation; use `references/tabs.md` for the exact bootstrap patterns.
- For isolated scratch work, stop the session you created at cleanup time: use `session-stop` for the current unnamed isolated session or `session-stop <name>` for a named one.
- Do not begin with `session-stop-all` unless you intentionally want to discard every active browser.
- Session state persists behind the CLI. Inspect it with `playwright-cli session-list`. Artifacts such as snapshots, console output, and screenshots are usually written under `.playwright-cli/` relative to the shell working directory; the printed path is the source of truth.

### 2) Establish tab and session ground truth

- Run `tab-list`.
- Decide whether to reuse the current tab or open a temporary work tab.
- When you need a new work surface, use `tab-new` first and `open <url>` second.
- For local fixtures, do **not** assume `file://`, `localhost`, or LAN URLs are reachable from the browser context. If `open file:///...` is blocked or `open http://127.0.0.1:...` fails from the session, switch to one of these paths:
  - use a `data:` URL for a tiny self-contained fixture
  - expose the page on a publicly reachable staging/tunnel URL
  - stop and tell the user the current browser context cannot reach the local target

> **Steering experience:** Do NOT use `tab-new <url>`. It is documented but unreliable — in testing it frequently opens `about:blank` instead of the requested URL. The safe two-step pattern is `tab-new` then `open <url>`.

- Record the tab map before you continue.
- If a popup or forced new window is expected, route to `references/tabs.md` before acting.

### 3) Observe before touching the page

> **Steering experience:** `snapshot` writes a YAML accessibility-tree file to `.playwright-cli/page-<timestamp>.yml` and prints the **file path**, not the tree content. You must `cat` the file to read the actual refs. Example flow:
> ```bash
> playwright-cli snapshot          # prints: Snapshot saved to .playwright-cli/page-1710456789.yml
> cat .playwright-cli/page-1710456789.yml   # read the YAML to find refs like e0, e1, e5
> ```

Use the cheapest command that gives trustworthy state:

```bash
playwright-cli snapshot
playwright-cli eval "() => window.location.href"
```

Add only the extra proof you need:
- `playwright-cli screenshot --filename=...` for layout, visual regressions, or before/after evidence
- `playwright-cli eval "() => document.title"` or more specific `eval` checks when correctness matters
- `playwright-cli console error` and `playwright-cli network` when diagnosing failures or proving backend behavior
- Treat `playwright-cli eval "() => window.location.href"` as the URL source of truth. The CLI's printed page metadata can lag or report `about:blank` after odd tab/navigation flows.

### 4) Act with the smallest direct command

The CLI has far more commands than just `click` and `fill`. Here is the task-focused command surface for this skill:

| Category | Commands | Reference |
|---|---|---|
| Navigation | `open`, `reload`, `go-back`, `go-forward` | `references/navigation.md` |
| Inputs | `fill`, `fill --submit`, `type`, `type --submit`, `select`, `check`, `uncheck` | `references/forms.md` |
| Click / hover | `click`, `dblclick`, `hover` | `references/selectors.md` |
| Keyboard | `press <Key>` (e.g., `press Enter`, `press Tab`, `press Escape`) | `references/forms.md` |
| Viewport | `resize <w> <h>`, `mousewheel <deltaX> <deltaY>` | `references/screenshots.md` |
| Files | `upload /absolute/path/to/file` (file chooser must be active first) | `references/forms.md` |
| Tabs | `tab-new`, `tab-list`, `tab-select <i>`, `tab-close [i]` | `references/tabs.md` |
| Dialogs | `dialog-accept [text]`, `dialog-dismiss` | `references/tabs.md` |
| Screenshots | `screenshot [--full-page] [--filename=...]`, `screenshot <ref>` | `references/screenshots.md` |
| PDF | `pdf --filename=...` | `references/screenshots.md` |
| Video | `video-start`, `video-stop` | `references/screenshots.md` |
| Observation | `snapshot`, `eval "() => ..."`, `eval "(el) => ..." <ref>` | `references/selectors.md` |
| Debug | `console [error\|warning\|info]`, `console --clear`, `network [--static]`, `network --clear` | `references/debugging.md` |
| Tracing | `tracing-start`, `tracing-stop` | `references/debugging.md` |
| Sessions | `session-list`, `session-stop [name]`, `session-stop-all`, `session-restart [name]` | `references/tabs.md` |
| Code | `run-code 'async (page) => { ... }'` | `references/selectors.md` |

For session reuse, persisted auth, cookie/storage inspection, downloads, and route mocking, use `references/patterns.md`. The current CLI build handles those cases through named sessions, `eval`, and `run-code`, not dedicated `state-save`, `cookie-*`, `localstorage-*`, `sessionstorage-*`, or `route` shell subcommands.

Use direct commands with these rules:
- use `check` for radios and checkboxes when possible; it is safer than blind `click`
- after `fill`, `select`, or `check`, verify the live value with `eval`
- for uploads, trigger the file chooser first, then call `upload`
- if the page needs a wait, wait for a selector, URL, or response with `run-code`, then `snapshot`

> **Steering experience:** The `mousewheel <deltaX> <deltaY>` parameter order may be swapped in some CLI versions (deltaY first, deltaX second). Always test with a small value first and verify with `eval "() => window.scrollY"` before relying on large scroll distances. See `references/screenshots.md` for details.

### 5) Verify immediately after each meaningful action

> **Steering experience:** All artifact commands (`console`, `network`, `snapshot`, `screenshot`) write results to **files**, not to stdout. The CLI prints the file path; you must `cat` or inspect that file to see actual content. Never assume the page is clean or broken based on command output alone — always read the artifact file. Likewise, do not trust the header-style "Page URL" line over `eval "() => window.location.href"`.

Use the lightest proof that actually confirms success:

| Goal | Minimum proof |
|---|---|
| Navigation or redirect worked | `eval "() => window.location.href"` + `snapshot` |
| Form field changed | `eval "(el) => el.value" <ref>` or `eval "(el) => el.checked" <ref>` |
| Upload succeeded | `eval` file list + screenshot if the UI must show the file |
| Visual state matters | screenshot with descriptive filename + state proof |
| A bug or regression is suspected | `console --clear` / `network --clear`, reproduce, then `cat` returned artifact files |

> **Steering experience:** `console --clear` and `network --clear` produce **no visible output** — they succeed silently. This is expected behavior, not an error. Do not re-run them thinking they failed.

Use progressively stronger evidence when risk increases:
1. **State proof** — `snapshot` + `eval`
2. **Behavior proof** — state proof + action-specific assertion
3. **Visual proof** — behavior proof + screenshot(s)
4. **Diagnosis proof** — visual/state proof + console, network, or tracing artifacts

## Do this, not that

| Do this | Not that |
|---|---|
| Reuse a good existing tab or session when it already has the right state | Reset or isolate by default |
| `tab-new` then `open <url>` | `tab-new <url>` (unreliable — may open about:blank) |
| Keep a live tab map and confirm the active tab before each action | Assume tab indexes and URLs stayed the same |
| `snapshot` → `cat <file>` to read refs, and re-snapshot after page changes | Reuse old refs after navigation or rerender |
| `eval` for URL, value, checked state, counts, and ready state | Trust headers or command echo alone |
| `check` or `uncheck` for radios and checkboxes | Blind `click` on stateful inputs |
| Click the upload trigger, then `upload /absolute/path/...` | Call `upload` before the chooser is active |
| `cat` the file returned by `console` or `network` to inspect artifacts | Assume the command output alone proves anything |
| Use `run-code` only for waits or missing primitives, then `snapshot` | Stay in custom code longer than necessary |
| Close transient tabs when finished | Leave disposable tabs or scratch sessions behind |
| Run `playwright-cli install --browser=chrome` every time during bootstrap | Skip it and assume browser binary exists |
| Test `mousewheel` with a small value + `eval "() => window.scrollY"` first | Assume parameter order is correct |

## Recovery rules

If the workflow drifts, recover in this order:
1. **Unsure which tab is active** — `tab-list`, `tab-select`, `eval "() => window.location.href"`, `snapshot`
2. **Ref not found or action did nothing** — re-snapshot (`snapshot` → `cat <file>`), then retry with fresh refs
3. **SPA or lazy UI did not settle** — use `run-code` to wait for a selector, URL, or response, then `snapshot`
4. **Popup or new window appeared** — handle it via `references/tabs.md`, then re-verify the main tab before continuing
5. **Form or upload state is unclear** — `eval` live values or files; do not infer from command success
6. **Bug evidence is weak** — `console --clear` (silent), `network --clear` (silent), reproduce once, `cat` artifact files, then capture a screenshot
7. **You used `run-code`** — assume refs are dead and rebuild state with `snapshot`
8. **`mousewheel` scrolled wrong direction** — try swapping deltaX/deltaY parameters; verify with `eval "() => window.scrollY"`
9. **`--clear` seemed to fail** — it didn't; `--clear` produces no output by design

## Reference routing

Read only what matches the current job:

| Need | Reference |
|---|---|
| Page loads, redirects, waits, SPA navigation, URL verification | `references/navigation.md` |
| Inputs, selects, radios, uploads, date pickers, multi-step forms, submission proof | `references/forms.md` |
| Screenshots, responsive checks, dark mode, before/after comparisons, layout integrity | `references/screenshots.md` |
| Tabs, named sessions, popups, shared-session work, cleanup boundaries | `references/tabs.md` |
| Console/network artifacts, tracing, truth checks, diagnosis workflow, troubleshooting | `references/debugging.md` |
| Refs, `eval` usage, extraction, CSS fallback, iframes, shadow DOM, `run-code` selectors | `references/selectors.md` |
| Login, search and filter, downloads, storage, multi-step flows, E2E verification levels | `references/patterns.md` |

## Common starting points

- **Navigate and verify a page** — `references/navigation.md`
- **Fill, submit, and prove a form** — `references/forms.md` and `references/debugging.md` if submit is flaky
- **Work across multiple tabs or popups** — `references/tabs.md`
- **Collect visual proof** — `references/screenshots.md`
- **Diagnose why something failed** — `references/debugging.md`
- **Run a full workflow such as login or download** — `references/patterns.md`

## Cleanup

When browser work ends:
- close transient tabs you opened for the task
- stop or delete only the scratch sessions you created — use `session-stop` for the current isolated session or `session-stop <name>` for a named one
- keep shared or preexisting sessions alive unless the user asked for teardown
- if you collected evidence, preserve the returned artifact paths in your answer
