# Searching and filtering tools in mcpc

mcpc has no built-in `grep` subcommand. Searching for tools — by name, description, or schema — is done by combining `tools-list --json` with standard UNIX tools (`grep`, `jq`). This page documents every approach, from one-liners to multi-server inventory scripts.

## Why there is no native grep

mcpc follows the principle of one clear way to do things and avoids redundancy. `tools-list --json` emits a JSON array that is fully composable with `jq` for filtering and `grep`/`ripgrep` for text search. Adding a built-in `grep` command would duplicate that capability without adding expressiveness.

The pattern is: **fetch once, filter locally** via standard UNIX pipes.

## The foundation: `tools-list --json`

All search workflows start here.

```bash
# Connect to a server (target BEFORE @session)
mcpc mcp.example.com connect @demo

# Fetch all tools as JSON
mcpc --json @demo tools-list
```

JSON output is a flat array of tool objects:

```json
[
  {
    "name": "search-actors",
    "description": "Search for actors in the Apify store",
    "inputSchema": {
      "type": "object",
      "properties": {
        "query": { "type": "string" },
        "limit": { "type": "number" }
      },
      "required": ["query"]
    }
  }
]
```

Add `--full` to include complete `inputSchema` (properties, required, descriptions). Without `--full`, the schema may be abbreviated.

```bash
mcpc --json @demo tools-list --full
```

## Filtering by name

### Exact name match

```bash
mcpc --json @demo tools-list | jq '.[] | select(.name == "search-actors")'
```

### Name contains substring (case-sensitive)

```bash
mcpc --json @demo tools-list | jq '[.[] | select(.name | test("search"))]'
```

### Name contains substring (case-insensitive)

```bash
mcpc --json @demo tools-list | jq '[.[] | select(.name | test("search"; "i"))]'
```

### Name starts with a prefix

```bash
mcpc --json @demo tools-list | jq '[.[] | select(.name | startswith("get_"))]'
```

### Name matches a regex

```bash
# Tools whose names begin with create, update, or delete
mcpc --json @demo tools-list | jq '[.[] | select(.name | test("^(create|update|delete)_"))]'
```

### Just the matching names (plain text, one per line)

```bash
mcpc --json @demo tools-list | jq -r '[.[] | select(.name | test("actor"))] | .[].name'
```

### Shell grep on names (faster for simple substrings)

```bash
mcpc --json @demo tools-list | jq -r '.[].name' | grep "actor"
```

## Filtering by description

### Description contains a keyword (case-insensitive)

```bash
mcpc --json @demo tools-list | jq '[.[] | select(.description | test("web scraping"; "i"))]'
```

### Multiple keywords (both must match)

```bash
mcpc --json @demo tools-list | jq '[.[] | select(
  (.description | test("scraping"; "i")) and
  (.description | test("proxy"; "i"))
)]'
```

### Either/or keyword search

```bash
mcpc --json @demo tools-list | jq '[.[] | select(
  (.description | test("scraping"; "i")) or
  (.description | test("crawl"; "i"))
)]'
```

### Shell grep on descriptions (multi-line friendly)

```bash
# Returns full tool objects whose description line matches
mcpc --json @demo tools-list | jq -c '.[]' | grep -i '"description".*actor'
```

## Filtering by schema (input parameters)

These patterns require `--full` to ensure `inputSchema.properties` is present.

### Tools that accept a specific parameter name

```bash
mcpc --json @demo tools-list --full | jq '[.[] | select(.inputSchema.properties | has("query"))]'
```

### Tools that require a specific parameter

```bash
mcpc --json @demo tools-list --full | jq '[.[] | select(.inputSchema.required | arrays | index("query") != null)]'
```

### Tools with no required parameters

```bash
mcpc --json @demo tools-list --full | jq '[.[] | select((.inputSchema.required // []) | length == 0)]'
```

### Tools with more than N parameters

```bash
mcpc --json @demo tools-list --full | jq '[.[] | select((.inputSchema.properties // {}) | length > 5)]'
```

### Tools that accept a parameter of a specific type

```bash
# Tools with at least one array-typed parameter
mcpc --json @demo tools-list --full | jq '[.[] | select(
  .inputSchema.properties // {} |
  to_entries | any(.value.type == "array")
)]'
```

### Search parameter names and descriptions

```bash
# Tools with any parameter whose name or description contains "url"
mcpc --json @demo tools-list --full | jq '[.[] | select(
  .inputSchema.properties // {} |
  to_entries | any(
    (.key | test("url"; "i")) or
    ((.value.description // "") | test("url"; "i"))
  )
)]'
```

## Combined name + description search

```bash
# Tools matching "search" in name OR description
mcpc --json @demo tools-list | jq '[.[] | select(
  (.name | test("search"; "i")) or
  ((.description // "") | test("search"; "i"))
)]'

# Show only name and description of matches
mcpc --json @demo tools-list | jq '[.[] | select(
  (.name | test("search"; "i")) or
  ((.description // "") | test("search"; "i"))
)] | .[] | {name, description}'
```

## Output formats for search results

### Names only

```bash
mcpc --json @demo tools-list | jq -r '[.[] | select(.name | test("actor"))] | .[].name'
```

### Name and description table

```bash
mcpc --json @demo tools-list | jq -r '
  [.[] | select(.name | test("actor"))] |
  .[] | "\(.name)\t\(.description // "—")"
' | column -t -s $'\t'
```

### Markdown table

```bash
mcpc --json @demo tools-list | jq -r '
  "| Tool | Description |",
  "| --- | --- |",
  ([.[] | select(.name | test("actor"))] |
    .[] | "| `\(.name)` | \(.description // "—") |")
'
```

### Parameter inventory for matching tools

```bash
mcpc --json @demo tools-list --full | jq '[.[] | select(.name | test("search"))] |
  .[] | {
    name,
    params: (.inputSchema.properties // {} | keys),
    required: (.inputSchema.required // [])
  }'
```

### Count matching tools

```bash
mcpc --json @demo tools-list | jq '[.[] | select(.name | test("actor"))] | length'
```

## How it differs from `tools-list` and `tools-get`

| Capability | `tools-list` | `tools-get <name>` | grep pattern (this page) |
|---|---|---|---|
| Returns all tools | yes | no (one tool) | yes (pre-filtered) |
| Filter by name pattern | no | no (exact match only) | yes |
| Filter by description | no | no | yes |
| Filter by schema fields | no | no | yes (with `--full`) |
| Full schema output | `--full` flag | always | `--full` flag |
| Machine-readable | `--json` flag | `--json` flag | requires `--json` |

`tools-get <name>` is for fetching one known tool's full detail. The grep patterns here are for discovery — finding tools when you don't know the exact name, or when exploring an unfamiliar server.

## Searching across multiple sessions

### Which session has a tool matching a pattern?

```bash
#!/bin/bash
PATTERN="${1:?Usage: $0 <pattern>}"
for session in $(mcpc --json | jq -r '.sessions[] | select(.status == "live") | .name'); do
  MATCHES=$(mcpc --json "@$session" tools-list 2>/dev/null | \
    jq -r "[.[] | select(.name | test(\"$PATTERN\"; \"i\"))] | length")
  if [ "$MATCHES" -gt 0 ]; then
    echo "@$session: $MATCHES match(es)"
    mcpc --json "@$session" tools-list | \
      jq -r "[.[] | select(.name | test(\"$PATTERN\"; \"i\"))] | .[].name" | \
      sed 's/^/  /'
  fi
done
```

### Full inventory across all live sessions

```bash
#!/bin/bash
# Build a JSON map: {session: [tool_names]}
mcpc --json | jq -r '.sessions[] | select(.status == "live") | .name' | \
while read -r session; do
  TOOLS=$(mcpc --json "@$session" tools-list 2>/dev/null | jq '[.[].name]')
  echo "{\"session\": \"$session\", \"tools\": $TOOLS}"
done | jq -s 'map({(.session): .tools}) | add'
```

### Find tools whose description mentions a keyword, across all sessions

```bash
#!/bin/bash
KEYWORD="${1:?Usage: $0 <keyword>}"
for session in $(mcpc --json | jq -r '.sessions[] | select(.status == "live") | .name'); do
  mcpc --json "@$session" tools-list 2>/dev/null | \
    jq -r --arg kw "$KEYWORD" --arg s "@$session" '
      [.[] | select((.description // "") | test($kw; "i"))] |
      .[] | "\($s)  \(.name)  \(.description // "—")"
    '
done
```

## Integration with scripting workflows

### Assert a tool matching a pattern exists (CI guard)

```bash
PATTERN="^search"
COUNT=$(mcpc --json @demo tools-list | jq --arg p "$PATTERN" '[.[] | select(.name | test($p))] | length')
if [ "$COUNT" -eq 0 ]; then
  echo "FAIL: No tool matching /$PATTERN/ found"
  exit 1
fi
echo "OK: $COUNT tool(s) match /$PATTERN/"
```

### Pipe matching tool names into a tool-call loop

```bash
# Call every tool whose name starts with "validate_"
mcpc --json @demo tools-list | jq -r '[.[] | select(.name | startswith("validate_"))] | .[].name' | \
while read -r tool; do
  echo "Calling $tool..."
  mcpc --json @demo tools-call "$tool" --json | jq '.isError // false'
done
```

### Save search results to a file

```bash
mcpc --json @demo tools-list | \
  jq '[.[] | select(.name | test("actor"; "i"))]' > actor-tools.json
```

### Environment variable for reusable pattern

```bash
export TOOL_PATTERN="actor"
mcpc --json @demo tools-list | jq --arg p "$TOOL_PATTERN" '[.[] | select(.name | test($p; "i"))]'
```

### Use `ripgrep` for fast text search on names

```bash
# Fastest option when you just need to know if a tool exists
mcpc --json @demo tools-list | jq -r '.[].name' | rg "actor"
```

## Performance notes

- `tools-list` fetches all pages automatically (mcpc handles `nextCursor` pagination transparently).
- Results are cached in the bridge process (5-minute TTL). Repeated searches within a session do not re-hit the server unless the tool list changes or `--refresh` is triggered by a `notifications/tools/list_changed` event.
- For large tool sets (100+ tools), prefer `jq` over `grep` — jq operates on the parsed JSON structure and handles multi-line descriptions correctly. Shell `grep` on raw JSON can produce false positives if a description contains a newline.
- When searching schemas, always add `--full`; without it, `inputSchema.properties` may be absent or truncated.

## Quick reference

```bash
# Setup
mcpc mcp.example.com connect @demo

# Name contains substring
mcpc --json @demo tools-list | jq '[.[] | select(.name | test("PATTERN"; "i"))]'

# Description contains keyword
mcpc --json @demo tools-list | jq '[.[] | select(.description | test("KEYWORD"; "i"))]'

# Has parameter named X (requires --full)
mcpc --json @demo tools-list --full | jq '[.[] | select(.inputSchema.properties | has("X"))]'

# Names only, one per line
mcpc --json @demo tools-list | jq -r '[.[] | select(.name | test("PATTERN"))] | .[].name'

# Count matches
mcpc --json @demo tools-list | jq '[.[] | select(.name | test("PATTERN"))] | length'

# Close session
mcpc @demo close
```
