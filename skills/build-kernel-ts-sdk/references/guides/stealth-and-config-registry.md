# Stealth, Config Registry, Web Bot Auth, and SSH

Getting a browser agent through a real site: what Kernel does by default, how to find settings that already worked on a target, how to sign requests with a verifiable identity, and how to open a shell in the VM.

---

## 1. Anti-detection defaults and stealth mode

Every Kernel browser launches with the anti-detection Chromium configuration applied; no setup. `stealth: true` adds two managed services on top (both opt-out):

1. **Default proxy**: an ISP proxy from a shared Kernel pool, hosted in data centers but announced on residential ISP networks. The exit IP is static for the session; a new session may get a different IP from the pool.
2. **Automatic CAPTCHA solver**: reCAPTCHA, Cloudflare/Turnstile, hCaptcha (beta, enabled per org on request), and press-and-hold challenges.

```ts
import Kernel from '@onkernel/sdk';
const kernel = new Kernel();

// stealth + your own proxy: the solver stays loaded, your proxy replaces the ISP default
const a = await kernel.browsers.create({ stealth: true, proxy: { id: 'prx_123' } });
// stealth, no proxy (keeps the CAPTCHA solver): proxy.mode 'direct'
const b = await kernel.browsers.create({ stealth: true, proxy: { mode: 'direct' } });
// your proxy, no CAPTCHA solver: non-stealth browser with an explicit proxy
const c = await kernel.browsers.create({ proxy: { name: 'my-isp-proxy' } });
```

An explicit `proxy` changes only egress; it never turns stealth or the solver on or off. For a stable IP across sessions (logins), create an ISP proxy and select it. (Kernel's stealth docs still show `proxy_id`; it is `@deprecated` in the SDK, so use `proxy`.)

Solver behavior:
- Computer-use models stop at a CAPTCHA; prompt them: "If you see a CAPTCHA or similar test, just wait for it to get solved automatically by the browser."
- Cloudflare: once the "Ready" message appears, continue; do not click the Cloudflare checkbox (it can interfere with the solver).
- To hold an agent while a solve is outstanding, use `captcha_*` telemetry events (see [telemetry.md](telemetry.md)); a solver task `success` does not prove the challenge cleared.

Practices Kernel recommends:

| Area | Do |
|---|---|
| Viewport | Keep the default 1920x1080@25 (tuned to realistic device profiles) |
| Headless | Avoid it; some detectors notice it |
| Headers | Do not override user-agent or other headers |
| Execution | Prefer `playwright.execute` or `computer.*` over self-hosted Playwright/Puppeteer; computer controls open no CDP connection |
| Navigation | Start at the home page and click through rather than landing on a deep link or login page |
| Identity | Profiles keep cookies/storage; stable IP (ISP proxy) especially when logging in; browser pools reuse a consistent IP |
| Extensions | Each adds its own detectable fingerprint |
| Rate | Many sites throttle rapid or concurrent actions |

Proxy choice: ISP is the stealth default (static IP on a residential ASN, good for logins). Residential routes through consumer devices and exit IPs may change between connections; it offers richer geo-targeting (country, state, city, ZIP, ASN) and tends to suit fingerprint-heavy vendors, while some IP-reputation systems (e.g. reCAPTCHA) penalize rotating pools. GPU browsers render through real hardware, which matters on sites that cross-check canvas/WebGL output. See [proxies.md](proxies.md).

---

## 2. Config registry (`kernel.configRegistry`)

Give it a public URL; it returns browser and proxy settings that have worked for that site. Recommendations are advisory; Kernel creates no browser or proxy until you do. Available on the Hobbyist plan and up.

- `lookup({ url, allowed_proxy_countries? })` returns immediately from current knowledge (no site visit, no analysis, no data change). `recommendation: null` means no usable answer yet, not that the site is unreachable.
- `resolve({ url, intent?, allowed_proxy_countries? })` starts or joins a background analysis (usually several minutes); the first response usually has a null `recommendation` (the SDK types note current knowledge is preserved when it exists) and an `analysis.id`.
- `analyses.waitForResult(id, { maxWaitMs?, pollIntervalMs? })` polls every 5 s by default; exceeding `maxWaitMs` throws `APIConnectionTimeoutError` and does not cancel the analysis. Terminal statuses: `completed`, `failed`, `canceled`, `expired`. `analyses.retrieve(id)` returns what that run concluded (historical, stable); `analyses.list()`; `analyses.cancel(id)` is asynchronous (poll until `canceled`). `configRegistry.list({ search, sort_by, sort_order })` lists analyzed targets.
- `intent` (one or two sentences, https targets only) makes the analysis attempt your workflow after finding a configuration; `workload_outcome` is `completed | turn_limit | auth_required | payment_required | blocked | error`. Supplying `intent` narrows what can be recommended when a recommendation already exists.
- `allowed_proxy_countries` (ISO 3166 codes) restricts where the proxy may exit; the default starts with the United States.
- `recommendation` is `{ type: 'recommendation', browser, proxy, evidence, match_scope, matched_target }` or `{ type: 'no_recommendation', code: 'proxy_restricted' | 'target_not_evaluable' | 'no_working_configuration' | 'inconclusive', message }`. `working_configurations` lists equally strong options in preference order. Judge `evidence.success_rate`, `sample_size`, and `last_observed_at`. `guidance` (markdown) can be returned even with no working configuration; use it in your agent's instructions.
- Only submit public URLs you are authorized to test; no secrets, session tokens, signed links, private data, or URLs where a GET triggers an action.

```ts
const { recommendation } = await kernel.configRegistry.lookup({ url: 'https://www.kernel.sh/docs' });

if (recommendation?.type === 'recommendation') {
  // Create a managed proxy ONCE and reuse proxy.id; running this again creates another proxy.
  const proxy =
    recommendation.proxy.mode === 'managed'
      ? await kernel.proxies.create({ ...recommendation.proxy.create, name: 'config-registry-kernel-docs' })
      : null;

  const browser = await kernel.browsers.create({
    ...recommendation.browser,
    proxy: proxy ? { id: proxy.id } : { mode: 'direct' },
  });
  // ... drive it, then kernel.browsers.deleteByID(browser.session_id)
} else {
  const started = await kernel.configRegistry.resolve({
    url: 'https://www.kernel.sh/docs',
    intent: 'search the docs for proxies and open the first result',
    allowed_proxy_countries: ['US', 'GB'],
  });
  const result = await kernel.configRegistry.analyses.waitForResult(started.analysis!.id, { maxWaitMs: 10 * 60_000 });
  console.log(result.analysis?.status, result.recommendation, result.guidance);
}
```

---

## 3. Web Bot Auth (WBA)

WBA lets a browser agent sign requests (HTTP message signatures, RFC 9421) so participating sites can verify its identity and challenge it less. Each site still decides; WBA is not a login and guarantees no access.

- **Kernel's WBA token** is opt-in, on request, for Startup and Enterprise plans (contact support with your use case and target sites). It is not enabled by stealth mode or by plan alone.
- **Your own identity**: generate an Ed25519 JWK (`kty: OKP`, `crv: Ed25519`, `x`, `d`), host the public key in JWKS form at `https://yourdomain.com/.well-known/http-message-signatures-directory`, build and upload the signing extension, then load it into browsers:

```bash
kernel extensions build-web-bot-auth \
  --to ./web-bot-auth-ext \
  --key ./my-key.jwk \
  --signature-agent https://yourdomain.com \
  --upload my-web-bot-auth        # needs Node.js and npm; without --key it uses the public RFC 9421 test key
```

```ts
const browser = await kernel.browsers.create({ extensions: [{ name: 'my-web-bot-auth' }] }); // connect with browser.cdp_ws_url
```

The extension adds `Signature`, `Signature-Input`, and `Signature-Agent` headers. The test key does not enable Kernel's production identity; verify at https://http-message-signatures-example.research.cloudflare.com/. Extensions restart Chromium at create.

---

## 4. SSH into the browser VM

`kernel browsers ssh <session-id>` (CLI only; needs `websocat` installed locally). By default it creates an ephemeral ed25519 keypair removed when the session ends; `-i <key>` uses yours (the `.pub` file must sit beside it).

```bash
kernel browsers create --timeout 600                         # SSH is not browser activity; set a timeout or keep live view open
kernel browsers ssh <session-id> -R 3000:localhost:3000      # expose your local dev server at localhost:3000 inside the VM
kernel browsers ssh <session-id> -L 5432:localhost:5432      # reach a VM service locally
kernel browsers ssh <session-id> --setup-only                # install/configure SSH, print the manual connect command
```

Flags: `-i/--identity`, `-L/--local-forward localport:host:remoteport`, `-R/--remote-forward remoteport:host:localport`, `--setup-only`. For commands that do not need a shell, prefer `browsers.process.*` ([browser-control-surfaces.md](../patterns/browser-control-surfaces.md)).
