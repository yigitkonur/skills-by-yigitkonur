# Safety, sensitive commands, and troubleshooting

What is safe to run without approval, what needs approval and why, and what to do when something breaks.

**Related:** `commands.md` for flag reference, `sessions-and-refs.md` for session/profile/state lifecycle, `SKILL.md` for operating transcripts.

---

## Part 1 — Risk-categorized commands

### Safe — no explicit approval needed

Navigation and read-only operations:

- `open`, `back`, `forward`, `reload`, `close`
- `click`, `dblclick`, `fill`, `type`, `press`, `hover`, `focus`, `select`, `check`, `uncheck`, `scroll`, `scrollintoview`, `drag`, `upload`
- `snapshot`, `screenshot`, `pdf`
- `get *`, `find *`, `is *`
- `wait` (any form)
- `tab`, `session`, `frame`, `dialog`
- `cookies` (read only — `cookies` and `cookies get`)

### Sensitive — require explicit approval, narrowly scoped

These commands can mutate system state, execute arbitrary code, persist secrets, or escape sandbox boundaries.

| Command | Risk | Reason |
|---|---|---|
| `eval` (any) | High | Arbitrary JavaScript execution in the page context. Even read-only DOM queries run in the page and can be affected by malicious page scripts. Prefer built-ins (`get text`, `get attr`, `get count`) when they suffice. Scope approval to specific URLs. |
| `download` | Medium | Writes a file to disk. |
| `set credentials` | High | Stores secrets in the browser credential store. |
| `cookies set` | Medium | Cookie injection / session hijacking risk. |
| `storage local set` / `storage session set` | Medium | Writes to local/session storage. |
| `network route` | High | Intercepts and modifies network traffic. |
| `--allow-file-access` | High | Enables `file://` URL access. |
| `--executable-path` | High | Runs an arbitrary binary as the browser. |
| `--cdp PORT` / `--auto-connect` | High | Connects to an arbitrary running Chrome. |
| `--args` | Medium | Passes raw Chromium flags. |
| `state save` / `state load` / `--state PATH` | Medium | Persists or loads auth tokens. |
| `--profile PATH` | Medium | Touches a long-lived Chrome user data directory. |
| `cookies clear` / `storage local clear` | Medium | Destructive. |

### Escalation policy for agent runs

1. **Default to read-only.** `snapshot -i`, `get *`, `screenshot` before any mutation.
2. **Require explicit human approval** before any sensitive command. Record reason, scope (which URLs), action being approved.
3. **Scope narrowly.** "Approve `eval` on `app.example.com/products`" — not "approve all eval".
4. **Log sensitive operations.** Take a screenshot before and after destructive actions.

### `eval` is not monolithic

The blanket "High" label hides real variation:

| Usage | Real risk | Example |
|---|---|---|
| Read-only DOM query | low | `document.querySelectorAll('.title')` |
| Read-only property | low | `document.title`, `window.location.href` |
| DOM mutation | medium | `element.remove()` |
| Navigation trigger | high | `window.location = ...`, `form.submit()` |
| External API call | high | `fetch('https://...')` |
| Credential access | high | `document.cookie`, `localStorage` |

Prefer built-ins over `eval`:

```bash
agent-browser get text "h1"
agent-browser get title
agent-browser get url
agent-browser get value @e1
agent-browser get attr @e1 href
agent-browser get count ".items"
```

Use `eval` only when the built-ins cannot do it (multi-element extraction, derived computation). Request narrowly-scoped approval.

---

## Part 2 — Safe-mode checklist for production / agent contexts

1. Set `AGENT_BROWSER_ALLOWED_DOMAINS` to restrict navigation scope (comma-separated; wildcards allowed).
2. Disable `eval` and file access unless explicitly approved.
3. Use ephemeral sessions by default — avoid persistent state.
4. Enable output boundaries: `export AGENT_BROWSER_CONTENT_BOUNDARIES=1`.
5. Cap output: `export AGENT_BROWSER_MAX_OUTPUT=50000`.
6. Apply an action policy file to gate destructive operations.
7. Run as a non-root user.
8. Pin the CLI version (`npm install -g agent-browser@0.31.1`).
9. Set `AGENT_BROWSER_ENCRYPTION_KEY` for state file encryption.
10. Set `AGENT_BROWSER_STATE_EXPIRE_DAYS` for auto-expiry.

### Action policy file

```json
{
  "default": "deny",
  "allow": [
    "open", "snapshot", "screenshot", "pdf",
    "click", "dblclick", "fill", "type", "press",
    "hover", "focus", "select", "check", "uncheck",
    "scroll", "scrollintoview",
    "wait", "get", "find", "is",
    "close", "tab", "session", "frame", "dialog",
    "back", "forward", "reload"
  ],
  "deny": [
    "eval", "download",
    "network route",
    "state save", "state load",
    "set credentials",
    "cookies set", "cookies clear",
    "storage local set", "storage session set",
    "storage local clear", "storage session clear"
  ]
}
```

Apply:

```bash
export AGENT_BROWSER_ACTION_POLICY=./policy.json
agent-browser open https://example.com
```

### Domain allowlist

```bash
export AGENT_BROWSER_ALLOWED_DOMAINS="app.example.com,*.example.com,cdn.example.com"
agent-browser open https://app.example.com         # allowed
agent-browser open https://malicious.example.org   # blocked
```

Be specific. Avoid wildcards that could include untrusted subdomains. Note: `--allowed-domains` blocking of WebSocket / EventSource connections is best-effort — pair it with an `eval`-denying `--action-policy` for stronger isolation.

### Confirmation gating

```bash
export AGENT_BROWSER_CONFIRM_ACTIONS=1     # or --confirm-actions
agent-browser click @e3                    # state-changing actions wait for approval
```

Pending confirmations auto-deny after ~60 seconds. `--confirm-interactive` requires a TTY and auto-denies when none is present (so it fails safe in CI). Approve/reject a pending action with `agent-browser confirm <id>` / `agent-browser deny <id>`.

### Encryption key

Set `AGENT_BROWSER_ENCRYPTION_KEY` (64-char hex, AES-256-GCM) to encrypt the auth vault + saved sessions. If unset, a key is auto-generated at `~/.agent-browser/.encryption-key` — back that file up, or saved state becomes unreadable on another machine.

### Supply-chain hygiene

- Pin the CLI: `npm install -g agent-browser@0.31.1`.
- Install in isolated environments — containers, VMs, dedicated CI runners.
- Never run with `sudo`.
- Review the changelog before updating.
- Delete session data after use unless persistence is explicitly needed.
- Only load trusted browser extensions.
- Credential plugins run as unsandboxed local executables — install them only from trusted maintainers.

---

## Part 3 — Troubleshooting

### CLI runs but no browser opens

Chromium is not installed.

```bash
agent-browser install
```

On Linux, system libraries are also required:

```bash
agent-browser install --with-deps
```

### Daemon not responding / stale session / `EADDRINUSE`

```bash
agent-browser close                      # try this first
agent-browser close --all                # close every session
```

If `close` fails:

```bash
# Confirm there is no live agent-browser process you care about
ps aux | grep '[a]gent-browser'

# Inspect socket/PID files
ls -la ~/.agent-browser

# Remove only stale files for the affected session
rm -f ~/.agent-browser/default.pid ~/.agent-browser/default.sock
rm -f ~/.agent-browser/daemon.pid  ~/.agent-browser/daemon.sock
```

Use the targeted removal first. Only fall back to `rm -f ~/.agent-browser/*.pid ~/.agent-browser/*.sock` when you have confirmed no live state worth preserving.

### Native binary not available

Current agent-browser is native-only (the old Node.js/Playwright daemon was removed), so there is no runtime fallback. If the binary is missing or stale, run `agent-browser doctor --fix`, then `agent-browser upgrade` (auto-detects npm / brew / cargo), or reinstall. Verify with `agent-browser --version`.

| Platform | Native binary |
|---|---|
| macOS ARM64 / x64 | yes |
| Linux ARM64 / x64 | yes |
| Windows x64 | yes |

### "Ref not found" — page changed since last snapshot

```bash
agent-browser snapshot -i        # always re-snapshot first
# then retry with the fresh ref
```

Triggers that invalidate refs: page navigation, form submission, SPA route change, tab switch, modal open/close, dynamic content load.

### Snapshot returns too many / too few elements

```bash
agent-browser snapshot -i              # interactive only (default)
agent-browser snapshot -i -C           # include cursor-interactive divs (onclick / cursor:pointer)
agent-browser snapshot -i -s "main"    # scope to a stable container
agent-browser snapshot -i -s "#main-content"
agent-browser snapshot                 # full tree (verbose; rarely needed)
```

### Strict-mode violation on `get text` / `get value` / `is visible`

Selector matched multiple elements. Either narrow the selector to match exactly one, or switch to `eval --stdin` (see `SKILL.md` Scenario C).

```bash
agent-browser get count ".item"      # verify how many matched
agent-browser get text ".item:first-child"
# or
agent-browser eval --stdin <<'EVALEOF'
Array.from(document.querySelectorAll('.item')).map(el => el.textContent.trim());
EVALEOF
```

### Timeout errors on slow pages

```bash
# Per-process default
export AGENT_BROWSER_DEFAULT_TIMEOUT=60000   # ms

# Or explicit waits in the flow
agent-browser open https://slow.example.com
agent-browser wait --load networkidle
agent-browser snapshot -i
```

If `networkidle` never resolves (analytics keep polling), fall back to `wait 2000` plus a content-based check like `wait --text "Welcome"` or `wait --fn "window.appReady === true"`.

### SSL / certificate errors

```bash
agent-browser --ignore-https-errors open https://self-signed.example.com
```

For testing only. Do not use in production.

### `diff snapshot` fails

`agent-browser diff` alone is not valid. Always pass a subcommand:

```bash
agent-browser diff snapshot
agent-browser diff snapshot --baseline ./snap.txt
agent-browser diff snapshot -s "#main"
agent-browser diff screenshot --baseline ./screen.png
agent-browser diff url https://a.example.com https://b.example.com
```

### Trace recording for hard-to-reproduce failures

```bash
agent-browser trace start
# ... reproduce the issue ...
agent-browser trace stop ./trace.zip
npx playwright show-trace ./trace.zip
```

Limitations: Chromium-only, ~5M event cap, 30 s timeout on stop.

### Browser extensions not loading

```bash
agent-browser --extension /path/to/ext1 --extension /path/to/ext2 open https://example.com
# or
export AGENT_BROWSER_EXTENSIONS="/path/to/ext1,/path/to/ext2"
```

Work in both headed and headless. Not supported under `--engine lightpanda`.

### Serverless / CI environments

```bash
# Lightweight Chromium for serverless (e.g. AWS Lambda via @sparticuz/chromium)
agent-browser --executable-path "$(node -e "console.log(require('@sparticuz/chromium').executablePath())")" open https://example.com

# System Chrome in CI
agent-browser --executable-path /usr/bin/google-chrome open https://example.com
```

### Debug logging

```bash
agent-browser --debug open https://example.com
# or
export AGENT_BROWSER_DEBUG=1
agent-browser open https://example.com
```

Debug output goes to stderr — combine with `--json` for machine-parseable stdout + human-readable debug on stderr.

### Sensitive-operations checklist

Before any of these, stop and verify scope:

- `eval` that mutates DOM, navigates, fetches, or reads cookies/localStorage.
- `download`, `state save`, `state load`, `cookies set`, `storage local set`.
- `network route` (mocking, blocking, modifying traffic).
- `--allow-file-access`, `--executable-path`, `--cdp`, `--args`.
- Any `--profile PATH` against a path that already contains real auth.

For each: ensure the user has authorized this specific action on this specific scope. Record what you did in the output contract.

### Common environment variables (subset)

| Variable | Purpose | Default |
|---|---|---|
| `AGENT_BROWSER_DEFAULT_TIMEOUT` | Default action timeout (ms) | 25000 |
| `AGENT_BROWSER_ALLOWED_DOMAINS` | Comma-separated allowlist | — |
| `AGENT_BROWSER_CONTENT_BOUNDARIES` | Wrap output in LLM-safe markers (0/1) | 0 |
| `AGENT_BROWSER_MAX_OUTPUT` | Truncate page output (chars) | 50000 |
| `AGENT_BROWSER_HEADED` | Show browser UI (0/1) | 0 |
| `AGENT_BROWSER_ACTION_POLICY` | Path to action policy JSON | — |
| `AGENT_BROWSER_CONFIRM_ACTIONS` | Action categories requiring confirmation | — |
| `AGENT_BROWSER_ENCRYPTION_KEY` | 64-char hex key for at-rest encryption | — |
| `AGENT_BROWSER_STATE_EXPIRE_DAYS` | Auto-delete states older than N days | 30 |
| `AGENT_BROWSER_DEBUG` | Debug logging (0/1) | 0 |
| `AGENT_BROWSER_NO_AUTO_DIALOG` | Disable auto-dismissal of alert/beforeunload | 0 |

See `commands.md` for the full env-var surface.
