# run-review.sh

Review mode convergence runner. Per branch per round: spawn `codex exec review --base <base> --json -o <findings>`, normalize findings, classify major/minor, and write a terminal manifest state. Round cap defaults to 10. Per-branch parallelism is bounded by `JOBS`.

## Inputs

```bash
bash run-review.sh --manifest <path> [--base main] [--concurrency N] [--max-rounds N] [--only id,id] [--dry-run]
```

| Arg/env | Default | Notes |
|---|---|---|
| `--manifest <path>` | required | Manifest with `mode=review` and per-branch `entries[]` |
| `--base <ref>` | `main` | Base ref passed to `codex exec review --base`. |
| `--concurrency N` / `JOBS=N` | 4 | Per-branch parallel |
| `--max-rounds N` | 10 | Per-branch round cap |
| `--state-dir <dir>` | `dirname(manifest)` | Parent for `rounds/`. Dispatcher passes a run-specific dir. |
| `--only id,id` | unset | Rescue subset replay. |
| `--dry-run` | off | Creates synthetic no-finding review output and reaches `converged` without calling Codex. |

## Outputs

stdout (Monitor-compatible):

```
START feat-auth (round 1 branch=feat/auth base=main)
DONE  feat-auth (converged round=1 findings=/state/rounds/feat-auth.r1.md)
START docs-quickstart (round 1 branch=docs/quickstart base=main)
DONE  docs-quickstart (blocked: 2 major finding(s); see /state/rounds/docs-quickstart.r1.classification.json)
--- all jobs finished ---
```

Per-round artefacts under `<rounds-dir>/`:

| File | Producer | Consumer |
|---|---|---|
| `<slug>.r<round>.md` | `codex exec review -o` | Human review; the runner's `answer_path` slot points here |
| `<slug>.r<round>.jsonl` | `codex exec review --json` | The classifier never reads this directly; forensics only |
| `<slug>.r<round>.json` | This runner (synthesised from JSONL events via jq) | `classify-review-feedback.py` |
| `<slug>.r<round>.classified.json` | `classify-review-feedback.py` | Orchestrator (Claude main agent) |
| `<slug>.r<round>.apply-queue.json` | Main agent evaluation | Apply step (main agent) |
| `<slug>.r<round>.err.log` | `codex exec review` stderr | Forensics; the runner's `log_path` slot points here |

The `<slug>.r<round>.json` file is built by walking the JSONL stream for
`item.type=agent_message` events and extracting the structured findings,
since `codex exec review -o` writes markdown despite `--json`. The classifier
consumes the synthesised JSON, preserving the documented contract that the
classifier reads JSON.

Manifest mutations:
- Per-entry `log_path` / `jsonl_path` / `answer_path` populated on the same
  write that flips status to `running` (per `manifest-contract.md`).
- One record appended to `mode_state.rounds[]` per completed round, of shape
  `{round, findings_md, findings_json, jsonl, ts}`. Round count is recoverable
  from `length(.entries[i].mode_state.rounds // [])`.
- Terminal state goes on `mode_state.terminal_state` — written by the
  orchestrator (Claude main agent), not this runner.
- On round-success the runner writes `status=done` (NOT `reviewed`, which
  isn't in the manifest's documented status enum). The orchestrator advances
  to `converged` / `cap-reached` / `blocked` after reading the classifier.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Runner loop completed; branch failures are recorded in the manifest |
| 1 | Manifest missing |
| 2 | `codex exec review` is not available (binary too old) |
| 3 | Invalid args or invalid concurrency |

## Behavior

- Uses `codex exec review` (not bare `codex review`). Verified against codex-cli 0.130.0: `exec review` accepts full `CODEX_FLAGS`, `--json`, and `-o`.
- Sources `codex-flags.sh` for `CODEX_FLAGS`.
- **One invocation = one round.** The script does not loop rounds itself —
  the orchestrator (Claude main agent) re-invokes `run-review.sh` with the
  next `<round-number>` after the classifier returns its verdict. Round cap
  enforcement (≤ 10) and terminal-state assignment (`converged` /
  `cap_reached_with_progress` / `cap_reached_no_progress` / `three_all_rejected` /
  `blocked` / `failed`) live in the orchestrator, NOT this runner.
- 3-consecutive-all-rejected detection: per branch, if 3 rounds in a row produce major items where the main agent rejects every one, the orchestrator marks `done` with `terminal_state="three_all_rejected"` and `terminal_reason="codex stuck"`.
- Per-branch worktrees created via `setup-worktree.sh` on round 1; reused for subsequent rounds.
- **Signal handling**: `trap 'kill 0' TERM INT EXIT` runs near the top so SIGTERM
  on the runner propagates to xargs and every `codex exec review` child. No
  orphan codex processes survive a runner kill.
- **Per-round JSON synthesis**: the runner reads the JSONL event stream and
  emits a structured `<slug>.r<round>.json` sidecar. If JSONL parsing fails
  (truncated stream, non-JSON banner lines), a stub is written with
  `error="jsonl_parse_failed"` so the classifier can still find the markdown
  and report a parse error to the orchestrator.

## Notes

The runner does not apply code edits. When classification finds major or ambiguous items, it marks the branch `blocked` and records artifact paths. The main agent evaluates items with `do-review` or a local equivalent; external/human/bot feedback consolidation belongs to `evaluate-code-review`; PR handoff belongs to `ask-review`.
