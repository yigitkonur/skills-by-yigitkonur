# CLI Reference

Complete reference for the mcp-use CLI client — connection management, tool execution, resource access, and scripting.

---

## Installation and Setup

Install globally or use via npx — no global install required.

```bash
# Global install
npm install -g mcp-use

# Or run directly with npx (no install needed)
npx mcp-use client --help
```

After installation, the `mcp-use` binary exposes a single top-level subcommand: `client`. All operations — connecting, calling tools, reading resources — live under `client`.

```bash
# Show all available subcommands
npx mcp-use client --help
```

Output:

```
Usage: mcp-use client <command> [options]

Commands:
  connect <url>        Connect to an MCP server
  disconnect [name]    Disconnect from a session
  sessions             Manage sessions
  tools                List, describe, and call tools
  resources            List, read, and subscribe to resources
  prompts              List and get prompts
  interactive          Start interactive mode

Options:
  --session <name>     Use a specific session
  --json               Output results in JSON format
  --timeout <ms>       Request timeout in milliseconds
  --help               Show help
```

---

## Connection Management

Every operation requires an active session. Connect first, then run commands.

### Connect via HTTP

```bash
npx mcp-use client connect http://localhost:3000/mcp --name my-server
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--name <name>` | string | auto-generated | Session name (optional, auto-generated if not provided) |
| `--auth <token>` | string | none | Authentication token for Bearer auth |
| `--stdio` | flag | — | Use stdio connector instead of HTTP |

### Connect via STDIO

Use `--stdio` to launch a child process and communicate over stdin/stdout.

```bash
npx mcp-use client connect --stdio "npx -y @modelcontextprotocol/server-filesystem /tmp" \
  --name fs-server
```

The CLI spawns the command as a child process and establishes an MCP session over stdio transport. The process stays alive for the duration of the session.

### Connect with Authentication

```bash
npx mcp-use client connect https://api.example.com/mcp \
  --name prod-server \
  --auth sk-your-api-key-here
```

The `--auth` flag sets a `Bearer` token in the `Authorization` header for every request in that session.

### Disconnect

```bash
# Disconnect the active session
npx mcp-use client disconnect

# Disconnect a specific session by name
npx mcp-use client disconnect my-server

# Disconnect all sessions at once
npx mcp-use client disconnect --all
```

> ❌ **BAD:** Leaving sessions open after scripting.
>
> ```bash
> npx mcp-use client connect http://localhost:3000/mcp --name temp
> npx mcp-use client tools call get_data '{}'
> # Script exits — session left dangling
> ```

> ✅ **GOOD:** Always disconnect when done.
>
> ```bash
> npx mcp-use client connect http://localhost:3000/mcp --name temp
> npx mcp-use client tools call get_data '{}'
> npx mcp-use client disconnect temp
> ```

---

## Session Management

Sessions persist across CLI invocations. The CLI stores session metadata at `~/.mcp-use/cli-sessions.json`.

### List Sessions

```bash
npx mcp-use client sessions list
```

Output:

```
Saved Sessions:

┌──────────────┬────────┬─────────────────────────────┬────────────────┬──────────────┐
│ Name         │ Type   │ Target                      │ Server         │ Status       │
├──────────────┼────────┼─────────────────────────────┼────────────────┼──────────────┤
│ my-server *  │ http   │ http://localhost:3000/mcp   │ my-mcp-server  │ connected    │
│ fs-server    │ stdio  │ npx -y @mc...filesystem     │ fs-server      │ disconnected │
└──────────────┴────────┴─────────────────────────────┴────────────────┴──────────────┘

* = active session
```

### Switch Active Session

```bash
npx mcp-use client sessions switch fs-server
```

After switching, all commands without `--session` target the new active session.

### Session Storage Structure

The `~/.mcp-use/cli-sessions.json` file contains:

```json
{
  "activeSession": "my-server",
  "sessions": {
    "my-server": {
      "type": "http",
      "url": "http://localhost:3000/mcp",
      "lastUsed": "2025-12-09T10:30:00Z",
      "serverInfo": {
        "name": "my-mcp-server",
        "version": "1.0.0"
      }
    },
    "fs-server": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
      "lastUsed": "2025-12-09T11:00:00Z"
    }
  }
}
```

You can manually edit this file to:

- Change session names
- Update connection details
- Remove old sessions

---

## Tools Commands

Tools are the primary way to invoke server-side actions.

### List Tools

```bash
# List all tools on the active session
npx mcp-use client tools list

# List tools on a specific session
npx mcp-use client tools list --session my-server

# JSON output for programmatic use
npx mcp-use client tools list --json
```

Human-readable output:

```
TOOL NAME        DESCRIPTION
read_file        Read contents of a file at the given path
write_file       Write content to a file at the given path
list_directory   List files and directories at the given path
search_files     Search for files matching a pattern
```

### Describe a Tool

Inspect a tool's input schema before calling it.

```bash
npx mcp-use client tools describe read_file
```

Output:

```
Tool: read_file

Read the contents of a file from the filesystem

Input Schema:
path (string) *required
  The path to the file to read
encoding (string)
  The text encoding to use (default: utf-8)
```

### Call a Tool

Execute a tool with arguments as a JSON string.

```bash
# With JSON arguments
npx mcp-use client tools call read_file '{"path": "/tmp/test.txt"}'

# Without arguments (for tools that don't require them)
npx mcp-use client tools call list_files

# With timeout for slow operations
npx mcp-use client tools call slow_operation '{}' --timeout 60000

# JSON output for scripting
npx mcp-use client tools call read_file '{"path": "/tmp/test.txt"}' --json

# Target a specific session
npx mcp-use client tools call read_file '{"path": "/tmp/test.txt"}' --session fs-server
```

**Tips:**

- Arguments must be valid JSON
- If a tool requires arguments but none are provided, an error will show the schema
- Use single quotes around JSON to avoid shell escaping issues

> ❌ **BAD:** Running tool commands without connecting first.
>
> ```bash
> npx mcp-use client tools call read_file '{"path": "/tmp/test.txt"}'
> # Error: No active session. Run 'mcp-use client connect' first.
> ```

> ✅ **GOOD:** Always connect before running tool, resource, or prompt commands.
>
> ```bash
> npx mcp-use client connect http://localhost:3000/mcp --name my-server
> npx mcp-use client tools call read_file '{"path": "/tmp/test.txt"}'
> ```

### Tool Call JSON Output

When using `--json`, the output follows the MCP `CallToolResult` structure:

```json
{
  "content": [
    {
      "type": "text",
      "text": "File contents here..."
    }
  ],
  "isError": false
}
```

If the tool returns an error:

```json
{
  "content": [
    {
      "type": "text",
      "text": "Error: File not found: /tmp/missing.txt"
    }
  ],
  "isError": true
}
```

---

## Resources Commands

Resources expose server-side data that can be read and observed.

### List Resources

```bash
# Human-readable list
npx mcp-use client resources list

# JSON output
npx mcp-use client resources list --json
```

Output:

```
Available Resources (3):

┌──────────────────────────────┬────────────────┬─────────────┐
│ URI                          │ Name           │ Type        │
├──────────────────────────────┼────────────────┼─────────────┤
│ file:///tmp/data.json        │ Data File      │ text/json   │
│ file:///tmp/config.yaml      │ Config         │ text/yaml   │
│ file:///tmp/image.png        │ Screenshot     │ image/png   │
└──────────────────────────────┴────────────────┴─────────────┘
```

### Read a Resource

```bash
npx mcp-use client resources read "file:///tmp/data.json"
```

Returns the resource content to stdout. Use `--json` to get the full MCP response envelope:

```bash
npx mcp-use client resources read "file:///tmp/data.json" --json
```

```json
{
  "contents": [
    {
      "uri": "file:///tmp/data.json",
      "mimeType": "application/json",
      "text": "{\"key\": \"value\"}"
    }
  ]
}
```

### Subscribe and Unsubscribe

Watch a resource for changes:

```bash
# Start watching for changes
npx mcp-use client resources subscribe "file:///tmp/data.json"

# Stop watching
npx mcp-use client resources unsubscribe "file:///tmp/data.json"
```

When subscribed, the CLI keeps the process running and displays updates as they arrive. Press Ctrl+C to stop.

---

## Prompts Commands

Prompts are server-defined templates that return structured messages.

### List Prompts

```bash
npx mcp-use client prompts list
```

Output:

```
PROMPT NAME       DESCRIPTION                          ARGUMENTS
greeting          Generate a personalized greeting      name (string, required)
daily_summary     Generate a daily summary report       (none)
code_review       Review code for issues                code (string, required), language (string, optional)
```

### Get a Prompt

```bash
# Prompt with arguments
npx mcp-use client prompts get greeting '{"name": "Alice"}'

# Prompt without arguments
npx mcp-use client prompts get daily_summary

# JSON output
npx mcp-use client prompts get greeting '{"name": "Alice"}' --json
```

JSON output returns the full MCP `GetPromptResult`:

```json
{
  "description": "Generate a personalized greeting",
  "messages": [
    {
      "role": "user",
      "content": {
        "type": "text",
        "text": "Hello Alice! Welcome."
      }
    }
  ]
}
```

---

## Interactive Mode

Start a REPL session for ad-hoc exploration.

```bash
npx mcp-use client interactive
```

The interactive shell presents a `mcp>` prompt. Available commands inside interactive mode:

- `tools list` - List available tools
- `tools call <name>` - Call a tool (will prompt for arguments)
- `tools describe <name>` - Show tool details
- `resources list` - List available resources
- `resources read <uri>` - Read a resource
- `prompts list` - List available prompts
- `prompts get <name>` - Get a prompt (will prompt for arguments)
- `sessions list` - List all sessions
- `exit` or `quit` - Exit interactive mode

When calling `tools call`, interactive mode prompts for arguments as a single JSON input:

```
mcp> tools list
Available tools: read_file, write_file, list_directory

mcp> tools call read_file
Arguments (JSON, or press Enter for none): {"path": "/tmp/test.txt"}
✓ Tool executed successfully
...

mcp> resources list
Available resources: file:///tmp/data.json, file:///tmp/config.yaml

mcp> exit
```

Exit with `exit` or `quit`.

---

## Global Flags

All commands support these global flags.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--session <name>` | string | active session | Target a specific named session |
| `--json` | boolean | false | Output results in JSON format |
| `--timeout <ms>` | number | — | Request timeout in milliseconds (for tool calls and resource operations) |

> ❌ **BAD:** Not using `--json` for scripting.
>
> ```bash
> RESULT=$(npx mcp-use client tools call get_data '{}')
> echo "$RESULT" | jq '.content[0].text'
> # Fails — human-readable output is not valid JSON
> ```

> ✅ **GOOD:** Always use `--json` when parsing output programmatically.
>
> ```bash
> RESULT=$(npx mcp-use client tools call get_data '{}' --json)
> echo "$RESULT" | jq '{text: .content[0].text, structuredContent}'
> ```

For scripting, prefer `.content[0].text` as the human-readable fallback but preserve `.structuredContent` when present. Do not assume all successful tools return only text.

---

## Command Reference Table

| Command | Subcommand | Arguments | Key Flags | Description |
|---------|------------|-----------|-----------|-------------|
| `connect` | — | `<url>` | `--name`, `--auth`, `--stdio` | Connect to an MCP server |
| `disconnect` | — | `[name]` | `--all` | Disconnect a session |
| `sessions` | `list` | — | `--json` | List all sessions |
| `sessions` | `switch` | `<name>` | — | Switch active session |
| `tools` | `list` | — | `--session`, `--json` | List available tools |
| `tools` | `describe` | `<tool>` | `--session` | Show tool input schema |
| `tools` | `call` | `<tool> [args]` | `--session`, `--json`, `--timeout` | Call a tool with JSON arguments |
| `resources` | `list` | — | `--session`, `--json` | List available resources |
| `resources` | `read` | `<uri>` | `--session`, `--json` | Read a resource by URI |
| `resources` | `subscribe` | `<uri>` | `--session` | Subscribe to resource changes |
| `resources` | `unsubscribe` | `<uri>` | `--session` | Unsubscribe from resource changes |
| `prompts` | `list` | — | `--session`, `--json` | List available prompts |
| `prompts` | `get` | `<name> [args]` | `--session`, `--json` | Get a prompt with optional arguments |
| `interactive` | — | — | `--session` | Start interactive REPL |

---

## Session Storage Path

Sessions are saved to `~/.mcp-use/cli-sessions.json`. This path is fixed and based on the system home directory. To change the home directory used, set the `HOME` environment variable before running the CLI (Unix/macOS behavior).

```bash
# View the session file
cat ~/.mcp-use/cli-sessions.json
```

---

## Scripting Patterns

### Basic Script — Connect, Call, Disconnect

```bash
#!/bin/bash
set -euo pipefail

SERVER_URL="http://localhost:3000/mcp"
SESSION_NAME="script-session"

# Connect
npx mcp-use client connect "$SERVER_URL" --name "$SESSION_NAME"

# Call tool and capture JSON output
DATA=$(npx mcp-use client tools call get_data '{}' --json --session "$SESSION_NAME")

# Extract specific field with jq
echo "$DATA" | jq -r '.content[0].text'

# Clean up
npx mcp-use client disconnect "$SESSION_NAME"
```

### List All Tool Names

```bash
npx mcp-use client tools list --json | jq -r '.[].name'
```

### Call a Tool and Extract a Specific Field

```bash
npx mcp-use client tools call get_user '{"id": "42"}' --json \
  | jq -r '.content[0].text' \
  | jq '.email'
```

### Loop Through Resources

```bash
#!/bin/bash
set -euo pipefail

npx mcp-use client resources list --json | jq -r '.[].uri' | while read -r uri; do
  echo "--- Reading: $uri ---"
  npx mcp-use client resources read "$uri"
  echo ""
done
```

### Error Handling in Scripts

```bash
#!/bin/bash
set -euo pipefail

SESSION="batch-job"

cleanup() {
  npx mcp-use client disconnect "$SESSION" 2>/dev/null || true
}
trap cleanup EXIT

npx mcp-use client connect http://localhost:3000/mcp --name "$SESSION"

RESULT=$(npx mcp-use client tools call process_data '{"input": "test"}' --json --session "$SESSION")

IS_ERROR=$(echo "$RESULT" | jq -r '.isError // false')
if [ "$IS_ERROR" = "true" ]; then
  echo "Tool returned an error:" >&2
  echo "$RESULT" | jq -r '.content[0].text' >&2
  exit 1
fi

echo "Success:"
echo "$RESULT" | jq -r '.content[0].text'
```

### Multi-Server Script

```bash
#!/bin/bash
set -euo pipefail

# Connect to multiple servers
npx mcp-use client connect http://localhost:3000/mcp --name data-server
npx mcp-use client connect http://localhost:4000/mcp --name ai-server

# Fetch data from one, process on another
RAW=$(npx mcp-use client tools call fetch_records '{}' --json --session data-server)
INPUT=$(echo "$RAW" | jq -r '.content[0].text')

npx mcp-use client tools call analyze "{\"data\": $INPUT}" --json --session ai-server

# Clean up both
npx mcp-use client disconnect --all
```

---

## Troubleshooting

### No Active Session

```
✗ Error: No active session. Connect to a server first.
Use: npx mcp-use client connect <url> --name <name>
```

Run `npx mcp-use client connect <url> --name <name>` before using any tool, resource, or prompt commands.

### Tool Not Found

```
✗ Error: Tool 'invalid_tool' not found

Available tools:
  • read_file
  • write_file
  • list_directory
```

Run `tools list` to see available tools and check spelling.

### Invalid Arguments

```
✗ Error: This tool requires arguments. Provide them as a JSON string.

Example:
  npx mcp-use client tools call read_file '{"path": "/tmp/test.txt"}'

Tool schema:
path (string) *required
  The path to the file to read
```

### Connection Issues

**Problem**: Can't connect to HTTP server

```
✗ Error: Connection failed: fetch failed
```

Check that:
- The server is running
- The URL is correct
- The server supports HTTP/SSE transport
- A firewall isn't blocking the connection

### Stdio Server Issues

**Problem**: Stdio server fails to start

- Ensure the command is available (`npx`, `node`, etc.)
- Check that the server package is installed or accessible
- Verify the arguments are correct

### Session Not Found

**Problem**: Session disappeared after restart

Sessions are stored in `~/.mcp-use/cli-sessions.json`. If the file is deleted, you'll need to reconnect.

### Resetting All State

```bash
# Remove all session data
rm -rf ~/.mcp-use/cli-sessions.json

# Or use disconnect --all
npx mcp-use client disconnect --all
```

---

## Tips and Best Practices

1. **Use Named Sessions** — always provide `--name` when connecting to make sessions easier to manage.
2. **Interactive Mode for Exploration** — use interactive mode when exploring a new server.
3. **JSON Output for Scripts** — use `--json` flag when using the CLI in scripts; never scrape human-readable output.
4. **Session Persistence** — sessions are saved automatically, so you can disconnect and reconnect later.
5. **Multiple Terminals** — you can have multiple terminal windows with different active sessions.

When building agent workflows that use the mcp-use CLI:

1. **Always use `--json`** — parse structured output, never scrape human-readable text.
2. **Always disconnect** — use a `trap` handler in bash scripts to clean up on exit.
3. **Name your sessions** — auto-generated names are hard to reference in multi-step scripts.
4. **Check `isError`** — tool calls can succeed at the transport level but return application errors.
5. **Use `--timeout`** — set generous timeouts for long-running tool calls to avoid premature failures.
6. **Prefer `--session`** — explicitly target sessions rather than relying on the active session.
7. **Describe before calling** — run `tools describe <name>` to discover required arguments before calling.
8. **Use `resources list` for discovery** — enumerate what the server exposes before accessing specific URIs.

> ❌ **BAD:** Guessing tool arguments.
>
> ```bash
> npx mcp-use client tools call read_file '{"file": "/tmp/test.txt"}'
> # Fails — the parameter is "path", not "file"
> ```

> ✅ **GOOD:** Describe the tool first to learn the schema.
>
> ```bash
> npx mcp-use client tools describe read_file
> # Shows: path (string, required)
> npx mcp-use client tools call read_file '{"path": "/tmp/test.txt"}'
> ```

---

## Quick Reference Card

```text
CONNECT     npx mcp-use client connect <url> [--name N] [--auth T] [--stdio]
DISCONNECT  npx mcp-use client disconnect [name] [--all]
SESSIONS    npx mcp-use client sessions list | switch <name>
TOOLS       npx mcp-use client tools list | describe <t> | call <t> [args]
RESOURCES   npx mcp-use client resources list | read <uri> | subscribe <uri> | unsubscribe <uri>
PROMPTS     npx mcp-use client prompts list | get <name> [args]
INTERACTIVE npx mcp-use client interactive
GLOBAL      --session <name>  --json  --timeout <ms>  (--timeout for tool calls and resource ops)
```
