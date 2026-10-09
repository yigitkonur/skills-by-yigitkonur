# Browser Telemetry

Kernel allows real-time streaming, historical querying, and OpenTelemetry (OTLP) export of browser session events, network requests, console output, and security challenges.

## Telemetry Architecture

1. **Operational Categories (Default On):** When telemetry is active on a session, these categories capture events automatically:
   - `control` — Session lifecycle, resizing, and supervisor actions.
   - `connection` — CDP, WebSocket, and Live View connection/disconnection events.
   - `system` — VM-level resource health, memory pressure, and browser crashes.
   - `captcha` — Detection and solving progress (`captcha_solve_started`, `captcha_solved`, `captcha_failed`), including `challenge_id` and `captcha_type`.
2. **CDP & Opt-in Categories:** Off by default; must be explicitly enabled:
   - `console` — Chromium `console.log`, `warn`, `error`.
   - `network` — HTTP request/response metadata, headers, status codes, and timing.
   - `page` — DOM lifecycle events, navigation starts, DOMContentLoaded.
   - `interaction` — Mouse, keyboard, and touch events dispatched to Chromium.
   - `screenshot` — Periodic visual frames.
   - `platform` — Kernel virtualization platform events.

---

## 1. Enabling Telemetry on Session Creation or Update

Pass the `telemetry` object on `browsers.create` or `browsers.update`:

```ts
import Kernel from '@onkernel/sdk';
const kernel = new Kernel();

const session = await kernel.browsers.create({
  stealth: true,
  telemetry: {
    enabled: true,
    // Opt into specific non-operational categories:
    network: true,
    console: true,
    page: true,
  },
});
```

CLI equivalent:

```bash
# Enable all categories:
kernel browsers create --telemetry=all

# Enable specific list:
kernel browsers create --telemetry=control,connection,system,captcha,network,console
```

---

## 2. Real-Time Streaming (`telemetry.stream`)

Stream live session events over Server-Sent Events (SSE):

```ts
const stream = await kernel.browsers.telemetry.stream(session.session_id, {
  // replay: 'all',          // optionally replay events from session start
  // 'Last-Event-ID': 'evt_123',
});

for await (const event of stream) {
  console.log(`[${event.timestamp}] ${event.category}/${event.type}:`, event.data);

  // First-class proxy error correlation:
  if (event.type === 'proxy_error') {
    console.error('Proxy failed:', event.data.error_code, event.data.details);
  }

  // First-class CAPTCHA solving events:
  if (event.type === 'captcha_solve_started') {
    console.log(`Solving ${event.data.captcha_type}, challenge: ${event.data.challenge_id}`);
  }
}
```

CLI equivalent:

```bash
kernel browsers telemetry stream <session_id>
```

---

## 3. Historical Events Querying (`telemetry.events`)

Archived session telemetry is retained for **30 days** and can be queried with filtering:

```ts
const history = await kernel.browsers.telemetry.events(session.session_id, {
  categories: ['captcha', 'control'],
  types: ['captcha_solve_started', 'proxy_error'],
  start_time: '2026-10-01T00:00:00Z',
  end_time: '2026-10-09T00:00:00Z',
  limit: 100,
});

for (const event of history.events) {
  console.log(event.id, event.type, event.timestamp);
}
```

CLI equivalent:

```bash
kernel browsers telemetry events <session_id> --category captcha,control --type proxy_error
```

---

## 4. Exporting to OpenTelemetry Backends (OTLP)

Export session telemetry directly to Datadog, Honeycomb, New Relic, or self-hosted OpenTelemetry collectors.

### 1. Register Org-Scoped Destination

OTLP destinations are managed at the organization level (`POST /org/telemetry/destinations`):

```ts
const dest = await kernel.telemetry.destinations.create({
  name: 'prod-datadog',
  url: 'https://otlp-http.datadoghq.com/v1/traces',
  protocol: 'http_protobuf', // or 'http_json'
  headers: {
    'DD-API-KEY': process.env.DD_API_KEY!,
  },
});
```

CLI equivalent:

```bash
kernel telemetry destinations create \
  --name prod-datadog \
  --url https://otlp-http.datadoghq.com/v1/traces \
  --protocol http_protobuf \
  --header "DD-API-KEY=$DD_API_KEY"
```

### 2. Bind Destination to Browser Session

Route session telemetry to the configured destination at creation time:

```ts
const session = await kernel.browsers.create({
  stealth: true,
  telemetry: {
    enabled: true,
    network: true,
    export: {
      otlp: {
        destination_id: dest.id,
      },
    },
  },
});
```
