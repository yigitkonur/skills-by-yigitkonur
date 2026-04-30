# Recipe — Creating Many Issues at Once

End-to-end patterns for "I have a spec / checklist / CSV / JSON, create N Linear issues from it." This is the single hottest agent workflow and the reason most agents reach for `linear-cli`.

## Decision: which pattern?

| Input shape | Pattern |
|---|---|
| Markdown checklist (`- [ ] item`) or bullet list | A — Loop with `i create --id-only` |
| CSV with title/description/priority columns | B — `im csv` (preview then commit) |
| JSON spec with structured per-issue fields | C — `i create --data -` per row |
| You'll re-use this issue shape many times | D — Local or remote template + `i create --template` |
| Issues are children of one parent / linked together | E — Pattern A or C + `rel parent` |
| Long list pre-existing in another tracker | F — Convert to CSV, run B |

## Setup gate (do this first, every time)

```bash
linear-cli auth status                              # exit 0 required
TEAM=ENG                                            # team key
linear-cli t get "$TEAM" --output json --fields id,key,name   # confirm team exists
export LINEAR_CLI_OUTPUT=json
export LINEAR_CLI_NO_PAGER=1
```

## Pattern A — Markdown checklist → many issues

### Input

```markdown
# TODO

- [ ] Replace deprecated auth middleware
- [ ] Add rate-limit headers to public endpoints
- [ ] Backfill audit log for 2025
```

### Recipe

```bash
TEAM=ENG
PARENT=LIN-1                  # optional umbrella issue
mapfile -t TITLES < <(grep -E '^- \[ \] ' TODO.md | sed -E 's/^- \[ \] //')

# Dry-run preview
for t in "${TITLES[@]}"; do
  linear-cli i create "$t" -t "$TEAM" --dry-run
done

# Commit + capture IDs
CREATED=()
for t in "${TITLES[@]}"; do
  ID=$(linear-cli i create "$t" -t "$TEAM" -p 3 --id-only --quiet) || break
  CREATED+=("$ID")
done

# Wire to a parent issue (optional)
for ID in "${CREATED[@]}"; do
  linear-cli rel parent "$ID" "$PARENT"
done

# Batch label
IDS=$(IFS=,; echo "${CREATED[*]}")
linear-cli b label backlog -i "$IDS"

# Report
printf 'Created %d issues:\n' "${#CREATED[@]}"
printf '  %s\n' "${CREATED[@]}"
```

### Atomicity note

There is **no transactional create**. If item 7/12 fails, items 1–6 are already in Linear. Three mitigations:

1. **Always dry-run first** to confirm titles, team, priority.
2. **Capture IDs as you go** so you can roll back with `b update-state "Cancelled" -i "$IDS"` or `i archive`.
3. **Set a single batch label** (e.g. `b label batch:2026-04-28 -i "$IDS"`) so you can find every issue from the run later.

## Pattern B — CSV import

### Input

`issues.csv`:

```csv
title,description,priority,status,assignee,labels,estimate,dueDate
Fix login redirect,"Multi-line\ndescription",1,Backlog,ada@example.com,"bug,auth",3,2026-05-01
Add 429 retry headers,"",2,Backlog,,api,2,
```

`status`, `assignee`, and `labels` resolve by name automatically. Multi-value label cells use comma separation inside a quoted CSV cell.

### Recipe

```bash
TEAM=ENG

# 1. Preview — surface name resolution failures before committing
linear-cli im csv issues.csv -t "$TEAM" --dry-run

# 2. Commit
linear-cli im csv issues.csv -t "$TEAM" --output json

# Output is a JSON array of created issue objects (see json-shapes.md).
```

### Round-trip

Export → tweak → re-import:

```bash
linear-cli exp json -t "$TEAM" -f backup.json
# … edit backup.json …
linear-cli im json backup.json -t "$TEAM" --dry-run
linear-cli im json backup.json -t "$TEAM"
```

CSV columns are documented in `data/import-export.md`.

## Pattern C — JSON spec, one create per row

Use when each issue needs distinct rich fields (description body, parent issue, label IDs).

### Input

`plan.ndjson`:

```ndjson
{"title":"Replace auth mw","description":"…","priority":1,"labelIds":["LBL_UUID"],"parentId":"PARENT_UUID"}
{"title":"Add rate headers","description":"…","priority":2}
```

### Recipe

```bash
TEAM=ENG
while IFS= read -r row; do
  title=$(jq -r '.title' <<<"$row")
  ID=$(printf '%s' "$row" \
    | linear-cli i create "$title" -t "$TEAM" --data - --id-only --quiet) \
    || { echo "FAIL: $title" >&2; break; }
  echo "$ID"
done < plan.ndjson
```

`--data -` reads a full JSON object. Combine with `--id-only` to capture the new identifier.

## Pattern D — Templates

When the same issue shape recurs (post-mortem, RFC, bug, customer-onboarding), define a template and reuse it.

### Local template (filesystem only)

```bash
linear-cli tpl create bug                 # interactive
linear-cli tpl list
linear-cli tpl show bug
linear-cli tpl delete bug
```

### Remote template (Linear workspace)

```bash
# Create a remote template tied to a team
linear-cli tpl remote-create --name "Bug Report" --type issue -t ENG

# List + get
linear-cli tpl remote-list
linear-cli tpl remote-get TEMPLATE_ID
```

Then create issues *from* the template:

```bash
linear-cli i create "..." -t ENG --template "Bug Report"
```

(Confirm the exact `--template` flag with `linear-cli i create --help`; some versions resolve by ID rather than name.)

## Pattern E — Parent / child wiring

Use after Pattern A or C to nest the new issues under an umbrella issue.

```bash
PARENT=LIN-1
for CHILD in LIN-101 LIN-102 LIN-103; do
  linear-cli rel parent "$CHILD" "$PARENT"
done
```

For non-parent links, use `rel add`:

```bash
linear-cli rel add LIN-101 -r blocks LIN-200
linear-cli rel add LIN-101 -r related LIN-300
linear-cli rel add LIN-101 -r duplicate LIN-400
```

See `issues/relations-and-labels.md` for the full relation type list.

## Pattern F — Convert from another tracker

If you're migrating from GitHub Issues, Jira, or a markdown export:

1. Coerce to the CSV columns in Pattern B.
2. Map status/assignee/label names to Linear's by hand or with a `sed`/`jq` pass.
3. Run `im csv --dry-run` until name resolution is clean.
4. Commit.

## Idempotency

Linear has **no native idempotency key**. To make a batch resumable:

1. Tag every issue from the run with a unique batch label (e.g. `batch:2026-04-28-foo`).
2. Before re-running, `linear-cli i list -l batch:2026-04-28-foo --output json --fields title` to see what already exists.
3. Skip titles that already match.

```bash
EXISTING=$(linear-cli i list -l batch:2026-04-28-foo --output json --fields title \
  --compact | jq -r '.[].title')
for t in "${TITLES[@]}"; do
  grep -Fxq "$t" <<<"$EXISTING" && continue
  linear-cli i create "$t" -t ENG -l "batch:2026-04-28-foo" --id-only --quiet
done
```

## Batch labelling without re-creating

If you've already created the issues and just want to retro-fit a label:

```bash
linear-cli b label review -i LIN-101,LIN-102,LIN-103
# or pipe IDs from a query
linear-cli i list -t ENG -s "Backlog" --id-only \
  | paste -sd, \
  | xargs -I {} linear-cli b label unreviewed -i {}
```

## Rollback

If a run goes wrong:

```bash
# Capture the IDs from the run
BATCH=( "${CREATED[@]}" )
IDS=$(IFS=,; echo "${BATCH[*]}")

# Mark them cancelled (preserves history)
linear-cli b update-state "Cancelled" -i "$IDS" --dry-run
linear-cli b update-state "Cancelled" -i "$IDS"

# Or archive (heavier — hides from default views)
for ID in "${BATCH[@]}"; do linear-cli i archive "$ID"; done
```

## Reporting back to the user

End every batch with a short summary:

```text
Created 12 issues in ENG (3 urgent, 7 normal, 2 low). Batch label: batch:2026-04-28-todo.
First: LIN-451 — "Replace deprecated auth middleware"
Last: LIN-462 — "Backfill audit log for 2025"
```

## See also

- `output-and-scripting.md` — every `--output`, `--id-only`, `--dry-run`, stdin pattern used here.
- `data/import-export.md` — full CSV/JSON column schemas.
- `issues/lifecycle.md` — full create/update flag matrix.
- `issues/relations-and-labels.md` — full relation types and label CRUD.
- `troubleshooting.md` — recovery when a batch hits rate limits or partial failures.
