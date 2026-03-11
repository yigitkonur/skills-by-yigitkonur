# Debugging Guide

## Headed Mode (Visual Debugging)

Run automation with a visible browser window to watch actions in real time:

```bash
# Via CLI flag
agent-browser --headed open https://example.com

# Via environment variable (persists across commands)
export AGENT_BROWSER_HEADED=1
agent-browser open https://example.com
```

Headed mode is invaluable when:
- An element click produces no visible effect
- You need to see animation/transition timing
- Debugging authentication flows with redirects
- Verifying visual state during automation

## Console & Error Capture

### Browser Console Logs

```bash
# View all console output (log, warn, error, info)
agent-browser console

# Clear accumulated console messages
agent-browser console --clear
```

Console output accumulates across page navigations within a session. Clear it before a specific action to isolate its console output.

### JavaScript Errors

```bash
# View only JavaScript errors (uncaught exceptions, failed assertions)
agent-browser errors

# Clear error log
agent-browser errors --clear
```

**Pattern: Capture errors around an action**

```bash
agent-browser errors --clear           # Start clean
agent-browser click @e3                # Perform action
ERRORS=$(agent-browser errors)         # Check for errors
if [ -n "$ERRORS" ]; then
  echo "JS errors after click: $ERRORS"
  agent-browser screenshot error-state.png
fi
```

## Element Highlighting

Visually highlight elements to confirm which element a ref or selector points to:

```bash
# Highlight by ref (requires --headed)
agent-browser --headed open https://example.com
agent-browser snapshot -i
agent-browser highlight @e3    # Element gets a colored overlay

# Highlight by CSS selector
agent-browser highlight ".submit-button"
```

Use highlighting when snapshot output is ambiguous (multiple similar elements) or when you need to verify an element's position on the page.

## Trace Recording (Playwright Trace)

Traces capture a complete timeline of every action, DOM snapshot, network request, and console log. They can be viewed in the Playwright Trace Viewer for post-mortem debugging.

### Basic Trace Workflow

```bash
agent-browser trace start

# Perform your automation
agent-browser open https://example.com
agent-browser snapshot -i
agent-browser click @e1
agent-browser wait --load networkidle

agent-browser trace stop trace.zip
```

### Viewing Traces

```bash
# Open in Playwright Trace Viewer (interactive timeline)
npx playwright show-trace trace.zip

# Or upload to trace.playwright.dev in a browser
```

The trace viewer shows:
- **Timeline** of all actions with timestamps
- **DOM snapshots** before and after each action
- **Network requests** with headers, body, and timing
- **Console logs** correlated to actions
- **Screenshots** at each step

### When to Use Traces

- Debugging intermittent failures (race conditions, timing issues)
- Understanding complex redirect chains
- Analyzing network request patterns
- Sharing reproducible bug reports with teammates

## Video Recording for Debug

```bash
# Record the entire automation session
agent-browser record start debug-session.webm

# Perform actions...
agent-browser open https://example.com
agent-browser snapshot -i
agent-browser click @e1

# Stop and save
agent-browser record stop
```

Add short pauses between actions for more readable recordings:

```bash
agent-browser click @e1
agent-browser wait 500        # Pause for human viewing
agent-browser fill @e2 "text"
agent-browser wait 500
```

## State Checks (Pre-Interaction Validation)

Before interacting with an element, validate its state to avoid cryptic errors:

```bash
# Is the element visible on screen?
agent-browser is visible @e1      # true / false

# Is the element enabled (not disabled)?
agent-browser is enabled @e1      # true / false

# Is a checkbox/radio checked?
agent-browser is checked @e1      # true / false

# Programmatic checks with JSON output
ENABLED=$(agent-browser is enabled @e1 --json | jq -r '.enabled')
if [ "$ENABLED" = "false" ]; then
  echo "Button is disabled, waiting..."
  agent-browser wait --fn "document.querySelector('button').disabled === false"
fi
```

## Debug Verbose Output

```bash
# Enable verbose debug logging
agent-browser --debug open https://example.com

# Shows: command parsing, daemon communication, Playwright calls, timing
```

## Chrome DevTools Profiling

For performance debugging, use the built-in profiler:

```bash
agent-browser profiler start

# Perform the slow action
agent-browser open https://slow-page.example.com
agent-browser wait --load networkidle

agent-browser profiler stop ./slow-page-trace.json

# View in Chrome DevTools: chrome://tracing
# Or in Perfetto UI: https://ui.perfetto.dev
```

### Custom Profiling Categories

```bash
# Profile specific categories (comma-separated)
agent-browser profiler start --categories "devtools.timeline,v8.execute,blink.user_timing"

# Profile with disabled-by-default categories for deep analysis
agent-browser profiler start --categories "disabled-by-default-devtools.timeline,disabled-by-default-v8.cpu_profiler"
```

## Common Issues & Solutions

### Element Not Found (`ref @eN not found`)

**Cause:** Refs were invalidated by navigation or DOM changes.

```bash
# Solution: Re-snapshot to get fresh refs
agent-browser snapshot -i
# Use new refs from output
```

### Element Not Visible

**Cause:** Element exists in DOM but is offscreen or hidden.

```bash
# Solution: Scroll to element first
agent-browser scroll down 500
agent-browser snapshot -i

# Or scope snapshot to a specific container
agent-browser snapshot -i -s "#main-content"
```

### Click Has No Effect

**Cause:** Element is disabled, overlapped, or handled by JavaScript.

```bash
# Check if enabled
agent-browser is enabled @e1

# Try force click (bypasses actionability checks)
agent-browser click @e1 --force

# Try JavaScript click as fallback
agent-browser eval 'document.querySelector("button.submit").click()'

# Check for overlapping elements (modals, tooltips)
agent-browser snapshot -i  # Look for overlay elements
```

### Form Not Submitting

**Cause:** Client-side validation, missing required fields, or AJAX submission.

```bash
# Check for validation errors after submit attempt
agent-browser snapshot -i
agent-browser get text ".error-message"

# Try pressing Enter instead of clicking submit
agent-browser press Enter

# Wait for network after form submission
agent-browser click @e5
agent-browser wait --load networkidle
```

### Authentication Redirect Loop

**Cause:** Session/cookies not persisting, or token expired.

```bash
# Save state after successful login
agent-browser state save auth-state.json

# On next run, load state and verify
agent-browser state load auth-state.json
agent-browser open https://app.example.com/dashboard
CURRENT_URL=$(agent-browser get url)

# If redirected to login, state is stale
if echo "$CURRENT_URL" | grep -q "login"; then
  echo "Auth state expired, re-authenticating..."
  rm auth-state.json
  # Re-run login flow
fi
```

### SSL/Certificate Errors

```bash
# Ignore HTTPS errors (development/staging environments only)
agent-browser --ignore-https-errors open https://self-signed.example.com
```

### Stale Daemon / Port Conflict

```bash
# Close any existing sessions
agent-browser close

# If that fails, the daemon may be stale
# Check for running processes
ps aux | grep agent-browser

# Kill stale daemon by PID
kill <PID>
```

### CI/CD Environment Issues

```bash
# Ensure Chromium dependencies are installed (Linux)
npx playwright install-deps chromium

# Use headless mode (default) in CI
# Increase timeout for slower CI environments
export AGENT_BROWSER_DEFAULT_TIMEOUT=60000

# Set a fixed viewport for consistent screenshots
agent-browser set viewport 1280 720
```
