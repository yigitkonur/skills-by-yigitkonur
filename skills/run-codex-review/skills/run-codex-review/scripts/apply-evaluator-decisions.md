# apply-evaluator-decisions.py

Print the ordered apply queue for one PR's Phase 8a main-agent direct apply. Read-only against the worktree. Reduces Phase 8a main-agent overhead from ~10 tool calls to ~5 per PR by offloading the queue derivation: dedup across sources, ambiguous-first BLOCKED gate, accepted items rendered with `file:line` + intended-shape + rationale + commit-message scaffold.

## Usage

```bash
# Default: human-readable apply queue
python3 scripts/apply-evaluator-decisions.py \
    --pr 53 \
    --worktree /Users/.../wt-feat-foo \
    --eval /repo/.codex-review-rounds/pr-53.evaluation.json

# Machine-readable (for downstream tooling)
python3 scripts/apply-evaluator-decisions.py \
    --pr 53 --worktree /path --eval /path/to.json --json
```

## Behavior

1. Read `<eval-path>`, validate it's an object, check that `--pr` matches `payload.pr`.
2. Group items by `decision` (`accepted | rejected | ambiguous`).
3. Dedup accepted items by `(file, line_start, title-prefix-60)` — first source wins. Production traces show 4+ bots flagging the same issue with slightly different wording; main agent applies once.
4. If ANY item is ambiguous: print BLOCKED gate first (the whole PR is blocked; main agent must not apply accepted items either). Exit 1.
5. Else if no accepted items: print no-op message. Exit 3.
6. Else: print apply queue with each item's `file:line`, current shape, intended shape, rationale, and commit-message scaffold (`(#<pr>)` suffix). Exit 0.

## Flags

| Flag | Default | Effect |
|---|---|---|
| `--pr <n>` | required | PR number; cross-checked against `payload.pr` to catch mistyped invocations. |
| `--worktree <path>` | required | Worktree path. Informational — the script doesn't read worktree contents. |
| `--eval <path>` | required | Path to `pr-<n>.evaluation.json` (the Phase 7 Evaluator's output). |
| `--print-queue` | default | Human-readable queue. |
| `--json` | off | Machine-readable JSON output (mutually exclusive with `--print-queue`). |

## Exit codes

| Code | Meaning | Caller (main-agent) action |
|---|---|---|
| `0` | Queue printed; PR has accepted items, zero ambiguous | Walk the queue, apply each, validate, push. |
| `1` | PR is BLOCKED — at least one ambiguous item | Mark PR BLOCKED in manifest; surface; do NOT apply, do NOT merge. |
| `2` | Evaluation file missing or malformed, OR --pr mismatches payload.pr | Investigate; do NOT apply blindly. |
| `3` | No accepted items AND no ambiguous items | Phase 8a is a no-op for this PR; advance to Phase 8b. |

## Expected `pr-<n>.evaluation.json` schema (Phase 7 Evaluator output)

```json
{
  "pr": 53,
  "branch": "feat/foo",
  "totals": {"accepted": 5, "rejected": 4, "ambiguous": 1},
  "items": [
    {
      "id": "<source>-<n>",
      "decision": "accepted|rejected|ambiguous",
      "source": "codex-rescue|copilot|cubic-dev-ai|devin|greptile|<human>",
      "file": "src/foo.ts",
      "line_start": 42,
      "line_end": 42,
      "title": "Off-by-one in slice",
      "intended_shape": "slice(0)",
      "current_shape": "slice(0, -1)",
      "rationale": "clearly drops last element"
    }
  ]
}
```

## Sample output (queue)

```
PR #53 — branch: feat/foo
  totals: accepted=2 (deduped from 5 raw), rejected=4, ambiguous=0

========================================================================
APPLY QUEUE (in dedup-source order — apply each via Edit, commit per concern)
========================================================================
  [1/2] Off-by-one in slice
    source:    codex-rescue
    file:line: src/foo.ts:42
    rationale: clearly drops last element
    current shape:
      slice(0, -1)
    intended shape:
      slice(0)
    commit:    <emoji> <type>(<scope>): Off-by-one in slice (#53)
  ...
```

## Sample output (BLOCKED)

```
========================================================================
⚠  PR IS BLOCKED — DO NOT APPLY ACCEPTED ITEMS EITHER
========================================================================
Per Phase 8a invariant: a single ambiguous item BLOCKS the entire PR.
Half-apply ships unreviewed code with a half-decided intent.

  [AMBIGUOUS #1] <title>
    source:    <source>
    file:line: src/bar.ts:99
    question:  <evaluator's question>

Action: mark PR BLOCKED in manifest with terminal_reason citing the items above.
Action: surface in deliverable. Action: do NOT merge.
```

## Read/write surface

- **Reads**: `--eval` JSON file.
- **Writes**: nothing. (Stdout only.)
- **Does NOT**: modify the worktree, commit, push, comment on the PR, or call codex.

## When to run

- **Phase 8a, per PR**, after the Phase 7 Evaluator's handback. One invocation per PR.
- Main agent walks the printed queue with Edit + git commands per item; this script does NOT do the walk.

## See also

- `scripts/run-codex-review.py` — Phase 3 wrapper (codex-companion review).
- `scripts/trigger-codex-rescue.py` — Phase 6 wrapper (codex-companion task --background).
- `references/post-pr-review-protocol.md` — full Phase 6 / 7 / 8 flow including the apply recipe.
- `references/review-evaluation-protocol.md` — the rubric the Evaluator follows; defines the JSON shape this script consumes.
