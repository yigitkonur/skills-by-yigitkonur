# Proxy Testing

Use the proxy when another process needs a local MCP HTTP endpoint backed by an existing `mcpc` session.

## Start a proxied session

```bash
mcpc connect https://research.yigitkonur.com/mcp @proxy-demo --proxy 127.0.0.1:8787
mcpc connect https://research.yigitkonur.com/mcp @proxy-auth --proxy 127.0.0.1:8788 --proxy-bearer-token demo-token
```

## What to test

```bash
curl http://127.0.0.1:8787/health
mcpc connect http://127.0.0.1:8788/mcp @proxy-check --no-profile
mcpc connect http://127.0.0.1:8788/mcp @proxy-check-auth --no-profile -H 'Authorization: Bearer demo-token'
mcpc close @proxy-check
mcpc close @proxy-check-auth
```

Current behavior to document:

- `/health` is the stable health endpoint
- treat `/health` as liveness only; do not use it to prove bearer-token enforcement
- local `mcpc 0.2.4` tests accepted real MCP connects through the proxied `/mcp` endpoint with and without an `Authorization` header
- document proxy auth only after you verify the exact release behavior yourself
- the proxy belongs to the detached session bridge and survives the original terminal after successful `connect`

## What not to overstate

- do not treat `/mcp` as the only public path contract unless you are intentionally documenting implementation detail
- do not claim bearer enforcement from `--proxy-bearer-token` alone unless you re-verified it with a real MCP request
- do not describe `MCP-Session-Id` as proxy-to-bridge IPC; upstream session resumption remains between bridge and upstream server
- do not recommend `nohup` or `tmux` as the normal fix for proxy longevity

## Debugging

Proxy failures are usually explained by the session log:

```bash
sed -n '1,120p' ~/.mcpc/logs/bridge-@proxy-demo.log
```
