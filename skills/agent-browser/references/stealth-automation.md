# Stealth & Anti-Bot Automation

Techniques for automating bot-protected websites. Use when standard headless automation triggers detection (Cloudflare, reCAPTCHA, Akamai, PerimeterX, etc.).

## When to Use Stealth

Only use these techniques when necessary:
- ❌ Internal tools, staging environments, sites you control → use standard mode
- ✅ Sites with active bot detection that blocks automation

## Core Principles

1. **Headed mode** — renders full browser UI, avoids headless detection signals
2. **Session persistence** — reuses browser state to avoid cold-start fingerprints
3. **Human-like pacing** — randomized delays between actions
4. **Region alignment** — match locale, timezone, and geolocation to target site

## Headed Mode

Bot detectors flag headless browsers via missing GPU compositing, absent window dimensions, and navigator properties. Headed mode avoids all of these:

```bash
# Via flag
agent-browser --headed open https://example.com

# Via environment variable (persistent across commands)
export AGENT_BROWSER_HEADED=1
agent-browser open https://example.com
```

Always combine with a named session for state persistence:

```bash
agent-browser --headed --session-name shop open https://shop.example.com
```

## Human-Like Typing

Instant field population (< 1ms per character) is a strong bot signal. Add per-character delays:

```bash
# 120ms per character — realistic typing speed (~50 WPM)
agent-browser fill @e1 "search query" --delay 120

# Slower for sensitive fields (password, credit card)
agent-browser fill @e2 "4242424242424242" --delay 150

# Keyboard mode for contenteditable / rich text editors
agent-browser keyboard type "Hello world" --delay 90
```

## Randomized Waits

Fixed delays (always exactly 2000ms) are themselves a detection signal. Use range-based waits:

```bash
# Random wait between 1.2s and 2.6s
agent-browser wait 1200-2600

# Between actions — vary the range
agent-browser click @e1
agent-browser wait 800-1500
agent-browser fill @e2 "text" --delay 100
agent-browser wait 1000-2000
agent-browser click @e3
agent-browser wait 1500-3500
```

## Session Reuse

Each new browser session creates a fresh fingerprint — cold starts trigger extra scrutiny. Reuse sessions:

```bash
# First visit — login and let state persist
agent-browser --headed --session-name shop open https://shop.example.com/login
agent-browser snapshot -i
agent-browser fill @e1 "user@example.com" --delay 100
agent-browser fill @e2 "password" --delay 120
agent-browser click @e3
agent-browser wait --url "**/dashboard"
agent-browser close  # State auto-saved with session name

# Later visits — state auto-restored (cookies, localStorage, etc.)
agent-browser --headed --session-name shop open https://shop.example.com/dashboard
# Already logged in — no cold-start fingerprint
```

## Region-Aware Automation

For region-locked sites (Shopee, TikTok, regional e-commerce), align browser locale and geolocation:

```bash
# Set geolocation
agent-browser set geo 25.0330 121.5654  # Taipei

# Navigate to regional domain
agent-browser --headed --session-name tw open https://shopee.tw

# Combine with proxy for IP alignment
export AGENT_BROWSER_PROXY="http://tw-proxy.example.com:8080"
agent-browser --headed open https://shopee.tw
```

## Stealth Workflow Template

```bash
#!/usr/bin/env bash
# stealth-session.sh — Automate a bot-protected site
set -euo pipefail

SITE_URL="${1:?Usage: stealth-session.sh <url>}"
SESSION="stealth-$(echo "$SITE_URL" | md5sum | cut -c1-8)"

# Headed mode + persistent session + human pacing
agent-browser --headed --session-name "$SESSION" open "$SITE_URL"
agent-browser wait --load networkidle
agent-browser wait 2000-4000  # Initial settling time

# Discover and interact
agent-browser snapshot -i
agent-browser fill @e1 "search query" --delay 110
agent-browser wait 800-1500
agent-browser click @e2
agent-browser wait --load networkidle
agent-browser wait 1500-3000

# Capture results
agent-browser snapshot -i
agent-browser screenshot results.png

agent-browser close
```

## Anti-Detection Checklist

| Technique | Command/Config |
|-----------|---------------|
| Headed mode | `--headed` or `AGENT_BROWSER_HEADED=1` |
| Session persistence | `--session-name <name>` |
| Typing delay | `--delay 100-150` on `fill`/`type` |
| Random waits | `wait 1000-3000` between actions |
| Geolocation | `set geo <lat> <lon>` |
| Proxy | `AGENT_BROWSER_PROXY=http://...` |
| Custom user agent | `--user-agent "Mozilla/5.0..."` |
| Real viewport | `agent-browser viewport 1920 1080` |
