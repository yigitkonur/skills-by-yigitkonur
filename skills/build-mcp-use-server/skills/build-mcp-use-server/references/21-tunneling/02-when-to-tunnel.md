# When to Tunnel

Tunneling solves one problem: a remote client cannot reach `localhost`. If you're not bridging a remote client to your laptop, you don't need a tunnel.

---

## Decision Table

| Scenario | Tunnel? | Reason |
|---|---|---|
| Local Inspector (browser) → local MCP on `localhost:3000` | no | Browser is on the same machine. |
| Browser-based Inspector on the same laptop → local MCP | no | The browser can reach `localhost` directly. |
| Browser-based Inspector on another device → local MCP | yes | That device cannot reach your laptop's `localhost`. |
| ChatGPT custom connector → local MCP | yes | ChatGPT runs server-side, never reaches localhost. |
| Claude Desktop with stdio command | no | Claude spawns the local process directly. |
| Claude with remote connector → local MCP | yes | Connector POSTs from cloud. |
| Production deploy | no | Deploy properly; tunnels expire in 24h. |
| Demoing your MCP server to a teammate over Zoom | yes | Their machine cannot reach your localhost. |

---

## 1. Testing ChatGPT Against Local Dev

The canonical use case. ChatGPT's custom connector flow needs a public URL.

```bash
# Terminal 1 — your MCP server with hot reload
mcp-use dev --mcp-dir src/mcp --port 3001

# Terminal 2 — tunnel
npx @mcp-use/tunnel 3001
# → https://happy-blue-cat.local.mcp-use.run/mcp
```

Add the printed URL as a custom connector in ChatGPT. Iterate: edit code, hot-reload picks it up, ChatGPT keeps using the same URL until you `Ctrl+C` the tunnel.

---

## 2. Browser-Based Inspector with a Local Server

An Inspector that runs in your browser can call whatever MCP URL you give it. For a local server, the browser can hit `localhost`, so a tunnel is not required when:

- You're using the Inspector on the same machine as the server.

A tunnel **is** required when:

- Sharing an Inspector session with a teammate over Zoom (their browser can't reach your localhost).
- Running the Inspector on a tablet / phone that's not on the same network.
- Debugging through a corporate proxy that blocks `localhost` references.

---

## 3. Public-URL Smoke Tests

For an end-to-end check that your local server works through a public URL:

```bash
# Step 1: start server
mcp-use start --port 3000 --tunnel

# Step 2: copy the printed public URL from stdout

# Step 3: run the same HTTP initialize check your client needs
curl -s -X POST "https://happy-blue-cat.local.mcp-use.run/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"smoke","version":"0"}}}'
```

Caveat: tunnel hostnames are random per run, so the test runner must read the URL from stdout, not hardcode it.

For most CI you don't need this — hitting `localhost` is faster and deterministic. Reserve tunneled CI for verifying behavior that only manifests over a public hostname.

---

## 4. When Not to Tunnel

| Situation | Better choice |
|---|---|
| You want to share a stable URL with a non-developer | Deploy and share the production URL. |
| You want to test the production deploy itself | Hit the prod URL directly — no tunnel. |
| You're testing locally with the local Inspector | `localhost:3000` directly, no tunnel needed. |
| You want a long-lived URL across days | Deploy. Tunnels die at 24h. |
| You're using Claude Desktop with stdio | stdio is local, no HTTP, no tunnel applies. |

---

## 5. Tunnel Auth Considerations

The tunneling doc does not describe tunnel-level authentication. Treat the public URL as reachable by anyone who learns it.

- If your MCP server has no auth, **the tunnel is open to the internet** for the next 24 hours.
- Add OAuth (`oauthAuth0Provider`, `oauthSupabaseProvider`, or another exported provider) before tunneling a server that touches sensitive data.
- Or restrict with `server.use(...)` middleware that checks a request header you define:
  ```typescript
  const expectedToken = "dev-only-token";

  server.use("/mcp", async (c, next) => {
    if (c.req.header("X-Dev-Token") !== expectedToken) {
      return c.text("Unauthorized", 401);
    }
    await next();
  });
  ```

---

## 6. See Also

- **Tunnel basics** → `01-overview.md`
- **Debugging when a remote client connects via tunnel** → `03-debugging-remote-clients.md`
- **OAuth before exposing a server** → `../11-auth/01-overview-decision-matrix.md`
- **Production deploy** → `../25-deploy/01-decision-matrix.md`
