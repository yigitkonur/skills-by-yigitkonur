# Session and Tab Management

## Table of Contents

- [Session Lifecycle](#session-lifecycle)
  - [Bootstrap](#bootstrap-run-once-before-any-browser-work)
  - [Session Cleanup](#session-cleanup)
  - [Why One Session, Many Tabs](#why-one-session-many-tabs)
  - [Config](#config)
- [Tab Management](#tab-management)
  - [Creating Tabs](#creating-tabs)
  - [Listing Tabs](#listing-tabs)
  - [Switching Tabs](#switching-tabs)
  - [Closing Tabs](#closing-tabs)
  - [close vs tab-close](#close-vs-tab-close-critical-distinction)
- [Sub-Agent Tab Lifecycle](#sub-agent-tab-lifecycle)
  - [The Standard Lifecycle](#the-standard-lifecycle)
  - [Rules for Sub-Agents](#rules-for-sub-agents)
  - [Multi-Agent Coordination](#multi-agent-coordination)
  - [Tab Coordination Patterns](#tab-coordination-patterns)
- [Named Sessions](#named-sessions)
- [Persistent Profiles](#persistent-profiles)

---

## Session Lifecycle

### Bootstrap (run once before any browser work)

```bash
which playwright-cli || npm install -g @anthropic-ai/playwright-cli@latest
PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=true npx playwright install chromium
playwright-cli session-stop 2>/dev/null    # kill stale sessions
playwright-cli config --browser=chromium
```

### Session Cleanup

| Command            | Effect                                              |
|--------------------|-----------------------------------------------------|
| `session-stop`     | Stops the current session                           |
| `session-stop-all` | Stops ALL sessions (use after all work is done)     |
| `close`            | Closes the entire browser (DANGEROUS in multi-agent setups) |
| `session-list`     | Shows all running sessions                          |
| `session-delete`   | Deletes session data                                |
| `session-restart`  | Restarts the session                                |

### Why One Session, Many Tabs

- 5 agents x 5 sessions = CPU death
- 1 session x 5 tabs = negligible overhead
- Tabs share cookies and localStorage -- same as real users
- If session dies mid-run, re-run bootstrap, agents create new tabs

### Config

| Command                      | Description                |
|------------------------------|----------------------------|
| `config --browser=chromium`  | Default, recommended       |
| `config --browser=firefox`   | Firefox                    |
| `config --browser=webkit`    | WebKit (Safari engine)     |
| `config --browser=msedge`    | Microsoft Edge             |
| `config --browser=chrome`    | Google Chrome              |

Configuration file location: `~/.playwright-cli/config.json`

---

## Tab Management

### Creating Tabs

- `tab-new` -- opens `about:blank` (NOT a URL!)
- CRITICAL: Always follow with `open <url>` -- two-step pattern
- The `about:blank` trap is the #1 tab mistake

```bash
# CORRECT: two-step tab creation
tab-new
open https://example.com

# WRONG: tab-new does NOT accept a URL argument
tab-new https://example.com   # This opens about:blank, ignores the URL
```

### Listing Tabs

- `tab-list` -- shows all tabs with indexes and URLs
- Tab indexes are 0-based
- The active tab is marked

### Switching Tabs

- `tab-select <index>` -- switches to tab by index
- All refs from previous tab become stale immediately
- You MUST run `snapshot` after every `tab-select` — this is not optional
- The "Page URL" header may lie in multi-tab scenarios
- Use `eval "() => window.location.href"` for truth

```bash
# Correct tab switch sequence:
tab-select 0
snapshot                    # get fresh refs for the switched-to tab
eval "() => window.location.href"   # verify you're on the right page
```

### Closing Tabs

- `tab-close <index>` -- closes a specific tab
- CRITICAL: Tab indexes shift after close!
- After closing tab 1 of [0,1,2], what was tab 2 becomes tab 1
- You MUST run `tab-list` after every `tab-close` — this is not optional
- Close tabs from highest index to lowest to avoid shifting issues

```bash
# Correct tab close sequence:
tab-close 2
tab-list                    # verify remaining tabs and their new indexes
# Now safe to tab-select or tab-close again
```

### close vs tab-close (critical distinction)

| Command              | Scope                                    | Safe for sub-agents? |
|----------------------|------------------------------------------|----------------------|
| `close`              | Kills the ENTIRE browser for ALL agents  | NO                   |
| `tab-close <index>`  | Closes only ONE tab                      | YES                  |

- Sub-agents must NEVER use `close`
- Sub-agents must ONLY use `tab-close <their-index>`

---

## Sub-Agent Tab Lifecycle

### The Standard Lifecycle

```
tab-new → open <url> → [work] → tab-close <your-index>
```

### Rules for Sub-Agents

1. Never create sessions -- you are a tenant
2. Never use `close` -- it kills the shared session
3. Always `tab-close <index>` when done
4. Track your own tab index via `tab-list`
5. Your tab shares cookies/localStorage with other tabs

### Multi-Agent Coordination

- Each agent gets their own tab
- Agents share cookies and localStorage (same as real users)
- Tab indexes can shift if another agent closes a tab
- Always verify your tab index with `tab-list` before closing

### Tab Coordination Patterns

#### Close tabs highest-to-lowest

```bash
# After work is done with tabs 1, 2, 3:
tab-close 3
tab-close 2
tab-close 1
# This avoids index shifting problems
```

#### Peek and return

```bash
# Save current position
tab-list  # note current tab index
tab-new
open <reference-url>
snapshot
# ... look up info ...
tab-close <new-tab-index>
tab-select <original-index>
snapshot
```

#### Recover from about:blank trap

```bash
# If you ran tab-new <url> and got about:blank:
eval "() => window.location.href"
# If it returns "about:blank", just navigate:
open https://intended-url.com
snapshot
```

---

## Named Sessions

```bash
# Create named session with persistent profile
playwright-cli -s=mysession open example.com --persistent
playwright-cli -s=mysession click e6
playwright-cli -s=mysession close
playwright-cli -s=mysession delete-data
```

---

## Persistent Profiles

```bash
playwright-cli open --persistent                    # default profile location
playwright-cli open --profile=/path/to/profile      # custom profile directory
```
