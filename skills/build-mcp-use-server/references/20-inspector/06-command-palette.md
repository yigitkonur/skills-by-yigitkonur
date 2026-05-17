# Command Palette

Open with `Cmd/Ctrl + K` from anywhere. Fuzzy search across every connected server's tools, prompts, resources, saved requests, plus global navigation, "Open in Client" actions, and doc links.

## Search

The palette searches:

- Tool names + descriptions
- Prompt names + descriptions
- Resource names + URIs
- Saved request names
- Server names
- Global commands

Matching is fuzzy: matches beginning-of-word, partial, and description metadata.

| Query | Matches |
|---|---|
| `lin iss` | "Linear Create Issue" |
| `get` | `get_user`, `get_project`, … |
| Partial description | Descriptions are searched alongside names |

## Result categories

Results group by category. Each category has its own icon.

| Category | Items | Display |
|---|---|---|
| Navigation | "Connect Server" and similar global actions | Plus icon |
| Open in Client | "Open in Cursor", "Open in Claude Code", "Open in Claude Desktop", "Open in VS Code", "Open in Gemini CLI", "Open in Codex CLI" | Client icon |
| Connected Servers | Each connected server | Server icon, status indicator, URL |
| Tools | All tools, grouped by server | Wrench icon, server badge |
| Prompts | All prompts, grouped by server | Message icon, server badge |
| Resources | All resources, grouped by server | File icon, server badge |
| Saved Requests | Persisted tool calls | Clock icon, tool name + server badge |
| Documentation | "MCP Use Website", "How to Create an MCP Server", "MCP Official Documentation" | Link icon |
| Community | "Join Discord Community" | Discord icon |

## Actions

### Connect Server

Navigate to dashboard for new connection. Use to start a session.

### Execute a tool

1. `Cmd/Ctrl + K`
2. Type tool name
3. `Enter` — Inspector navigates to Tools tab with the tool selected
4. Fill arguments and execute

### Open a saved request

1. `Cmd/Ctrl + K`
2. Type the saved request name
3. Pick from **Saved Requests** category
4. Tools tab opens with arguments pre-filled

### Switch server

1. `Cmd/Ctrl + K`
2. Type server name or URL
3. Pick from **Connected Servers**
4. Detail view opens for that server

### Add to Client

The "Open in Client" entries hand the current MCP server config to a client.

| Client | Mechanism |
|---|---|
| Cursor | Deep link → opens MCP install dialog |
| VS Code | Deep link → opens MCP install dialog |
| Claude Desktop | Downloads `.mcpb` config file |
| Claude Code | Copies CLI command to clipboard |
| Gemini CLI | Copies CLI command to clipboard |
| Codex CLI | Copies CLI command to clipboard |

Same actions are available from the **Add to Client** dropdown in the header.

## Keyboard navigation

| Key | Action |
|---|---|
| `↑` / `↓` | Move selection |
| `Enter` | Select highlighted item |
| `Esc` | Close palette |

## Multi-server search

When more than one server is connected:

- Tools, prompts, and resources are grouped by server.
- A server-name badge appears on each item.
- You can filter by typing the server name.

## Tips

- `Cmd/Ctrl+K` works inside input fields — it is the one shortcut that ignores input focus, so you can always reach it.
- For regular tool replay, prefer **Saved Requests** over re-typing arguments.
- Use the palette as a switchboard: open it, type the next thing you want, `Enter`, repeat.
