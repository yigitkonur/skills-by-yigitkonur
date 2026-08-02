# Proxy Testing

Use the proxy when another process needs a local MCP HTTP endpoint backed by an existing `mcpc` session.

## Start a proxied session

```bash
mcpc connect https://research-mcp.yigitkonur.com/mcp @proxy-demo --proxy 127.0.0.1:8787
mcpc connect https://research-mcp.yigitkonur.com/mcp @proxy-auth --proxy 127.0.0.1:8788 --proxy-bearer-token demo-token
```

## What to test

```bash
curl http://127.0.0.1:8787/health
mcpc connect http://127.0.0.1:8788/mcp @proxy-check --no-profile
mcpc connect http://127.0.0.1:8788/mcp @proxy-check-auth --no-profile -H 'Authorization: Bearer demo-token'
mcpc close @proxy-check
mcpc close @proxy-check-auth
```

Current behavior (verified against 0.6.0):

- `/health` is the stable health endpoint: `GET /health` → `200 {"status":"ok"}`. It runs before bearer-token validation but is still subject to Host/Origin validation below — a spoofed `Host`/`Origin` gets a `403` even on `/health`.
- the proxy enforces the real MCP session lifecycle (`initialize` → `mcp-session-id` → subsequent calls) — it is NOT a stateless pass-through; a bare `tools/list` before `initialize` fails with `Server not initialized`.
- the proxy identifies itself in `serverInfo` as `mcpc-proxy@<session>` (e.g. `mcpc-proxy@proxy-demo`), not the real upstream server name — tests asserting on `serverInfo.name` through the proxy must expect this, not the upstream server's identity.
- with `--proxy-bearer-token` set: a request missing `Authorization` gets `401`; a wrong token gets `403`; the correct `Authorization: Bearer <token>` header succeeds. Confirmed live via both raw `curl` and `mcpc connect ... -H`.
- **DNS-rebinding protection (0.5.0+):** the proxy validates `Host` and `Origin` headers. When bound to loopback (the default), a spoofed `Host` or cross-origin `Origin` pointing elsewhere gets `403 Forbidden`. This blocks a malicious web page from pointing a hostname it controls at `127.0.0.1` to ride on the bridge's authenticated upstream session.
- multiple clients can connect to the same proxied session concurrently (0.5.0+; previously a second client was locked out until restart).
- `HTTP DELETE` against the proxy actually terminates the session (0.5.0+ fix; previously a stub that didn't).
- the proxy belongs to the detached session bridge and survives the original terminal after a successful `connect`

## What not to overstate

- do not treat `/mcp` as the only public path contract unless you are intentionally documenting implementation detail
- do not describe `MCP-Session-Id` as proxy-to-bridge IPC; upstream session resumption remains between bridge and upstream server
- do not recommend `nohup` or `tmux` as the normal fix for proxy longevity
- a proxy does not make an untrusted server safe — stdio servers still touch your system, and HTTP servers still hold your credentials; only connect to servers you trust

## Debugging

Prefer the built-in log command over raw file access — it spans rotated log files and supports streaming/filtering:

```bash
mcpc @proxy-demo logs -n 120
mcpc @proxy-demo logs --follow
mcpc @proxy-demo logs --since 1h
```
