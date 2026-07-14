# Claude Desktop Integration

Claude Desktop reads MCP server config from a JSON file. After editing, fully quit (Cmd+Q) and reopen Claude — config is read on startup, not hot-reloaded.

---

## Config paths by OS

| OS | Path |
|---|---|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Linux | `~/.config/Claude/claude_desktop_config.json` |

If the file doesn't exist, create it with `{"mcpServers": {}}`.

---

## HTTP server config (mcp-use default)

mcp-use servers run over Streamable HTTP on `/mcp`. Claude Desktop connects by URL.

```json
{
  "mcpServers": {
    "my-server": {
      "url": "http://localhost:3000/mcp"
    }
  }
}
```

Production servers swap the URL for an HTTPS endpoint:

```json
{
  "mcpServers": {
    "production": {
      "url": "https://mcp.example.com/mcp"
    }
  }
}
```

---

## stdio server config (rare for mcp-use)

If you've explicitly built a stdio server, Claude Desktop spawns it as a subprocess. Use absolute paths — Claude does not inherit your shell's `PATH` or env.

```json
{
  "mcpServers": {
    "my-stdio-server": {
      "command": "/usr/local/bin/node",
      "args": ["/Users/me/projects/my-server/dist/server.js"],
      "env": {
        "API_KEY": "sk-...",
        "DEBUG": "1"
      }
    }
  }
}
```

| Key | Purpose |
|---|---|
| `command` | Absolute path to the binary (`node`, `python`, `/path/to/myserver`) |
| `args` | CLI args passed to the binary |
| `env` | Environment variables; vars from your shell profile are NOT inherited |
| `cwd` | Optional working directory |

---

## Verifying the config loaded

1. Quit Claude completely (Cmd+Q on macOS — closing the window doesn't quit).
2. Reopen.
3. Click the hammer icon (or the slash menu) — your tools should appear listed under the server name.
4. Try calling a tool to confirm round-trip.

---

## Reading Claude Desktop logs

```bash
# Tail live (macOS)
tail -f ~/Library/Logs/Claude/mcp*.log

# Search for errors
grep -i "error\|fail\|crash" ~/Library/Logs/Claude/mcp*.log

# Per-server log
ls ~/Library/Logs/Claude/mcp-server-*.log
```

Each MCP server gets its own log file: `mcp-server-<name>.log`. Server stdout/stderr lands here.

---

## Common Claude Desktop issues

| Issue | Cause | Fix |
|---|---|---|
| Tools don't appear | Invalid JSON | `cat ~/Library/Application\ Support/Claude/claude_desktop_config.json \| jq` to validate |
| Tools don't appear | Config file edited but Claude not restarted | Cmd+Q (not just close window) and reopen |
| Server keeps restarting | Stdio binary crashes on startup | `tail -f mcp-server-*.log` for stack trace |
| `command not found` | Relative path or bare binary name | Use absolute path; `which node` to find it |
| Env vars missing | Shell profile not inherited by GUI apps | Embed in `env` block of config |
| HTTP server: 404 on tool call | URL missing `/mcp` suffix | Use `http://localhost:3000/mcp`, not `http://localhost:3000` |
| HTTP server: connection refused | Server not running | Start with `mcp-use start` or `mcp-use dev` |

---

## Multiple servers

You can register many MCP servers under `mcpServers` — each gets its own connection and namespace.

```json
{
  "mcpServers": {
    "local-dev": { "url": "http://localhost:3000/mcp" },
    "staging":   { "url": "https://mcp-staging.example.com/mcp" },
    "production": { "url": "https://mcp.example.com/mcp" }
  }
}
```

---

## OAuth flows

If your server requires OAuth, Claude Desktop pops up a browser window on first connection. The redirect URI must be reachable; for local dev, expose your callback via the tunnel — see `02-setup/` for OAuth setup.

---

## Add to Client (auto-config)

The Inspector's **Add to Client** button writes Claude Desktop config for you in one click. See `05-add-to-client-button.md`.
