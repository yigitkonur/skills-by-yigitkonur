# Tailscale Serve and Funnel rules

Canonical rule book for the `make tunnel`, `make tunnel-stop`, and `make funnel` targets. Serve and Funnel are different things — Serve is tailnet-only, Funnel is public via Tailscale's edge ingress. The Makefile generates targets for both, but Funnel is opt-in only and gated behind `PUBLIC_FUNNEL=1`. Every fact in this file was verified against the live Tailscale docs on **2026-05-08**.

## Serve vs Funnel

| Property | Serve | Funnel |
|---|---|---|
| Reach | Tailnet only (signed-in devices) | Public internet |
| Ingress | Direct WireGuard from peer | Tailscale edge ingress relays to your node |
| Cert | Real Let's Encrypt | Real Let's Encrypt |
| ACL gate | Standard tailnet ACL | Extra `nodeAttrs` `funnel` attribute required |
| Allowed ports | Any (`--http=<n>`, `--https=<n>`, etc.) | **Only 443, 8443, 10000** |
| `--bg` persistence | Survives reboot, `tailscale down/up` | Same |

Sources (verified 2026-05-08):
- `https://tailscale.com/kb/1312/serve` — Serve overview, command surface, `--bg` semantics, `reset` is destructive
- `https://tailscale.com/kb/1223/funnel` — Funnel overview, port restrictions, ACL gate
- `https://tailscale.com/kb/1464/funnel-vs-sharing` — When to use each
- `https://tailscale.com/blog/reintroducing-serve-funnel` — 1.52 redesign rationale

## Command surface (verified 2026-05-08)

```text
tailscale serve  [flags] <target>     # tailnet-only
tailscale funnel [flags] <target>     # public via edge ingress

flags:
  --bg                    persist across reboot AND `tailscale down/up`
  --http=<port>           publish via HTTP on <port> (defaults: 80)
  --https=<port>          publish via HTTPS on <port> (default: 443)
  --tcp=<port>            publish raw TCP on <port>
  --tls-terminated-tcp=<port>   TLS-terminate at tailscaled, hand off TCP to backend
  --set-path=<path>       mount the target on a sub-path

status:
  tailscale serve  status [--json]    # list active Serve mappings on this node
  tailscale funnel status [--json]    # list active Funnel mappings on this node

destructive:
  tailscale serve  reset              # WIPES ALL Serve  mappings on this node
  tailscale funnel reset              # WIPES ALL Funnel mappings on this node
```

Without `--bg` the mapping disappears with the terminal session (or whenever the foreground command exits). The Makefile always uses `--bg` for `tunnel`/`funnel` so the mapping survives a Ctrl-C in the dev process.

`reset` is destructive — it wipes **all** Serve or Funnel mappings on this node, including any from other projects. The Makefile NEVER runs `reset`. Targeted disable for a single port: `tailscale serve --https=443 <port> off` or `tailscale funnel <port> off`.

## `make tunnel` — Serve, tailnet-only (default)

```makefile
.PHONY: tunnel
tunnel: _free-port-$(TUNNEL_PORT) _ts-preflight _ts-clear-our-port _ts-bind-serve _print-banner-tunnel
	@PORT=$(TUNNEL_PORT) HOSTNAME=127.0.0.1 $(DEV_CMD) -- --port $(TUNNEL_PORT) --hostname 127.0.0.1

_ts-preflight:
	@command -v tailscale >/dev/null 2>&1 || { \
	  printf "$(R)tailscale CLI not found$(Z)  $(D)brew install --cask tailscale$(Z)\n"; exit 1; }
	@tailscale status >/dev/null 2>&1 || { \
	  printf "$(R)Tailscale not signed in$(Z)  $(D)open menu-bar → log in$(Z)\n"; exit 1; }
	@printf "$(D)→ current state (read-only):$(Z)\n"
	@tailscale serve status 2>/dev/null || true
	@tailscale funnel status 2>/dev/null || true

_ts-clear-our-port:
	@tailscale serve --https=443 $(TUNNEL_PORT) off 2>/dev/null || true
	@tailscale serve --http=80   $(TUNNEL_PORT) off 2>/dev/null || true
	@tailscale funnel            $(TUNNEL_PORT) off 2>/dev/null || true

_ts-bind-serve:
	@if [ "$(TUNNEL_TLS)" = "1" ]; then \
	  tailscale serve --bg --https=443 $(TUNNEL_PORT) >/dev/null; \
	else \
	  tailscale serve --bg --http=80   $(TUNNEL_PORT) >/dev/null; \
	fi

_print-banner-tunnel:
	@scheme=$$( [ "$(TUNNEL_TLS)" = "1" ] && echo https || echo http ); \
	  node=$$(tailscale status --json 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['Self']['DNSName'].rstrip('.'))" 2>/dev/null); \
	  short=$${node%%.*}; \
	  printf "\n$(B)$(G)$(PROJECT_NAME) dev$(Z)  $(D)Tailscale Serve · tailnet only$(Z)\n"; \
	  printf "  $(C)→$(Z) $(B)$$scheme://$$node$(Z)\n"; \
	  printf "  $(C)→$(Z) $$scheme://$$short  $(D)(short MagicDNS)$(Z)\n"; \
	  printf "  $(C)→$(Z) http://localhost:$(TUNNEL_PORT)\n"; \
	  printf "  $(D)stop:  make tunnel-stop      Funnel is OFF      try TUNNEL_TLS=1 for HTTPS$(Z)\n\n"
```

Why each step:
- `_free-port-$(TUNNEL_PORT)` reclaims the port if held by a stale dev process; refuses if held by anything else. See `port-hygiene.md`.
- `_ts-preflight` confirms the CLI is installed and the daemon is signed in. **Reads** current Serve/Funnel state — does not mutate. The user sees what's mapped right now before the recipe touches anything.
- `_ts-clear-our-port` disables only the project's port. NEVER `reset`. Three `off` calls (https=443, http=80, funnel) cover both modes and both schemes; the absent ones are no-ops.
- `_ts-bind-serve` adds the new mapping. `--bg` persists. Default HTTP (`*.ts.net` HSTS preload + Next.js EPROTO interaction — see HSTS section below). Opt-in HTTPS via `TUNNEL_TLS=1`.
- The banner prints the FQDN, the short MagicDNS form, the loopback URL, and the stop hint.
- The dev server is started with `--port $(TUNNEL_PORT) --hostname 127.0.0.1`. Bind LOOPBACK, not `0.0.0.0`. Tailscale's tailscaled fronts the loopback port; binding `0.0.0.0` would expose the dev server on the LAN as well.

## `make funnel` — PUBLIC, opt-in, gated

```makefile
.PHONY: funnel
funnel: _free-port-$(TUNNEL_PORT) _ts-preflight _funnel-gate _funnel-port-check _ts-clear-our-port _ts-bind-funnel _print-banner-funnel
	@PORT=$(TUNNEL_PORT) HOSTNAME=127.0.0.1 $(DEV_CMD) -- --port $(TUNNEL_PORT) --hostname 127.0.0.1

_funnel-gate:
	@if [ "$$PUBLIC_FUNNEL" != "1" ]; then \
	  printf "$(R)refusing: make funnel exposes this dev server to the public internet$(Z)\n"; \
	  printf "$(D)  re-run with:  PUBLIC_FUNNEL=1 make funnel TUNNEL_PORT=443$(Z)\n"; \
	  printf "$(D)  see:  references/tailscale-funnel-rules.md$(Z)\n"; \
	  exit 1; \
	fi

_funnel-port-check:
	@case "$(TUNNEL_PORT)" in \
	  443|8443|10000) ;; \
	  *) \
	    printf "$(R)Funnel only allows ports 443, 8443, 10000$(Z)\n"; \
	    printf "$(D)  re-run with:  PUBLIC_FUNNEL=1 make funnel TUNNEL_PORT=443$(Z)\n"; \
	    exit 1 ;; \
	esac

_ts-bind-funnel:
	@tailscale funnel --bg --https=$(TUNNEL_PORT) $(TUNNEL_PORT) >/dev/null

_print-banner-funnel:
	@node=$$(tailscale status --json 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['Self']['DNSName'].rstrip('.'))" 2>/dev/null); \
	  printf "\n$(B)$(R)$(PROJECT_NAME) dev$(Z)  $(B)$(R)PUBLIC$(Z)  $(D)Tailscale Funnel$(Z)\n"; \
	  printf "  $(C)→$(Z) $(B)https://$$node:$(TUNNEL_PORT)$(Z)  $(R)reachable from anywhere$(Z)\n"; \
	  printf "  $(D)stop:  make tunnel-stop$(Z)\n\n"
```

Why each step:
- `_funnel-gate` refuses unless `PUBLIC_FUNNEL=1` is set — explicit opt-in, never as a side effect.
- `_funnel-port-check` validates the port is one of `443 | 8443 | 10000`. The Makefile validates BEFORE invoking `tailscale funnel`, so the user gets a clear error and a re-run hint instead of an opaque CLI error.
- The recipe uses `tailscale funnel`, not `tailscale serve`. Funnel implies Serve under the hood but the explicit command exposes the right semantics.

If the tailnet ACL doesn't permit Funnel (`nodeAttrs` `funnel` attribute missing for this node), `tailscale funnel` errors out with a clear message. The skill prints the ACL JSON snippet (below) so the user can fix the policy file in the admin web UI.

## `make tunnel-stop` — targeted disable, NEVER reset

```makefile
.PHONY: tunnel-stop
tunnel-stop:
	@tailscale serve --https=443 $(TUNNEL_PORT) off 2>/dev/null || true
	@tailscale serve --http=80   $(TUNNEL_PORT) off 2>/dev/null || true
	@tailscale funnel            $(TUNNEL_PORT) off 2>/dev/null || true
	@pid=$$(lsof -ti :$(TUNNEL_PORT) 2>/dev/null || true); \
	if [ -n "$$pid" ]; then \
	  kill -TERM $$pid 2>/dev/null || true; sleep 0.4; \
	  if kill -0 $$pid 2>/dev/null; then kill -9 $$pid 2>/dev/null || true; fi; \
	fi
	@printf "$(D)tunnel disabled for :$(TUNNEL_PORT); other projects' mappings untouched$(Z)\n"
```

This target NEVER runs `tailscale serve reset` or `tailscale funnel reset`. Reset wipes ALL mappings on this node, including other projects'. The targeted-disable form (`<port> off`) is the only safe shutdown.

If the user explicitly wants to wipe everything (e.g. "I have stale mappings from three dead projects on this machine"), they run `tailscale serve reset` and `tailscale funnel reset` themselves, with eyes open. The Makefile does not auto-generate that target.

## Tailnet ACL gate (Funnel only)

Funnel is double opt-in: tailnet ACL permits it (`nodeAttrs` with `funnel` attribute), AND each device must be approved in the admin web UI (Funnel section). Verified 2026-05-08 against `https://tailscale.com/kb/1223/funnel`.

ACL JSON snippet to add in the tailnet policy file:

```json
{
  "nodeAttrs": [
    {
      "target": ["autogroup:member"],
      "attr":   ["funnel"]
    }
  ]
}
```

Apply at `https://login.tailscale.com/admin/acls`. After saving, individual nodes still need per-device approval in the Funnel section of the admin UI. The `tailscale funnel` CLI errors out with a clear "Funnel attribute not enabled" message if the ACL gate is missing — the skill catches that and prints this snippet.

## App binding rule

Always bind the dev server to `127.0.0.1:<port>`, NEVER `0.0.0.0`, when Funnel or Serve fronts the app. Tailscale's tailscaled terminates TLS at the edge and proxies to the loopback port. Binding `0.0.0.0` would expose the same dev server on the LAN simultaneously, defeating the "Funnel is the only public path" property.

For Docker containers fronted by Tailscale:

```yaml
# docker-compose.yml
services:
  web:
    ports:
      - "127.0.0.1:3457:3457"   # publish ONLY to loopback
```

The `127.0.0.1:` prefix in the publish syntax binds the host port to loopback only. Without it, Docker binds `0.0.0.0` by default. Verified against `https://tailscale.com/blog/docker-tailscale-guide`.

## HSTS / EPROTO trap — why `make tunnel` defaults to HTTP

`*.ts.net` is on Chrome's HSTS preload list (Firefox, Safari too — `https://tailscale.com/blog/letting-everyone-use-https`). This interacts badly with Next.js dev:

| Tunnel scheme | Browser works? | Next.js middleware works? |
|---|---|---|
| `--http=80` | NO — Chrome `ERR_BLOCKED_BY_CLIENT` (HSTS rewrites HTTP→HTTPS, then HTTPS fails) | YES — clean |
| `--https=443` (TLS-front, HTTP backend) | YES — real cert | NO — EPROTO crash on every middleware self-fetch |

Why EPROTO: Next.js middleware self-fetches via `https://localhost:<port>/_next/...` because it sees `X-Forwarded-Proto: https`. The dev server is HTTP, so the TLS handshake fails with `wrong version number`. Chains every Clerk-protected route into a 500.

Decision matrix the skill encodes:

- **Default for Next.js**: `TUNNEL_TLS=0` (HTTP). Loopback browser access works (`http://localhost:<port>`). Tailnet peers get a Chrome HSTS error — they discover `TUNNEL_TLS=1` from the banner if they need cross-device.
- **Optional for non-Next frameworks** (Express / Hono / Fastify / plain Node / Vite without a custom middleware proxy): `TUNNEL_TLS=1` works fine — most non-Next frameworks don't have Next's "middleware self-fetches with X-Forwarded-Proto" behavior.
- **Right answer for Next.js + cross-device**: `TUNNEL_TLS=1` + ensure the app trusts `X-Forwarded-Proto` so middleware self-fetches go to `http://localhost:<port>` (not `https://`). Set up only when explicitly needed.

**EPROTO mechanism.** When Tailscale Serve fronts the app with HTTPS but the app itself is plain HTTP on `127.0.0.1:<port>`, Next.js middleware self-fetches (e.g., `await fetch(request.url)` from middleware) hit `https://<host>:<port>` because `request.url` carries the public scheme. The HTTPS request lands at the HTTP backend → Node throws `EPROTO ... wrong version number`. Workarounds: (a) keep `TUNNEL_TLS=0` (default — Chrome HSTS error on tailnet peers, but middleware works); (b) set `TUNNEL_TLS=1` AND make the app trust `X-Forwarded-Proto: http` so middleware self-fetches use HTTP; (c) avoid middleware self-fetches entirely. The skill defaults to (a).

## macOS DNS verification — `host`/`nslookup`/bare `dig` LIE

On macOS, `host`, `nslookup`, and bare `dig` bypass the system resolver and query upstream DNS directly. They will return `NXDOMAIN` for valid MagicDNS names that resolve correctly via the system resolver (which is what browsers and applications actually use). Verified 2026-05-08 against `https://tailscale.com/docs/features/magicdns` and the macOS `man 5 resolver` page.

CORRECT verification commands on macOS:

```bash
# Tailscale-native — uses MagicDNS directly (Tailscale CLI 1.76+)
tailscale dns query <node>.<tailnet>.ts.net

# macOS system resolver — same one Safari/Chrome use
dscacheutil -q host -a name <node>.<tailnet>.ts.net

# Inspect resolver configuration (which servers handle which suffixes)
scutil --dns
```

For PUBLIC Funnel addresses (i.e. anything you'd expect a non-tailnet client to resolve), use a public resolver:

```bash
# Use any public resolver — 1.1.1.1, 8.8.8.8, 9.9.9.9 all work
dig <node>.<tailnet>.ts.net A    +short @1.1.1.1
dig <node>.<tailnet>.ts.net AAAA +short @1.1.1.1
```

DO NOT hardcode `dig @ns1.dnsimple.com`. The "DNSimple is authoritative for `ts.net`" claim could not be verified from a Tailscale-published page (research note 2026-05-08). Use `@1.1.1.1` or any public resolver — they all answer authoritative queries via the standard delegation chain.

The `/etc/resolver/<tailnet>.ts.net` mechanism (per-suffix resolver override) is real per `man 5 resolver`, but the exact filename is plausible-by-convention rather than directly cited from a Tailscale page. The skill notes this as "macOS-side mechanism, file path inferred from convention".

## AAAA-only failure mode

Tailscale assigns each node an IPv6 address via the 100.64.0.0/10 pool (CGNAT-style v4) and a fd7a:115c:a1e0::/48 prefix (v6). Funnel ingress is dual-stack but if a client lacks IPv6 transit (corporate network, older home router, captive portal), AAAA-only resolution can fail with `Network unreachable` / `ENETUNREACH`.

Diagnostic:

```bash
curl -4 -v https://<node>.<tailnet>.ts.net   # force IPv4
```

If `curl -4` works and `curl` (default) fails, the client has no IPv6 transit. Cite open issues `github.com/tailscale/tailscale/issues/15404` and `github.com/tailscale/tailscale/issues/12473` (open as of 2026-05-08).

The Makefile doesn't auto-detect this; the verification ladder includes `curl -4 -v` as one of the rungs (see `verification-ladder.md`).

## Funnel port restriction (validated in Makefile)

Funnel only accepts these ports:

```
443    HTTPS standard
8443   HTTPS alt
10000  HTTPS alt
```

Any other port → `tailscale funnel` errors out. The `_funnel-port-check` helper validates BEFORE invoking the CLI, so the user gets a clear "Funnel only allows ports 443, 8443, 10000" with a re-run hint. Verified against `https://tailscale.com/kb/1223/funnel` (2026-05-08).

Serve has no such restriction — any port works.

## Verification ladder (handed off to `verification-ladder.md`, summary here)

For tunnel/funnel specifically:

| Rung | Command | Proves |
|---|---|---|
| 1 | `curl -sI http://127.0.0.1:$(TUNNEL_PORT)` | App actually listening on loopback |
| 2 | `tailscale serve status` (or `funnel status`) | Mapping registered with tailscaled |
| 3 (Funnel only) | `dig <node>.<tailnet>.ts.net A    +short @1.1.1.1` and `... AAAA +short @1.1.1.1` | Public DNS resolves to ingress IPs |
| 4 (tailnet-side) | `tailscale dns query <node>.<tailnet>.ts.net` and `curl -sI https://...` | Reachable from this tailnet device |
| 5 (external from this machine, no proxy) | `curl -4 -sI --noproxy '*' https://<node>.<tailnet>.ts.net` | Reachable via public ingress (claims max for the Makefile) |
| 6 (independent client — phone on cellular) | User runs the curl from a non-tailnet device | Actually-public proof; manual user step in the post-deploy banner |

The Makefile's `make verify` claims rung 5 max. Rung 6 is the manual post-tunnel banner the user runs from their phone (off-tailnet, off-LAN).

## Top-5 beginner-failure list

1. **HSTS preload trap.** "I set up `--http=80` and Chrome shows `ERR_BLOCKED_BY_CLIENT`." Cause: `*.ts.net` is HSTS-preloaded; Chrome rewrites HTTP→HTTPS and the HTTPS server isn't there. Fix: switch to `TUNNEL_TLS=1`, or open via the bare short MagicDNS hostname (not the FQDN), or use a non-`.ts.net` custom domain.
2. **`reset` wiped other projects.** "Why did all my mappings disappear?" Cause: `tailscale serve reset` is destructive and wipes ALL mappings. The Makefile uses targeted `<port> off` instead. If the user runs `reset` themselves, that's on them.
3. **macOS `host`/`nslookup` lie.** "I confirmed with `host` that the URL resolves but the browser can't reach it." Cause: macOS `host` bypasses the system resolver. Use `tailscale dns query` or `dscacheutil -q host -a name`.
4. **Funnel port not in 443/8443/10000.** "I tried `tailscale funnel --bg --https=3457 3457` and got an error." Cause: Funnel restricts ports. Use `make funnel TUNNEL_PORT=443` (and `PUBLIC_FUNNEL=1`).
5. **App bound to `0.0.0.0` while Funnel is on.** "Why is my dev server reachable on the LAN AND via Funnel?" Cause: app should bind `127.0.0.1` so only Tailscale's edge fronts it. Fix: `--hostname 127.0.0.1` flag in the dev command (Makefile already does this).

## DO-NOT list (Tailscale)

- **DO NOT run `tailscale serve reset` or `tailscale funnel reset` without explicit user consent.** They wipe ALL mappings on this node, including other projects'. Use targeted `<port> off` for shutdown.
- **DO NOT enable Funnel as a side effect of any other command.** Funnel is opt-in only via `make funnel` with `PUBLIC_FUNNEL=1`.
- **DO NOT bind the app to `0.0.0.0` while Funnel/Serve is on.** Bind `127.0.0.1`. Tailscaled fronts the loopback port.
- **DO NOT use `host`, `nslookup`, or bare `dig` to verify MagicDNS names on macOS.** Use `tailscale dns query`, `dscacheutil -q host -a name`, or `dig @1.1.1.1` for public-facing DNS.
- **DO NOT hardcode `dig @ns1.dnsimple.com`.** The DNSimple-as-NS claim is unverified. Use any public resolver (`@1.1.1.1`, `@8.8.8.8`).
- **DO NOT default to HTTPS for Next.js tunnels.** EPROTO crash. HTTP is the safe default; `TUNNEL_TLS=1` is the explicit opt-in.
- **DO NOT use `tailscale funnel` on ports other than 443/8443/10000.** The CLI rejects other ports; the Makefile validates first for a clearer error.
- **DO NOT trust `curl` alone to confirm browser reachability.** curl ignores HSTS preload; Chrome doesn't.

## Cross-references

- `port-hygiene.md` — `_free-port-$(TUNNEL_PORT)` helper (kill our own only)
- `makefile-frontend.md` — full Makefile recipes for Scenarios A/C/D that consume these helpers
- `makefile-base.md` — universal preamble (SHELL, ANSI palette, `.ONESHELL`)
- `verification-ladder.md` — full 6-rung ladder; Makefile claims rung 5 max
