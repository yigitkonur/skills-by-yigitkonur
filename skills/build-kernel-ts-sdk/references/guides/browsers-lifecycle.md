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
  viewport: { width: 1920, height: 1080 }, // browser WINDOW size (default 1920x1080@25); refresh_rate auto-derived when omitted
  profile: { name: 'user-123', save_changes: true }, // persist cookies/storage
  proxy: { mode: 'default' },       // typed proxy config — exactly one of mode | id | name
  region: 'us-east',                // 'us-east' | 'us-west' | 'eu-west' | 'ap-southeast'; FIXED at create; plan-gated
  name: 'checkout-run-42',          // unique among active sessions; usable anywhere an id is
  tags: { team: 'growth', env: 'prod' }, // up to 50 pairs; filter via browsers.list({ tags })
  start_url: 'https://example.com', // best-effort navigation on boot
  memory: '8GiB',                   // '8GiB' | '16GiB'; headful non-GPU only, defaults 8GiB
  gpu: false,                       // headful only; Start-Up/Enterprise plan; us-east only
  // video_memory: '4GiB',          // '2GiB' (default) | '4GiB'; requires gpu: true
  kiosk_mode: false,                // hide address bar and tabs in live view
  chrome_policy: {                  // Chrome Enterprise Policies
    DefaultPopupsSetting: 1,        // allow popups
    DownloadRestrictions: 0,        // allow downloads
    PrintingEnabled: true,
    PrintPdfAsImageDefault: false,
  },                              // kernel-managed policies (extensions, proxy, CDP/automation) are rejected; payload <= 5 MiB
  extensions: [{ name: 'my-ext' }], // pre-installed extensions; each by id or name
  vaults: [{ id: 'vlt_123' }],       // project-scoped credential or payment vaults linked at create (immutable)
  network: {
    allowed_hosts: ['example.com', '*.example.com'], // egress allowlist
    private_hosts: ['10.0.0.0/8'],                  // direct microVM network routing
    proxy_routes: [                                 // per-host proxy routing
      { hosts: ['*.auth.site.com'], proxy: { name: 'dedicated-isp' } }
    ],
  },
  telemetry: {                      // omit = no capture; { enabled: true } = default set (control, connection, system, captcha)
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
- `headless`: Headless Chromium image (1 GB memory vs 8 GB headful; some bot detectors notice it; no live view, no replays). Headful sessions play audio by default and include standard Ubuntu desktop fonts.
- `timeout_seconds`: Inactivity seconds before termination (10 to 259,200 = 72h).
- `viewport`: `{ width, height, refresh_rate? }` window dimensions, not the page area: on headful, `window.innerHeight` is smaller than `height` because of the tab strip and toolbar (use `kiosk_mode: true`, add the UI height, or `page.setViewportSize`). Default 1920x1080@25 (GPU images 1920x1080@60). Presets that set `refresh_rate` automatically: 2560x1440@10, 1920x1080@25, 1920x1200@25, 1440x900@25, 1280x800@60, 1200x800@60, 1024x768@60, 768x1024@60, 390x844@60; other sizes are accepted but unsupported ("use at your own risk"). `refresh_rate` is ignored on headless. A custom viewport, `kiosk_mode`, or `extensions` restarts Chromium at create (several seconds); use a browser pool when that cost matters.
- `region`: `'us-east'` (default) | `'us-west'` | `'eu-west'` | `'ap-southeast'`, fixed at create, Start-Up or Enterprise plan. The docs regions page lists only us-east, eu-west, and ap-southeast; `us-west` is in the 0.120.0 SDK types and CLI. Regions give lower latency, not data residency (profiles, replays, and metadata may be processed in the US); concurrency and rate limits are shared across regions.
- `memory`: `'8GiB'` (default) or `'16GiB'` for headful non-GPU sessions.
- `gpu` & `video_memory`: GPU acceleration (headful only, `us-east` only, no standby, not available in pools). `video_memory` defaults to `'2GiB'` (4 vCPU, 6 GiB memory); `'4GiB'` gives 8 vCPU, 12 GiB memory. Replays above 20 fps need `gpu: true`.
- `profile`: `{ name, id, save_changes? }` profile snapshot binding.
- `proxy`: `{ mode: 'direct' | 'default', id?: string, name?: string }` typed proxy config.
- `network`:
  - `allowed_hosts`: Destinations not matching an entry are rejected with 403 `X-Kernel-Proxy-Error: network_policy_denied`. Only an allowlist the browser was created with can be changed at runtime; a browser created without one cannot be given one later, and an allowlist removed with `null` cannot be added back. An empty list `[]` is invalid. Entries: exact hostnames, one leading `*.` wildcard (subdomains at any depth, not the bare domain), public IPv4/IPv6 addresses, or public CIDRs; no ports, paths, or schemes; max 100 (CLI); `start_url` must be allowed. Needs proxy v3; create-time allowlists are gated by an org flag (0.120.0 changelog). Enforced at Kernel's egress proxy only: `private_hosts` destinations and VM processes that bypass the browser proxy are not filtered. Runtime updates take effect within seconds (open connections close within ~30 s). Pools support it too.
  - `private_hosts`: Route directly through VM network (e.g. Tailscale/VPN). Defaults to RFC1918, CGNAT `100.64.0.0/10`, and IPv6 ULA; `[]` disables direct routing. Providing a list **replaces** the defaults. Max 32 entries of <= 255 chars: hostnames, one leading `*.` wildcard, private IPs (IPv6 bracketed `[fd00::1]`), canonical private CIDRs; hostnames and exact IPs may carry a port, CIDRs may not. IP/CIDR entries only match URLs written with a literal IP, so add private DNS names explicitly. Not the same as a proxy's `bypass_hosts`. Immutable at create (CLI `--private-host`).
  - `proxy_routes`: Per-host proxy routing, create-time only. Matching requests fail closed if the route's proxy becomes unavailable. Browser pools support routes too.
- `chrome_policy`: Chrome Enterprise Policies (e.g. `DefaultPopupsSetting`, `DownloadRestrictions`, `PrintingEnabled`, `HomepageLocation`). Rejected: kernel-managed policies (extensions, proxy, CDP/automation); `DeveloperToolsAvailability: 2` is rejected, `1` re-enables DevTools on policy-installed extensions. Keep `PrintingEnabled: true` for `page.pdf()` / `Page.printToPDF`. `URLBlocklist` + `URLAllowlist` lock top-level navigation (other URLs fail with `ERR_BLOCKED_BY_ADMINISTRATOR`). Also settable on browser pools.
- `telemetry`: `{ enabled: true }` captures the default set; category toggles nest under `telemetry.browser.<category>.enabled`; `export` and `storage` are covered in [telemetry.md](telemetry.md).
- `kiosk_mode`: Hide address bar and tabs in live view (restarts Chromium at create).
- `extensions`: Pre-installed extensions by ID or name (immutable at create; each needs an unpacked zip with `manifest.json` uploaded via `kernel.extensions.upload({ file, name })`). Loading restarts Chromium. Live loading via `kernel.browsers.loadExtensions` can disrupt active CDP connections (docs: restart; SDK: live CDP activation when eligible, restart when enterprise policy requires it or activation fails).
- `vaults`: Project-scoped credential or payment vaults linked at create (immutable; up to 20 references).
- `invocation_id`: Tag with parent invocation for automatic cleanup.
- `start_url`: Initial navigation. When passed to `browsers.update` with a profile load, it navigates and collapses all restored tabs onto a single page.
- `@deprecated proxy_id`: Deprecated in `@onkernel/sdk@0.88.0` (2026-08-10) in favor of typed `proxy` object. Cannot be combined with `proxy`.
- `@deprecated disable_default_proxy`: Deprecated in favor of `proxy: { mode: 'direct' }`.
- *(Note on browser pools: Neither `pool_id` nor `pool` is a creation parameter on `kernel.browsers.create()`. `pool?: BrowserPoolRef` is strictly an output response property indicating which pool the browser was leased from. Browsers are acquired from a pool via `kernel.browserPools.acquire()`.)*

**Immutable Parameters**: `region`, `vaults`, `headless`, `gpu`, `video_memory`, `memory`, `stealth`, `kiosk_mode`, `timeout_seconds`, initial `extensions`, `network.private_hosts`, `network.proxy_routes`, and `chrome_policy` are fixed at creation time.

Returns `BrowserCreateResponse`:
- `session_id`: Unique identifier for all operations (`deleteByID`, `fs`, `replays`, `repl`, etc.).
- `cdp_ws_url`: WebSocket URL for Playwright/Puppeteer/Stagehand.
- `webdriver_ws_url`: WebDriver BiDi URL.
- `browser_live_view_url`: Interactive remote-control URL (headful only).
- `base_url`: Metro-API HTTP base URL for the session; the SDK routes `curl`, `computer`, `playwright`, `process`, `fs`, and stream sub-resources there directly.
- `profile_save_changes`: Boolean confirming whether profile changes will persist on termination.

---

## 2. Inspect and Update a Live Session

- `kernel.browsers.retrieve(idOrName)` — Retrieve session details (`region`, `memory`, `usage`, `pool`, `profile`, `tags`, `telemetry`, URLs). Accepts either `session_id` or `name`; `{ include_deleted: true }` includes soft-deleted sessions.
- `kernel.browsers.update(idOrName, { name?, tags?, profile?, proxy?, viewport?, telemetry?, start_url?, network? })` — Mutate a live session (`profile` can only be loaded into a browser created without one, and loading restarts Chromium, so reconnect CDP clients):
  - `start_url`: Navigates the live session. When accompanied by loading a profile, it collapses all restored tabs onto a single page.
  - `tags`: Replaces the entire tag set (not a shallow merge). Passing `{}` clears all tags.
  - `viewport`: `{ width, height, force?: boolean }`. Resizing is refused while a live view or recording is active unless `force: true` (CLI `--force`); forcing stops the recording and restarts it as a separate segment. Headless resize restarts Chromium.
  - `network`: `allowed_hosts: string[] | null`. Only editable if the session was created with an allowlist; set to `null` to remove and return to unfiltered egress.
- `kernel.browsers.list({ status?, region?, tags?, query? })` — Auto-paginating session listing (`status`: `'active'` default, `'deleted'`, or `'all'`; `include_deleted` is deprecated). Filter by `region` (`'us-east' | 'us-west' | 'eu-west' | 'ap-southeast'`), `tags` (all pairs must match), or search `query` (matches name, session ID, profile name or ID, proxy ID, or pool name).
- `kernel.browsers.loadExtensions(idOrName, { extensions: [{ name, zip_file }] })` — Live ad-hoc extension loading into a running browser instance.

---

## 3. Standby Mode (Automatic)

After **5 seconds** with zero activity, the browser automatically enters **standby**:
- Activity sources: (1) Connected CDP client, (2) Connected WebDriver/BiDi client, (3) Attached Live View client, or (4) Active `computer.*` request. An SSH connection does not count.
- Compute usage drops to zero during standby, but a standby browser still holds its concurrency slot; delete it to free the slot.
- The `timeout_seconds` countdown to deletion begins at standby entry; any active connection resets the countdown.
- **GPU browsers do not standby** — they bill continuously at the GPU rate.
- CDP websockets typically stay open up to ~1 hour; the browser keeps running, so reconnect to the same `cdp_ws_url` and add reconnect logic.
- `browsers.create` has its own per-org rate limit (`429` with `Retry-After`; the SDK retries 2x); acquiring from a [browser pool](../patterns/profiles-pools-credentials.md) is not subject to it.

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
- Everything in the VM (downloads, files written through `fs`) is permanently deleted when the browser is deleted or times out, and `browser_live_view_url` stops working. Download replays and files first.
- `timeout_seconds` is polled every 5 s, so expect +/- 5 s around the value.

---

## 5. Control Surfaces & Subresources

Each browser session provides multiple subresources:
- `kernel.browsers.playwright.execute(id, { code, timeout_sec?, executor? })` — In-VM Playwright execution with zero network latency. Pass `executor: 'name'` to target one of up to 8 dedicated executor processes for multi-tab concurrency. Submitted code (up to 8 KB) is captured in `control` telemetry.
- `kernel.browsers.playwright.executors.list(id)` / `delete(name, { id_or_name, close_tab? })` — Manage named in-VM Playwright executors.
- `kernel.browsers.computer.*` — Computer use primitives (`captureScreenshot`, `clickMouse`, `moveMouse`, `dragMouse`, `getMousePosition`, `typeText`, `pressKey`, `scroll`, `setCursorVisibility`, `readClipboard`, `writeClipboard`, `batch`).
- `kernel.browsers.repl(id, { code, reset?, timeout_sec? })` — In-VM stateful Node.js REPL and Code Mode.
- `kernel.browsers.webmcp.*` — Discovery and invocation of WebMCP page tools (`listTools`, `invokeTool`) and custom tools (`customTools.add/list/remove`), including polyfill-registered tools.
- `kernel.browsers.curl(id, { url, ... })` — HTTP requests exiting through Chromium's TLS fingerprint and proxy; `kernel.browsers.fetch(id, url, init)` streams the response.
- `kernel.browsers.fs.*` — MicroVM filesystem operations (`readFile`, `writeFile`, `uploadZip`, `watch`).
- `kernel.browsers.process.*` — In-VM shell process execution (`exec`, `spawn` with `allocate_tty`, `status`, `kill`, `stdin`, `stdoutStream`, `resize`).
- `kernel.browsers.logs.stream(id, { source: 'path' | 'supervisor', follow?, path?, supervisor_process? })` — SSE log stream (`path` required for `source: 'path'`).
- `kernel.browsers.replays.*` — Video screen recordings (`start`, `stop`, `list`, `download`); `start` takes `record_audio`, `framerate`, `max_duration_in_seconds`.
- `kernel.browsers.telemetry.*` — Streaming and historical telemetry (`stream`, `events`).
- SSH into the VM: `kernel browsers ssh <id>` (CLI only); see [stealth-and-config-registry.md](stealth-and-config-registry.md).

---

## 6. Live View

`browser_live_view_url` (headful only) opens the interactive view; append `?readOnly=true` for a non-interactive one, or embed it in an iframe (`allow="autoplay; clipboard-read; clipboard-write"`). With a Content Security Policy add `frame-src https://*.onkernel.com:8443 https://*.kernel.sh:8443; connect-src https://*.onkernel.com:8443 wss://*.onkernel.com:8443 https://*.kernel.sh:8443 wss://*.kernel.sh:8443`. The iframe posts `KERNEL_CONNECTED`, `KERNEL_PLAYING`, `KERNEL_PAUSED`, `KERNEL_CONNECTION_TIMEOUT`, and `KERNEL_CONNECTION_FAILED` to the parent and accepts `KERNEL_SET_READ_ONLY { readOnly }`; gate on `KERNEL_PLAYING` to detect a viewer that never started.

---

## 7. Where to Look Next

- Dedicated Proxy Guide: `references/guides/proxies.md`
- Multi-Provider Search API: `references/guides/search.md`
- In-VM Browser REPL & Code Mode: `references/patterns/browser-repl.md`
- WebMCP Tool Integration: `references/patterns/webmcp.md`
- Picking the right control surface: `references/patterns/browser-control-surfaces.md`
- Dedicated CLI commands: `references/guides/cli-reference.md`
- Vaults and payments: `references/patterns/vaults-and-payments.md`
- Browser telemetry and OTLP export: `references/guides/telemetry.md`
- Stealth, config registry, Web Bot Auth, SSH: `references/guides/stealth-and-config-registry.md`
- Profiles and pools: `references/patterns/profiles-pools-credentials.md`
- Troubleshooting and gotchas: `references/troubleshooting/pitfalls.md`
