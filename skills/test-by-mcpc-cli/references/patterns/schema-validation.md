# Schema validation in mcpc

Schema validation lets you compare a tool's live `inputSchema` (and `outputSchema`) against a
previously saved JSON file before—or instead of—executing a call. It catches breaking API changes
early, powers regression suites, and documents exactly which fields your integration depends on.

## How validation fits into a tool call

```
mcpc @session tools-call tool-name [args] --schema file.json --schema-mode strict
```

Before forwarding the call to the MCP server, mcpc fetches the tool's schema via `tools/get`,
loads `file.json`, and compares the two. If the comparison fails, the call is aborted with exit
code 1 and a structured error listing every mismatch. Warnings are printed but do not block
execution.

---

## Three validation modes

### ignore

```bash
mcpc @session tools-call my-tool arg:=value --schema-mode ignore
```

Skips all schema comparison. Equivalent to running without `--schema`. Useful as an explicit
no-op in scripts where the flag is set conditionally.

---

### compatible (default)

```bash
mcpc @session tools-call my-tool arg:=value --schema file.json
# --schema-mode compatible is the default when --schema is given
```

Focuses on whether **this specific call** will succeed. The logic applied by the validator:

**Input schema checks (errors — block the call):**
- A field you are passing no longer exists in the live schema.
- A field you are passing changed its `type`.
- The live schema added a new `required` field that you are not passing.
- An expected property is missing from the live schema entirely (when no args are passed, all
  expected properties are checked).
- A previously required field is no longer required (contract weakened).

**Input schema notes (warnings — do not block):**
- Description text changed.
- A new optional field appeared in the live schema.

**Output schema checks (errors):**
- A field the saved schema expected to receive was removed from the live output schema.
- A field's type changed.

**Output schema notes (warnings):**
- A field changed from required to optional (or vice-versa).
- New output fields appeared (more data than before — fine for the caller).

Compatible mode intentionally ignores optional input fields you are not using. A tool can gain
ten new optional parameters without breaking your existing call.

---

### strict

```bash
mcpc @session tools-call my-tool arg:=value --schema file.json --schema-mode strict
```

Every part of the schema must match exactly via deep equality:

- Tool name must match.
- Description must match exactly.
- `inputSchema` must be byte-for-byte equivalent (same properties, same types, same required
  array, same order-independent key set).
- `outputSchema` must be byte-for-byte equivalent.

Any deviation — including an added optional field or a rephrased description — is an error. Use
strict mode for locked-down regression tests where the contract must be frozen.

---

## Schema file format

Schema files are plain JSON. The expected structure mirrors the MCP `tools/get` response object:

```json
{
  "name": "search-actors",
  "description": "Search for Apify actors by keyword.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": { "type": "string" },
      "limit": { "type": "number" }
    },
    "required": ["query"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "actors": { "type": "array" },
      "total":  { "type": "number" }
    },
    "required": ["actors"]
  }
}
```

Both `inputSchema` and `outputSchema` are optional in the file. If only `inputSchema` is
present, only input is validated (and vice-versa).

---

## Getting a tool's schema

Capture the live schema and save it as the baseline:

```bash
# Full tool object (name + description + inputSchema + outputSchema)
mcpc --json @session tools-get search-actors > schemas/search-actors.json

# Extract only the inputSchema for inspection
mcpc --json @session tools-get search-actors | jq '.inputSchema'

# Extract and pretty-print required fields
mcpc --json @session tools-get search-actors | jq '.inputSchema.required'

# List all tools and dump their schemas in one pass
mcpc --json @session tools-list | jq '.[] | {name, inputSchema}' > schemas/all-tools.jsonl
```

---

## Practical examples

### Saving schemas for regression testing

Run once against a known-good server version to create baselines:

```bash
mkdir -p schemas/v1
for tool in $(mcpc --json @session tools-list | jq -r '.[].name'); do
  mcpc --json @session tools-get "$tool" > "schemas/v1/${tool}.json"
done
```

### Validating a specific tool call

```bash
mcpc @session tools-call search-actors query:="web scraper" \
  --schema schemas/v1/search-actors.json \
  --schema-mode compatible
```

Exit code 0 means the live schema is compatible with your saved baseline and the call proceeded.
Exit code 1 means validation failed; the call was not made.

### Schema-only check without running the tool

Use `tools-get` plus `diff` to compare schemas without making a live call:

```bash
# Capture live schema
mcpc --json @session tools-get search-actors > /tmp/live-search-actors.json

# Diff against baseline
diff <(jq --sort-keys . schemas/v1/search-actors.json) \
     <(jq --sort-keys . /tmp/live-search-actors.json)
```

A clean diff means no schema change. Any output signals a potential breaking change to
investigate before running tests.

### Building a schema test suite

Create a shell script that validates every tool against its saved baseline:

```bash
#!/usr/bin/env bash
# scripts/validate-schemas.sh
set -euo pipefail

SESSION="${1:?Usage: validate-schemas.sh @session}"
SCHEMA_DIR="schemas/v1"
FAILED=0

for schema_file in "$SCHEMA_DIR"/*.json; do
  tool_name=$(jq -r '.name' "$schema_file")
  echo "Checking $tool_name..."

  # Use tools-get to fetch live and compare; abort on mismatch
  live=$(mcpc --json "$SESSION" tools-get "$tool_name")
  expected=$(cat "$schema_file")

  # Strict diff: sorted keys, ignore whitespace
  if ! diff -q \
    <(echo "$expected" | jq --sort-keys .) \
    <(echo "$live"     | jq --sort-keys .) > /dev/null 2>&1; then
    echo "  CHANGED: $tool_name"
    diff <(echo "$expected" | jq --sort-keys .) \
         <(echo "$live"     | jq --sort-keys .)
    FAILED=$((FAILED + 1))
  else
    echo "  OK: $tool_name"
  fi
done

echo ""
echo "Results: $(($(ls "$SCHEMA_DIR"/*.json | wc -l) - FAILED)) passed, $FAILED changed"
exit $FAILED
```

Run with `./scripts/validate-schemas.sh @staging`.

### CI integration

```yaml
# .github/workflows/schema-regression.yml
name: Schema regression

on:
  schedule:
    - cron: "0 6 * * *"   # daily at 06:00 UTC
  workflow_dispatch:

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install mcpc
        run: npm install -g mcpc

      - name: Start session
        run: mcpc "${{ secrets.MCP_SERVER_URL }}" connect @ci
        env:
          APIFY_TOKEN: ${{ secrets.APIFY_TOKEN }}

      - name: Validate all tool schemas
        run: ./scripts/validate-schemas.sh @ci

      - name: Teardown session
        if: always()
        run: mcpc @ci close
```

To validate a tool call as part of a test job:

```yaml
      - name: Call search-actors with schema guard
        run: |
          mcpc @ci tools-call search-actors query:="test" \
            --schema schemas/v1/search-actors.json \
            --schema-mode strict
```

---

## Diff-based schema change detection

Keep schemas under version control. When a server is upgraded, regenerate baselines in a
branch and open a PR — the diff becomes the official schema changelog:

```bash
# Regenerate all baselines after a server upgrade
for tool in $(mcpc --json @session tools-list | jq -r '.[].name'); do
  mcpc --json @session tools-get "$tool" | jq --sort-keys . \
    > "schemas/v2/${tool}.json"
done

# See what changed
git diff schemas/
```

Reviewing the PR diff surfaces:
- New required fields (breaking for callers who do not pass them).
- Removed fields (breaking for callers who depend on them).
- Type changes (almost always breaking).
- New optional fields (safe additive change).
- Description-only changes (informational).

---

## Common validation errors and fixes

| Error message | Cause | Fix |
|---|---|---|
| `New required field "X" added (breaking change)` | Server made a formerly optional field required. | Pass `X` in your call, or update your baseline after verifying the new requirement. |
| `Argument "X" no longer exists in schema` | Server removed or renamed a field you are passing. | Remove `X` from the call, or find the renamed replacement in the live schema. |
| `Argument "X" type changed: expected "string", got "number"` | Field type changed. | Update your call to pass the correct type, then save a new baseline. |
| `Property "X" is missing from input schema` | Expected property disappeared (compatible mode, no args passed). | Check if the tool was renamed; update baseline if the removal is intentional. |
| `Input schema was removed` | Tool no longer declares an `inputSchema`. | Inspect the live tool; may be a server regression or tool redesign. |
| `Output field "X" was removed (caller expects this field)` | A field your saved schema expected in the response is gone. | Update downstream code that reads `X`, then save a new baseline. |
| `Output field "X" type changed` | Response field type changed. | Fix consumers of that field, then update baseline. |
| `Schema file not found: path/to/file.json` | Path typo or missing baseline file. | Run `mcpc --json @session tools-get tool-name > path/to/file.json` to create it. |
| `Invalid JSON in schema file: path/to/file.json` | Corrupted or hand-edited schema file. | Re-capture with `tools-get` or fix the JSON syntax error. |
| `Description mismatch` (strict mode) | Server updated the tool description. | If intentional, re-capture baseline. If unexpected, flag for review. |
| `Arguments do not match exactly` (strict mode, prompts) | Any structural change to a prompt's argument list. | Re-capture baseline or switch to compatible mode if description-only changes are acceptable. |
