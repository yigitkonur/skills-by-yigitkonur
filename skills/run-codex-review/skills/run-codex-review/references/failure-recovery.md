# Failure Recovery

Catalogue of failure modes the skill encounters and the exact recovery for each. If you hit something not on this list, halt the affected branch (mark `BLOCKED` or `FAILED`) and surface for human decision — never improvise.

## Phase 3 — inner loop failures

### CAP-REACHED

A branch hit 20 rounds with at least one major item still present after the worker's evaluation.

**What it means**: either the classifier policy is wrong (treating recurring minor items as major) or the branch is too broad to converge under the cap.

**Recovery**:
1. Read the last round's classifier output AND the worker's last handback (round-log JSON) to see what items + decisions were in flight.
2. Triage:
   - **Policy mis-classification**: edit `references/major-vs-minor-policy.md` to demote the recurring item; the classifier promotes/demotes per the file. Re-classify the last round's review JSON; if `major[]` is now empty, mark DONE retroactively.
   - **Branch too broad**: split the branch into N narrower branches (per `references/commit-redistribution.md`'s cherry-pick-into-new-branch pattern), abandon the original, restart Phase 2 for the new branches.
   - **Genuine known limitation**: human accepts the remaining items as known issues, manually marks `DONE` with a `terminal_reason: "accepted as known: <items>"`. Phase 5 PR-Creator's brief should mention these in the body's "Known limitations" section.
3. Never raise the 20-round cap. If a branch genuinely needs >20 rounds to converge, it's the wrong shape.

### FAILED (tooling)

Codex CLI crashed, push was rejected, validation kept failing past retry budget.

**Recovery**:
1. Read the manifest's `terminal_reason` for the raw error.
2. Common causes:
   - **codex CLI not on PATH**: install / fix shell. Re-run `audit-review-state.py` to confirm the environment is sound.
   - **Push rejected (non-fast-forward)**: someone else pushed to the branch. `git fetch origin && git pull --rebase` (only on this branch in its worktree); resume from current HEAD.
   - **Validation kept failing**: usually a syntax error introduced by the worker's last fix. Look at the diff of the last commit; the worker should have caught this and reverted; if not, manual revert + restart.
3. Decide: redispatch the coordinator (resumes from `rounds + 1` if state is recoverable), or split-and-restart, or abandon.
4. Never retry a `FAILED` round more than once at the wrapper level. Cap subagent-level retries at 3.

### BLOCKED — coordinator-level

The coordinator marks BLOCKED when worker's `/do-review` evaluator marks items ambiguous in 2+ consecutive rounds, OR an oscillation pattern emerges.

**Trigger conditions** (coordinator sets BLOCKED on any of these):
- Two consecutive rounds where worker emitted ambiguous items.
- Same major item recurs after the worker (and `/do-review`) accepted it (oscillation: applied fix didn't satisfy Codex; second attempt also failed).
- A major item requires a decision outside this branch's scope (worker marked it ambiguous with a question).

**Recovery**:
1. Read `terminal_reason` for the contradiction or oscillation cause.
2. Human decides:
   - Pick one of the contradictory recommendations; codify in `policy.json` so future runs don't see the same conflict.
   - Mark the major item as a known limitation, manually advance to DONE.
   - Split the branch so the conflicting concerns separate.
3. Document the decision in the manifest's `terminal_reason` for posterity.

### Worker sub-agent crash mid-round

The worker dies before writing its handback. Coordinator detects via heartbeat (round-log mtime / manifest write timestamp).

**Recovery**:
1. Coordinator reads round-log file (if any) to determine partial state.
2. Redispatch a fresh worker for the same round (rounds counter not incremented).
3. After 2 worker redispatches without progress, mark FAILED for the branch.

### Coordinator sub-agent crash

Main agent detects via stale `updated_at` on the manifest entry.

**Recovery**:
1. Main agent reads manifest entry to determine state (which round was active).
2. Redispatch the coordinator with the same brief; it resumes from `rounds + 1` (or from the current round if no round-log written).
3. After 2 redispatches without progress, mark FAILED for the branch.

### Lost worktree

The worktree directory was deleted (`rm -rf`, accidental cleanup, disk full).

**Recovery**:
```bash
git worktree prune                           # clean up dangling refs
git worktree add <expected-path> <branch>    # recreate from manifest
```

The coordinator resumes from `rounds + 1` because all round logs and state are external to the worktree (in `<rounds-dir>` and the manifest).

If the branch itself is also lost (only existed locally, no `origin/<branch>`), it's gone. Mark `FAILED`; surface for human; recover from `backup/codex-review/<branch>/<timestamp>` ref if Phase 1 redistribution created one.

### Dirty tree mid-loop

A worker's worktree shows uncommitted changes from a prior round failure.

**Recovery**:
1. **Don't discard.** The dirty changes may be the partial fix from the last round.
2. `git status` and `git diff` to inspect.
3. If the changes are recoverable: complete the commit, push, resume.
4. If not: `git stash push -u -m "phase-3-recovery-<branch>-<round>"`, restore from manifest's `head_sha_current`, re-classify the last round to decide whether to retry.
5. If the worktree is irrecoverably mangled, `git worktree remove --force <path>`, recreate per "Lost worktree" recovery above. Mark the round failed; let the coordinator decide redispatch.

---

## Phase 5 — PR creation failures

### `/ask-review` skill unavailable

PR-Creator can't invoke `/ask-review`. Brief explicitly forbids hand-rolling.

**Recovery**:
1. Mark PR-Creator's mission FAILED with `terminal_reason: "ask-review skill not registered"`.
2. Surface for human: install/restore the skill, then redispatch PR-Creator for that branch.
3. Do NOT hand-roll the body. Phase 6's expectations (codex rescue + bot reviews) assume a comprehensive body; a hand-rolled body degrades the rest of the pipeline.

### PR body exceeds 50,000 chars

`/ask-review` produced a body too long.

**Recovery**:
1. PR-Creator should trim via `/ask-review` flags (`--summary-only`, `--skip-per-commit`, etc.).
2. If still >50k after `/ask-review`'s trimming options: the PR is too wide. Two options:
   - Split the branch (return to Phase 1 for that branch).
   - Move detail into repo docs and link from the body.
3. Never cut sections that contain reviewer questions or risks — those are critical to Phase 6 reviewers.

### gh pr create rejects

Common causes: branch not pushed, base branch missing, fork-safety violation.

**Recovery**:
1. **Fork-safety violation** (PR target is upstream): IMMEDIATELY mark FAILED. Do NOT retry on upstream. See `skills/run-repo-cleanup/references/fork-safety.md` for full recovery if a PR did open on upstream.
2. **Branch not pushed**: `git -C <wt> push -u origin <branch>` from the worktree, retry.
3. **Base branch missing**: verify `<base>` (default `main`) exists on origin; fetch if needed.

### Accidental upstream PR

Someone opened a PR on `upstream` instead of the fork.

**Immediate**:
1. **Stop everything.** Pause all sub-agents (kill the dispatch).
2. Recover per `skills/run-repo-cleanup/references/fork-safety.md` "If you mess up":
   - `gh pr close <number> --repo <upstream> --delete-branch`
3. Rotate any secrets that may have leaked.
4. Run `audit-review-state.py` and `audit-state.py`. Both must show CLEAN before resuming.
5. Re-verify `git remote -v` shows the expected layout.
6. Resume — but only after a human confirms the leak is contained.

---

## Phase 6 — codex rescue + wait window failures

### Codex rescue invocation fails

`trigger-codex-rescue.py` returns rc=2 (codex CLI missing or failure).

**Recovery**:
1. Manifest is marked `rescue_status: "failed"` with the error.
2. `await-pr-reviews.py` proceeds anyway — it gathers what's there. Codex rescue items will simply be missing from the gathered JSON.
3. Phase 7 evaluator processes whatever sources arrived. If none arrived, the evaluator's decisions JSON has zero items and main agent merges directly.
4. Surface in the deliverable: "codex rescue unavailable for PR #<n>".

### Codex rescue runs forever

`audit-review-state.py` flags the `rescue_review_id` as in-flight past total_cap.

**Recovery**:
1. Treat as missing source — proceed with whatever did arrive in the wait window.
2. Note in PR's manifest entry: `rescue_status: "timeout"`.
3. The evaluator (Phase 7) handles the missing source gracefully — it just doesn't see codex-rescue items.

### No external bots installed in repo

`await-pr-reviews.py` waits the base 900s, sees no external sources. Quiet window triggers (no comments at all → 3 min quiet from t=900s = always quiet). Returns at t=1080s with only codex rescue in `sources[]` (or empty if rescue also failed).

**Recovery**:
1. The Phase 7 evaluator handles a single source (or no source) gracefully. If the gathered JSON has zero items, evaluator outputs an empty decisions array.
2. Main agent merges directly (no items to apply).
3. Surface in the deliverable: "PR #<n> received no external review (only codex-rescue, or none)".

### External bot reviews are still arriving at total cap

`await-pr-reviews.py` terminates with `wait_terminated_by: "total_cap"`. Some bots are still posting comments.

**Recovery**:
1. The current state is gathered. Phase 7 evaluates what we have.
2. Late-arriving comments after evaluation are surfaced for human attention but don't block merge — the bot will still see them on the merged commit if it cares.
3. If the late comments are substantial, optionally open a follow-up PR (Phase 8's "ask for a new PR" path).

### Codex rescue produces unparseable artifact

Codex rescue completed but the artifact format doesn't match `codex-review-contract.md`'s schema.

**Recovery**:
1. The wrapper (`trigger-codex-rescue.py` doesn't fetch; `await-pr-reviews.py` parses via gh API) treats unstructured output as a single item (raw text in `body`).
2. Evaluator handles it as a single ambiguous item if it can't make sense of it.
3. If this happens persistently, update `references/codex-review-contract.md`'s schema and the wrappers to match the actual output.

---

## Phase 7 — evaluator failures

### Evaluator marks everything ambiguous

Surface for human triage. Do not merge. Likely cause: PR is too broad or too cross-cutting; consider splitting in a follow-up.

### Evaluator returns no decision for some items

The evaluator must classify every item per its DoD. If the brief is followed, this can't happen. If it does (degenerate case), the missing items default to **ambiguous**. Never silently default to accepted or rejected.

### Evaluator's decisions disagree with classifier

Classifier said major; evaluator says rejected. The evaluator wins for the apply decision. If this happens often (≥30% of major items rejected), the classifier policy is too loose — edit `major-vs-minor-policy.md` to demote the recurring keyword.

### Cross-source contradictions

Source A and Source B contradict on the same item. The evaluator marks BOTH ambiguous (per `review-evaluation-protocol.md`). Surface for human. Do not auto-resolve.

### Oscillation across rounds (Phase 3) AND PR (Phase 7)

If Phase 3 worker accepted Codex's fix, then Phase 7 reviewer (codex-rescue or bot) flags the SAME area as broken: the fix didn't satisfy. Surface as ambiguous for that item. Phase 8 doesn't apply; surface in deliverable; human decides whether to revert + retry or split the branch.

### Evaluator sub-agent crashes

Heartbeat detection (manifest `updated_at` not advancing). If stale, redispatch with the same brief. After 2 redispatches without progress, mark FAILED for that PR; surface for human.

---

## Phase 8 — apply + merge failures

### Evaluator's accepted fix breaks CI

Phase 8 push fails CI. Treat as a worker-style failure: revert the bad commit, mark the item ambiguous in the manifest with `terminal_reason: "post-apply CI failure: <details>"`, surface for human. Do NOT auto-retry the same fix.

### Merge conflict at apply

The branch's tip has drifted from the evaluator's recorded `head_sha_current` (rare — would require external push between Phase 7 and Phase 8).

**Recovery**:
1. `git fetch origin && git pull --rebase` on the worktree.
2. Re-run Phase 7 evaluator on the new state (the prior evaluation may now be stale).
3. Apply the fresh accepted set.

### Auto-merge fails (CI red, branch protection)

`gh pr merge` rejects.

**Recovery**:
1. Check CI status; wait for green.
2. If branch protection requires reviews: check that human reviewers have approved (the bots may not satisfy required-reviewers).
3. If still failing, surface for human.

### Sub-agent dispatched in Phase 8

You shouldn't be here — Phase 8 is main-agent direct. If a sub-agent was dispatched by accident, terminate it; main agent applies.

---

## Cross-phase failures

### Manifest corruption

`audit-review-state.py` reports the manifest is malformed (JSON parse failure, missing required fields).

**Recovery**:
1. Look for `redistribute-commits.py`'s backup at `<manifest-path>.bak` (only present if a recent edit failed).
2. Reconstruct from round logs + pr-reviews / pr-evaluation files: scan `<rounds-dir>/*.json`, group by branch slug, infer status from latest artifacts, write a minimal manifest.
3. If reconstruction is impossible, abandon the run: `cleanup-worktrees.py --execute --force-abandon <every-branch>`, delete manifest, restart from Phase 0.

### In-flight Codex job from prior session

`audit-review-state.py` finds a Codex background job ID in the prior manifest that's still `running`.

**Recovery**:
1. Query the job: `codex review --status <job-id>`.
2. If `completed`: fetch the artifact, write to the appropriate round log, advance the manifest's branch entry, resume.
3. If `running`: wait `--timeout` for it to finish, then proceed.
4. If `failed` or `cancelled`: discard the prior round, mark FAILED for that branch, decide redispatch.

### Brief defects (sub-agent produces garbage)

The sub-agent's handback shows clearly bad work (over-applies, misreads, ignores DoD).

**Recovery**:
1. Read the brief. Apply the brief discipline checklist (`parallel-subagent-protocol.md`).
2. Likely defects: missing context, soft DoD, no failure protocol, no handback structure.
3. Revise the brief; redispatch.
4. **Do not blame the agent.** The brief is the lever — bad output = bad brief 90% of the time.

---

## Hard rule across all failures

Never use a destructive shortcut to "make the failure go away":

- No `git reset --hard` without a backup ref.
- No `rm -rf` of a worktree with uncommitted changes.
- No manual `--force` push to "unstick" a branch.
- No editing the manifest by hand to fake a `DONE` state.
- No dispatching a sub-agent that bypasses the failure protocol.
- No applying ambiguous items "to make the deliverable look clean".

If a recovery path here doesn't fit your situation, halt the affected branch and ask a human. Wrong recovery is irreversible; asking is cheap.

## Decision flowchart

```
Sub-agent or main agent encounters a problem
                   │
                   ▼
       Is it on this list?
       ├── Yes → follow the recipe
       └── No
            │
            ▼
       Halt the affected branch / phase
            │
            ▼
       Set status to BLOCKED if semantic, FAILED if tooling
            │
            ▼
       Persist terminal_reason with raw error
            │
            ▼
       Surface in final deliverable
            │
            ▼
       Wait for human decision
```

The decision flowchart never has "improvise" as a node. Either there's a recipe, or there's a halt + surface.

## Bottom line

Every failure has a recovery path. Most failures are sub-agent failures, and most sub-agent failures are brief defects. Fix the brief, not the agent. Surface the rest for human decision. Never silently fail.
