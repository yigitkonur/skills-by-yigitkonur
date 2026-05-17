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
# Browserbase
agent-browser -p browserbase open https://example.com
# Requires: BROWSERBASE_API_KEY, BROWSERBASE_PROJECT_ID

# BrowserUse
agent-browser -p browseruse open https://example.com
# Requires: BROWSERUSE_API_KEY

# Kernel (by Browserbase — stealth-optimized)
agent-browser -p kernel open https://example.com
# Requires: BROWSERBASE_API_KEY

# iOS Simulator (see iOS Simulator section below)
agent-browser -p ios --device "iPhone 16 Pro" open https://example.com
```

```bash
# Via environment variable (avoids passing -p every time)
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
agent-browser network route "**analytics**" --abort
agent-browser network route "**ads**" --abort

# Mock API responses with a custom body
agent-browser network route "https://api.example.com/data" --body '{"items":[]}'

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
agent-browser cookies
agent-browser cookies --json | jq '.[] | select(.domain == ".example.com")'
agent-browser cookies set session "abc" --domain .example.com --path /
agent-browser cookies clear

# localStorage / sessionStorage
agent-browser storage local
agent-browser storage local get key
agent-browser storage local set key "value"
agent-browser storage local clear
agent-browser storage session get sessionKey
```

## Tab Management

```bash
agent-browser tab                         # List open tabs
agent-browser tab new https://example.com # Open new tab
agent-browser tab 2                       # Switch by index
agent-browser tab close                   # Close current tab
agent-browser click @e1 --new-tab         # Open link in new tab
```

## Mouse Control

Low-level mouse operations for drag-and-drop, canvas, or custom interactions:

```bash
agent-browser mouse move 100 200       # Move to coordinates
agent-browser mouse down left          # Press button
agent-browser mouse up left            # Release button
agent-browser mouse wheel -300 0       # Scroll (dy, dx)
agent-browser drag @e1 @e2             # Drag element to target
```

## JavaScript Evaluation

Use `eval` to run JavaScript in the browser context. **Shell quoting can corrupt complex expressions** — use `--stdin` or `-b` to avoid issues.

```bash
# Simple expressions work with regular quoting
agent-browser eval 'document.title'
agent-browser eval 'document.querySelectorAll("img").length'

# Complex JS: use --stdin with heredoc (RECOMMENDED)
agent-browser eval --stdin <<'EVALEOF'
JSON.stringify(
  Array.from(document.querySelectorAll("img"))
    .filter(i => !i.alt)
    .map(i => ({ src: i.src.split("/").pop(), width: i.width }))
)
EVALEOF

# Alternative: base64 encoding (avoids all shell escaping issues)
agent-browser eval -b "$(echo -n 'Array.from(document.querySelectorAll("a")).map(a => a.href)' | base64)"
```

**Rules of thumb:**
- Single-line, no nested quotes → regular `eval 'expression'` with single quotes
- Nested quotes, arrow functions, template literals, or multiline → use `eval --stdin <<'EVALEOF'`
- Programmatic/generated scripts → use `eval -b` with base64

## iOS Simulator (Mobile Safari)

Test on mobile Safari using iOS Simulator on macOS:

```bash
# List available iOS simulators
agent-browser device list

# Launch Safari on a specific device
agent-browser -p ios --device "iPhone 16 Pro" open https://example.com

# Same workflow as desktop — snapshot, interact, re-snapshot
agent-browser -p ios snapshot -i
agent-browser -p ios tap @e1          # Tap (alias for click)
agent-browser -p ios fill @e2 "text"
agent-browser -p ios swipe up         # Mobile-specific gesture

# Take screenshot
agent-browser -p ios screenshot mobile.png

# Close session (shuts down simulator)
agent-browser -p ios close
```

**Requirements:** macOS with Xcode, Appium (`npm install -g appium && appium driver install xcuitest`)

**Real devices:** Works with physical iOS devices if pre-configured. Use `--device "<UDID>"` where UDID is from `xcrun xctrace list devices`.

## Native Mode (Experimental)

agent-browser has an experimental native Rust daemon that communicates with Chrome directly via CDP, bypassing Node.js and Playwright entirely:

```bash
# Enable via flag
agent-browser --native open example.com

# Enable via environment variable (avoids passing --native every time)
export AGENT_BROWSER_NATIVE=1
agent-browser open example.com
```

Supports Chromium and Safari (via WebDriver). Firefox and WebKit are not yet supported. All core commands work identically. Use `agent-browser close` before switching between native and default mode.

## Engine Selection

Use `--engine` to choose a local browser engine (default: `chrome`):

```bash
# Use Lightpanda (fast headless browser, requires separate install)
agent-browser --engine lightpanda open example.com

# Via environment variable
export AGENT_BROWSER_ENGINE=lightpanda
agent-browser open example.com
```

Supported engines:
- `chrome` (default) — Chrome/Chromium via CDP
- `lightpanda` — 10x faster, 10x less memory than Chrome (no `--extension`, `--profile`, `--state`, or `--allow-file-access`)

Install Lightpanda from https://lightpanda.io/docs/open-source/installation.

## Viewport & Device Emulation

```bash
# Set viewport size (default: 1280x720)
agent-browser set viewport 1920 1080

# Retina/HiDPI: same CSS layout at 2x pixel density
agent-browser set viewport 1920 1080 2

# Device emulation (sets viewport + user agent)
agent-browser set device "iPhone 14"

# Color scheme
agent-browser --color-scheme dark open https://example.com
agent-browser set media dark
```

The `scale` parameter (3rd argument to viewport) sets `window.devicePixelRatio` without changing CSS layout.

## Local Files (PDFs, HTML)

```bash
agent-browser --allow-file-access open file:///path/to/document.pdf
agent-browser --allow-file-access open file:///path/to/page.html
agent-browser screenshot output.png
```

## Global Options Reference

| Option | Env Variable | Description |
|--------|-------------|-------------|
| `--session <name>` | `AGENT_BROWSER_SESSION` | Named session for isolation |
| `--session-name <name>` | `AGENT_BROWSER_SESSION_NAME` | Auto-save/restore session state |
| `--profile <dir>` | `AGENT_BROWSER_PROFILE` | Persistent browser profile |
| `--state <path>` | `AGENT_BROWSER_STATE` | Load storage state JSON |
| `-p, --provider <name>` | `AGENT_BROWSER_PROVIDER` | Cloud provider (browserbase, browseruse, kernel, ios) |
| `--cdp <port>` | — | Connect via Chrome DevTools Protocol |
| `--auto-connect` | — | Auto-discover running Chrome |
| `--headed` | `AGENT_BROWSER_HEADED` | Show browser UI |
| `--native` | `AGENT_BROWSER_NATIVE` | Use native Rust daemon |
| `--engine <name>` | `AGENT_BROWSER_ENGINE` | Browser engine (chrome, lightpanda) |
| `--color-scheme <mode>` | `AGENT_BROWSER_COLOR_SCHEME` | dark / light / no-preference |
| `--extension <path>` | `AGENT_BROWSER_EXTENSIONS` | Load browser extension (repeatable) |
| `--executable-path <path>` | `AGENT_BROWSER_EXECUTABLE_PATH` | Custom browser binary path |
| `--ignore-https-errors` | — | Bypass SSL certificate errors |
| `--allow-file-access` | — | Enable file:// URLs |
| `--config <path>` | `AGENT_BROWSER_CONFIG` | Custom config file path |
| `--download-path <dir>` | — | Default download directory |
| `--content-boundaries` | `AGENT_BROWSER_CONTENT_BOUNDARIES` | LLM-safe output wrapping |
| `--max-output <chars>` | `AGENT_BROWSER_MAX_OUTPUT` | Truncate page output |
| `--allowed-domains <list>` | `AGENT_BROWSER_ALLOWED_DOMAINS` | Domain allowlist (comma-separated) |
| `--action-policy <path>` | `AGENT_BROWSER_ACTION_POLICY` | Path to action policy JSON |
| `--confirm-actions <list>` | `AGENT_BROWSER_CONFIRM_ACTIONS` | Actions requiring confirmation |
| `--args <flags>` | `AGENT_BROWSER_ARGS` | Extra Chromium flags |
| `--user-agent <string>` | `AGENT_BROWSER_USER_AGENT` | Custom user agent string |
| `--debug` | `AGENT_BROWSER_DEBUG` | Enable debug logging |
| `--json` | — | Machine-readable JSON output |
