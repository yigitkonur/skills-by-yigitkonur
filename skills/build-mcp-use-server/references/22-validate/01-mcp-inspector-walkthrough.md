# MCP Inspector — Validation Entry Point

The Inspector is the primary tool for validating an mcp-use server before shipping. It exercises every JSON-RPC surface — tools, resources, prompts, elicitation, notifications — from a browser UI you can connect to any local or remote MCP endpoint.

This file is the high-level "use the Inspector to validate" guide. The deep walkthrough (every tab, every panel, every keyboard shortcut, the RPC logging surface, CSP modes, BYOK chat) lives in `../20-inspector/`.

---

## When to use the Inspector

| Situation | Why the Inspector wins |
|---|---|
| Verifying a tool's schema and output shape | RPC Messages panel shows the raw `tools/list` and `tools/call` payloads |
| Reproducing a client bug | Connect Inspector to the same `/mcp` URL the broken client is using |
| Debugging widget rendering | CSP toggle, device/locale panels, protocol switch |
| Adding the server to Cursor / VS Code / Claude Desktop | Header has an "Add to Client" button that writes the config for you |
| Sanity check before deploy | One-shot tour of all tabs catches missing tools, broken schemas, dead resources |

---

## Launch flow

```bash
# Standalone Inspector — point at any /mcp URL
npx @mcp-use/inspector --url http://localhost:3000/mcp

# Custom port (default 8080; auto-falls-back if busy)
npx @mcp-use/inspector --port 9000

# Built-in Inspector — exposed automatically by `mcp-use dev`
mcp-use dev
# → http://localhost:3000/inspector
```

The standalone Inspector is also hosted at `https://inspector.mcp-use.com`; point it at a tunneled URL for remote validation without installing anything locally.

---

## Connect flow

1. Open the Inspector URL.
2. Paste your MCP endpoint (e.g. `http://localhost:3000/mcp`) into the connection panel — or skip if `--url` was passed.
3. Click **Connect**. The handshake (`initialize` → `notifications/initialized`) runs; the session ID is captured automatically.
4. Confirm the **Tools**, **Resources**, **Prompts** tabs populate. Empty tabs mean the capability isn't advertised.
5. Open **RPC Messages** and watch the live JSON-RPC traffic.

If the connection fails, the most common causes are:

| Symptom | Cause | Fix |
|---|---|---|
| `Failed to fetch` | Server not running or wrong port | Verify `mcp-use dev` is up on the expected port |
| 404 on connect | URL points at `/` not `/mcp` | Append `/mcp` |
| 403 from CORS | Browser origin not allowed | Add origin to `cors` config or `allowedOrigins` |
| Hangs at "Initializing…" | DNS rebinding protection blocking | See `../20-inspector/` for the rebinding troubleshooting |

---

## Validate-this-server checklist

Use the Inspector to confirm each item before declaring a build done. Every row maps to a tab.

- [ ] **Tools** — every tool name, description, and input schema appears
- [ ] **Tools** — calling each tool returns either expected `text` / `structuredContent` or a meaningful error
- [ ] **Resources** — every URI and MIME type renders; subscriptions work
- [ ] **Prompts** — argument definitions render; preview generated messages
- [ ] **Elicitation** — pending elicitation requests show; forms submit cleanly
- [ ] **Chat (BYOK)** — at least one tool gets called via the LLM
- [ ] **RPC Messages** — no orphan errors during the tour
- [ ] **Notifications** — `list_changed` notifications fire when schemas change

---

## Add to Client (one-click export)

The Inspector header has an **Add to Client** button that exports a config snippet for Cursor, VS Code, Claude Desktop, or a generic CLI. See `05-add-to-client-button.md` for the surface.

---

## Deep cluster

For the full Inspector reference — every tab, the RPC logging surface, the CSP modes, the protocol toggle, command palette, OAuth flow, multi-server connection panel, session persistence — see:

- `../20-inspector/01-overview.md` — entry point
- `../20-inspector/11-protocol-toggle-and-csp-mode.md` — widget protocol + CSP debugging
- the rest of `../20-inspector/` for tab-by-tab detail

**Canonical doc:** [https://docs.mcp-use.com/inspector](https://docs.mcp-use.com/inspector)
