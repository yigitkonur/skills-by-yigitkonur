# jq Patterns for mcpc

Reusable jq expressions for extracting, filtering, transforming, and validating mcpc JSON output. All patterns assume `--json` mode (either `--json` flag or `MCPC_JSON=1`).

## Tool discovery patterns

### List tool names

```bash
# All tool names, one per line
mcpc --json @s tools-list | jq -r '.[].name'

# Sorted alphabetically
mcpc --json @s tools-list | jq -r '[.[].name] | sort | .[]'

# Count tools
mcpc --json @s tools-list | jq 'length'
```

### Filter tools by name

```bash
# Exact match
mcpc --json @s tools-list | jq '.[] | select(.name == "search")'

# Name contains substring (regex)
mcpc --json @s tools-list | jq '[.[] | select(.name | test("search"))]'

# Name starts with prefix
mcpc --json @s tools-list | jq '[.[] | select(.name | startswith("get_"))]'

# Name matches glob-like pattern
mcpc --json @s tools-list | jq '[.[] | select(.name | test("^(create|update|delete)_"))]'
```

### Filter tools by description

```bash
# Description contains keyword (case-insensitive)
mcpc --json @s tools-list | jq '[.[] | select(.description | test("web"; "i"))]'

# Tools with no description (quality check)
mcpc --json @s tools-list | jq '[.[] | select(.description == null or .description == "")]'

# Tools with long descriptions (> 200 chars)
mcpc --json @s tools-list | jq '[.[] | select((.description // "") | length > 200)]'
```

### Inspect tool schemas

```bash
# Get one tool's full schema
mcpc --json @s tools-get my-tool | jq '.inputSchema'

# Extract required parameters for a tool
mcpc --json @s tools-get my-tool | jq '.inputSchema.required'

# Extract all parameter names
mcpc --json @s tools-get my-tool | jq '.inputSchema.properties | keys'

# RECOMMENDED — parameter names, types, array item types, and cardinality constraints:
mcpc --json @s tools-get my-tool | jq '
  .inputSchema.properties | to_entries | map({
    name: .key,
    type: .value.type,
    items: (if .value.type == "array" then (.value.items.type // .value.items) else null end),
    min: .value.minItems,
    max: .value.maxItems
  })'

# AVOID — this pattern only shows top-level type, hiding critical array details:
# mcpc --json @s tools-get my-tool | jq '.inputSchema.properties | to_entries | map({name: .key, type: .value.type})'
# It will show {"name":"urls","type":"array"} but NOT that items must be objects or that minItems is 3.

# Generate parameter inventory across all tools (use --full)
mcpc --json @s tools-list --full | jq '.[] | {name, params: [.inputSchema.properties | keys[]]}'

# Find tools that accept a specific parameter name
mcpc --json @s tools-list --full | jq '[.[] | select(.inputSchema.properties | has("query"))]'

# Find tools with no required parameters
mcpc --json @s tools-list --full | jq '[.[] | select((.inputSchema.required // []) | length == 0)]'

# Find tools with more than 5 parameters
mcpc --json @s tools-list --full | jq '[.[] | select((.inputSchema.properties // {}) | length > 5)]'
```

## Tool call result patterns

### Extract content

```bash
# Get the first text content block
mcpc --json @s tools-call search query:=test | jq -r '.content[0].text'

# Get all text content blocks concatenated
mcpc --json @s tools-call search query:=test | jq -r '[.content[] | select(.type == "text") | .text] | join("\n")'

# Get raw content array
mcpc --json @s tools-call search query:=test | jq '.content'

# Count content blocks
mcpc --json @s tools-call search query:=test | jq '.content | length'

# Get content by type
mcpc --json @s tools-call search query:=test | jq '[.content[] | select(.type == "text")]'
mcpc --json @s tools-call screenshot | jq '[.content[] | select(.type == "image")]'
```

### Parse structured text responses

Many tools return JSON-as-string inside `content[0].text`. Parse it:

```bash
# Parse JSON embedded in text response
mcpc --json @s tools-call get-data id:=123 | jq -r '.content[0].text' | jq .

# Extract a field from embedded JSON
mcpc --json @s tools-call get-data id:=123 | jq -r '.content[0].text' | jq '.results[0].title'

# One-liner with fromjson (if text is valid JSON)
mcpc --json @s tools-call get-data id:=123 | jq '.content[0].text | fromjson | .results'
```

### Extract image content

```bash
# Get base64-encoded image data
mcpc --json @s tools-call screenshot | jq -r '.content[] | select(.type == "image") | .data'

# Get image MIME type
mcpc --json @s tools-call screenshot | jq -r '.content[] | select(.type == "image") | .mimeType'

# Save image to file
mcpc --json @s tools-call screenshot | jq -r '.content[] | select(.type == "image") | .data' | base64 -d > screenshot.png
```

### Error checking

```bash
# Check if tool returned an error
mcpc --json @s tools-call search query:=test | jq '.isError // false'

# Conditional: only process result if no error
if mcpc --json @s tools-call search query:=test | jq -e '.isError == false' > /dev/null 2>&1; then
  echo "Success"
else
  echo "Tool returned error"
fi

# Extract error details when isError is true
mcpc --json @s tools-call bad-tool 2>&1 | jq '{isError, content: [.content[] | .text]}'
```

## Session management patterns

### List and inspect sessions

```bash
# List all sessions with status
mcpc --json | jq '.sessions[] | {name, status, server: .server.url}'

# Filter only live sessions
mcpc --json | jq '[.sessions[] | select(.status == "live")]'

# Filter disconnected or crashed sessions
mcpc --json | jq '[.sessions[] | select(.status == "disconnected" or .status == "crashed")]'

# Session count by status
mcpc --json | jq '.sessions | group_by(.status) | map({status: .[0].status, count: length})'

# Get total session count
mcpc --json | jq '.sessions | length'
```

### Inspect session details

```bash
# Get protocol version
mcpc --json @s | jq '.protocolVersion'

# Extract server capabilities
mcpc --json @s | jq '.capabilities'

# List capability keys only
mcpc --json @s | jq '.capabilities | keys'

# Check specific capability
mcpc --json @s | jq '.capabilities.tools // "not supported"'

# Get server info (name, version)
mcpc --json @s | jq '.serverInfo'

# Full session diagnostic dump
mcpc --json @s | jq '{
  protocolVersion: .protocolVersion,
  serverInfo: .serverInfo,
  capabilities: (.capabilities | keys),
  sessionId: .sessionId
}'
```

## Data transformation patterns

### Export as CSV

```bash
# Tools as CSV (name, description)
mcpc --json @s tools-list | jq -r '.[] | [.name, .description] | @csv'

# Tools as CSV with header
mcpc --json @s tools-list | jq -r '["name","description"], (.[] | [.name, .description]) | @csv'

# Resources as CSV
mcpc --json @s resources-list | jq -r '.[] | [.uri, .name, .mimeType] | @csv'
```

### Export as TSV

```bash
# Tools as TSV (tab-separated, for spreadsheets)
mcpc --json @s tools-list | jq -r '.[] | [.name, .description] | @tsv'
```

### Export as Markdown table

```bash
# Generate Markdown table of tools
mcpc --json @s tools-list | jq -r '
  "| Tool | Description |",
  "| --- | --- |",
  (.[] | "| `\(.name)` | \(.description // "—") |")
'

# Markdown table with parameter count
mcpc --json @s tools-list --full | jq -r '
  "| Tool | Params | Required |",
  "| --- | --- | --- |",
  (.[] |
    "| `\(.name)` | \((.inputSchema.properties // {}) | length) | \((.inputSchema.required // []) | length) |"
  )
'
```

### Tool diff between two servers

```bash
# Compare tool names between two sessions
diff <(mcpc --json @server1 tools-list | jq -r '.[].name' | sort) \
     <(mcpc --json @server2 tools-list | jq -r '.[].name' | sort)

# Show tools only in server1 (removed)
comm -23 <(mcpc --json @server1 tools-list | jq -r '.[].name' | sort) \
         <(mcpc --json @server2 tools-list | jq -r '.[].name' | sort)

# Show tools only in server2 (added)
comm -13 <(mcpc --json @server1 tools-list | jq -r '.[].name' | sort) \
         <(mcpc --json @server2 tools-list | jq -r '.[].name' | sort)

# Full schema diff for a specific tool
diff <(mcpc --json @server1 tools-get my-tool | jq -S '.inputSchema') \
     <(mcpc --json @server2 tools-get my-tool | jq -S '.inputSchema')
```

## Resource patterns

### List and filter resources

```bash
# All resource URIs
mcpc --json @s resources-list | jq -r '.[].uri'

# Filter by URI scheme
mcpc --json @s resources-list | jq '[.[] | select(.uri | startswith("file://"))]'

# Filter by MIME type
mcpc --json @s resources-list | jq '[.[] | select(.mimeType == "application/json")]'

# Resources with their templates
mcpc --json @s resources-templates-list | jq '.[] | {uriTemplate, name, mimeType}'
```

### Read and process resources

```bash
# Read resource and extract text content
mcpc --json @s resources-read "file:///path" | jq -r '.contents[0].text'

# Read resource and parse as JSON (when content is JSON text)
mcpc --json @s resources-read "file:///data.json" | jq '.contents[0].text | fromjson'
```

## Prompt patterns

### Inspect prompts

```bash
# List prompt names
mcpc --json @s prompts-list | jq -r '.[].name'

# Extract prompt arguments (what parameters it expects)
mcpc --json @s prompts-list | jq '.[] | {name, arguments}'

# Get prompt with arguments and extract messages
mcpc --json @s prompts-get my-prompt arg1:=val1 | jq '.messages'

# Extract just the text from prompt messages
mcpc --json @s prompts-get my-prompt arg1:=val1 | jq -r '.messages[].content.text'
```

## Error handling patterns

### Parse error output

```bash
# mcpc writes JSON errors to stdout even on failure
# Capture and parse
RESULT=$(mcpc --json @s tools-call bad-tool 2>&1)
EXIT_CODE=$?

echo "$RESULT" | jq '{
  error: .error,
  code: .code
}'
```

### Check for specific error types

```bash
# Check if error is auth-related
mcpc --json @s tools-call tool 2>&1 | jq -e '.error == "AuthError"' > /dev/null && echo "Auth error"

# Check by exit code and error type
RESULT=$(mcpc --json @s tools-call tool 2>&1)
EXIT=$?
case $EXIT in
  0) echo "$RESULT" | jq . ;;
  1) echo "Client error: $(echo "$RESULT" | jq -r '.error // "unknown client error"')" ;;
  2) echo "Server error: $(echo "$RESULT" | jq -r '.error // "unknown server error"')" ;;
  3) echo "Network error: $(echo "$RESULT" | jq -r '.error // "unknown network error"')" ;;
  4) echo "Auth error: $(echo "$RESULT" | jq -r '.error // "unknown auth error"')" ;;
esac
```

## x402 payment patterns

```bash
# Check which tools require payment (need --full for _meta)
mcpc --json @paid tools-list --full | jq '[.[] | select(._meta.x402.paymentRequired == true)]'

# List paid tools with their max cost
mcpc --json @paid tools-list --full | jq '[.[] | select(._meta.x402) | {name, maxCost: ._meta.x402.maxAmountRequired}]'

# Check if a specific tool requires payment
mcpc --json @paid tools-get my-tool | jq '._meta.x402.paymentRequired // false'
```

## Batch and cross-session patterns

### Inventory tools across all sessions

```bash
#!/bin/bash
# List tools from every live session
for session in $(mcpc --json | jq -r '.sessions[] | select(.status == "live") | .name'); do
  echo "=== $session ==="
  mcpc --json "$session" tools-list | jq -r '.[].name' | sed 's/^/  /'
done
```

### Find a tool across all sessions

```bash
#!/bin/bash
# Which session has a tool named "search"?
TOOL_NAME="${1:?Usage: $0 <tool-name>}"
for session in $(mcpc --json | jq -r '.sessions[] | select(.status == "live") | .name'); do
  if mcpc --json "$session" tools-list | jq -e ".[] | select(.name == \"$TOOL_NAME\")" > /dev/null 2>&1; then
    echo "Found '$TOOL_NAME' in $session"
  fi
done
```

### Aggregate tool counts

```bash
# Tool count per session as JSON
mcpc --json | jq -r '.sessions[] | select(.status == "live") | .name' | while read -r session; do
  COUNT=$(mcpc --json "$session" tools-list 2>/dev/null | jq 'length')
  echo "{\"session\": \"$session\", \"tools\": $COUNT}"
done | jq -s '.'
```

## Assertion patterns for test scripts

### Assert tool count

```bash
EXPECTED=5
ACTUAL=$(mcpc --json @s tools-list | jq 'length')
if [ "$ACTUAL" -ne "$EXPECTED" ]; then
  echo "FAIL: Expected $EXPECTED tools, got $ACTUAL"
  exit 1
fi
```

### Assert tool exists

```bash
if ! mcpc --json @s tools-list | jq -e '.[] | select(.name == "search")' > /dev/null 2>&1; then
  echo "FAIL: Tool 'search' not found"
  exit 1
fi
```

### Assert tool has required parameters

```bash
REQUIRED=$(mcpc --json @s tools-get search | jq -r '.inputSchema.required | sort | join(",")')
EXPECTED="limit,query"
if [ "$REQUIRED" != "$EXPECTED" ]; then
  echo "FAIL: Expected required params [$EXPECTED], got [$REQUIRED]"
  exit 1
fi
```

### Assert tool result contains expected text

```bash
RESULT=$(mcpc --json @s tools-call search query:=test | jq -r '.content[0].text')
if ! echo "$RESULT" | grep -q "expected substring"; then
  echo "FAIL: Result does not contain expected substring"
  echo "Got: $RESULT"
  exit 1
fi
```

### Assert no tool errors

```bash
IS_ERROR=$(mcpc --json @s tools-call search query:=test | jq '.isError // false')
if [ "$IS_ERROR" = "true" ]; then
  echo "FAIL: Tool returned isError: true"
  exit 1
fi
```

### Assert response has specific content type

```bash
HAS_IMAGE=$(mcpc --json @s tools-call screenshot | jq '[.content[] | select(.type == "image")] | length > 0')
if [ "$HAS_IMAGE" != "true" ]; then
  echo "FAIL: Expected image content in response"
  exit 1
fi
```

## Performance measurement patterns

```bash
# Time a tool call and extract duration
START=$(date +%s%N)
mcpc --json @s tools-call search query:=test > /dev/null
END=$(date +%s%N)
DURATION_MS=$(( (END - START) / 1000000 ))
echo "Tool call took ${DURATION_MS}ms"

# Batch timing for multiple tools
for tool in $(mcpc --json @s tools-list | jq -r '.[].name'); do
  START=$(date +%s%N)
  mcpc --json @s tools-get "$tool" > /dev/null 2>&1
  END=$(date +%s%N)
  MS=$(( (END - START) / 1000000 ))
  echo "$tool: ${MS}ms"
done
```

## Tips

- Always use `--json` (or `MCPC_JSON=1`) when piping to jq. Human-readable output has ANSI colors that break parsing.
- Use `jq -e` for boolean assertions in conditionals — it sets exit code based on truthiness.
- Use `jq -r` for raw string output (strips quotes).
- Use `jq -S` when comparing JSON (sorts keys for stable diff).
- Use `jq -s` (slurp) to collect multiple JSON lines into an array.
- When a tool returns JSON-as-text in `content[0].text`, chain `| fromjson` to parse it.
- Redirect stderr when capturing: `mcpc --json @s tools-call tool 2>&1` — error JSON goes to stdout, but stderr may have debug info.
