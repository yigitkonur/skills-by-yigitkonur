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
linear-cli u me --output json | jq -e '.id | strings | length > 0' >/dev/null || exit 1
linear-cli config workspace-current                 # confirm intended workspace/profile
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
PARENT=${PARENT:-}             # optional; set only to a resolved umbrella issue
TITLES=()
while IFS= read -r title; do
  TITLES+=("$title")
done < <(sed -n 's/^- \[ \] //p' TODO.md)

# Dry-run preview
for t in "${TITLES[@]}"; do
  linear-cli i create "$t" -t "$TEAM" -p 3 --dry-run || exit 1
done

if [ "${#TITLES[@]}" -gt 5 ] && [ "${CONFIRMED_BULK_LINEAR:-}" != 1 ]; then
  echo "Review the dry-run output, then rerun with CONFIRMED_BULK_LINEAR=1 to create ${#TITLES[@]} issues."
  exit 0
fi

# Commit + capture IDs
CREATED=()
for t in "${TITLES[@]}"; do
  ID=$(linear-cli i create "$t" -t "$TEAM" -p 3 --id-only --quiet) || exit 1
  CREATED+=("$ID")
done

# Wire to a parent issue (optional)
if [ -n "$PARENT" ]; then
  for ID in "${CREATED[@]}"; do
    linear-cli rel parent "$ID" "$PARENT" || exit 1
  done
fi

# Batch label
IDS=$(IFS=,; echo "${CREATED[*]}")
linear-cli b label backlog -i "$IDS" --dry-run
if [ "${#CREATED[@]}" -gt 5 ] && [ "${CONFIRMED_BULK_LINEAR:-}" != 1 ]; then
  echo "Review the dry-run output, then rerun with CONFIRMED_BULK_LINEAR=1 to execute: linear-cli b label backlog -i \"$IDS\""
  exit 0
fi
linear-cli b label backlog -i "$IDS"

# Report
printf 'Created %d issues:\n' "${#CREATED[@]}"
printf '  %s\n' "${CREATED[@]}"
```

### Atomicity note

There is **no transactional create**. If item 7/12 fails, items 1–6 are already in Linear. Three mitigations:

1. **Always dry-run first** to confirm titles, team, priority.
2. **Capture IDs as you go** and reconcile partial results. Any cancellation or archival is a separate mutation, not a transactional rollback.
3. **Set a single batch label** (e.g. `b label batch:2026-04-28 -i "$IDS"`) so you can find every issue from the run later.

## Pattern B — CSV import

### Input

`issues.csv`:

```csv
title,description,priority,status,assignee,labels,estimate,dueDate
Fix login redirect,"Multi-line\ndescription",1,Backlog,ada@example.com,"bug,auth",3,2026-05-01
Add 429 retry headers,"",2,Backlog,,api,2,
```

The actual import attempts to resolve `status`, `assignee`, and `labels` by name; unresolved values only produce warnings and can be omitted. Validate names independently first. Multi-value labels use commas inside a quoted CSV cell.

### Recipe

```bash
TEAM=ENG

# 1. Preview rows; validate names independently (preview does not resolve them)
linear-cli im csv issues.csv -t "$TEAM" --dry-run

# 2. Commit
linear-cli im csv issues.csv -t "$TEAM" --output json

# In 0.3.28 results are reported on stderr; inspect and reconcile every row. Exit 0 can include per-item failures.
```

### Create new issues from an export

Export → tweak → import creates new issues and does not update existing issues or preserve all fields:

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
COUNT=$(jq -s 'length' plan.ndjson) || exit 1
[ "$COUNT" -gt 0 ] || { echo "No issue rows" >&2; exit 1; }
while IFS= read -r row; do
  title=$(jq -er '.title | strings | select(length > 0)' <<<"$row") || exit 1
  printf '%s' "$row" | linear-cli i create "$title" -t "$TEAM" --data - --dry-run || exit 1
done < plan.ndjson
if [ "$COUNT" -gt 5 ] && [ "${CONFIRMED_BULK_LINEAR:-}" != 1 ]; then
  echo "Review the exact input and preview before authorizing this batch." >&2
  exit 0
fi
while IFS= read -r row; do
  title=$(jq -er '.title | strings | select(length > 0)' <<<"$row") || exit 1
  ID=$(printf '%s' "$row" \
    | linear-cli i create "$title" -t "$TEAM" --data - --id-only --quiet) \
    || { echo "FAIL: $title" >&2; exit 1; }
  printf '%s\n' "$ID"  # persist this output as the batch's successful-ID record
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

To use the **local** `bug` template created above:

```bash
linear-cli i create "..." -t ENG --template bug
```

In 0.3.28 `--template` reads a local template name. Creating a remote template does not make it available through that flag; explicitly map its data into issue-create input if needed.

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
3. Preview with `im csv --dry-run`; independently validate each status, assignee, and label against the target workspace.
4. Commit.

## Idempotency

These CLI create commands do not expose an idempotency key. Title matching is only a best-effort duplicate check, with races and duplicate-title ambiguity. Persist created IDs and verify the exact target workspace/team before resuming. For a batch label check:

1. Tag every issue from the run with a unique batch label (e.g. `batch:2026-04-28-foo`).
2. Before re-running, `linear-cli i list -t ENG -l batch:2026-04-28-foo --all --output json --fields title` to see what already exists.
3. Skip titles that already match.

```bash
EXISTING=$(linear-cli i list -t ENG -l batch:2026-04-28-foo --all --output json --fields title \
  --compact | jq -r '.[].title') || exit 1
for t in "${TITLES[@]}"; do
  grep -Fxq -- "$t" <<<"$EXISTING" && continue
  linear-cli i create "$t" -t ENG -l "batch:2026-04-28-foo" --id-only --quiet
done
```

## Batch labelling without re-creating

If you've already created the issues and just want to retro-fit a label:

```bash
linear-cli b label review -i LIN-101,LIN-102,LIN-103 --dry-run
linear-cli b label review -i LIN-101,LIN-102,LIN-103

# Or capture IDs from a query
linear-cli i list -t ENG -s "Backlog" --limit 25 --output json --compact \
  --fields identifier,title > /tmp/linear-backlog.json
jq -r '.[] | "\(.identifier)\t\(.title)"' /tmp/linear-backlog.json
COUNT=$(jq 'length' /tmp/linear-backlog.json)
IDS=$(jq -r '.[].identifier' /tmp/linear-backlog.json | paste -sd,)
[ "$COUNT" -gt 0 ] && [ "$COUNT" -le 25 ] || { echo "Unexpected count: $COUNT"; exit 1; }
linear-cli b label unreviewed -i "$IDS" --dry-run
if [ "$COUNT" -gt 5 ] && [ "${CONFIRMED_BULK_LINEAR:-}" != 1 ]; then
  echo "Review the dry-run output, then rerun with CONFIRMED_BULK_LINEAR=1 to execute: linear-cli b label unreviewed -i \"$IDS\""
  exit 0
fi
linear-cli b label unreviewed -i "$IDS"
```

## Reconcile a partial batch

There is no automatic rollback. Inspect the IDs created by this run, verify the intended recovery, and choose cancellation or archival as a separate authorized operation. Execute one alternative only:

```bash
# Capture the IDs from the run
BATCH=( "${CREATED[@]}" )
IDS=$(IFS=,; echo "${BATCH[*]}")

# Mark them cancelled (preserves history)
linear-cli b update-state "Cancelled" -i "$IDS" --dry-run
if [ "${#BATCH[@]}" -gt 5 ] && [ "${CONFIRMED_BULK_LINEAR:-}" != 1 ]; then
  echo "Review the dry-run output, then rerun with CONFIRMED_BULK_LINEAR=1 to execute: linear-cli b update-state \"Cancelled\" -i \"$IDS\""
  exit 0
fi
linear-cli b update-state "Cancelled" -i "$IDS"

# Alternative: archive these newly created issues instead, only if that is the chosen recovery.
# for ID in "${BATCH[@]}"; do linear-cli i archive "$ID" || exit 1; done
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
