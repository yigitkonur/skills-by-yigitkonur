# Output and scripting

Global flag acceptance does not prove that every handler implements it. The following notes target 0.3.28.

| Flag | Behavior |
|---|---|
| `--output json` | Request JSON; some handlers still print prose or no result. |
| `--output ndjson` | Stream JSON records where implemented; see the `i list` exceptions below. |
| `--compact` | Compact JSON. |
| `--fields a,b.c` | Select fetched object properties, not additional API fields. |
| `--filter k=v` | Client-side filter; also supports `!=` and substring `~=`. |
| `--sort FIELD --order asc\|desc` | Sort arrays on supported output paths. |
| `--format TEMPLATE` | Render fields such as `{{identifier}} {{title}}`. |
| `--id-only` | Implemented by selected mutations such as issue create/update; ignored by `i list`. |
| `--fail-on-empty` | Fail on empty supported list paths. |
| `--dry-run` | Preview supported operations; other handlers can reject it. |
| `--yes` | Confirm supported prompts; no global `-y` alias. |
| `--no-pager`, `--no-cache` | Disable paging or supported cache use. |

Use literal `true`/`false` for boolean environment flags; `1` is rejected by this release's parser:

```bash
export LINEAR_CLI_OUTPUT=json
export LINEAR_CLI_NO_PAGER=true
```

## Handler limits

- `i list --output ndjson` bypasses `--fields`, `--filter`, `--sort`, `--count-only`, and `--fail-on-empty`. Use JSON mode when those transformations matter, or transform the stream with `jq`.
- `i list --count-only` counts fetched rows before client-side output filtering. It is not automatically the complete workspace count.
- `i list` does not fetch descriptions, labels, `updatedAt`, or assignee email. Select them through `i get` or a raw query instead.
- Dot paths traverse objects, not array members: select `labels.nodes`, then map `.labels.nodes[].name` in `jq`.
- `agent --schema` prints output schema metadata. Bare `linear-cli --schema` still fails because the parser requires a subcommand.

## Stdin and IDs

```bash
linear-cli i create "Title" -t ENG -d - < description.md
linear-cli i create "Title" -t ENG --data - < issue.json
linear-cli i update LIN-123 --data - < patch.json
linear-cli api query - < query.graphql
```

Extract list IDs explicitly:

```bash
linear-cli i list -t ENG --limit 25 --output json --fields identifier,title > candidates.json
jq -r '.[].identifier' candidates.json > candidate-ids.txt
```

Inspect the saved target set before passing IDs to a mutation. See `recipes/creating-many-issues.md` for creation and partial-failure handling.

## Pagination

```bash
linear-cli i list --limit 25 --output json
linear-cli i list --all --page-size 50 --output json
linear-cli i list --after CURSOR_TOKEN --output json
```

Pagination is command-specific: global `--all` does not paginate arbitrary GraphQL or every handler. Raw queries require connection variables, nodes and page-info paths; see `advanced.md`. Narrow server-side filters before broad scans.

## Errors and retries

| Exit | Meaning |
|---|---|
| 0 | Handler returned successfully; inspect result/partial failures too. |
| 1 | General error. |
| 2 | Not-found or plain-text parser failure. |
| 3 | Auth failure. |
| 4 | Rate limit. |

Runtime JSON error envelopes go to stderr. Keep stderr separate from stdout, which can contain successful partial results. Codes can be inferred from message text; `details` and `retry_after` may be null. See `json-shapes.md` for shapes and `troubleshooting.md` for a bounded retry that works with `set -e`. Reconcile an ambiguous mutation before retrying it.
