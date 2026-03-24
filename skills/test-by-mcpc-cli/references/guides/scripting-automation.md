# Scripting and Automation

Write automated test scripts for MCP servers using mcpc's JSON mode and exit codes.

## JSON mode

All mcpc commands support `--json` for machine-readable output. Always use `--json` in scripts — never parse human-readable colored output.

```bash
# Enable per-command
mcpc @session tools-list --json

# Enable globally via environment variable
export MCPC_JSON=1
mcpc @session tools-list   # Outputs JSON without --json flag
```

### JSON output structure

Tool list:
```json
[
  {
    "name": "tool-name",
    "description": "What this tool does",
    "inputSchema": { ... }
  }
]
```

Tool call result:
```json
{
  "content": [
    { "type": "text", "text": "result text" }
  ],
  "isError": false
}
```

Resource list:
```json
[
  {
    "uri": "file:///path",
    "name": "Resource Name",
    "mimeType": "text/plain"
  }
]
```

## Exit codes

| Code | Constant | Meaning | Script action |
|---|---|---|---|
| 0 | Success | Command completed | Continue |
| 1 | ClientError | Invalid args, unknown command | Fix command syntax |
| 2 | ServerError | Tool execution failed, resource not found | Check server logs |
| 3 | NetworkError | Connection failed, timeout, DNS | Check connectivity |
| 4 | AuthError | Invalid credentials, 401/403, token expired | Re-authenticate |

```bash
mcpc @session tools-call my-tool arg:=value --json
EXIT_CODE=$?

case $EXIT_CODE in
  0) echo "Success" ;;
  1) echo "Client error: bad arguments" ;;
  2) echo "Server error: tool failed" ;;
  3) echo "Network error: cannot reach server" ;;
  4) echo "Auth error: re-authenticate" ;;
esac
```

## Complete test script template

```bash
#!/bin/bash
set -euo pipefail

# Configuration
SERVER="${1:?Usage: $0 <server-url-or-config:entry>}"
SESSION="test-$$-$(date +%s)"
TIMEOUT="${2:-300}"
FAILURES=0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { echo -e "${GREEN}  ✓ $1${NC}"; }
fail() { echo -e "${RED}  ✗ $1${NC}"; FAILURES=$((FAILURES + 1)); }
warn() { echo -e "${YELLOW}  ⚠ $1${NC}"; }
info() { echo "  $1"; }

# Cleanup on exit
cleanup() {
  mcpc "@$SESSION" close 2>/dev/null || true
}
trap cleanup EXIT

echo "=== MCP Server Test Suite ==="
echo "Server: $SERVER"
echo "Session: @$SESSION"
echo "Timeout: ${TIMEOUT}s"
echo ""

# === Phase 1: Connection ===
echo "Phase 1: Connection"
if mcpc "$SERVER" connect "@$SESSION" --timeout "$TIMEOUT" 2>/dev/null; then
  pass "Connected to server"
else
  fail "Failed to connect"
  exit 1
fi

# === Phase 2: Health Check ===
echo "Phase 2: Health Check"
if mcpc "@$SESSION" ping 2>/dev/null; then
  pass "Server responds to ping"
else
  fail "Ping failed"
fi

# Server info
SERVER_INFO=$(mcpc "@$SESSION" help --json 2>/dev/null || echo '{}')
SERVER_NAME=$(echo "$SERVER_INFO" | jq -r '.serverInfo.name // "unknown"')
SERVER_VERSION=$(echo "$SERVER_INFO" | jq -r '.serverInfo.version // "unknown"')
PROTOCOL=$(echo "$SERVER_INFO" | jq -r '.protocolVersion // "unknown"')
info "Server: $SERVER_NAME v$SERVER_VERSION (protocol: $PROTOCOL)"

# === Phase 3: Tool Discovery ===
echo "Phase 3: Tool Discovery"
TOOLS=$(mcpc "@$SESSION" tools-list --json 2>/dev/null || echo '[]')
TOOL_COUNT=$(echo "$TOOLS" | jq 'length')

if [ "$TOOL_COUNT" -gt 0 ]; then
  pass "Found $TOOL_COUNT tool(s)"
  echo "$TOOLS" | jq -r '.[].name' | while read -r tool; do
    info "  - $tool"
  done
else
  warn "No tools found"
fi

# Verify each tool has a schema
for tool in $(echo "$TOOLS" | jq -r '.[].name'); do
  SCHEMA=$(mcpc "@$SESSION" tools-get "$tool" --json 2>/dev/null || echo '{}')
  HAS_SCHEMA=$(echo "$SCHEMA" | jq 'has("inputSchema")')
  HAS_DESC=$(echo "$SCHEMA" | jq '.description != null')

  if [ "$HAS_SCHEMA" = "true" ]; then
    pass "Tool '$tool' has input schema"
  else
    fail "Tool '$tool' missing input schema"
  fi

  if [ "$HAS_DESC" = "true" ]; then
    pass "Tool '$tool' has description"
  else
    warn "Tool '$tool' missing description"
  fi
done

# === Phase 4: Resource Discovery ===
echo "Phase 4: Resource Discovery"
RESOURCES=$(mcpc "@$SESSION" resources-list --json 2>/dev/null || echo '[]')
RESOURCE_COUNT=$(echo "$RESOURCES" | jq 'length')

if [ "$RESOURCE_COUNT" -gt 0 ]; then
  pass "Found $RESOURCE_COUNT resource(s)"
  echo "$RESOURCES" | jq -r '.[].uri' | head -5 | while read -r uri; do
    info "  - $uri"
  done
else
  info "No resources (this is fine for tool-only servers)"
fi

# === Phase 5: Prompt Discovery ===
echo "Phase 5: Prompt Discovery"
PROMPTS=$(mcpc "@$SESSION" prompts-list --json 2>/dev/null || echo '[]')
PROMPT_COUNT=$(echo "$PROMPTS" | jq 'length')

if [ "$PROMPT_COUNT" -gt 0 ]; then
  pass "Found $PROMPT_COUNT prompt(s)"
else
  info "No prompts (this is fine)"
fi

# === Summary ===
echo ""
echo "=== Summary ==="
echo "Server: $SERVER_NAME v$SERVER_VERSION"
echo "Protocol: $PROTOCOL"
echo "Tools: $TOOL_COUNT | Resources: $RESOURCE_COUNT | Prompts: $PROMPT_COUNT"

if [ "$FAILURES" -eq 0 ]; then
  echo -e "${GREEN}All tests passed!${NC}"
  exit 0
else
  echo -e "${RED}$FAILURES test(s) failed${NC}"
  exit 1
fi
```

### Using the test script

```bash
# Save as test-mcp.sh and make executable
chmod +x test-mcp.sh

# Test a remote HTTP server
./test-mcp.sh https://mcp.example.com

# Test a stdio server from config
./test-mcp.sh ~/.vscode/mcp.json:my-server

# Test with custom timeout
./test-mcp.sh https://slow-server.com 600
```

## CI integration

### GitHub Actions example

```yaml
name: MCP Server Tests
on: [push, pull_request]

jobs:
  test-mcp:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install mcpc
        run: npm install -g @apify/mcpc

      - name: Start MCP server
        run: |
          npm run build
          npm run start &
          sleep 5  # Wait for server to start

      - name: Run MCP tests
        run: |
          mcpc localhost:3000 connect @ci-test

          # Verify tools exist
          TOOL_COUNT=$(mcpc @ci-test tools-list --json | jq 'length')
          if [ "$TOOL_COUNT" -eq 0 ]; then
            echo "No tools found!"
            exit 1
          fi

          # Run smoke test
          mcpc @ci-test tools-call health-check --json

          mcpc @ci-test close
        env:
          MCPC_JSON: 1
```

## Isolated test environments

Use `MCPC_HOME_DIR` to isolate test sessions from your normal mcpc data:

```bash
# Each test run gets its own home directory
export MCPC_HOME_DIR="/tmp/mcpc-test-$(date +%s)"

mcpc <server> connect @isolated
mcpc @isolated tools-list
mcpc @isolated close

# Cleanup
rm -rf "$MCPC_HOME_DIR"
```

## Comparing server versions

```bash
#!/bin/bash
# Compare tool schemas between two server versions

SESSION_OLD="@compare-old"
SESSION_NEW="@compare-new"

mcpc "$OLD_SERVER" connect "$SESSION_OLD"
mcpc "$NEW_SERVER" connect "$SESSION_NEW"

# Compare tool lists
OLD_TOOLS=$(mcpc "$SESSION_OLD" tools-list --json | jq -r '.[].name' | sort)
NEW_TOOLS=$(mcpc "$SESSION_NEW" tools-list --json | jq -r '.[].name' | sort)

echo "=== Tool Changes ==="
diff <(echo "$OLD_TOOLS") <(echo "$NEW_TOOLS") || true

# Compare each shared tool's schema
for tool in $(comm -12 <(echo "$OLD_TOOLS") <(echo "$NEW_TOOLS")); do
  OLD_SCHEMA=$(mcpc "$SESSION_OLD" tools-get "$tool" --json | jq '.inputSchema')
  NEW_SCHEMA=$(mcpc "$SESSION_NEW" tools-get "$tool" --json | jq '.inputSchema')

  if [ "$OLD_SCHEMA" != "$NEW_SCHEMA" ]; then
    echo "CHANGED: $tool"
    diff <(echo "$OLD_SCHEMA" | jq -S .) <(echo "$NEW_SCHEMA" | jq -S .) || true
  fi
done

mcpc "$SESSION_OLD" close
mcpc "$SESSION_NEW" close
```

## Parallel testing

```bash
# Test multiple servers concurrently
SERVERS=("https://server1.com" "https://server2.com" "config.json:local")

for server in "${SERVERS[@]}"; do
  (
    SESSION="@parallel-$(echo "$server" | md5sum | cut -c1-8)"
    mcpc "$server" connect "$SESSION" && \
    mcpc "$SESSION" tools-list --json > "/tmp/results-$SESSION.json" && \
    mcpc "$SESSION" close
  ) &
done

wait
echo "All parallel tests complete"
```

## Watching for changes

```bash
# Poll server capabilities every 30 seconds
while true; do
  TOOLS=$(mcpc @session tools-list --json 2>/dev/null | jq 'length')
  echo "$(date): $TOOLS tools available"
  sleep 30
done
```
