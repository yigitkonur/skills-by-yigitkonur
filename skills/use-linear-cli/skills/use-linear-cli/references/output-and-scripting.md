# Output and Scripting

Every agent-relevant flag, exit code, env var, stdin pattern, and chaining recipe for `linear-cli`. This is the single source of truth for `--output`, pagination, and exit-code handling in agent scripts.

## Output flags

| Flag | Purpose |
|---|---|
| `--output json` | Machine-readable JSON. |
| `--output ndjson` | Newline-delimited JSON (stream-friendly). |
| `--compact` | Strip pretty-print whitespace. |
| `--fields a,b,c` | Whitelist fields. Dot paths supported (`state.name`, `labels.nodes.name`). |
| `--sort field` | Sort JSON arrays by field (default: `identifier` / `id`). |
| `--order asc\|desc` | Sort direction. |
| `--filter k=v` | Client-side filter. Operators: `=`, `!=`, `~=` (substring). Dot paths. Case-insensitive. |
| `--format tpl` | Template output, e.g. `"{{identifier}} {{title}}"`. |
| `--id-only` | Emit only the created/updated resource ID. |
| `--quiet` / `-q` | Suppress decoration / progress output. |
| `--fail-on-empty` | Exit non-zero when an array result is empty (great for `set -e` agents). |
| `--no-pager` | Bypass auto-pager (use in CI / agent runs). |
| `--no-cache` | Bypass read-through cache. |
| `--dry-run` | Preview a mutation without writing. |
| `--yes` / `-y` | Auto-confirm interactive prompts. |
| `--no-color` | Strip ANSI color codes (also good for log capture). |
| `--width N` / `--no-truncate` | Table width control. |

## Session defaults

```bash
export LINEAR_CLI_OUTPUT=json     # all commands default to JSON
export LINEAR_CLI_NO_PAGER=1      # no pager
export LINEAR_CLI_YES=1           # auto-confirm prompts (dangerous if mutating; opt in deliberately)
```

## Stdin patterns

| Pattern | Use |
|---|---|
| `linear-cli i create "Title" -t ENG -d -` | Read **description body** from stdin. |
| `linear-cli i create "Title" -t ENG --data -` | Read a **full JSON object** as the issue body. Useful for templated batch creation. |
| `linear-cli i update LIN-123 --data -` | Same JSON-body pattern for updates. |
| `linear-cli api query -` | Read a GraphQL query from stdin. |
| `linear-cli b assign --user me -` | Read whitespace-separated IDs from stdin (combine with `i list --id-only`). |

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

# IDs piped from one command into another
linear-cli i list -t ENG -s "In Progress" --id-only \
  | linear-cli b label --add review
```

## Pagination

```bash
linear-cli i list --limit 25
linear-cli i list --all                        # walk every page
linear-cli i list --all --page-size 100
linear-cli i list --after CURSOR_TOKEN
```

Use `--all` cautiously — large workspaces produce many pages. Prefer narrow filters first.

## Exit codes (contract)

| Code | Meaning | What an agent should do |
|---|---|---|
| 0 | success | continue |
| 1 | general error | parse stderr / JSON error envelope; surface to user |
| 2 | not found | the ID does not exist; do not retry |
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

`retry_after` is non-null when `code == 4`.

Agent retry pattern (rate limit only):

```bash
out=$(linear-cli i list --output json 2>/dev/null)
code=$?
if [ "$code" = 4 ]; then
  sleep "$(echo "$out" | jq -r '.retry_after // 5')"
  out=$(linear-cli i list --output json)
fi
```

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
linear-cli s issues "stale" --output json --fields identifier --compact \
  | jq -r '.[].identifier' \
  | linear-cli b label --add stale -
```

### Fail loudly on empty result

```bash
linear-cli i list --mine --state "In Progress" --fail-on-empty \
  || echo "no work in progress — nothing to report"
```

## Common pitfalls

- `--output json` is per-command; set `LINEAR_CLI_OUTPUT=json` once per session to avoid re-typing.
- `--fields` accepts dot paths but **not** `nodes.*` shorthand — use `labels.nodes.name`.
- `--filter` is *client-side* — it does not reduce API cost. For server-side narrowing, use the dedicated flags (`--state`, `--label`, `--assignee`, `--project`, `--team`, `--since`, `--view`).
- `--id-only` returns just the ID; an empty result still produces empty stdout — check exit code.
- `--dry-run` is supported on create/update/import/bulk/sprint commands. Read each `--help` to confirm.
- `LINEAR_CLI_YES=1` auto-confirms destructive prompts. Use `--force` per-command instead when you want explicit opt-in.

## Pagination + JSON together

```bash
linear-cli i list --all --page-size 100 \
  --output ndjson \
  --fields identifier,title,state.name,priority \
  | jq -s 'sort_by(.priority)'
```

## See also

- `setup.md` for env vars and profile switching.
- `json-shapes.md` for the actual payload shapes you will be parsing.
- `troubleshooting.md` for exit-code-by-exit-code recovery.
- `recipes/creating-many-issues.md` for a worked example using these flags end-to-end.
