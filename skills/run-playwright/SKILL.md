---
name: run-playwright
description: Use skill if you are controlling a live browser with @anthropic-ai/playwright-cli for navigation, forms, screenshots, tab workflows, or interactive debugging from the terminal.
---

# Playwright CLI

Use `@anthropic-ai/playwright-cli` to drive a live browser from the terminal. Keep this file focused on trigger logic, workflow, guardrails, and reference routing. Use `references/` for detailed commands, edge cases, and larger patterns.

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
playwright-cli install --browser=chrome
```

- If an existing session or tab already contains the needed login or state, inspect it first instead of resetting everything.
- Start a named session or isolated browser only when you need clean-room state, parallel isolation, or risky experimentation; use `references/tabs.md` for the exact bootstrap patterns.
- Do not begin with `session-stop-all` unless you intentionally want to discard every active browser.

### 2) Establish tab and session ground truth

- Run `tab-list`.
- Decide whether to reuse the current tab or open a temporary work tab.
- When you need a new work surface, use `tab-new` first and `open <url>` second.
- Record the tab map before you continue.
- If a popup or forced new window is expected, route to `references/tabs.md` before acting.

### 3) Observe before touching the page

Use the cheapest command that gives trustworthy state:

```bash
snapshot
eval "() => window.location.href"
```

Add only the extra proof you need:
- `screenshot --filename=...` for layout, visual regressions, or before/after evidence
- `eval "() => document.title"` or more specific `eval` checks when correctness matters
- `console error` and `network` when diagnosing failures or proving backend behavior

### 4) Act with the smallest direct command

Prefer the direct CLI primitive over custom code:
- navigation: `open`, `reload`, `go-back`, `go-forward`
- inputs: `fill`, `type`, `select`, `check`, `uncheck`
- clicks and hovers: `click`, `dblclick`, `hover`
- tabs: `tab-new`, `tab-list`, `tab-select`, `tab-close`

Use direct commands with these rules:
- use `check` for radios and checkboxes when possible; it is safer than blind `click`
- after `fill`, `select`, or `check`, verify the live value with `eval`
- for uploads, trigger the file chooser first, then call `upload`
- if the page needs a wait, wait for a selector, URL, or response with `run-code`, then `snapshot`

### 5) Verify immediately after each meaningful action

Use the lightest proof that actually confirms success:

| Goal | Minimum proof |
|---|---|
| Navigation or redirect worked | `eval "() => window.location.href"` + `snapshot` |
| Form field changed | `eval "(el) => el.value" <ref>` or `eval "(el) => el.checked" <ref>` |
| Upload succeeded | `eval` file list + screenshot if the UI must show the file |
| Visual state matters | screenshot with descriptive filename + state proof |
| A bug or regression is suspected | `console --clear` / `network --clear`, reproduce, then inspect returned artifact files |

Use progressively stronger evidence when risk increases:
1. **State proof** — `snapshot` + `eval`
2. **Behavior proof** — state proof + action-specific assertion
3. **Visual proof** — behavior proof + screenshot(s)
4. **Diagnosis proof** — visual/state proof + console, network, or tracing artifacts

## Do this, not that

| Do this | Not that |
|---|---|
| Reuse a good existing tab or session when it already has the right state | Reset or isolate by default |
| `tab-new` then `open <url>` | `tab-new <url>` |
| Keep a live tab map and confirm the active tab before each action | Assume tab indexes and URLs stayed the same |
| `snapshot` before using refs, and again after page changes | Reuse old refs after navigation or rerender |
| `eval` for URL, value, checked state, counts, and ready state | Trust headers or command echo alone |
| `check` or `uncheck` for radios and checkboxes | Blind `click` on stateful inputs |
| Click the upload trigger, then `upload /absolute/path/...` | Call `upload` before the chooser is active |
| Inspect the file returned by `console` or `network` | Assume the command output alone proves anything |
| Use `run-code` only for waits or missing primitives, then `snapshot` | Stay in custom code longer than necessary |
| Close transient tabs when finished | Leave disposable tabs or scratch sessions behind |

## Recovery rules

If the workflow drifts, recover in this order:
1. **Unsure which tab is active** — `tab-list`, `tab-select`, `eval "() => window.location.href"`, `snapshot`
2. **Ref not found or action did nothing** — re-snapshot, then retry with fresh refs
3. **SPA or lazy UI did not settle** — use `run-code` to wait for a selector, URL, or response, then `snapshot`
4. **Popup or new window appeared** — handle it via `references/tabs.md`, then re-verify the main tab before continuing
5. **Form or upload state is unclear** — `eval` live values or files; do not infer from command success
6. **Bug evidence is weak** — clear console/network, reproduce once, inspect artifact files, then capture a screenshot
7. **You used `run-code`** — assume refs are dead and rebuild state with `snapshot`

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
- stop or delete only the scratch named sessions you created
- keep shared or preexisting sessions alive unless the user asked for teardown
- if you collected evidence, preserve the returned artifact paths in your answer
