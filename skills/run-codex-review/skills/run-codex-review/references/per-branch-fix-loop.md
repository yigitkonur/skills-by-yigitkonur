# Per-Branch Fix Loop

Phase 3 of the skill. The convergence loop that takes a branch from "ready for review" to "Codex has nothing major" via the **two-level sub-agent pattern**:

- One **coordinator sub-agent** per branch (parallel across branches; lives the entire loop).
- One **worker sub-agent** per round (fresh dispatch each round; uses `/do-review`).

This file specifies the loop pseudocode, the round-counter persistence, the 20-cap rationale, the validation step, the push rules, and the state machine. Mission brief templates for both sub-agents are in `parallel-subagent-protocol.md`. Every brief is written per `~/MISSION_PROTOCOL.md` (see `mission-protocol-integration.md`).

## The two-level pattern

```
                   main agent
                       │
                       │ (Phase 3 dispatch — N parallel)
                       ▼
       ┌─────────────────────────────────────────────────┐
       │   coordinator sub-agent  (per branch, lives the │
       │   entire loop, drives convergence to terminal)  │
       └────────────────────┬────────────────────────────┘
                            │
                            │ (per round, FRESH dispatch each time)
                            ▼
       ┌─────────────────────────────────────────────────┐
       │   worker sub-agent  (one round of work,         │
       │   evaluates via /do-review, applies, pushes,    │
       │   hands back to coordinator)                    │
       └─────────────────────────────────────────────────┘
```

The coordinator orchestrates over time (loop counter, terminal-state decision, dispatch). The worker acts in a moment (one round, one fix-set, one push). Both follow `~/MISSION_PROTOCOL.md`.

## Why fresh worker per round

| Approach | Pros | Cons |
|---|---|---|
| Fresh worker per round (this skill) | Brief discipline applied every round; no stale context; per-round failure isolated | 2× dispatch overhead |
| Long-lived worker per branch | Cheaper dispatch | Brief discipline degrades over rounds; round-N's mistakes contaminate round-N+1 |

The user's wording — *"after every review from Codex we invoke sub-agents… once the sub-agent finishes, we start another Codex review"* — explicitly codifies fresh-per-round. The two-level pattern is the only way to achieve that AND keep parallel branches AND comply with MISSION_PROTOCOL strictly per round.

## Pseudocode (canonical) — coordinator's loop

```python
round = 1
all_rejected_streak = 0  # consecutive rounds where worker rejected ALL items

while round <= 20:
    # 1. REVIEW
    # Coordinator triggers Codex via the wrapper (returns when review JSON is written).
    rc_review = run("python3 scripts/run-codex-review.py --branch <b> --worktree <wt>")
    if rc_review == 1:
        # timeout — retry once
        rc_review = run(...)
    if rc_review == 2:
        manifest[branch].status = "FAILED"
        terminal_reason = "codex review failed past retry budget"
        break

    review_json = "/tmp/codex-review-rounds/<slug>.<round>.json"

    # 2. CLASSIFY
    rc_class = run(f"python3 scripts/classify-review-feedback.py --review-json {review_json}")
    if rc_class == 1:
        # No major items — Codex says clean
        manifest[branch].status = "DONE"
        terminal_reason = f"no major feedback (round {round})"
        break
    if rc_class == 2:
        # malformed review JSON — retry the round once
        retry round, else mark FAILED.

    # 3. DISPATCH WORKER (fresh sub-agent for THIS round)
    brief = build_worker_brief(branch, worktree, round, review_json, prior_round_summaries)
    handback = Agent(prompt=brief, subagent_type="general-purpose")
    # Wait for worker's handback. Worker has used /do-review, applied accepted, pushed.

    # 4. INTERPRET HANDBACK
    if handback.status == "FAILED":
        manifest[branch].status = "FAILED"
        terminal_reason = f"worker FAILED round {round}: <reason>"
        break

    decisions = handback.decisions  # {accepted, rejected, ambiguous}
    if decisions.ambiguous:
        # Coordinator's call: cap-1 ambiguous can pass; ≥2 or persistent -> BLOCKED
        if persistent_ambiguity():
            manifest[branch].status = "BLOCKED"
            terminal_reason = f"ambiguous items in round {round}: {decisions.ambiguous}"
            break

    if decisions.accepted == 0 and len(decisions.rejected) > 0:
        # All-rejected round (no accepts, ≥1 rejected, no ambiguous)
        all_rejected_streak += 1
        if all_rejected_streak >= 3:
            manifest[branch].status = "DONE"
            terminal_reason = f"3 consecutive all-rejected rounds; Codex stuck on items the worker evaluator rejected"
            break
    else:
        all_rejected_streak = 0  # reset

    # 5. INCREMENT
    round += 1

if round > 20:
    manifest[branch].status = "CAP-REACHED"
    terminal_reason = f"20 rounds; remaining major items in last review"
```

## Round-counter persistence

The round counter lives in the manifest entry's `rounds` field. `run-codex-review.py` increments it after each successful review write. The coordinator never increments it manually — every increment must correspond to a written round-log file at `<rounds-dir>/<slug>.<N>.json`.

If the coordinator restarts mid-loop (process crash, host reboot), it reads `rounds` from the manifest and resumes at `rounds + 1`.

## Why 20

Empirically, Codex feedback that hasn't converged by round 20 is feedback the classifier shouldn't treat as major in the first place — usually subjective items the regex catches as `unclassified_treated_as_major`. 20 is the cap that keeps cost bounded without cutting off legitimate convergence.

If a branch genuinely needs >20 rounds, the right answer is **decompose**: split the branch into N smaller branches and re-run. Don't raise the cap.

## Why 3 consecutive all-rejected → DONE

If the worker (using `/do-review`) decides every major item is a false positive for 3 rounds in a row, Codex is stuck on items the evaluator has already determined aren't real. Continuing the loop is wasted compute — Codex won't change its mind, and the worker won't change theirs.

The coordinator marks DONE with `terminal_reason: "3 consecutive all-rejected; Codex stuck on rejected items"`. Phase 5 proceeds to PR creation. The PR body should mention the persistent rejected items so the human reviewer knows the worker considered them and disagreed.

## Validation step (worker's responsibility)

Skip re-review if the worker broke the build. The classifier can't tell the difference between "Codex found a real bug" and "Codex found the syntax error the worker just introduced". The worker validates BEFORE pushing:

| Repo type | Validation |
|---|---|
| Python | `python3 -m py_compile <changed-files>` |
| TypeScript / JavaScript | `bun run type-check` or `tsc --noEmit` (on changed files) |
| Rust | `cargo check` (on changed files) |
| Skills repo with validator | `python3 <repo-root>/scripts/validate-skills.py` |
| Multi-language | the project's `Makefile` `lint` / `check` target |

If validation fails, the worker reverts the bad commit, retries once, else FAILED for that round (worker hands back FAILED; coordinator marks branch FAILED).

## Push rules

- Always to `origin`. The branch was pushed `-u` in Phase 2.
- **Never `--force`** while a review is in flight — invalidates inline review attribution and breaks the round-log → review-id mapping.
- Never push to upstream. Hard rule from `skills/run-repo-cleanup/references/fork-safety.md`.
- If a push is rejected (non-fast-forward), someone else pushed to the branch. The worker stops; coordinator decides (typically FAILED).

## Per-round evaluation (the `/do-review` step)

The worker's central act each round is **evaluation via `/do-review`** before applying. Per `references/review-evaluation-protocol.md`:

```
For each major item from the classifier:
  1. Read the cited code in the worktree.
  2. Use /do-review skill (Skill tool: skill='do-review').
  3. Decide:
     - accepted (real issue, valid fix) → apply via diff-walk
     - rejected (false positive, stale, scope creep) → record reason
     - ambiguous (needs human) → record question
```

Default-when-uncertain: **ambiguous**. Never silently accept. Never silently reject.

Direct-apply (skipping the evaluator) is forbidden by skill invariant 11. The worker brief enforces this in its DoD: "every major item has a decision".

## State machine

```
                 spawn-review-worktrees.py
                          │
                          ▼
                       SPAWNED
                          │
              (main agent dispatches coordinator)
                          │
                          ▼
                       IN-LOOP
                          │
          ┌───────────────┼─────────────────────┬───────────────────────┐
          ▼               ▼                     ▼                       ▼
     classifier:     classifier:            worker hands back        worker hands
     no major        ≥1 major               with all-rejected        back FAILED
          │               │                     │                       │
          ▼               ▼                     ▼                       ▼
        DONE         dispatch worker      all_rejected_streak += 1    FAILED
                          │                     │
                          ▼                     ▼
              (worker applies + pushes)    if streak >= 3:
                          │                       DONE
              (handback to coordinator)         else continue
                          │                     │
                          ▼                     ▼
                    round += 1, loop      round += 1, loop
                          │
                rounds == 20 with major
                          │
                          ▼
                    CAP-REACHED

   Anywhere in IN-LOOP: persistent ambiguity (≥2 ambiguous items, or
   ambiguous-then-recurring) → coordinator marks BLOCKED.
```

## Terminal states

| State | Means | Auto-merged in Phase 5? |
|---|---|---|
| `DONE` (no-major) | Last classifier output had `major == []` | yes (Phase 5 opens PR) |
| `DONE` (3-all-rejected) | 3 consecutive rounds where worker rejected all major items | yes (Phase 5 opens PR; body mentions rejected items) |
| `CAP-REACHED` | 20 rounds reached; ≥1 major still present after worker's evaluation | **no** — surface for human |
| `BLOCKED` | Persistent ambiguity (worker can't decide; needs human) | **no** — surface for human |
| `FAILED` | Tooling failure (codex crashed, push rejected, validation kept failing) past retry budget | **no** — surface for human |

## When to mark BLOCKED

The coordinator marks `BLOCKED` when:

- Worker reports ambiguous items in 2+ consecutive rounds, AND the items are roughly the same item recurring.
- Worker reports ambiguous items where the question requires architectural input outside the branch's scope.
- Two consecutive workers' decisions contradict on the same item ("apply Codex's fix" then "the prior fix made things worse, reject any further attempt").

In all cases, persist the ambiguity into the manifest's `terminal_reason` for human triage. Phase 5 will skip BLOCKED branches.

## Why per-round, not per-major-item

The worker reviews → evaluates → applies ALL accepted items in one round → pushes → re-reviews. Per-item dispatches would be slower (one Codex call per fix) and would fragment commit history. One commit per accepted item per round is the right granularity: small enough to bisect, big enough to not flood the PR.

## Coordinator vs main agent

The main agent dispatches N coordinators in parallel (one per branch). Coordinators run their loops independently. The main agent does NOT enter coordinators' loops to check progress — it monitors via `loop-status.py` (read-only).

If a coordinator crashes (heartbeat stale via manifest mtime), main agent:

1. Reads manifest entry to determine state.
2. Decides: redispatch the coordinator (resumes from `rounds + 1`) OR mark FAILED.
3. After 2 redispatches without progress, mark FAILED for that branch.

## Hard rules (coordinator + worker must enforce)

- One coordinator per branch.
- One fresh worker per round.
- Always `--background` Codex review.
- 20-round hard cap. Never raise.
- Never `--force` push.
- Never amend.
- Never touch `main`.
- Never push to upstream.
- Never decide DONE without classifier exit 1 OR 3-all-rejected streak.
- Never increment `rounds` without a corresponding round-log file.
- Worker NEVER applies an item without `/do-review` evaluation.
- Worker NEVER skips a major item without recording a decision.
- Coordinator NEVER bypasses the worker (no direct edits to the worktree).

## Anti-patterns

| Anti-pattern | Why it fails |
|---|---|
| Coordinator does the work itself instead of dispatching workers | Brief discipline degrades; round-N stale context contaminates round-N+1 |
| Worker applies items without `/do-review` evaluation | Direct-apply violates invariant 11; false positives ship |
| Worker pushes without validating | Validation failures get classified as Codex bugs in next round |
| Coordinator increments rounds without round-log file | Round counter drifts; can't bisect later |
| `--force` push on a branch with active review | Invalidates round-log → review-id mapping |
| Skip the 3-all-rejected check | Codex loops on rejected items forever; cap-reached triggers without progress |
| Re-evaluate prior-round rejected items | The decision was made; don't re-litigate |

## Bottom line

Phase 3 is parallel branches via coordinator sub-agents, each running a fresh-worker-per-round loop. Workers evaluate via `/do-review` before applying. Convergence is no-major OR 3-all-rejected. Cap is 20 rounds. Failure modes are well-defined. The brief discipline (per MISSION_PROTOCOL) is what separates a good convergence from a noisy one.
