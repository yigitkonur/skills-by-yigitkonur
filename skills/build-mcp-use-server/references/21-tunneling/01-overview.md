# Tunneling Overview

A tunnel exposes your local MCP server through a public URL so a remote MCP client (ChatGPT, Claude, or another client) can reach it without you deploying anything. Use it during development to close the loop between code change and remote-client behavior.

---

## What a Tunnel Does

```
ChatGPT / Claude / other MCP client
        │
        ▼
https://happy-blue-cat.local.mcp-use.run/mcp
        │   (TLS, public)
        ▼
   tunnel relay  ──────►  your laptop on localhost:3000
                          (mcp-use start --port 3000)
```

A tunnel:

- Forwards HTTPS POST/GET to your local `/mcp` endpoint.
- Issues a public subdomain on `local.mcp-use.run` (e.g. `happy-blue-cat.local.mcp-use.run`).
- Runs only while the tunnel command runs — `Ctrl+C` closes it.

---

## Two Ways to Start One

### A. Bundled flag on `mcp-use start`

```bash
mcp-use start --port 3000 --tunnel
```

Starts the MCP server **and** the tunnel in one process. Use during normal `start` runs when you also want remote access.

### B. Standalone tunnel command

```bash
# Terminal 1
mcp-use start --port 3000

# Terminal 2
npx @mcp-use/tunnel 3000
```

Use the standalone form when:

- You started the server some other way (`tsx index.ts`, `pnpm dev`, `node dist/server.js`).
- You want to point the tunnel at a non-mcp-use server that exposes `/mcp`.

The tunnel works against **any** MCP server, not just mcp-use, as long as it serves on the `/mcp` path.

---

## Output Shape

```
╭────────────────────────────╮
│  Tunnel Created Successfully!  │
╰────────────────────────────╯

  Public URL:
     https://happy-blue-cat.local.mcp-use.run/mcp

  Subdomain: happy-blue-cat
  Local Port: 3000
```

Hand the public URL to the remote client (ChatGPT custom connector, Claude, or any MCP client that needs a public URL).

---

## Limits

| Limit | Value |
|---|---|
| Tunnel max lifetime | 24 hours from creation |
| Idle cleanup | 1 hour with no activity |
| Tunnel creations per IP per hour | 10 |
| Max simultaneously active tunnels per IP | 5 |

The tunnel closes when the command stops. Restart and you'll get a new subdomain.

---

## When to Reach for It

- Testing your MCP server against ChatGPT, Claude, or another remote MCP client before deploying.
- Smoke-testing a CI build by running `mcp-use start --tunnel` and pointing a remote test runner at the URL.
- Debugging connection issues in a production-like (TLS, public hostname) shape.

When **not** to use a tunnel:

- Production. Deploy properly — see `../25-deploy/01-decision-matrix.md`.
- Tunnels are not stable URLs; CI that hardcodes a tunnel hostname will break.
- Long-lived agent sessions over a tunnel hit the 24h limit.

---

## Cluster Map

- **`02-when-to-tunnel.md`** — concrete scenarios that need a tunnel vs ones that don't.
- **`03-debugging-remote-clients.md`** — what to inspect when a remote client hits your tunneled server and something breaks.

---

**Canonical doc:** https://manufact.com/docs/tunneling
