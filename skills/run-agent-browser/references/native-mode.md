# Native Mode (Experimental)

Experimental native Rust daemon communicating with Chrome directly via CDP, eliminating Node.js and Playwright dependencies.

## Enabling

- CLI flag: `agent-browser --native open example.com`
- Environment: `export AGENT_BROWSER_NATIVE=1`
- Config: `{"native": true}` in agent-browser.json

## Architecture Comparison

| | Default (Node.js) | Native (--native) |
|---|---|---|
| Runtime | Node.js + Playwright | Pure Rust binary |
| Protocol | Playwright protocol | Direct CDP / WebDriver |
| Install size | Larger (Node.js + npm deps) | Smaller (single binary) |
| Browser support | Chromium, Firefox, WebKit | Chromium, Safari (via WebDriver) |
| Stability | Stable | Experimental |

## What Works

All core commands: navigation, interaction (click, fill, type, press, hover, scroll, drag), observation (snapshot, screenshot, eval), state management (cookies, storage, state save/load), tabs, emulation (viewport, device, timezone, locale, geolocation), streaming, diffing, recording, profiling.

## Known Limitations

- Firefox and WebKit not supported (Chromium and Safari only)
- Playwright trace format not available (uses Chrome's built-in tracing)
- HAR export not available
- Network route interception uses CDP Fetch domain instead of Playwright's route API

## Switching Between Modes

Native and Node.js daemons share same session socket. Cannot run simultaneously.

```bash
agent-browser close
export AGENT_BROWSER_NATIVE=1
agent-browser open example.com
```
