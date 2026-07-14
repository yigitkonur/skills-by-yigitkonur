# architecture — the four-piece model

The single most common cause of "Tailscale Funnel doesn't work and I don't know why" is treating the system as one component when it's four. Each can be in a different state. Each fails for different reasons. The CLI shows you only one of the four.

## The four components

```
┌─────────────────────────┐
│ 1. The local app        │  listens on 127.0.0.1:<port>
│    (your dev server)    │
└────────────┬────────────┘
             │ HTTP over loopback
             ▼
┌─────────────────────────┐
│ 2. tailscaled (daemon)  │  manages Funnel mappings via `tailscale funnel` CLI
│    on this machine      │  device-side state — set by you, on this Mac
└────────────┬────────────┘
             │ control plane
             ▼
┌─────────────────────────┐
│ 3. Tailscale            │  owns the ACL: is your node allowed to expose Funnel?
│    coordination server  │  decides whether to publish public DNS records
│    (hosted by Tailscale)│  tailnet-side state — set by tailnet admin in console
└────────────┬────────────┘
             │ DNS publish
             ▼
┌─────────────────────────┐
│ 4. Public DNS           │  A + AAAA records for <node>.<tailnet>.ts.net
│    (Tailscale ingress)  │  routes external traffic to 208.111.34.11 / 208.111.35.209
└─────────────────────────┘
```

Each layer has its own state, its own verification command, and its own way to fail. The CLI (`tailscale funnel up`) talks only to layer 2. It cannot detect that layer 3 hasn't authorized your node, because layer 3 doesn't tell layer 2 — it just silently refuses to publish DNS.

## Layered verification map

| Layer | What it does | Verification command | Failure mode |
|---|---|---|---|
| 1. Local app | Accepts HTTP on `127.0.0.1:<port>` | `curl -sI http://127.0.0.1:<port>/` | App not running / wrong port / bound to wrong interface |
| 2. Daemon | Forwards `<funnel-port>` → loopback | `tailscale funnel status` | No mapping, or mapping points at wrong loopback port |
| 3. ACL gate | Authorizes the node to expose Funnel | `dig @ns1.dnsimple.com <fqdn> A +short` | Empty answer = `funnel` nodeAttr not granted, or HTTPS Certs not enabled |
| 4. Public DNS / cert | Routes external traffic, terminates TLS | `curl --resolve <fqdn>:<port>:208.111.34.11 https://<fqdn>:<port>/` | DNS still propagating (≤60s after gate opens), or cert still issuing |

When you see a confusing state — "the CLI says Funnel is on but the URL doesn't work" — walk down this map. The layer where verification stops working is the layer with the actual problem.

## Why this matters for browser-automation agents

This skill is most often triggered because a browser-automation tool (agent-browser, Playwright in microVM, AgentCore cloud browser, Vercel Sandbox) can't reach `127.0.0.1`. Some of these tools also block private IP ranges as an SSRF defense.

The reason Funnel works for this case is layer 4: the URL is a real public hostname with a real cert, and the IP it resolves to is a public Tailscale ingress (`208.111.34.11` / `208.111.35.209`), not a private range. Tools that block private IPs accept public ones.

The reason loopback fails is that the sandboxed Chrome runs in its own network namespace — its `127.0.0.1` is the *container's* loopback, not the host's. There is no shortcut here; the public URL is the path.

The reason LAN IPs fail (`192.168.x.x`, `100.x.x.x`) is that browser-automation tools commonly enforce an SSRF allowlist. agent-browser specifically rejects with "restricted target; contact support team." That's a feature — it stops a runaway agent from probing the internal network.

So when you're standing up Funnel for a browser agent, layer 4 is the layer that matters. Funnel exists to give layer 4 a working address.

## Common cross-layer failures

**"`tailscale funnel up` succeeded but the URL is NXDOMAIN."**
Layer 2 succeeded; layer 3 hasn't authorized. The ACL gate is the part with no device-side error. Verify with `dig @ns1.dnsimple.com <fqdn> A +short`.

**"`dig @ns1.dnsimple.com` returns records but `curl <fqdn>` says 'Could not resolve.'"**
Layer 3 and 4 are fine; the macOS resolver chain on this Mac isn't routing `*.ts.net` queries to Tailscale's daemon. See `macos-dns-fixup.md`.

**"Public URL returns 200 from cellular phone, fails from this Mac."**
Same as above — phone uses public DNS, your Mac has a broken local resolver chain. Same fix.

**"Public URL returns 502."**
Layer 1 isn't running, or layer 2 is forwarding to the wrong loopback port. Confirm with `lsof -nP -iTCP:<port> -sTCP:LISTEN` and `tailscale funnel status`.

**"Public URL returns 403, body says 'Forbidden.'"**
Layers 1–4 all succeed; the app at layer 1 is rejecting the request because of a Host-header allowlist mismatch. See `backend-host-validation.md`.

## How long does each layer take to "settle"?

| Action | Layer | Time to take effect |
|---|---|---|
| Start the local app | 1 | seconds |
| `tailscale funnel --bg --https=<port>` | 2 | immediate (device-side) |
| Grant `funnel` nodeAttr in admin console | 3 | ~30–60 seconds (DNS publishes to most resolvers) |
| Cloudflare `1.1.1.1` cache to clear | 3 → 4 | up to 5 minutes (negative TTL) |
| First-time Let's Encrypt cert issuance | 4 | usually <60 seconds, sometimes longer |

When the user says "it doesn't work yet" within 60 seconds of opening the ACL gate, ask them to wait. Cloudflare DNS is the slowest resolver to clear a stale NXDOMAIN. Probe from Google `8.8.8.8`, Quad9 `9.9.9.9`, and OpenDNS in parallel — if 3 out of 4 work, it's stale Cloudflare cache, not a real failure.
