# Security Reference

> Source: [agent-browser.dev/security](https://agent-browser.dev/security)

## Overview

agent-browser includes security features to protect against credential exposure, prompt injection via untrusted page content, and unauthorized browser actions.

All security features are opt-in. By default, agent-browser imposes no restrictions on navigation, actions, or output. Enable these features as needed for your deployment — existing workflows are unaffected until you explicitly activate a feature.

## Threat Model

These features mitigate the following threats when an LLM-based agent drives a browser:

1. **Credential exposure** — Passwords stored in the auth vault are never included in LLM context. The CLI handles vault operations locally; credentials do not pass through the daemon's IPC channel.
2. **Prompt injection via page content** — Malicious pages can embed text that looks like tool output or system instructions. Content boundary markers (`--content-boundaries`) let the orchestrator distinguish trusted tool output from untrusted page content.
3. **Unauthorized navigation / data exfiltration** — A compromised or manipulated agent could navigate to attacker-controlled domains to exfiltrate data. The domain allowlist (`--allowed-domains`) blocks navigations, sub-resource requests, WebSocket connections, EventSource streams, and `sendBeacon` calls to non-allowed domains.
4. **Unauthorized destructive actions** — Action policy (`--action-policy`) and confirmation gating (`--confirm-actions`) prevent the agent from performing dangerous operations (eval, downloads, uploads) without explicit approval.
5. **Context flooding** — Large page outputs can overwhelm an LLM's context window. Output truncation (`--max-output`) caps the size of page-sourced content.

## Known Limitations

- **WebSocket/EventSource blocking is best-effort.** It works by overriding browser constructors via an init script. If the `eval` action category is allowed, page scripts could theoretically restore the original constructors. Deny `eval` via `--action-policy` for maximum protection.
- **Domain filter timing on remote connections.** When connecting to a pre-existing browser via CDP or a cloud provider, pages may have already loaded content before the domain filter is installed. agent-browser navigates disallowed pages to `about:blank` after the filter is active, but resources loaded before that point are not retroactively blocked.
- **Content boundaries are defense-in-depth.** They rely on the LLM and orchestrator respecting the structural markers. A sufficiently capable adversarial page could attempt to mimic the boundary format, though the per-process CSPRNG nonce makes this impractical to predict.
- **Confirmation timeout.** Pending confirmations auto-deny after 60 seconds. Orchestrators must respond within that window.
- **Non-TTY auto-deny.** When `--confirm-interactive` is set but stdin is not a terminal (e.g., piped input), actions are automatically denied to prevent accidental approval in non-interactive contexts.

## Authentication Vault

Store credentials locally and reference them by name. The LLM never sees passwords.

```bash
# Save credentials (--password-stdin recommended to avoid shell history)
echo "pass" | agent-browser auth save github --url https://github.com/login --username user --password-stdin

# Or pass directly (a warning will be shown)
agent-browser auth save github --url https://github.com/login --username user --password pass

# Login using saved credentials
agent-browser auth login github

# List saved profiles (names and URLs only, no secrets)
agent-browser auth list

# Show profile metadata
agent-browser auth show github

# Delete a profile
agent-browser auth delete github
```

### Custom Selectors

If auto-detection fails, specify custom selectors:

```bash
agent-browser auth save myapp \
  --url https://app.example.com/login \
  --username user --password pass \
  --username-selector "#email" \
  --password-selector "#password" \
  --submit-selector "button.login"
```

### Storage & Encryption

- Profiles stored in `~/.agent-browser/auth/`
- Always encrypted with AES-256-GCM
- If `AGENT_BROWSER_ENCRYPTION_KEY` is not set, a key is auto-generated at `~/.agent-browser/.encryption-key` on first use
- Back up this file or set the environment variable explicitly for portability
- File permissions enforced: Unix (`chmod 600`/`700`), Windows (`icacls` restricted to current user)

## Content Boundary Markers

When `--content-boundaries` is enabled, all page-sourced output is wrapped in structural markers so LLMs can distinguish tool output from untrusted page content:

```
--- AGENT_BROWSER_PAGE_CONTENT nonce=a1b2c3d4 origin=https://example.com ---
[snapshot / text / html / eval output here]
--- END_AGENT_BROWSER_PAGE_CONTENT nonce=a1b2c3d4 ---
```

The nonce is a random value generated per CLI process invocation, making it unpredictable to page content that might attempt to spoof the boundary.

Enable via flag or environment variable:

```bash
agent-browser --content-boundaries snapshot
# or
export AGENT_BROWSER_CONTENT_BOUNDARIES=1
```

**Affected output types:** `snapshot`, `get text`, `get html`, `eval`, `console`.

### JSON Mode

In `--json` mode, boundary metadata is injected as a `_boundary` object containing `nonce` and `origin` fields:

```json
{
  "success": true,
  "data": { "snapshot": "...", "origin": "https://example.com" },
  "_boundary": { "nonce": "a1b2c3d4e5f6...", "origin": "https://example.com" }
}
```

## Domain Allowlist

Restrict which domains the browser can interact with, preventing redirect-based attacks and data exfiltration:

```bash
agent-browser --allowed-domains "example.com,*.example.com,github.com" open https://example.com
# or
export AGENT_BROWSER_ALLOWED_DOMAINS="example.com,*.example.com"
```

- Supports exact match (`github.com`) and wildcard prefix (`*.example.com`, which also matches the bare domain `example.com`)
- Blocks: page navigations + sub-resource requests (scripts, images, fetch, XHR) + WebSocket + EventSource connections
- Non-http(s) sub-resources (data URIs, blobs) are still allowed
- When a request is blocked, the command returns an error

> **CDN note:** The domain filter blocks all sub-resource requests to non-allowed domains. Most websites load assets from CDN domains — include these in your allowlist or pages will break.
>
> ```bash
> --allowed-domains "myapp.com,*.myapp.com,cdn.jsdelivr.net,fonts.googleapis.com,fonts.gstatic.com"
> ```

Config file:

```json
{
  "allowedDomains": ["example.com", "*.example.com", "github.com"]
}
```

## Action Policy

Gate actions using a static JSON policy file. The policy is enforced by the daemon — denied actions fail immediately.

```bash
agent-browser --action-policy ./policy.json open https://example.com
# or
export AGENT_BROWSER_ACTION_POLICY=./policy.json
```

### Example Policies

Permissive with specific denials:

```json
{
  "default": "allow",
  "deny": ["eval", "download", "upload"]
}
```

Restrictive:

```json
{
  "default": "deny",
  "allow": ["navigate", "snapshot", "click", "scroll", "wait", "get"]
}
```

### Action Categories

| Category | Actions |
|----------|---------|
| `navigate` | open, back, forward, reload, tab new |
| `click` | click, dblclick, tap |
| `fill` | fill, type, keyboard type/inserttext, select, check, uncheck |
| `eval` | eval, evalhandle, addscript, addinitscript, addstyle, expose, setcontent |
| `download` | download, waitfordownload |
| `upload` | upload |
| `snapshot` | snapshot, screenshot, pdf, diff |
| `scroll` | scroll, scrollintoview |
| `wait` | wait, waitforurl, waitforloadstate, waitforfunction |
| `get` | get text/html/url/title, count, isvisible, getbyrole, getbytext, getbylabel, etc. |
| `interact` | hover, focus, drag, press, keydown, keyup, mousemove, dispatch |
| `network` | network route/unroute, requests |
| `state` | state save/load, cookies set, storage set |

Auth vault operations (`auth save`, `auth login`, `auth list`, `auth show`, `auth delete`) and other internal/meta operations bypass action policy enforcement since they are trusted local operations. Domain allowlist restrictions still apply to `auth login` navigations.

## Action Confirmation

For actions that require explicit approval, use `--confirm-actions` to specify categories that require confirmation:

```bash
# Orchestrator mode: returns confirmation_required response
agent-browser --confirm-actions eval,download eval "document.title"

# Then approve or deny:
agent-browser confirm c_8f3a1234
agent-browser deny c_8f3a1234
```

For interactive (human-in-the-loop) confirmation:

```bash
agent-browser --confirm-actions eval,download --confirm-interactive eval "document.title"
# Prompts: Allow? [y/N]
```

Pending confirmations auto-deny after 60 seconds.

> **Non-TTY behavior:** When `--confirm-interactive` is set but stdin is not a TTY (e.g., piped input or running inside an automated pipeline), actions are automatically denied to prevent accidental approval in non-interactive contexts.

## Output Length Limits

Prevent context flooding by truncating large page outputs:

```bash
agent-browser --max-output 50000 get text body
# or
export AGENT_BROWSER_MAX_OUTPUT=50000
```

**Affected output types:** `snapshot`, `get text`, `get html`, `eval`, `console`.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `AGENT_BROWSER_CONTENT_BOUNDARIES` | Wrap page output in boundary markers |
| `AGENT_BROWSER_MAX_OUTPUT` | Max characters for page output |
| `AGENT_BROWSER_ALLOWED_DOMAINS` | Comma-separated allowed domain patterns |
| `AGENT_BROWSER_ACTION_POLICY` | Path to action policy JSON file |
| `AGENT_BROWSER_CONFIRM_ACTIONS` | Comma-separated action categories requiring confirmation |
| `AGENT_BROWSER_CONFIRM_INTERACTIVE` | Enable interactive confirmation prompts |
| `AGENT_BROWSER_ENCRYPTION_KEY` | 64-char hex key for AES-256-GCM encryption (auth vault + sessions) |

## Recommended Production Configuration

```json
{
  "contentBoundaries": true,
  "maxOutput": 50000,
  "allowedDomains": ["your-app.com", "*.your-app.com"],
  "actionPolicy": "./policy.json"
}
```
