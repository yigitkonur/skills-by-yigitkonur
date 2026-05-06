# Tailscale Serve setup

[Tailscale Serve](https://tailscale.com/kb/1242/tailscale-serve) proxies a port from this machine to `<hostname>.<tailnet>.ts.net`, reachable from any device signed into the same tailnet. Real Let's Encrypt cert if you opt into HTTPS.

## Hostname customization

The URL uses your Tailscale node hostname. To rename:

```bash
tailscale set --hostname=PROJECT_NAME
```

URL becomes `<scheme>://PROJECT_NAME.<tailnet>.ts.net`. Change is reversible (`tailscale set --hostname=<previous>`), no sudo required, instant.

The Makefile reads the current hostname dynamically from `tailscale status --json`, so no recipe edits are needed when the user renames.

## HTTP vs HTTPS — pick deliberately

The default in `make tunnel` is **HTTP** (`tailscale serve --bg --http=80 PORT`). Counter-intuitive, but for Next.js dev:

- HTTPS via Tailscale terminates TLS at :443, then proxies to your HTTP dev server. Next.js middleware sees `X-Forwarded-Proto: https` but `Host: localhost:PORT` and tries to internally proxy `https://localhost:PORT/...` → **EPROTO crash on every Clerk-protected route**.
- HTTP avoids the protocol mismatch. The tailnet itself is end-to-end encrypted by WireGuard, so HTTPS would be belt-on-belt anyway.
- See `references/hsts-preload-trap.md` and `references/eproto-tls-mismatch.md` for the full reasoning.

Set `TUNNEL_TLS=1 make tunnel` to opt into HTTPS — only useful if you've fixed the upstream proxy-protocol handling first (or for non-Next frameworks).

## Funnel is opt-in only

Tailscale Funnel exposes the dev server **to the public internet**. Reset it on every `make tunnel` run:

```sh
tailscale funnel reset >/dev/null 2>&1 || true
```

Never default `make tunnel` to Funnel. If a user explicitly asks for "share my dev with someone outside my tailnet" — that's the only context where `tailscale funnel --bg PORT` is appropriate.

## Idempotent re-wiring

Always reset before adding a new route. Otherwise stale routes accumulate from previous sessions:

```sh
tailscale serve  reset >/dev/null 2>&1 || true
tailscale funnel reset >/dev/null 2>&1 || true
tailscale serve --bg --http=80 PORT
```

## Pre-flight checks

```sh
command -v tailscale >/dev/null 2>&1 || exit 1   # CLI installed
tailscale status >/dev/null 2>&1   || exit 1     # account signed in
```

If either fails, surface an actionable message:
- "tailscale CLI not found — brew install --cask tailscale"
- "Tailscale not signed in — open the menu-bar icon and log in"

## DNS resolution from peer devices

MagicDNS resolves `<short>` AND `<short>.<tailnet>.ts.net` from any signed-in peer. If MagicDNS isn't enabled in the admin console, only the FQDN works.

```bash
# Confirm MagicDNS suffix
tailscale status --json | jq -r '.MagicDNSSuffix'
```

If empty, the user needs to enable MagicDNS in https://login.tailscale.com/admin/dns.

## Troubleshooting cross-device unreachability

| Symptom | Cause | Fix |
|---|---|---|
| Phone shows `ERR_NAME_NOT_RESOLVED` for `<host>.ts.net` | MagicDNS off, or phone not on tailnet | Enable MagicDNS, or sign phone into tailnet |
| MacBook gets HTTP 200 but blank/Internal Server Error | Tunnel fine; app crash | Check dev server log on the host; same crash via `localhost:PORT` |
| Chrome shows `ERR_BLOCKED_BY_CLIENT` for HTTP `.ts.net` URL | HSTS preload of `*.ts.net` rejects HTTP | Switch to HTTPS (`TUNNEL_TLS=1 make tunnel`), accept EPROTO if Next | 
| `make tunnel` says "tailscale not signed in" | Daemon up but account not linked | `tailscale up` interactively |
| Funnel left on from previous session | Public exposure persisted | `tailscale funnel reset` |

## Stop / clean

`make tunnel-stop` resets both serve and funnel and kills the dev process:

```sh
tailscale serve  reset
tailscale funnel reset
lsof -ti :$(TUNNEL_PORT) | xargs -r kill -9
```

Always reset both — funnel state is independent of serve state.
