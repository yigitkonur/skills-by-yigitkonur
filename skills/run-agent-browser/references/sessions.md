# Sessions

Sessions provide isolated browser contexts with independent cookies, storage, navigation history, and auth state.

## Multiple Sessions

```bash
# Named session
agent-browser --session staging open https://staging.example.com

# Via environment variable
AGENT_BROWSER_SESSION=staging agent-browser open https://staging.example.com
```

Each session gets its own browser instance with complete isolation.

## Session Listing

```bash
agent-browser session list
```

## Persistent Profiles

Use `--profile` to persist browser data (cookies, localStorage, etc.) across sessions:

```bash
agent-browser --profile ./browser-data open example.com

# Via environment variable
AGENT_BROWSER_PROFILE=./browser-data agent-browser open example.com
```

## Session Persistence

Name sessions for persistence with `--session-name`:

```bash
agent-browser --session-name my-session open example.com

# Via environment variable
AGENT_BROWSER_SESSION_NAME=my-session agent-browser open example.com
```

### Session Name Rules

- Alphanumeric characters, hyphens, and underscores only
- No path traversal (`..`), spaces, or slashes

## State Storage

State files are stored in `~/.agent-browser/sessions/`.

### State Encryption

Encrypt state files with AES-256-GCM:

```bash
# Generate a 64-character hex key
openssl rand -hex 32

# Set the encryption key
export AGENT_BROWSER_ENCRYPTION_KEY=<64-char-hex-key>
```

### State Auto-Expiration

States expire automatically after a configurable period:

```bash
# Default: 30 days
export AGENT_BROWSER_STATE_EXPIRE_DAYS=30

# Manual cleanup: remove states older than 7 days
agent-browser state clean --older-than 7
```

### State Management Commands

```bash
# List all saved states
agent-browser state list

# Show details of a state
agent-browser state show <name>

# Rename a state
agent-browser state rename <old-name> <new-name>

# Clear a specific state
agent-browser state clear <name>

# Clear all states
agent-browser state clear --all

# Save current state
agent-browser state save <name>

# Load a saved state
agent-browser state load <name>
```

## Authenticated Sessions

Scope custom headers to specific origins:

```bash
agent-browser --headers '{"Authorization": "Bearer <token>"}' open https://api.example.com
```

- Headers are scoped to the origin they are set on
- Headers are **NOT** sent to other domains
- Multiple origins are supported

### Global Headers

Set headers that apply globally:

```bash
agent-browser set headers '{"X-Custom-Header": "value"}'
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `AGENT_BROWSER_SESSION` | Session name |
| `AGENT_BROWSER_SESSION_NAME` | Persistent session name |
| `AGENT_BROWSER_PROFILE` | Browser profile directory path |
| `AGENT_BROWSER_STATE_EXPIRE_DAYS` | Days before state auto-expires (default: 30) |
| `AGENT_BROWSER_ENCRYPTION_KEY` | 64-char hex key for AES-256-GCM state encryption |
