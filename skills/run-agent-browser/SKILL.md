---
name: run-agent-browser
description: Use skill if you are automating browser tasks like navigation, form filling, screenshots, data extraction, or web app testing with Browserbase agent CLI.
allowed-tools: Bash(npx agent-browser:*), Bash(agent-browser:*)
---

# Browser Automation with agent-browser

Browser automation CLI designed for AI agents. Compact text output minimizes context usage (200-400 tokens vs 3000-5000 for full DOM). Fast Rust CLI with Node.js fallback. Client-daemon architecture: Rust CLI parses commands → Node.js Daemon manages Playwright browser (or Native Rust Daemon using direct CDP). 50+ commands for navigation, forms, screenshots, network, storage.

Works with: Claude Code, Cursor, GitHub Copilot, OpenAI Codex, Google Gemini, opencode, and any agent that can run shell commands.

---

## 1. Installation

```bash
# Global install (fastest — native Rust CLI)
npm install -g agent-browser

# macOS via Homebrew
brew install agent-browser

# No install (slower — Node.js routing)
npx agent-browser open example.com

# Project-local
npm install agent-browser

# Download Chromium
agent-browser install

# Linux: include system dependencies
agent-browser install --with-deps

# AI agent setup
npx skills add vercel-labs/agent-browser
```

**Custom browser:** Use `--executable-path /path/to/chrome` or `AGENT_BROWSER_EXECUTABLE_PATH` env var.

**Serverless:** Use `@sparticuz/chromium` (~50MB vs ~684MB for full Chromium).

**Native binaries available for:** macOS (ARM64, x64), Linux (ARM64, x64), Windows (x64).

---

## 2. Core Workflow

Every browser automation follows this pattern:

1. **Navigate**: `agent-browser open <url>`
2. **Snapshot**: `agent-browser snapshot -i` — get interactive elements with refs (`@e1`, `@e2`)
3. **Interact**: Use refs to `click`, `fill`, `select`
4. **Re-snapshot**: After page changes, get fresh refs

```bash
agent-browser open https://example.com/form
agent-browser snapshot -i
# Output: @e1 [input type="email"], @e2 [input type="password"], @e3 [button] "Submit"

agent-browser fill @e1 "user@example.com"
agent-browser fill @e2 "password123"
agent-browser click @e3
agent-browser wait --load networkidle
agent-browser snapshot -i  # Check result
```

### DOM-Evidence Principle

After performing actions, verify results via DOM assertions before relying on screenshots:

```bash
agent-browser click @e3                    # Submit form
agent-browser wait --load networkidle
agent-browser snapshot -i
RESULT=$(agent-browser get text @e1)       # DOM evidence (deterministic)
agent-browser screenshot ./evidence.png    # Visual evidence (supplementary)
```

DOM text is the source of truth. Screenshots supplement for human review.

### Ref Lifecycle (Important)

Refs (`@e1`, `@e2`, etc.) are invalidated when the page changes. Always re-snapshot after:

- Clicking links or buttons that navigate
- Form submissions
- Dynamic content loading (dropdowns, modals)

```bash
agent-browser click @e5              # Navigates to new page
agent-browser snapshot -i            # MUST re-snapshot — old refs are invalid
agent-browser click @e1              # Use new refs
```

---

## 3. Selector Types

When targeting elements, prefer this order:

### 1. Refs (Recommended)

From `snapshot -i` output. Deterministic, fast, AI-friendly.

```bash
agent-browser click @e1
agent-browser fill @e2 "text"
```

### 2. CSS Selectors

Standard CSS selectors when refs are unavailable.

```bash
agent-browser click "#submit-btn"
agent-browser click ".nav > button"
agent-browser click "[data-testid='submit']"
```

### 3. Text & XPath

```bash
agent-browser click "text=Submit"
agent-browser click "xpath=//button[@type='submit']"
```

### 4. Semantic Locators

Framework-agnostic, resilient to DOM changes.

```bash
agent-browser find role button click --name "Submit"
agent-browser find text "Sign In" click
agent-browser find label "Email" fill "user@test.com"
agent-browser find placeholder "Search" type "query"
agent-browser find alt "Logo" click
agent-browser find title "Close" click
agent-browser find testid "submit-btn" click
agent-browser find first "button" click
agent-browser find last "button" click
agent-browser find nth "li" 3 click
```

---

## 4. Complete Command Reference

### Navigation

```bash
agent-browser open <url>                   # Navigate to URL
agent-browser back                         # Go back
agent-browser forward                      # Go forward
agent-browser reload                       # Reload page
agent-browser close                        # Close browser
agent-browser connect <port|url>           # Connect to existing browser via CDP
```

### Interaction

```bash
agent-browser click <selector>             # Click element
agent-browser dblclick <selector>          # Double-click element
agent-browser fill <selector> "text"       # Clear field, then type text
agent-browser type <selector> "text"       # Type text without clearing
agent-browser press <key>                  # Press key (Enter, Tab, Escape, etc.)
agent-browser keyboard type "text"         # Type at current focus (no selector)
agent-browser keyboard inserttext "text"   # Insert text without key events
agent-browser keydown <key>                # Press key down
agent-browser keyup <key>                  # Release key
agent-browser hover <selector>             # Hover over element
agent-browser focus <selector>             # Focus element
agent-browser select <selector> "option"   # Select dropdown option
agent-browser check <selector>             # Check checkbox
agent-browser uncheck <selector>           # Uncheck checkbox
agent-browser scroll <direction> <amount>  # Scroll page (up/down/left/right)
agent-browser scrollintoview <selector>    # Scroll element into view
agent-browser drag <src> <dst>             # Drag from source to destination
agent-browser upload <selector> <file>     # Upload file to input
```

### Get Information

```bash
agent-browser get text <selector>          # Get element text content
agent-browser get html <selector>          # Get element HTML
agent-browser get value <selector>         # Get input value
agent-browser get attr <selector> <name>   # Get attribute value
agent-browser get title                    # Get page title
agent-browser get url                      # Get current URL
agent-browser get count <selector>         # Count matching elements
agent-browser get box <selector>           # Get bounding box (x, y, width, height)
agent-browser get styles <selector>        # Get computed styles
```

### Check State

```bash
agent-browser is visible <selector>        # Check if element is visible
agent-browser is enabled <selector>        # Check if element is enabled
agent-browser is checked <selector>        # Check if checkbox is checked
```

### Snapshot & Screenshot

```bash
agent-browser snapshot                     # Full accessibility tree
agent-browser snapshot -i                  # Interactive elements only (recommended)
agent-browser snapshot -i -C               # Include cursor-interactive elements
agent-browser snapshot -c                  # Compact mode
agent-browser snapshot -d <N>              # Limit tree depth
agent-browser snapshot -s "<selector>"     # Scope to CSS selector
agent-browser snapshot --json              # JSON output
agent-browser screenshot                   # Screenshot to temp dir
agent-browser screenshot <path>            # Screenshot to specific path
agent-browser screenshot --full            # Full page screenshot
agent-browser screenshot -f               # Full page (short flag)
agent-browser screenshot --annotate        # Numbered labels on interactive elements
agent-browser pdf <path>                   # Save page as PDF
```

### Wait Strategies

```bash
agent-browser wait <selector>              # Wait for element to appear
agent-browser wait <ms>                    # Wait fixed milliseconds
agent-browser wait --text "text"           # Wait for text to appear on page
agent-browser wait --url "pattern"         # Wait for URL match (glob)
agent-browser wait --load networkidle      # Wait for network idle
agent-browser wait --fn "js expression"    # Wait for JS condition to be truthy
agent-browser wait --download <path>       # Wait for download to complete
```

### Downloads

```bash
agent-browser download <selector> <path>            # Click to trigger download
agent-browser wait --download <path>                 # Wait for any download
agent-browser --download-path ./downloads open <url> # Set default download dir
```

### JavaScript Evaluation

```bash
agent-browser eval 'expression'            # Evaluate JS in browser
agent-browser eval --stdin                  # Read JS from stdin
agent-browser eval -b "<base64>"           # Execute base64-encoded JS
```

### Find Elements (Semantic Locators with Actions)

```bash
agent-browser find role <role> <action>              # By ARIA role
agent-browser find text "text" <action>              # By visible text
agent-browser find label "label" <action>            # By label text
agent-browser find placeholder "text" <action>       # By placeholder
agent-browser find alt "text" <action>               # By alt text
agent-browser find title "text" <action>             # By title attribute
agent-browser find testid "id" <action>              # By data-testid
agent-browser find first "<selector>" <action>       # First matching element
agent-browser find last "<selector>" <action>        # Last matching element
agent-browser find nth "<selector>" <N> <action>     # Nth matching element
```

Actions: `click`, `fill "text"`, `type "text"`, `hover`, `focus`, etc.

### Mouse Control

```bash
agent-browser mouse move <x> <y>           # Move mouse to coordinates
agent-browser mouse down                   # Press mouse button
agent-browser mouse up                     # Release mouse button
agent-browser mouse wheel <dx> <dy>        # Scroll wheel
```

### Settings

```bash
agent-browser set viewport <w> <h>         # Set viewport size
agent-browser set viewport <w> <h> <scale> # Set viewport with device pixel ratio
agent-browser set device "name"            # Emulate device (viewport + UA)
agent-browser set geo <lat> <lon>          # Set geolocation
agent-browser set offline <true|false>     # Toggle offline mode
agent-browser set headers '{"key":"val"}'  # Set extra HTTP headers
agent-browser set credentials <user> <pw>  # Set HTTP auth credentials
agent-browser set media <scheme>           # Set color scheme (dark/light)
```

### Cookies & Storage

```bash
agent-browser cookies get                  # Get all cookies
agent-browser cookies set <json>           # Set cookies
agent-browser cookies clear                # Clear all cookies
agent-browser storage local get [key]      # Get localStorage value(s)
agent-browser storage local set <k> <v>    # Set localStorage value
agent-browser storage local clear          # Clear localStorage
agent-browser storage session get [key]    # Get sessionStorage value(s)
agent-browser storage session set <k> <v>  # Set sessionStorage value
agent-browser storage session clear        # Clear sessionStorage
```

### Network Interception

```bash
agent-browser network route <pattern>              # Intercept matching requests
agent-browser network route <pattern> --abort       # Block matching requests
agent-browser network route <pattern> --body <file> # Respond with file content
agent-browser network unroute <pattern>             # Remove route
agent-browser network requests                      # List captured requests
agent-browser network requests --clear              # Clear request log
agent-browser network requests --filter <pattern>   # Filter requests
```

### Tabs & Windows

```bash
agent-browser tab list                     # List open tabs
agent-browser tab new <url>                # Open new tab
agent-browser tab switch <index>           # Switch to tab by index
agent-browser tab close [index]            # Close tab
agent-browser window new <url>             # Open new window
```

### Frames

```bash
agent-browser frame switch <selector>      # Switch to iframe
agent-browser frame main                   # Switch back to main frame
```

### Dialogs

```bash
agent-browser dialog accept [text]         # Accept dialog (optional input text)
agent-browser dialog dismiss               # Dismiss dialog
```

### State Management

```bash
agent-browser state save <name>            # Save cookies + localStorage
agent-browser state load <name>            # Load saved state
agent-browser state list                   # List saved states
agent-browser state show <name>            # Show state contents
agent-browser state rename <old> <new>     # Rename saved state
agent-browser state clear <name>           # Delete specific state
agent-browser state clean                  # Clean expired states
agent-browser state clean --older-than <N> # Clean states older than N days
```

### Auth Vault

```bash
agent-browser auth save <name> --url <url> --username <user> --password-stdin  # Save credentials
agent-browser auth login <name>            # Login using saved profile
agent-browser auth list                    # List saved auth profiles
agent-browser auth show <name>             # Show auth profile details
agent-browser auth delete <name>           # Delete auth profile
```

### Sessions

```bash
agent-browser session                      # Current session info
agent-browser session list                 # List active sessions
```

### Confirmation (with --confirm-actions)

```bash
agent-browser confirm                      # Approve pending action
agent-browser deny                         # Deny pending action
```

### Debug & Profiling

```bash
agent-browser trace start                  # Start Playwright trace
agent-browser trace stop                   # Stop trace
agent-browser profiler start               # Start Chrome DevTools profiler
agent-browser profiler stop [path]         # Stop profiler, save trace
agent-browser record start <path>          # Start recording video
agent-browser record stop                  # Stop recording
agent-browser record restart               # Restart recording
agent-browser console                      # Show console messages
agent-browser errors                       # Show page errors
agent-browser highlight <selector>         # Highlight element visually
```

### Diffing

```bash
agent-browser diff snapshot                              # Compare current vs last snapshot
agent-browser diff snapshot --baseline <file>             # Compare current vs saved file
agent-browser diff screenshot --baseline <file>           # Pixel-level visual diff
agent-browser diff url <url1> <url2>                      # Compare two pages
agent-browser diff url <url1> <url2> --wait-until <state> # Custom wait
agent-browser diff url <url1> <url2> --selector "#main"   # Scope diff
```

---

## 5. Snapshot Options and Best Practices

### Options

| Flag | Description |
|------|-------------|
| `-i` | Interactive elements only (recommended default) |
| `-C` | Include cursor-interactive elements (divs with onclick, cursor:pointer) |
| `-c` | Compact output |
| `-d <N>` | Limit tree depth |
| `-s "<selector>"` | Scope to CSS selector |
| `--json` | Output as JSON |

### Best Practices

- **Always use `-i`** for interaction workflows — reduces noise dramatically
- **Use `-C`** when clickable divs/spans aren't appearing in `-i` output
- **Use `-s`** to scope to a specific region (e.g., `-s "#modal"`, `-s ".sidebar"`)
- **Re-snapshot after every page change** — refs are invalidated on navigation, form submit, dynamic content load
- **Use `--json`** when programmatically parsing output

### Annotated Screenshots (Vision Mode)

Use `--annotate` to take a screenshot with numbered labels overlaid on interactive elements. Each label `[N]` maps to ref `@eN`. This caches refs, so you can interact immediately without a separate snapshot.

```bash
agent-browser screenshot --annotate
# Output includes the image path and a legend:
#   [1] @e1 button "Submit"
#   [2] @e2 link "Home"
#   [3] @e3 textbox "Email"
agent-browser click @e2              # Click using ref from annotated screenshot
```

Use annotated screenshots when:
- The page has unlabeled icon buttons or visual-only elements
- You need to verify visual layout or styling
- Canvas or chart elements are present (invisible to text snapshots)
- You need spatial reasoning about element positions

---

## 6. Wait Strategies

The default Playwright timeout is 25 seconds for local browsers. Override with `AGENT_BROWSER_DEFAULT_TIMEOUT` (milliseconds).

```bash
# Wait for network activity to settle (best for slow pages)
agent-browser wait --load networkidle

# Wait for a specific element to appear
agent-browser wait "#content"
agent-browser wait @e1

# Wait for a specific URL pattern (useful after redirects)
agent-browser wait --url "**/dashboard"

# Wait for text to appear on page
agent-browser wait --text "Success"

# Wait for a JavaScript condition
agent-browser wait --fn "document.readyState === 'complete'"

# Wait for download to complete
agent-browser wait --download ./output.zip

# Wait a fixed duration (milliseconds) — last resort
agent-browser wait 5000
```

**Best practice:** Use `wait --load networkidle` after `open` for slow pages. Use `wait <selector>` or `wait @ref` for elements that render asynchronously.

---

## 7. Session Management

### Named Sessions (Isolation)

Each `--session` gets its own browser instance with isolated cookies, storage, auth, and history.

```bash
# Parallel isolated sessions
agent-browser --session site1 open https://site-a.com
agent-browser --session site2 open https://site-b.com

agent-browser --session site1 snapshot -i
agent-browser --session site2 snapshot -i

# List active sessions
agent-browser session list

# Close specific session
agent-browser --session site1 close
```

### Session Persistence (--session-name)

Auto-save/restore cookies and localStorage across browser restarts.

```bash
agent-browser --session-name myapp open https://app.example.com/login
# ... login flow ...
agent-browser close  # State auto-saved to ~/.agent-browser/sessions/

# Next time — state is auto-loaded
agent-browser --session-name myapp open https://app.example.com/dashboard
```

### Browser Profiles (--profile)

Persistent browser profiles across restarts (full Chrome profile directory).

```bash
agent-browser --profile ./browser-data open https://example.com
```

### State Files

State files stored in `~/.agent-browser/sessions/`.

```bash
agent-browser state save auth.json       # Save current state
agent-browser state load auth.json       # Load state
agent-browser state list                 # List all saved states
agent-browser state show myapp.json      # Inspect state contents
agent-browser state rename old.json new.json
agent-browser state clear myapp          # Delete specific state
agent-browser state clean --older-than 7 # Clean states older than 7 days
```

### State Encryption

```bash
# Generate encryption key (AES-256-GCM, 64-char hex)
export AGENT_BROWSER_ENCRYPTION_KEY=$(openssl rand -hex 32)
agent-browser --session-name secure open https://app.example.com
```

### Auto-Expiration

```bash
export AGENT_BROWSER_STATE_EXPIRE_DAYS=30  # Default: 30 days
```

### Cleanup

Always close sessions when done to avoid leaked processes:

```bash
agent-browser close                    # Close default session
agent-browser --session agent1 close   # Close specific session
```

If a previous session was not closed properly, use `agent-browser close` to clean up.

---

## 8. Authentication

### Auth Vault (Recommended)

Encrypted credential storage. LLM never sees passwords.

```bash
# Save credentials — pipe password via stdin to avoid shell history exposure
echo "pass" | agent-browser auth save github \
  --url https://github.com/login \
  --username user \
  --password-stdin

# Login using saved profile
agent-browser auth login github

# Manage profiles
agent-browser auth list
agent-browser auth show github
agent-browser auth delete github
```

### State-Based Authentication

Login once and reuse state in future sessions.

```bash
# Login and save state
agent-browser open https://app.example.com/login
agent-browser snapshot -i
agent-browser fill @e1 "$USERNAME"
agent-browser fill @e2 "$PASSWORD"
agent-browser click @e3
agent-browser wait --url "**/dashboard"
agent-browser state save auth.json

# Reuse in future sessions
agent-browser state load auth.json
agent-browser open https://app.example.com/dashboard
```

### Custom Headers

`--headers` are scoped to the origin for authenticated sessions.

```bash
agent-browser --headers '{"Authorization":"Bearer token123"}' open https://api.example.com
```

---

## 9. Configuration

### Config Files

| Source | Path | Priority |
|--------|------|----------|
| User config | `~/.agent-browser/config.json` | Lowest |
| Project config | `./agent-browser.json` | Higher |
| Environment variables | `AGENT_BROWSER_*` | Higher |
| CLI flags | `--flag` | Highest |

Custom config: `--config <path>` or `AGENT_BROWSER_CONFIG` env var.

### Example Config

```json
{
  "headed": true,
  "proxy": "http://localhost:8080",
  "profile": "./browser-data",
  "colorScheme": "dark",
  "maxOutput": 50000
}
```

All CLI options map to camelCase keys (e.g., `--executable-path` → `"executablePath"`). Boolean flags accept `true`/`false`. Extensions from user and project configs are merged, not replaced.

### Key Environment Variables

| Variable | Description |
|----------|-------------|
| `AGENT_BROWSER_EXECUTABLE_PATH` | Path to browser binary |
| `AGENT_BROWSER_HEADED` | `1` to enable headed mode |
| `AGENT_BROWSER_COLOR_SCHEME` | `dark` or `light` |
| `AGENT_BROWSER_DEFAULT_TIMEOUT` | Timeout in ms (default 25000) |
| `AGENT_BROWSER_MAX_OUTPUT` | Max output characters |
| `AGENT_BROWSER_ALLOWED_DOMAINS` | Comma-separated domain allowlist |
| `AGENT_BROWSER_ACTION_POLICY` | Path to action policy JSON |
| `AGENT_BROWSER_CONTENT_BOUNDARIES` | `1` to enable content boundaries |
| `AGENT_BROWSER_ENCRYPTION_KEY` | 64-char hex key for state encryption |
| `AGENT_BROWSER_STATE_EXPIRE_DAYS` | State auto-expiration (default 30) |
| `AGENT_BROWSER_STREAM_PORT` | WebSocket streaming port |
| `AGENT_BROWSER_CONFIG` | Path to custom config file |
| `AGENT_BROWSER_NATIVE` | `1` to enable native Rust daemon |
| `AGENT_BROWSER_ENGINE` | Browser engine (`chrome`, `lightpanda`) |
| `AGENT_BROWSER_CONFIRM_ACTIONS` | `1` to require action confirmation |

---

## 10. Network Interception

```bash
# Intercept and modify network requests
agent-browser network route "**/*.jpg" --abort          # Block all JPEG images
agent-browser network route "**/api/data" --body mock.json  # Respond with mock data
agent-browser network unroute "**/*.jpg"                # Remove route

# Monitor requests
agent-browser network requests                          # List all captured requests
agent-browser network requests --filter "**/api/**"     # Filter by pattern
agent-browser network requests --clear                  # Clear request log
```

---

## 11. Tabs, Frames, and Dialogs

### Tabs & Windows

```bash
agent-browser tab list                     # List open tabs
agent-browser tab new https://other.com    # Open new tab
agent-browser tab switch 1                 # Switch to tab by index
agent-browser tab close                    # Close current tab
agent-browser tab close 2                  # Close tab by index
agent-browser window new https://other.com # Open new window
```

### Frames (iframes)

```bash
agent-browser frame switch "#iframe-id"    # Switch to iframe
agent-browser snapshot -i                  # Snapshot within frame
agent-browser click @e1                    # Interact within frame
agent-browser frame main                   # Return to main frame
```

### Dialogs

```bash
# Handle JavaScript alert/confirm/prompt dialogs
agent-browser dialog accept               # Accept (OK/Yes)
agent-browser dialog accept "input text"   # Accept with input (for prompt)
agent-browser dialog dismiss              # Dismiss (Cancel/No)
```

---

## 12. Mouse Control

For precise mouse interactions (canvas, drag-and-drop, games):

```bash
agent-browser mouse move 100 200          # Move to coordinates
agent-browser mouse down                  # Press button
agent-browser mouse up                    # Release button
agent-browser mouse wheel 0 500           # Scroll (dx, dy)
```

### Drag and Drop

```bash
agent-browser drag @e1 @e2               # Drag from source to destination
```

---

## 13. Diffing (Verifying Changes)

### Snapshot Diff

Compare accessibility tree between two points. Uses `+` for additions and `-` for removals (git diff style).

```bash
# Typical workflow: snapshot → action → diff
agent-browser snapshot -i              # Take baseline snapshot
agent-browser click @e2                # Perform action
agent-browser diff snapshot            # See what changed (auto-compares to last snapshot)

# Compare against a saved baseline
agent-browser diff snapshot --baseline before.txt
```

### Screenshot Diff

Pixel-level visual diff. Changed pixels highlighted in red, plus a mismatch percentage.

```bash
agent-browser screenshot baseline.png
# ... changes happen ...
agent-browser diff screenshot --baseline baseline.png
```

### URL Diff

Compare two pages side-by-side.

```bash
agent-browser diff url https://staging.example.com https://prod.example.com
agent-browser diff url <url1> <url2> --wait-until networkidle
agent-browser diff url <url1> <url2> --selector "#main"
```

---

## 14. CDP Mode and Cloud Providers

### Connect to Existing Browser

```bash
# Auto-discover running Chrome with remote debugging
agent-browser --auto-connect open https://example.com
agent-browser --auto-connect snapshot

# Explicit CDP port
agent-browser --cdp 9222 snapshot

# WebSocket URL
agent-browser --cdp "wss://browser.example.com" snapshot

# Connect command
agent-browser connect 9222
agent-browser connect "wss://browser.example.com"
```

### Cloud Providers

Use `-p` flag to connect to cloud browser providers:

```bash
agent-browser -p browserbase open https://example.com
agent-browser -p browseruse open https://example.com
agent-browser -p kernel open https://example.com
```

---

## 15. Streaming

WebSocket streaming for pair browsing, remote preview, and recording.

```bash
# Enable streaming
export AGENT_BROWSER_STREAM_PORT=9223
agent-browser open https://example.com
# Connect WebSocket client to ws://localhost:9223
```

### Message Types

- **Frame messages**: base64-encoded JPEG frames
- **Status messages**: browser state updates

### Input Injection

Supports remote input: mouse events, keyboard events, touch events.

---

## 16. iOS Simulator

Mobile Safari automation on macOS with Xcode.

```bash
# Launch Safari on iOS simulator
agent-browser -p ios --device "iPhone 16 Pro" open https://example.com

# Same workflow — snapshot, interact, re-snapshot
agent-browser -p ios snapshot -i
agent-browser -p ios click @e1
agent-browser -p ios fill @e2 "text"

# Mobile-specific gestures
agent-browser -p ios swipe up
agent-browser -p ios swipe down
agent-browser -p ios swipe left
agent-browser -p ios swipe right
agent-browser -p ios tap @e1                # Alias for click

# Screenshot
agent-browser -p ios screenshot mobile.png

# Close (shuts down simulator)
agent-browser -p ios close
```

**Requirements:** macOS + Xcode + Appium + XCUITest driver:
```bash
npm install -g appium && appium driver install xcuitest
```

**Real devices:** Physical iOS devices via USB. Use `--device "<UDID>"` where UDID is from `xcrun xctrace list devices`. Requires WebDriverAgent signing.

---

## 17. Native Mode (Experimental)

Pure Rust daemon using direct CDP. No Node.js or Playwright needed.

```bash
# Enable via flag
agent-browser --native open example.com

# Enable via environment variable
export AGENT_BROWSER_NATIVE=1
agent-browser open example.com
```

**Supports:** Chromium + Safari (via WebDriver).

**Known limitations:**
- No Firefox or WebKit support
- No Playwright traces
- No HAR recording

Use `agent-browser close` before switching between native and default mode within the same session.

---

## 18. Security Features

All security features are opt-in. By default, agent-browser imposes no restrictions.

### Content Boundaries

Wrap page-sourced output in markers with CSPRNG nonce to help LLMs distinguish tool output from untrusted page content.

```bash
export AGENT_BROWSER_CONTENT_BOUNDARIES=1
agent-browser snapshot
# --- AGENT_BROWSER_PAGE_CONTENT nonce=<hex> origin=https://example.com ---
# [accessibility tree]
# --- END_AGENT_BROWSER_PAGE_CONTENT nonce=<hex> ---
```

### Domain Allowlist

Restrict navigation and sub-resource loading to trusted domains. Wildcards `*.example.com` also match bare `example.com`. Blocks navigation, sub-resources, WebSocket, and EventSource to non-allowed domains.

```bash
export AGENT_BROWSER_ALLOWED_DOMAINS="example.com,*.example.com,cdn.example.net"
agent-browser open https://example.com        # OK
agent-browser open https://malicious.com       # Blocked
```

Include CDN domains your target pages depend on.

### Action Policy

Gate destructive actions with a policy file. 13 action categories available.

```bash
export AGENT_BROWSER_ACTION_POLICY=./policy.json
```

Example `policy.json`:
```json
{"default": "deny", "allow": ["navigate", "snapshot", "click", "scroll", "wait", "get"]}
```

Auth vault operations (`auth login`, etc.) bypass action policy. Domain allowlist still applies.

### Action Confirmation

Require explicit confirmation before actions execute.

```bash
agent-browser --confirm-actions open https://example.com
# Actions pause and wait for confirmation
agent-browser confirm    # Approve pending action
agent-browser deny       # Deny pending action
```

Use `--confirm-interactive` for interactive confirmation mode.

### Output Limits

Prevent context flooding from large pages:

```bash
export AGENT_BROWSER_MAX_OUTPUT=50000
```

---

## 19. Profiling and Debugging

### Chrome DevTools Profiler

```bash
agent-browser profiler start                   # Start profiling
agent-browser profiler stop trace.json         # Stop and save (path optional)
agent-browser profiler start --categories "devtools.timeline,v8"  # Custom trace categories
```

Output in Chrome Trace Event format. View in Chrome DevTools, Perfetto, or `chrome://tracing`.

### Playwright Traces

```bash
agent-browser trace start
# ... perform actions ...
agent-browser trace stop
```

### Console & Errors

```bash
agent-browser console                          # Show browser console messages
agent-browser errors                           # Show page errors
```

### Visual Debugging

```bash
agent-browser --headed open https://example.com  # Visible browser window
agent-browser highlight @e1                      # Highlight element visually
```

Use `AGENT_BROWSER_HEADED=1` for headed mode via environment variable. Browser extensions work in both headed and headless mode.

### Debug Flag

```bash
agent-browser --debug open https://example.com  # Verbose debug output
```

---

## 20. Command Chaining

Commands can be chained with `&&` in a single shell invocation. The browser persists between commands via a background daemon.

```bash
# Chain open + wait + snapshot in one call
agent-browser open https://example.com && agent-browser wait --load networkidle && agent-browser snapshot -i

# Chain multiple interactions
agent-browser fill @e1 "user@example.com" && agent-browser fill @e2 "password123" && agent-browser click @e3

# Navigate and capture
agent-browser open https://example.com && agent-browser wait --load networkidle && agent-browser screenshot page.png
```

**When to chain:** Use `&&` when you don't need to read intermediate output (e.g., open + wait + screenshot). Run commands separately when you need to parse output first (e.g., snapshot to discover refs, then interact).

---

## 21. JSON Output

Use `--json` for machine-parseable output:

```bash
agent-browser snapshot -i --json
agent-browser get text @e1 --json
agent-browser get url --json
agent-browser cookies get --json
agent-browser tab list --json
agent-browser session list --json
```

---

## 22. JavaScript Evaluation (eval)

Shell quoting can corrupt complex expressions. Use `--stdin` or `-b` to avoid issues.

```bash
# Simple expressions — single quotes are fine
agent-browser eval 'document.title'
agent-browser eval 'document.querySelectorAll("img").length'

# Complex JS — use --stdin with heredoc (RECOMMENDED)
agent-browser eval --stdin <<'EVALEOF'
JSON.stringify(
  Array.from(document.querySelectorAll("img"))
    .filter(i => !i.alt)
    .map(i => ({ src: i.src.split("/").pop(), width: i.width }))
)
EVALEOF

# Programmatic/generated scripts — use base64
agent-browser eval -b "$(echo -n 'Array.from(document.querySelectorAll("a")).map(a => a.href)' | base64)"
```

**Rules of thumb:**
- Single-line, no nested quotes → regular `eval 'expression'`
- Nested quotes, arrow functions, template literals, multiline → `eval --stdin <<'EVALEOF'`
- Programmatic/generated scripts → `eval -b` with base64

---

## 23. Browser Engine Selection

```bash
# Chrome (default) — auto-discovered or installed via `agent-browser install`
agent-browser open example.com

# Lightpanda — 10x faster, 10x less memory, headless only
agent-browser --engine lightpanda open example.com

# Via environment variable
export AGENT_BROWSER_ENGINE=lightpanda
agent-browser open example.com

# Custom binary path
agent-browser --engine lightpanda --executable-path /path/to/lightpanda open example.com
```

**Chrome:** Supports extensions, profiles, headed mode, `--allow-file-access`.

**Lightpanda:** Does not support `--extension`, `--profile`, `--state`, or `--allow-file-access`. Limited feature set. Headless only.

---

## 24. Local Files

```bash
agent-browser --allow-file-access open file:///path/to/document.pdf
agent-browser --allow-file-access open file:///path/to/page.html
agent-browser screenshot output.png
```

---

## 25. Viewport & Device Emulation

```bash
# Set viewport size (default: 1280x720)
agent-browser set viewport 1920 1080

# Retina/HiDPI — same CSS layout, higher pixel density
agent-browser set viewport 1920 1080 2

# Device emulation (sets viewport + user agent)
agent-browser set device "iPhone 14"
```

The `scale` parameter (3rd argument) sets `window.devicePixelRatio` without changing CSS layout. Use for retina testing or higher-resolution screenshots.

---

## 26. Color Scheme

```bash
# Via flag
agent-browser --color-scheme dark open https://example.com

# Via environment variable
AGENT_BROWSER_COLOR_SCHEME=dark agent-browser open https://example.com

# During session
agent-browser set media dark
```

---

## 27. Global Options Reference

| Flag | Description |
|------|-------------|
| `--session <name>` | Isolated browser session |
| `--session-name <name>` | Auto-save/restore session state |
| `--profile <path>` | Persistent browser profile directory |
| `--state <path>` | Load state file on start |
| `--headers <json>` | Extra HTTP headers (origin-scoped) |
| `--executable-path <path>` | Custom browser binary |
| `--extension <path>` | Load browser extension |
| `--args <args>` | Additional browser launch arguments |
| `--user-agent <string>` | Custom user agent |
| `--proxy <url>` | HTTP/SOCKS proxy |
| `--proxy-bypass <list>` | Proxy bypass list |
| `--ignore-https-errors` | Ignore SSL/TLS errors |
| `--allow-file-access` | Allow `file://` URLs |
| `-p, --provider <name>` | Browser provider (ios, browserbase, browseruse, kernel) |
| `--device <name>` | Device to emulate |
| `--json` | JSON output |
| `--full, -f` | Full page (screenshot/snapshot) |
| `--annotate` | Annotated screenshot with element labels |
| `--headed` | Show browser window |
| `--cdp <port\|url>` | Connect via CDP |
| `--auto-connect` | Auto-discover running Chrome |
| `--color-scheme <scheme>` | Color scheme (dark/light) |
| `--download-path <path>` | Default download directory |
| `--content-boundaries` | Enable output content markers |
| `--max-output <chars>` | Max output character limit |
| `--allowed-domains <list>` | Domain allowlist (comma-separated) |
| `--action-policy <path>` | Action policy JSON file |
| `--confirm-actions` | Require action confirmation |
| `--confirm-interactive` | Interactive confirmation mode |
| `--config <path>` | Custom config file path |
| `--native` | Use native Rust daemon (experimental) |
| `--engine <name>` | Browser engine (chrome, lightpanda) |
| `--debug` | Verbose debug output |

---

## 28. Common Patterns

### Form Submission

```bash
agent-browser open https://example.com/signup
agent-browser snapshot -i
agent-browser fill @e1 "Jane Doe"
agent-browser fill @e2 "jane@example.com"
agent-browser select @e3 "California"
agent-browser check @e4
agent-browser click @e5
agent-browser wait --load networkidle
agent-browser snapshot -i  # Verify result
```

### Data Extraction

```bash
agent-browser open https://example.com/products
agent-browser snapshot -i
agent-browser get text @e5                   # Get specific element text
agent-browser get text body > page.txt       # Get all page text
agent-browser snapshot -i --json             # JSON output for parsing
```

### Multi-Account Testing

```bash
agent-browser --session admin open https://app.com/login
# ... login as admin ...
agent-browser --session user open https://app.com/login
# ... login as user ...
agent-browser --session admin snapshot -i    # Check admin view
agent-browser --session user snapshot -i     # Check user view
```

### Connect to Existing Chrome

```bash
agent-browser --auto-connect open https://example.com
agent-browser --auto-connect snapshot
# Or with explicit CDP port
agent-browser --cdp 9222 snapshot
```

---

## 29. Architecture

1. **Rust CLI** — Parses commands, communicates with daemon
2. **Node.js Daemon** (default) — Manages Playwright browser instance
3. **Native Daemon** (experimental, `--native`) — Pure Rust daemon using direct CDP, no Node.js/Playwright

---

## 30. Deep-Dive Reference Files

| File | When to Use |
|------|-------------|
| `references/commands.md` | Complete command reference with all 50+ commands, syntax, flags, and examples |
| `references/selectors.md` | Ref-based, CSS, text/XPath, and semantic locator selection strategies |
| `references/snapshots.md` | Snapshot options (-i/-C/-c/-d/-s), output format, ref lifecycle, annotated screenshots |
| `references/configuration.md` | Config file locations, priority chain, all configurable options, environment variables |
| `references/installation.md` | Global, npx, project, Homebrew, source install, serverless, AI agent setup |
| `references/sessions.md` | Session isolation, persistence, encryption, state management, auth headers |
| `references/authentication.md` | Auth vault, header-based auth, state persistence, profiles, HTTP basic auth |
| `references/security.md` | Threat model, auth vault, content boundaries, domain allowlist, action policy, confirmation |
| `references/diffing.md` | Snapshot diff, screenshot diff, URL diff — all options and use cases |
| `references/cdp-mode.md` | CDP connections, WebSocket URLs, auto-connect, cloud providers (browserbase, browseruse, kernel) |
| `references/streaming.md` | WebSocket streaming protocol, frame/status messages, input events, TypeScript API |
| `references/profiling.md` | Performance profiling commands, categories, output format, viewing results |
| `references/ios-simulator.md` | iOS Simulator setup, device list, swipe/tap commands, real device support |
| `references/native-mode.md` | Experimental native Rust daemon, CDP-based, supported commands, limitations |
| `references/engines.md` | Chrome engine discovery/config, Lightpanda engine (Zig-based, 10x faster) |
| `references/nextjs-vercel.md` | Vercel Sandbox integration, server actions, ephemeral microVMs |
| `references/troubleshooting.md` | Common issues: daemon, browser, Linux deps, containers, CDP, state, iOS |

---

## 31. Ready-to-Use Templates

| Template | Purpose |
|----------|---------|
| `templates/authenticated-session.sh` | Login flow with state persistence |
| `templates/form-automation.sh` | Form filling and submission workflow |
| `templates/capture-workflow.sh` | Page capture with screenshots and snapshots |
| `templates/e2e-test-workflow.sh` | End-to-end test execution pattern |
| `templates/data-extraction.sh` | Structured data extraction with pagination |
| `templates/visual-regression.sh` | Visual regression testing using diff commands |

```bash
./templates/authenticated-session.sh https://app.example.com user@example.com password123
./templates/form-automation.sh https://example.com/contact
./templates/capture-workflow.sh https://example.com ./captures
./templates/e2e-test-workflow.sh https://example.com ./test-results
./templates/data-extraction.sh https://example.com/products ./output
./templates/visual-regression.sh https://staging.example.com https://prod.example.com ./diffs
```
