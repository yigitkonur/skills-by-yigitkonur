# Troubleshooting

Common issues and resolution steps.

## CLI runs but no browser opens

Chromium is not installed. Run the install command:

```bash
agent-browser install
```

On Linux, system libraries are also required:

```bash
# Install Chromium + system dependencies
agent-browser install --with-deps

# Or via Playwright
npx playwright install-deps chromium
```

## Daemon not responding / stale session

```bash
# Close any existing session
agent-browser close

# If close fails with EADDRINUSE or a stale-socket error:
# 1) confirm there is no live agent-browser process you care about
ps aux | grep '[a]gent-browser'

# 2) inspect the socket/pid files in ~/.agent-browser
ls -la ~/.agent-browser

# 3) remove only stale files for the affected session
#    (common names: default.sock, daemon.sock, or <session>.sock)
rm -f ~/.agent-browser/default.pid ~/.agent-browser/default.sock
rm -f ~/.agent-browser/daemon.pid ~/.agent-browser/daemon.sock
rm -f ~/.agent-browser/*.pid ~/.agent-browser/*.sock
```

Use the targeted removal commands first. The wildcard cleanup is the last resort when you have confirmed there is no live browser state worth preserving.

## Native binary not available

The CLI automatically falls back to the Node.js daemon when the native Rust binary isn't available for your platform. Ensure Node.js 18+ is installed.

| Platform | Native Binary | Fallback |
|----------|--------------|----------|
| macOS ARM64 (Apple Silicon) | ✅ | Node.js daemon |
| macOS x64 (Intel) | ✅ | Node.js daemon |
| Linux ARM64 | ✅ | Node.js daemon |
| Linux x64 | ✅ | Node.js daemon |
| Windows x64 | ✅ | Node.js daemon |

## Refs not working after page change

Refs (`@e1`, `@e2`) are invalidated when the DOM changes. **Always re-snapshot after any action that changes the page:**

```bash
agent-browser click @e5          # Triggers navigation
agent-browser wait --load networkidle
agent-browser snapshot -i        # MUST re-snapshot — old refs are stale
agent-browser click @e1          # Now safe — uses fresh refs
```

Common triggers that invalidate refs:
- Page navigation (`open`, clicking links)
- Form submissions
- SPA route changes
- Dynamic content loading (AJAX, infinite scroll)
- Tab switching

## Snapshot returns too many/few elements

```bash
# Interactive elements only (recommended default)
agent-browser snapshot -i

# Include cursor-interactive elements (divs with onclick, cursor:pointer)
agent-browser snapshot -i -C

# Scope to a specific section
agent-browser snapshot -i -s "#main-content"

# Full page (rarely needed — very verbose)
agent-browser snapshot
```

## Timeout errors on slow pages

```bash
# Increase default timeout (milliseconds)
export AGENT_BROWSER_DEFAULT_TIMEOUT=60000

# Use explicit waits for slow-loading pages
agent-browser open https://slow-site.com
agent-browser wait --load networkidle
agent-browser snapshot -i
```

## SSL / certificate errors

```bash
# For self-signed certs or corporate SSL inspection proxies
agent-browser --ignore-https-errors open https://self-signed.example.com
```

## Trace recording for debugging

Record a Playwright trace to debug complex automation failures:

```bash
agent-browser trace start
# ... perform actions ...
agent-browser trace stop trace.zip
npx playwright show-trace trace.zip
```

Limitations: Chromium-only, ~5M event cap, 30-second timeout on stop.

## Browser extensions not loading

```bash
# Single extension
agent-browser --extension /path/to/extension open https://example.com

# Multiple extensions
agent-browser --extension ./ext1 --extension ./ext2 open https://example.com

# Via environment variable (comma-separated)
export AGENT_BROWSER_EXTENSIONS="/path/to/ext1,/path/to/ext2"
```

Extensions work in both headed and headless mode.

## Serverless / CI environments

```bash
# Use lightweight Chromium for serverless (e.g., AWS Lambda)
agent-browser --executable-path $(node -e "console.log(require('@sparticuz/chromium').executablePath())") open https://example.com

# System Chrome in CI
agent-browser --executable-path /usr/bin/google-chrome open https://example.com
```

## Debug Logging

When commands behave unexpectedly, enable debug output:

```bash
# Via flag
agent-browser --debug open https://example.com

# Via environment variable
export AGENT_BROWSER_DEBUG=1
agent-browser open https://example.com
```

Debug output goes to stderr. Combine with `--json` for machine-parseable stdout + human debug on stderr.

## Common Environment Variables

| Variable | Purpose |
|----------|---------|
| `AGENT_BROWSER_DEFAULT_TIMEOUT` | Default timeout in ms (default: 30000) |
| `AGENT_BROWSER_ALLOWED_DOMAINS` | Domain allowlist (comma-separated) |
| `AGENT_BROWSER_CONTENT_BOUNDARIES` | Wrap output for LLM safety (0/1) |
| `AGENT_BROWSER_MAX_OUTPUT` | Max output characters (default: 50000) |
| `AGENT_BROWSER_HEADED` | Show browser UI (0/1) |
| `AGENT_BROWSER_ACTION_POLICY` | Path to action policy JSON |
| `AGENT_BROWSER_EXTENSIONS` | Comma-separated extension paths |
| `AGENT_BROWSER_PROVIDER` | Cloud browser provider name |
| `AGENT_BROWSER_SESSION` | Default session name |
| `AGENT_BROWSER_SESSION_NAME` | Auto-save/restore session name |
| `AGENT_BROWSER_STATE` | Storage state JSON path |
| `AGENT_BROWSER_NATIVE` | Use native Rust daemon (0/1) |
| `AGENT_BROWSER_ENGINE` | Browser engine (chrome, lightpanda) |
| `AGENT_BROWSER_COLOR_SCHEME` | Color scheme (dark/light/no-preference) |
| `AGENT_BROWSER_PROFILE` | Persistent browser profile directory |
| `AGENT_BROWSER_CONFIG` | Config file path |
| `AGENT_BROWSER_USER_AGENT` | Custom user agent string |
| `AGENT_BROWSER_ARGS` | Extra Chromium launch flags |
| `AGENT_BROWSER_DEBUG` | Enable debug logging (0/1) |
| `AGENT_BROWSER_PROXY_BYPASS` | Hosts to bypass proxy |
| `AGENT_BROWSER_CONFIRM_ACTIONS` | Actions requiring confirmation |
| `AGENT_BROWSER_CONFIRM_INTERACTIVE` | Interactive cmds requiring confirmation |
| `AGENT_BROWSER_ENCRYPTION_KEY` | Encryption key for saved state |
| `AGENT_BROWSER_STATE_EXPIRE_DAYS` | Auto-expire saved state after N days |
