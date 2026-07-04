# Advanced — providers, stealth, proxy, profiling, video, install, engines

Everything the 80% scenarios in SKILL.md do not need. Read the section you actually need and skip the rest.

**Related:** `commands.md` for full flag reference, `safety.md` for risk policy, `sessions-and-refs.md` for session/profile lifecycle.

---

## Installation and platform support

### Quick install

```bash
npm install -g agent-browser            # global (native Rust binary preferred)
agent-browser install                    # downloads Chromium

# alternatives
brew install agent-browser               # macOS
cargo install agent-browser              # Rust toolchain
npx agent-browser open example.com       # ad hoc, no install
```

### Linux system dependencies

```bash
agent-browser install --with-deps
# or
npx playwright install-deps chromium
```

### Pinning for production / CI

```bash
npm install -g agent-browser@0.31.1
agent-browser --version
```

### Verify

```bash
agent-browser --version
agent-browser open https://example.com
agent-browser snapshot -i
agent-browser close
```

### Configuration precedence (low → high)

1. Built-in defaults.
2. `~/.agent-browser/config.json` — user-level.
3. `./agent-browser.json` — project-level.
4. Environment variables (`AGENT_BROWSER_*`).
5. CLI flags.

Example `agent-browser.json`:

```json
{
  "headed": false,
  "defaultTimeout": 30000,
  "proxy": "http://proxy.example.com:8080",
  "colorScheme": "dark",
  "viewport": { "width": 1280, "height": 720 },
  "profile": "~/.agent-browser/profile"
}
```

### Docker

```dockerfile
FROM node:20-slim
RUN apt-get update && apt-get install -y \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libxcomposite1 libxdamage1 libxrandr2 \
    libgbm1 libasound2 libpangocairo-1.0-0 libgtk-3-0 \
  && rm -rf /var/lib/apt/lists/*
RUN npm install -g agent-browser@0.31.1 && agent-browser install
RUN useradd -m agent
USER agent
```

### GitHub Actions

```yaml
- name: Install agent-browser
  run: |
    npm install -g agent-browser@0.31.1
    agent-browser install --with-deps

- name: Run browser checks
  run: |
    agent-browser open http://localhost:3000
    agent-browser wait --load networkidle
    agent-browser snapshot -i
    agent-browser screenshot ./results/home.png
    agent-browser close
```

---

## Cloud browser providers

The CLI command surface is identical — only the browser backend changes. Cloud providers handle lifecycle, scaling, geo-distribution, and (Kernel especially) anti-bot.

```bash
# Browserbase — generic cloud Chrome
agent-browser -p browserbase open https://example.com
# env: BROWSERBASE_API_KEY   (BROWSERBASE_PROJECT_ID no longer required as of v0.18.0)
# note: Browserbase is Chromium-only, no extensions/profile dirs, ~10s default timeout

# BrowserUse — agent-oriented hosted browser
agent-browser -p browseruse open https://example.com
# env: BROWSER_USE_API_KEY

# Kernel — cloud browser provider (managed auth, stealth)
agent-browser -p kernel open https://example.com
# env: KERNEL_API_KEY  (optional: KERNEL_STEALTH, KERNEL_HEADLESS, KERNEL_PROFILE_NAME)

# Browserless
agent-browser -p browserless open https://example.com
# env: BROWSERLESS_API_KEY  (optional: BROWSERLESS_API_URL, BROWSERLESS_STEALTH)

# AWS Bedrock AgentCore
agent-browser -p agentcore open https://example.com
# env: AWS creds (AWS_PROFILE / standard AWS SDK vars) + AGENTCORE_REGION, AGENTCORE_BROWSER_ID

# iOS Simulator (see iOS section below)
agent-browser -p ios open https://example.com
```

To avoid repeating `-p`:

```bash
export AGENT_BROWSER_PROVIDER=browserbase
export BROWSERBASE_API_KEY=...
agent-browser open https://example.com
```

---

## Stealth and anti-bot

Use these only when needed. Internal tools, staging environments, sites you control → standard headless is fine.

### Core principles

1. Headed mode renders full browser UI and avoids most headless detection signals.
2. Session persistence avoids cold-start fingerprints.
3. Human-paced typing and randomized waits avoid robotic timing.
4. Locale, timezone, viewport, and geolocation should match the target's expected user.

### Headed mode

```bash
agent-browser --headed open https://example.com
# or persistently
export AGENT_BROWSER_HEADED=1
```

Combine with `--session NAME --restore` so state persists across cold starts:

```bash
agent-browser --headed --session shop open https://shop.example.com
```

### Human-paced typing

`type` and `keyboard type` are character-by-character. There is no built-in `--delay`. Add pacing inline between chunks:

```bash
agent-browser type @e1 "search"
agent-browser wait 300
agent-browser type @e1 " query"
```

### Randomized waits

A fixed `wait 2000` is itself a detection signal. Vary it:

```bash
agent-browser wait "$((1200 + RANDOM % 1401))"   # 1.2s – 2.6s
agent-browser click @e1
agent-browser wait "$((800  + RANDOM % 701))"
agent-browser type  @e2 "text"
agent-browser wait "$((1500 + RANDOM % 2001))"
```

### Region alignment

```bash
agent-browser set geo 25.0330 121.5654                 # Taipei
agent-browser --headed --session tw open https://shopee.tw
export AGENT_BROWSER_PROXY="http://tw-proxy.example.com:8080"
agent-browser --headed open https://shopee.tw
```

### Anti-detection checklist

| Technique | Command / config |
|---|---|
| Headed mode | `--headed` or `AGENT_BROWSER_HEADED=1` |
| Session persistence | `--session NAME` |
| Human-paced typing | `type` / `keyboard type` with `wait` between chunks |
| Random waits | `agent-browser wait "$((1000 + RANDOM % 2001))"` |
| Geolocation | `set geo LAT LON` |
| Proxy | `--proxy URL` or `AGENT_BROWSER_PROXY` |
| Custom UA | `--user-agent "..."` |
| Real viewport | `set viewport 1920 1080` |
| Stealth provider | `-p kernel` |

---

## Proxy support

Use `--proxy` or `AGENT_BROWSER_PROXY`. Prefer the agent-browser-specific env var over generic `HTTP_PROXY` / `HTTPS_PROXY` for unambiguous routing.

### Basic

```bash
agent-browser --proxy "http://proxy.example.com:8080" open https://example.com
# or
export AGENT_BROWSER_PROXY="http://proxy.example.com:8080"
agent-browser open https://example.com
```

### Authenticated proxy

```bash
export AGENT_BROWSER_PROXY="http://user:pass@proxy.example.com:8080"
agent-browser open https://example.com
```

### SOCKS

```bash
export AGENT_BROWSER_PROXY="socks5://proxy.example.com:1080"
# with auth
export AGENT_BROWSER_PROXY="socks5://user:pass@proxy.example.com:1080"
```

### Bypass

```bash
agent-browser --proxy "http://proxy.example.com:8080" \
              --proxy-bypass "localhost,*.internal.com" \
              open https://example.com
# or
export AGENT_BROWSER_PROXY_BYPASS="localhost,127.0.0.1,.internal.company.com"
```

### Verify

```bash
agent-browser open https://httpbin.org/ip
agent-browser get text body
# Should show the proxy's egress IP, not your real IP.
```

### Common pitfalls

- Some proxies do SSL inspection — `--ignore-https-errors` works for testing but never in production.
- Route CDN traffic direct via `--proxy-bypass` for performance.
- Test proxy connectivity with `curl -x ... https://httpbin.org/ip` before automating against it.

---

## iOS Simulator (Mobile Safari)

Run mobile Safari on macOS via the iOS Simulator (requires Xcode + Appium).

```bash
# Install Appium prerequisites
npm install -g appium
appium driver install xcuitest

# List devices
agent-browser -p ios device list

# Launch Safari on a specific device
agent-browser -p ios --device "iPhone 16 Pro" open https://example.com

# Same workflow as desktop — snapshot, interact, re-snapshot
agent-browser -p ios snapshot -i
agent-browser -p ios tap @e1          # tap is the click alias on iOS
agent-browser -p ios fill @e2 "text"
agent-browser -p ios swipe up         # mobile-specific gesture

agent-browser -p ios screenshot mobile.png
agent-browser -p ios close
```

Real devices work if pre-configured. Use `--device "<UDID>"` from `xcrun xctrace list devices`.

---

## Browser extensions

```bash
agent-browser --extension /path/to/ext1 --extension /path/to/ext2 open https://example.com
# or
export AGENT_BROWSER_EXTENSIONS="/path/to/ext1,/path/to/ext2"
```

User-level and project-level config extensions are merged (not replaced). Extensions work in both headed and headless. Not supported under `--engine lightpanda`.

---

## Custom browser executable

```bash
# System Chrome
agent-browser --executable-path /usr/bin/google-chrome open https://example.com

# AWS Lambda (@sparticuz/chromium)
CHROMIUM_PATH=$(node -e "console.log(require('@sparticuz/chromium').executablePath())")
agent-browser --executable-path "$CHROMIUM_PATH" open https://example.com

# Custom build
agent-browser --executable-path /opt/chromium/chrome open https://example.com
```

Sensitive — `--executable-path` lets you run an arbitrary binary. Approve narrowly.

---

## Engine selection (`--engine`)

```bash
# Chrome / Chromium (default)
agent-browser --engine chrome open https://example.com

# Lightpanda — ~10× faster, ~10× less memory, no JS-heavy support
agent-browser --engine lightpanda open https://example.com
# or
export AGENT_BROWSER_ENGINE=lightpanda
```

Lightpanda limitations: no `--extension`, no `--profile`, no `--state`, no `--allow-file-access`, partial JS support. Use for fast read-only / simple extraction only. Install from https://lightpanda.io/docs/open-source/installation.

---

## Native engine (default)

agent-browser is 100% native Rust by default — a daemon that talks to Chrome directly over CDP. The old Node.js + Playwright daemon has been removed, so there is no Node.js runtime to install and `--native` / `AGENT_BROWSER_NATIVE` are no longer needed (they're accepted as no-ops on current versions).

```bash
agent-browser open example.com   # already native; nothing to opt into
```

Chromium is the primary engine; use `--engine lightpanda` for the fast read-only engine. Use `agent-browser close` before switching engines.

---

## Network interception

```bash
# Block analytics / ads
agent-browser network route "**analytics**" --abort
agent-browser network route "**ads**"       --abort

# Mock an API response with a custom body
agent-browser network route "https://api.example.com/data" --body '{"items":[]}'

# Remove a route
agent-browser network unroute "**analytics**"

# Inspect captured requests
agent-browser network requests --filter "api.example.com"
agent-browser network requests --clear

# HAR recording
agent-browser network har start ./traffic.har
# ... actions ...
agent-browser network har stop
```

Sensitive — `network route` can mock production data. Approve narrowly.

---

## Frames / iframes

```bash
agent-browser frame "#payment-iframe"     # switch into iframe
agent-browser snapshot -i                  # refs are scoped to this frame
agent-browser fill @e1 "4242 4242 4242 4242"
agent-browser frame main                   # back to main frame
```

Treat frame switches like tab switches — re-snapshot.

---

## Dialogs

```bash
agent-browser dialog accept              # accept alert / confirm
agent-browser dialog dismiss             # cancel
agent-browser dialog accept "response"   # accept prompt with text input
```

Dialogs are auto-dismissed by default. Disable with `AGENT_BROWSER_NO_AUTO_DIALOG=1` if you want to handle them manually.

---

## Cookies and storage (full surface)

```bash
# cookies
agent-browser cookies
agent-browser cookies --json | jq '.[] | select(.domain == ".example.com")'
agent-browser cookies set name "value" --domain .example.com --path / \
              --httpOnly --secure --sameSite Lax --expires 3600
agent-browser cookies clear

# localStorage / sessionStorage
agent-browser storage local
agent-browser storage local get  key
agent-browser storage local set  key "value"
agent-browser storage local clear
agent-browser storage session get sessionKey
```

Sensitive operations: `cookies set`, `cookies clear`, `storage * set`, `storage * clear`. See `safety.md`.

---

## Viewport, device, color-scheme

```bash
agent-browser set viewport 1920 1080            # CSS pixels
agent-browser set viewport 1920 1080 2          # 2× device pixel ratio (HiDPI)
agent-browser set device "iPhone 14"            # viewport + UA + touch
agent-browser --color-scheme dark open https://example.com
agent-browser set media dark
agent-browser set media light reduced-motion
```

---

## Video recording

Capture automation runs as WebM (VP8/VP9).

```bash
agent-browser record start ./demo.webm
# ... actions ...
agent-browser record stop
agent-browser record restart ./take2.webm   # stop current + start new
```

Use cases:

- Debugging — record the run, replay to see where it broke.
- Documentation — `wait` between steps for human readability.
- CI evidence — drop into artifacts on failed runs.

Add pauses for human viewing:

```bash
agent-browser click @e1
agent-browser wait 500
agent-browser screenshot ./step1.png
```

Costs disk space; some headless environments have codec quirks.

---

## Profiling (Chrome DevTools traces)

Capture a Chrome DevTools performance profile during automation.

```bash
agent-browser profiler start
agent-browser open https://app.example.com
agent-browser wait --load networkidle
agent-browser profiler stop ./trace.json
```

Custom trace categories:

```bash
agent-browser profiler start --categories "devtools.timeline,v8.execute,blink.user_timing"
agent-browser profiler stop ./trace.json
```

View in:

- Chrome DevTools → Performance → Load profile.
- Perfetto UI (https://ui.perfetto.dev).
- `chrome://tracing` in any Chromium browser.

Limitations: Chromium only; ~5M event cap; 30 s timeout on stop.

`trace` is a related but distinct surface — Playwright-style traces for replay rather than perf analysis:

```bash
agent-browser trace start
# ... actions ...
agent-browser trace stop ./trace.zip
npx playwright show-trace ./trace.zip
```

---

## WebSocket streaming (live preview)

```bash
export AGENT_BROWSER_STREAM_PORT=9223
agent-browser open https://example.com
agent-browser stream enable
agent-browser stream status
```

Connect a WebSocket client to `ws://localhost:9223`. Protocol:

| Type | Direction | Format |
|---|---|---|
| Frame | server → client | `{"type":"frame","data":"<base64 jpeg>"}` |
| Status | server → client | `{"type":"status","url":"...","title":"..."}` |
| Input | client → server | `{"type":"input","action":"click","x":100,"y":200}` |

Input modifier bitmask: 1=Alt, 2=Ctrl, 4=Meta, 8=Shift.

Sensitive — exposes browser control on a TCP port. Bind to localhost only.

---

## Mouse control (low level)

```bash
agent-browser mouse move 100 200
agent-browser mouse down left
agent-browser mouse up   left
agent-browser mouse wheel 100         # dy
agent-browser mouse wheel -300 0      # dy dx
agent-browser drag @e1 @e2
```

For canvas, drag-and-drop, custom widgets where refs alone are not enough.

---

## Eval — full guidance

```bash
# Simple — single-quoted, no nested quotes
agent-browser eval 'document.title'
agent-browser eval 'document.querySelectorAll("img").length'

# Complex — heredoc with single-quoted delimiter (RECOMMENDED)
agent-browser eval --stdin <<'EVALEOF'
JSON.stringify(
  Array.from(document.querySelectorAll('img'))
    .filter(i => !i.alt)
    .map(i => ({ src: i.src.split('/').pop(), width: i.width }))
)
EVALEOF

# Programmatic / generated — base64 to avoid all shell escaping
agent-browser eval -b "$(echo -n 'Array.from(document.querySelectorAll("a")).map(a => a.href)' | base64)"
```

Rules of thumb:

- Single-line, no nested quotes → inline `eval 'expression'`.
- Nested quotes, arrow functions, template literals, multi-line → `eval --stdin <<'EVALEOF'`.
- Generated by another script → `eval -b` with base64.

Always single-quote the heredoc delimiter (`<<'EVALEOF'`) so the shell does not expand `$`, backticks, or escapes inside the JS.

---

## Workflow patterns (when scenarios in SKILL.md are not enough)

### Multi-account parallel testing

Run admin / editor / viewer at the same time in named sessions:

```bash
for role in admin editor viewer; do
  agent-browser --session "$role" open https://app.example.com/login
  agent-browser --session "$role" snapshot -i
  agent-browser --session "$role" fill @e1 "${role}@example.com"
  agent-browser --session "$role" fill @e2 "password"
  agent-browser --session "$role" click @e3
  agent-browser --session "$role" wait --url "**/dashboard"
done

agent-browser --session admin  open https://app.example.com/admin
agent-browser --session editor open https://app.example.com/admin
agent-browser --session viewer open https://app.example.com/admin

agent-browser --session admin  get url
agent-browser --session editor get url
agent-browser --session viewer get url

for role in admin editor viewer; do
  agent-browser --session "$role" close
done
```

This is a legitimate script use — the loop is part of the user's intent, not a substitute for the inline pattern.

### PR-affected E2E smoke

Test only routes touched by a PR. Get changed files from `gh pr view --json files -q '.files[].path'`, map to routes, then for each route: `open`, `wait --load networkidle`, `snapshot -i`, `screenshot`.

### DOM-evidence validation (preferred over screenshot-only)

```bash
agent-browser click @e3                     # submit
agent-browser wait --load networkidle
agent-browser snapshot -i
RESULT=$(agent-browser get text @e1)        # for the inline command pattern

if [[ "$RESULT" == *"Success"* ]]; then
  echo "PASS: $RESULT"
else
  agent-browser screenshot "./evidence/failure-$(date +%s).png"
  echo "FAIL: expected Success, got: $RESULT"
fi
```

DOM evidence is the source of truth. Screenshots supplement it for human review.

### Data extraction pipeline

```bash
agent-browser open https://example.com/products
agent-browser wait --load networkidle
agent-browser snapshot -i --json | jq -r '.data.refs | to_entries[] | select(.value.role == "link") | .value.name' > products.txt

while IFS= read -r product; do
  agent-browser find text "$product" click
  agent-browser wait --load networkidle
  PRICE=$(agent-browser get text ".product-detail .price")
  DESC=$(agent-browser get text ".product-detail .description")
  echo "$product|$PRICE|$DESC" >> product-details.csv
  agent-browser back
  agent-browser wait --load networkidle
  agent-browser snapshot -i
done < products.txt
```

Again — the loop here is the user's intent. The shape "open, snapshot, find, get, back, re-snapshot" is the same observe-act-verify loop, just iterated.

### Diff-driven verification

```bash
agent-browser snapshot                            # baseline
# ... changes ...
agent-browser diff snapshot                       # vs last snapshot
agent-browser diff snapshot --baseline ./snap.txt # vs saved baseline
agent-browser diff screenshot --baseline ./shot.png
agent-browser diff url https://staging/page https://prod/page
```
