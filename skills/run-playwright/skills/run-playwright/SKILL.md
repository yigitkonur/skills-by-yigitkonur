---
name: run-playwright
description: Use skill if you are driving playwright-cli from @playwright/cli for live browser navigation, forms, screenshots, tabs, sessions, or terminal debugging.
---

# Playwright Agent CLI

Use `@playwright/cli`'s `playwright-cli` binary to drive a live browser from the terminal. This skill owns CLI-driven browser sessions, Playwright Agent CLI artifacts, and `npx playwright test --debug=cli` investigation. It does not own normal `@playwright/test` authoring unless the user explicitly asks for CLI-backed live debugging or verification.

## Trigger Boundary

| Use | When |
|---|---|
| `run-playwright` | User names `playwright-cli`, Playwright Agent CLI, `@playwright/cli`, `--debug=cli`, trace/debug commands, or asks for Playwright-specific screenshots, traces, locators, storage state, or session evidence. |
| `run-agent-browser` | User names `agent-browser`, needs that CLI's DOM-grounded workflow, local/file target flags, or agent-browser profile/auth features. |
| `build-kernel-ts-sdk` | Work is a Kernel SDK/browser-cloud app or service using `@onkernel/sdk`. |
| `build-chrome-extension` | Work is extension implementation or extension-specific debugging. Use `run-playwright` only for separate browser verification when requested. |

Do not use this skill for:

- writing or refactoring Playwright test suites without live CLI control
- static scraping, HTTP fetching, or code review where no browser session is needed
- programmatic browser automation libraries unless the user wants `playwright-cli`
- browser-cloud or anti-bot routing work owned by Kernel or another provider

## Source Of Truth

1. Check the executable first: `playwright-cli --help` and `playwright-cli --help <command>`.
2. Use official docs as context, but prefer installed help when docs disagree with the package.
3. For the verified `@playwright/cli@0.1.13` surface, network inspection is `requests` / `request`, not `network`, even though some docs still say `network`.
4. If a command in docs is absent from help, say so in the final evidence instead of guessing.

## Bootstrap

Node.js 20+ is required.

Prefer an existing command only after confirming it exposes the current public surface:

```bash
playwright-cli --version
playwright-cli --help install-browser
playwright-cli --help state-save
```

If the project has a local install, use it without downloading another package:

```bash
npx --no-install playwright-cli --version
npx --no-install playwright-cli --help
```

For ad hoc execution without a local install, use the current public package:

```bash
npx -y @playwright/cli@latest --version
npx -y @playwright/cli@latest --help
```

If an existing global binary is old and lacks current commands such as `install-browser`, `state-save`, `list`, or `show`, use `npx -y @playwright/cli@latest` for the task or replace the global install. Install globally only when repeated commands need a stable `playwright-cli` binary:

```bash
npm install -g @playwright/cli@latest
playwright-cli --help
```

Install a browser explicitly when first use reports a missing browser or the environment is fresh:

```bash
playwright-cli install-browser          # default chromium
playwright-cli install-browser firefox
playwright-cli install-browser --with-deps
```

Use `scripts/check-playwright-cli.sh` for a no-launch environment and drift check. Use `scripts/launch-debug-session.sh` as a safe opener for live debugging.

## Operating Rules

1. Keep one command per shell invocation. There is no required interactive prompt.
2. Observe before acting: `snapshot`, URL/title checks, or `show` when visual state matters.
3. Re-snapshot after navigation, tab switch, rerender, submit, popup handling, storage changes, routing changes, or `run-code`.
4. Treat refs as short-lived. Use fresh refs from the most recent snapshot.
5. Use direct CLI commands before `run-code`. Return to snapshot-driven commands after any custom code.
6. Prefer headless/default mode for automated checks. Use `open --headed` for live observation, UI review, 2FA/CAPTCHA handoff, or user-visible debugging.
7. Track sessions and tabs you create. Close only those unless the user asked for a full teardown.
8. Inspect returned output and artifact paths. If the CLI prints a file path, read that file before using it as evidence.

## Core Workflow

### 1. Choose Session And Visibility

```bash
playwright-cli list
playwright-cli open https://example.com
playwright-cli open https://example.com --headed
playwright-cli -s=checkout-debug open https://example.com --persistent
PLAYWRIGHT_CLI_SESSION=checkout-debug playwright-cli snapshot
```

Use:

- default in-memory session for short tasks
- `-s=name` for parallel work, role separation, or a named debug target
- `PLAYWRIGHT_CLI_SESSION` when every command in the shell should use one session
- `open --persistent` to preserve a generated profile on disk
- `open --profile=./profile-dir` only when the profile path is intentionally managed
- `state-save` / `state-load` for portable auth state files

Cleanup boundaries:

```bash
playwright-cli close                    # close current/default session
playwright-cli -s=checkout-debug close  # close named session
playwright-cli -s=checkout-debug delete-data  # delete owned scratch profile data
playwright-cli close-all                # only when you own all sessions
playwright-cli kill-all                 # only for stale/zombie process recovery
```

### 2. Navigate And Observe

Use `open [url]` to start a browser. Use `goto <url>` to navigate an already-open session.

```bash
playwright-cli open https://example.com
playwright-cli goto https://example.com/account
playwright-cli snapshot
playwright-cli eval "() => window.location.href"
```

For tabs:

```bash
playwright-cli tab-list
playwright-cli tab-new https://example.com/docs
playwright-cli tab-select 0
playwright-cli tab-close 1
```

Current `@playwright/cli@0.1.13` help supports `tab-new [url]`, and a smoke test with a `data:` URL opened the requested URL. If an older build opens `about:blank`, recover with `tab-new` then `goto <url>` and record the drift.

### 3. Act With The Smallest Command

| Need | Commands | Detail |
|---|---|---|
| Navigation | `open`, `goto`, `reload`, `go-back`, `go-forward` | `references/navigation.md` |
| Inputs/forms | `fill`, `fill --submit`, `type`, `type --submit`, `select`, `check`, `uncheck`, `press`, `upload`, `drop` | `references/forms.md` |
| Selectors/refs | `snapshot`, `eval`, `click`, `dblclick`, `hover`, `generate-locator`, `highlight` | `references/selectors.md` |
| Tabs/dialogs | `tab-list`, `tab-new`, `tab-select`, `tab-close`, `dialog-accept`, `dialog-dismiss` | `references/tabs.md` |
| Screenshots/media | `screenshot`, `pdf`, `video-start`, `video-stop`, `video-chapter`, `resize` | `references/screenshots.md` |
| Storage/auth | `state-save`, `state-load`, `cookie-*`, `localstorage-*`, `sessionstorage-*`, `open --persistent`, `open --profile` | `references/patterns.md` |
| Network | `requests`, `request`, `request-*`, `response-*`, `route`, `route-list`, `unroute`, `network-state-set` | `references/debugging.md` |
| Traces/debug | `console`, `tracing-start`, `tracing-stop`, `show`, `show --annotate`, `pause-at`, `resume`, `step-over`, `attach` | `references/debugging.md`, `references/interactive-debugging.md` |
| Custom code | `run-code` | `references/selectors.md` |

### 4. Verify After Meaningful Changes

| Goal | Minimum proof |
|---|---|
| Navigation or redirect | `eval "() => window.location.href"` plus `snapshot` |
| Form state | `eval "(el) => el.value" <ref>` or checked/selected state |
| Visual state | screenshot path plus URL/state proof |
| Auth persistence | `state-save`/`state-load` path or named/persistent session evidence |
| Network behavior | `requests` summary plus `request <index>` or response detail when needed |
| Trace/debug session | `tracing-stop` path, command sequence, and test/session state |

Verification rungs for final answers:

1. State: snapshot, URL/title, DOM value, storage, or network state checked
2. Behavior: user flow/action completed and verified
3. Visual: screenshot/PDF/video captured and tied to state
4. Diagnosis: console, requests, trace, or debugger evidence captured
5. Test-debug: attached to a paused Playwright test and stepped/resumed to a finding

## Output Contract

When browser work ends, report:

- session name or default session used
- tabs/sessions created and cleanup performed
- verification rung reached: state, behavior, visual, diagnosis, or test-debug session
- artifact paths returned by the CLI: snapshot YAML/Markdown, screenshot, trace zip, video, PDF, state file, downloaded file
- any commands that could not be verified because docs and installed help disagreed

## Reference Routing

Read only what matches the current job:

| Need | Reference |
|---|---|
| Page loads, redirects, waits, SPA navigation, URL checks | `references/navigation.md` |
| Inputs, selects, radios, uploads, date pickers, multi-step forms | `references/forms.md` |
| Screenshots, PDFs, video, responsive checks, trace viewer handoff | `references/screenshots.md` |
| Tabs, sessions, popups, named sessions, cleanup boundaries | `references/tabs.md` |
| Console, requests, routing, tracing, diagnosis workflow | `references/debugging.md` |
| Refs, `eval`, CSS fallback, locators, iframes, shadow DOM, `run-code` | `references/selectors.md` |
| Login, storage state, cookies, local/session storage, downloads, E2E patterns | `references/patterns.md` |
| `npx playwright test --debug=cli`, `attach`, stepping, dashboard, locator generation | `references/interactive-debugging.md` |
| CLI availability and drift check | `scripts/check-playwright-cli.md` |
| Canonical live debug opener | `scripts/launch-debug-session.md` |

## Recovery

1. Wrong tab/session: `list`, `tab-list`, `tab-select`, URL check, `snapshot`.
2. Ref failed: re-snapshot and retry with fresh refs.
3. Page not settled: wait with `run-code`, then re-snapshot.
4. Docs/help conflict: trust `playwright-cli --help <command>` and record the conflict.
5. Browser missing: run `install-browser [browser]`, then retry.
6. Stale browser processes: close owned sessions first; use `kill-all` only for stale/zombie recovery you intentionally own.
