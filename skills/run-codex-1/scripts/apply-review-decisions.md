# apply-review-decisions.py

Read-only ordered apply queue. Reads the main agent's evaluator-decisions JSON and prints the queue of accepted items in `file:line:intended-shape:rationale` form. Does NOT modify the worktree — main agent applies via `Edit`.

## Inputs

```bash
python3 apply-review-decisions.py --eval <decisions.json> [--branch <name>] [--json]
```

`--input` and `--evaluation` are accepted as aliases for `--eval`.

| Arg | Notes |
|---|---|
| `--eval <path>` (alias: `--input`, `--evaluation`) | Required. The evaluator's per-item decisions JSON (`accepted | rejected | ambiguous` per item). |
| `--branch <name>` | Optional. Override branch label printed in the header (default: `decisions.branch`). |
| `--json` | Machine-readable JSON output for downstream tooling. |

Expected `<decisions.json>` shape (see script docstring for the full schema): an object with `branch`, `round`, `totals`, and `items[]` where each item has `decision`, `source`, `file`, `line_start`, `title`, `intended_shape`, `rationale`, `current_shape`.

## Outputs

Human (default), with ambiguous-first BLOCKED gating:

```
branch: feat/auth  round: 1
  totals: accepted=3 (deduped from 5 raw), rejected=4, ambiguous=0

========================================================================
APPLY QUEUE (in dedup-source order — apply each via Edit, commit per concern)
========================================================================
  [1/3] Add tenant scope to getUserSession
    source:    codex-review
    file:line: src/auth.ts:42
    rationale: per-tenant isolation requires the parameter
    current shape:
      const session = getUserSession();
    intended shape:
      const session = getUserSession(tenantId);
    commit:    <type>(<scope>): Add tenant scope to getUserSession
  ...
```

JSON (`--json`):

```json
{
  "branch": "feat/auth",
  "round": 1,
  "status": "READY",
  "totals": {"accepted_raw": 5, "accepted_deduped": 3, "rejected": 4, "ambiguous": 0},
  "ambiguous": [],
  "queue": [
    {"decision":"accepted","file":"src/auth.ts","line_start":42,"title":"...","intended_shape":"...","rationale":"..."}
  ],
  "rejected_titles": ["[codex-review] ..."]
}
```

## Exit codes

| Code | Meaning |
|---|---|
| 0 | READY — accepted items present, zero ambiguous; main agent applies the queue |
| 1 | BLOCKED — at least one ambiguous item; the whole branch is BLOCKED for this round (main agent must NOT apply) |
| 2 | Evaluation file missing or malformed; bad input |
| 3 | NO-OP — no accepted AND no ambiguous items (round done; nothing to apply) |

## Behavior

- Reads `<decisions.json>`.
- Deduplicates accepted items by `(file.lower, line_start, title-prefix.lower)`. Earliest-source rationale wins.
- When ANY item is `ambiguous`, prints all ambiguous items first under a BLOCKED banner and exits 1. Half-applying is forbidden — a single ambiguous item blocks the entire round.
- Otherwise prints accepted items in dedup-source order with `current_shape` / `intended_shape` excerpts and a templated commit-message hint.
- Read-only: never modifies any file.

## Notes

Per the role split (see `references/modes/review.md`), this script does NOT apply changes. The main agent reads the queue, applies each accepted item via the `Edit` tool, validates (build + tests), and pushes commits to the worktree's branch.

The script's purpose is to surface the queue in a stable order with the rationale visible — so the main agent can apply mechanically without re-evaluating. Decisions are pre-made by the time the queue is printed.
