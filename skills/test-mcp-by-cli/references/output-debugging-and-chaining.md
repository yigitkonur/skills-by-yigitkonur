# Output, Debugging, and Chaining

Grounded in the installed `philschmid/mcp-cli v0.3.0` binary. Prefer these observed behaviors over repo-source internals when they disagree.

## Output model

`mcp-cli call` writes the raw MCP JSON envelope to stdout.

What the server returns (MCP protocol):
```json
{
  "content": [
    { "type": "text", "text": "the actual result" }
  ]
}
```

What `call` outputs to stdout:
```json
{
  "content": [
    { "type": "text", "text": "the actual result" }
  ]
}
```

- Parse the envelope yourself with `jq`
- Errors still go to stderr
- Errors: always to stderr

```bash
# Extract text content
mcp-cli call my-server my-tool '{"param": "value"}' | jq -r '.content[0].text'

# Parse JSON within text output
mcp-cli call my-server my-tool '{"param": "value"}' | jq -r '.content[0].text' | jq '.some_field'
```

## Streams

| Stream | Contains |
|---|---|
| stdout | Raw MCP JSON from `call`, or human-readable text from `info`/`grep`/list |
| stderr | Errors, server startup logs, debug output |

```bash
# stdout only (suppress server noise)
mcp-cli call server tool '{}' 2>/dev/null

# stderr only (see server logs)
mcp-cli call server tool '{}' 2>&1 >/dev/null

# With descriptions
mcp-cli -d
mcp-cli info my-server -d
```

## Searching across servers

```bash
mcp-cli grep "*file*"        # find all file-related tools
mcp-cli grep "*search*" -d   # with descriptions
```

Pattern matches tool names only (not server names or descriptions). Glob: `*` (any chars), `?` (single char), case-insensitive.

## Chaining calls

```bash
# Output of one tool feeds another
mcp-cli call filesystem search_files '{"path": "src/", "pattern": "*.ts"}' 2>/dev/null \
  | head -1 \
  | xargs -I {} mcp-cli call filesystem read_file "{\"path\": \"{}\"}" 2>/dev/null

# Conditional proceed
mcp-cli call filesystem list_directory '{"path": "."}' 2>/dev/null \
  | grep -q "config.json" \
  && mcp-cli call filesystem read_file '{"path": "./config.json"}' 2>/dev/null

# Error handling in shell
if result=$(mcp-cli call server tool '{"param": "value"}' 2>/dev/null); then
  echo "$result"
else
  exit_code=$?
  case $exit_code in
    1) echo "Client error — bad arguments or config" ;;
    2) echo "Server error — tool execution failed" ;;
    3) echo "Network error — connection failed" ;;
    4) echo "Auth error — credentials rejected" ;;
    *) echo "Unknown error (exit $exit_code)" ;;
  esac
fi
```

## jq tips

| Pattern | What it does |
|---|---|
| `jq -r '...'` | Raw output — no quotes around strings |
| `jq -e '...'` | Exit code 1 if result is false/null (for conditionals) |
| `jq -s '.'` | Slurp — combine multiple JSON inputs into array |
| `jq 'select(.field == "value")'` | Filter objects |
| `jq -r '.content[0].text'` | Extract first text content item from `call` output |

---

## Environment variables (verified for the installed release)

| Variable | Default | Description |
|---|---|---|
| `MCP_NO_DAEMON=1` | unset (daemon on) | Disable daemon, force fresh connections |
| `MCP_DAEMON_TIMEOUT=N` | `60` (seconds) | Daemon idle timeout before auto-shutdown |
| `MCP_DEBUG=1` | unset (off) | Full protocol traffic to stderr |
| `MCP_TIMEOUT=N` | `1800` (30 min, in seconds) | Total timeout budget for operation |
| `MCP_STRICT_ENV` | `true` | Error on missing `${VAR}` in config (`false` = warn) |
| `MCP_CONFIG_PATH` | unset | Config file path override |

Do not document or depend on undocumented flags or env vars without checking the installed binary first. This release exposes some inconsistencies between `--help`, error suggestions, and repo source.

### Recommended combinations

After rebuilding a server:
```bash
MCP_NO_DAEMON=1 mcp-cli call my-server my-tool '{"param": "value"}'
```

Debugging a connection failure:
```bash
MCP_DEBUG=1 MCP_NO_DAEMON=1 MCP_TIMEOUT=30 mcp-cli info my-server
```

Fast-failing CI pipeline:
```bash
MCP_NO_DAEMON=1 MCP_TIMEOUT=30 mcp-cli call my-server my-tool '{}' >/dev/null
```

Scripted output processing:
```bash
mcp-cli call my-server my-tool '{"param": "value"}' 2>/dev/null | jq -r '.content[0].text'
```

---

## CI/CD verification pattern

```bash
#!/bin/bash
set -euo pipefail

CONFIG_PATH="./test/mcp_servers.json"
SERVER="my-server"

echo "=== MCP Server Verification ==="

# Phase 1: Connection
echo -n "Connect... "
if MCP_NO_DAEMON=1 MCP_TIMEOUT=30 mcp-cli info "$SERVER" -c "$CONFIG_PATH" >/dev/null 2>&1; then
  echo "OK"
else
  echo "FAILED (exit $?)"
  exit 1
fi

# Phase 2: Happy path
echo -n "Call... "
if MCP_NO_DAEMON=1 MCP_TIMEOUT=30 mcp-cli call "$SERVER" my-tool '{"param": "value"}' -c "$CONFIG_PATH" 2>/dev/null >/dev/null; then
  echo "OK"
else
  echo "FAILED (exit $?)"
  exit 1
fi

# Phase 3: Error handling
echo -n "Error handling... "
if MCP_NO_DAEMON=1 MCP_TIMEOUT=30 mcp-cli call "$SERVER" my-tool '{}' -c "$CONFIG_PATH" >/dev/null 2>&1; then
  echo "WARN (empty args accepted)"
else
  code=$?
  if [ $code -eq 2 ]; then
    echo "OK (server returned error)"
  else
    echo "FAILED (exit $code)"
    exit 1
  fi
fi

echo "=== All checks passed ==="
```

## Repository-local command mode

When validating this repository's own source code:

```bash
bun run src/index.ts -c ./mcp_servers.json info filesystem
bun run src/index.ts -c ./mcp_servers.json call filesystem read_file '{"path":"./README.md"}'
```
