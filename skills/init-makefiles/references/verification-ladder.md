# Verification ladder — six rungs of "is it actually running?"

Verification has six rungs. Each higher rung is more independent — and harder to fake. The Makefile claims at most rung 5; rung 6 is a manual user step printed in the post-deploy banner. The ladder exists because "the deploy returned 200" is not proof of "the world can reach this app" — only an independent client can prove that, and the Makefile cannot be an independent client of itself.

## The six rungs

### Rung 1 — Local listening

The app is bound to a port and serving HTTP on this machine.

```bash
curl -sI http://127.0.0.1:$(PORT)
# Expect: HTTP/1.1 200 (or any 2xx/3xx — 301/302/304 are fine)
```

What it proves: the dev server / production app is running and accepting TCP connections on the expected port. Rules out crashes, port-binding failures, and silent-exit dev servers.

What it does NOT prove: that anything beyond this machine can reach the app. Localhost-only.

### Rung 2 — Process check

A process holds the port (or a process with the expected name exists).

```bash
# By port (preferred when known)
lsof -ti :$(PORT)
# Returns: a PID, or empty if nothing listens

# By name (preferred for native apps and macOS GUI apps)
pgrep -x "$(APP_NAME)"
# Returns: a PID, or empty if no process matches that exact name
```

What it proves: a process exists, with the expected identity. Rules out the case where rung 1 is succeeding because of a stale handler from a *different* process (Caddy, OrbStack, or a forgotten dev session squatting on the port).

`-x` (exact match) is critical for `pgrep`: without it, `pgrep "Mail"` matches `Mailmate`, `Mailbutler`, etc. The skill always uses `-x` for native macOS apps.

### Rung 3 — Public DNS resolves (Funnel only)

The public DNS for the Funnel hostname returns at least one A and at least one AAAA record from a public resolver.

```bash
dig @1.1.1.1 <node>.<tailnet>.ts.net A    +short
dig @1.1.1.1 <node>.<tailnet>.ts.net AAAA +short
# Expect: at least one IPv4 in the first call, at least one IPv6 in the second
```

What it proves: Tailscale's authoritative DNS for `ts.net` has published a record for this node — i.e., Funnel is enabled and the tailnet ACL permits it. Rules out the misconfiguration where `tailscale funnel` ran "successfully" but DNS hasn't propagated (or the node attribute hasn't been set).

`@1.1.1.1` (Cloudflare) is used as a "neutral" public resolver — bypassing the local resolver eliminates "the local cache is stale" as a confounder. **NOT** `@ns1.dnsimple.com` — the authoritative NS for `ts.net` is not directly verifiable as a hard-coded host (per `tailscale-funnel-rules.md`), and any public recursive resolver that honors the actual NS chain works fine.

This rung applies to **`make funnel` only**. `make tunnel` (Serve, tailnet-only) doesn't publish public DNS by design.

### Rung 4 — Tailnet-side curl

A node already on the tailnet can hit the FQDN over HTTPS.

```bash
# From a tailnet-joined Mac (or Linux, or anywhere with Tailscale up)
tailscale dns query <node>.<tailnet>.ts.net
# Expect: shows the tailscaled-resolved IP (100.x.y.z range)

curl -sI https://<node>.<tailnet>.ts.net
# Expect: HTTP/2 200 (or 30x)
```

What it proves: tailnet routing works end-to-end. The tailnet client resolves the MagicDNS name, routes to the node via the WireGuard mesh, the node's tailscaled terminates TLS, and the configured Serve/Funnel mapping forwards to the local app. This is the "internal Slack-link works" rung.

What it does NOT prove: that traffic from the public internet reaches the node — Funnel-only paths can fail at the Funnel relay even when tailnet routing is fine.

`tailscale dns query` is the **only** correct way to verify MagicDNS resolution on macOS — see the macOS DNS-quirks block below.

### Rung 5 — External-from-this-machine, no proxy

This machine reaches the public FQDN without going through the tailnet.

```bash
curl -4 -sI --noproxy '*' https://<node>.<tailnet>.ts.net
# Expect: HTTP/2 200 (or 30x)
```

What it proves: a request leaving this machine through the public internet (IPv4 only, no proxy, no tailnet) reaches the Funnel-served app. This is the strongest rung the Makefile can claim — the request is *originating* externally even though the machine is on the tailnet.

Why each flag:

- `-4` — force IPv4. Tailscale Funnel's AAAA is real but propagation lags AAAA records on some networks; without `-4`, clients without IPv6 transit get NXDOMAIN-on-AAAA failures even when IPv4 is fine. Documented failure mode in `github.com/tailscale/tailscale/issues/15404` and `#12473`.
- `--noproxy '*'` — bypass any HTTP_PROXY / HTTPS_PROXY env vars. Corporate networks often set these globally; the proxy could short-circuit the request through internal routing and falsely "succeed."
- `-s` — silent. We're parsing the headers, not the progress bar.
- `-I` — HEAD only. We don't need the body, just the status. Faster, smaller, no body-consumption side effects.

This rung is the highest the Makefile can self-claim. The machine is technically tailnet-joined, but the request is taking the public Funnel path. It's *almost* an independent client.

### Rung 6 — Independent client

A device the agent does not control reaches the FQDN over HTTPS.

```bash
# User runs this from a phone on cellular, OR from a non-tailnet Linux box, OR from any
# machine that is NOT signed into the same tailnet:
curl -sI https://<node>.<tailnet>.ts.net
```

What it proves: the world can reach this app. This is the only rung that *truly* proves "publicly accessible" — every prior rung can fail in subtle ways (proxy pinning to internal route, tailnet shadowing public DNS, ISP-level transparent proxy on the agent's network).

The Makefile cannot run this. The post-deploy banner (template below) prints the URL and instructs the user to do this themselves.

## Per-target rung table

Each generated target verifies up to a specific rung. The Makefile fails fast if a rung fails; the next rung is only attempted on success.

| Target | Rungs claimed by Makefile |
|---|---|
| `make local` | Rung 1 (curl localhost) + Rung 2 (process check) |
| `make local-lan` | Rung 1 + Rung 2 + LAN-IP enumeration printed (no rung claim — info only) |
| `make tunnel` (Serve) | Rung 1 + Rung 2 + Rung 4 (`tailscale dns query` + tailnet-side curl) |
| `make funnel` (PUBLIC, opt-in) | Rung 1 + Rung 2 + Rung 3 (public DNS) + Rung 4 (tailnet curl) + Rung 5 (external-no-proxy curl); banner instructs rung 6 |
| `make deploy-vercel` | `vercel inspect <url> --wait` (provider-native readiness) + `curl -sI <url>` post-Ready |
| `make deploy-railway` | `railway logs --build -s <svc>` clean + `curl -sI <public-domain>/health` |
| `make deploy-supabase`, `make supabase-migrate-apply` | `supabase db push --dry-run` (rung 1-equivalent: schema valid), then no-error `--linked` apply |
| `make ship` (Scenario G) | Rung 2 on remote (`pgrep -x "$(APP_NAME)"` after `sleep 2`); on failure, dump `log show --last 30s --predicate 'process == "..."'` |
| `make verify` | Re-checks the highest rung the deploy target claimed; HTTP-probes whatever URLs the recent `deploy*` produced |

The `make verify` target exists so the user can re-check the latest deploy state without re-deploying — useful after rotating DNS or fixing a healthcheck without changing code.

## macOS DNS quirks — use the right tool

On macOS, the standard Unix DNS tools **lie** about MagicDNS names. They bypass `mDNSResponder` (the system resolver) and query DNS directly, which means they don't see the per-domain resolver overrides Tailscale installs.

| Tool | Behavior on `<node>.<tailnet>.ts.net` |
|---|---|
| `host <fqdn>` | NXDOMAIN — bypasses system resolver, no public DNS for unfilled MagicDNS names |
| `nslookup <fqdn>` | NXDOMAIN — same problem |
| `dig <fqdn>` (no `@server`) | Uses `/etc/resolv.conf` if present; on macOS, that file is present but barely used. NXDOMAIN. |
| `dig @1.1.1.1 <fqdn>` | NXDOMAIN — public DNS doesn't have private MagicDNS names (only Funnel-published nodes) |
| `tailscale dns query <fqdn>` | **CORRECT** — queries via the tailscaled DNS proxy, which knows MagicDNS |
| `dscacheutil -q host -a name <fqdn>` | **CORRECT** — uses `mDNSResponder` (the actual macOS resolver), which honors `/etc/resolver/<tailnet>.ts.net` |
| `scutil --dns` | Diagnostic — shows the resolver chain. Useful for debugging "why doesn't the FQDN resolve" but doesn't itself do a lookup. |

The skill uses `tailscale dns query <fqdn>` (Tailscale CLI v1.76+) for tailnet/MagicDNS verification. Falls back to `dscacheutil -q host -a name <fqdn>` if the Tailscale version is older. **Never** `host` / `nslookup` / bare `dig`.

For the public-DNS rung 3 check (Funnel-published nodes only), `dig @1.1.1.1 <fqdn> A +short` *does* work — those records ARE in public DNS, published by Tailscale's authoritative nameservers for `ts.net`. That's the one place a public-resolver `dig` is correct.

Cross-reference: `tailscale-funnel-rules.md` covers the Funnel-side DNS topology in more detail.

## The post-deploy banner — rung 6 instructions for the user

When `make funnel` finishes (rungs 1-5 confirmed), the Makefile prints this banner. The agent never simulates rung 6 — it cannot be done from this machine.

```
Tunnel URL: https://<node>.<tailnet>.ts.net

✓ Verified rung 1-5 from this machine.
⚠ Verify rung 6 yourself: from a phone on cellular or any
  machine NOT signed into your tailnet, run:

      curl -sI https://<node>.<tailnet>.ts.net

  Expected: HTTP/2 200 (or 30x). If you get a connection error,
  Tailscale's edge can't reach this machine yet — wait ~10 minutes
  for DNS propagation, then retry.
```

The banner is intentionally short. The user is informed (a) what the Makefile checked, (b) what's left to check, (c) the exact command, (d) the most common failure mode (DNS propagation lag) and how to react.

For deploy targets (Vercel / Railway / Supabase), the equivalent rung-6 banner shows the deploy URL and the same `curl -sI` instruction. Cellular-from-a-phone is the gold standard because it's the network most likely to NOT have any path to the tailnet — IPv4-only carrier-grade NAT is closer to "the world" than corporate Wi-Fi which might pin a route through a VPN.

## When verification fails

The skill never silently swallows a failed rung. The recipe exits non-zero with a colored failure message, and includes the diagnostic command for the next debugging step.

| Rung | Failure diagnostic |
|---|---|
| 1 | `lsof -i :$(PORT)`; `ps aux \| grep -i <name>`; tail the dev-server log |
| 2 | `pgrep -fl <name>` (fuzzy match, see if a different name is running); `ps aux \| grep <name>` |
| 3 | `dig @8.8.8.8 <fqdn>` (try a different resolver); `tailscale funnel status` (is funnel actually on?); ACL configuration check |
| 4 | `tailscale status` (am I online?); `tailscale serve status` / `tailscale funnel status`; `curl -v` for the full handshake trace |
| 5 | `curl -4 -v --noproxy '*' https://<fqdn>`; check for IPv6-only AAAA records (`dig <fqdn> AAAA`); check upstream firewalls |
| 6 | (User-side) try a different network; check phone's cellular has IPv4 transit; wait 10 min for DNS propagation |

The skill prints the highest-rung failure diagnostic. If rung 4 fails, no rung-5 message appears — it never got there.

## DO-NOT list

- **DO NOT claim rung 6 from the Makefile.** Even with creative workarounds (curl through an external HTTP-curl proxy service, etc.), the request is still originating from infrastructure the agent is on. Rung 6 is by definition independent.
- **DO NOT use `host` / `nslookup` / bare `dig` for MagicDNS verification on macOS.** They bypass the system resolver and lie. Use `tailscale dns query <fqdn>` or `dscacheutil -q host -a name <fqdn>`.
- **DO NOT skip the `-4` flag on the rung-5 `curl`.** Tailscale Funnel publishes AAAA, and clients without IPv6 transit fail on AAAA-only fallback. `-4` forces IPv4 and dodges this real failure mode.
- **DO NOT swallow `--noproxy '*'`.** Corporate proxies pin internal routes; without bypass, rung 5 silently degrades to "the proxy reached it" instead of "the public internet reached it."
- **DO NOT print a fake "rung 6 verified" line.** The user must do rung 6, and the banner says so. Lying about it removes the user's only signal that the deploy needs an independent check.
- **DO NOT use `curl <url>` (no flags).** Always `-sI` — silent + headers-only. `curl <url>` dumps the body, which is noise for verification and may have HTML-escaped failure modes (200 page that says "service unavailable" in the body).
- **DO NOT verify against `localhost` for tunnel/Funnel rungs.** `localhost` and `127.0.0.1` skip the Funnel ingress entirely. Always use the FQDN for rungs 3+.
- **DO NOT treat 401/403 as a failure.** Auth-required endpoints return 401 cleanly; that's still proof of "ingress reaches the app." The rung-1 check expects ANY 2xx/3xx/4xx that isn't a connection failure or 5xx.

## What this file does NOT cover

| Topic | Reference |
|---|---|
| Tailscale Serve / Funnel command syntax, port restrictions, ACL rules | `tailscale-funnel-rules.md` |
| `_free-port-%` helper and port-collision diagnostics | `port-hygiene.md` |
| MacBook ship verification (rung 2 on remote via SSH) | `makefile-macbook.md` |
| Provider-native readiness signals (`vercel inspect --wait`, `railway logs --build`) | `makefile-frontend.md`, `makefile-backend.md` |
| The post-deploy banner formatting and ANSI palette | `makefile-base.md` |
