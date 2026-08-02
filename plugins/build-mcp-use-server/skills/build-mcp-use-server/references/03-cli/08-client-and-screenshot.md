# Client and Screenshot

*Read this to test MCP servers from the CLI and capture view screenshots.*

## mcp-use client

Terminal MCP client: connect to any MCP server, list and call tools, read resources, inspect prompts, test interactively.

```bash
mcp-use client [subcommand] [options]
```

### Key subcommands

| Subcommand | Purpose |
|---|---|
| `connect <name> <url>` | Save a server connection |
| `list` | List all saved server connections |
| `remove <name>` | Delete a saved connection |
| `<server> tools list` | List server's tools |
| `<server> tools describe <tool-name>` | Show tool schema |
| `<server> tools call <tool-name> [args]` | Invoke a tool |
| `<server> resources list` | List server's resources |
| `<server> resources read <uri>` | Read a resource |
| `<server> prompts list` | List server's prompts |
| `<server> prompts get <prompt-name>` | Get a prompt template |
| `<server> interactive` | Start interactive REPL |

### Examples

**Save a local server connection:**
```bash
mcp-use client connect my-dev-server http://localhost:3000/mcp
```

**List connections:**
```bash
mcp-use client list
```

**List tools:**
```bash
mcp-use client my-dev-server tools list
```

**Call a tool:**
```bash
mcp-use client my-dev-server tools call weather get_forecast city=Seattle
```

**Interactive REPL:**
```bash
mcp-use client my-dev-server interactive
```

### OAuth handling

When a server requires OAuth, the client prompts for authorization:

```
Server requires authentication.
Authorize at: https://auth.example.com/authorize?...
```

Complete the flow in your browser, then the client resumes.

### Session persistence

Saved connections and active sessions are stored in `~/.mcp-use/cli-sessions.json`.

## mcp-use screenshot

Capture a screenshot of an MCP Apps view (tool with a widget):

```bash
mcp-use screenshot [options]
```

### Flags

| Flag | Type | Effect |
|------|------|--------|
| `--mcp <url>` | string | MCP server URL (for ad-hoc capture) |
| `--tool <name>` | string | Tool name to invoke |
| `--output <path>` | string | Save screenshot to file |
| `--width <px>` | number | Viewport width (default: 1280) |
| `--height <px>` | number | Viewport height (default: 720) |
| `--device-scale-factor <n>` | number | Device pixel ratio (1 or 2) |
| `--theme <theme>` | string | `light` or `dark` |
| `--wait-for <selector>` | string | CSS selector to wait for before capture |
| `--delay <ms>` | number | Delay before capture (ms) |
| `--timeout <ms>` | number | Max wait time (ms) |
| `--cdp-url <url>` | string | Chrome DevTools Protocol URL (for local debugging) |
| `-H <header>` | string | Custom HTTP header (repeatable) |

### Examples

**Capture a tool's widget:**
```bash
mcp-use screenshot \
  --mcp http://localhost:3000/mcp \
  --tool my-chart-tool \
  --output chart.png
```

**Mobile screenshot (dark theme):**
```bash
mcp-use screenshot \
  --mcp https://prod.example.com/mcp \
  --tool dashboard \
  --width 390 \
  --height 844 \
  --theme dark \
  --output mobile-dark.png
```

**With custom headers (authentication):**
```bash
mcp-use screenshot \
  --mcp https://api.example.com/mcp \
  --tool report \
  -H "Authorization: Bearer token123" \
  --output report.png
```

### Output

Screenshots are saved as PNG files. Dimensions match the requested viewport.

## Testing workflow

**1. Start dev server:**
```bash
npm run dev
```

**2. In another terminal, connect client:**
```bash
mcp-use client connect test-local http://localhost:3000/mcp
```

**3. Test tools interactively:**
```bash
mcp-use client test-local interactive
```

**4. Capture views:**
```bash
mcp-use screenshot --mcp http://localhost:3000/mcp --tool my-view --output preview.png
```

This workflow avoids needing a browser for validation testing.
