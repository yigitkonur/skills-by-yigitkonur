# Agent Thinking Steering

**Meta-cognition for the cleanup flow.** This file tells the agent *how to think* about each phase, not what commands to run. Commands alone don't catch the subtle failures — bad ordering, scope creep, premature commits — that this skill is designed to prevent.

## Decomposition — finding the N

Most cleanup work starts feeling like one big pile ("there are 30 dirty files"). It's actually **N logical units**:

- N commits within a branch.
- N branches across worktrees.
- N PRs across branches.
- N items within a PR.

**The decomposition question at every level:** *What is the natural N here, and what is each element of N?*

If you can write down the list of N elements with one-sentence names each, you understand the unit. If you can't, you're looking at something too large. Keep decomposing.

### Decomposition at file level

Question: *If I had to commit this file in isolation, what would the commit message be?*
- Answer is crisp → the file is one concern, stage it.
- Answer is vague → split with `git add -p`.

### Decomposition at branch level

Question: *If I had to open a PR with only this branch's commits, what would the title and summary be?*
- Answer is crisp → branch is one concern, push it.
- Answer is vague → some commits belong on a different branch.

### Decomposition at PR level

Question: *What would the reviewer learn from reading only the PR title and summary?*
- Answer is "everything important" → good PR boundary.
- Answer is "I'd still need to read the diff" → PR is too broad.

## Ordering — foundation → leaf

When you have N elements and they interact, **dependencies drive order**:

- A commit that renames a symbol must come before commits that reference the new name.
- A PR that moves a module must merge before PRs that import from the new location.
- A branch that refactors a shared helper must merge before branches that use the helper.

**The ordering question:** *If I do B before A, what breaks?*
- Nothing breaks → order is flexible; do simplest first.
- Something breaks → A is the foundation for B; A goes first.

This generalizes: commits → branches → PRs all follow the same foundation-first rule.

## Verification — always from state, never from memory

Every time you're about to claim something is done, ask: *How do I **know**?*

- "The tests pass" — did you **run** them? Which ones? What output?
- "The PR is on the fork" — did you **check** the URL? Which URL?
- "The branch is merged" — did you **confirm** with `git branch --merged main`?
- "The working tree is clean" — did you **run** `git status`?

Replace every "I think so" with either evidence or a probe. Memory lies on long sessions. The repo state does not.

## When to stop and re-audit

Stop forward motion and re-run `scripts/audit-state.py` when:

1. **Surprise.** You find a file / branch / worktree you don't remember.
2. **Contradiction.** Two signals disagree (e.g., `git status` says clean but `gh pr list` shows an open PR from work you thought was abandoned).
3. **Rabbit hole.** You started on task X and are three levels deep in unrelated fixups.
4. **Time dilation.** You've been in one phase for more than ~15 minutes without progress.
5. **Rationalization.** You catch yourself thinking "this commit is close enough" or "I'll clean up later".

Re-audit is free. It costs 30 seconds and saves bad commits / bad PRs / bad state.

## Red-flag thoughts (stop and re-audit)

Source these to the top of your awareness:

| Thought | Red flag because |
|---|---|
| "Let me just squash these." | You're losing granular evidence for no reason. |
| "I'll open this on upstream as a courtesy." | Never. Fork-only. |
| "Good enough." | Tidy is binary. There's no "good enough". |
| "Reviewer will figure it out." | Write the PR body. |
| "I'll amend real quick." | Never amend published commits. Forward-fix. |
| "Thanks for the great …" | Performative. Delete. |
| "The clean-up can wait." | Phase 5 isn't optional. |
| "Let me skip Phase 0." | Bad Phase 1 follows. |
| "I already know the state." | The repo state is authoritative, not memory. |
| "Let me check if this has been added before doing anything else." | Rabbit hole. You're procrastinating. |

If any fires, **run `scripts/audit-state.py` before doing anything else**. The audit will either confirm your impulse or snap you back.

## Escalation — when to stop and ask

There's always an escape hatch. Ask the user when:

- You can't determine the correct merge order for two worktrees, and the script's suggestion feels wrong.
- You find a file you can't classify as "belongs here" or "doesn't belong here" — even `to-delete/` feels presumptuous.
- You see secrets in a tracked file and are unsure of the rotation/revoke protocol.
- Two worktrees have overlapping commits that might be the same work done twice.
- Open PRs on upstream that predate this session.

Asking is not failure. Wrong decisions on any of these is irreversible.

## The meta-pattern

Each phase has the **same structural pattern**:

```
1. Audit   (what is the state?)
2. Decompose (what are the N pieces?)
3. Order   (in what sequence?)
4. Execute (one at a time, verify each)
5. Tidy    (back to clean state, plus the delta)
```

If you're stuck, map your situation to this pattern and find the step you skipped. Usually it's 1 (audit) or 2 (decompose).

## Self-questioning at phase boundaries

Before leaving each phase, ask:

- **End of Phase 0:** *What surprised me? Is any of it blocking?*
- **End of Phase 1:** *Is `git status` clean? Can I describe every commit in one sentence?*
- **End of Phase 2:** *Do I have a written merge order with rationale?*
- **End of Phase 3:** *Is every PR on the fork, not upstream?*
- **End of Phase 4:** *Could the reviewer answer "why this approach" from my body alone?*
- **End of Phase 5:** *Is every check in the tidy list green? Would a subagent confirm?*

If any answer is "no" or "I think so", you haven't finished that phase. Go back.

## The bottom line

The skill's commands are table stakes. What distinguishes a successful cleanup from a bad one is **how the agent thinks about the state**: decomposing, ordering, verifying, stopping when state disagrees with assumption. The commands execute the decision; the thinking decides which command to run.

Cultivate audit → decompose → order → execute → tidy as a reflex. Every phase. Every time.
