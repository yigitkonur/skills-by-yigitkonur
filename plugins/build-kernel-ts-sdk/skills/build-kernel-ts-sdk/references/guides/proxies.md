# Kernel Proxies: Subsystem, Tiers, Routing & Verification

Kernel's proxy infrastructure provides an enterprise-grade egress subsystem designed for anti-bot evasion, localization, residential IP attribution, and corporate TLS inspection. The proxy subsystem is fully decoupled from anti-detection stealth and session creation flags.

---

## 1. Core Architecture & Invariants

Historically, Kernel accepted flat parameters (`proxy_id: string`, `disable_default_proxy: boolean`). As of `@onkernel/sdk@0.88.0` (August 10/14, 2026), proxy configuration is strictly modeled as a typed, nested object:

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
1. **Strict Mutual Exclusivity**: You must provide **exactly one** of `mode`, `id`, or `name`. Providing an empty object (`{}`) or multiple properties (e.g. `{ id: '...', mode: 'direct' }`) throws HTTP 400 Bad Request.
2. **Decoupled Egress & Stealth**: Setting a proxy modifies **only where outbound traffic exits**. It never toggles stealth patches or the automated CAPTCHA solver. A session configured with `stealth: true, proxy: { mode: 'direct' }` retains stealth browser fingerprinting and the CAPTCHA solver while egressing directly via Kernel's microVM network.
3. **Session Creation Defaults**:
   - `stealth: true` with proxy omitted → Automatically uses Kernel's default stealth **ISP proxy**.
   - `stealth: false` with proxy omitted → Routes directly to the internet (`mode: 'direct'`).
   - `proxy: { id }` or `proxy: { name }` → Uses the specified proxy regardless of whether stealth is true or false.
4. **Session Update Semantics (`browsers.update`)**:
   - Proxy omitted → Existing session proxy remains unchanged.
   - `proxy: { mode: 'default' }` → Restores the browser default (stealth ISP proxy for stealth sessions, direct for non-stealth).
   - `proxy: { mode: 'direct' }` → Drops proxy routing and exits directly to the internet.
   - `proxy: { id }` or `proxy: { name }` → Hot-swaps egress to the new proxy synchronously within 2–3 seconds.
5. **Deprecations & Active Exceptions**:
   - `proxy_id` was deprecated in `@onkernel/sdk@0.88.0` (August 10/14, 2026) across single-session APIs (`BrowserCreateParams`, `BrowserUpdateParams`) and `ManagedAuthConnection`.
   - `proxy_id?: string` remains **active** on `BrowserPoolCreateParams` and `BrowserPoolUpdateParams` (browser pool definitions do not accept a nested `proxy` object).
   - `disable_default_proxy` is `@deprecated` in favor of `proxy: { mode: 'direct' }`.
   - Datacenter (`datacenter`) proxy tier is `@deprecated` in favor of `isp`.

---

## 2. Per-Host Proxy Routing (`network.proxy_routes`)

Per-host proxy routing enables a single browser session or browser pool to route traffic across multiple upstream proxies based on destination hostnames.

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
        // Explicit apex domain and wildcard subdomain must both be declared
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
- **Evaluation Order**: Exact hostnames take highest precedence (`auth.site.com` beats `*.site.com`). Longer wildcard suffixes take precedence over shorter wildcard suffixes (`*.auth.site.com` beats `*.site.com`). Array ordering does not matter.
- **Wildcard Boundaries**: Leading `*.` wildcards match **subdomains only at any depth**, but **never match the apex domain**. `*.example.com` matches `sub.example.com` and `a.b.example.com`, but does NOT match `example.com`. To match both, supply `['example.com', '*.example.com']`.
- **Fail-Closed Semantics**: If a route proxy fails or is deleted, requests to matching hosts **fail closed** with HTTP 502 and header `X-Kernel-Proxy-Error: destination_route_unavailable`. Kernel deliberately does NOT fall back to top-level proxy or direct egress, preventing sensitive IP leaks.
- **Lifecycle Scope**: In single browser sessions, `proxy_routes` is **create-time only**; it cannot be modified on running sessions. In browser pools, `proxy_routes` can be updated across the pool (`kernel.browserPools.update`).

---

## 3. Proxy Tiers Taxonomy

Kernel supports four primary proxy tiers:

| Tier | Infrastructure | IP Persistence | Anti-Bot Strength | Targeting Options | .gov Support | Best Used For |
|---|---|---|---|---|---|---|
| **ISP** | Datacenter hosts with residential ISP ASNs | **Static IP** across sessions | Good | Country (`US`, `SG`, `GB`, `FR`, `DE`, `KR`) | ❌ No auto-routing | Default stealth mode; IP allowlists; high throughput |
| **Residential** | Consumer residential devices | **Rotating IP** per connection | Very High | `country`, `state` (US), `city` (lowercase no spaces), `zip` (US), `asn` (note: `os` is deprecated; `zip` is US-only and conflicts with city/state; `asn` conflicts with city/state; `city` requires `country`) | ✅ Yes (no targeting or state) | Hardened anti-bot sites; localized scraping; CAPTCHA evasion |
| **Mobile** | Cellular 4G/5G carrier networks | **Dynamic carrier IP** | Maximum | `country`, `state` (US only), `city` | ❌ Restricted | Mobile-specific web targets; highest-friction fraud walls |
| **Custom** | Customer HTTP/HTTPS proxy server | Managed by customer | Customer IP dependent | Custom `host`, `port`, `username`, `password`, `ca_bundle` | Network dependent | Corporate egress; internal compliance proxies; BYO Bright Data / Oxylabs |

*(Note: Legacy `datacenter` tier is deprecated in favor of `isp`.)*

### Custom MITM Proxies & CA Bundles
For custom proxies requiring TLS interception/decryption:
- Upload PEM-encoded root certificates up to 64 KiB via `config.ca_bundle`.
- Injected directly into Chromium's root trust store inside the microVM.
- `ca_bundle` contents are write-only; API responses return `has_ca_bundle: true`.
- **Creation-Only Invariant**: Custom proxies with `ca_bundle` must be assigned at session creation; Chromium cannot reload root certificates dynamically without restarting.

### Lifecycle Policies & Referential Protection
- **Automatic Cleanup**: Kernel automatically deletes proxy configurations unused for 14 days in organizations with >100 active configurations. Configurations attached to active sessions, pools, or managed auth connections are preserved.
- **Referential Deletion Protection**: `DELETE /proxies/{id}` returns HTTP 400 `resource_in_use` if the proxy is referenced by an active managed auth connection. Remove or repoint those connections before deleting.

---

## 4. Reachability & Health Check Engine (`proxy.check`)

Validate proxy health and target site reachability before provisioning browser sessions:

```ts
// 1. General provider health check (updates stored proxy status)
const generalHealth = await kernel.proxies.check('prx_123');
console.log(`Stored status: ${generalHealth.status}`); // 'available' | 'unavailable'

// 2. Target URL reachability test (does NOT mutate stored proxy status)
const targetCheck = await kernel.proxies.check('prx_123', {
  url: 'https://www.target-domain.com',
});
if (targetCheck.status !== 'available') {
  console.warn(`Target unreachable via proxy: ${targetCheck.status}`);
}
```

- **Static vs Rotating Semantics**: For ISP proxies, exit IPs are static, so checking against a URL reliably validates that subsequent sessions will reach the target from that IP. For Residential and Mobile proxies, exit IPs rotate across requests.

---

## 5. Proxy Errors & Telemetry Integration

When proxy egress fails, Kernel returns HTTP 502 (or 403 for policy denial) with an authoritative header:

```http
HTTP/1.1 502 Bad Gateway
X-Kernel-Proxy-Error: upstream_timeout
```

### Official 12-Code `X-Kernel-Proxy-Error` Taxonomy (HTTP 502)
- `upstream_timeout`: Upstream provider connection timed out (retryable).
- `provider_unreachable`: Gateway host or port unreachable (retryable).
- `upstream_connect_failed`: TCP connection to upstream proxy failed (retryable).
- `upstream_dns_failure`: DNS resolution of upstream proxy host failed.
- `origin_tls_timeout`: TLS handshake with origin server timed out.
- `restricted_route_unavailable`: Restricted destination route could not be established.
- `destination_route_unavailable`: Target matched a route whose proxy is deleted or broken (non-retryable; fail-closed).
- `proxy_unavailable`: Upstream proxy temporarily unavailable.
- `origin_response_incomplete`: Origin server closed response stream prematurely.
- `provider_rejected`: Upstream proxy provider rejected the connection.
- `provider_blacklisted`: Destination host blocked by upstream proxy provider.
- `destination_blocked`: Destination host blocked by proxy network filter.

### Egress Policy Denial (HTTP 403)
- `network_policy_denied`: Request rejected by security or egress policy (e.g. `network.allowed_hosts` destination mismatch).

In Browser Telemetry, proxy errors emit under the `network` category as `proxy_error` events.

---

## 6. CLI Reference (`@onkernel/cli@0.47.0`)

```bash
# List proxies
kernel proxies list

# Inspect proxy details
kernel proxies get prx_isp_01

# Create an ISP proxy (supports US, SG, GB, FR, DE, KR)
kernel proxies create --type isp --name kr-isp --country KR

# Create a Residential proxy with location targeting
kernel proxies create --type residential --name ny-res --country US --state NY --city newyork

# Create a Custom proxy with CA certificate bundle
kernel proxies create --type custom --name corp-mitm \
  --host proxy.corp.internal --port 8080 \
  --username admin --password secret \
  --ca-bundle /path/to/corporate-root-ca.pem

# Run reachability checks
kernel proxies check prx_isp_01
kernel proxies check prx_isp_01 --url https://www.example.com

# Launch browser with explicit proxy by ID or name
kernel browsers create --proxy-id prx_isp_01 --stealth
kernel browsers create --proxy-name us-east-isp --stealth

# Launch browser with per-host routing (repeatable flag; name: prefix required for proxy names)
kernel browsers create \
  --proxy-route "api.example.com,*.api.example.com=prx_isp_01" \
  --proxy-route "*.corp.internal=name:corp-mitm" \
  --stealth

# Launch browser with direct internet egress
kernel browsers create --proxy-mode direct --stealth
```
