# HSTS preload trap — why `*.ts.net` HTTP fails in browsers

This is the single highest-impact gotcha when wiring `make tunnel` to Tailscale.

## Symptom

User opens `http://<host>.ts.net/anything` in Chrome. Result:

```
ERR_BLOCKED_BY_CLIENT
```

Curl on the same machine returns HTTP 200 fine. Confusing.

## Cause

Tailscale enrolled the entire `.ts.net` zone on Chrome's HSTS preload list (and Firefox's, Safari's). The browser refuses to issue any HTTP request to `*.ts.net` and rewrites it to HTTPS internally — which then fails because we're serving HTTP.

curl ignores HSTS preload, which is why command-line probes mislead you.

## Decision matrix

| Tunnel scheme | Browser works? | Next.js middleware works? | Verdict |
|---|---|---|---|
| `--http=80` | ❌ Chrome `ERR_BLOCKED_BY_CLIENT` | ✓ Clean | Wrong for `.ts.net` |
| `--https=443` (TLS-front, HTTP backend) | ✓ Real cert | ❌ EPROTO on middleware self-fetches | Wrong for Next without proxy headers |
| `--https=443` + `--bg` + `X-Forwarded-Proto: https` honored by app | ✓ | ✓ | Right answer for Next |
| `--http=80` + non-`.ts.net` domain (e.g. plain LAN bind) | ✓ | ✓ | Right answer when not using Tailscale |

## What to do

For Next.js + Tailscale Serve, the only correct production-grade config is:

1. `tailscale serve --bg --https=443 PORT` (HTTPS, real Let's Encrypt cert)
2. App must trust `X-Forwarded-Proto` header so middleware self-fetches go to `http://localhost:PORT` (not `https://`)
3. `next.config.ts` must list the FQDN in `allowedDevOrigins`

For non-Next frameworks (Express/Hono/Fastify): use HTTPS too, but test EPROTO doesn't bite. Most frameworks don't have Next.js's "middleware self-fetches with X-Forwarded-Proto" behavior.

For dev mode where you don't care about the EPROTO crashes (favicon-only, static-asset, public-only routes): HTTP works on Chrome only via the bare hostname workaround:

```bash
# This works because Chrome HSTS-preloads the FQDN, not the bare hostname
tailscale serve --bg --http=80 PORT
# Open http://<short-hostname>/  ← bypass HSTS preload
# But http://<short>.<tailnet>.ts.net/ is still blocked
```

That's brittle. Don't rely on it.

## Why our Makefile defaults to HTTP

The zeo-radar Makefile defaults `make tunnel` to `--http=80` despite this trap, with `TUNNEL_TLS=1` as an opt-in. Reasoning:

- The default user (typing `make tunnel` for the first time) is on this machine, opening `http://localhost:PORT` directly. No HSTS issue.
- Cross-device users (typing `make tunnel` to share with a phone/MacBook) hit the HSTS wall and discover `TUNNEL_TLS=1` from the banner.
- Making HTTPS the default would mean every Next.js dev session starts with EPROTO crashes and a blank-page user experience that's hard to debug.

If the project uses a non-`.ts.net` custom domain (Tailscale lets you BYO), HTTP is fine — no HSTS preload outside `.ts.net`.

## Testing

curl is **insufficient** for verifying tunnel reachability. Always test in a real browser:

```bash
agent-browser --session test open "http://<host>.ts.net/"
agent-browser --session test get url
agent-browser --session test get text body
```

If the URL changes to `https://...` or you get `ERR_BLOCKED_BY_CLIENT`, you've hit the HSTS trap.

## Resetting Chrome HSTS for testing

Useful only for *non*-`.ts.net` domains. `.ts.net` is on the static preload list and CANNOT be reset:

```
chrome://net-internals/#hsts
```

Type the host into "Delete domain security policies" — works for opt-in HSTS, no-op for preload list.

## References

- Chrome HSTS preload list: https://hstspreload.org/
- Tailscale's enrollment: https://tailscale.com/blog/letting-everyone-use-https
