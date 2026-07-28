# Optimization workflow: the engagement sequence

The ordered sequence for any CI/CD optimization engagement. Read this before
touching workflow YAML: most failed optimizations skip the inspection and
measurement steps and patch a guess. Steps 1–7 are analysis and are always
safe; steps 8+ mark where authorization gates apply.

## Contents

- [Phase A — Inspect before proposing (steps 1–4)](#phase-a--inspect-before-proposing)
- [Phase B — Measure and rank (steps 5–8)](#phase-b--measure-and-rank)
- [Phase C — One bounded experiment (steps 9–12)](#phase-c--one-bounded-experiment)
- [Phase D — Remote verification (steps 13–14)](#phase-d--remote-verification)
- [Phase E — Report and stop (steps 15–16)](#phase-e--report-and-stop)

## Phase A — Inspect before proposing

**1. Capture the target.** Which pipeline, which event (PR, push, merge
queue, schedule), which branch, what "fast enough" means (target median and
p95), which checks are required and must remain required. If the user has
no target, propose one from the baseline and get agreement.

**2. Read the repository's rules first.** CONTRIBUTING/AGENTS files,
branch protection, required checks, CODEOWNERS on workflow paths. An
optimization that violates a repo rule is a defect, not a win.

**3. Read every workflow file that fires on the target event** — including
reusable workflows it calls and anything triggered via `workflow_run`.
Sketch the real job DAG from `needs`/dependencies, not from stage names.
Note triggers, path filters, concurrency groups, matrices, caches, runner
labels, timeouts, and permissions.

**4. Inventory what already exists.** Existing caches and their hit
history, existing change detection, existing sharding, runner pools and
their labels, and any prior optimization attempts in git history. Removing
a broken optimization is often the best first experiment.

## Phase B — Measure and rank

**5. Mine run history aggregate-first.** Use the provider's aggregated
stats (or `references/avrea/cli-evidence.md` on Avrea) before
hand-collecting: run counts, median/p95 durations, failure and flake
counts over a stated window. Then drill into representative runs. Protocol
details, sample rules, and evidence rungs: `references/measurement.md`.

**6. Split wall time into queue / setup / execution / transfer /
finalization.** Each has a different fix; a 20-minute wall with 9 minutes
of execution is a capacity problem, not a test problem. Queue analysis and
concurrency ceilings: `references/capacity-and-contention.md`.

**7. Reconstruct the critical path.** Which jobs' start offsets plus
durations determine the finish line, and how often each job is on that
path. Rank candidate bottlenecks by `critical-path seconds saved ÷ effort
and risk` — not by total CPU seconds.

**8. Check cache reality, not cache config.** A configured cache with cold
hits, volatile keys, or restore cost exceeding the work it saves is a
pessimization. Hit counts, sizes, key discipline: `references/caching.md`.

## Phase C — One bounded experiment

**9. Choose the single smallest reversible change** that attacks the
top-ranked bottleneck. Preference order: prevent unneeded work → cancel
stale work → reuse verified prior work → fix cache correctness → remove
artificial dependencies → parallelize independent work → shard by measured
duration → move fewer bytes → improve capacity → architectural change
(last, and only with demonstrated need).

**10. Write the experiment card before editing:** evidence observed;
expected wall-clock effect and on which percentile; effectiveness risk and
which gate could be affected; cost effect; rollback (usually `git revert`).
If the card cannot name an expected effect, the experiment is a guess —
return to Phase B.

**11. Check the effectiveness contract.** If the change touches required
checks, trust boundaries, cache write policy, merge-base logic, or artifact
identity, read `references/effectiveness-contract.md` and resolve conflicts
in the contract's favor.

**12. Edit and validate locally.** Smallest diff; workflow syntax/schema
check where tooling exists; keep unrelated cleanup out of the diff.
Pushing the change is an outward action — do it when the task calls for it
or with authorization, per the SKILL.md gate list.

## Phase D — Remote verification

**13. Push and watch the exact SHA to a terminal verdict.** Use
`scripts/ci-watch.py` per `references/feedback-loops.md`. React to the
first red with the attached log command; a superseded or timed-out watch
is "no verdict", not a result. Never validate against branch-latest.

**14. Compare matched runs.** Same event type, comparable commit, same
runner class, interleaved with baseline runs if the pool is contended
(`references/capacity-and-contention.md`). Compare median and p95 wall
clock, queue time, cache behavior, first-time pass rate, and cost. One
fast run proves little; state the sample size.

## Phase E — Report and stop

**15. Report per the SKILL.md report contract** — including neutral and
disproved hypotheses. A disproved hypothesis ("bigger runners did not help;
queue share was the bottleneck") is a paid-for result; losing it forces the
next person to buy it again.

**16. Stop when:** the target is met; the remaining bottleneck is fixed
cost (billing floor, provider limits) the team accepted; two repair
attempts failed the same way (question the approach, not the retry count);
or every remaining idea weakens a gate. Say which stop rule fired.

## Anti-sequence: the failure mode this file exists to prevent

Do not: guess a fix from the workflow file alone → push → stare at
branch-latest → see green → claim faster. That sequence has produced most
of the regressions in this skill's defect corpus: unmeasured pessimization,
broken required checks, stale-SHA greens, and false capacity conclusions.
