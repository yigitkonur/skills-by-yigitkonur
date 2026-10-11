# Kernel Proxies: Subsystem, Tiers, Routing & Verification

Kernel's proxy infrastructure routes browser egress for anti-bot evasion, localization, residential IP attribution, and corporate TLS inspection. Proxy selection is decoupled from stealth and session-creation flags.

---

## 1. Core Architecture & Invariants

Since `@onkernel/sdk@0.88.0` (released 2026-08-10) proxy configuration is a typed, nested object:

```ts
export interface BrowserProxyConfig {
  /** Proxy egress mode. Mutually exclusive with id and name. */
  mode?: 'direct' | 'default';
  /** Proxy ID in the same project. Mutually exclusive with mode and name. */
  id?: string;
  /** Proxy name matching exactly one active proxy in project. Mutually exclusive with mode and id. */
  name?: string;
}
```

### Key Semantics & Invariants
1. **Exactly one of `mode`, `id`, `name`.** An empty object or several properties (e.g. `{ id: '...', mode: 'direct' }`) is invalid. Names must match exactly one active proxy in the project; proxy names are not unique, so prefer `id`.
2. **Egress only.** A proxy changes where traffic exits. It never toggles stealth patches or the CAPTCHA solver: `stealth: true, proxy: { mode: 'direct' }` keeps the stealth fingerprint and CAPTCHA solver and egresses directly.
3. **Creation defaults:**
   - `stealth: true`, `proxy` omitted: Kernel's default stealth **ISP proxy**.
   - `stealth: false`, `proxy` omitted: direct egress.
   - `proxy: { id }` / `{ name }`: that proxy, regardless of stealth.
4. **Update semantics (`browsers.update`):**
   - `proxy` omitted: unchanged.
   - `proxy: { mode: 'default' }`: restore the browser default (stealth ISP proxy for stealth sessions, direct otherwise).
   - `proxy: { mode: 'direct' }`: drop proxy routing.
   - `proxy: { id }` / `{ name }`: hot-swap, synchronous, typically 2-3 seconds. The browser network is momentarily disconnected, so in-flight requests can fail. If you swap the proxy on a browser acquired from a pool, release is delayed by the swap duration while the pool default proxy is restored.
5. **Deprecations:**
   - `proxy_id` is `@deprecated` on `BrowserCreateParams`, `BrowserUpdateParams`, every browser response shape, and on the top-level `proxy` / `proxy_id` of Managed Auth connections (use `browser.proxy`). It cannot be combined with `proxy`.
   - `proxy_id?: string` stays **active** on `BrowserPoolCreateParams` / `BrowserPoolUpdateParams` (pools take no nested `proxy`; send `proxy_id: ''` on update to clear it).
   - `disable_default_proxy` (update only) is `@deprecated`; use `proxy: { mode: 'direct' }`.
   - The `datacenter` proxy type is gone from `@onkernel/sdk@0.123.0`: `ProxyCreateParams.type` is `'isp' | 'residential' | 'mobile' | 'custom'` (changelog 0.121.0 "Deprecate datacenter proxies in the API"). Use `isp`.

---

## 2. Per-Host Proxy Routing (`network.proxy_routes`)

One browser or pool can send different destination hosts through different proxies. Setting routes requires proxy v3.

```ts
import Kernel from '@onkernel/sdk';

const kernel = new Kernel();

const browser = await kernel.browsers.create({
  stealth: true,
  // Top-level proxy handles all non-matching traffic
  proxy: { name: 'us-residential-default' },
  network: {
    proxy_routes: [
      {
        // The apex and the wildcard must both be listed
        hosts: ['target-auth.com', '*.target-auth.com'],
        proxy: { name: 'static-isp-dedicated' },
      },
      {
        hosts: ['*.internal-corp.net'],
        proxy: { id: 'prx_custom_corp_gw' },
      },
    ],
  },
});
```

### Routing Rules & Semantics
- **Precedence:** exact hostname beats wildcard; a longer wildcard suffix beats a shorter one (`a.b.example.com`: `a.b.example.com` > `*.b.example.com` > `*.example.com`). Array order does not matter. A host pattern may appear in only one route. Patterns cannot include ports; matching ignores the destination port.
- **Wildcards:** a leading `*.` matches subdomains at any depth, never the apex. Supply `['example.com', '*.example.com']` for both.
- **Route proxy:** `proxy` is `{ id }` or `{ name }` of an active, non-direct proxy (there is no `mode` on a route). The route proxy's own `bypass_hosts` still apply.
- **Fail closed:** if a route's proxy is unavailable or deleted, matched requests fail with 502 and `X-Kernel-Proxy-Error: destination_route_unavailable`. No fallback to the top-level proxy or direct egress.
- **Timing:** routes apply from the start of the session, including `start_url` and setup traffic.
- **Limits (CLI):** at most 10 routes and 50 hosts per route.
- **Single sessions:** `proxy_routes` is create-time only (the live-update type `BrowserNetworkUpdate` only carries `allowed_hosts`).

### Pools
`BrowserPoolCreateParams.network` / `BrowserPoolUpdateParams.network` take the same `BrowserNetworkConfig` (routes, `private_hosts`, `allowed_hosts`).

```ts
await kernel.browserPools.create({
  name: 'routed-pool',
  size: 5,
  stealth: true,
  proxy_id: 'prx_default',                // pools take proxy_id, not proxy
  network: {
    allowed_hosts: ['example.com', '*.example.com'],
    proxy_routes: [{ hosts: ['example.com', '*.example.com'], proxy: { name: 'static-isp-dedicated' } }],
  },
});
```

- `browserPools.update` with `network`: omitted = unchanged; `{}` removes the whole network config; the supplied object replaces the pool's network config (CLI: "Network flags replace the pool's whole network configuration", so resend `private_hosts` to keep it).
- Routes and other network fields apply only to browsers created after the update; pass `discard_all_idle: true` to rebuild idle ones. Changing `allowed_hosts` replaces idle browsers automatically.
- Leased browsers keep their allowlist until release; on release it is reset to the pool baseline (or the browser is replaced).
- `allowed_hosts` must be non-empty when supplied. Egress allowlists and routes require proxy v3.
- CLI 0.47.0: `kernel browser-pools create|update --proxy-route HOST[,HOST...]=PROXY` exists; there is no pool `--allowed-host` flag (SDK only).

---

## 3. Proxy Tiers Taxonomy

| Tier | Infrastructure | IP Persistence | Targeting Options | .gov | Best Used For |
|---|---|---|---|---|---|
| **ISP** | Datacenter hosts with residential ISP ASNs | **Static IP** across sessions (`ip_address` on the proxy) | `country`: `US` (default), `SG`, `GB`, `FR`, `DE`; `KR` is feature-gated (changelog 0.122.0 "feature-gated Korean ISP proxies"; SDK/CLI list it, docs list five countries) | Not auto-routed | Default stealth egress; IP allowlists; managed-auth health checks |
| **Residential** | Consumer residential devices, several upstream providers | IP can change per connection | `country`, `state` (US), `city` (lowercase, no spaces; requires `country`), `zip` (US only; not with city/state), `asn` (not with city/state); `os` is `@deprecated` | Routed automatically with no targeting, country-only, or US-state targeting; ZIP, ASN and non-US state may return `restricted_route_unavailable` | Hardened anti-bot sites; localized scraping |
| **Mobile** | Cellular carrier networks | Dynamic carrier IP | `country`, `state` (US only), `city` (provider alias); state/city are best-effort | Not documented | Advanced stealth cases |
| **Custom** | Your HTTP/HTTPS proxy | Yours | `host`, `port` (1-65535), `username`, `password` (min 5 chars), `protocol`, `ca_bundle` | Network dependent | Corporate egress; BYO provider |

Prefer the least-specific targeting that works: narrower targeting means fewer IPs and more `no_peer` failures. ISP proxies may use a backup endpoint from a different provider during a primary outage, so an allowlisted IP can briefly change.

### Options available on every type
- `bypass_hosts`: hostnames that skip the proxy (max 100 entries, 253 chars each, exact or `*.` wildcard, no IPs/ports/schemes). Start-Up and Enterprise plans.
- `protocol`: `'http' | 'https'` (default `https`).
- `kernel.proxies.update(id, { name })` renames only; recreate to change settings.

```ts
const proxy = await kernel.proxies.create({
  type: 'isp',
  name: 'us-isp',
  config: { country: 'US' },
  bypass_hosts: ['localhost', '*.amazonaws.com'],
});
console.log(proxy.ip_address);
```

Plan gating (pricing page): configurable proxies Hobbyist and up; BYO (custom) proxies Start-Up and up. Kernel-provided proxies are not billed per GB, subject to fair use (traffic must come from your Kernel sessions; no reselling or tunneling). Upstream providers block some categories (government, banking, payment processors); those fail at the proxy layer, not as a Kernel outage. Try `proxy: { mode: 'direct' }` or a custom proxy for those.

### Custom MITM Proxies & CA Bundles
- `config.ca_bundle`: PEM CA certificate(s), up to 64 KiB, trusted by Chromium inside the VM.
- Write-only; responses return `has_ca_bundle: true`.
- A proxy with a `ca_bundle` must be bound at browser creation; it cannot be hot-swapped onto a running browser.

### Lifecycle Policies
- Kernel deletes proxy configs unused for 14 days when the org has more than 100 active configs. Configs attached to sessions, pools, instances or managed auth connections are kept.
- `DELETE /proxies/{id}` returns `400 resource_in_use` while a live managed auth connection references the proxy; repoint or delete those connections first.

---

## 4. Reachability & Health Check (`proxies.check`)

```ts
// General provider health check (updates the stored status)
const generalHealth = await kernel.proxies.check('prx_123');
console.log(generalHealth.status); // 'available' | 'unavailable'

// Target URL reachability (public http/https URL; does NOT update the stored status)
const targetCheck = await kernel.proxies.check('prx_123', { url: 'https://www.target-domain.com' });
if (targetCheck.status !== 'available') {
  console.warn(`Target unreachable via proxy: ${targetCheck.status}`);
}
```

- ISP exit IPs are static, so a URL check reliably predicts later sessions. Residential and mobile exits change between requests, so the check validates credentials and connectivity only.

---

## 5. Proxy Errors & Telemetry

Every branded proxy-layer error is HTTP **502** with `X-Kernel-Proxy-Error` (the status is always 502, including timeouts; branch on the header):

```http
HTTP/1.1 502 Bad Gateway
X-Kernel-Proxy-Error: upstream_timeout
```

| Code | Meaning | Retry |
|---|---|---|
| `upstream_timeout` | Connection to the upstream proxy provider did not complete in time | Yes |
| `provider_unreachable` | The upstream provider could not reach the destination | Yes |
| `upstream_connect_failed` | The connection to the destination failed | Yes |
| `upstream_dns_failure` | The upstream proxy host could not be resolved | Yes |
| `origin_tls_timeout` | Destination did not finish its TLS handshake in time | Yes |
| `restricted_route_unavailable` | Destination needs a specialized egress route Kernel could not build | Yes, except `.gov`: create a residential proxy with no targeting, country-only, or US-state targeting, confirm with `proxies.check`, use it |
| `destination_route_unavailable` | Destination matches a per-host route whose proxy is deleted/unavailable | No: fix or remove the route |
| `proxy_unavailable` | Failure inside Kernel's own proxy layer | Yes |
| `origin_response_incomplete` | Destination closed the connection before a complete response | Only if repeating cannot duplicate side effects |
| `provider_rejected` | Provider rejected the request before connecting (check custom-proxy credentials) | No: change proxy or type |
| `provider_blacklisted` | Provider blocks this destination | No: change proxy/type or go direct |
| `destination_blocked` | Kernel policy blocks internal and private addresses | No: use a public address |

Egress-allowlist denial is the exception to the 502 rule: a destination that misses `network.allowed_hosts` is refused with a 403 and `X-Kernel-Proxy-Error: network_policy_denied` (SDK `BrowserNetworkConfig.allowed_hosts` docs).

```ts
const RETRYABLE = new Set([
  'upstream_timeout', 'provider_unreachable', 'upstream_connect_failed', 'upstream_dns_failure',
  'origin_tls_timeout', 'restricted_route_unavailable', 'proxy_unavailable',
]);
// after page.goto(url): response?.headers()['x-kernel-proxy-error'] -> retry only if in RETRYABLE
```

Proxy failures also appear as `proxy_error` events in the `network` telemetry category. `origin_response_incomplete` is not reported as an event, and a header value the browser image does not recognize is reported as `unknown` with the original in `raw_code`.

### Egress allowlist (`network.allowed_hosts`)
Rules for the field shown in [browsers-lifecycle.md](browsers-lifecycle.md): needs proxy v3 and may be gated by an org flag (changelog 0.120.0); max 100 entries (CLI `--allowed-host` limit); entries are exact hostnames, one leading `*.` wildcard (subdomains only, not the apex), public IPv4/IPv6 addresses, or public CIDRs; no ports, paths or schemes; wildcards over a public suffix and entries overlapping `private_hosts` are rejected; `start_url` must be allowed; enforced only at Kernel's egress proxy (`private_hosts` and VM processes that bypass the browser proxy are not filtered).

---

## 6. CLI Reference (`@onkernel/cli@0.47.0`)

```bash
kernel proxies list
kernel proxies get prx_isp_01

# ISP proxy (US, SG, GB, FR, DE; KR is gated)
kernel proxies create --type isp --name gb-isp --country GB

# Residential with location targeting
kernel proxies create --type residential --name ny-res --country US --state NY --city newyork

# Custom proxy with CA bundle and bypass hosts
kernel proxies create --type custom --name corp-mitm \
  --host proxy.corp.internal --port 8080 \
  --username admin --password secret \
  --ca-bundle /path/to/corporate-root-ca.pem \
  --bypass-host localhost --bypass-host '*.amazonaws.com'

kernel proxies update prx_isp_01 --name us-checkout-proxy
kernel proxies check prx_isp_01 [--url https://www.example.com]
kernel proxies delete prx_isp_01 --yes

# Browsers: proxy by ID or name, direct egress, per-host routes
kernel browsers create --proxy-id prx_isp_01 --stealth
kernel browsers create --proxy-name us-east-isp --stealth
kernel browsers create --proxy-mode direct --stealth
# PROXY in --proxy-route is an ID by default; use id:ID or name:NAME explicitly
kernel browsers create \
  --proxy-route "api.example.com,*.api.example.com=prx_isp_01" \
  --proxy-route "*.corp.internal=name:corp-mitm" \
  --stealth
```
