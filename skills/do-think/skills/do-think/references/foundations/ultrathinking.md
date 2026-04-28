# Ultrathinking — When the Cost of Being Wrong is High

Use ultrathinking only when the change is hard to reverse, the blast radius is broad, or the team will inherit this decision for a long time.

Ultrathinking is not maximal analysis. It is **disciplined analysis scaled to irreversible or high-cost decisions**. The discipline lives in the foundations:
- Effort tier set to **High** (`effort-calibration.md`)
- Stress-test trio runs strict (`stress-test-trio.md`) — Inversion with named mitigations baked into the plan; Ladder of Inference depth audit; Second-Order at 10-min/10-mo/10-yr scales
- Verification path defined before action; rollback named explicitly

## When to escalate to ultrathink

- The change is hard to reverse
- The change could alter architecture or workflow
- The blast radius is broad (multiple teams, customers, services)
- The team will inherit this decision for a long time
- Weak assumptions would be expensive to discover late

## The ultrathink pass — what changes vs. standard Tier-High

Standard Tier-High already runs strict trio + full grounding. Ultrathink adds:

1. **Widen the frame.** Ask:
   - What problem am I really solving?
   - What outcome actually matters?
   - What am I assuming about constraints, users, the system?
   Re-enter Phase A2 (reframe) if the widened frame exposes a different problem.

2. **Compare real options.** Do not compare one real option to two strawmen. Keep 2-3 *serious* options alive through Phase C1. Use the SKILL.md routing to reach `frameworks/zwicky-box.md` if option generation is dry.

3. **Force the simplest adequate path.** Reject solutions that are technically clever but operationally heavier than the problem needs. The path with the smallest surface area that still solves the problem usually wins on long-horizon costs.

4. **Define the rollback explicitly.** If the chosen path fails in production, what is the safest recovery move? Write it. If the answer is "we can't roll back," that's a fact about the option, not a quirk — surface it.

## Solo mode application

In Solo mode, ultrathink is what you do when the opening contract reads `Tier: High`. The discipline is silent but visible in the artifact: stress-test outputs are written, mitigations are baked in, rollback is named.

## Interactive mode application

In Interactive mode, ultrathink runs through the 5 forks (`modes/interactive-brainstorm.md`) with the user validating each phase. The forks are *especially* load-bearing at this tier; do not compress.

## Anti-patterns

| Anti-pattern | Counter |
|---|---|
| Treating every decision as ultrathink-worthy | Tier inflation. Run the calibration matrices; reserve ultrathink for genuine High-tier work. |
| Ultrathinking with no rollback path | If you cannot name the rollback, you have not finished. Either find a rollback, or accept the path as one-shot and surface that explicitly. |
| Strawman options ("Option A vs. nothing") | Compare *real* options. Use Zwicky Box or Six Thinking Hats to widen if generation is dry. |
| Over-engineering "the right" solution when a smaller path solves the problem | The simplest adequate path is the ultrathink answer most of the time. Clever ≠ correct under operational load. |
