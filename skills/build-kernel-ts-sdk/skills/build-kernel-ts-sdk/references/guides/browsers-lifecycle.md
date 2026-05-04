# Browsers lifecycle

A Kernel browser is a unikernel-isolated VM running headful (default) or headless Chromium. Lifecycle: **create → use → standby (auto) → terminate**.

## Create

```ts
const session = await kernel.browsers.create({
  stealth: true,                    // anti-detection; default for production
  headless: false,                  // headful default; live-view + replays require headful
  timeout_seconds: 300,             // auto-delete after N seconds idle (default 60, max 259200)
  viewport: { width: 1920, height: 1080 }, // refresh-rate auto-determined
  profile: { name: 'user-123', save_changes: true }, // persist cookies/storage
  proxy_id: 'proxy_xyz',            // optional Kernel-managed proxy
  kiosk_mode: false,                // hide address bar in live view
  gpu: false,                       // headful + paid plan only
  extensions: [{ name: 'my-ext' }], // pre-installed extensions
  invocation_id: '…',               // tag with parent invocation for cleanup-on-stop
});
```

Returns `BrowserCreateResponse`:

| Field | Use |
|---|---|
| `session_id` | The handle for every other call (`deleteByID`, `fs`, `replays`, etc.) |
| `cdp_ws_url` | Pass to Playwright/Puppeteer/Stagehand: `chromium.connectOverCDP(cdp_ws_url)` |
| `webdriver_ws_url` | WebDriver BiDi clients (Vibium etc.) |
| `browser_live_view_url` | Iframe-able human handoff URL (only when `headless: false`) |
| `base_url` | The browser VM's exposed HTTP base (used by `fs`, `process`, `computer`, `playwright.execute`) |

## Sensible defaults

- `stealth: true` for any user-facing scenario or any commercial site.
- `timeout_seconds: 300` minimum; bump for long sessions. The 60s default reaps too aggressively.
- Headful for live view, replays, GPU. Headless for fast scripted scrapes (~8× cheaper).
- Use `profile.name` for any flow that needs login state across sessions.

## Use

Three control surfaces. Pick one per task — see `references/patterns/browser-control-surfaces.md` for the decision tree.

```ts
import { chromium } from 'playwright';

// 1. Raw CDP — long-lived sessions, full Playwright API on your machine
const browser = await chromium.connectOverCDP(session.cdp_ws_url);
const ctx = browser.contexts()[0];          // never browser.newContext()
const page = ctx.pages()[0];                // never ctx.newPage()
await page.goto('https://example.com');

// 2. Playwright-execute inside the browser VM — hot paths, no CDP roundtrip
const { result } = await kernel.browsers.playwright.execute(session.session_id, {
  code: 'await page.goto("https://example.com"); return await page.title();',
  timeout_sec: 60,                              // default 60
});

// 3. Computer-controls — vision-loop / VLM driven, no CDP at all
await kernel.browsers.computer.captureScreenshot(session.session_id);
await kernel.browsers.computer.clickMouse(session.session_id, { x: 100, y: 200, button: 'left' });
await kernel.browsers.computer.typeText(session.session_id, { text: 'hello' });
```

## Standby (automatic)

After **5 seconds** with no CDP or live-view connection, the browser enters **standby**:

- VM state is preserved.
- Compute usage drops to zero.
- The `timeout_seconds` countdown to deletion **continues running**.
- GPU browsers do not standby.

Reconnecting (CDP open or live-view load) wakes the browser. There is no API to force standby; it is purely connection-driven.

## Terminate

Always pair `create` with `deleteByID`:

```ts
try {
  const session = await kernel.browsers.create({ stealth: true, timeout_seconds: 300 });
  try {
    // … work …
  } finally {
    await kernel.browsers.deleteByID(session.session_id);
  }
} catch (err) { /* … */ }
```

- `kernel.browsers.deleteByID(id)` — preferred.
- `kernel.browsers.delete({ persistent_id })` — **deprecated**; relates to the old persistence model.
- If you forget: the browser auto-deletes after `timeout_seconds` of inactivity (CDP + live-view both idle).
- Calling Playwright `browser.close()` does **not** delete the Kernel browser — it only severs your local CDP connection.

## Live view

Headful sessions return `browser_live_view_url`. This is a fully interactive remote-control page:

- Embed in an iframe for human-in-the-loop handoff
- Append `?readOnly=true` to make it observe-only
- `kiosk_mode: true` at create time hides the address bar

Live view counts as an active connection — opening it prevents standby.

## Viewports and refresh rate

`viewport: { width, height }` controls the rendered dimensions. Refresh rate is auto-tuned based on resolution and plan. Larger viewports increase rendering cost; pick the smallest viewport that still triggers responsive breakpoints you need.

## Headful vs headless trade-offs

| | Headful (default) | Headless |
|---|---|---|
| Image size | ~8 GB | ~1 GB |
| Boot time | Slower | Faster |
| Live view | Yes | No |
| Replays | Yes | No |
| GPU | Yes | No |
| Detection risk | Lower | Some sites flag headless |
| Cost | Higher | ~8× cheaper |

## Profiles

A profile stores cookies, localStorage, IndexedDB, and login state across sessions:

```ts
// First session — log in and save changes
await kernel.browsers.create({
  profile: { name: 'user-123', save_changes: true },
});
// … perform login …
// Profile snapshot is taken on browser termination.

// Subsequent sessions — load the saved state
await kernel.browsers.create({
  profile: { name: 'user-123' /* save_changes default false */ },
});
```

For end-user credentials, use Managed Auth instead of asking the user for their password — see `references/guides/managed-auth.md`.

Profile management API: `kernel.profiles.create / retrieve / list / delete / download`. Use `download` to back up profile archives off-platform.

## Replays

Captured `.webm` recordings of the browser session. Headful only. Multiple per session allowed.

```ts
const r = await kernel.browsers.replays.start(session.session_id);
// … work …
await kernel.browsers.replays.stop(r.replay_id, { id: session.session_id });

const all = await kernel.browsers.replays.list(session.session_id);
const dl = await kernel.browsers.replays.download(r.replay_id, { id: session.session_id });
const buffer = Buffer.from(await dl.arrayBuffer());
```

See `references/troubleshooting/files-and-replays.md` for download timing and size gotchas.

## Stop sequence and `invocation_id`

If you are inside a Kernel App action, tag every browser you create with the parent `invocation_id`:

```ts
await kernel.browsers.create({ invocation_id: ctx.invocation_id, stealth: true });
```

Then `kernel.invocations.update(id, { status: 'failed' })` (or a graceful stop) reaps every browser tagged to that invocation. Without the tag, an aborted invocation leaves orphan browsers running until their `timeout_seconds` elapses.

## Per-browser HTTP, files, processes, logs

Each browser VM exposes more than the Chromium surface:

- `kernel.browsers.curl(id, { url, method, headers, body, timeout_ms, response_encoding })` — HTTP through Chrome's TLS fingerprint
- `kernel.browsers.fs.*` — read/write files, watch directories
- `kernel.browsers.process.*` — exec/spawn inside the VM (PTY, stdin/stdout streaming)
- `kernel.browsers.logs.stream(id)` — VM-level log events

See `references/troubleshooting/files-and-replays.md` for `fs` patterns.

## Where to look next

- Picking the right control surface: `references/patterns/browser-control-surfaces.md`
- Stagehand or Playwright wiring: `references/patterns/playwright-stagehand-integration.md`
- Profiles, pools, and credential providers: `references/patterns/profiles-pools-credentials.md`
- Common foot-guns: `references/troubleshooting/pitfalls.md`
