# apply-review-decisions.py

Read-only ordered apply queue. Reads the main agent's evaluator-decisions JSON, prints the queue of accepted items in `file:line:intended-shape:rationale` form. Does NOT modify the worktree — main agent applies via `Edit`.

## Inputs

```bash
python3 apply-review-decisions.py --input <decisions.json> [--json] [--check-ambiguous]
```

| Arg | Notes |
|---|---|
| `--input <path>` | The evaluator's per-item decisions JSON (accepted / rejected / ambiguous per item) |
| `--json` | Machine-readable JSON output |
| `--check-ambiguous` | Exit 2 if any item is `ambiguous` (PR is BLOCKED until human decides) |

## Outputs

Human (default):

```
Apply queue for round 1:

  1. src/auth.ts:42
     [accepted] correctness
     intended-shape: replace `getUserSession()` call with `getUserSession(tenantId)`
     rationale: per-tenant isolation requires the parameter

  2. src/util.ts:155
     [accepted] correctness
     intended-shape: wrap fetch() in retry-with-backoff helper
     rationale: transient 5xx errors silently lose data

3 items accepted, 0 ambiguous, 4 rejected.
```

JSON (`--json`):

```json
{
  "ok": true,
  "ambiguous_count": 0,
  "blocked": false,
  "queue": [
    {"order": 1, "file": "src/auth.ts", "line": 42, "category": "correctness", "intended_shape": "...", "rationale": "..."},
    ...
  ]
}
```

## Exit codes

| Code | Meaning |
|---|---|
| 0 | READY — apply queue available |
| 1 | NO-OP — no accepted items (everything rejected); round is done |
| 2 | BLOCKED — at least one ambiguous item; the whole PR is BLOCKED until human decides |

## Behavior

- Reads `decisions.json`.
- Sorts accepted items by `(file, line)` for predictable apply order.
- Filters out `rejected` items.
- If `--check-ambiguous` and any item is `ambiguous`, prints all ambiguous items first and exits 2.
- Read-only: never modifies any file.

## Notes

Per the role split (see `references/modes/review.md`), this script does NOT apply changes. The main agent reads the queue, applies each accepted item via the `Edit` tool, validates (build + tests), and pushes commits to the worktree's branch.

The script's purpose is to surface the queue in a stable order with the rationale visible — so the main agent can apply mechanically without re-evaluating. Decisions are pre-made by the time the queue is printed.
