# Tool, Resource, and Prompt Testing

Deep patterns for testing MCP server tools, resources, and prompts via mcpc.

## Tool discovery

### List all tools

```bash
# Summary view (name + description)
mcpc @session tools

# Full view (includes input schemas)
mcpc @session tools --full

# JSON output for scripting
mcpc @session tools-list --json
mcpc @session tools-list --json | jq '.[].name'
mcpc @session tools-list --json | jq '.[] | {name, description}'
```

### Inspect a specific tool

```bash
# Human-readable
mcpc @session tools-get tool-name

# JSON with full schema
mcpc @session tools-get tool-name --json
mcpc @session tools-get tool-name --json | jq '.inputSchema'

# Check array params for item types and cardinality constraints BEFORE calling:
mcpc @session tools-get tool-name --json | jq '
  .inputSchema.properties | to_entries[] | select(.value.type == "array") | {
    param: .key,
    items: (.value.items.type // .value.items),
    min: .value.minItems,
    max: .value.maxItems
  }'
# This tells you: is items a string or object? How many are required?
# Without this, you'll guess wrong on the first call (e.g., pass strings when objects are expected, or pass 1 item when 3 are required).

# Save schema for later validation
mcpc @session tools-get tool-name --json > expected-schema.json
```

## Tool calling

### Argument syntax (`key:=value`)

Arguments use the `:=` operator with auto-type detection:

```bash
# String (not valid JSON → string)
mcpc @session tools-call search query:=hello

# Number (valid JSON number)
mcpc @session tools-call paginate offset:=0 limit:=10

# Boolean (valid JSON boolean)
mcpc @session tools-call toggle enabled:=true

# Force string for numeric-looking values
mcpc @session tools-call lookup id:='"123"'
# Parsed as string "123", not number 123

# Multiple arguments
mcpc @session tools-call create-user \
  name:=John \
  age:=30 \
  active:=true \
  role:=admin
```

### Auto-parsing rules

| Input | Parsed value | Type | Rule |
|---|---|---|---|
| `count:=10` | `10` | number | Valid JSON number |
| `enabled:=true` | `true` | boolean | Valid JSON boolean |
| `enabled:=false` | `false` | boolean | Valid JSON boolean |
| `name:=hello` | `"hello"` | string | Not valid JSON → string |
| `data:=null` | `null` | null | Valid JSON null |
| `id:='"abc"'` | `"abc"` | string | JSON string literal (quoted) |
| `tags:='["a","b"]'` | `["a","b"]` | array | Valid JSON array |
| `meta:='{"k":"v"}'` | `{"k":"v"}` | object | Valid JSON object |

### Inline JSON

```bash
# Pass entire argument object as JSON (first arg starts with { or [)
mcpc @session tools-call create-user '{"name": "John", "age": 30, "active": true}'
```

### Piped input

```bash
# Pipe JSON from stdin
echo '{"query": "test", "limit": 10}' | mcpc @session tools-call search

# Pipe from file
cat request.json | mcpc @session tools-call process-data

# Pipe from command
jq -n '{"path": "/tmp/test.txt"}' | mcpc @session tools-call read_file
```

### JSON output

```bash
# Get structured response
mcpc @session tools-call search query:=test --json

# Extract specific fields
mcpc @session tools-call search query:=test --json | jq '.content'
mcpc @session tools-call search query:=test --json | jq '.content[0].text'

# Check for errors
mcpc @session tools-call bad-args --json | jq '.isError'
```

## Schema validation

### Save and validate schemas

```bash
# Step 1: Export the expected schema
mcpc @session tools-get my-tool --json > /tmp/my-tool-schema.json

# Step 2: Call tool with schema validation
mcpc @session tools-call my-tool arg:=value --schema /tmp/my-tool-schema.json

# Step 3: Strict mode (fails on extra fields or type mismatches)
mcpc @session tools-call my-tool arg:=value \
  --schema /tmp/my-tool-schema.json \
  --schema-mode strict
```

### Schema validation modes

| Mode | Behavior |
|---|---|
| `compatible` (default) | Allows extra fields, checks required fields and types |
| `strict` | Exact match — no extra fields, all types must match precisely |
| `ignore` | Skip schema validation entirely |

### Regression testing with schemas

```bash
#!/bin/bash
# Save schemas from a known-good server version
for tool in $(mcpc @baseline tools-list --json | jq -r '.[].name'); do
  mcpc @baseline tools-get "$tool" --json > "/tmp/schemas/$tool.json"
done

# Later, validate against new server version
for schema in /tmp/schemas/*.json; do
  tool=$(basename "$schema" .json)
  echo "Validating: $tool"
  mcpc @new-version tools-call "$tool" --schema "$schema" --schema-mode strict 2>&1 || \
    echo "  SCHEMA MISMATCH: $tool"
done
```

## Resource testing

### List resources

```bash
# All resources
mcpc @session resources

# JSON output
mcpc @session resources-list --json
mcpc @session resources-list --json | jq '.[].uri'

# Resource templates
mcpc @session resources-templates-list
```

### Read resources

```bash
# Read to stdout
mcpc @session resources-read "file:///path/to/resource"

# Read with JSON wrapper
mcpc @session resources-read "file:///path" --json | jq '.contents'

# Save to file
mcpc @session resources-read "https://example.com/data.csv" > data.csv
```

### Resource subscriptions

```bash
# Subscribe to changes (blocks and prints updates)
mcpc @session resources-subscribe "file:///watched-path"

# Unsubscribe
mcpc @session resources-unsubscribe "file:///watched-path"
```

## Prompt testing

### List prompts

```bash
mcpc @session prompts
mcpc @session prompts-list --json
```

### Get prompts with arguments

```bash
# Get prompt (renders the template)
mcpc @session prompts-get code-review language:=typescript file:=main.ts

# JSON output
mcpc @session prompts-get code-review language:=typescript --json | jq '.messages'
```

## Long-running work

`mcpc 0.1.11` does not expose `--task`, `--detach`, or `tasks-*` commands.

For slow tools, increase the timeout and keep the call synchronous:

```bash
mcpc @session tools-call long-process data:=input --timeout 900
```

If the server models background work through normal tools, follow that server-specific job workflow instead of assuming generic task commands exist.

## Logging level control

```bash
# Set server-side logging verbosity
mcpc @session logging-set-level debug
mcpc @session logging-set-level info
mcpc @session logging-set-level warning
mcpc @session logging-set-level error

# Valid levels: debug, info, notice, warning, error, critical, alert, emergency
```

## Testing patterns

### Exhaustive tool testing

```bash
#!/bin/bash
# Test every tool's schema is valid and callable
SESSION="@exhaustive-test"

for tool in $(mcpc "$SESSION" tools-list --json | jq -r '.[].name'); do
  echo "=== Testing: $tool ==="

  # 1. Schema is retrievable
  SCHEMA=$(mcpc "$SESSION" tools-get "$tool" --json 2>&1)
  if [ $? -ne 0 ]; then
    echo "  FAIL: Cannot get schema"
    continue
  fi
  echo "  ✓ Schema retrieved"

  # 2. Required fields exist
  REQUIRED=$(echo "$SCHEMA" | jq -r '.inputSchema.required // [] | .[]')
  echo "  Required fields: ${REQUIRED:-none}"

  # 3. Check for description
  DESC=$(echo "$SCHEMA" | jq -r '.description // "MISSING"')
  if [ "$DESC" = "MISSING" ]; then
    echo "  WARN: No description"
  else
    echo "  ✓ Description present"
  fi
done
```

### Error handling verification

```bash
# Test with missing required arguments
mcpc @session tools-call my-tool --json 2>&1
# Should return error, not crash

# Test with wrong types
mcpc @session tools-call my-tool count:=not-a-number --json 2>&1
# Should return validation error

# Test with extra arguments
mcpc @session tools-call my-tool known-arg:=val unknown-arg:=val --json 2>&1
# Behavior depends on server: may ignore, may error
```

### Performance baseline

```bash
# Time a tool call
time mcpc @session tools-call fast-tool arg:=value --json > /dev/null

# Compare across runs
for i in $(seq 1 5); do
  time mcpc @session tools-call fast-tool arg:=value --json > /dev/null 2>&1
done
```
