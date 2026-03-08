# Orchestrator Guide: Multi-Agent Browser Coordination

## Table of Contents

- [What this guide assumes](#what-this-guide-assumes)
- [Bootstrap](#bootstrap)
- [What every sub-agent brief should include](#what-every-sub-agent-brief-should-include)
- [Verification depth](#verification-depth)
- [Shared-session coordination](#shared-session-coordination)
- [High-signal patterns](#high-signal-patterns)

## What this guide assumes

This guide assumes you are using the installed `playwright-cli`, not generic Playwright examples.
It is designed for shared-session work where one orchestrator coordinates multiple agents.

Important corrections carried into this file:
- default examples use `chrome`, not `chromium`;
- named sessions use `--session=name`, not `-s=name`;
- uploads are modal-driven, not ref-driven;
- `tab-new <url>` is not trusted even though help advertises it.

## Bootstrap

Run once before dispatching browser work:

```bash
which playwright-cli || npm install -g @anthropic-ai/playwright-cli@latest
playwright-cli install --browser=chrome
playwright-cli session-stop 2>/dev/null
playwright-cli config --browser=chrome --isolated
```

After all agents complete:

```bash
playwright-cli session-stop-all
```

## What every sub-agent brief should include

Paste or adapt this block for any agent that will touch the browser:

> **PLAYWRIGHT OPERATING RULES**
>
> **You are a tab tenant, not the session owner.**
> Use:
> ```text
> tab-new → open <url> → [your work] → tab-close <index>
> ```
>
> **Do not trust old refs.**
> After any meaningful UI change, run `snapshot` before using refs again.
>
> **Do not trust `tab-new <url>`.**
> Use `tab-new` then `open <url>`.
>
> **Use `eval` for truth checks.**
> Especially for `window.location.href`, field values, checked state, and uploaded file names.
> For stateful flows, do not rely on command headers or visual motion alone.
>
> **Uploads are modal-driven.**
> Trigger the file chooser first, then run:
> ```bash
> upload /absolute/path/to/file
> ```
>
> **If command output looks suspicious, re-check with:**
> ```bash
> snapshot
> eval "() => window.location.href"
> ```
>
> **Console and network return artifact files.**
> You must open the returned file path.
> The returned file may also be empty, so inspect before claiming a clean or broken state.

## Verification depth

### Level 1 — existence check

```text
open → snapshot → screenshot → confirm target exists
```

Use for static copy or low-risk UI presence checks.

### Level 2 — behavior check

```text
open → snapshot → interact → snapshot → verify with eval → screenshot
```

Use for form interactions, simple filters, and button behavior.
For search/filter/sort work, prefer URL proof plus a screenshot rather than only one of them.

### Level 3 — visual matrix

```text
desktop light
desktop dark
mobile light
mobile dark
```

Use for design or layout changes.

### Level 4 — regression flow

```text
Level 3 matrix
+ connected user flow checks
+ console/network artifacts
+ before/after screenshots
```

Use for high-risk or business-critical paths.

## Shared-session coordination

### Session model

One browser session, many tabs.
This is usually cheaper and closer to real user state than spinning up many isolated browsers.

### Tab model

Each agent should:

```text
tab-new
open <url>
snapshot
[work]
tab-close <index>
```

### Safety rules

- prefer explicit `tab-close <index>`;
- re-run `tab-list` if multiple agents are opening/closing tabs;
- re-run `snapshot` after `tab-select`;
- use `eval "() => window.location.href"` when tab metadata is ambiguous.

## High-signal patterns

### Page health check

```bash
open <url>
snapshot
screenshot --filename=initial.png
console error
network
```

### Search / filter flow

```bash
open "https://www.amazon.com/s?k=fidget+spinner"
snapshot
screenshot --filename=search-before.png
# inspect sort/filter refs or option values
click <filter-ref>
snapshot
eval "() => window.location.href"
screenshot --filename=search-after.png
```

### Upload flow

```bash
snapshot
click <upload-trigger-ref>
upload /absolute/path/to/file
eval "() => [...document.querySelector('input[type=file]').files].map(f => f.name)"
```

### Async or complex edge case

```bash
run-code 'async (page) => {
  await page.waitForSelector("[data-ready=true]")
  return "ready"
}'
snapshot
screenshot --filename=after-wait.png
```
