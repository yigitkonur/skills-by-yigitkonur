# Review mode — per-branch convergence loop

Drive `codex exec review` per branch per round. Classify findings as major or minor. Zero major findings converge; major or ambiguous findings block the branch with artifact paths for the main agent to evaluate.

This skill never opens PRs and never merges. Use `ask-review` for PR creation and the user's normal merge flow. Review mode produces clean branches and converged findings; the human ships them.

## Contents

- When to pick review mode
- Inputs
- Pre-flight
- Runtime loop
- Terminal states
- Role boundaries
- Recovery

## When to pick review mode

- A list of branches that need rigorous review before shipping.
- Each branch has a coherent concern (one PR's worth of changes).
- The user wants codex review as the source of findings — not Greptile / Devin / Copilot, not human reviewers (yet).

When to skip:
- One branch → run `codex exec review --base main` directly.
- Branches with mixed concerns → split first via repo-cleanup tools.
- Multi-bot review evaluation → out of scope; this skill drives codex review only.

## Inputs

```
node orchestrate-codex.mjs review --branches feat/auth feat/billing docs/quickstart
```

Or `--branches-file branches.txt` (one branch per line).

Per-branch settings flow through `tasks.json`-like structure inside the manifest:

```json
{
  "branch": "feat/auth",
  "base_branch": "main",
  "max_rounds": 10,
  "round_focus": "the auth subsystem refactor: session handling, token rotation, audit logging"
}
```

`round_focus` is the per-branch context the prompt template uses. See `references/templates/review.tmpl.md`.

## Pre-flight

1. `git rev-parse --is-inside-work-tree` succeeds.
2. Each branch in `--branches` exists locally OR can be fetched from `origin`.
3. Each branch has a remote ref on `origin` (if not, push first).
4. `codex login status` exits 0.
5. `<skill-root>/scripts/codex-cc/lib/args.mjs`, `state.mjs`, and `workspace.mjs` are present; the dispatcher imports them.
6. `codex exec review --help` shows `--json`, `-o`, `--base`, `-m`, and `--dangerously-bypass-approvals-and-sandbox`.

## Per-branch round flow

`run-review.sh` iterates rounds for each branch. Up to `max_rounds=10` per branch. Per-branch parallelism is bounded by `JOBS` (default 4).

```bash
for round in $(seq 1 "$max_rounds"); do
  # 1. Select non-terminal entries.
  # 2. Set up/reuse each branch worktree.
  # 3. Run native codex exec review with CODEX_FLAGS, --base, --json, and -o.
  # 4. Normalize findings to <slug>.r<round>.review.json.
  # 5. Run classify-review-feedback.py --review-json ... --json.
  # 6. If major_count == 0, mark status=converged.
  # 7. If major_count > 0, mark status=blocked and record findings/classification paths.
done

# Anything still non-terminal after the cap becomes cap_reached.
```

## Why the role split (read this once)

The script classifies. It does not apply code edits. That boundary keeps review findings observable and keeps contextual decisions in the main agent.

In this skill:
- The classifier (`classify-review-feedback.py`) is mechanical and runs as a script.
- Per-item evaluation is **main agent's** work using `do-review` or a documented local equivalent. It produces accepted / rejected / ambiguous decisions with rationale.
- The apply queue (`apply-review-decisions.py`) is a read-only ordered listing of `file:line:intended-shape:rationale`. The script does not modify the worktree.
- The main agent applies accepted fixes directly in its own context, then reruns review when appropriate.

Direct-apply without contextual evaluation is forbidden. Main agent evaluates; main agent applies.

## Major vs minor policy

Loop on (major):
- correctness bugs in the changed code.
- runtime stability regressions (race conditions, null derefs, silent error swallowing).
- data integrity hazards (lost writes, ordering bugs, partial state on failure).
- security regressions.
- regressions of existing behavior.
- hygiene that hides bugs.
- branch-structure issues that block reviewability.

Do not loop on (minor):
- formatting, naming preferences, style nits.
- doc-only polish.
- speculative perf.
- scope creep.

Default-when-ambiguous (classifier): **major**, conservative. The user's repo `CONTRIBUTING.md` may tighten further; the skill respects it.

## Terminal states

| State | Meaning | Acceptable? |
|---|---|---|
| `converged` | Latest round produced 0 major items. | yes — branch is done |
| `blocked` | Major or ambiguous findings require contextual evaluation/apply, or a contradiction needs a human decision. | surface; branch is not converged |
| `cap_reached` | Round cap hit before a branch reached another terminal state. | surface; branch likely needs splitting |
| `failed` | Tooling crash past retry budget; codex review crashed; classifier crashed. | surface for human |

Do not invent additional states. If a situation doesn't fit, pick `blocked` with a `terminal_reason` describing the mismatch, surface it, and file the issue.

## Recovery

| Symptom | Mitigation |
|---|---|
| `codex exec review` exits non-zero | Re-run once (transient network). On second failure, mark round `failed`, status `failed`, rescue eligible. |
| Classifier cannot parse normalized JSON | Capture the raw output; mark `failed`; the classifier or normalizer needs a fix. |
| Round 10 hit | Set terminal state per the table above. Do not extend the cap silently. |
| Major findings persist after evaluation/apply | Rerun review after fixes; if it oscillates, mark `blocked` and surface the contradiction. |
| Branch CI is red before review starts | Surface immediately. Reviewing red code pollutes the findings. The user fixes CI first. |

Full taxonomy: `references/universal/failure-modes.md`.

## Cleanup

After every branch reaches a terminal state:
1. The skill produces a deliverable: per-branch summary (rounds, classifier outcomes, accepted/rejected/ambiguous counts, terminal state).
2. `python3 cleanup-worktrees.py --execute` removes worktrees for branches that are converged AND merged. Refuses converged-but-unmerged.
3. The user opens PRs via `ask-review` (separate skill) and merges via their normal flow.
4. Manifest deleted only after every branch is converged AND every worktree is removed.

The skill **never opens PRs**. Use `ask-review` for that.

## Out of scope (kept out, intentionally)

- PR opening — `ask-review` owns this.
- Multi-bot review wait — no third-party reviewers; codex is the only review source.
- Foundation-to-leaf merge orchestration — use `run-repo-cleanup` or manual merging.
- Auto-merge — operator-driven only.
- An Applier sub-agent that evaluates and applies — main agent owns evaluation; main agent applies directly via `Edit`.

## Anti-patterns

- Asking codex review to FIX things. Review is read-only by design. The findings are inputs; fixes happen in main agent's own context.
- Letting the classifier output drive apply directly. Always go through main-agent `do-review` or a documented local equivalent first.
- Extending `max_rounds` past 10 silently. The cap exists to prevent oscillation; bump only after the user confirms the branch needs more rounds AND the trend is convergent.
- Reviewing branches with mixed concerns. Codex flags every concern in every round; the loop never converges. Split first.
- Auto-merging converged branches. The user merges; the skill stops at converged.
