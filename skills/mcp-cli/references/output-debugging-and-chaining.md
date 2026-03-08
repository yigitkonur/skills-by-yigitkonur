# Reading Output, Streams, and Chaining

## Output model for this project

In this repository's current implementation, `mcp-cli call` prints extracted text content from MCP tool results to stdout.

- If text content exists, output is raw text.
- If no text content exists, output falls back to JSON.
- Use `jq` when output text itself is JSON.

```bash
mcp-cli call my-server my-tool '{"param":"value"}'
mcp-cli call my-server my-tool '{"param":"value"}' | jq '.some_field'
```

> Note: Some external docs/tools may assume wrapped MCP envelope output. Validate behavior against the actual CLI version you are running.

## Streams

- `stdout`: command result
- `stderr`: errors + startup noise

```bash
# stdout only
mcp-cli call server tool '{}' 2>/dev/null

# stderr only
mcp-cli call server tool '{}' 2>&1 >/dev/null

# with descriptions
mcp-cli -d
mcp-cli info my-server -d
```

## Search across servers

```bash
mcp-cli grep "*file*"
mcp-cli grep "*search*" -d
```

## Chaining calls

```bash
# Output of one tool feeds another
mcp-cli call filesystem search_files '{"path":"src/","pattern":"*.ts"}' \
  | head -1 \
  | xargs -I {} mcp-cli call filesystem read_file '{"path":"{}"}'

# Conditional proceed
mcp-cli call filesystem list_directory '{"path":"."}' \
  | grep -q "config.json" \
  && mcp-cli call filesystem read_file '{"path":"./config.json"}'

# Error handling in shell
if result=$(mcp-cli call server tool '{"param":"value"}' 2>/dev/null); then
  echo "$result"
else
  echo "Call failed"
fi
```

## Useful environment variables

```bash
MCP_NO_DAEMON=1   # bypass daemon cache
MCP_DEBUG=1       # full debug/protocol traffic
MCP_TIMEOUT=30    # faster hang detection
MCP_STRICT_ENV=true
```

## Repository-local command mode

When validating this repository source, run:

```bash
bun run src/index.ts -c ./mcp_servers.json info filesystem
bun run src/index.ts -c ./mcp_servers.json call filesystem read_file '{"path":"./README.md"}'
```
