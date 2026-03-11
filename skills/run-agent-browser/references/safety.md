# Safety & Governance

Guidelines for running agent-browser in production and AI agent contexts.

## Risk-Categorized Commands

### Safe (no approval needed)

Navigation and read-only operations:
- `open`, `click`, `dblclick`, `fill`, `type`, `press`, `hover`, `select`, `check`
- `snapshot`, `screenshot`, `pdf`, `get`, `find`, `wait`, `scroll`
- `close`, `session list`, `tab list`

### Sensitive (require explicit approval)

These commands can modify system state, execute arbitrary code, or persist secrets:

| Command | Risk | Reason |
|---------|------|--------|
| `eval` | High | Arbitrary JavaScript execution in page context. Read-only DOM queries (e.g. `document.querySelectorAll('.title').map(...)`) are lower risk but still require approval since they run in the page context and could be affected by malicious page scripts. Scope approval to specific pages and prefer read-only queries over mutations. |
| `download` | Medium | Writes files to disk |
| `set credentials` | High | Stores secrets in browser credential store |
| `cookies set` | Medium | Sets cookies (session hijacking risk) |
| `storage set` | Medium | Writes to localStorage/sessionStorage |
| `network route` / `network mock` | High | Intercepts and modifies network traffic |
| `--allow-file-access` | High | Enables `file://` URL access |
| `--executable-path` | High | Runs arbitrary binary as browser |
| `--cdp` | High | Connects to arbitrary Chrome instance |
| `--args` | Medium | Passes raw flags to Chromium |
| `state save` / `state load` | Medium | Persists/loads auth tokens and session data |

### Escalation Policy

For AI agent workflows:

1. **Default to read-only.** Use `snapshot`, `get`, `screenshot` before attempting mutations.
2. **Require human approval** before using any sensitive command. Record the reason, scope (which URLs), and action being approved.
3. **Scope approvals narrowly.** "Approve `eval` on `app.example.com/api`" — not "approve all eval."
4. **Log sensitive operations.** Capture screenshots before and after destructive actions.

## Safe Mode Checklist

Before running automated browser sessions in production:

1. ✅ Set `AGENT_BROWSER_ALLOWED_DOMAINS` to restrict navigation scope
2. ✅ Disable `eval` and file access unless explicitly approved
3. ✅ Use ephemeral sessions — avoid persistent state by default
4. ✅ Enable content boundaries: `export AGENT_BROWSER_CONTENT_BOUNDARIES=1`
5. ✅ Set output limits: `export AGENT_BROWSER_MAX_OUTPUT=50000`
6. ✅ Apply action policy file to gate destructive operations
7. ✅ Run as non-root user
8. ✅ Pin CLI version for reproducibility

## Action Policy File

Restrict which commands agents can execute:

```json
{
  "default": "deny",
  "allow": [
    "open", "snapshot", "screenshot",
    "click", "dblclick", "fill", "type", "press",
    "hover", "select", "check", "scroll",
    "wait", "get", "find",
    "close", "tab list", "tab switch"
  ],
  "deny": [
    "eval", "download",
    "network route", "network mock",
    "state save", "state load",
    "set credentials", "cookies set", "storage set"
  ]
}
```

Apply it:

```bash
export AGENT_BROWSER_ACTION_POLICY=./policy.json
agent-browser open https://example.com
```

## Domain Allowlist

```bash
# Restrict to specific domains (comma-separated, supports wildcards)
export AGENT_BROWSER_ALLOWED_DOMAINS="app.example.com,*.example.com,cdn.example.com"

# Navigation to non-allowed domains will be blocked
agent-browser open https://app.example.com      # ✅ Allowed
agent-browser open https://malicious.example.org  # ❌ Blocked
```

## Supply-Chain Hygiene

- **Pin CLI version:** `npm install -g agent-browser@0.16.2`
- **Install in isolated environments:** containers, VMs, or dedicated CI runners
- **Avoid elevated privileges:** never run with `sudo`
- **Review upgrades:** check changelogs before updating
- **Keep state ephemeral:** delete session data after use unless persistence is explicitly needed
- **Audit extensions:** only load trusted browser extensions
