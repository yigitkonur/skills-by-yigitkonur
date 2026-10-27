# Create many issues

Choose a format, save the exact input, preview it, and execute only the authorized batch. Persist each successful identifier so a partial run can be reconciled. Bash examples below work with macOS Bash 3.2.

## Checklist or structured plan → NDJSON

Use one issue object per line:

```ndjson
{"title":"Extract retry helper","description":"Implementation details","priority":3}
{"title":"Cover timeout recovery","priority":2,"parentId":"RESOLVED_PARENT_UUID"}
```

For a Markdown checklist, this conversion preserves quoted titles:

```bash
sed -n 's/^- \[ \] //p' TODO.md | jq -Rc '{title: .}' > plan.ndjson
```

Resolve the team and any UUID fields first. Preview the same JSON that will be sent:

```bash
TEAM=ENG  # replace with the resolved target team
jq -s -e 'length > 0 and all(.[]; (.title | type == "string" and length > 0))' plan.ndjson >/dev/null || exit 1
while IFS= read -r row; do
  title=$(jq -r '.title' <<<"$row")
  printf '%s' "$row" | linear-cli i create "$title" -t "$TEAM" --data - --dry-run || exit 1
done < plan.ndjson
```

After checking the preview and confirming the existing task authorization covers this exact batch:

```bash
touch created-ids.txt
while IFS= read -r row; do
  title=$(jq -r '.title' <<<"$row")
  ID=$(printf '%s' "$row" | linear-cli i create "$title" -t "$TEAM" --data - --id-only --quiet) || exit 1
  printf '%s\n' "$ID" >> created-ids.txt
done < plan.ndjson
```

Keep the input unchanged between preview and execution. Use an ID record dedicated to this batch and preserve it when resuming. Resolve existing records before retrying a create whose outcome is unknown; title matching alone is not reliable idempotency.

## CSV or exported JSON

```bash
linear-cli im csv issues.csv -t ENG --dry-run
linear-cli im json issues.json -t ENG --dry-run
```

In 0.3.28 import preview resolves the team but not status, user, or label names. Real import can warn and omit unresolved fields, and can exit 0 after some creates fail. Import progress/results go to stderr, so inspect and reconcile every row. See `data/import-export.md` for accepted fields. Import creates new issues; it does not update the exported originals.

For precise per-row success handling or rich fields such as parent/project UUIDs, prefer the NDJSON create loop above.

## Templates

`i create --template NAME` loads a **local** template. Remote `tpl remote-*` commands are a separate API surface; a remote template is not automatically usable through that flag. See `issues/relations-and-labels.md` for the observed compatibility limits.

```bash
linear-cli tpl create bug --team ENG --priority 2 --label bug
linear-cli i create "Resolved title" -t ENG --template bug --dry-run
```

## Wire or label existing creations

```bash
linear-cli rel parent CHILD_ID PARENT_ID
linear-cli rel add LIN-101 -r blocks LIN-200
linear-cli b label review -i LIN-101,LIN-102
```

`bulk --dry-run` is rejected in 0.3.28. Inspect current records and the exact planned targets/values before invoking the authorized bulk command. Use only captured successful IDs. `b label` appends; `i update -l` replaces the label set. For an empty generated ID set, stop instead of invoking a bulk mutation.

## Partial failure

Creation is not transactional. Record successes, inspect failures, and query ambiguous outcomes before retrying. Cancellation or archival of newly created issues is a separate authorized recovery operation, not an automatic inverse. Report created/failed counts and any unresolved IDs.
