# Issue Lifecycle

Full create / update / start / stop / done / move / transfer / archive flag matrix for `linear-cli i ...`. Pairs with `recipes/creating-many-issues.md` and `recipes/git-and-pr-loop.md`.

## Create

```bash
linear-cli i create "Title" -t TEAM
linear-cli i create "Bug" -t ENG -p 1 -a me -l bug -l urgent --due +3d
linear-cli i create "Task" -t ENG --id-only --quiet         # capture ID
linear-cli i create "Test" -t ENG --dry-run                 # preview
cat desc.md  | linear-cli i create "Title" -t ENG -d -      # description body from stdin
cat body.json | linear-cli i create "Title" -t ENG --data - # full JSON body
```

### Create flag matrix

| Flag | Meaning |
|---|---|
| `-t TEAM` (req) | Team key (e.g. `ENG`) |
| `-p N` | Priority — `0` no priority, `1` urgent, `2` high, `3` normal, `4` low |
| `-a USER` | Assignee — `me` or display name or email |
| `-l LABEL` | Label name (repeatable) |
| `--due DATE` | Due date — `today`, `tomorrow`, `+3d`, `+2w`, `monday`, `eow`, `eom`, ISO date |
| `-e N` | Estimate (story points) |
| `-d -` | Description body from stdin |
| `--data -` | Full JSON object from stdin |
| `--id-only` | Output only the new ID |
| `--quiet` | Suppress decoration |
| `--dry-run` | Preview without writing |

### Priority values

| Value | Meaning |
|---|---|
| 0 | No priority |
| 1 | Urgent |
| 2 | High |
| 3 | Normal |
| 4 | Low |

### Due date shortcuts

`today`, `tomorrow`, `+3d`, `+2w`, `monday`, `eow` (end of week), `eom` (end of month), or any ISO date `YYYY-MM-DD`.

### `--data -` JSON shape

```json
{
  "description": "Full markdown body...",
  "priority": 1,
  "stateId": "WORKFLOW_STATE_UUID",
  "assigneeId": "USER_UUID",
  "labelIds": ["LABEL_UUID_1", "LABEL_UUID_2"],
  "estimate": 3,
  "dueDate": "2026-05-01",
  "parentId": "PARENT_ISSUE_UUID",
  "projectId": "PROJECT_UUID"
}
```

Use this when name-resolution would be ambiguous (multiple labels with the same name, two assignees with the same display name, etc.).

## Update

```bash
linear-cli i update LIN-123 -s Done                         # status (workflow state name)
linear-cli i update LIN-123 -p 2                            # priority
linear-cli i update LIN-123 -a me
linear-cli i update LIN-123 -a "Ada Lovelace"
linear-cli i update LIN-123 -l bug -l urgent                # add labels (repeatable)
linear-cli i update LIN-123 --due tomorrow
linear-cli i update LIN-123 -e 3                            # estimate
linear-cli i update LIN-123 --output json
linear-cli i update LIN-123 -s Done --dry-run
cat patch.json | linear-cli i update LIN-123 --data -
```

`--data -` accepts the same JSON shape as create.

## Lifecycle transitions

| Action | Command |
|---|---|
| Start work (assign me + In Progress + branch) | `linear-cli i start LIN-123 --checkout` |
| Stop work (unassign + reset) | `linear-cli i stop LIN-123` |
| Mark Done (any issue) | `linear-cli i update LIN-123 -s Done` |
| Mark Done (current branch) | `linear-cli done` |
| Close (alias for Done) | `linear-cli i close LIN-123` |
| Assign | `linear-cli i assign LIN-123 "Alice"` |
| Move to a project | `linear-cli i move LIN-123 "Q2 Project"` |
| Transfer to a different team | `linear-cli i transfer LIN-123 ENG` |
| Archive | `linear-cli i archive LIN-123` |
| Open in browser | `linear-cli i open LIN-123` |
| Print URL | `linear-cli i link LIN-123` |
| Delete | `linear-cli i delete LIN-123 --force` |

## Comment shortcut on the issue itself

```bash
linear-cli i comment LIN-123 -b "LGTM"     # equivalent to `linear-cli cm create LIN-123 -b ...`
```

For full comment CRUD see the comments section in `recipes/triage-and-comments.md`.

## Get with extra context

```bash
linear-cli i get LIN-123                        # full body
linear-cli i get LIN-123 --history              # activity timeline inline
linear-cli i get LIN-123 --comments             # inline comments
linear-cli i get LIN-1 LIN-2 LIN-3              # batch fetch — one API call
linear-cli i get LIN-123 --output json          # parse-friendly
```

## Common confusions

| Looks like | Is actually |
|---|---|
| `i close` | Alias for `i update -s Done`. |
| `i archive` | Removes from default views; preserves history. Reversible via `i unarchive` (when supported). |
| `i delete` | Hard delete — irreversible. Requires `--force`. |
| `i stop` | Inverse of `i start`. Does not revert recent edits. |
| `i transfer` | Moves the issue to a different team key (and re-numbers). |
| `i move` | Moves the issue to a project; team unchanged. |
| `i comment` | One-liner sugar for `cm create`. |

## See also

- `recipes/creating-many-issues.md` — bulk creation patterns using the flags above.
- `recipes/git-and-pr-loop.md` — `i start --checkout` deep dive.
- `issues/relations-and-labels.md` — wiring relations after create.
- `issues/search-and-filter.md` — finding issues to update.
- `output-and-scripting.md` — `--id-only`, `--dry-run`, `--data -` patterns.
- `json-shapes.md` — the `i get` payload.
