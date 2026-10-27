# Issue Lifecycle

Create / update / start / stop / done / move / transfer / archive guide for `linear-cli i ...`. Pairs with `recipes/creating-many-issues.md` and `recipes/git-and-pr-loop.md`.

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
| `-t TEAM` | Team key/name/ID; may fall back to the selected profile default, environment or local template. Resolve the intended team explicitly. |
| `-p N` | Priority — `0` no priority, `1` urgent, `2` high, `3` normal, `4` low |
| `-a USER` | Assignee — `me` or display name or email |
| `-l LABEL` | Label name (repeatable) |
| `--due DATE` | Due date — `today`, `tomorrow`, `+3d`, `+2w`, `monday`, `eow`, `eom`, ISO date |
| `-e N` | Estimate (story points) |
| `-s STATE` | Initial workflow state name/ID |
| `--project PROJECT` | Project name/ID |
| `--template NAME` | Local filesystem template name |
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
linear-cli i update LIN-123 -T "New title"
linear-cli i update LIN-123 -d "New description"
linear-cli i update LIN-123 -s Done                         # status (workflow state name)
linear-cli i update LIN-123 -p 2                            # priority
linear-cli i update LIN-123 -a me
linear-cli i update LIN-123 -a "Ada Lovelace"
linear-cli i update LIN-123 -l bug -l urgent                # replace label set (repeatable)
linear-cli i update LIN-123 --due tomorrow
linear-cli i update LIN-123 -e 3                            # estimate
linear-cli i update LIN-123 --output json
linear-cli i update LIN-123 -s Done --dry-run
cat patch.json | linear-cli i update LIN-123 --data -
```

Use `--due none` to clear a due date and `--project none` to remove a project. `--data` can express explicit nulls/empty arrays where supported by Linear, such as `assigneeId: null` or `labelIds: []`.

`--data -` accepts fields for the corresponding Linear update input. Create-only fields may be invalid. In particular, `labelIds: []` clears labels, while `-l` sets a replacement label list rather than appending. Read and preserve existing labels when adding one.

## Lifecycle transitions

| Action | Command |
|---|---|
| Start work (assign me + In Progress + branch) | `linear-cli i start LIN-123 --checkout` |
| Stop work (backlog, falling back to unstarted) | `linear-cli i stop LIN-123` |
| Stop and unassign | `linear-cli i stop LIN-123 --unassign` |
| Mark Done (any issue) | `linear-cli i update LIN-123 -s Done` |
| Mark Done (current branch) | `linear-cli done` |
| Close (first completed-type workflow state) | `linear-cli i close LIN-123` |
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
linear-cli i get LIN-1 LIN-2 LIN-3              # concurrent per-ID requests
linear-cli i get LIN-123 --output json          # parse-friendly
```

## Common confusions

| Looks like | Is actually |
|---|---|
| `i close` | Selects a completed-type workflow state; it need not be named Done. |
| `i archive` | Removes from default views; preserves history. Reversible via `i unarchive` (when supported). |
| `i delete` | Prompts by default; `--force` skips confirmation. Treat deletion as destructive. |
| `i stop` | Sets backlog (or unstarted), not the previous state. Keeps the assignee unless `--unassign` is passed. |
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
