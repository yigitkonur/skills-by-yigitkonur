---
name: run-agent-browser
description: Use skill if you are driving agent-browser CLI @ref snapshots for stateful sessions, browser navigation, forms, screenshots, extraction, or provider/stealth runs.
allowed-tools: Bash(npx agent-browser:*), Bash(agent-browser:*)
---

# Browser Automation with agent-browser

Use this skill when the task should be executed through the `agent-browser` CLI: `@ref` snapshots, stateful sessions, providers, screenshots, DOM-grounded extraction, headed/stealth runs, or cloud-backed browser flows. If the task is diagnosis in DevTools rather than browser automation, use the relevant debug skill.

## Decision gate

| Need | Skill |
|---|---|
| `agent-browser`, `@ref`, `snapshot -i --json`, provider/stealth/session-name/profile flows | `run-agent-browser` |
| `@anthropic-ai/playwright-cli`, `playwright-cli snapshot`, Playwright CLI console/network artifacts | `run-playwright` |
| TypeScript browser automation code with `@onkernel/sdk` or Kernel Apps | `build-kernel-ts-sdk` |
| Rebuild a captured site into Next.js | `convert-url-to-nextjs` owns the build; call this skill only for capture |
| Document an existing SaaS/admin visual system | `extract-saas-design` owns the docs; call this skill only for browser evidence |

## Trigger boundaries

Use this skill for:
- terminal-driven browser automation with `agent-browser`
- form filling, login flows, data extraction, screenshots, and DOM-grounded web app checks with `@ref` snapshots
- multi-tab or multi-session workflows where `snapshot -i --json`, refs, and deterministic verification matter
- hosted, headed, stealth, profile, session-name, or provider-backed browser runs through the `agent-browser` CLI

Do not use this skill for:
- tasks explicitly asking for `playwright-cli`, Browserbase `browse`, or another browser CLI
- writing Playwright test code or running Playwright CLI workflows; use `run-playwright` or the repo's coding skill as appropriate
- Kernel SDK implementation work; use `build-kernel-ts-sdk`
- full site conversion or design-system extraction deliverables; return browser artifacts to `convert-url-to-nextjs` or `extract-saas-design`
- static research that does not require active browser interaction
- DevTools-first debugging or profiling unless the task still centers on `agent-browser`

## Mode and persistence gates

| Mode | Use when |
|---|---|
| default/headless | deterministic local/staging navigation, forms, extraction, screenshots |
| `--headed` | manual auth, 2FA, visual debugging, anti-bot pressure, human-observed flows |
| `--profile` | long-lived single-user auth across restarts |
| `--session-name` | named auto-persisted state for one app/account |
| `--session` | parallel isolated contexts in one run |
| `-p browserbase/browseruse/kernel/ios` | hosted, mobile, geo, or provider-backed browser runs through the CLI |
| `--engine lightpanda` | fast read-only/simple extraction where Lightpanda limitations are acceptable |

Choose one persistence strategy. Prefer the default ephemeral session, then `--session` for parallel isolation, `--session-name` for auto-persisted app state, `--profile` for native Chrome persistence, and `state save/load` only when a portable state file is required.

## Capture handoff

`convert-url-to-nextjs` may use this skill to capture live routes, DOM snapshots, screenshots, runtime metadata, and asset URLs before reconstruction. `extract-saas-design` may use this skill to inspect implemented UI evidence when source or snapshots need browser verification. After capture, hand artifacts back to the owning skill; do not take over rebuild or design-doc output.

For cross-skill calls, name the minimal artifacts:
- current URL and title
- `snapshot -i --json` or scoped snapshots
- relevant `get text`, `get attr`, or `get styles` outputs
- screenshot paths when visual evidence matters
- saved state or profile path only if intentionally created and safe to retain

## Non-negotiable operating rules

1. **Observe before acting.** After open, navigation, tab switch, popup, frame change, or major click, wait for state and run `snapshot -i` before choosing the next action.
2. **Reuse the current session by default.** Do not spawn a new session just because you changed pages.
3. **Prefer a new tab over a new window.** Use `window new` only when the site or task truly requires a separate window.
4. **Track focus before every action.** Know the active tab, URL, and title before clicking or typing.
5. **Verify after every meaningful interaction.** Check URL, title, text, value, visibility, checked state, or `diff snapshot` before assuming success.
6. **Treat DOM evidence as the source of truth.** Screenshots are supporting evidence for layout, failures, or human review.
7. **Close only what you opened.** Leave pre-existing tabs, windows, and reusable sessions alone unless the user asked to close them.
8. **Keep output scoped.** Prefer `snapshot -i`, scoped snapshots, `--json`, `get text`, and `get attr` over verbose full-page output.

## Default loop: observe → act → verify → clean up

### 1) Establish session and baseline

- Verify agent-browser is available before your first command. Run `agent-browser --version` (or `npx agent-browser --version`). If the command is not found, install with `npm install -g agent-browser` (pin a specific version in production — see `references/safety.md`).
- If the first real browser command fails because Chromium is missing, run `agent-browser install` once, then retry the same command. Treat browser-binary installation as part of the happy path, not a troubleshooting detour.
- If you may be joining an existing browser context, inspect it first:

```bash
agent-browser tab
agent-browser get url
agent-browser get title
agent-browser snapshot -i
```

- Reuse the default session for a single continuous task.
- Use `--session SESSION_NAME` only for isolated concurrent work.
- Use `--session-name SESSION_NAME` only when deliberate persistence across runs is valuable and safe.
- Use `--profile PATH` for permanent authentication persistence without manual save/load. When set globally (config.json or env var), all sessions automatically retain cookies, IndexedDB, service workers, and cache across browser restarts and reboots. See `references/authentication.md#persistent-profiles`.
- Use `--auto-connect` to import authentication from a running Chrome session the user is already logged into — fastest way to bootstrap auth for one-off tasks. See `references/authentication.md#import-auth-from-your-browser`.

### 2) Navigate or focus the correct page

- Open the target URL or switch to the correct tab.
- Local fixtures are valid targets. For local HTML or PDF files, use an absolute `file:///...` URL and add `--allow-file-access` when needed:

```bash
agent-browser --allow-file-access open "file:///absolute/path/to/fixture.html"
```

- After any focus change, verify focus immediately:

```bash
agent-browser tab
agent-browser get url
agent-browser get title
agent-browser snapshot -i
```

- Never assume a newly opened tab, popup, or site-driven redirect left you on the expected page.

### 3) Inspect before interacting

- Use `snapshot -i` first. Note: `snapshot -i` shows only interactive elements (links, buttons, inputs, checkboxes). Non-interactive text (headings, paragraphs, spans) is invisible in this view.
- Use `snapshot -i --json` when you need structured extraction or machine-readable branching logic. The JSON schema is `{success, data: {origin, refs: {refId: {name, role, ...}}, snapshot: string}, error}` — access refs via `.data.refs`, not `.elements[]`.
- For data extraction from non-interactive text, use `get text CSS_SELECTOR` (must match exactly one element) or `eval --stdin` with a heredoc for multi-element extraction.
- If expected UI elements are missing from `snapshot -i`, the page may use custom components (dropdowns, popovers, accordions) whose children only appear after clicking the trigger. Click the likely trigger → re-snapshot → verify new elements appeared.
- Use `screenshot --annotate` only when visual layout, canvas content, or element disambiguation matters.
- Selector priority:
  1. `@refs` from `snapshot -i`
  2. semantic `find`
  3. CSS selectors
  4. XPath only as a last resort
- When extracting structured data, prefer JSON arrays or objects unless the user asked for CSV or a table. Include selector/ref provenance and count checks; route deeper patterns to `references/workflows.md`.

### 4) Interact one state change at a time

- Prefer small, verifiable steps over long blind chains.
- Chain commands only when you do not need intermediate output.
- After any action that can change DOM or focus, wait and re-snapshot before reusing refs.
- Refs are invalid after navigation, SPA route changes, modal expansion, dynamic loading, tab switching, and many form submissions.
- Use `agent-browser back` (not `go back`) to return to the previous page. Prefer `back` over re-navigating with `open URL` to preserve history. Treat it like a navigation event: re-snapshot after.
- Note: `check` and `uncheck` return the new checked state (`true`/`false`) rather than `✓ Done`. This is expected.

### 5) Verify the result before moving on

Use at least one deterministic check after each major interaction:
- `agent-browser get url`
- `agent-browser get title`
- `agent-browser get text REF_OR_SELECTOR` — selector must match exactly one element; for multiple matches use `eval --stdin` with JS
- `agent-browser get value REF_OR_SELECTOR`
- `agent-browser is visible REF`
- `agent-browser is checked REF` — works for both checkboxes and radio buttons
- `agent-browser diff snapshot`
- If `snapshot -i` returns `(no interactive elements)` (e.g. after form submission to a raw response page), verify with `get text body` for page content or `get url` / `get title` for navigation confirmation.
- For visual verification or archival: `agent-browser screenshot /tmp/descriptive-name.png`

Capture screenshots only when you need:
- visual evidence for a human
- layout or styling confirmation
- failure triage
- annotated element mapping

### 6) Clean up deliberately

- If you opened auxiliary tabs, close them with `agent-browser tab close INDEX` (get the index from `tab` listing) and return to the original tab.
- If you started isolated sessions, close those sessions when their work is done.
- If you used persisted state or state files, secure them and avoid leaving secrets behind.
- If you opened a fresh disposable default session for the task, close it at the end.

## Session, tab, and window hygiene

### Session choice

- Same task, same auth context: stay in the current or default session.
- Concurrent or role-separated work: use named `--session` sessions.
- Intentional long-lived login reuse across runs: use `--session-name`, `auth`, or `state save/load`.
- Permanent auth persistence without manual save/load: use `--profile` (set globally via config.json `{"profile": "~/.myapp"}` or `AGENT_BROWSER_PROFILE` env var).

### Tab and window rules

- Prefer `tab new URL` for side routes, docs, exports, or OAuth flows that should not disturb the current page.
- Prefer switching back to the original tab instead of reopening pages from scratch.
- Use `window new` only if the site truly requires a separate window or the user asked for one.
- After `tab new`, `tab INDEX`, or any action that opens a popup or new tab, verify focus with `tab`, `get url`, `get title`, then `snapshot -i`.
- Treat tab switches like navigation for ref lifecycle purposes: re-snapshot after every switch.

### Cleanup rules

- Record which tab or session you started in.
- Record which tabs, windows, or sessions you created.
- Close only the ones you created.
- If the browser context pre-existed, leave it in a sane state and avoid shutting it down unnecessarily.

## Do this, not that

| Do this | Not that |
|---|---|
| Reuse the current session when the task stays in the same auth and state context | Start a brand-new session for every page |
| Open a new tab for side work, then verify focus | Spawn unnecessary windows or assume the new tab is active |
| Run `snapshot -i` before interaction and after every major change | Reuse stale refs after navigation or tab switches |
| Use `get text`, `get value`, `is visible`, `diff snapshot`, and URL/title checks | Treat screenshots as the only proof an action worked |
| Use `snapshot -i --json` or targeted getters for extraction | Pull huge raw outputs when a narrow query would do |
| Use `eval --stdin` heredoc for multi-element data extraction | Use inline `eval "..."` with complex JS (shell escaping breaks) |
| Use `agent-browser back` to return to previous page | Re-navigate with `open URL` (loses form state and history) |
| Scope snapshots with `-s` on complex pages | Parse through 100+ flat elements looking for the right ref |
| Close only tabs and sessions you created | Blindly run `agent-browser close` on a shared or reusable context |

## Recovery paths

- **Ref not found or wrong element:** re-check focus, then `snapshot -i` again. If the page changed, old refs are stale. If the page is crowded, scope the snapshot or use `find`.
- **Multiple elements match a CSS selector:** `get text CSS_SELECTOR` requires exactly one match (strict mode). For multi-element extraction, use `eval --stdin` with a heredoc to run a JS query:
  ```bash
  agent-browser eval --stdin <<'EVALEOF'
  Array.from(document.querySelectorAll('.item-title')).map(el => el.textContent.trim()).slice(0, 10);
  EVALEOF
  ```
- **Unexpected redirect or login screen:** verify URL and title first, then decide whether to load saved state, use auth vault, or continue with a login flow.
- **Slow or flaky page:** use explicit waits, increase timeout if needed, then re-snapshot.
- **Too much snapshot output:** use `snapshot -i`, `snapshot -i --json`, scoped snapshots, or targeted getters instead of full page dumps.
- **Stale daemon or broken session:** try `agent-browser close`; if that fails, follow `references/troubleshooting.md`.
- **Sensitive operations needed:** before `eval`, downloads, state persistence, storage writes, cookies, network routing, or unsafe flags, read `references/safety.md` and narrow scope first.

## Minimal reference routing

| Need | Read |
|---|---|
| Install, config, environment setup | `references/installation.md` |
| Core commands, check-state commands, tabs, windows, diff | `references/commands.md` |
| Ref lifecycle, scoped snapshots, stale-ref recovery | `references/snapshot-refs.md` |
| Session reuse, named sessions, persistence, cleanup | `references/session-management.md` |
| Login flows, auth vault, saved state | `references/authentication.md` |
| Safe automation boundaries and sensitive-command policy | `references/safety.md` |
| Observe and verify loops, DOM-evidence validation, extraction patterns | `references/workflows.md` |
| Stale daemon, timeout, and focus-related failures | `references/troubleshooting.md` |
| Proxies, stealth, cloud browsers, extensions, iOS, profiling, video | `references/proxy-support.md`, `references/stealth-automation.md`, `references/advanced.md`, `references/profiling.md`, `references/video-recording.md` |
| Ready-made shell starting points | `templates/ai-agent-workflow.sh`, `templates/form-automation.sh`, `templates/authenticated-session.sh`, `templates/e2e-test-workflow.sh`, `templates/capture-workflow.sh` |

## Minimal reading sets

### Form or login automation
- `references/snapshot-refs.md`
- `references/authentication.md`
- `references/commands.md`

### Multi-tab, popup, or session-heavy work
- `references/session-management.md`
- `references/commands.md`
- `references/troubleshooting.md`

### Data extraction or verification
- `references/snapshot-refs.md` (JSON schema, snapshot limitations, scoped snapshots)
- `references/workflows.md` (multi-element extraction pattern, hidden UI discovery)
- `references/commands.md` (get text, get count, eval --stdin, find commands)

### Safe or production-like automation
- `references/safety.md`
- `references/session-management.md`
- `references/workflows.md`

## Output contract

When browser work ends, report:
- final active URL and title
- session, profile, provider, engine, or headed mode used when non-default
- deterministic verification performed, such as `get url`, `get title`, `get text`, `get value`, `is visible`, or `diff snapshot`
- screenshot, video, trace, profile, or saved-state paths if created
- extracted data shape when data was extracted, such as JSON array, CSV rows, table, or key-value map, plus selectors/refs used and count checks
- cleanup performed: tabs closed, sessions closed, state files kept/deleted, or persistent profile left in place

## Final reminder

This SKILL.md is the steering layer. Keep the live loop disciplined:
1. establish session and focus
2. observe (`snapshot -i` for interaction, `get text`/`eval` for extraction)
3. act (one state change, then verify)
4. verify (URL, title, text, value, `diff snapshot`)
5. record evidence only as needed (`screenshot` for visual proof)
6. clean up only what you changed (`tab close INDEX`, `close`)

Key rules to internalize:
- `snapshot -i` hides non-interactive text -- use `get text` or `eval --stdin` for data extraction
- CSS selectors in `get text` must match exactly one element -- use `eval --stdin` for multiples
- `eval --stdin <<'EVALEOF'` heredoc is the safe JS execution pattern
- `diff snapshot` is the correct diff form (not bare `diff`)
- `back` works (not `go back`)
- Refs expire after any page/DOM change -- always re-snapshot

When in doubt, stop acting, inspect state again, and route into the smallest relevant reference instead of guessing.
