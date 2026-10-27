# Output and Scripting

Output and shell behavior for 0.3.28. Handlers do not uniformly implement every global flag; verify the specific command before relying on an output contract.

## Output flags

| Flag | Purpose |
|---|---|
| `--output json` | Machine-readable JSON. |
| `--output ndjson` | Newline-delimited JSON (stream-friendly). |
| `--compact` | Strip pretty-print whitespace. |
| `--fields a,b,c` | Select fetched fields; object dot paths such as `state.name` work. Select `labels.nodes` as an array, then map names with `jq`. |
| `--sort field` | Sort JSON arrays by field (default: `identifier` / `id`). |
| `--order asc\|desc` | Sort direction. |
| `--filter k=v` | Client-side filter. Operators: `=`, `!=`, `~=` (substring). Dot paths. Case-insensitive. |
| `--format tpl` | Template output, e.g. `"{{identifier}} {{title}}"`. |
| `--id-only` | Supported by selected mutation handlers such as issue create/update; ignored by `i list`. Extract list identifiers from JSON. |
| `--quiet` / `-q` | Suppress decoration / progress output. |
| `--fail-on-empty` | Exit non-zero when an array result is empty (great for `set -e` agents). |
| `--no-pager` | Bypass auto-pager (use in CI / agent runs). |
| `--no-cache` | Bypass read-through cache. |
| `--dry-run` | Preview supported handlers; unsupported operations may reject it rather than simulate a mutation. |
| `--yes` | Auto-confirm supported interactive prompts. There is no global `-y` alias. |
| `--no-color` | Strip ANSI color codes (also good for log capture). |
| `--width N` / `--no-truncate` | Table width control. |

## Session defaults

```bash
export LINEAR_CLI_OUTPUT=json     # request JSON where supported
export LINEAR_CLI_NO_PAGER=1      # no pager
# Opt into --yes on a specific authorized command rather than setting it session-wide.
```

## Stdin patterns

| Pattern | Use |
|---|---|
| `linear-cli i create "Title" -t ENG -d -` | Read **description body** from stdin. |
| `linear-cli i create "Title" -t ENG --data -` | Read a **full JSON object** as the issue body. Useful for templated batch creation. |
| `linear-cli i update LIN-123 --data -` | Same JSON-body pattern for updates. |
| `linear-cli api query -` | Read a GraphQL query from stdin. |
| `linear-cli i list ... --output json > /tmp/linear-ids.json` | Capture generated ID sets before any bulk mutation; inspect, count, dry-run, then execute against the same IDs. |

Example chains:

```bash
# Description from a file
cat findings.md | linear-cli i create "Investigate prod 500" -t ENG -d -

# Full JSON body
cat <<EOF | linear-cli i create "Bug" -t ENG --data -
{
  "priority": 1,
  "description": "Repro steps...",
  "labelIds": ["LABEL_UUID_1"]
}
EOF

# IDs from one command into a bulk mutation: capture first
linear-cli i list -t ENG -s "In Progress" --limit 25 --output json --compact \
  --fields identifier,title > /tmp/linear-review-ids.json
jq -r '.[] | "\(.identifier)\t\(.title)"' /tmp/linear-review-ids.json
COUNT=$(jq 'length' /tmp/linear-review-ids.json)
IDS=$(jq -r '.[].identifier' /tmp/linear-review-ids.json | paste -sd,)
[ "$COUNT" -gt 0 ] && [ "$COUNT" -le 25 ] || { echo "Unexpected count: $COUNT"; exit 1; }
linear-cli b label review -i "$IDS" --dry-run
if [ "$COUNT" -gt 5 ] && [ "${CONFIRMED_BULK_LINEAR:-}" != 1 ]; then
  echo "Review the dry-run output, then rerun with CONFIRMED_BULK_LINEAR=1 to execute: linear-cli b label review -i \"$IDS\""
  exit 0
fi
linear-cli b label review -i "$IDS"
```

## Handler-specific limits

- `i list --output ndjson` streams raw issue rows and bypasses `--fields`, `--filter`, `--sort`, `--count-only`, and `--fail-on-empty`. Use JSON mode when those transformations matter; use `jq` to transform an NDJSON stream.
- `i list --count-only` counts the fetched set before client-side output filtering, not necessarily every matching workspace issue. Set the intended pagination explicitly.
- `--fields` cannot fetch a property absent from the command's GraphQL selection. `i list` does not fetch `updatedAt`, descriptions, labels, or assignee email. Use `i get` or a raw query when needed.
- Runtime JSON errors go to stderr; parser errors remain plain text. Some commands, including several lifecycle mutations and import, emit prose rather than JSON.
- `linear-cli agent --schema` returns CLI output schema metadata without executing the subcommand. Bare `linear-cli --schema` fails because the parser still requires a subcommand.

## Pagination

```bash
linear-cli i list --limit 25
linear-cli i list --all                        # walk every page
linear-cli i list --all --page-size 100
linear-cli i list --after CURSOR_TOKEN
```

Use `--all` cautiously — large workspaces can produce hundreds of pages. Prefer narrow server-side filters and field selection first (e.g., `-s "In Progress" -t ENG --fields identifier,title`). Linear query complexity is multiplied by pagination size for connection fields, so do not blindly raise `--page-size`. Use the default or `50`-`100` for broad scans; only raise page size after checking the payload shape is narrow enough.

## Exit codes (contract)

| Code | Meaning | What an agent should do |
|---|---|---|
| 0 | command returned successfully | inspect results too; import may report per-item failures on stderr |
| 1 | general error | parse stderr / JSON error envelope; surface to user |
| 2 | not found or parser error | If JSON with `details.status: 404`, the ID/object does not exist; do not retry. If plain stderr/usage text, fix the command syntax via `--help`. |
| 3 | auth error | route to `setup.md` and re-auth |
| 4 | rate limited | sleep `retry_after` seconds (in JSON body), retry once |

JSON error envelope (when `--output json` is set on a failing command):

```json
{
  "error": true,
  "message": "Issue not found: LIN-999",
  "code": 2,
  "details": { "status": 404, "reason": "Not Found", "request_id": null },
  "retry_after": null
}
```

`retry_after` may be null even for rate limits; use a bounded fallback.

Parser errors can also exit 2. Regression check:

```bash
set +e
out=$(linear-cli i list --state 2>&1)
code=$?
set -e
test "$code" = 2
printf '%s\n' "$out" | grep -E "value is required|Usage:|unexpected argument"
```

For a retry example that preserves stdout/stderr and works with `set -e`, see `troubleshooting.md`. Never retry a mutation blindly after an ambiguous network failure.

## Chaining recipes

### Capture an ID for later commands

```bash
ID=$(linear-cli i create "Bug" -t ENG --id-only --quiet)
linear-cli rel parent "$ID" LIN-100
linear-cli i update "$ID" -l bug -p 1
```

### Field-selected JSON for token efficiency

```bash
linear-cli i list -t ENG --output json --compact \
  --fields identifier,title,state.name,assignee.name
```

### Group + count (no JSON parsing needed)

```bash
linear-cli i list -t ENG --group-by state --count-only
```

### Streaming many results

```bash
linear-cli i list --all --output ndjson \
  | jq -r 'select(.priority == 1) | .identifier'
```

### Templates for one-line summaries

```bash
linear-cli i list -t ENG --format '{{identifier}} {{state.name}} {{title}}'
```

### Pipe IDs into a bulk mutation

```bash
linear-cli s issues "stale" --limit 25 --output json --fields identifier,title --compact \
  > /tmp/linear-stale-issues.json
jq -r '.[] | "\(.identifier)\t\(.title)"' /tmp/linear-stale-issues.json
COUNT=$(jq 'length' /tmp/linear-stale-issues.json)
IDS=$(jq -r '.[].identifier' /tmp/linear-stale-issues.json | paste -sd,)
[ "$COUNT" -gt 0 ] && [ "$COUNT" -le 25 ] || { echo "Unexpected count: $COUNT"; exit 1; }
linear-cli b label stale -i "$IDS" --dry-run
if [ "$COUNT" -gt 5 ] && [ "${CONFIRMED_BULK_LINEAR:-}" != 1 ]; then
  echo "Review the dry-run output, then rerun with CONFIRMED_BULK_LINEAR=1 to execute: linear-cli b label stale -i \"$IDS\""
  exit 0
fi
linear-cli b label stale -i "$IDS"
```

### Fail loudly on empty result

```bash
linear-cli i list --mine --state "In Progress" --fail-on-empty \
  || echo "no work in progress — nothing to report"
```

## Common pitfalls

- `--output json` is per-command; set `LINEAR_CLI_OUTPUT=json` once per session to avoid re-typing.
- `--fields` traverses object keys only. Use `labels.nodes`, then `jq` to map names inside the array.
- `--filter` is *client-side* — it does not reduce API cost. For server-side narrowing, use the dedicated flags (`--state`, `--label`, `--assignee`, `--project`, `--team`, `--since`, `--view`).
- `--id-only` returns just the ID; an empty result still produces empty stdout — check exit code.
- `--dry-run` support differs by operation. Verify behavior for the specific command. Import preview does not resolve status, assignee, or label names.
- `LINEAR_CLI_YES=1` auto-confirms destructive prompts. Use `--force` per-command instead when you want explicit opt-in.

## Pagination + JSON together

```bash
linear-cli i list --all --page-size 100 \
  --output ndjson \
  | jq -s 'map({identifier,title,state,priority}) | sort_by(.priority)'
```

## See also

- `setup.md` for env vars and profile switching.
- `json-shapes.md` for the actual payload shapes you will be parsing.
- `troubleshooting.md` for exit-code-by-exit-code recovery.
- `recipes/creating-many-issues.md` for a worked example using these flags end-to-end.
