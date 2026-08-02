# Connect Real Clients

*Read this when you want to test your MCP server with actual MCP clients or hosted platforms.*

## Via mcp-use CLI

Save your local server connection and test from the command-line client.

```bash
# From another terminal, while npm run dev is running:
npx mcp-use client connect my-local http://localhost:3000/mcp

# List tools
npx mcp-use client my-local tools list

# Call a tool
npx mcp-use client my-local tools call get-weather --arguments '{"location":"Paris"}'

# Interactive REPL
npx mcp-use client my-local interactive
```

The client keeps connections saved in `~/.mcp-use/` for reuse.

## Tunnel for Remote Clients (ChatGPT, Claude.ai)

When you want to test with hosted platforms, expose your local server via public HTTPS tunnel:

```bash
npm run dev -- --tunnel
```

Output shows:
```
[mcp-use] starting tunnel for port 3000…
mcp-use public MCP URL: https://happy-blue.local.mcp-use.run/mcp
```

**Copy the full URL** (including `/mcp` suffix). Use this in ChatGPT or Claude App config.

To test the tunnel works:

```bash
npx mcp-use client connect tunnel-test https://happy-blue.local.mcp-use.run/mcp
npx mcp-use client tunnel-test tools list
```

Tunnel expires after **24 hours** or 1 hour of inactivity. Rate limit: 5 active tunnels per IP.

## Deploy for Stable Public URL

Tunnels are temporary. For permanent public access, deploy your server.

```bash
mcp-use login  # One-time OAuth
mcp-use deploy
```

Result: `https://<slug>.deploy.mcp-use.com/mcp` (available 24/7, no expiry)

Use this URL in any MCP client settings.

## ChatGPT Integration

After tunnel or deploy, add to ChatGPT:

1. ChatGPT → **Custom GPT** (or App) → **Connections** (or MCP settings)
2. Paste your tunnel/deploy URL with `/mcp` suffix
3. ChatGPT tests connection; shows available tools
4. Use tool calls in chat

Inspector can confirm ChatGPT's view rendering:
- Open server in **Inspector** → **Tools tab** → run a tool that returns a view
- Inspector shows the view rendered in both **MCP Apps** and **ChatGPT Apps** protocol modes (see references/20-inspector/08-debugging-chatgpt-apps.md)

## Troubleshooting Client Connection

| Issue | Check |
| --- | --- |
| `Connection refused` | Server running? `npm run dev` started? |
| `404` | URL correct? Must include `/mcp` suffix |
| `CORS error` | Using tunnel/deploy (not localhost)? Add `cors: {}` to ServerConfig |
| `OAuth required` | Connection shows `pending_auth`? Complete OAuth in Inspector first |
| Tool succeeds locally, fails in ChatGPT | Check CSP headers in view config (see references/18-mcp-apps/server-surface/05-csp-metadata.md) |

## Sister Skills

- **test-by-mcpc-cli**: For live v2 protocol verification with the official mcpc client
- **build-mcp-use-client**: For building a custom MCP client in TypeScript

