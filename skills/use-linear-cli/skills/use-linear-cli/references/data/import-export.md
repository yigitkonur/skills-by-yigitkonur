# Import and Export

Round-trip Linear data through CSV, JSON, and Markdown. Use for migrations, bulk creation from spreadsheets, archival snapshots, and external reporting.

## Export

```bash
linear-cli exp csv -t ENG                          # human-friendly
linear-cli exp csv -t ENG -f issues.csv            # to file
linear-cli exp csv --all -t ENG                    # paginate every page
linear-cli exp csv -t ENG -s "In Progress"
linear-cli exp csv -t ENG --assignee me

linear-cli exp markdown -t ENG
linear-cli exp markdown -t ENG -f issues.md

linear-cli exp json -t ENG -f backup.json          # round-trip-compatible
linear-cli exp projects-csv -f projects.csv
```

| Flag | Meaning |
|---|---|
| `-f FILE` | Output to file (otherwise stdout) |
| `--all` | Walk every page |
| `-t TEAM` | Filter by team |
| `-s STATE` | Filter by state |
| `--assignee USER` | Filter by assignee |

## Import

```bash
linear-cli im csv issues.csv -t ENG
linear-cli im csv issues.csv -t ENG --dry-run        # always preview first
linear-cli im json issues.json -t ENG
linear-cli im json backup.json -t ENG --dry-run
```

| Flag | Meaning |
|---|---|
| `-t TEAM` (req) | Target team |
| `--dry-run` | Preview without creating |
| `--output json` | Return created issues as JSON |

## CSV column schema

Header row required.

| Column | Required | Notes |
|---|---|---|
| `title` | yes | Plain string |
| `description` | no | Markdown body; can contain `\n` for multi-line |
| `priority` | no | `0`–`4` (0=no priority, 1=urgent, 4=low) |
| `status` | no | Workflow state name (resolved by name in the team) |
| `assignee` | no | User name or email (resolved by name) |
| `labels` | no | `;`-separated list, names (resolved by name) |
| `estimate` | no | Story points (integer) |
| `dueDate` | no | ISO date `YYYY-MM-DD` |

Example:

```csv
title,description,priority,status,assignee,labels,estimate,dueDate
Fix login redirect,"Multi-line\ndescription",1,Backlog,ada@example.com,bug;auth,3,2026-05-01
Add 429 retry headers,"",2,Backlog,,api,2,
```

### Name resolution

`status`, `assignee`, and `labels` are resolved by name within the target team. If a name doesn't match, the row fails with exit 2 (not found). Always run `--dry-run` first to surface name-resolution errors before writing.

## JSON round-trip

```bash
linear-cli exp json -t ENG -f backup.json
# … edit backup.json …
linear-cli im json backup.json -t ENG --dry-run
linear-cli im json backup.json -t ENG
```

JSON is round-trip compatible: an export → import recreates issues with the same titles, descriptions, labels, etc. (but new IDs and identifiers — Linear does not allow you to set those manually).

## Markdown export

Best for human-readable archives or pasting a summary into a doc.

```bash
linear-cli exp markdown -t ENG --since 30d -f sprint-archive.md
```

## Recipe: migrate from another tracker (CSV-driven)

1. Export from the source tool to CSV.
2. Map columns to the schema above. Multi-value cells (labels, etc.) need `;` separation.
3. Map status names to your Linear team's workflow states (use `linear-cli st list -t ENG`).
4. Run `linear-cli im csv migration.csv -t ENG --dry-run` until it reports zero name-resolution failures.
5. Commit: `linear-cli im csv migration.csv -t ENG`.

## Recipe: weekly archive

```bash
DATE=$(date +%Y-%m-%d)
linear-cli exp json -t ENG -f "archives/$DATE.json"
linear-cli exp markdown -t ENG -f "archives/$DATE.md"
```

## Recipe: round-trip edits

When the upstream tool isn't programmatically editable but Linear is, export, edit programmatically, re-import.

```bash
linear-cli exp json -t ENG -f stale.json
jq '.[] | select(.priority == 4) | .priority = 3' stale.json > bumped.json
linear-cli im json bumped.json -t ENG --dry-run
```

## Common confusions

| Looks like | Is actually |
|---|---|
| `exp` | Export |
| `im` | Import |
| `--dry-run` (on import) | No writes; reports name-resolution outcome. |
| `dueDate` (CSV) | ISO `YYYY-MM-DD` only — no `+3d` shortcuts inside CSV cells. |
| `labels` (CSV) | `;`-separated; not `,`. |

## See also

- `recipes/creating-many-issues.md` — full CSV/JSON-driven creation patterns.
- `issues/lifecycle.md` — `--data -` JSON shape for one-off creates.
- `output-and-scripting.md` — `--dry-run`, `--output json` plumbing.
