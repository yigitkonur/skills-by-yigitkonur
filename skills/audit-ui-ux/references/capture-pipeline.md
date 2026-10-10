# Dual-Engine Capture Pipeline

The audit relies on a unified capture pipeline that generates visual PNG assets across Web and Mobile platforms without exposing source code to the evaluation lens.

---

## 1. Engine 1: Web Capture (`ego-browser`)

For all Web targets (desktop, tablet, responsive web), capture is performed exclusively using `ego-browser`.
- **Prohibited:** Raw Playwright scripts, Puppeteer, Selenium, or headless web scrapers.
- **Why:** `ego-browser` provides true Chromium rendering with realistic user viewport sizing, mouse hover state emulation, cookie session persistence, and authentic visual pixel generation.

### Remote Environment Detection & SCP Sync
Modern development frequently occurs on remote servers (e.g. remote development host `tugce` or cloud containers). When capturing on a remote host:
1. **Detect SSH / Remote Host:**
   Check `$SSH_CLIENT`, `$SSH_TTY`, `$SSH_CONNECTION`, or hostname to determine if the test server is running remotely.
2. **Execute Remote Capture:**
   Execute the browser capture commands within the remote host environment where the dev server (`localhost:3000`, `localhost:8080`) is listening.
3. **Automated SCP Synchronization:**
   Immediately sync the generated screenshot directory back to the local workspace:
   ```bash
   scp -r user@remote-host:/path/to/remote/audit-artifacts/<YYYY-MM-DD>/ ./audit-artifacts/<YYYY-MM-DD>/
   ```
   Or if triggered locally against a remote tunnel:
   ```bash
   scp -r tugce:~/app/audit-artifacts/2026-10-10/ ./audit-artifacts/2026-10-10/
   ```

### Capturing Interactive States with `ego-browser`
To evaluate a screen thoroughly, capture standard states into `audit-artifacts/<YYYY-MM-DD>/<screen-slug>/`:
- `default.png`: Base rendered viewport after initial paint and data load.
- `hover.png`: Hover state over primary action or navigational link.
- `active.png`: Active/focus state on form inputs or pressed state on buttons.
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

### Mobile Execution Loop with Maestro MCP
1. **Target Identification:**
   Query booted devices via `maestro list-devices` or MCP `list_devices`.
2. **Flow Navigation & Screenshot Command:**
   Execute declarative Maestro steps using inline YAML via MCP `run`:
   ```yaml
   - launchApp: "com.example.app"
   - takeScreenshot: "audit-artifacts/2026-10-10/onboarding/default.png"
   - tapOn: "Sign Up"
   - takeScreenshot: "audit-artifacts/2026-10-10/onboarding/active.png"
   ```
3. **State Capture on Mobile:**
   - Tap primary fields to expose mobile virtual keyboards (`active.png`).
   - Trigger network mock disconnection or empty list endpoints (`empty-state.png`, `error-state.png`).
   - Open bottom sheets and navigation drawers (`modal-open.png`).

---

## 3. Post-Capture Verification Gate

Once screenshots are captured from either engine (Web or Mobile), run the verification gate:
```bash
bash skills/audit-ui-ux/scripts/validate-capture-gate.sh audit-artifacts/<YYYY-MM-DD>/
```
Only proceed to Phase 3 (Vision Evaluation) after the capture gate outputs:
`✅ Capture Gate Status: PASSED.`
