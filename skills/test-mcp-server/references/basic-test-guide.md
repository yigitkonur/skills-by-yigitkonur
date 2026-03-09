# Basic MCP Server Testing Guide (`/mcp-test`)

This guide walks through testing every MCP primitive to verify a server is working correctly. Every step uses `curl` through the inspector proxy. No browser needed.

## Phase 0: Gather Information

Before doing anything, figure out what you're testing.

1. **Get the MCP server URL from the user.** If they don't provide one, check:
   - Is there a running server in the project? (`lsof -i :3000` or similar)
   - Is there a `package.json` with a start script?
   - Is there an `mcp_servers.json` or similar config?
   - Ask the user if you can't determine it.

2. **Check if the MCP server is running.** Try a direct HTTP request:
   ```bash
   curl -sf "$MCP_URL" -o /dev/null && echo "reachable" || echo "unreachable"
   ```

3. **Check if auth is needed.** Ask the user or check for headers/tokens in config files.

Use the crash thinking tool to plan your approach:
```
Step 1: Identify MCP URL, auth requirements, and server state
Purpose: planning
Context: User wants to test their MCP server
Thought: Need to determine URL, whether server is running, and if auth is needed
```

## Phase 1: Start Inspector

```bash
PORT=19876
MCP_URL="<user's MCP URL>"

MCP_USE_ANONYMIZED_TELEMETRY=false npx @mcp-use/inspector \
  --url "$MCP_URL" \
  --port "$PORT" \
  --no-open &
INSPECTOR_PID=$!

# Wait for startup
for i in $(seq 1 30); do
  curl -sf "http://localhost:${PORT}/inspector/health" > /dev/null 2>&1 && break
  sleep 1
done
```

Set up the helper function (use this for all subsequent calls):
```bash
BASE="http://localhost:${PORT}/inspector"

rpc() {
  local method="$1"
  local params="${2:-{}}"
  curl -sf -X POST "${BASE}/api/proxy" \
    -H "Content-Type: application/json" \
    -H "x-mcp-url: ${MCP_URL}" \
    -d "{\"jsonrpc\":\"2.0\",\"id\":$RANDOM,\"method\":\"${method}\",\"params\":${params}}"
}
```

## Phase 2: Protocol-Level Checks

Run these in order. Each depends on the previous succeeding.

### Check 1: Health (Inspector itself)

```bash
curl -sf "${BASE}/health" | jq -e '.status == "ok"'
```

**Pass:** Returns `{"status":"ok",...}`
**Fail:** Inspector didn't start. Check port, check if npx install succeeded.

### Check 2: Initialize (MCP handshake)

```bash
INIT_RESULT=$(rpc "initialize" '{
  "protocolVersion":"2025-03-26",
  "capabilities":{},
  "clientInfo":{"name":"mcp-test","version":"1.0.0"}
}')
echo "$INIT_RESULT" | jq .
```

**Validate:**
```bash
# Has server info
echo "$INIT_RESULT" | jq -e '.result.serverInfo.name'

# Has protocol version
echo "$INIT_RESULT" | jq -e '.result.protocolVersion'

# Has capabilities object
echo "$INIT_RESULT" | jq -e '.result.capabilities'
```

**Pass:** All three return values.
**Fail:** Server not running, wrong URL, or server doesn't implement MCP properly.

Record the capabilities — they tell you what primitives the server supports:
```bash
CAPABILITIES=$(echo "$INIT_RESULT" | jq '.result.capabilities')
HAS_TOOLS=$(echo "$CAPABILITIES" | jq 'has("tools")')
HAS_RESOURCES=$(echo "$CAPABILITIES" | jq 'has("resources")')
HAS_PROMPTS=$(echo "$CAPABILITIES" | jq 'has("prompts")')
```

### Check 3: Ping

```bash
rpc "ping" | jq -e '.result == {} or .result == null'
```

**Pass:** Returns empty result (server is alive and responsive).
**Fail:** Server accepts connections but doesn't respond to ping.

## Phase 3: Tools Testing

Skip this phase if the server doesn't advertise tools capability.

### Check 4: List Tools

```bash
TOOLS_RESULT=$(rpc "tools/list")
TOOL_COUNT=$(echo "$TOOLS_RESULT" | jq '.result.tools | length')
echo "Found $TOOL_COUNT tools"
echo "$TOOLS_RESULT" | jq -r '.result.tools[] | "  - \(.name): \(.description // "no description")"'
```

**Pass:** Returns a list of tools (can be empty if server has none).
**Fail:** Error response or malformed JSON.

### Check 5: Schema Validation (per tool)

For each tool, verify its inputSchema is valid JSON Schema:

```bash
echo "$TOOLS_RESULT" | jq -c '.result.tools[]' | while read -r tool; do
  NAME=$(echo "$tool" | jq -r '.name')
  HAS_SCHEMA=$(echo "$tool" | jq 'has("inputSchema")')
  SCHEMA_TYPE=$(echo "$tool" | jq -r '.inputSchema.type // "missing"')
  REQUIRED=$(echo "$tool" | jq '.inputSchema.required // []')
  PROPS=$(echo "$tool" | jq '.inputSchema.properties // {}')

  echo "Tool: $NAME"
  echo "  Has schema: $HAS_SCHEMA"
  echo "  Schema type: $SCHEMA_TYPE"
  echo "  Required fields: $REQUIRED"
  echo "  Properties: $(echo "$PROPS" | jq 'keys')"
  echo ""
done
```

**Pass:** Every tool has `inputSchema` with `type: "object"` and valid `properties`.
**Fail:** Missing schema, wrong type, or properties don't match what the tool expects.

### Check 6: Call Each Tool (Happy Path)

For each tool, construct minimal valid arguments from its schema and call it:

```bash
# For each tool, build arguments from required properties with sensible defaults
echo "$TOOLS_RESULT" | jq -c '.result.tools[]' | while read -r tool; do
  NAME=$(echo "$tool" | jq -r '.name')
  echo "=== Calling: $NAME ==="

  # Build minimal arguments from required fields
  # This requires reading the schema and constructing valid test inputs
  ARGS=$(echo "$tool" | jq '{
    name: .name,
    arguments: (
      .inputSchema.required // [] | map(
        . as $key |
        {($key): (
          if (.inputSchema.properties[$key].type // "") == "string" then "test"
          elif (.inputSchema.properties[$key].type // "") == "number" then 0
          elif (.inputSchema.properties[$key].type // "") == "integer" then 0
          elif (.inputSchema.properties[$key].type // "") == "boolean" then false
          elif (.inputSchema.properties[$key].type // "") == "array" then []
          elif (.inputSchema.properties[$key].type // "") == "object" then {}
          else "test"
          end
        )}
      ) | add // {}
    )
  }' 2>/dev/null || echo "{\"name\":\"$NAME\",\"arguments\":{}}")

  RESULT=$(rpc "tools/call" "$ARGS")
  IS_ERROR=$(echo "$RESULT" | jq '.result.isError // false')
  HAS_CONTENT=$(echo "$RESULT" | jq '.result.content | length > 0')
  HAS_ERROR=$(echo "$RESULT" | jq 'has("error")')

  if [ "$HAS_ERROR" = "true" ]; then
    echo "  RESULT: JSON-RPC error"
    echo "  Error: $(echo "$RESULT" | jq -r '.error.message')"
  elif [ "$IS_ERROR" = "true" ]; then
    echo "  RESULT: Tool returned error (isError=true)"
    echo "  Content: $(echo "$RESULT" | jq -r '.result.content[0].text // "no text"' | head -3)"
  else
    echo "  RESULT: Success"
    echo "  Content type: $(echo "$RESULT" | jq -r '.result.content[0].type // "unknown"')"
    echo "  Content preview: $(echo "$RESULT" | jq -r '.result.content[0].text // "no text"' | head -3)"
  fi
  echo ""
done
```

Use the crash thinking tool to reason about each tool's expected inputs:
```
Purpose: analysis
Thought: Tool "X" has required fields [a, b, c] with types [string, number, object].
  I need to construct realistic test inputs, not just type-default placeholders.
  Looking at the description: "Searches for files matching a pattern"
  So "a" is probably a search query, "b" is a limit, "c" is options.
  Better test input: {"query": "test", "limit": 10, "options": {}}
```

The auto-generated defaults above are a starting point. For each tool, read the description and property names to construct more realistic inputs. A tool called `search_files` with a `path` parameter needs an actual path like `"."`, not just `"test"`.

### Check 7: Error Handling (per tool)

For each tool, verify it handles bad input gracefully:

```bash
# Empty arguments (missing required fields)
rpc "tools/call" '{"name":"TOOL_NAME","arguments":{}}'

# Wrong types
rpc "tools/call" '{"name":"TOOL_NAME","arguments":{"string_field": 12345}}'

# Extra unknown fields
rpc "tools/call" '{"name":"TOOL_NAME","arguments":{"unknown_field":"value"}}'
```

**Pass:** Returns `isError: true` with a descriptive error message, or a JSON-RPC error. Does NOT crash the server.
**Fail:** Server crashes, hangs, or returns success with garbage data.

### Check 8: Nonexistent Tool

```bash
rpc "tools/call" '{"name":"__nonexistent_tool_12345__","arguments":{}}'
```

**Pass:** Returns an error (either `result.isError: true` or JSON-RPC error).
**Fail:** Server crashes or returns success.

## Phase 4: Resources Testing

Skip if server doesn't advertise resources capability.

### Check 9: List Resources

```bash
RESOURCES_RESULT=$(rpc "resources/list")
RESOURCE_COUNT=$(echo "$RESOURCES_RESULT" | jq '.result.resources | length')
echo "Found $RESOURCE_COUNT resources"
echo "$RESOURCES_RESULT" | jq -r '.result.resources[] | "  - \(.uri): \(.name // "unnamed") [\(.mimeType // "unknown")]"'
```

### Check 10: Read Each Resource

```bash
echo "$RESOURCES_RESULT" | jq -r '.result.resources[].uri' | while read -r uri; do
  echo "=== Reading: $uri ==="
  RESULT=$(rpc "resources/read" "{\"uri\":\"$uri\"}")
  CONTENT_COUNT=$(echo "$RESULT" | jq '.result.contents | length')
  HAS_ERROR=$(echo "$RESULT" | jq 'has("error")')

  if [ "$HAS_ERROR" = "true" ]; then
    echo "  FAIL: $(echo "$RESULT" | jq -r '.error.message')"
  else
    echo "  Contents: $CONTENT_COUNT items"
    echo "$RESULT" | jq -r '.result.contents[] | "  Type: \(.mimeType // "text") | Size: \(.text // .blob | length) chars"'
  fi
  echo ""
done
```

### Check 11: Read Nonexistent Resource

```bash
rpc "resources/read" '{"uri":"resource://__nonexistent_12345__"}'
```

**Pass:** Returns an error.
**Fail:** Server crashes or returns empty success.

### Check 12: Resource Templates

```bash
TEMPLATES_RESULT=$(rpc "resources/templates/list")
echo "$TEMPLATES_RESULT" | jq '.result'
```

If templates exist, try to fill one:
```bash
echo "$TEMPLATES_RESULT" | jq -c '.result.resourceTemplates[]' | while read -r tmpl; do
  URI_TEMPLATE=$(echo "$tmpl" | jq -r '.uriTemplate')
  echo "Template: $URI_TEMPLATE"
  # Fill template variables with test values
  FILLED_URI=$(echo "$URI_TEMPLATE" | sed 's/{[^}]*}/test/g')
  echo "  Filled: $FILLED_URI"
  rpc "resources/read" "{\"uri\":\"$FILLED_URI\"}" | jq '.result // .error'
done
```

## Phase 5: Prompts Testing

Skip if server doesn't advertise prompts capability.

### Check 13: List Prompts

```bash
PROMPTS_RESULT=$(rpc "prompts/list")
PROMPT_COUNT=$(echo "$PROMPTS_RESULT" | jq '.result.prompts | length')
echo "Found $PROMPT_COUNT prompts"
echo "$PROMPTS_RESULT" | jq -r '.result.prompts[] | "  - \(.name): \(.description // "no description")"'
```

### Check 14: Get Each Prompt

```bash
echo "$PROMPTS_RESULT" | jq -c '.result.prompts[]' | while read -r prompt; do
  NAME=$(echo "$prompt" | jq -r '.name')
  echo "=== Prompt: $NAME ==="

  # Build arguments from prompt's declared arguments
  PROMPT_ARGS=$(echo "$prompt" | jq '{
    name: .name,
    arguments: (
      .arguments // [] | map({(.name): "test_value"}) | add // {}
    )
  }')

  RESULT=$(rpc "prompts/get" "$PROMPT_ARGS")
  HAS_ERROR=$(echo "$RESULT" | jq 'has("error")')

  if [ "$HAS_ERROR" = "true" ]; then
    echo "  FAIL: $(echo "$RESULT" | jq -r '.error.message')"
  else
    MSG_COUNT=$(echo "$RESULT" | jq '.result.messages | length')
    echo "  Messages: $MSG_COUNT"
    echo "$RESULT" | jq -r '.result.messages[] | "  [\(.role)] \(.content.text // .content | tostring | .[0:100])..."'
  fi
  echo ""
done
```

### Check 15: Prompt with Missing Arguments

```bash
# For prompts that have required arguments, call without them
echo "$PROMPTS_RESULT" | jq -c '.result.prompts[] | select(.arguments | length > 0)' | while read -r prompt; do
  NAME=$(echo "$prompt" | jq -r '.name')
  rpc "prompts/get" "{\"name\":\"$NAME\",\"arguments\":{}}"
done
```

**Pass:** Returns an error about missing arguments.
**Fail:** Server crashes or returns a prompt with unfilled placeholders.

## Phase 6: Advanced Protocol Checks

### Check 16: Completion

If the server supports completion (check capabilities):
```bash
# Try resource URI completion
rpc "completion/complete" '{
  "ref":{"type":"ref/resource","uri":"resource://"},
  "argument":{"name":"uri","value":"resource://"}
}'

# Try prompt argument completion
rpc "completion/complete" '{
  "ref":{"type":"ref/prompt","name":"PROMPT_NAME"},
  "argument":{"name":"ARG_NAME","value":"partial"}
}'
```

### Check 17: Logging

```bash
rpc "logging/setLevel" '{"level":"debug"}'
rpc "logging/setLevel" '{"level":"info"}'
rpc "logging/setLevel" '{"level":"warning"}'
rpc "logging/setLevel" '{"level":"error"}'
```

### Check 18: Concurrent Requests

Send multiple tool calls simultaneously to test server stability:
```bash
for i in $(seq 1 5); do
  rpc "tools/list" &
done
wait
echo "All concurrent requests completed"
```

### Check 19: Large Input

If a tool accepts string input, send something large:
```bash
LARGE_INPUT=$(python3 -c "print('x' * 10000)")
rpc "tools/call" "{\"name\":\"TOOL_NAME\",\"arguments\":{\"input\":\"$LARGE_INPUT\"}}"
```

**Pass:** Returns an error or handles gracefully.
**Fail:** Server crashes or hangs.

## Phase 7: Cleanup and Report

```bash
kill $INSPECTOR_PID 2>/dev/null
```

### Report Format

Present results as a clear table:

```
## MCP Server Test Results

Server: http://localhost:3000/mcp
Server name: <from initialize>
Protocol version: <from initialize>

### Protocol
| Check | Result | Notes |
|-------|--------|-------|
| Health (inspector) | PASS | |
| Initialize | PASS | server v1.0.0 |
| Ping | PASS | |

### Tools (N found)
| Tool | Schema | Happy Path | Error Handling |
|------|--------|------------|----------------|
| search_files | PASS | PASS | PASS |
| read_file | PASS | PASS | FAIL: crashes on missing path |

### Resources (N found)
| Resource | Read | Notes |
|----------|------|-------|
| resource://config | PASS | 2.3KB JSON |
| resource://data | FAIL | timeout after 10s |

### Prompts (N found)
| Prompt | Render | Missing Args |
|--------|--------|-------------|
| summarize | PASS | PASS |

### Advanced
| Check | Result | Notes |
|-------|--------|-------|
| Nonexistent tool | PASS | returns error |
| Nonexistent resource | PASS | returns error |
| Concurrent requests | PASS | 5 parallel OK |
| Large input | PASS | returns error for >10KB |

### Summary
- Total checks: N
- Passed: N
- Failed: N
- Skipped: N (capability not advertised)
```

Use the crash thinking tool to summarize findings:
```
Purpose: summary
Thought: Analyzing all test results to provide actionable summary.
  3 tools passed all checks. 1 tool fails on missing required args (crashes instead of error).
  Resources all work. No prompts exposed.
  Recommendation: Fix error handling in read_file tool for missing path argument.
```
