---
name: run-playwright
description: Use skill if you are automating a browser with @anthropic-ai/playwright-cli for navigation, forms, screenshots, tab flows, debugging, or small run-code steps.
---

# Playwright CLI

Validated against the installed `playwright-cli` binary on this machine (`0.0.62`).
Treat the installed CLI help and live runtime behavior as the primary authority.
Prefer this skill's documented + tested workflow over copied snippets from older skills.

## How playwright-cli actually works

`playwright-cli` gives you a browser session controlled through terminal commands.
The key object model is:

- **pages/tabs** you navigate and inspect,
- **refs** like `e5` from `snapshot`,
- **artifact files** from `snapshot --filename`, `screenshot`, `console`, and `network`.

Snapshots are not magical live DOM handles. They are point-in-time accessibility-tree dumps.
Saved snapshots are markdown-style outline files in the current `.playwright-cli/` artifact area.

## Bootstrap (run once before browser work)

Use the documented CLI first:

```bash
which playwright-cli || npm install -g @anthropic-ai/playwright-cli@latest
playwright-cli install --browser=chrome
playwright-cli session-stop 2>/dev/null
playwright-cli config --browser=chrome --isolated
```

If you intentionally use named sessions, stop the specific one:

```bash
playwright-cli session-stop my-session 2>/dev/null
```

When all work is done, clean up deliberately:

```bash
playwright-cli session-stop-all
```

## The default workflow: observe → act → snapshot again

Do not trust implicit snapshots from command output. Some commands print one, some do not,
and some site changes are subtle.

Use this control loop instead:

```text
open <url>
snapshot
screenshot --filename=step-1.png
[decide]
click / fill / select / check / press / open
snapshot
screenshot --filename=step-2.png
[repeat]
```

**Rule:** after any meaningful UI change, run `snapshot` before reusing refs.
**Proof rule:** when correctness matters, pair the interaction with browser truth (`eval`) and visual evidence (`screenshot`), not just optimistic command output.

## Refs are disposable

Refs die when page state changes in ways that matter:

- navigation (`open`, `go-back`, `go-forward`, `reload`)
- tab switches (`tab-select`)
- some clicks/selects that re-render UI
- any `run-code` that mutates page state

Treat refs as disposable. If in doubt, `snapshot` again.

## CLI-first principle

Prefer direct CLI commands for:

- navigation: `open`, `go-back`, `go-forward`, `reload`
- observation: `snapshot`, `screenshot`, `pdf`
- interaction: `click`, `fill`, `select`, `check`, `uncheck`, `press`
- tab/session management: `tab-new`, `tab-list`, `tab-select`, `tab-close`, `session-*`
- diagnostics: `console`, `network`

Use `run-code` only when the CLI does not express the step cleanly:

- waits (`waitForSelector`, `waitForResponse`, `waitForURL`)
- popups / downloads / file chooser edge cases
- media emulation, cookies, geolocation
- hidden-input fallback or page-level atomic operations

After `run-code`, assume the page may have changed and re-enter the normal loop:

```bash
snapshot
screenshot --filename=after-run-code.png
```

---

## Essential commands

### Navigation
```bash
open <url>
go-back
go-forward
reload
```

### Observation
```bash
snapshot
snapshot --filename=page-state.md
screenshot --filename=view.png
screenshot --full-page --filename=page.png
screenshot <ref> --filename=element.png
pdf --filename=page.pdf
```

### Interaction
```bash
click <ref>
fill <ref> "text"
fill <ref> "text" --submit
type "text"
select <ref> "value"
check <ref>
uncheck <ref>
hover <ref>
dblclick <ref>
drag <source-ref> <target-ref>
press Enter
keydown Shift
keyup Shift
```

### Uploads
```bash
# 1. trigger a file chooser first by clicking the visible upload control or file input
click <upload-trigger-ref>

# 2. only after the page reports a file-chooser modal state:
upload /absolute/path/to/file
upload /absolute/path/to/file-a /absolute/path/to/file-b
```

### JavaScript / Playwright API
```bash
eval "() => document.title"
eval "() => window.location.href"
eval "(el) => el.value" <ref>
run-code 'async (page) => { ... }'
```

### Tabs and sessions
```bash
tab-new
tab-list
tab-select <index>
tab-close <index>

playwright-cli --session=my-session open https://example.com
playwright-cli session-list
playwright-cli session-stop my-session
playwright-cli session-delete my-session
```

---

## Critical validated gotchas

### 1. `tab-new [url]` is not trustworthy in practice
The installed help advertises `tab-new [url]`, but on this machine's installed CLI the runtime still opened `about:blank` during testing.

Safest pattern:

```bash
tab-new
open https://example.com
```

### 2. Quote URLs in zsh
Unquoted URLs with `?`, `&`, or similar shell-sensitive characters can fail before they ever reach the CLI.

```bash
open "https://www.amazon.com/s?k=fidget+spinner"
```

### 3. Snapshots are not live form state
A snapshot may show the field in the tree, but not the live value you need to trust.

```bash
fill <ref> "hello@example.com"
eval "(el) => el.value" <ref>
```

### 4. `upload` is modal-driven, not ref-driven
Current tested behavior:

- `upload <ref> ...` is wrong for this installed CLI.
- `upload /absolute/path` only works after a file chooser is active.
- paths outside allowed roots are rejected.

### 5. `check` works for radios too
Older lore said to use `click` for radios. On the installed CLI, `check <ref>` worked on a radio input in testing.

Prefer `check` when you want idempotent "selected" behavior.

### 6. Do not trust stale session/profile lore
Current docs/help support:

- `--session=name`
- `session-stop [name]`
- `session-delete [name]`

The older `-s=name`, `--persistent`, and `--profile` guidance in this repo was stale and should not be copied forward.

### 7. The printed page header can be stale across tab operations
In testing, `eval "() => window.location.href"` was more trustworthy than the surrounding command header when tab state got odd.

Use `eval` for URL truth when it matters.

### 8. Console and network return artifact files, not inline diagnosis
The CLI returns log artifacts you must inspect. They can also be empty.

```bash
console error
network
```

Then open the generated files before claiming the page is clean or broken.

### 9. Artifact paths are implementation details
Do not build workflow assumptions around where `.playwright-cli/...` ends up relative to your current repo. Use the path the CLI returns.

### 10. `run-code` is a bridge, not a new default workflow
Use it for the one hard step, then go back to:

```bash
snapshot
screenshot --filename=evidence.png
```

### 11. `select` should use the option value
Inspect the select options first, then pass the option `value`, not the visible label you hope will work.

### 12. Public-site logs are evidence, not automatic blame
Large public sites can emit telemetry, anti-bot, or graphics noise. Capture it, inspect it, and interpret it carefully.

### 13. Commerce/search/filter flows need URL proof and visual proof
For stateful list pages, do not trust motion alone. Pair the interaction with:

```bash
snapshot
eval "() => window.location.href"
screenshot --filename=search-after.png
```

---

## Verification patterns

### Page health check
```bash
open <url>
snapshot
screenshot --filename=initial.png
console error
network
```

### Form verification
```bash
fill <ref> "value"
eval "(el) => el.value" <ref>
click <submit-ref>
snapshot
eval "() => window.location.href"
```

### Upload verification
```bash
click <upload-trigger-ref>
upload /absolute/path/to/file
eval "() => [...document.querySelector('input[type=file]').files].map(f => f.name)"
```

### Search / filter / sort verification
```bash
open "https://www.amazon.com/s?k=fidget+spinner"
snapshot
screenshot --filename=search-before.png
# inspect refs / option values
select <sort-ref> "review-rank"
click <filter-ref>
snapshot
eval "() => window.location.href"
screenshot --filename=search-after.png
```

### Multi-tab verification
```bash
open https://example.com
snapshot

tab-new
open https://example.org
snapshot

tab-select 0
snapshot
eval "() => window.location.href"
```

---

## Sub-agent rules (shared-session work)

If you are a tab tenant inside a shared browser session:

```text
tab-new → open <url> → [work] → tab-close <index>
```

- Never create ad-hoc browser processes outside the shared CLI unless explicitly asked.
- Never use `close` if other agents depend on the same session.
- Prefer explicit `tab-close <index>` even though the command can omit the index.
- Re-run `snapshot` after `tab-select`.
- Re-check your tab index with `tab-list` before closing if other agents may have changed tab order.
- Keep upload test files inside allowed roots and verify file names with `eval` after `upload`.

---

## Reference files

- **[Command reference](references/command-reference.md)** — validated syntax and behavior notes for the installed CLI
- **[Form and data extraction](references/form-and-data.md)** — forms, `eval`, radios, uploads, and extraction patterns
- **[Session and tabs](references/session-and-tabs.md)** — tabs, sessions, cleanup, and stale-lore removals
- **[Visual testing](references/visual-testing.md)** — screenshots, responsive checks, and comparison patterns
- **[Debugging](references/debugging.md)** — console/network artifacts, troubleshooting, tracing, and `run-code`
- **[Async and advanced recipes](references/async-and-advanced.md)** — waits, popups, downloads, and safe re-entry after advanced steps
- **[Orchestrator guide](references/orchestrator-guide.md)** — shared-session coordination for multiple agents
