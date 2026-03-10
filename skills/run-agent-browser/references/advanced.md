# Advanced Features

## Browser Extensions

Load Chrome extensions for testing extension-dependent workflows:

```bash
# Single extension
agent-browser --extension /path/to/extension open https://example.com

# Multiple extensions
agent-browser --extension ./ext1 --extension ./ext2 open https://example.com

# Via environment variable (comma-separated)
export AGENT_BROWSER_EXTENSIONS="/path/to/ext1,/path/to/ext2"
```

Extensions load in both headed and headless mode. User-level and project-level config extensions are merged.

## Custom Browser Executable

Use system Chrome, lightweight builds for serverless, or custom Chromium:

```bash
# System Chrome
agent-browser --executable-path /usr/bin/google-chrome open https://example.com

# AWS Lambda (@sparticuz/chromium)
CHROMIUM_PATH=$(node -e "console.log(require('@sparticuz/chromium').executablePath())")
agent-browser --executable-path "$CHROMIUM_PATH" open https://example.com

# Custom Chromium build
agent-browser --executable-path /opt/chromium/chrome open https://example.com
```

## WebSocket Streaming

Stream live browser frames over WebSocket for real-time preview:

```bash
export AGENT_BROWSER_STREAM_PORT=9223
agent-browser open https://example.com
# Connect WebSocket client to ws://localhost:9223
```

Protocol messages:
| Type | Direction | Format |
|------|-----------|--------|
| Frame | Server→Client | `{"type":"frame","data":"<base64 jpeg>"}` |
| Status | Server→Client | `{"type":"status","url":"...","title":"..."}` |
| Input | Client→Server | `{"type":"input","action":"click","x":100,"y":200}` |

Modifier bitmask for input: 1=Alt, 2=Ctrl, 4=Meta, 8=Shift.

## Trace Recording

Record Playwright traces for debugging complex automation:

```bash
agent-browser trace start
# ... perform actions ...
agent-browser trace stop trace.zip

# View in Playwright Trace Viewer
npx playwright show-trace trace.zip
```

Custom trace categories:

```bash
agent-browser profiler start --categories "devtools.timeline,v8.execute,blink.user_timing"
agent-browser profiler stop trace.json
```

View in Chrome DevTools Performance tab or [Perfetto UI](https://ui.perfetto.dev). Limitations: Chromium-only, ~5M event cap, 30s timeout on stop.

## Cloud Browser Providers

Connect to cloud-hosted browsers instead of local Chromium:

```bash
# Via flag
agent-browser -p browserbase open https://example.com

# Via environment variables
export AGENT_BROWSER_PROVIDER=browserbase
export BROWSERBASE_API_KEY=your-api-key
export BROWSERBASE_PROJECT_ID=your-project-id
agent-browser open https://example.com
```

The CLI command interface is identical — only the browser backend changes. Cloud providers handle lifecycle, scaling, and geo-distribution.

## Network Interception

Route, mock, or abort network requests:

```bash
# Block analytics/tracking
agent-browser network route "**analytics**" abort
agent-browser network route "**ads**" abort

# Mock API responses
agent-browser network mock "https://api.example.com/data" '{"items":[]}'

# Remove routes
agent-browser network unroute "**analytics**"

# View captured requests
agent-browser network requests --filter "api.example.com"
```

## Frames and Iframes

Navigate into nested browsing contexts:

```bash
agent-browser frame "#payment-iframe"   # Switch to iframe
agent-browser snapshot -i               # Snapshot within iframe
agent-browser fill @e1 "4242..."        # Interact inside iframe
agent-browser frame main                # Return to main frame
```

## Dialog Handling

Handle JavaScript alerts, confirms, and prompts:

```bash
agent-browser dialog accept             # Accept alert/confirm
agent-browser dialog dismiss            # Cancel/dismiss
agent-browser dialog accept "response"  # Accept prompt with text
```

## Cookie and Storage Management

```bash
# Cookies
agent-browser cookies get                          # All cookies
agent-browser cookies get --domain example.com     # Filter by domain
agent-browser cookies set name=session value=abc domain=.example.com
agent-browser cookies clear

# localStorage / sessionStorage
agent-browser storage get localStorage
agent-browser storage set localStorage key "value"
agent-browser storage clear localStorage
```

## Tab Management

```bash
agent-browser tab list                    # List open tabs
agent-browser tab new https://example.com # Open new tab
agent-browser tab switch 2                # Switch by index
agent-browser tab close                   # Close current tab
agent-browser click @e1 --new-tab         # Open link in new tab
```

## Mouse Control

Low-level mouse operations for drag-and-drop, canvas, or custom interactions:

```bash
agent-browser mouse move 100 200       # Move to coordinates
agent-browser mouse down               # Press button
agent-browser mouse up                 # Release button
agent-browser mouse wheel 0 -300       # Scroll (deltaX, deltaY)
agent-browser drag @e1 @e2             # Drag element to target
```

## Global Options Reference

| Option | Env Variable | Description |
|--------|-------------|-------------|
| `--session <name>` | — | Named session for isolation |
| `--profile <dir>` | `AGENT_BROWSER_PROFILE` | Persistent browser profile |
| `-p, --provider <name>` | `AGENT_BROWSER_PROVIDER` | Cloud browser provider |
| `--cdp <port>` | — | Connect via Chrome DevTools Protocol |
| `--auto-connect` | — | Auto-discover running Chrome |
| `--headed` | `AGENT_BROWSER_HEADED` | Show browser UI |
| `--native` | `AGENT_BROWSER_NATIVE` | Use native Rust daemon |
| `--engine <name>` | `AGENT_BROWSER_ENGINE` | Browser engine (chrome, lightpanda) |
| `--color-scheme <mode>` | `AGENT_BROWSER_COLOR_SCHEME` | dark / light / no-preference |
| `--extension <path>` | `AGENT_BROWSER_EXTENSIONS` | Load browser extension |
| `--executable-path <path>` | — | Custom browser binary path |
| `--ignore-https-errors` | — | Bypass SSL certificate errors |
| `--allow-file-access` | — | Enable file:// URLs |
| `--config <path>` | `AGENT_BROWSER_CONFIG` | Custom config file path |
| `--download-path <dir>` | — | Default download directory |
| `--content-boundaries` | `AGENT_BROWSER_CONTENT_BOUNDARIES` | LLM-safe output wrapping |
| `--args <flags>` | — | Extra Chromium flags |
| `--user-agent <string>` | — | Custom user agent string |
