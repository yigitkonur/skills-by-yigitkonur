# Tabs, Sessions, and Multi-Agent Coordination

How to manage tabs, use named sessions, handle popups, and coordinate
multiple agents sharing a single browser in `playwright-cli`.

---

## Table of Contents

- [Tab commands](#tab-commands)
- [Tab workflows](#tab-workflows)
- [Session lifecycle](#session-lifecycle)
- [Named sessions](#named-sessions)
- [Session cleanup](#session-cleanup)
- [Popup and new-window handling](#popup-and-new-window-handling)
- [Multi-agent shared sessions](#multi-agent-shared-sessions)
- [Orchestrator guide](#orchestrator-guide)
- [Known traps](#known-traps)

All examples in this file are shell commands. Run them as `playwright-cli <command> ...`, not inside an interactive prompt.

---

## Tab commands

### tab-new

```bash
tab-new [url]
```

Opens a new tab. The `[url]` argument is documented but **unreliable**.

> **Steering experience:** In repeated real runs, `tab-new <url>` opened `about:blank` instead of the requested URL. Treat that as the common behavior. Always use the two-step pattern below. Never pass a URL to `tab-new`.

**Safe pattern (always use this):**

```bash
tab-new
open https://example.com
snapshot
```

### tab-list

```bash
tab-list
```

Lists all open tabs with their indexes and current URLs.

### tab-select

```bash
tab-select <index>
```

Switches to the tab at the given index. After switching:

```bash
tab-select 0
snapshot
eval "() => window.location.href"
```

Always re-snapshot after `tab-select` because refs from the previous tab are dead.

### tab-close

```bash
tab-close [index]
```

Closes the tab at the given index, or the current tab if omitted.

**Prefer explicit indexes** — especially in shared or multi-step work:

```bash
tab-close 2
tab-list
```

Tab order shifts after closing. Re-run `tab-list` before further tab actions.

---

## Tab workflows

### Open a page in a new tab

```bash
tab-new
open https://docs.example.com
snapshot
screenshot --filename=docs-tab.png
```

### Compare two pages side by side

```bash
open https://app.example.com/v1/feature
snapshot
screenshot --filename=v1.png

tab-new
open https://app.example.com/v2/feature
snapshot
screenshot --filename=v2.png

tab-select 0
snapshot
# Compare screenshots or snapshot content
```

### Multi-tab data collection

```bash
# Tab 0: main page
open https://example.com
snapshot

# Tab 1: docs
tab-new
open https://docs.example.com
snapshot
eval "() => document.title"

# Tab 2: API
tab-new
open https://api.example.com/health
eval "() => document.body.textContent"

# Return to main
tab-select 0
snapshot
```

### Close a tab and continue

```bash
tab-close 2
tab-list
tab-select 0
snapshot
```

---

## Session lifecycle

### Bootstrap (run once before browser work)

> **Steering experience:** Always run `playwright-cli install --browser=chrome` even if the CLI is installed. It is a no-op when the binary exists but prevents cryptic errors when it is missing. If you are about to reconfigure the current scratch session, stop it first with `session-stop`; otherwise leave an already-useful session alone. For isolated cleanup, use `session-stop` for the current unnamed session or `session-stop <name>` for a named one.

```bash
which playwright-cli || npm install -g @anthropic-ai/playwright-cli@latest
playwright-cli install --browser=chrome    # always run — ensures binary exists
playwright-cli session-stop 2>/dev/null    # optional: only before reconfiguring the current scratch session
playwright-cli config --browser=chrome --isolated
playwright-cli session-list
```

`--isolated` keeps the browser profile in memory, reducing cross-run residue.

### Session commands

| Command | Effect |
|---------|--------|
| `session-list` | List all active sessions |
| `session-stop` | Stop current session |
| `session-stop <name>` | Stop named session |
| `session-stop-all` | Stop all sessions |
| `session-restart` | Restart current session |
| `session-restart <name>` | Restart named session |
| `session-delete` | Delete current session data |
| `session-delete <name>` | Delete named session data |

`session-stop-all` and `session-delete` are destructive. Use them only for scratch sessions you created and only when their data or browser lifetime should really be discarded.

### End of work cleanup

```bash
playwright-cli session-stop           # current unnamed scratch session
playwright-cli session-stop research  # named scratch session
```

---

## Named sessions

Use named sessions when you need parallel or durable command scopes.

### Create and use a named session

```bash
playwright-cli --session=research open https://example.com
playwright-cli --session=research snapshot
playwright-cli --session=research screenshot --filename=research.png
```

### List and manage

```bash
playwright-cli session-list
playwright-cli session-stop research
playwright-cli session-delete research   # only if you also want to discard saved session data
```

### When to use named sessions

| Scenario | Use named session? |
|----------|-------------------|
| Quick single-page task | No — default session is fine |
| Parallel browser work | Yes — isolate each workflow |
| Long-running agent task | Yes — named sessions are easier to manage |
| Multi-agent coordination | Yes — one session, multiple tabs |

---

## Session cleanup

### Stop specific session

> **Steering experience:** When using isolated sessions (`config --isolated`), you MUST stop the one you created when done. Use `session-stop` for the current unnamed isolated session, or `session-stop <name>` for a named one. Forgetting cleanup leaks browser processes that consume memory until manually killed.

```bash
playwright-cli session-stop
playwright-cli session-stop my-session
```

### Stop all sessions

Use this only when you intentionally own every active session and want a full teardown.

```bash
playwright-cli session-stop-all
```

### Delete session data

Delete only scratch sessions you created and no longer need.

```bash
playwright-cli session-delete my-session
```

### Emergency cleanup

If sessions are stuck:

```bash
playwright-cli session-stop-all
```

---

## Popup and new-window handling

Popups (like OAuth windows) are best handled atomically inside `run-code`.

### Capture popup info

```bash
run-code 'async (page) => {
  const [popup] = await Promise.all([
    page.waitForEvent("popup"),
    page.locator("a[target=_blank]").first().click()
  ])
  await popup.waitForLoadState()
  return { title: await popup.title(), url: popup.url() }
}'
```

### OAuth-style popup

```bash
run-code 'async (page) => {
  const [popup] = await Promise.all([
    page.waitForEvent("popup"),
    page.locator("button.oauth-google").click()
  ])
  await popup.waitForLoadState()
  return { popupTitle: await popup.title(), popupUrl: popup.url() }
}'
```

### After popup changes main page state

If the popup affects the main page (e.g., OAuth callback), re-enter the CLI loop:

```bash
snapshot
eval "() => window.location.href"
screenshot --filename=after-popup.png
```

### Dialog handling

> **Steering experience:** Dialog commands (`dialog-accept`, `dialog-dismiss`) are normal shell invocations: `playwright-cli dialog-accept` or `playwright-cli dialog-dismiss`. They must be issued while the dialog is active — if the dialog auto-dismissed, these commands will error.

For JavaScript `alert()`, `confirm()`, `prompt()` dialogs:

```bash
dialog-accept
dialog-dismiss
dialog-accept "user input text"
```

---

## Multi-agent shared sessions

When multiple agents share one browser session, each agent operates as a
**tab tenant**, not a session owner.

### Tenant lifecycle

```text
tab-new → open <url> → [work] → tab-close <index>
```

### Rules for tab tenants

1. **Never close the browser** — only close your own tab.
2. **Use explicit `tab-close <index>`** — not bare `tab-close`.
3. **Re-snapshot after `tab-select`** — refs from other tabs are dead.
4. **Re-check tab order with `tab-list`** before closing if other agents
   may have changed tab order.
5. **Avoid `close`** in shared runs — it affects the entire browser context.
6. **Use `tab-new` then `open <url>`** — not `tab-new <url>`.
7. **Never use `session-stop-all` in shared runs** — it tears down other agents' work.

### Agent brief template

Paste this into any sub-agent brief that will touch the browser:

```text
PLAYWRIGHT OPERATING RULES

You are a tab tenant, not the session owner.
Use: tab-new → open <url> → [work] → tab-close <index>

Do not trust old refs. After any UI change, run snapshot.
Do not trust tab-new <url>. Use tab-new then open <url>.
Use eval for truth checks (URLs, values, checked state).
Uploads are modal-driven — trigger the file chooser first.
Console and network return artifact files — inspect them.
Do not use close or session-stop-all unless you own the whole browser.
```

---

## Orchestrator guide

### Verification levels

| Level | Pattern | Use for |
|-------|---------|---------|
| 1 — Existence | open → snapshot → screenshot | Static copy, UI presence |
| 2 — Behavior | open → interact → verify with eval → screenshot | Forms, filters, buttons |
| 3 — Visual matrix | 4 screenshots: desktop/mobile × light/dark | Design and layout changes |
| 4 — Regression | Level 3 + flow checks + console/network + before/after | Business-critical paths |

### Bootstrap for orchestrator

```bash
which playwright-cli || npm install -g @anthropic-ai/playwright-cli@latest
playwright-cli install --browser=chrome
playwright-cli session-stop 2>/dev/null   # optional: only before reconfiguring the current scratch session
playwright-cli config --browser=chrome --isolated
playwright-cli session-list
```

### After all agents complete

Stop only the scratch session or sessions the orchestrator created. Reserve `session-stop-all` for cases where the orchestrator intentionally owns the whole active browser pool.

```bash
playwright-cli session-stop
playwright-cli session-stop orchestrator
```

---

## Known traps

### Trap: tab-new with URL

`tab-new <url>` may open `about:blank` instead. Always use:

```bash
tab-new
open <url>
```

### Trap: stale page header after tab switch

Command output headers can show wrong URLs after tab operations. Use:

```bash
eval "() => window.location.href"
```

### Trap: stale session folklore

Old examples using `-s=name`, `--persistent`, `--profile`, or `delete-data`
are stale for the current CLI. Use `--session=name` and `session-*` commands.

### Trap: tab order changes after close

Closing a tab shifts indexes of tabs after it. Always re-run `tab-list`
before acting on other tabs.

### Trap: close vs tab-close

`close` closes the entire browser context. `tab-close` closes one tab.
In shared sessions, always use `tab-close`.
