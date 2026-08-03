# Client and Screenshot

*Read this to test MCP servers from the CLI and capture view screenshots.*

## mcp-use client

Terminal MCP client: connect to any MCP server, list and call tools, read resources, inspect prompts, test interactively.

```bash
mcp-use client [subcommand] [options]
```

There is no `interactive` subcommand — every invocation targets one saved server and one command family; there is no persistent REPL mode.

### Key subcommands

| Subcommand | Purpose |
|---|---|
| `connect <name> <url>` | Connect to and save an HTTP(S) server. Options: `-H/--header <"Key: Value">` (repeatable), `--no-oauth`, `--auth-timeout <ms>` (default 300000), `--protocol <auto\|legacy\|modern>` (default auto), `--no-open`, `--json`, `-h/--help` |
| `list` | List saved servers. Options: `--json`, `-h/--help` |
| `remove <name>` | Immediately remove a saved server and its credentials — no confirmation prompt, no `--yes` flag. Options: `--json`, `-h/--help` |
| `<server> tools list` | List server's tools. Options: `--json`, `-h/--help` |
| `<server> tools describe <tool-name>` | Show a tool definition. Options: `--json`, `-h/--help` |
| `<server> tools call <tool-name> [args...]` | Invoke a tool. Options: `--timeout <ms>` (default 30000), `--json`, `-h/--help` |
| `<server> resources list` | List server's resources. Options: `--json`, `-h/--help` |
| `<server> resources read <uri>` | Read a resource. Options: `--json`, `-h/--help` |
| `<server> prompts list` | List server's prompts. Options: `--json`, `-h/--help` |
| `<server> prompts get <prompt-name> [args...]` | Get a prompt template. Options: `--json`, `-h/--help` |
| `<server> auth status` | Show saved OAuth status. Options: `--json`, `-h/--help` |
| `<server> auth logout` | Delete saved OAuth credentials but keep the server. Options: `--yes` (skip confirmation), `--json`, `-h/--help` |

`tools call` and `prompts get` arguments are either one JSON object or `key=value`/`key:=<json>` pairs — do not mix forms.

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
mcp-use client my-dev-server tools call get_forecast city=Seattle
```

**Check and clear saved OAuth state:**
```bash
mcp-use client my-dev-server auth status
mcp-use client my-dev-server auth logout --yes
```

### OAuth handling

When `connect` hits an authorization challenge in an interactive TTY, the client prompts before opening a browser:

```
This server requires OAuth. Press Enter to open your browser.
```

In `--json` mode, with `--no-open`, or in a non-TTY session, it never opens a browser or prints an interactive prompt — non-interactive attempts instead surface an `oauth_interaction_required` error with an interactive retry command; `--no-open` alone (interactive TTY) prints the authorization URL to stderr (`Open this URL to authenticate:\n<url>`) without launching a browser.

### Session persistence

- Saved server list: `~/.mcp-use/client/servers.json`
- Per-server OAuth/session credentials: `~/.mcp-use/client/credentials/<sha256-of-server-name>/credentials.json`
- Per-server OAuth token cache: `~/.mcp-use/client/credentials/<sha256-of-server-name>/oauth/`

## mcp-use screenshot

Call a view-backed MCP tool and capture its rendered MCP App as PNG:

```bash
mcp-use screenshot (--server <name> | --mcp <url>) --tool <name> [args...] [options]
```

Exactly one of `--server`/`--mcp` is required.

### Flags

| Flag | Type | Effect |
|------|------|--------|
| `--server <name>` | string | Use a server saved by `mcp-use client connect` |
| `--mcp <url>` | string | Connect directly to an HTTP(S) MCP endpoint |
| `-H, --header <"Key: Value">` | string | Header for `--mcp`; repeatable — throws if combined with `--server` |
| `--tool <name>` | string | View-backed tool to call (required) |
| `--output <path>` | string | Output PNG path (default: timestamped view name) |
| `--width <px>` | number | Host/widget width (default: **768**, matching an OpenAI inline MCP App container) |
| `--height <px>` | number | Host viewport height used for responsive layout (default: 720); PNG is cropped to widget bounds |
| `--device-scale-factor <n>` | number | Pixel density, greater than 0 and at most 4 (default: 1) |
| `--theme <light\|dark>` | string | Host theme (default: light) |
| `--wait-for <selector>` | string | CSS selector to wait for before capture |
| `--delay <ms>` | number | Additional delay after readiness (default: 0) |
| `--timeout <ms>` | number | Tool/browser timeout (default: 30000) |
| `--inspector <url>` | string | Use an existing Inspector origin instead of auto-launching a packaged one |
| `--cdp-url <url>` | string | Use an existing Chrome DevTools Protocol endpoint instead of auto-launching local Chrome |
| `--json` | boolean | Emit one result or error; never prompt |
| `-h, --help` | boolean | Show this help |

Tool arguments are one JSON object or `key=value`/`key:=<json>` pairs after the options.

### Examples

**Capture a saved server's tool widget:**
```bash
mcp-use screenshot --server demo --tool show-app appName=Demo
```

**Ad-hoc capture with a JSON argument object:**
```bash
mcp-use screenshot --mcp https://example.com/mcp --tool show-app \
  '{"appName":"CI"}' --theme dark --output app.png --json
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

**With custom headers (authentication, `--mcp` only):**
```bash
mcp-use screenshot \
  --mcp https://api.example.com/mcp \
  --tool report \
  -H "Authorization: Bearer token123" \
  --output report.png
```

### Output

Screenshots are saved as PNG files. The PNG is cropped to the widget's bounds within the `--width`/`--height` host viewport.

### Exit codes

- `0` — Capture succeeded or help
- `2` — Invalid arguments
- `1` — MCP, tool, Inspector, browser, readiness, or write failure

## Testing workflow

**1. Start dev server:**
```bash
npm run dev
```

**2. In another terminal, connect client:**
```bash
mcp-use client connect test-local http://localhost:3000/mcp
```

**3. List and call tools:**
```bash
mcp-use client test-local tools list
mcp-use client test-local tools call my-tool arg=value
```

**4. Capture views:**
```bash
mcp-use screenshot --server test-local --tool my-view --output preview.png
```

This workflow avoids needing a browser for validation testing.
