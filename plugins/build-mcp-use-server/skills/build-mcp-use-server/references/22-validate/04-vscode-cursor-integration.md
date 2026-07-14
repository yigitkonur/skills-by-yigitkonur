# VS Code & Cursor Integration

VS Code (with GitHub Copilot Chat) and Cursor both consume MCP servers via JSON config files. The shape is similar to Claude Desktop but the path differs.

---

## VS Code

VS Code stores MCP server config either at user scope or workspace scope.

| Scope | Path | When to use |
|---|---|---|
| User (global) | `~/Library/Application Support/Code/User/mcp.json` (macOS) | Servers used across all projects |
| Workspace | `.vscode/mcp.json` (committed) | Project-specific servers; teammates pick up automatically |

### HTTP server (mcp-use default)

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

### stdio server

```json
{
  "servers": {
    "my-stdio-server": {
      "type": "stdio",
      "command": "/usr/local/bin/node",
      "args": ["/abs/path/to/server.js"],
      "env": { "API_KEY": "${input:apiKey}" }
    }
  },
  "inputs": [
    { "id": "apiKey", "type": "promptString", "password": true, "description": "API key" }
  ]
}
```

`${input:foo}` placeholders pull from the `inputs` array — VS Code prompts the user once and caches the value securely.

### Reload

VS Code picks up `mcp.json` changes via **Command Palette → "MCP: Restart Server"** without restarting the editor. For new servers, run **"MCP: List Servers"** and start them.

---

## Cursor

Cursor stores MCP config in a project-local file or globally.

| Scope | Path |
|---|---|
| Project | `.cursor/mcp.json` |
| Global | `~/.cursor/mcp.json` |

### HTTP server

```json
{
  "mcpServers": {
    "my-server": {
      "url": "http://localhost:3000/mcp"
    }
  }
}
```

### stdio server

```json
{
  "mcpServers": {
    "my-stdio-server": {
      "command": "/usr/local/bin/node",
      "args": ["/abs/path/to/server.js"],
      "env": { "API_KEY": "sk-..." }
    }
  }
}
```

### Reload

Cursor watches `mcp.json` and reconnects automatically. If a connection sticks, toggle the server off/on in **Cursor Settings → MCP**.

---

## Key differences vs Claude Desktop

| Surface | Claude Desktop | VS Code | Cursor |
|---|---|---|---|
| Top-level key | `mcpServers` | `servers` | `mcpServers` |
| HTTP server | `{ "url": "..." }` | `{ "type": "http", "url": "..." }` | `{ "url": "..." }` |
| Reload | Cmd+Q + reopen | "MCP: Restart Server" command | Auto-reload |
| Workspace config | None | `.vscode/mcp.json` | `.cursor/mcp.json` |
| Secret prompts | Inline `env` | `${input:...}` + `inputs` array | Inline `env` |

---

## Verifying the connection

### VS Code

1. Open Copilot Chat.
2. Type `#` to mention a tool — your server's tools should autocomplete.
3. Logs: **Output panel → "MCP" channel**.

### Cursor

1. Open Cursor's chat sidebar.
2. **Settings → MCP** — server should show a green dot.
3. Try referencing a tool by name in chat.

---

## Common issues

| Symptom | Cause | Fix |
|---|---|---|
| Tools missing in VS Code | Wrong top-level key (`mcpServers` instead of `servers`) | Use `servers` for VS Code |
| `inputs` placeholder not resolved | VS Code-only feature; Cursor doesn't support it | Embed env directly in Cursor |
| Cursor shows red dot | Server not running or wrong URL | Start `mcp-use dev`; verify URL ends in `/mcp` |
| HTTP works in Inspector, fails in editor | CORS — editor origin blocked | Add the editor origin to `cors` config |

---

## Auto-config via Inspector

Easiest path: connect your server in the Inspector, click **Add to Client**, pick **Cursor** or **VS Code**. The Inspector copies the correct snippet to your clipboard. See `05-add-to-client-button.md`.
