# Inspector CLI

Run the Inspector standalone via `npx` — no install, no project required.

## Quick start

```bash
npx @mcp-use/inspector
```

Boots the inspector server on the first available port starting at `8080`, opens the browser, prints the URL.

## Flags

| Flag | Purpose | Default |
|---|---|---|
| `--url <url>` | Auto-connect to an MCP server on load | none |
| `--port <port>` | Starting port; auto-increments if taken | `8080` |
| `--no-open` | Do not open browser automatically | opens by default |
| `--help`, `-h` | Print help and exit | — |

`--port` accepts `1`–`65535`. If the chosen port is in use, the inspector picks the next free one and logs the actual port.

## URL formats

```bash
# Local HTTP MCP server
npx @mcp-use/inspector --url http://localhost:3000/mcp

# Remote
npx @mcp-use/inspector --url https://mcp.linear.app/mcp

# WebSocket
npx @mcp-use/inspector --url ws://localhost:8080/mcp
```

Must include the protocol. `localhost:3000/mcp` (no scheme) is rejected.

## Combining flags

```bash
npx @mcp-use/inspector \
  --url http://localhost:3000/mcp \
  --port 9000 \
  --no-open
```

CI / headless environments should always pass `--no-open`.

## Environment variables

### `MCP_INSPECTOR_FRAME_ANCESTORS`

Whitelist of origins allowed to embed the inspector or its widget iframes (CSP `frame-ancestors`). Space-separated.

| Mode | Default |
|---|---|
| Development | `*` |
| Production | `'self'` |

```bash
# Specific origins
MCP_INSPECTOR_FRAME_ANCESTORS="https://app.example.com https://dev.example.com" \
  npx @mcp-use/inspector

# All origins (dev only)
MCP_INSPECTOR_FRAME_ANCESTORS="*" npx @mcp-use/inspector

# Wildcards
MCP_INSPECTOR_FRAME_ANCESTORS="https://*.example.com http://localhost:*" \
  npx @mcp-use/inspector
```

### `MCP_URL`

External base URL of the MCP server. Use when running behind a tunnel or reverse proxy where the public host differs from `localhost`.

```bash
MCP_URL=https://abc123.ngrok.io npx @mcp-use/cli dev
MCP_URL=https://3000-abc123.e2b.app npx @mcp-use/cli dev
MCP_URL=https://my-tunnel.trycloudflare.com npx @mcp-use/cli dev
```

When set, widget asset URLs and Vite HMR WebSocket connections route through the proxy. When unset, the CLI generates a `localhost` URL automatically.

## Tunneling pairing

Pair the CLI with `@mcp-use/tunnel` to expose a local server publicly while inspecting locally:

```bash
# Terminal 1: server + auto-mounted inspector
mcp-use dev --tunnel

# Terminal 2: open the printed inspector URL, or hit it from any browser
```

For the CLI flow without auto-mount:

```bash
# Terminal 1: server
mcp-use dev

# Terminal 2: tunnel
npx @mcp-use/tunnel 3000
# → https://happy-cat.local.mcp-use.run/mcp

# Terminal 3: standalone inspector pointed at the tunnel
npx @mcp-use/inspector --url https://happy-cat.local.mcp-use.run/mcp
```

Tunnel detail lives in `../21-tunneling/`.

## Terminal output

```
🚀 MCP Inspector running on http://localhost:8081
📡 Auto-connecting to: http://localhost:3000/mcp
🌐 Browser opened
```

The first line is the URL to share or open manually if `--no-open` was passed.

## Troubleshooting

**Port already in use** — pass `--port`, or kill the holder:

```bash
lsof -ti:8080 | xargs kill
```

**Invalid URL** — include the scheme. `localhost:3000/mcp` is invalid; `http://localhost:3000/mcp` is valid.

**Browser does not open** — the inspector still ran. Read the URL from the terminal and open it manually. With `--no-open`, that is the expected flow.
