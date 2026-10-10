# Dual-Engine Capture Pipeline & Resilient Fallback Runbooks

The audit relies on a unified, fault-tolerant capture pipeline that generates visual PNG assets across Web and Mobile platforms without exposing source code, DOM trees, or internal selectors to the evaluation lens.

---

## 1. Engine 1: Web Capture (`ego-browser`)

For all Web targets (desktop, tablet, responsive mobile web), capture is performed exclusively using `ego-browser`.
- **Strictly Prohibited:** Raw Playwright scripts, Puppeteer, Selenium, or headless web scrapers.
- **Why:** `ego-browser` provides true Chromium rendering with realistic user viewport sizing, mouse hover state emulation, cookie session persistence, and authentic visual pixel generation.

### 1.1 Viewport & Device Pixel Ratio (DPR) Normalization
#### The Failure Mode:
Displays operate at varying native DPRs (1x standard desktop vs 2x/3x Apple Retina). Without normalization, captures produce inconsistent pixel dimensions across machines (e.g. 1440×900 vs 2880×1800), distorting bounding box coordinates and visual measurements. Mobile emulation without explicit touch parameters also fails to trigger responsive layouts.

#### Normalization Protocol:
Prior to navigation, enforce deterministic device metrics via Chrome DevTools Protocol (CDP) and specify `scale: "css"` during capture:

```javascript
// 1. Enforce canonical mobile viewport & DPR via CDP
await page.cdp("Emulation.setDeviceMetricsOverride", {
  width: 390,
  height: 844,
  deviceScaleFactor: 3, // Emulate @3x Super Retina
  mobile: true,
  hasTouch: true
});

// 2. Capture screenshot with CSS scaling to prevent host-display dimension drift
await page.screenshot({
  path: "audit-artifacts/2026-10-10/checkout/default.png",
  scale: "css"
});
```

#### Layout Overflow & Clipping Check:
Before capturing, verify that content does not break horizontal viewport bounds:
```javascript
const hasHorizontalOverflow = await page.evaluate(() => {
  return document.documentElement.scrollWidth > window.innerWidth;
});
if (hasHorizontalOverflow) {
  console.warn("⚠️ Layout defect: Horizontal scroll overflow detected on target viewport.");
}
```

---

### 1.2 Cookie Consent Banners & GDPR / CCPA Overlay Mitigation
#### The Failure Mode:
Third-party consent managers (OneTrust, Cookiebot, Klaro, Termly) inject asynchronous backdrops 500–1500ms post-load, obscuring up to 100% of the UI. If unhandled, the audit critiques the cookie modal instead of the application.

#### The 3-Tier Mitigation Strategy:
1. **Tier 1 (Pre-seed Known Cookies):** Set consent cookies via CDP before navigating to prevent banners from ever rendering.
2. **Tier 2 (Semantic Dismissal Loop):** If a banner appears, click standard dismissal buttons (`Accept`, `Allow all`, `Agree`, `Reject non-essential`) using accessible role selectors.
3. **Tier 3 (DOM Suppression Fallback):** If persistent, remove the banner node from the DOM and restore body scroll.

```javascript
// Tier 1: Pre-seed common consent cookies
await page.cdp("Network.setCookie", {
  name: "OptanonAlertBoxClosed",
  value: new Date().toISOString(),
  domain: new URL(await page.url()).hostname
});

// Tier 2: Semantic click loop
const dismissSelectors = [
  'loc=role:button[name*="Accept" i]',
  'loc=role:button[name*="Allow all" i]',
  'loc=role:button[name*="Agree" i]',
  'loc=role:button[name*="Reject non-essential" i]',
  'loc=css:#onetrust-accept-btn-handler',
  'loc=css:.cookie-consent-accept'
];

for (const sel of dismissSelectors) {
  try {
    await page.click(sel, { timeout: 1000 });
    await page.waitForTimeout(300);
    break;
  } catch (e) { /* continue */ }
}

// Tier 3: DOM Suppression Fallback & Overflow Reset
await page.evaluate(() => {
  const bannerSelectors = ['#onetrust-consent-sdk', '.cookie-banner', '[aria-label*="cookie" i]'];
  document.querySelectorAll(bannerSelectors.join(',')).forEach(el => el.remove());
  document.body.style.overflow = 'auto';
  document.documentElement.style.overflow = 'auto';
});
```

---

### 1.3 SPA Hydration Races & The 4-Gate Settling Protocol
#### The Failure Mode:
Modern frameworks (Next.js App Router, Vite, Nuxt) render an initial server shell followed by client-side hydration, bundle compilation, and dynamic data fetching. Arbitrary timeouts (e.g. `sleep 1`) capture blank skeleton pulses or half-painted screens.

#### The 4-Gate Visual Settling Protocol:
Every capture must pass four sequential visual gates before `page.screenshot()` is invoked:

```
┌────────────────────────────────────────────────────────┐
│            GATE 1: Network & Load Lifecycle            │
│   page.waitForLoadState("load")                        │
│   page.waitForLoadState("networkidle", { idleMs: 500 })│
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│       GATE 2: Skeleton & Spinner Disappearance         │
│   waitForSelector(".skeleton", { state: "detached" })  │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│         GATE 3: Visual Layout Stability (rAF)          │
│   Double requestAnimationFrame layout flush            │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│        GATE 4: Timeout Contingency (10s Max)           │
│   Capture "loading-timeout.png", log Catastrophe,     │
│   proceed with audit without crashing pipeline         │
└────────────────────────────────────────────────────────┘
```

```javascript
async function waitForVisualStability(page, maxTimeoutMs = 10000) {
  const startTime = Date.now();

  // Gate 1: Lifecycle & Network Idle
  await page.waitForLoadState("load");
  await page.waitForLoadState("networkidle", { idleMs: 500, timeout: 5000 }).catch(() => {});

  // Gate 2: Spinner Detachment
  const spinnerSelectors = [
    'loc=css:[data-testid="loading"]',
    'loc=css:.skeleton',
    'loc=css:.spinner',
    'loc=css:[role="progressbar"]'
  ];
  for (const spinner of spinnerSelectors) {
    try {
      await page.waitForSelector(spinner, { state: "detached", timeout: 3000 });
    } catch (e) { /* ignore if not present */ }
  }

  // Gate 3: Double requestAnimationFrame layout flush
  await page.evaluate(() => new Promise(resolve => {
    requestAnimationFrame(() => requestAnimationFrame(resolve));
  }));

  // Gate 4: Timeout check
  if (Date.now() - startTime >= maxTimeoutMs) {
    console.warn("⚠️ Hydration settling timed out (>10s). Capturing loading-timeout.png.");
    await page.screenshot({ path: "loading-timeout.png" });
  }
}
```

---

### 1.4 Resilient Remote SSH Synchronization Runbook
#### The Failure Mode:
When the dev server runs on a remote host (e.g. `tugce` or cloud container), naive `scp -r` fails on transient network drops, leaving partial, 0-byte, or corrupted PNG files that crash downstream vision evaluators.

#### Hardened Synchronization Protocol:
1. Use `rsync` with `--partial`, `--delay-updates`, and `--checksum` to guarantee atomic writes.
2. Implement 3-tier exponential backoff retry with SSH keepalive.
3. Automatically execute `validate-capture-gate.sh` immediately after transfer.

```bash
#!/usr/bin/env bash
# sync-remote-artifacts.sh: Resilient Remote Artifact Synchronization
set -euo pipefail

REMOTE_TARGET="${1:-}"
LOCAL_DEST="${2:-./audit-artifacts/}"

if [[ -z "$REMOTE_TARGET" ]]; then
  echo "Usage: $0 <user@host:/path/to/artifacts> [local_destination]"
  exit 1
fi

MAX_RETRIES=3
RETRY_DELAY=2
SUCCESS=0

echo "🚀 Initiating resilient artifact sync from $REMOTE_TARGET to $LOCAL_DEST"

for attempt in $(seq 1 $MAX_RETRIES); do
  echo "Attempt $attempt of $MAX_RETRIES..."
  if rsync -avz --partial --delay-updates --checksum --timeout=30 \
       -e "ssh -o ConnectTimeout=10 -o ServerAliveInterval=5 -o ServerAliveCountMax=3" \
       "$REMOTE_TARGET" "$LOCAL_DEST"; then
    SUCCESS=1
    break
  else
    echo "⚠️ Sync attempt $attempt failed. Retrying in ${RETRY_DELAY}s..."
    sleep $RETRY_DELAY
    RETRY_DELAY=$((RETRY_DELAY * 2))
  fi
done

if [[ $SUCCESS -ne 1 ]]; then
  echo "❌ Fatal: Remote artifact sync failed after $MAX_RETRIES attempts."
  exit 1
fi

echo "🔍 Running local capture verification gate..."
bash skills/audit-ui-ux/scripts/validate-capture-gate.sh "$LOCAL_DEST"
```

---

### 1.5 Standard Interactive State Capture Choreography
To evaluate a screen thoroughly, capture standard states into `audit-artifacts/<YYYY-MM-DD>/<screen-slug>/`:
- `default.png`: Base rendered viewport after initial paint and settling.
- `hover.png`: Hover state over primary action or navigational link.
- `active.png`: Active/focus state on form inputs or pressed state on buttons (used for focus indicator evaluation).
- `empty-state.png`: Viewport rendered with zero records/items.
- `error-state.png`: Form validation trigger or network error banner.
- `loading.png`: Skeleton loading pulse or progress state.
- `modal-open.png`: Overlay sheet, dialog, or drawer open over the page.

---

## 2. Engine 2: Mobile Capture (`test-by-maestro`)

For Mobile targets (iOS Simulator, Android Emulator, physical Android device), capture is performed via `test-by-maestro`.
- **Prerequisite:** Declare `skills/test-by-maestro` as the prerequisite mobile driver.
- **Supported Targets:**
  - **iOS Simulators:** Darwin/macOS hosts with Xcode (`xcode-select -p`) or Maestro Cloud.
  - **Android Emulators / Physical Devices:** ADB-connected targets across macOS, Linux, and Windows.

### 2.1 Mobile Failure Recovery Runbook
When executing automated mobile flows, common device and environment glitches must be trapped and recovered automatically:

| Failure Scenario | Underlying Mechanism | Automated Recovery Runbook |
|---|---|---|
| **Device Offline / ADB Daemon Hang** | Android ADB daemon drops connection or enters zombie state. | Execute `adb kill-server && adb start-server && adb wait-for-device`. Verify with `adb devices` before starting Maestro flow. |
| **iOS Simulator Boot Timeout** | Simulator fails to reach booted state before Maestro flow timeout. | Execute `xcrun simctl bootstatus "$UDID" -b` to guarantee boot completion. Use dynamic `SIMCTL_CHILD_PORT` if running parallel instances. |
| **App Crash Loop on Launch** | Stale local storage, corrupted auth token, or dirty database crash app. | Set `clearState: true` and `stopIfRunning: true` inside `launchApp` step to guarantee a pristine start. |
| **System Permission Alerts** | OS displays push notification, camera, or location permission dialogs, blocking app UI. | Add optional auto-dismiss step in flow: `- tapOn: { text: "Allow\|While Using the App\|OK", optional: true }`. |
| **Virtual Soft-Keyboard Occlusion** | Focusing an input opens soft keyboard, hiding adjacent fields or buttons in `active.png`. | Capture `active.png`, then immediately call `- hideKeyboard: { optional: true }` before subsequent state actions. |
| **Flow Step Assertion Timeout** | Network delay causes a tap or navigation assertion to fail unexpectedly. | Enclose flow with `onFlowComplete:` hook to capture `last-known-state.png` before the flow terminates. |

---

### 2.2 Maestro Resilient Capture Flow Recipe
```yaml
appId: com.example.app
tags:
  - visual-audit
onFlowStart:
  - launchApp:
      clearState: true
      stopIfRunning: true
  - tapOn:
      text: "Allow|While Using the App|OK"
      optional: true

---
# 1. Base Screen Capture (Default State)
- assertVisible: "Dashboard"
- takeScreenshot: "audit-artifacts/2026-10-10/dashboard/default.png"

# 2. Input Focus State Capture (Active State with Focus Ring)
- tapOn:
    id: "search_input"
- takeScreenshot: "audit-artifacts/2026-10-10/dashboard/active.png"
- hideKeyboard:
    optional: true

# 3. Drawer / Modal Capture
- tapOn: "Filter Options"
- assertVisible: "Filter Categories"
- takeScreenshot: "audit-artifacts/2026-10-10/dashboard/modal-open.png"

# Fallback hook guarantees screenshot on unexpected exception
onFlowComplete:
  - takeScreenshot: "audit-artifacts/2026-10-10/dashboard/last-known-state.png"
```

---

## 3. Post-Capture Verification Gate

Once screenshots are captured from either engine (Web or Mobile), run the verification gate:
```bash
bash skills/audit-ui-ux/scripts/validate-capture-gate.sh audit-artifacts/<YYYY-MM-DD>/
```
Only proceed to Phase 3 (Vision Evaluation) after the capture gate outputs:
`✅ Capture Gate Status: PASSED.`
