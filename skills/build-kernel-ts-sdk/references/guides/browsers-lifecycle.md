# Browsers Lifecycle & Virtual Machines

A Kernel browser is a unikernel-isolated microVM running headful (default) or headless Chromium. Lifecycle: **create → use → standby (auto) → terminate**.

---

## 1. Create a Browser Session

```ts
import Kernel from '@onkernel/sdk';
const kernel = new Kernel();

const session = await kernel.browsers.create({
  stealth: true,                    // anti-detection + CAPTCHA solver; default for production
  headless: false,                  // headful default; live-view + replays require headful
  timeout_seconds: 300,             // idle seconds before auto-delete (default 60, min 10, max 259200 = 72h)
  viewport: { width: 1920, height: 1080 }, // browser WINDOW size; refresh_rate auto-derived when omitted
  profile: { name: 'user-123', save_changes: true }, // persist cookies/storage
  proxy: { mode: 'default' },       // typed proxy config — exactly one of mode | id | name
  region: 'us-east',                // 'us-east' | 'us-west' | 'eu-west' | 'ap-southeast'; FIXED at create
  name: 'checkout-run-42',          // unique among active sessions; usable anywhere an id is
  tags: { team: 'growth', env: 'prod' }, // up to 50 pairs; filter via browsers.list({ tags })
  start_url: 'https://example.com', // best-effort navigation on boot
  memory: '8GiB',                   // '8GiB' | '16GiB'; headful non-GPU only, defaults 8GiB
  gpu: false,                       // headful only; Start-Up/Enterprise plan; us-east only
  video_memory: '4GiB',             // '2GiB' | '4GiB' (when gpu: true)
  kiosk_mode: false,                // hide address bar and tabs in live view
  chrome_policy: {                  // Chrome Enterprise Policies
    DefaultPopupsSetting: 1,        // allow popups
    DownloadRestrictions: 0,        // allow downloads
    PrintingEnabled: true,
    PrintPdfAsImageDefault: false,
  },
  extensions: [{ name: 'my-ext' }], // pre-installed extensions; each by id or name
  vaults: [{ id: 'vlt_123' }],       // project-scoped credential or payment vaults linked at create (immutable)
  network: {
    allowed_hosts: ['example.com', '*.example.com'], // egress allowlist
    private_hosts: ['10.0.0.0/8'],                  // direct microVM network routing
    proxy_routes: [                                 // per-host proxy routing
      { hosts: ['*.auth.site.com'], proxy: { name: 'dedicated-isp' } }
    ],
  },
  telemetry: {
    browser: {
      network: { enabled: true },
      console: { enabled: true },
    },
  },
  invocation_id: '…',               // tag with parent invocation for cleanup-on-stop
});
```

### Parameter Reference & Invariants
- `stealth`: Anti-detection browser fingerprinting + automated CAPTCHA solver.
- `headless`: Headless Chromium image. Headful sessions play audio by default and include standard Ubuntu desktop fonts; headless sessions mute audio by default.
- `timeout_seconds`: Inactivity seconds before termination (10 to 259,200 = 72h).
- `viewport`: `{ width, height, refresh_rate? }` window dimensions.
- `memory`: `'8GiB'` (default) or `'16GiB'` for headful non-GPU sessions.
- `gpu` & `video_memory`: GPU acceleration with `'2GiB'` or `'4GiB'` dedicated VRAM (`us-east` only).
- `profile`: `{ name, id, save_changes? }` profile snapshot binding.
- `proxy`: `{ mode: 'direct' | 'default', id?: string, name?: string }` typed proxy config.
- `network`:
  - `allowed_hosts`: Destinations not matching an entry are rejected with 403 `X-Kernel-Proxy-Error: network_policy_denied`. Only an allowlist the browser was created with can be changed at runtime; a browser created without one cannot be given one later, and an allowlist removed with `null` cannot be added back. An empty list `[]` is invalid.
  - `private_hosts`: Route directly through VM network (e.g. Tailscale/VPN). Defaults to RFC1918, CGNAT `100.64.0.0/10`, and IPv6 ULA; `[]` disables direct routing. Immutable at create.
  - `proxy_routes`: Per-host proxy routing. Create-time only for individual sessions.
- `chrome_policy`: Chrome Enterprise Policies (e.g. `DefaultPopupsSetting`, `DownloadRestrictions`, `PrintingEnabled`, `HomepageLocation`).
- `telemetry`: Category toggles nested under `telemetry.browser.<category>.enabled`.
- `kiosk_mode`: Hide address bar and tabs in live view.
- `extensions`: Pre-installed extensions by ID or name (immutable at create; live extensions loaded via `kernel.browsers.loadExtensions`).
- `vaults`: Project-scoped credential or payment vaults linked at create (immutable; up to 20 references).
- `invocation_id`: Tag with parent invocation for automatic cleanup.
- `start_url`: Initial navigation. When passed to `browsers.update` with a profile load, it navigates and collapses all restored tabs onto a single page.
- `@deprecated proxy_id`: Deprecated in `@onkernel/sdk@0.88.0` (August 10/14, 2026) in favor of typed `proxy` object. Cannot be combined with `proxy`.
- `@deprecated disable_default_proxy`: Deprecated in favor of `proxy: { mode: 'direct' }`.
- *(Note on browser pools: Neither `pool_id` nor `pool` is a creation parameter on `kernel.browsers.create()`. `pool?: BrowserPoolRef` is strictly an output response property indicating which pool the browser was leased from. Browsers are acquired from a pool via `kernel.browserPools.acquire()`.)*

**Immutable Parameters**: `region`, `vaults`, `headless`, `gpu`, `video_memory`, `memory`, `stealth`, `kiosk_mode`, `timeout_seconds`, initial `extensions`, `network.private_hosts`, `network.proxy_routes`, and `chrome_policy` are fixed at creation time.

Returns `BrowserCreateResponse`:
- `session_id`: Unique identifier for all operations (`deleteByID`, `fs`, `replays`, `repl`, etc.).
- `cdp_ws_url`: WebSocket URL for Playwright/Puppeteer/Stagehand.
- `webdriver_ws_url`: WebDriver BiDi URL.
- `browser_live_view_url`: Interactive remote-control URL (headful only).
- `base_url`: MicroVM internal HTTP endpoint.
- `profile_save_changes`: Boolean confirming whether profile changes will persist on termination.

---

## 2. Inspect and Update a Live Session

- `kernel.browsers.retrieve(idOrName)` — Retrieve session details (`region`, `memory`, `usage`, `pool`, `profile`, `tags`, `telemetry`, URLs). Accepts either `session_id` or `name`.
- `kernel.browsers.update(idOrName, { name?, tags?, profile?, proxy?, viewport?, telemetry?, start_url?, network? })` — Mutate a live session:
  - `start_url`: Navigates the live session. When accompanied by loading a profile, it collapses all restored tabs onto a single page.
  - `tags`: Replaces the entire tag set (not a shallow merge). Passing `{}` clears all tags.
  - `viewport`: `{ width, height, force?: boolean }`. Pass `force: true` (CLI `--force`) to force resizing even if active live views or recordings are attached.
  - `network`: `allowed_hosts: string[] | null`. Only editable if the session was created with an allowlist; set to `null` to remove and return to unfiltered egress.
- `kernel.browsers.list({ status?, region?, tags?, query? })` — Auto-paginating session listing (`status` defaults to `'active'`). Filter by `region` (`'us-east' | 'us-west' | 'eu-west' | 'ap-southeast'`), `tags`, or search `query` (matches session ID, name, or profile name).
- `kernel.browsers.loadExtensions(idOrName, { extensions: [{ name, zip_file }] })` — Live ad-hoc extension loading into a running browser instance.

---

## 3. Standby Mode (Automatic)

After **5 seconds** with zero activity, the browser automatically enters **standby**:
- Activity sources: (1) Connected CDP client, (2) Connected WebDriver/BiDi client, (3) Attached Live View client, or (4) Active `computer.*` request.
- Compute usage drops to zero during standby.
- The `timeout_seconds` countdown to deletion begins at standby entry; any active connection resets the countdown.
- **GPU browsers do not standby** — they bill continuously at the GPU rate.

---

## 4. Termination

Always pair `create` with `deleteByID` in a `finally` block:

```ts
try {
  const session = await kernel.browsers.create({ stealth: true, timeout_seconds: 300 });
  try {
    // automation work
  } finally {
    await kernel.browsers.deleteByID(session.session_id);
  }
} catch (err) {
  // handle error
}
```

- `kernel.browsers.deleteByID(idOrName)` is the **only** delete method on `kernel.browsers`. There is no `kernel.browsers.delete`.
- Calling Playwright `browser.close()` does **not** terminate the Kernel browser VM — it only severs the local WebSocket.

---

## 5. Control Surfaces & Subresources

Each browser session provides multiple subresources:
- `kernel.browsers.playwright.execute(id, { code, timeout_sec?, executor? })` — In-VM Playwright execution with zero network latency. Pass `executor: 'name'` to target one of up to 8 dedicated executor processes for multi-tab concurrency. Submitted code (up to 8 KB) is captured in `control` telemetry.
- `kernel.browsers.playwright.executors.list(id)` / `delete(name, { id_or_name })` — Manage named in-VM Playwright executors.
- `kernel.browsers.computer.*` — Computer use primitives (`captureScreenshot`, `clickMouse`, `moveMouse`, `dragMouse`, `typeText`, `pressKey`, `scroll`, `batch`).
- `kernel.browsers.repl(id, { code, reset?, timeout_sec? })` — In-VM stateful Node.js REPL and Code Mode.
- `kernel.browsers.webmcp.*` — Discovery and invocation of WebMCP page tools (`listTools`, `invokeTool`), custom tools (`customTools.add/list/remove`), and `navigator.modelContext` polyfills.
- `kernel.browsers.curl(id, { url, ... })` — HTTP requests exiting through Chromium's TLS fingerprint and proxy.
- `kernel.browsers.fs.*` — MicroVM filesystem operations (`readFile`, `writeFile`, `uploadZip`, `watch`).
- `kernel.browsers.process.*` — In-VM shell process execution (`exec`, `spawn` with `allocate_tty`).
- `kernel.browsers.replays.*` — Video screen recordings (`start`, `stop`, `list`, `download`). Replays support `record_audio: boolean` and named MP4 chapter markers.
- `kernel.browsers.telemetry.*` — Streaming and historical telemetry (`stream`, `events`).

---

## 6. Where to Look Next

- Dedicated Proxy Guide: `references/guides/proxies.md`
- Multi-Provider Search API: `references/guides/search.md`
- In-VM Browser REPL & Code Mode: `references/patterns/browser-repl.md`
- WebMCP Tool Integration: `references/patterns/webmcp.md`
- Picking the right control surface: `references/patterns/browser-control-surfaces.md`
- Dedicated CLI commands: `references/guides/cli-reference.md`
- Vaults and payments: `references/patterns/vaults-and-payments.md`
- Browser telemetry and OTLP export: `references/guides/telemetry.md`
- Profiles and pools: `references/patterns/profiles-pools-credentials.md`
- Troubleshooting and gotchas: `references/troubleshooting/pitfalls.md`
