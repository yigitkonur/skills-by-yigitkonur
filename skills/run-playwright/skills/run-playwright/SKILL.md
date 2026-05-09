---
name: run-playwright
description: Use skill if you are driving playwright-cli from @playwright/cli or attaching to @playwright/test --debug=cli for live browser sessions, snapshots, traces, or selector debugging.
---

# run-playwright

Drive the `playwright-cli` binary from `@playwright/cli` to operate a live browser from the terminal: navigate, fill forms, snapshot the DOM, capture screenshots/traces, manage tabs and sessions, and attach to a paused `@playwright/test` run via `--debug=cli`. Snapshot-driven, ref-grounded, deterministic.

## When to use

Use this skill when:

- *the user names `playwright-cli`, `@playwright/cli`, the Playwright Agent CLI, or `--debug=cli`*
- *the request is `playwright-cli <command>` style — `open`, `snapshot`, `goto`, `fill`, `screenshot`, `tracing-start`, `state-save`, `attach`, etc.*
- *a `@playwright/test` run is paused (`npx playwright test --debug=cli`) and needs interactive attach, stepping, locator inspection, or `show` dashboard work*
- *the deliverable is Playwright-specific evidence: a snapshot YAML/Markdown, trace zip, screenshot, video, PDF, storage state file, or `requests`/`request` network log*
- *the workspace shows Playwright signals: `playwright.config.ts`, `playwright.config.js`, `tests/*.spec.ts`, imports of `@playwright/test`, or `@playwright/cli` in `package.json`*
- *the task requires CLI-backed live verification of a flow already covered by Playwright tests, separate from authoring new specs*
- *named or persistent sessions, storage state, cookies, local/session storage, or profile dirs need to be captured and replayed*
- *DOM-grounded debugging via refs (`e3`, `e5`) — `snapshot` -> act -> verify -> re-snapshot — is the right loop*

Do NOT use this skill for:

- *generic ad-hoc browser automation where the user names `agent-browser`, `@ref` snapshots, or provider/stealth flows* — use `run-agent-browser`
- *authoring or refactoring `@playwright/test` spec files (no live CLI control involved)* — write the test directly without this skill
- *building or extending a Kernel SDK / browser-cloud app using `@onkernel/sdk`* — use `build-kernel-ts-sdk`
- *Chrome extension implementation or extension-internal debugging* — use `build-chrome-extension` (call this skill only for separate-browser verification when explicitly asked)
- *static scraping, HTTP fetching, or code review tasks where no browser session is needed*

## Source of truth

1. The installed binary wins over docs. Always confirm command surface with `playwright-cli --help` and `playwright-cli --help <command>` before relying on a command from memory.
2. For `@playwright/cli@0.1.13` (the verified surface), network inspection commands are `requests` / `request` / `request-*` / `response-*`, not `network`. Some external docs still say `network` — trust installed help.
3. If a command in external docs is absent from `--help`, treat it as drift and record the gap in the final evidence; do not guess flags.
4. Run `scripts/check-playwright-cli.sh` once per fresh shell to detect stale binaries before scripting against a command surface.

## Bootstrap

Node.js 20+ is required.

```bash
playwright-cli --version                        # global install
npx --no-install playwright-cli --version       # local install in repo
npx -y @playwright/cli@latest --version         # ad hoc, current public package
```

Install a browser explicitly when first use reports a missing browser or the environment is fresh:

```bash
playwright-cli install-browser                  # default chromium
playwright-cli install-browser firefox
playwright-cli install-browser --with-deps
```

If an existing global binary is old and lacks current commands (`install-browser`, `state-save`, `list`, `show`), use `npx -y @playwright/cli@latest` for the task or replace the global install. Install globally only when repeated commands need a stable `playwright-cli` binary:

```bash
npm install -g @playwright/cli@latest
```

For environment and drift checks, use `scripts/check-playwright-cli.md` (read-only). For a canonical live opener, use `scripts/launch-debug-session.md`.

## Operating rules

These are load-bearing. Violating them breaks the snapshot/ref contract and produces unverifiable output.

1. **One command per shell invocation.** No interactive prompt is required; chain through repeat invocations, not subshells.
2. **Observe before acting.** `snapshot`, URL/title check, or `show` before any click/fill/goto when state matters.
3. **Re-snapshot after every state change** — navigation, tab switch, rerender, submit, popup, storage write, route change, or any `run-code` block. Stale refs from a prior snapshot will silently fail.
4. **Refs are short-lived.** Use only refs from the most recent snapshot. Never copy a ref across navigation.
5. **Direct CLI commands first; `run-code` last.** Return to snapshot-driven commands after any custom JS.
6. **Headless by default.** Use `open --headed` only for live observation, UI review, 2FA/CAPTCHA handoff, or user-visible debugging.
7. **Track what you create.** Sessions and tabs you opened are yours to close. Never `close-all` or `kill-all` unless the user asked for full teardown.
8. **Read what the CLI prints.** When a command returns a file path, read that file before claiming it as evidence.
9. **Mind drift.** When `--help` and external docs disagree, trust `--help` and record the conflict in the final report.

## Core workflow

### 1. Choose session and visibility

```bash
playwright-cli list
playwright-cli open https://example.com
playwright-cli open https://example.com --headed
playwright-cli -s=checkout-debug open https://example.com --persistent
PLAYWRIGHT_CLI_SESSION=checkout-debug playwright-cli snapshot
```

Pick:

- default in-memory session for short, single-shot tasks
- `-s=<name>` for parallel work, role separation, or a named debug target
- `PLAYWRIGHT_CLI_SESSION` when every command in the shell should use one session
- `open --persistent` to preserve a generated profile on disk
- `open --profile=./profile-dir` only when the profile path is intentionally managed
- `state-save` / `state-load` for portable auth state files

Cleanup, in order of escalating scope:

```bash
playwright-cli close                             # current/default session
playwright-cli -s=checkout-debug close           # named session
playwright-cli -s=checkout-debug delete-data     # owned scratch profile data
playwright-cli close-all                         # only when you own all sessions
playwright-cli kill-all                          # only for stale/zombie process recovery
```

### 2. Navigate and observe

`open [url]` starts a session. `goto <url>` navigates an already-open session.

```bash
playwright-cli open https://example.com
playwright-cli goto https://example.com/account
playwright-cli snapshot
playwright-cli eval "() => window.location.href"
```

Tabs:

```bash
playwright-cli tab-list
playwright-cli tab-new https://example.com/docs
playwright-cli tab-select 0
playwright-cli tab-close 1
```

`@playwright/cli@0.1.13` supports `tab-new [url]`. Older builds may open `about:blank` — recover with `tab-new` then `goto <url>` and record the drift.

### 3. Act with the smallest command

| Need | Commands | Reference |
|---|---|---|
| Page loads, redirects, waits, SPA navigation, URL/title verification | `open`, `goto`, `reload`, `go-back`, `go-forward` | `references/navigation.md` |
| Inputs, selects, radios, uploads, date pickers, multi-step forms | `fill`, `fill --submit`, `type`, `type --submit`, `select`, `check`, `uncheck`, `press`, `upload`, `drop` | `references/forms.md` |
| Refs, `eval`, CSS fallback, locators, iframes, shadow DOM, custom JS | `snapshot`, `eval`, `click`, `dblclick`, `hover`, `generate-locator`, `highlight`, `run-code` | `references/selectors.md` |
| Tabs, popups, dialogs, named sessions, cleanup boundaries | `tab-list`, `tab-new`, `tab-select`, `tab-close`, `dialog-accept`, `dialog-dismiss` | `references/tabs.md` |
| Screenshots, PDFs, video, responsive checks, trace viewer handoff | `screenshot`, `pdf`, `video-start`, `video-stop`, `video-chapter`, `resize` | `references/screenshots.md` |
| Login, storage state, cookies, local/session storage, downloads, E2E patterns | `state-save`, `state-load`, `cookie-*`, `localstorage-*`, `sessionstorage-*`, `open --persistent`, `open --profile` | `references/patterns.md` |
| Console, requests, routing, tracing, diagnosis | `console`, `requests`, `request`, `request-*`, `response-*`, `route`, `route-list`, `unroute`, `network-state-set`, `tracing-start`, `tracing-stop`, `show`, `show --annotate` | `references/debugging.md` |
| Attach to a paused `@playwright/test` run, step through, inspect locators | `attach`, `pause-at`, `resume`, `step-over`, `show`, `generate-locator`, `highlight` | `references/interactive-debugging.md` |

### 4. Verify after meaningful changes

| Goal | Minimum proof |
|---|---|
| Navigation or redirect | `eval "() => window.location.href"` plus `snapshot` |
| Form state | `eval "(el) => el.value" <ref>` or checked/selected state |
| Visual state | screenshot path plus URL/state proof |
| Auth persistence | `state-save`/`state-load` path or named/persistent session evidence |
| Network behavior | `requests` summary plus `request <index>` or response detail when relevant |
| Trace/debug session | `tracing-stop` path, command sequence, and test/session state |

Verification rungs to claim only what was reached:

1. **State** — snapshot, URL/title, DOM value, storage, or network state checked
2. **Behavior** — user flow/action completed and verified
3. **Visual** — screenshot/PDF/video captured and tied to state
4. **Diagnosis** — console, requests, trace, or debugger evidence captured
5. **Test-debug** — attached to a paused Playwright test and stepped/resumed to a finding

## Output contract

When browser work ends, report:

- session name (or default) used
- tabs/sessions created and cleanup performed
- verification rung reached
- artifact paths returned by the CLI: snapshot YAML/Markdown, screenshot, trace zip, video, PDF, state file, downloaded file
- any commands that could not be verified because docs and installed help disagreed

## Reference routing

Read only what matches the current job:

| Need | Reference |
|---|---|
| Page loads, redirects, waits, SPA navigation, URL checks | `references/navigation.md` |
| Inputs, selects, radios, uploads, date pickers, multi-step forms | `references/forms.md` |
| Refs, `eval`, CSS fallback, locators, iframes, shadow DOM, `run-code` | `references/selectors.md` |
| Tabs, sessions, popups, named sessions, cleanup boundaries | `references/tabs.md` |
| Screenshots, PDFs, video, responsive checks, trace viewer handoff | `references/screenshots.md` |
| Login, storage state, cookies, local/session storage, downloads, E2E patterns | `references/patterns.md` |
| Console, requests, routing, tracing, diagnosis workflow | `references/debugging.md` |
| `npx playwright test --debug=cli`, `attach`, stepping, dashboard, locator generation | `references/interactive-debugging.md` |
| CLI availability and drift check | `scripts/check-playwright-cli.md` |
| Canonical live debug opener | `scripts/launch-debug-session.md` |

## Recovery

1. **Wrong tab/session** — `list`, `tab-list`, `tab-select`, URL check, `snapshot`.
2. **Ref failed** — re-snapshot and retry with fresh refs.
3. **Page not settled** — wait with `run-code`, then re-snapshot.
4. **Docs/help conflict** — trust `playwright-cli --help <command>` and record the conflict.
5. **Browser missing** — run `install-browser [browser]`, then retry.
6. **Stale browser processes** — close owned sessions first; use `kill-all` only for stale/zombie recovery you intentionally own.
