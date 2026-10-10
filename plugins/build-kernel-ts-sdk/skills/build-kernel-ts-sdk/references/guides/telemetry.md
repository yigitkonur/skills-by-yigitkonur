# Browser Telemetry: Streaming, Retention & OTLP Export

Kernel's Browser Telemetry subsystem is a high-fidelity observability pipeline providing real-time streaming, historical retrieval, and OpenTelemetry (OTLP/HTTP) export of browser execution, DOM events, CDP commands, network traffic, and security challenges.

---

## 1. Telemetry Architecture & Categories

Telemetry events are grouped into operational and opt-in categories:

1. **Operational Categories (Default Enabled when telemetry is on):**
   - `control` — Commands that drive the browser (`api_call`, `cdp_command`, screenshots, clipboard). For Playwright executions, submitted code is captured in `BrowserAPICallEvent.Data.code` (clipped to 8192 bytes / 8KB).
   - `connection` — CDP, WebSocket, and Live View client connections and disconnections.
   - `system` — VM-level failure events (`system_oom_kill`, `service_crashed`). (Does not report CPU/RAM metrics).
   - `captcha` — Solver detection and progress (`captcha_solve_started`, `captcha_solve_result`, `captcha_challenge_result`). Tasks correlate on `task_id` with `captcha_provider` and `task_kind` (`captcha_type` is deprecated); visible challenge episodes correlate on `challenge_id`.
   *(Note: `monitor` is not user-configurable; it emits CDP collector health like `monitor_disconnected` and flows automatically whenever browser-activity categories are captured).*

2. **Opt-in Categories (Off by default; must be explicitly enabled):**
   - `platform` — VM management actions performed by Kernel on your behalf (`platform_api_call`: profile saves, replays, recorder polling).
   - `network` — HTTP request/response headers, status codes, timing, and proxy errors (`proxy_error`).
   - `console` — Chromium `console.log`, `warn`, `error`.
   - `page` — DOM lifecycle (`navigation`, `dom_content_loaded`, `load`, and computed readiness events `network_idle`, `page_layout_settled`).
   - `interaction` — Dispatched mouse clicks, keypresses, scrolls, and drag gestures.
   - `screenshot` — Periodic visual viewport frames.

---

## 2. Enabling Telemetry on Session Creation

Category toggles are strictly nested under `telemetry.browser.<category>.enabled`:

```ts
import Kernel from '@onkernel/sdk';
const kernel = new Kernel();

const session = await kernel.browsers.create({
  stealth: true,
  telemetry: {
    browser: {
      // Opt into specific categories:
      platform: { enabled: true },
      network: { enabled: true },
      console: { enabled: true },
      page: { enabled: true },
      // Optional: Filter out high-volume CDP commands
      control: {
        cdp: {
          excluded_methods: ['Input.dispatchMouseEvent', 'Page.captureScreenshot'],
        },
      },
    },
    // Optional: Zero Data Retention (ZDR) — suppress Kernel storage
    // Requires an OTLP export destination to be configured
    storage: { enabled: false },
  },
});
```

CLI equivalent:
```bash
# Enable all categories:
kernel browsers create --telemetry=all

# Enable specific list:
kernel browsers create --telemetry=control,connection,system,captcha,network,console

# Zero Data Retention with OTLP export:
kernel browsers create --telemetry-storage off --telemetry-export-otlp prod-datadog
```

---

## 3. Real-Time Streaming (`telemetry.stream`)

Stream live session events over Server-Sent Events (SSE). Streams yield envelopes `{ seq: number, event: BrowserTelemetryEvent }`, where `event.ts` is in Unix microseconds:

```ts
const stream = await kernel.browsers.telemetry.stream(session.session_id, {
  // replay: 'all',            // optionally replay events from session start
  // type: ['proxy_error'],    // filter stream by specific event type(s)
});

for await (const { seq, event } of stream) {
  const time = new Date(Math.floor(event.ts / 1000)).toISOString();
  console.log(`[#${seq} ${time}] ${event.category}/${event.type}`);

  // Proxy error correlation:
  if (event.type === 'proxy_error' && event.data) {
    console.error('Proxy failure:', event.data.code, event.data.status);
  }

  // CAPTCHA solving progress:
  if (event.type === 'captcha_solve_started') {
    console.log(`Solving ${event.data.task_kind} via ${event.data.captcha_provider}`);
  }
  if (event.type === 'captcha_solve_result' && event.data) {
    console.log(`Solver result: ${event.data.status}`); // 'success' | 'failure' | 'timeout' | 'abandoned'
  }

  // Computed page readiness events:
  if (event.type === 'network_idle' || event.type === 'page_layout_settled') {
    console.log('Page ready for interaction:', event.type);
  }
}
```

CLI equivalent:
```bash
kernel browsers telemetry stream <session_id>
```

---

## 4. Historical Events Querying (`telemetry.events`)

Archived session telemetry is retained for **30 days** (unless ZDR is enabled). Query parameters support array filters for `category` and `type`, along with `since` and `until` time windows:

```ts
const history = await kernel.browsers.telemetry.events(session.session_id, {
  category: ['network'],
  type: ['proxy_error'],
  since: '2026-10-01T00:00:00Z',
  until: '2026-10-09T00:00:00Z',
  limit: 100,
});

for await (const { seq, event } of history) {
  console.log(`Seq #${seq} ts=${event.ts} type=${event.type}`);
}
```

CLI equivalent:
```bash
kernel browsers telemetry events <session_id> --category network --type proxy_error
```

---

## 5. Exporting to OpenTelemetry Backends (OTLP)

Export session telemetry directly to Datadog, Honeycomb, New Relic, or OTLP collectors.

### 1. Register Org-Scoped Destination
Register the destination via `POST /telemetry/destinations` (or manage via `kernel.telemetry.destinations.{create,retrieve,update,list,delete}`). The parameter is `endpoint` **without signal paths** (Kernel appends `/v1/logs` automatically):

```ts
const dest = await kernel.telemetry.destinations.create({
  name: 'prod-datadog',
  endpoint: 'https://otlp-http.datadoghq.com', // DO NOT append /v1/logs or /v1/traces
  headers: {
    'DD-API-KEY': process.env.DD_API_KEY!,
  },
});

// Inspect export delivery health
const info = await kernel.telemetry.destinations.retrieve(dest.id);
console.log(`Failures: ${info.consecutive_failures}, Last export: ${info.last_export_at}`);
```

CLI equivalent:
```bash
kernel telemetry destinations create \
  --name prod-datadog \
  --endpoint https://otlp-http.datadoghq.com \
  --header "DD-API-KEY=$DD_API_KEY"
```

### 2. Bind Destination to Browser Session
Bind the destination at session creation via `export.otlp.destination`:

```ts
const session = await kernel.browsers.create({
  stealth: true,
  telemetry: {
    browser: {
      network: { enabled: true },
      console: { enabled: true },
    },
    export: {
      otlp: {
        destination: { id: dest.id }, // or { name: 'prod-datadog' }
      },
    },
  },
});
```

---

## 6. Replays: MP4 Chapter Markers & Audio Capture

Kernel session replays support named markers embedded directly into the MP4 container metadata as chapters, allowing video players to jump between distinct test phases without having to split the session into multiple disconnected recordings.

Replays can also capture system audio in headful sessions:

```ts
// Start recording with audio capture
const replay = await kernel.browsers.replays.start(session.session_id, {
  record_audio: true, // capture tab audio (headful sessions)
});
```
