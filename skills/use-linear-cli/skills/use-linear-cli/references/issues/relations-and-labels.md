# Relations, Labels, Statuses, Templates

The "structural" surface around an issue: relations (parent/child/blocks), labels, workflow states, and templates.

## Relations

```bash
linear-cli rel list LIN-123                          # show all relations
linear-cli rel add LIN-1 -r blocks LIN-2             # LIN-1 blocks LIN-2
linear-cli rel add LIN-1 -r related LIN-2            # related (non-directional)
linear-cli rel add LIN-1 -r duplicate LIN-2          # duplicate-of
linear-cli rel remove LIN-1 -r blocks LIN-2          # remove relation
linear-cli rel parent LIN-2 LIN-1                    # set LIN-1 as parent of LIN-2
linear-cli rel unparent LIN-2                        # remove parent
```

### Relation types

| Type | Meaning | Direction |
|---|---|---|
| `blocks` | A blocks B | A → B |
| `blocked-by` | A is blocked by B | A ← B |
| `related` | A is related to B | undirected |
| `duplicate` | A is a duplicate of B | A → B |

`rel parent` is separate — it sets a true parent-child hierarchy used by Linear sub-issue rendering.

### Wiring many sub-issues to one parent

```bash
PARENT=LIN-1
for CHILD in LIN-101 LIN-102 LIN-103; do
  linear-cli rel parent "$CHILD" "$PARENT"
done
```

## Labels

```bash
linear-cli l list                              # list project + team labels
linear-cli l list --type issue                 # issue labels only
linear-cli l list --output json --compact

linear-cli l create "Feature" --color "#10B981"
linear-cli l create "Bug" --color "#EF4444" --id-only

linear-cli l delete LABEL_ID
linear-cli l delete LABEL_ID --force
```

### Apply / remove labels on issues

Already covered in `lifecycle.md` for single issues. Bulk variant:

```bash
linear-cli b label --add bug LIN-1 LIN-2 LIN-3
linear-cli b label --add urgent --add bug LIN-1 LIN-2
```

To remove a label, use the dedicated label delete or `i update` against each issue with the label removed (Linear's API does not currently expose a "remove specific label" bulk; confirm with `linear-cli b label --help` on your binary version).

### Color hex format

`#RRGGBB`. Linear accepts any 6-digit hex. Common semantic palette: `#EF4444` red (bug), `#F59E0B` amber (review), `#10B981` green (done/feature), `#3B82F6` blue (info).

## Statuses (workflow states)

Linear teams have a configurable workflow. Default states: `Backlog`, `Triage`, `In Progress`, `In Review`, `Done`, `Cancelled`.

```bash
linear-cli st list -t ENG                          # all states for the team
linear-cli st list -t ENG --output json --compact
linear-cli st get "In Progress" -t ENG             # one state's details
linear-cli st update STATE_ID --name "Reviewing" --color "#3B82F6"
```

When a team has custom states (e.g. `In Beta`, `Blocked`), confirm names with `st list` before using them in `i update -s ...` — typos return exit 2 (not found).

## Templates

Two flavors:

| Kind | Storage | Sharable | Command prefix |
|---|---|---|---|
| Local | Filesystem (your machine) | No | `linear-cli tpl ...` |
| Remote (Linear API) | Linear workspace | Yes (whole team) | `linear-cli tpl remote-...` |

### Local templates

```bash
linear-cli tpl list
linear-cli tpl show bug
linear-cli tpl create bug                          # interactive
linear-cli tpl delete bug
```

### Remote templates

```bash
linear-cli tpl remote-list
linear-cli tpl remote-list --output json
linear-cli tpl remote-get TEMPLATE_ID
linear-cli tpl remote-create "Bug Report" -t ENG
linear-cli tpl remote-update TEMPLATE_ID --name "Updated"
linear-cli tpl remote-delete TEMPLATE_ID --force
```

### Using a template when creating

```bash
linear-cli i create "Login bug" -t ENG --template "Bug Report"
```

Some binary versions resolve `--template` by ID rather than name — confirm with `linear-cli i create --help`.

## Common confusions

| Looks like | Is actually |
|---|---|
| `rel parent` | Hierarchy (sub-issues). One parent per child. |
| `rel add -r related` | Soft link, undirected. |
| `l create --color` | Color is a hex string, including `#`. |
| `st update` | Renames or recolors a workflow state — affects the whole team. |
| `tpl` | Local templates on your machine. |
| `tpl remote-*` | Linear workspace templates, visible to the whole team. |

## See also

- `issues/lifecycle.md` — applying labels/states during create/update.
- `recipes/creating-many-issues.md` — bulk label batching, parent wiring.
- `output-and-scripting.md` — `--id-only` for capturing label IDs to use in `--data -`.
