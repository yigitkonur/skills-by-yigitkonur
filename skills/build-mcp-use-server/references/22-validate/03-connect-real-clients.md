# Connect Real Clients

*Read this when you want to test your MCP server with actual MCP clients or hosted platforms.*

## Via mcp-use CLI

Save your local server connection and test from the command-line client.

```bash
# From another terminal, while npm run dev is running:
npx mcp-use client connect my-local http://localhost:3000/mcp

# List tools
npx mcp-use client my-local tools list

# Call a tool — arguments are key=value pairs, key:=<json> for typed/nested values, or one JSON object
npx mcp-use client my-local tools call get-weather location=Paris
npx mcp-use client my-local tools call get-weather '{"location":"Paris"}'
```

There is no `interactive`/REPL subcommand — `client` scopes to `tools` (`list`, `describe <tool>`, `call <tool> [args...]`), `resources` (`list`, `read <uri>`), `prompts` (`list`, `get <prompt> [args...]`), and `auth` (`status`, `logout`).

The client keeps saved server metadata under `~/.mcp-use/client/servers.json` and credentials under `~/.mcp-use/client/credentials/`.

## Tunnel for Remote Clients (ChatGPT, Claude.ai)

When you want to test with hosted platforms, expose your local server via public HTTPS tunnel:

```bash
mcp-use dev --tunnel
```

Successful output includes a tunnel endpoint:
```
[mcp-use] starting tunnel for port 3000…
  ➜ MCP endpoint:  http://localhost:3000/mcp
  ➜ Inspector:     http://localhost:3000/mcp/inspector
  ➜ Tunnel:        https://happy-blue.local.mcp-use.run/mcp
```

**Copy the value after `Tunnel:`** (including `/mcp` suffix — do not copy only the bare host). Use this in ChatGPT or Claude App config. Note that a public tunnel only exposes the MCP endpoint; `/mcp/inspector` returns 404 through the tunnel URL — Inspector stays local-only.

To test the tunnel works:

```bash
npx mcp-use client connect tunnel-test https://happy-blue.local.mcp-use.run/mcp
npx mcp-use client tunnel-test tools list
```

Keep the terminal running the tunnel process open — the public URL stops working when it exits.

Tunnel limits:

| Limit | Value |
| --- | --- |
| Lifetime | Expires 24 hours after creation |
| Inactive cleanup | 1 hour of no activity |
| Creation rate limit | 10 tunnel creations per IP per hour |
| Active tunnel limit | 5 active tunnels per IP |
| Close behavior | Closes when the CLI process exits |

## Deploy for Stable Public URL

Tunnels are temporary. For permanent public access, deploy your server.

```bash
mcp-use login  # One-time OAuth
mcp-use deploy
```

Copy the exact generated MCP URL from the Manufact Cloud dashboard after the deployment finishes — do not infer the hostname from the server slug; the dashboard is authoritative for both generated and custom domains.

```bash
export MCP_URL="PASTE_THE_GENERATED_MCP_URL"
npx mcp-use client connect production "${MCP_URL}"
npx mcp-use client production tools list
```

Use that same exact URL in any other MCP client configuration.

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

