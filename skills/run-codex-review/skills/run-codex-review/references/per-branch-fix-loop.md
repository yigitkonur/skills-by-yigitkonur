# Per-Branch Fix Loop

Phase 3 of the skill. The convergence loop that takes a branch from "ready for review" to "Codex has nothing major". **Main agent owns the loop directly** — there is no coordinator sub-agent. Sub-agents are short-lived per-round Appliers.

```
                   main agent (the coordinator)
                       │
                       │ per round, per active branch:
                       │   1. Bash-bg: run-codex-review.py
                       │   2. classify-review-feedback.py
                       │   3. for each major item: Skill(do-review) in own context → decision
                       │   4. compose pre-decided fix specs
                       │
                       ▼ Agent dispatch (FRESH per round, per branch, parallel)
       ┌─────────────────────────────────────────────────┐
       │   Applier sub-agent  (one round of work,        │
       │   applies pre-decided fixes mechanically,       │
       │   validates, pushes; binary push DoD;           │
       │   never invokes /do-review)                     │
       └─────────────────────────────────────────────────┘
```

Main agent orchestrates over time (loop counter, terminal-state decision, dispatch, evaluation). Applier acts in a moment (apply N pre-decided fixes, validate, push). Applier brief follows `~/MISSION_PROTOCOL.md` (see `mission-protocol-integration.md`); main-agent self-direction is documented in `parallel-subagent-protocol.md` "Coordinator role".

## Why fresh Applier per round

| Approach | Pros | Cons |
|---|---|---|
| Fresh Applier per round (this skill) | Brief discipline applied every round; no stale context; per-round failure isolated; binary push DoD | 2× dispatch overhead |
| Long-lived worker per branch | Cheaper dispatch | Brief discipline degrades; round-N mistakes contaminate round-N+1 |

The user's wording — *"after every review from Codex we invoke sub-agents… once the sub-agent finishes, we start another Codex review"* — explicitly codifies fresh-per-round.

## Why no Coordinator sub-agent

Older drafts of this file dispatched a per-branch Coordinator sub-agent that held the convergence loop. Production runs revealed:

- Coordinators that need to live for hours (5+ hours, 9 branches, 20 rounds) drift, lose context, or hit harness session limits.
- Sub-sub-agent dispatch (Coordinator dispatching its own Worker per round) is brittle in Claude Code; depth-2 dispatch isn't a stable interface.
- The worker brief framing that asked workers to `/do-review` then apply caused 100% decision-only failure across runs.

The current pattern moves orchestration and decisions to main agent, leaves only mechanical apply to short-lived sub-agents. This is the empirically reliable shape.

## Pseudocode (canonical) — main agent's per-branch loop

```python
# Main agent runs this PER BRANCH, but executes branches in parallel via
# Bash run_in_background for the codex-review steps and Agent dispatch for
# the per-round Applier.

round = 1
all_rejected_streak = 0  # consecutive rounds where every decision was rejected

while round <= 20:
    # 1. REVIEW (parallel across branches — main agent kicks off all in
    #    parallel via Bash run_in_background and gathers results).
    rc_review = run("python3 scripts/run-codex-review.py "
                    "--branch <b> --base <base> --worktree <wt> "
                    "--output <rounds-dir>/<slug>.<round>.json")
    if rc_review == 1:
        rc_review = run(...)  # timeout — retry once
    if rc_review == 2:
        manifest[branch].status = "FAILED"
        terminal_reason = "codex review failed past retry budget"
        break

    review_json = "<rounds-dir>/<slug>.<round>.json"

    # 2. CLASSIFY
    rc_class = run(f"python3 scripts/classify-review-feedback.py "
                   f"--review-json {review_json}")
    if rc_class == 1:
        manifest[branch].status = "DONE"
        terminal_reason = f"no major feedback (round {round})"
        break
    if rc_class == 2:
        # malformed review JSON — retry the round once, else FAILED
        ...

    # 3. EVALUATE — main agent decides each major item in own context.
    #    NOT delegated to a sub-agent. Skill(do-review) runs in main.
    decisions = []
    for item in major_items:
        cited_code = read(<worktree>/<item.file>, around <item.line>, ±25)
        decision = Skill(skill="do-review",
                         args=f"--item {item.body} --code {cited_code}")
        # decision ∈ {accepted, rejected, ambiguous}
        decisions.append(decision)

    if all(d == "ambiguous" for d in decisions) and persistent_ambiguity():
        manifest[branch].status = "BLOCKED"
        terminal_reason = f"persistent ambiguous items in round {round}"
        break

    accepted = [d for d in decisions if d.kind == "accepted"]
    rejected = [d for d in decisions if d.kind == "rejected"]

    # 4. ALL-REJECTED-STREAK detection (skip Applier dispatch this round
    #    since there are no fixes to apply).
    if not accepted and rejected:
        all_rejected_streak += 1
        if all_rejected_streak >= 3:
            manifest[branch].status = "DONE"
            terminal_reason = ("3 consecutive all-rejected rounds; "
                               "Codex stuck on items main agent rejected")
            break
        round += 1
        continue
    else:
        all_rejected_streak = 0

    # 5. DISPATCH APPLIER — fresh sub-agent for this round.
    #    Brief contains pre-decided fix specs; NO /do-review invocation.
    brief = build_applier_brief(branch, worktree, round, accepted)
    handback = Agent(prompt=brief, subagent_type="general-purpose")

    # 6. INTERPRET HANDBACK (binary)
    if not handback.pushed:
        manifest[branch].status = "FAILED"
        terminal_reason = f"applier failed to push round {round}: {handback.terminal_reason}"
        break

    # 7. NEXT ROUND
    round += 1

if round > 20:
    if any_round_pushed_fixes():
        manifest[branch].status = "CONVERGED-AT-CAP"
        terminal_reason = (f"{round-1} rounds applied; remaining items "
                            "captured for PR body")
    else:
        manifest[branch].status = "CAP-REACHED"
        terminal_reason = "20 rounds, no convergence"
```

## Round-counter persistence

The round counter lives in the manifest entry's `rounds` field. `run-codex-review.py` increments it after each successful review write. Main agent never increments it manually — every increment must correspond to a written round-log file at `<rounds-dir>/<slug>.<N>.json`.

If main agent restarts mid-loop (host reboot, fresh session), it reads `rounds` from the manifest and resumes at `rounds + 1`.

## Why 20

Empirically, Codex feedback that hasn't converged by round 20 is feedback the classifier shouldn't treat as major in the first place — usually subjective items the regex catches as `unclassified_treated_as_major`. 20 is the cap that keeps cost bounded without cutting off legitimate convergence.

If a branch genuinely needs >20 rounds, the right answer is **decompose**: split the branch into N smaller branches and re-run. Don't raise the cap.

## Why 3 consecutive all-rejected → DONE

If main agent (using `/do-review` in own context) decides every major item is a false positive for 3 rounds in a row, Codex is stuck on items the evaluator has already determined aren't real. Continuing the loop is wasted compute — Codex won't change its mind, and main agent won't change its.

Main agent marks DONE with `terminal_reason: "3 consecutive all-rejected; Codex stuck on rejected items"`. Phase 5 proceeds to PR creation. The PR body should mention the persistent rejected items so the human reviewer knows main agent considered them and disagreed.

## Validation step (Applier's responsibility)

Skip re-review if the Applier broke the build. The classifier can't tell the difference between "Codex found a real bug" and "Codex found the syntax error the Applier just introduced". The Applier validates BEFORE pushing:

| Repo type | Validation |
|---|---|
| Python | `python3 -m py_compile <changed-files>` |
| TypeScript / JavaScript | `bun run type-check` or `tsc --noEmit` (on changed files) |
| Rust | `cargo check` (on changed files) |
| Skills repo with validator | `python3 <repo-root>/scripts/validate-skills.py` |
| Multi-language | the project's `Makefile` `lint` / `check` target |

If validation fails, the Applier reverts the bad commit, retries once, else hands back FAILED. Main agent marks the branch FAILED.

## Push rules

- Always to `origin`. The branch was pushed `-u` in Phase 2.
- **Never `--force`** while a review is in flight — invalidates inline review attribution and breaks the round-log → review-id mapping.
- Never push to upstream. Hard rule from `skills/run-repo-cleanup/references/fork-safety.md`.
- If a push is rejected (non-fast-forward), someone else pushed to the branch. The Applier hands back FAILED; main agent decides (typically FAILED at branch level).

## Per-round evaluation (main agent's `/do-review` step)

Main agent's central act each round (step 3 of the loop pseudocode) is **per-item evaluation via `Skill(do-review)` in own context**. Per `references/review-evaluation-protocol.md`:

```
For each major item from the classifier:
  1. Main agent reads the cited code in the worktree (Read tool, ±25 lines).
  2. Main agent calls Skill(skill="do-review", args="--item ... --code ...")
     in own context (NOT delegated to a sub-agent — empirically causes
     decision-only failure in dispatched sub-agents).
  3. Decide:
     - accepted (real issue, valid fix) → bake fix spec into Applier brief
     - rejected (false positive, stale, scope creep) → record reason; Applier never sees it
     - ambiguous (needs human) → record question; do not apply
```

Default-when-uncertain: **ambiguous**. Never silently accept. Never silently reject.

Direct-apply (skipping the evaluator) is forbidden by skill invariant 11. The pseudocode above enforces this — no major item ever reaches the Applier without a prior `accepted` decision from main agent.

## State machine

```
                 spawn-review-worktrees.py
                          │
                          ▼
                       SPAWNED
                          │
              (main agent enters Phase 3 loop; per-branch round 1)
                          │
                          ▼
                       IN-LOOP
                          │
          ┌───────────────┼─────────────────────┬───────────────────────┐
          ▼               ▼                     ▼                       ▼
     classifier:     classifier:            main-agent decisions    Applier hands
     no major        ≥1 major               all-rejected            back FAILED
          │               │                     │                       │
          ▼               ▼                     ▼                       ▼
        DONE      main agent /do-review  all_rejected_streak += 1    FAILED
                  per item, then              │
                  dispatch Applier            ▼
                          │              if streak >= 3:
                          ▼                  DONE
              (Applier applies + pushes)   else continue
                          │                     │
              (handback: pushed:bool)           │
                          │                     │
                          ▼                     ▼
                    round += 1, loop      round += 1, loop
                          │
                rounds == 20 with major still present
                          │
                          ▼
            len(round_history) ≥ 1 with pushed fixes?
                  yes / no
                  ▼     ▼
          CONVERGED-AT-CAP / CAP-REACHED

   Anywhere in IN-LOOP: persistent ambiguity (≥2 ambiguous items, or
   ambiguous-then-recurring across rounds) → main agent marks BLOCKED.
```

## Terminal states

(See SKILL.md "Convergence taxonomy" — single source of truth. Summary:)

| State | Means | PR? |
|---|---|---|
| `DONE` (no-major) | Last classifier output had `major == []` | yes |
| `DONE` (3-all-rejected) | 3 consecutive rounds where main-agent rejected all major items | yes (PR body mentions rejected items) |
| `CONVERGED-AT-CAP` | 20 rounds (or configured cap); ≥1 round of fixes pushed; remaining items deferred to PR body | yes |
| `CAP-REACHED` | 20 rounds reached, no convergence at all (no rounds pushed fixes) | **no** — surface for human |
| `BLOCKED` | Persistent ambiguity / contradictions | **no** — surface |
| `FAILED` | Tooling crash past retry budget | **no** — surface |

## When to mark BLOCKED

Main agent marks `BLOCKED` when:

- `/do-review` returned ambiguous in 2+ consecutive rounds, AND the items are roughly the same recurring item.
- `/do-review` returned ambiguous where the question requires architectural input outside the branch's scope.
- Cross-round decision contradicts (round N said apply Codex's fix; round N+1 said the prior fix made things worse — reject any further attempt).

In all cases, persist the ambiguity into the manifest's `terminal_reason` for human triage. Phase 5 will skip BLOCKED branches.

## Why per-round, not per-major-item

Main agent evaluates ALL major items in one round, dispatches ONE Applier per branch per round to apply all accepted items, pushes once, re-reviews. Per-item dispatches would be slower (one Codex call per fix) and would fragment commit history. One commit per accepted item per round is the right granularity: small enough to bisect, big enough to not flood the PR.

## Failure recovery

If an Applier crashes (heartbeat stale via manifest mtime), main agent:

1. Reads manifest entry to determine state.
2. Re-dispatches the Applier with the same brief (resumes from `rounds + 1`).
3. After 2 redispatches without progress, mark FAILED for that branch.

## Hard rules

- Main agent IS the coordinator; no Coordinator sub-agent.
- One fresh Applier per round per branch.
- Codex review is invoked via `scripts/run-codex-review.py` (which internally calls `codex-companion.mjs review --json`).
- 20-round hard cap. Never raise. Above 20 → `CONVERGED-AT-CAP` (if any rounds pushed fixes) or `CAP-REACHED` (if no rounds pushed at all).
- Never `--force` push.
- Never amend.
- Never touch `main`.
- Never push to upstream.
- Never decide DONE without classifier exit 1 OR 3-all-rejected streak.
- Never increment `rounds` without a corresponding round-log file.
- Main agent NEVER skips `/do-review` evaluation for an accepted item (invariant 11).
- Applier NEVER invokes `/do-review` (decisions are pre-made; framing causes decision-only failure).
- Applier NEVER skips an accepted item without recording a decision in the round-log JSON.
- Main agent NEVER bypasses the Applier (no direct edits to the worktree during Phase 3).

## Anti-patterns

| Anti-pattern | Why it fails |
|---|---|
| Dispatching a Coordinator sub-agent per branch (older pattern) | Long-lived sub-agents drift; depth-2 dispatch is brittle in Claude Code |
| Worker brief mentioning `/do-review` | Empirically causes 100% decision-only failure (sub-agents stop at "Verdict: apply") |
| Main agent applies fixes itself instead of dispatching an Applier | The user's spec demands sub-agent application; also Phase 3 is parallel-N-branches, main agent can't apply N branches concurrently |
| Applier pushes without validating | Validation failures get classified as Codex bugs in next round |
| Round counter increments without a round-log file | Round counter drifts; can't bisect later |
| `--force` push on a branch with active review | Invalidates round-log → review-id mapping |
| Skip the 3-all-rejected check | Codex loops on rejected items forever; cap-reached triggers without progress |
| Re-evaluate prior-round rejected items | The decision was made; don't re-litigate |
| Inventing a `DONE-PRAGMATIC` state when round-budget is exhausted | Use `CONVERGED-AT-CAP` (taxonomy is closed) |
| Asking the user "how should I proceed?" at the end of Phase 3 | The user authorized full flow; proceed to Phase 5 (see SKILL.md "Authorization rule") |

## Bottom line

Phase 3 is parallel branches under main agent's coordination, each running a fresh-Applier-per-round loop. Main agent evaluates via `/do-review` before dispatching the Applier; Applier applies the pre-decided fixes mechanically. Convergence is no-major OR 3-all-rejected. Cap is 20 rounds (`CONVERGED-AT-CAP` if any rounds applied fixes; `CAP-REACHED` if none did). Failure modes are well-defined. The brief discipline (per MISSION_PROTOCOL) plus the eval/apply role split is what separates a good convergence from a noisy one.
