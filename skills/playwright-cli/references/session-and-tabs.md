# Session and Tab Management

## Table of Contents

- [What this file is for](#what-this-file-is-for)
- [Validated baseline](#validated-baseline)
- [Session lifecycle](#session-lifecycle)
- [Tab management](#tab-management)
- [Shared-session rules for sub-agents](#shared-session-rules-for-sub-agents)
- [Known traps](#known-traps)

---

## What this file is for

This reference is about the installed `playwright-cli` behavior, not older snippets copied from other skills.

Use it when you need to reason about:

- how to bootstrap a session,
- how to use named sessions,
- how tabs behave in practice,
- what is safe in multi-agent shared-browser work,
- and which old session/profile examples should be treated as stale.

---

## Validated baseline

These were confirmed from the installed CLI help and live runs:

- `playwright-cli install --browser=chrome`
- `playwright-cli config --browser=chrome --isolated`
- `playwright-cli --session=name ...`
- `playwright-cli session-stop [name]`
- `playwright-cli session-delete [name]`
- `playwright-cli session-list`
- `tab-new`, `tab-list`, `tab-select <index>`, `tab-close [index]`

Important stale lore removed from this file:

- `-s=mysession`
- `open --persistent`
- `open --profile=...`
- `delete-data`
- defaulting docs to `chromium`

Treat the installed CLI plus live runtime behavior as authoritative over copied historical snippets.

---

## Session lifecycle

### Bootstrap

```bash
which playwright-cli || npm install -g @anthropic-ai/playwright-cli@latest
playwright-cli install --browser=chrome
playwright-cli session-stop 2>/dev/null
playwright-cli config --browser=chrome --isolated
```

Why this is the safer baseline:

- it uses the documented CLI installer instead of mixing in unrelated `npx playwright` install assumptions,
- it matches the currently supported `--browser` values,
- `--isolated` keeps the browser profile in memory and reduces cross-run residue.

### Named sessions

Use named sessions when you intentionally want parallel or durable command scopes:

```bash
playwright-cli --session=research open https://example.com
playwright-cli --session=research snapshot
playwright-cli session-list
playwright-cli session-stop research
playwright-cli session-delete research
```

### Cleanup

| Command | Effect |
|---|---|
| `session-stop` | Stop current session |
| `session-stop <name>` | Stop named session |
| `session-stop-all` | Stop all sessions |
| `session-delete` | Delete current session data |
| `session-delete <name>` | Delete named session data |
| `session-list` | Show all sessions |
| `close` | Close the current page / browser context; risky in shared setups |

---

## Tab management

### Creating tabs

The installed help advertises `tab-new [url]`, but the runtime still opened `about:blank` during testing when a URL was supplied inline.

Safe pattern:

```bash
tab-new
open https://example.com
snapshot
```

Treat `tab-new <url>` as untrusted behavior unless you verify it again in your environment.

### Listing tabs

```bash
tab-list
```

This shows indexes and current tab state.

### Switching tabs

```bash
tab-select 0
snapshot
eval "() => window.location.href"
```

Use that full pattern when correctness matters because:

- refs from the old tab are dead,
- tab-related output can be confusing,
- `eval(() => window.location.href)` is the most trustworthy URL check.

### Closing tabs

```bash
tab-close 1
tab-list
```

Notes:

- help allows omitting the index to close the current tab, but explicit indexes are easier to reason about;
- tab order can shift after close, so re-run `tab-list` before follow-up tab actions.

---

## Shared-session rules for sub-agents

Use one shared session and multiple tabs when several agents need browser access.

### Tenant lifecycle

```text
tab-new → open <url> → [work] → tab-close <index>
```

### Rules

1. You are a tab tenant, not the session owner.
2. Prefer explicit `tab-close <index>` over bare `tab-close`.
3. Re-run `snapshot` after `tab-select`.
4. Re-check tab order with `tab-list` if other agents may have opened or closed tabs.
5. Avoid `close` in shared runs unless you intentionally want to affect the whole current browser context.
6. Treat `tab-new <url>` as untrusted even if help advertises it; use `tab-new` then `open <url>`.

---

## Known traps

### Trap: `tab-new <url>`
Observed behavior on the installed CLI still produced `about:blank`.

### Trap: stale page header after tab changes
In awkward tab states, command output can be less trustworthy than:

```bash
eval "() => window.location.href"
```

### Trap: stale session/profile folklore
Older snippets referencing `-s=...`, `--persistent`, `--profile`, or `delete-data` should not be copied into current docs unless revalidated against a newer CLI version.
