# When to use a tunnel + remote client debugging

*Read this when testing your MCP server with ChatGPT, Claude, or other remote MCP clients.*

## When to tunnel

**Tunnel your server when:**

- You need to test in **ChatGPT, Claude, or another remote client** that cannot reach `localhost`.
- Your local network is behind a NAT or firewall that blocks external access.
- You want to test MCP Apps (widgets) in a remote client before deploying.
- You are iterating on server code and want instant feedback from a remote client.

**Do not use a tunnel when:**

- You can test locally with `inspector.mcp-use.com` or `npx @mcp-use/inspector`.
- Your client runs on the same machine (localhost connections do not need a tunnel).
- You are ready for production — deploy the server instead.

## Debugging remote clients

When testing an MCP server tunneled to a remote client (ChatGPT, Claude, etc.), use the inspector locally to diagnose issues before (or after) involving the remote client:

1. **Start the tunnel:**
```bash
mcp-use dev --tunnel
```

2. **Open the local inspector:**
```bash
npx @mcp-use/inspector --url http://localhost:3000/mcp
```

This connects to the local MCP endpoint. You can test all tools, views, and resources without involving the remote client.

3. **Test the remote client separately:**

Copy the public tunnel URL into your remote MCP client. If the remote client fails to connect or shows errors, first verify the server works with the local inspector. If local works but remote fails, check:
- The tunnel URL includes `/mcp` suffix (non-negotiable).
- The remote client supports Streamable HTTP transport (mcp-use v2 does not serve stdio or SSE-transport).
- If OAuth: the remote client's OAuth callback matches your server's configuration.
- Network/firewall: the remote client can reach `https://<subdomain>.local.mcp-use.run`.

4. **Inspect view/widget rendering:**

If you are testing MCP Apps (views), use the inspector's widget debug panel (protocol toggle, CSP mode, device/locale panels). See references/20-inspector for the full debug workflow.

After debugging locally, the remote client should connect to the same server with the tunnel URL.
