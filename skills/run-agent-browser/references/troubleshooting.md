# Troubleshooting

Common issues and resolution steps.

## Daemon Not Starting

```bash
# Check for stale socket/PID files (v0.8.6+ auto-cleans these)
ls -la ~/.agent-browser/daemon.sock ~/.agent-browser/daemon.pid

# Close any existing session and restart
agent-browser close
agent-browser open example.com

# Check for port conflicts if using --cdp-port
lsof -i :9222
```

## Browser Not Found

```bash
# Install Chromium via agent-browser
agent-browser install

# Or specify a custom binary path
agent-browser --executable-path /path/to/chromium open example.com
# Environment variable alternative
export AGENT_BROWSER_EXECUTABLE_PATH=/path/to/chromium
```

## Linux Dependencies

```bash
# Install Chromium + system libraries
agent-browser install --with-deps

# Or via Playwright
npx playwright install-deps chromium
```

## Container / CI Environments

```bash
# Disable sandbox for container environments
agent-browser --args "--no-sandbox,--disable-gpu" open example.com

# agent-browser auto-adds --no-sandbox when running as root or in Docker/Podman
```

## CDP Connection Issues

```bash
# Verify Chrome DevTools port is accessible
curl -s http://localhost:9222/json/version

# Check Chrome's DevToolsActivePort file
cat /tmp/DevToolsActivePort 2>/dev/null || echo "Not found"

# Explicit CDP port
agent-browser --cdp-port 9222 open example.com
```

## Session State

```bash
# List saved states
agent-browser state list

# Clear all states
agent-browser state clear

# State files are encrypted; manage encryption key via:
export AGENT_BROWSER_STATE_KEY="your-encryption-key"
```

## iOS Automation Issues

- Appium must be installed: `npm install -g appium`
- Simulator runtimes: download via Xcode > Settings > Platforms
- WebDriverAgent requires Apple Developer signing
- Only Safari and WebViews are automatable on iOS

## Lightpanda Engine Issues

```bash
# Ensure binary is in PATH
which lightpanda || echo "Not found — install from github.com/lightpanda-io/browser"

# Known limitations: no extensions, no persistent profiles,
# no storage state, no headed mode, no screenshots (depends on CDP support)
```

## Native Mode Issues

```bash
# Must close existing daemon before switching modes
agent-browser close
export AGENT_BROWSER_NATIVE=1
agent-browser open example.com

# Known limitations: no Firefox/WebKit, no Playwright traces,
# no HAR export, network interception uses CDP Fetch domain
```

## IPC Timeout

```bash
# Default timeout is 25000ms (25 seconds)
# Keep below 30000ms to avoid daemon-level timeouts
export AGENT_BROWSER_DEFAULT_TIMEOUT=25000
```

## Refs Not Working After Page Change

Refs (`@e1`, `@e2`) are invalidated when the DOM changes. Always re-snapshot after any action that changes the page:

```bash
agent-browser click @e5          # triggers navigation
agent-browser wait --load networkidle
agent-browser snapshot -i        # MUST re-snapshot — old refs are stale
agent-browser click @e1          # now safe — uses fresh refs
```

## Snapshot Returns Too Many/Few Elements

```bash
# Interactive elements only (recommended default)
agent-browser snapshot -i

# Include cursor-interactive elements (divs with onclick, cursor:pointer)
agent-browser snapshot -i -C

# Scope to a specific section
agent-browser snapshot -i -s "#main-content"
```

## Stale Daemon

The CLI (v0.8.6+) automatically cleans up stale socket and PID files on next start. For older versions:

```bash
rm -f ~/.agent-browser/daemon.pid ~/.agent-browser/daemon.sock
```

## SSL / Certificate Errors

```bash
# For self-signed certs or corporate SSL inspection proxies
agent-browser --ignore-https-errors open https://self-signed.example.com
```

## Common Environment Variables

| Variable | Purpose |
|----------|---------|
| `AGENT_BROWSER_DEFAULT_TIMEOUT` | Default timeout in ms (default: 25000, keep below 30000) |
| `AGENT_BROWSER_EXECUTABLE_PATH` | Custom browser binary path |
| `AGENT_BROWSER_NATIVE` | Enable native Rust daemon (0/1) |
| `AGENT_BROWSER_ENGINE` | Browser engine: chrome, lightpanda |
| `AGENT_BROWSER_HEADED` | Show browser UI (0/1) |
| `AGENT_BROWSER_EXTENSIONS` | Comma-separated extension paths |
| `AGENT_BROWSER_STATE_KEY` | Encryption key for state files |
| `AGENT_BROWSER_ALLOWED_DOMAINS` | Domain allowlist (comma-separated) |
| `AGENT_BROWSER_MAX_OUTPUT` | Max output characters (default: 50000) |
