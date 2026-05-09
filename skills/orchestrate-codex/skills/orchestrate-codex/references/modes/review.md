# Review mode — per-branch convergence loop

Drive `codex exec review` per branch per round. Classify findings as major or minor. Main agent decides per-major-item using context the classifier surfaces. Apply accepted decisions via Edit. Repeat until convergence or cap.

This skill never opens PRs and never merges. Use `ask-review` for PR creation and the user's normal merge flow. Review mode produces clean branches and converged findings; the human ships them.

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
5. `<skill-root>/scripts/codex-cc/codex-companion.mjs` is resolvable (it's vendored — should be present).
6. `gh auth status` succeeds (used for any auxiliary GitHub queries the run needs).

## Per-branch round flow

`run-review.sh` iterates rounds for each branch. Up to `max_rounds=10` per branch. Per-branch parallelism is bounded by `JOBS` (default 4).

```bash
round=1
all_rejected_streak=0

while [ "$round" -le "$max_rounds" ]; do
    # 1. Set up worktree (round 1) or reuse (round ≥ 2).
    if [ "$round" = "1" ]; then
        bash setup-worktree.sh "review-$branch_slug" "$branch" "$base_branch"
    fi
    WORKTREE="../$repo-wt-review-$branch_slug"

    # 2. Mark round running.
    python3 manifest-update.py --manifest "$MANIFEST" --entry "$branch_slug" \
        --set "mode_state.rounds[$((round-1))]=$(jq -n --argjson r "$round" '{round:$r,status:"running"}')"

    # 3. Run native codex exec review.
    . codex-flags.sh
    findings_path="$rounds_dir/$branch_slug.$round.json"
    codex exec review \
        "${CODEX_REVIEW_FLAGS[@]}" \
        --json \
        --base "$base_branch" \
        --title "Round $round of review for $branch" \
        -C "$WORKTREE" \
        < "$round_prompt_file" \
        > "$findings_path"

    # 4. Classify findings.
    if python3 classify-review-feedback.py --input "$findings_path" --output "$rounds_dir/$branch_slug.$round.classified.json"; then
        # Exit 0 = at least one major item.
        major_count=$(jq '.major | length' "$rounds_dir/$branch_slug.$round.classified.json")

        # 5. Main agent decides per-item (in main agent's own context, not via this script).
        # The runner emits a stdout signal: the main agent reads the classified.json,
        # uses /do-review to evaluate each major item, writes back apply-queue.json.
        echo "MAJOR $branch_slug round=$round count=$major_count needs-decision"

        # ...main agent decides...

        # 6. Read the apply queue.
        apply_count=$(jq '.accepted | length' "$rounds_dir/$branch_slug.$round.apply-queue.json")

        # 7. Main agent applies via Edit (not via this script).
        # ...main agent applies...

        # 8. Read post-apply state.
        if [ "$apply_count" -eq 0 ]; then
            all_rejected_streak=$((all_rejected_streak + 1))
            if [ "$all_rejected_streak" -ge 3 ]; then
                terminal_state="three_all_rejected"
                break
            fi
        else
            all_rejected_streak=0
        fi
    else
        # Exit 1 = no major items. Round converged.
        terminal_state="converged"
        break
    fi

    round=$((round + 1))
done

if [ "$round" -gt "$max_rounds" ]; then
    if [ "$any_round_pushed" = "true" ]; then
        terminal_state="cap_reached_with_progress"
    else
        terminal_state="cap_reached_no_progress"
    fi
fi

python3 manifest-update.py ... --set "mode_state.terminal_state=$terminal_state"
```

## Why the role split (read this once)

If the worker brief says "evaluate via `/do-review`, then apply", workers stop at the evaluation step ~100% of the time. The `/do-review` framing pulls them into evaluator-mode and "Verdict: apply" feels like the deliverable. Splitting evaluation (main agent) from application (main agent in own context, via Edit) makes apply reliable.

In this skill:
- The classifier (`classify-review-feedback.py`) is mechanical and runs as a script.
- Per-item evaluation is **main agent's** work using `Skill(do-review)`. It produces a per-item decision JSON: accepted / rejected / ambiguous with a rationale and an intended-shape per accepted.
- The apply queue (`apply-review-decisions.py`) is a read-only ordered listing of `file:line:intended-shape:rationale`. The script does not modify the worktree.
- The main agent applies via `Edit` directly, in its own context. No applier sub-agent.

Direct-apply without prior `/do-review` evaluation is forbidden. But pushing eval onto a worker subagent is also forbidden. Main agent evaluates; main agent applies.

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
| `cap_reached_with_progress` | Round 10 hit; at least one round pushed fixes; remaining items go to PR body as known-deferred. | yes — branch is done with carry-over |
| `cap_reached_no_progress` | Round 10 hit; no round produced apply-able fixes. | surface — branch likely needs splitting |
| `three_all_rejected` | 3 consecutive rounds where main agent rejected every item. Codex is producing items that don't survive evaluation. | mark `done` with reason; further rounds won't help |
| `blocked` | Persistent ambiguous items, oscillation, contradictions. | surface for human decision |
| `failed` | Tooling crash past retry budget; codex review crashed; classifier crashed. | surface for human |

Do not invent additional states. If a situation doesn't fit, pick `blocked` with a `terminal_reason` describing the mismatch, surface it, and file the issue.

## Recovery

| Symptom | Mitigation |
|---|---|
| `codex exec review` exits non-zero | Re-run once (transient network). On second failure, mark round `failed`, status `failed`, rescue eligible. |
| `codex exec review` produces malformed JSON | Capture the raw output; surface; do not retry the same input — codex output drift across versions can break the classifier. The skill's classifier may need bumping. |
| Round 10 hit | Set terminal state per the table above. Do not extend the cap silently. |
| Main agent rejects every item for 3 rounds | `three_all_rejected` terminal. Codex is stuck. Surface; human decides next steps. |
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
- Foundation→leaf merge orchestration — use repo-cleanup tools or manual merging.
- Auto-merge — operator-driven only.
- An Applier sub-agent that evaluates and applies — main agent owns evaluation; main agent applies directly via `Edit`.

## Anti-patterns

- Asking codex review to FIX things. Review is read-only by design. The findings are inputs; fixes happen in main agent's own context.
- Letting the classifier output drive apply directly. Always go through main-agent `/do-review` evaluation first.
- Extending `max_rounds` past 10 silently. The cap exists to prevent oscillation; bump only after the user confirms the branch needs more rounds AND the trend is convergent.
- Reviewing branches with mixed concerns. Codex flags every concern in every round; the loop never converges. Split first.
- Auto-merging converged branches. The user merges; the skill stops at converged.
