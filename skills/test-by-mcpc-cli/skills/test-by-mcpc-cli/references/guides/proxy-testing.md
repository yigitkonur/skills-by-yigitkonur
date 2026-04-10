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
curl -H 'Authorization: Bearer demo-token' http://127.0.0.1:8788/health
```

Current behavior to document:

- `/health` is the stable health endpoint
- missing or malformed bearer auth returns `401`
- wrong bearer token returns `403`
- the proxy belongs to the detached session bridge and survives the original terminal after successful `connect`

## What not to overstate

- do not treat `/mcp` as the only public path contract unless you are intentionally documenting implementation detail
- do not describe `MCP-Session-Id` as proxy-to-bridge IPC; upstream session resumption remains between bridge and upstream server
- do not recommend `nohup` or `tmux` as the normal fix for proxy longevity

## Debugging

Proxy failures are usually explained by the session log:

```bash
sed -n '1,120p' ~/.mcpc/logs/bridge-@proxy-demo.log
```
