# Authentication Patterns

> Sources: [agent-browser.dev/security](https://agent-browser.dev/security), [agent-browser.dev/sessions](https://agent-browser.dev/sessions)

## Contents

- [Auth Vault](#auth-vault)
- [Header-Based Auth](#header-based-auth)
- [State Persistence](#state-persistence)
- [HTTP Basic Auth](#http-basic-auth)
- [Serverless Auth](#serverless-auth)

## Auth Vault

Store credentials locally and reference them by name. The LLM never sees passwords.

### Commands

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

## Header-Based Auth

Use `--headers` to set HTTP headers scoped to a specific origin:

```bash
# Headers scoped to api.example.com only
agent-browser open api.example.com --headers '{"Authorization": "Bearer <token>"}'

# Requests to api.example.com include the auth header
agent-browser snapshot -i --json
agent-browser click @e2

# Navigate to another domain — headers NOT sent
agent-browser open other-site.com
```

### Multiple Origins

```bash
agent-browser open api.example.com --headers '{"Authorization": "Bearer token1"}'
agent-browser open api.acme.com --headers '{"Authorization": "Bearer token2"}'
```

### Global Headers

For headers on all domains:

```bash
agent-browser set headers '{"X-Custom-Header": "value"}'
```

### Use Cases

- **Skipping login flows** — Authenticate via headers
- **Switching users** — Different auth tokens per session
- **API testing** — Access protected endpoints
- **Security** — Headers scoped to origin, not leaked

## State Persistence

### Session Names (Auto Save/Restore)

Use `--session-name` to automatically save and restore cookies and localStorage across browser restarts:

```bash
# Auto-save/load state for "twitter" session
agent-browser --session-name twitter open twitter.com

# Login once, then state persists automatically
agent-browser --session-name twitter click "#login"

# Or via environment variable
export AGENT_BROWSER_SESSION_NAME=twitter
agent-browser open twitter.com
```

State files stored in `~/.agent-browser/sessions/` and automatically loaded on daemon start.

### Manual State Management

```bash
# Save state manually
agent-browser state save ./backup.json

# Load state from file
agent-browser state load ./backup.json

# List all saved states
agent-browser state list

# Show state summary (cookies, origins, domains)
agent-browser state show my-session-default.json

# Rename a state file
agent-browser state rename old-name new-name

# Clear states for a specific session name
agent-browser state clear my-session

# Clear all saved states
agent-browser state clear --all
```

### State Encryption

Encrypt saved state files (cookies, localStorage) using AES-256-GCM:

```bash
# Generate a 256-bit key (64 hex characters)
openssl rand -hex 32

# Set the encryption key
export AGENT_BROWSER_ENCRYPTION_KEY=<your-64-char-hex-key>

# State files are now encrypted automatically
agent-browser --session-name secure-session open example.com
```

### Persistent Profiles

Use `--profile` to persist full browser state across restarts:

```bash
# Use a persistent profile directory
agent-browser --profile ~/.myapp-profile open myapp.com

# Login once, then reuse the authenticated session
agent-browser --profile ~/.myapp-profile open myapp.com/dashboard

# Or via environment variable
AGENT_BROWSER_PROFILE=~/.myapp-profile agent-browser open myapp.com
```

The profile directory stores cookies, localStorage, IndexedDB, service workers, browser cache, and login sessions.

## HTTP Basic Auth

For sites using HTTP Basic Authentication:

```bash
agent-browser set credentials <username> <password>
```

## Serverless Auth

For serverless deployments (e.g., Vercel, AWS Lambda), use `@sparticuz/chromium` with agent-browser:

```javascript
const chromium = require("@sparticuz/chromium");

// Launch with serverless-compatible Chromium
const browser = await chromium.executablePath();
// Then connect agent-browser via CDP to the launched browser
```

See [agent-browser.dev/next](https://agent-browser.dev/next) for full Next.js + Vercel deployment patterns.
