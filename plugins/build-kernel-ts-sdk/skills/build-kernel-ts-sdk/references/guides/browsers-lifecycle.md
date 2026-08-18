# Browsers lifecycle

A Kernel browser is a unikernel-isolated VM running headful (default) or headless Chromium. Lifecycle: **create → use → standby (auto) → terminate**.

## Create

```ts
const session = await kernel.browsers.create({
  stealth: true,                    // anti-detection + CAPTCHA solver; default for production
  headless: false,                  // headful default; live-view + replays require headful
  timeout_seconds: 300,             // idle seconds before auto-delete (default 60, min 10, max 259200 = 72h; checked every 5s, so ±5s)
  viewport: { width: 1920, height: 1080 }, // browser WINDOW size; refresh_rate auto-derived when omitted
  profile: { name: 'user-123', save_changes: true }, // persist cookies/storage
  proxy: { mode: 'default' },       // typed proxy config — exactly one of mode | id | name
  region: 'us-east',                // 'us-east' | 'eu-west'; FIXED at create; Start-Up/Enterprise only
  name: 'checkout-run-42',          // unique among active sessions; usable anywhere an id is
  tags: { team: 'growth', env: 'prod' }, // up to 50 pairs; filter via browsers.list({ tags })
  start_url: 'https://example.com', // best-effort navigation on boot
  memory: '8GiB',                   // '8GiB' | '16GiB'; headful non-GPU only, defaults 8GiB
  kiosk_mode: false,                // hide address bar and tabs in live view
  gpu: false,                       // headful only; Start-Up/Enterprise plan; not available in pools
  extensions: [{ name: 'my-ext' }], // pre-installed extensions; each by id or name
  invocation_id: '…',               // tag with parent invocation for cleanup-on-stop
});
```

That is 15 of the 19 `BrowserCreateParams` fields. The remaining four are advanced: `network` (`{ private_hosts: [...] }` — route named hosts through the session's own network instead of Kernel egress; cannot be changed after creation), `chrome_policy` (Chrome enterprise policy overrides; kernel-managed policies are blocked), `telemetry`, and the `@deprecated` `proxy_id`. Read `node_modules/@onkernel/sdk/resources/browsers/browsers.d.ts` for the full doc comments.

Fixed for the life of the session: **`region`** and **`network`** are documented as unchangeable after create, and `headless`, `gpu`, `memory`, `stealth`, `kiosk_mode`, and `timeout_seconds` have no counterpart in `BrowserUpdateParams`. Only `name`, `tags`, `profile`, `proxy`, `viewport`, and `telemetry` can be changed on a running session.

`proxy_id` is `@deprecated` in v0.92.0 in favor of the typed `proxy` object, and the two **cannot be combined**. Omit `proxy` entirely to get the default (stealth → Kernel's stealth proxy, non-stealth → direct egress). `mode: 'direct'` forces direct egress even with `stealth: true`; `mode: 'default'` restores the stealth-derived default. Proxy selection changes egress only — it never enables or disables stealth or the CAPTCHA solver.

Returns `BrowserCreateResponse`:

| Field | Use |
|---|---|
| `session_id` | The handle for every other call (`deleteByID`, `fs`, `replays`, etc.) |
| `cdp_ws_url` | Pass to Playwright/Puppeteer/Stagehand: `chromium.connectOverCDP(cdp_ws_url)` |
| `webdriver_ws_url` | WebDriver BiDi clients (Vibium etc.) |
| `browser_live_view_url` | Iframe-able human handoff URL (only when `headless: false`) |
| `base_url` | The browser VM's exposed HTTP base (used by `fs`, `process`, `computer`, `playwright.execute`) |

## Inspect and update a live session

- `kernel.browsers.retrieve(idOrName)` — inspect one session. Returns `region`, `memory`, `usage`, `pool`, `profile`, `tags`, `telemetry`, `deleted_at`, and the URLs. Use this instead of scanning `list()` when you already know the session.
- `kernel.browsers.update(idOrName, { name?, tags?, profile?, proxy?, viewport?, telemetry? })` — mutate a live session. `profile` is only allowed if the session does not already have one loaded; `tags` is a full replace, not a merge. **`timeout_seconds` is not updatable** — pick it at create time.
- `kernel.browsers.list({ status?, region?, tags?, query? })` — `status` defaults to `'active'`; pass `'all'` to include soft-deleted sessions. `tags` pairs are ANDed.

Every `idOrName` parameter accepts either the `session_id` or the `name` you set at create time.

## Sensible defaults

- `stealth: true` for any user-facing scenario or any commercial site.
- `timeout_seconds: 300` as a working floor (the API minimum is 10, the default 60). The 60s default reaps too aggressively.
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

// 2. Playwright-execute inside the browser VM — hot paths, no CDP roundtrip.
// Response is { success, error?, result, stderr, stdout } — check success first.
const res = await kernel.browsers.playwright.execute(session.session_id, {
  code: 'await page.goto("https://example.com"); return await page.title();',
  timeout_sec: 60,                              // default 60, max 300
});
if (!res.success) throw new Error(res.error);
const title = res.result;

// 3. Computer-controls — vision-loop / VLM driven, no CDP at all
await kernel.browsers.computer.captureScreenshot(session.session_id);
await kernel.browsers.computer.clickMouse(session.session_id, { x: 100, y: 200, button: 'left' });
await kernel.browsers.computer.typeText(session.session_id, { text: 'hello' });
```

## Standby (automatic)

After **5 seconds** with no activity, the browser enters **standby**. Activity is any one of four things:

1. A CDP client is connected (Playwright, Puppeteer, raw CDP).
2. A WebDriver/BiDi client is connected.
3. A Live View client is connected.
4. A computer-controls API request is in flight (clicks, keypresses, screenshots).

Standby behaviour:

- VM state is preserved.
- Compute usage drops to zero.
- The `timeout_seconds` countdown to deletion **starts** at the moment the browser enters standby (not at create time). Any of the four activity sources resets the countdown.
- GPU browsers do not standby.

Reconnecting — or simply issuing the next computer-controls call — wakes the browser. There is no API to force standby; it is driven entirely by those four activity sources. A vision loop on `browsers.computer.*` holds no CDP or live-view connection, but each call still resets the idle timer, so a loop that fires more often than every 5 seconds never reaches standby and bills at the full per-second rate.

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

- `kernel.browsers.deleteByID(idOrName)` — the only delete method on `kernel.browsers`. Accepts either the `session_id` or the `name` you set at create time. There is no `kernel.browsers.delete`.
- If you forget: the browser auto-deletes after `timeout_seconds` of inactivity (all four activity sources idle).
- Calling Playwright `browser.close()` does **not** delete the Kernel browser — it only severs your local CDP connection.
- To tear down every browser an invocation created, use `kernel.invocations.deleteBrowsers(invocationId)`.

## Live view

Headful sessions return `browser_live_view_url`. This is a fully interactive remote-control page:

- Embed in an iframe for human-in-the-loop handoff
- Append `?readOnly=true` to make it observe-only
- `kiosk_mode: true` at create time hides the address bar

Live view counts as an active connection — opening it prevents standby.

## Viewports and refresh rate

`viewport: { width, height, refresh_rate? }` sets the browser **window** size, not the visible page area. On headful browsers Chromium's tab strip and toolbar occupy part of the window height, so `window.innerHeight` is less than the configured `height` and bottom-of-page content is missing from screenshots and live view. Set `kiosk_mode: true` to strip the UI so window and page dimensions match exactly, or add the UI height to your target. Headless browsers have no UI, so the page area already matches.

- `refresh_rate` is optional; omitted, it is derived from width × height (higher resolutions get lower rates to keep bandwidth reasonable). It applies to **live view only** and is ignored for headless browsers.
- Defaults when `viewport` is omitted: 1920x1080@25, or 1920x1080@60 on GPU images.
- Arbitrary dimensions and rates are accepted, but viewports outside the known-good presets (2560x1440@10, 1920x1080@25, 1920x1200@25, 1440x900@25, 1280x800@60, 1024x768@60, 390x844@60, …) can produce unstable live view or recording behaviour.
- Cost is per second by browser type (headless 1×, headful 8×, headful+GPU 48×) — there is no published viewport term in Kernel's pricing. Pick the smallest viewport that triggers the responsive breakpoints you need for correctness and rendering stability, not to save money.

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

A profile stores cookies, localStorage, IndexedDB, and login state across sessions. Direct `browsers.create({ profile: { name } })` requires the profile to already exist — call `kernel.profiles.create` first, or use Managed Auth (`auth.connections.create` auto-creates the profile if `profile_name` does not exist):

```ts
// One-time setup
await kernel.profiles.create({ name: 'user-123' });

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

Profile management API: `kernel.profiles.create / retrieve / update / list / delete / download`.

- `update(idOrName, { name })` renames. Never rename while a browser session references the profile by name — that session's `save_changes` snapshot may not save.
- `list({ name, query })` filters by exact name or by case-insensitive substring on name or ID.
- `download(idOrName, { format: 'tar.zst' | 'tar' })` backs up the profile archive off-platform. Legacy profiles are always returned as JSON regardless of `format`.

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

- `kernel.browsers.curl(id, { url, method, headers, body, timeout_ms, response_encoding })` — HTTP through Chrome's TLS fingerprint; returns a structured JSON envelope (status, headers, body, timing)
- `kernel.browsers.fetch(id, input, init)` — plain `fetch` through the VM's network stack, returns a real `Response` (use when you want `res.json()` / streaming ergonomics instead of `curl`'s envelope)
- `kernel.browsers.fs.*` — read/write files, watch directories
- `kernel.browsers.process.*` — exec/spawn inside the VM (PTY, stdin/stdout streaming)
- `kernel.browsers.logs.stream(id, { source: 'supervisor' \| 'path', path?, supervisor_process?, follow? })` — VM-level log events (`source` is required)
- `kernel.browsers.telemetry.stream(id, …)` / `kernel.browsers.telemetry.events(id, …)` — live and historical browser telemetry (enable it via `telemetry` on create or update)

See `references/troubleshooting/files-and-replays.md` for `fs` patterns.

## Where to look next

- Picking the right control surface: `references/patterns/browser-control-surfaces.md`
- Stagehand or Playwright wiring: `references/patterns/playwright-stagehand-integration.md`
- Profiles, pools, and credential providers: `references/patterns/profiles-pools-credentials.md`
- Common foot-guns: `references/troubleshooting/pitfalls.md`
