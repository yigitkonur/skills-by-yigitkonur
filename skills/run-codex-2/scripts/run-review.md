# run-review.sh

Review mode convergence runner. **One invocation = one round.** For each non-terminal entry in the manifest, in parallel: spawn `codex exec review --base <base> --json -o <findings.md>`, normalize the JSONL stream to a structured findings JSON sidecar, and write `status=done` (round-complete) on the manifest entry. The runner does NOT loop rounds, does NOT classify findings, and does NOT assign terminal states (`converged` / `cap_reached` / `blocked`) — those live in the orchestrator (the main agent).

## Inputs

```bash
bash run-review.sh [--dry-run] <manifest.json> <round-number>
```

Positional, simple by design. There are NO `--manifest`, `--base`, `--concurrency`, `--max-rounds`, `--state-dir`, or `--only` flags — they were documented in earlier drafts but never implemented; the dispatcher invokes the runner with just `[manifestPath, "1"]` plus optional `--dry-run` (`run-codex-2.mjs:1811-1813`).

| Arg / env | Default | Notes |
|---|---|---|
| `<manifest.json>` (positional) | required | Manifest with `mode=review` and per-branch `entries[]`. Read for entry list, base branch (per-entry `mode_state.review.base_branch` or `entries[].base_branch`), worktree paths, and rounds-dir. |
| `<round-number>` (positional) | required | Integer ≥ 1. Names round artefacts (`<slug>.r<N>.{md,json,jsonl}`) under `<rounds-dir>`. |
| `--dry-run` | off | Skips real codex spawn; writes synthetic no-finding round artefacts and reaches `done` with zero majors. |
| `JOBS` (env) | `4` | Per-branch parallelism (passed through to `xargs -P "$JOBS"`). |
| `STATE_DIR` (env) | `dirname(<manifest.json>)` | Parent for `rounds/`. The dispatcher exports a run-specific dir; standalone callers can override. |
| `PROJECT_DIR` (env) | from manifest `workspace_root` | Source repo root, needed for worktree creation. |
| `ALLOW_REUSE=1` (env) | propagated by dispatcher | Forwarded to `setup-worktree.sh` so the runner reuses an existing worktree on rounds 2+. |

> *Multi-round automation, per-branch base override, and per-round focus injection are **Planned — not yet wired**. See `references/modes/review.md:86,39`. Until they ship, the orchestrator drives rounds manually by re-invoking this runner with an incremented round number.*

## Outputs

stdout (Monitor-compatible — every line line-buffered):

```
START feat-auth (round 1 branch=feat/auth base=main)
DONE  feat-auth (round=1 findings=<rounds-dir>/feat-auth.r1.md)
START docs-quickstart (round 1 branch=docs/quickstart base=main)
FAIL  docs-quickstart (codex exec review exit=1)
--- all jobs finished ---
```

Per-round artefacts under `<rounds-dir>/`:

| File | Producer | Consumer |
|---|---|---|
| `<slug>.r<round>.md` | `codex exec review -o` | Human review; the runner's `answer_path` slot points here |
| `<slug>.r<round>.jsonl` | `codex exec review --json` | Forensics only; the classifier never reads this directly |
| `<slug>.r<round>.json` | This runner (synthesised from the JSONL stream by walking `item.type=agent_message` events) | `classify-review-feedback.py` |
| `<slug>.r<round>.classified.json` | `classify-review-feedback.py` | Orchestrator (main agent) |
| `<slug>.r<round>.apply-queue.json` | Main agent evaluation | Apply step (main agent) |
| `<slug>.r<round>.err.log` | `codex exec review` stderr | Forensics; the runner's `log_path` slot points here |

The `<slug>.r<round>.json` file is built by the runner because `codex exec review -o` writes markdown despite `--json`. The classifier consumes the synthesised JSON, preserving the documented contract that the classifier reads JSON. On JSONL parse failure (truncated stream, non-JSON banner lines), the runner writes a stub `{error: "jsonl_parse_failed", findings_md: "<path>"}` so the classifier can still find the markdown and report a parse error to the orchestrator.

Manifest mutations:
- Per-entry `log_path` / `jsonl_path` / `answer_path` populated on the same write that flips status to `running` (per `references/universal/manifest-contract.md`).
- One record appended to `mode_state.rounds[]` per completed round, of shape `{round, findings_md, findings_json, jsonl, ts}`. Round count is recoverable from `length(.entries[i].mode_state.rounds // [])`.
- `mode_state.terminal_state` is written by the **orchestrator** (main agent) after reading the classifier — NOT this runner.
- On round-success the runner writes `status=done` (NOT `reviewed`, which isn't in the manifest's documented status enum). The orchestrator advances to `converged` / `cap_reached` / `blocked` after reading the classifier.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Runner loop completed; per-branch failures are recorded in the manifest, not surfaced as exit codes. |
| 1 | Manifest missing or unreadable. |
| 2 | `codex exec review` is not available (binary too old). |
| 3 | Invalid args (missing manifest path or round number). |

## Behavior

- Uses `codex exec review` (not bare `codex review`). Verified against codex-cli 0.130.0: `exec review` accepts the full `CODEX_FLAGS`, `--json`, `-o`, and `--base`.
- Sources `codex-flags.sh` for `CODEX_FLAGS` (`--dangerously-bypass-approvals-and-sandbox --skip-git-repo-check -m gpt-5.5 -c model_reasoning_effort=xhigh`). The codex-flags variable is re-exported into each `xargs bash -c` subshell because zsh function wrappers do not survive subshell boundaries.
- **One invocation = one round.** The script does not loop rounds itself — the orchestrator (main agent) re-invokes `run-review.sh` with the next `<round-number>` after the classifier returns its verdict. Round cap enforcement (≤ 10) and terminal-state assignment (`converged` / `cap_reached_with_progress` / `cap_reached_no_progress` / `three_all_rejected` / `blocked` / `failed`) live in the orchestrator, NOT this runner.
- 3-consecutive-all-rejected detection: per branch, if 3 rounds in a row produce major items where the main agent rejects every one, the orchestrator marks `done` with `terminal_state="three_all_rejected"` and `terminal_reason="codex stuck"`.
- Per-branch worktrees created via `setup-worktree.sh` on round 1; reused for subsequent rounds via `ALLOW_REUSE=1`.
- **Signal handling**: `trap 'kill 0' TERM INT EXIT` runs near the top so SIGTERM on the runner propagates to xargs and every `codex exec review` child. No orphan codex processes survive a runner kill.

## Notes

The runner does not apply code edits. When classification finds major or ambiguous items, it marks the branch `blocked` and records artifact paths. The main agent evaluates items with `review-pr` or a local equivalent; external/human/bot feedback consolidation belongs to `review-feedback`; PR handoff belongs to `review-self`.
