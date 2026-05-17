# Add to Client Button

The Inspector's **Add to Client** button is the fastest way to register a connected server with Cursor, VS Code, Claude Desktop, or a generic CLI. It generates the correct JSON snippet for each client and either copies it to your clipboard or writes it directly to the client's config file.

---

## Where the button lives

In the Inspector header (right side, next to the connection panel), there's an **Add to Client** dropdown. It is enabled only after a successful connection — the button needs to know your server's URL, transport, and capabilities to build the snippet.

---

## Supported clients

| Client | Action | Notes |
|---|---|---|
| **Claude Desktop** | Writes to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS path equivalents on Win/Linux) | Server appears under `mcpServers.<name>` |
| **Cursor** | Writes to `~/.cursor/mcp.json` (or copies snippet for `.cursor/mcp.json`) | Same `mcpServers` shape as Claude Desktop |
| **VS Code** | Generates snippet for `~/Library/Application Support/Code/User/mcp.json` or `.vscode/mcp.json` | Uses VS Code's `servers` shape with `type: "http"` |
| **Generic CLI** | Copies a JSON snippet to clipboard | For any client that takes Claude-Desktop-shaped config |

---

## Flow

1. Connect the Inspector to your server (`http://localhost:3000/mcp` or a tunnel URL).
2. Open the **Add to Client** menu.
3. Pick a client.
4. Confirm or edit the **server name** (defaults to your server's `serverInfo.name`).
5. Inspector either writes the config or shows a snippet to copy.
6. Restart the client (Claude Desktop needs a full Cmd+Q; VS Code uses "MCP: Restart Server"; Cursor reloads automatically).

---

## What the snippets look like

**Claude Desktop / Cursor:**

```json
{
  "mcpServers": {
    "my-server": {
      "url": "http://localhost:3000/mcp"
    }
  }
}
```

**VS Code:**

```json
{
  "servers": {
    "my-server": {
      "type": "http",
      "url": "http://localhost:3000/mcp"
    }
  }
}
```

If the connected URL is a tunnel (e.g. `https://happy-blue-cat.local.mcp-use.run/mcp`), Inspector substitutes that URL — useful for sharing a dev server with teammates by handing them the JSON snippet.

---

## When direct-write fails

The hosted Inspector at `https://inspector.mcp-use.com` cannot write to your local filesystem — it only offers the **Copy snippet** action. The local Inspector (`npx @mcp-use/inspector`) and the built-in dev Inspector (`http://localhost:3000/inspector`) can write files directly.

| Inspector flavor | Can write client config? |
|---|---|
| `https://inspector.mcp-use.com` (hosted) | No — copy snippet only |
| `npx @mcp-use/inspector` (local CLI) | Yes |
| `http://localhost:3000/inspector` (built-in dev) | Yes |

---

## Verifying after Add to Client

After clicking, the workflow is:

1. **Claude Desktop:** Cmd+Q, reopen, hammer icon → tool list.
2. **Cursor:** Auto-reloads — check **Settings → MCP** for the green dot.
3. **VS Code:** Run **"MCP: Restart Server"** from the command palette, then try referencing a tool with `#`.

If the tool list is empty after restart, fall back to manually inspecting the written config — see `03-claude-desktop-integration.md` and `04-vscode-cursor-integration.md` for the per-client paths.

---

## Edits afterward

Add to Client overwrites only its own server entry. Other servers in the same config file are preserved. If you rename a server in the Inspector and re-click Add to Client, the old entry stays — manually remove the stale one or let the client surface it as "unreachable".
