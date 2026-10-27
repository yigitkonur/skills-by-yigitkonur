# Import and Export

Export and import Linear data through CSV or JSON, and export Markdown. Import creates new issues; it does not update existing issues or preserve every field.

## Export

```bash
linear-cli exp csv -t ENG                          # human-friendly
linear-cli exp csv -t ENG -f issues.csv            # to file
linear-cli exp csv --all -t ENG                    # paginate every page
linear-cli exp csv -t ENG --include-completed
linear-cli exp csv -t ENG --limit 100

linear-cli exp markdown -t ENG
linear-cli exp markdown -t ENG -f issues.md

linear-cli exp json -t ENG -f backup.json          # export, not a full-fidelity backup
linear-cli exp projects-csv -f projects.csv
```

| Flag | Meaning |
|---|---|
| `-f FILE` | Output to file (otherwise stdout) |
| `--all` | Walk every page |
| `-t TEAM` | Filter by team |
| `--include-completed` | Include completed issues |
| `--limit N` | Limit number of issues |

Export commands do not accept issue-list filters like `-s`, `--assignee`, or `--since`. For filtered subsets, use `i list --output json` and shape the export with `jq` / CSV tooling.

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
| `--output json` | Import progress and results are written to stderr in 0.3.28; do not assume a JSON result array. |

## CSV column schema

Header row required.

| Column | Required | Notes |
|---|---|---|
| `title` | yes | Plain string |
| `description` | no | Markdown; quoted CSV fields can contain actual newlines. A literal `\n` is not decoded into a newline. |
| `priority` | no | `0`–`4` (0=no priority, 1=urgent, 4=low) |
| `status` | no | Workflow state name (resolved by name in the team) |
| `assignee` | no | User name or email (resolved by name) |
| `labels` | no | Comma-separated label names inside one CSV cell; quote the cell when using multiple labels. |
| `estimate` | no | Story points (integer) |
| `dueDate` | no | ISO date `YYYY-MM-DD` |

Example:

```csv
title,description,priority,status,assignee,labels,estimate,dueDate
Fix login redirect,"Multi-line\ndescription",1,Backlog,ada@example.com,"bug,auth",3,2026-05-01
Add 429 retry headers,"",2,Backlog,,api,2,
```

### Name resolution

In 0.3.28 the dry run resolves the team but does not resolve status, assignee, or label names. The real import attempts name resolution; on failure it warns and can create the issue without that field. Check each name independently before importing. Rows without titles are skipped. Per-item create failures are reported on stderr, but the import can still exit 0: reconcile results and inspect stderr rather than trusting the exit code.

## JSON export and import

```bash
linear-cli exp json -t ENG -f backup.json
# … edit backup.json …
linear-cli im json backup.json -t ENG --dry-run
linear-cli im json backup.json -t ENG
```

JSON export contains fields that import does not apply. Import creates new issues with new IDs; it does not update the originals or preserve all relationships and metadata. Check and map the fields supported by the installed version before importing.

## Markdown export

Best for human-readable archives or pasting a summary into a doc.

```bash
linear-cli exp markdown -t ENG --all -f sprint-archive.md
```

## Recipe: migrate from another tracker (CSV-driven)

1. Export from the source tool to CSV.
2. Map columns to the schema above. Multi-value cells (labels, etc.) need comma separation inside a quoted CSV cell.
3. Map status names to your Linear team's workflow states (use `linear-cli st list -t ENG`).
4. Run `linear-cli im csv migration.csv -t ENG --dry-run` to inspect rows. Independently verify all status, assignee, and label names; preview does not resolve them.
5. Commit: `linear-cli im csv migration.csv -t ENG`.

## Recipe: weekly archive

```bash
DATE=$(date +%Y-%m-%d)
linear-cli exp json -t ENG -f "archives/$DATE.json"
linear-cli exp markdown -t ENG -f "archives/$DATE.md"
```

## Recipe: create new issues from edited export

This creates new issues; it does not edit the exported issues. For changes to existing issues, use `i update` or a supported bulk command instead.

```bash
linear-cli exp json -t ENG -f stale.json
# Modify matching entries while preserving the import array shape
jq 'map(if .priority == 4 then .priority = 3 else . end)' stale.json > bumped.json
linear-cli im json bumped.json -t ENG --dry-run
```

## Common confusions

| Looks like | Is actually |
|---|---|
| `exp` | Export |
| `im` | Import |
| `--dry-run` (on import) | Previews parsed rows after resolving the team; does not validate other names. |
| `dueDate` (CSV) | Passed through the CLI date parser; verify accepted input with your installed version. |
| `labels` (CSV) | Comma-separated names inside one quoted CSV cell. |

## See also

- `recipes/creating-many-issues.md` — full CSV/JSON-driven creation patterns.
- `issues/lifecycle.md` — `--data -` JSON shape for one-off creates.
- `output-and-scripting.md` — `--dry-run`, `--output json` plumbing.
