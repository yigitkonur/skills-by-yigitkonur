# Search and Filter

Find issues fast — search, list flags, client-side filter, saved views, favorites, and the chaining patterns to feed results into other commands.

## Free-text search

```bash
linear-cli s issues "authentication bug"
linear-cli s issues "login" --limit 5
linear-cli s issues "crash" --output json --fields identifier,title,state.name

linear-cli s projects "backend"
linear-cli s projects "api" --limit 10 --output json
```

Search is case-insensitive, scans titles and descriptions, and is best for keyword discovery rather than precise filters.

## `i list` flag matrix

```bash
linear-cli i list                                  # everything you can see
linear-cli i list --mine                           # assigned to me
linear-cli i list -t ENG                           # team
linear-cli i list -t ENG --mine
linear-cli i list -s "In Progress"                 # status (workflow state name)
linear-cli i list --assignee "Ada Lovelace"
linear-cli i list --project "Q1 Roadmap"
linear-cli i list --label bug
linear-cli i list --since 7d                       # updated in the last 7 days
linear-cli i list --view "My Sprint"               # apply a saved view
linear-cli i list --group-by state                 # group by state / priority / assignee / project
linear-cli i list --count-only --label bug         # count, no rows
linear-cli i list --archived                       # include archived
```

| Flag | Filter |
|---|---|
| `--mine` | assigned to me |
| `-t TEAM` / `--team` | team key |
| `-s STATE` / `--state` | workflow state name |
| `--assignee NAME` | name or `me` |
| `--project NAME` | project name or ID |
| `--label NAME` | label name (single) |
| `--since DURATION` | `1d`, `7d`, `2w`, etc. |
| `--view NAME` | apply a saved custom view |
| `--group-by FIELD` | `state`, `priority`, `assignee`, `project` |
| `--count-only` | return count, no rows |
| `--archived` | include archived |
| `--limit N` | hard cap |
| `--all` / `--page-size N` / `--after CURSOR` | pagination |

## Client-side `--filter`

Server-side flags are first; `--filter` runs after the API result lands.

```bash
linear-cli i list -t ENG --filter priority=1
linear-cli i list -t ENG --filter "state.name=In Progress"
linear-cli i list -t ENG --filter "assignee.email~=@vendor.com"
linear-cli i list -t ENG --filter "title~=login"
linear-cli i list -t ENG --filter "priority!=4"
```

Operators:

| Op | Meaning |
|---|---|
| `=` | equals (case-insensitive) |
| `!=` | not equals |
| `~=` | substring contains (case-insensitive) |

Dot paths supported (e.g. `state.name`, `assignee.email`).

`--filter` is **client-side** — it does not save API quota. Use the dedicated server-side flags first, then `--filter` for the long tail.

## Output for chaining

```bash
linear-cli i list -t ENG --output json --compact \
  --fields identifier,title,state.name,priority

linear-cli i list -t ENG -s "In Progress" --id-only
linear-cli i list -t ENG --format '{{identifier}} {{state.name}} {{title}}'
```

For bulk mutations, convert `--id-only` output to a comma-separated `-i` value:

```bash
linear-cli i list -t ENG -l stale --id-only \
  | paste -sd, \
  | xargs -I {} linear-cli b update-state "Cancelled" -i {}
```

## Saved views

Saved Linear views encode complex filters once and apply them everywhere.

```bash
linear-cli v list                              # all my views
linear-cli v list --shared                     # shared views only
linear-cli v get "Bug Triage"
linear-cli v create "Open Bugs" -t ENG --shared
linear-cli v update VIEW_ID --name "Open Bugs (P0–P2)"
linear-cli v delete VIEW_ID --force
```

Apply a view to `i list` or `p list`:

```bash
linear-cli i list --view "Bug Triage"
linear-cli p list --view "Active Projects"
```

## Favorites

Personal shortcuts to issues / projects.

```bash
linear-cli fav list
linear-cli fav add LIN-123
linear-cli fav add PROJECT_UUID
linear-cli fav remove LIN-123
```

## Recipe: "show me my urgent in-progress bugs"

```bash
linear-cli i list --mine -s "In Progress" -l bug \
  --filter priority=1 \
  --output json --fields identifier,title,project.name --compact
```

## Recipe: "issues stale > 14 days, group by assignee"

```bash
# Fetch all In Progress issues with updatedAt, then filter client-side
CUTOFF=$(node -e "console.log(new Date(Date.now() - 14*86400000).toISOString())")
linear-cli i list -t ENG -s "In Progress" --output json --all \
  --fields identifier,title,updatedAt,assignee.name \
  | jq ".[] | select(.updatedAt < \"$CUTOFF\")" \
  | jq -rs 'group_by(.assignee.name)[] | {assignee: .[0].assignee.name, issues: map(.identifier)}'
```

## Recipe: "fail CI if there are no open bugs"

```bash
if linear-cli i list -l bug -s "In Progress" --fail-on-empty --quiet; then
  echo "Found open bugs — triage required"
else
  echo "No open bugs — stopping"
  exit 1
fi
```

## Common confusions

| Looks like | Is actually |
|---|---|
| `s issues` | Free-text search across the workspace. |
| `i list` | Filter-based listing. Faster, more precise. |
| `--filter` | Client-side post-filter. |
| `--state` | Server-side state filter. |
| `--view NAME` | Apply a *saved* (server-side) view. |
| `fav` | Personal pinning, not a query. |

## See also

- `output-and-scripting.md` — `--output ndjson`, `--fields`, `--filter` semantics.
- `recipes/creating-many-issues.md` — using `i list --id-only` in idempotency checks.
- `recipes/triage-and-comments.md` — using `s issues` to surface inbound work.
- `planning/teams-and-org.md` — managing the saved views themselves.
