# Tunneling: Expose local MCP to remote clients

*Read this when testing an MCP server in ChatGPT, Claude, or other remote MCP clients without deploying.*

A tunnel creates a temporary public HTTPS URL that forwards to your local MCP endpoint. Keep the terminal running while you test; the URL stops working when the process exits.

## Start a tunnel

**With mcp-use dev (recommended for development):**
```bash
mcp-use dev --tunnel
```

Output includes:
```
[mcp-use] dev server ready
  ➜ MCP endpoint:  http://localhost:3000/mcp
  ➜ Inspector:     http://localhost:3000/mcp/inspector
[mcp-use] starting tunnel for port 3000…
  ➜ Tunnel:        https://happy-blue.local.mcp-use.run/mcp
```

**Copy the full URL** (including `/mcp`) into your remote MCP client.

**With mcp-use start (for testing production builds):**
```bash
mcp-use build
mcp-use start --port 3000 --tunnel
```

Output includes:
```
[mcp-use] starting tunnel for port 3000…
mcp-use server running at http://localhost:3000/mcp
mcp-use public MCP URL: https://happy-blue.local.mcp-use.run/mcp
```

**With a standalone server already running on /mcp:**
```bash
npx @mcp-use/tunnel 3000
```

Output:
```
✔ Local MCP server available at

  https://happy-blue.local.mcp-use.run

```

The standalone package prints the bare origin — **append `/mcp` yourself** before handing the URL to a client; the tunnel only forwards `/mcp**` and `/mcp-use**` paths, so other paths (including the bare origin) return `404`.

## URL format

The tunnel URL is always:
```
https://<subdomain>.local.mcp-use.run/mcp
```

The `/mcp` suffix is required — clients must include it.

**Inspector is not reachable through the tunnel.** Only the MCP endpoint is exposed publicly; the Inspector UI, its proxy, and its OAuth routes stay local-only. Requesting `/mcp/inspector` through the tunnel URL returns `404`. Debug with the Inspector on the local URL (`http://localhost:3000/mcp/inspector`) while the remote client talks to the tunnel URL.

## Verify

Test the tunnel with the `mcp-use client` CLI:
```bash
npx mcp-use client connect tunnel-test https://happy-blue.local.mcp-use.run/mcp
npx mcp-use client tunnel-test tools list
```

This performs the MCP handshake and saves the connection as `tunnel-test`. If the server requires OAuth or bearer auth, complete the auth flow or pass credentials before testing.

## Lifetime and limits

- **Active only while running:** Close the terminal and the URL stops working.
- **24-hour expiry:** Tunnels auto-expire after 24 hours.
- **Inactive cleanup:** After 1 hour without activity, tunnels are cleaned up.
- **Rate limits:** 10 tunnels per hour per IP; 5 active tunnels per IP.
- **Auto-reconnect:** With `mcp-use dev --tunnel` or `mcp-use start --tunnel`, dropped tunnel connections re-establish automatically while the command runs.

For a stable public URL, deploy the server instead of using a temporary tunnel.

## Stop

Press `Ctrl+C` in the terminal running the tunnel.

- `mcp-use dev --tunnel` or `mcp-use start --tunnel`: Stops both server and tunnel.
- `npx @mcp-use/tunnel`: Stops only the tunnel; local server continues running.

See references/25-deploy for permanent deployment options.
