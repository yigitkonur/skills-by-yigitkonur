# Browser Telemetry: Streaming, Retention & OTLP Export

Kernel's Browser Telemetry subsystem provides real-time streaming, historical retrieval (30 days), and OpenTelemetry (OTLP/HTTP logs) export of browser execution, DOM events, CDP commands, network traffic, and captcha activity.

---

## 1. Categories

Telemetry is off unless you enable it. Events are grouped into categories; a category is the unit you turn on or off.

| Category | Default when telemetry is on | Event types |
|---|---|---|
| `control` | yes | `api_call`, `cdp_command` — computer-control calls, Playwright execution (submitted code is captured in `BrowserAPICallEvent.Data.code`, capped at 8192 bytes, ends in `...[truncated]`), screenshots, clipboard, and classified browser-control commands on the CDP proxy |
| `connection` | yes | `cdp_connect`, `cdp_disconnect`, `live_view_connect`, `live_view_disconnect` |
| `system` | yes | `system_oom_kill` (carries RSS, total and free memory), `service_crashed`. No continuous CPU/RAM metrics; sample with `process.exec` |
| `captcha` | yes | `captcha_solve_started`, `captcha_solve_result`, `captcha_challenge_result` |
| `platform` | no | `platform_api_call` — VM management (profile saves, replays, recorder polling, filesystem, process, config) |
| `network` | no | `network_request`, `network_response`, `network_loading_failed`, `network_idle`, `proxy_error` |
| `console` | no | `console_log`, `console_error` |
| `page` | no | `page_navigation`, `page_dom_content_loaded`, `page_load`, `page_tab_opened`, `page_crashed`, `page_layout_shift`, `page_lcp`, `page_layout_settled`, `page_navigation_settled` |
| `interaction` | no | `interaction_click`, `interaction_key`, `interaction_scroll_settled` — browser-native DOM events in the page, not `computer.*` calls (those are `control`) |
| `screenshot` | no | `monitor_screenshot` (periodic, high volume) |

`monitor` (`monitor_disconnected`, `monitor_reconnected`, `monitor_reconnect_failed`, `monitor_init_failed`) is not settable; it flows whenever `console`, `network`, `page`, or `interaction` is captured, and you can filter on it.

Computed readiness events: `network_idle` fires 500 ms after in-flight requests reach zero; `page_layout_settled` fires 1 s after `page_load` with no layout shift; `page_navigation_settled` fires once DOM-content-loaded and layout-settled have both fired for a navigation (use it as the single "page ready" signal). Each fires at most once per top-level navigation.

The browser-activity categories (`console`, `network`, `page`, `interaction`) attach a CDP collector and capture sensitive data (`network` includes `Authorization` and `Cookie` headers and request bodies; `console`, `page` URLs, `interaction`, and `screenshot` can hold tokens and personal data). Enable only what you need. For orgs with a BAA, `network`, `console`, and `screenshot` cannot be captured.

---

## 2. Enabling Telemetry on Session Creation

Omitting `telemetry` (or `null`, `{}`, `enabled: false`) captures nothing.

```ts
import Kernel from '@onkernel/sdk';
const kernel = new Kernel();

// Default set (control, connection, system, captcha):
await kernel.browsers.create({ telemetry: { enabled: true } });

// Default set plus extra categories (provided categories layer onto the default set):
const session = await kernel.browsers.create({
  stealth: true,
  telemetry: {
    browser: {
      platform: { enabled: true },
      network: { enabled: true },
      console: { enabled: true },
      page: { enabled: true },
      // Optional: omit high-volume CDP commands from cdp_command events (they still reach the browser)
      control: {
        cdp: { excluded_methods: ['Input.dispatchMouseEvent', 'Page.captureScreenshot'] },
      },
      // Opt out of a default category:
      // captcha: { enabled: false },
    },
    // Optional: Zero Data Retention. Requires an OTLP destination and cannot be changed after create.
    // storage: { enabled: false },
  },
});
```

Update semantics (`kernel.browsers.update(id, { telemetry })`): a category list merges onto the session's current selection; `{ enabled: true }` resets to the default set plus any categories you pass; `{ enabled: false }` stops capture (cannot be combined with `browser` settings). Docs describe a create-time category list as "only those categories"; the SDK types say it layers onto the default set, and the skill follows the SDK. The CLI help says `--telemetry=console,network` captures exactly those categories.

CLI equivalents:
```bash
kernel browsers create --telemetry=all                       # default set
kernel browsers create --telemetry=control,connection,system,captcha,network,console
kernel browsers create --telemetry-cdp-exclude Input.dispatchMouseEvent,Page.captureScreenshot
kernel browsers create --telemetry-storage off --telemetry-export-otlp prod-honeycomb
kernel browsers update <session-id> --telemetry=off
```

---

## 3. Real-Time Streaming (`telemetry.stream`)

SSE stream of envelopes `{ seq: number, event: BrowserTelemetryEvent }`; `event.ts` is Unix microseconds. The stream closes when the session terminates, sends a keepalive every 15 s, and opens but delivers nothing if telemetry was never enabled. Fresh connections only see new events.

```ts
const stream = await kernel.browsers.telemetry.stream(session.session_id, {
  // replay: 'all',                    // start from the oldest retained event
  // type: ['proxy_error'],            // server-side filter by event type (filtered events are never sent)
  // 'Last-Event-ID': String(lastSeq), // resume after a disconnect (wins over replay)
});

let lastSeq = 0;
for await (const { seq, event } of stream) {
  lastSeq = seq; // gaps in seq mean dropped events
  const time = new Date(Math.floor(event.ts / 1000)).toISOString();
  console.log(`[#${seq} ${time}] ${event.category}/${event.type}`);

  if (event.type === 'proxy_error' && event.data) {
    console.error('Proxy failure:', event.data.code, event.data.status);
  }
  if (event.type === 'captcha_solve_started') {
    console.log(`Solving ${event.data.task_kind} via ${event.data.captcha_provider}`);
  }
  if (event.type === 'captcha_solve_result' && event.data) {
    console.log(`Solver result: ${event.data.status}`); // 'success' | 'failure' | 'timeout' | 'abandoned'
  }
  if (event.type === 'page_navigation_settled') {
    console.log('Page ready for interaction');
  }
}
```

The stream does not reconnect on its own: re-open it with `'Last-Event-ID': String(lastSeq)` to resume without gaps. (Docs prose calls this `last_event_id`; the TS parameter is `'Last-Event-ID'`.)

Captcha events: pair a start with its result on `task_id`; `challenge_id` only groups tasks of one visible challenge and can be absent. Delivery is best-effort and unordered, so wait with a deadline and fall back to the page state. `captcha_solve_result.status: 'success'` means the solver returned a usable answer, not that the challenge cleared. `captcha_challenge_result` (`solved|failure|timeout|abandoned`) is emitted for reCAPTCHA v2, hCaptcha, and press-and-hold only. `captcha_type` is deprecated; read `captcha_provider` and `task_kind`.

CLI:
```bash
kernel browsers telemetry stream <session-id> --categories=network,console --types=network_response,console_error
kernel browsers telemetry stream <session-id> --replay=all     # or --seq 1024 to resume; -o json for NDJSON
```

---

## 4. Historical Events (`telemetry.events`)

Archived events are retained for **30 days**. The default window is the **last 5 minutes**: pass `since` (RFC-3339 timestamp or a duration like `24h`) to look further back, `until` (exclusive) to end the window, and `order: 'desc'` for newest first (cannot be combined with `since`). Filters apply within each page, so a page can be empty while more pages exist; iterate all pages.

```ts
const history = await kernel.browsers.telemetry.events(session.session_id, {
  category: ['network'],
  type: ['proxy_error'],      // combines with category: an event must match both
  since: '2026-10-01T00:00:00Z',
  until: '2026-10-09T00:00:00Z',
  limit: 100,                 // CLI: 1-100, default 20
});

for await (const { seq, event } of history) {
  console.log(`Seq #${seq} ts=${event.ts} type=${event.type}`);
}
```

CLI:
```bash
kernel browsers telemetry events <session-id> --categories network --types proxy_error --since 1h --all
```

---

## 5. Exporting to OpenTelemetry Backends (OTLP)

Events are exported as OTLP **logs** only (no traces or metrics); Kernel appends `/v1/logs`. Resource `service.name` is `kernel-browser`; each record carries `kernel.event.type`, `kernel.event.category`, `kernel.event.seq`. Export runs alongside storage and streaming. Every captured category except `screenshot` and `monitor` is exported.

### 1. Register an org-scoped destination
Create, update, and delete need an organization-scoped credential (a project-scoped key gets `403`); project keys can list, retrieve, and select a destination. Limits: 50 destinations per org, name `^[a-zA-Z0-9._-]{1,255}$` (unique, not Kernel-ID-shaped), up to 32 headers totalling 8,192 bytes. The endpoint is the collector base URL: `http`/`https`, public IP, no query or fragment, <= 2,048 chars, no redirects followed, and **no** `/v1/logs`, `/v1/traces`, or `/v1/metrics` suffix (rejected). Header values are write-only (responses show empty values).

```ts
const dest = await kernel.telemetry.destinations.create({
  name: 'honeycomb-prod',
  endpoint: 'https://api.honeycomb.io',
  description: 'Production browser telemetry',
  headers: { 'x-honeycomb-team': process.env.HONEYCOMB_API_KEY! },
});

// Delivery health covers every session using the destination (id or name):
const info = await kernel.telemetry.destinations.retrieve(dest.id);
console.log(info.consecutive_failures, info.last_export_at, info.last_error);

// Rotate a key without restarting sessions; updates merge header by header, null deletes one:
await kernel.telemetry.destinations.update('honeycomb-prod', {
  headers: { 'x-honeycomb-team': process.env.HONEYCOMB_API_KEY_NEXT! },
});
```

CLI: `kernel telemetry destinations create --name honeycomb-prod --endpoint https://api.honeycomb.io --header "x-honeycomb-team=$KEY"`; `update ... --header ...` / `--remove-header`; `get`, `delete`. Deleting an in-use destination returns `409`.

### 2. Bind it at session creation
Capture must be enabled in the same request (`enabled: true` or a category list), otherwise the request fails. Provide exactly one of `id` or `name`; setting a destination turns export on.

```ts
await kernel.browsers.create({
  stealth: true,
  telemetry: {
    browser: { network: { enabled: true }, console: { enabled: true } },
    export: { otlp: { destination: { id: dest.id } } }, // or { name: 'honeycomb-prod' }
  },
});
```

The destination is fixed at creation (`browsers.update` ignores `telemetry.export`); turning capture off also stops export. Browser pools reject `telemetry.export` with `400`. `browsers.retrieve(id)` reports `telemetry.export.otlp`. Managed-auth connections export through `browser.telemetry`: on update it replaces the stored config instead of merging (repeat the categories), and on a single login it applies to that login only.

---

## 6. Replays: audio, framerate, chapters

```ts
const replay = await kernel.browsers.replays.start(session.session_id, {
  record_audio: true,          // default false (video only); browser sessions play audio by default (docs changelog)
  framerate: 30,               // > 20 requires gpu: true
  max_duration_in_seconds: 600,
});
```

The platform can stamp named markers into recordings as MP4 chapters (docs changelog, Jul 31). No SDK or CLI call for adding a marker is documented; do not write code that assumes one.
