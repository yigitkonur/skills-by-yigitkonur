# Mission Gravity — What Makes a Codex Dispatch Work

This skill's scripts are plumbing. The prompts you write are the real engine. This guide is about how to write prompts that consistently land committable code.

These observations come from ~20 real dispatches where the same skeleton was used with varying detail. The gap between a plan that shipped in 10 minutes and one that bailed silently was almost always in the prompt.

## The mental model: gravity, not walls

When you write a prompt for Codex, don't think "how do I constrain this agent?" Think "how do I make it impossible for the agent to miss the target?"

Gravity: the plan objective is so clear that every path the agent explores pulls back toward it.

Walls: rigid step-by-step instructions that cap output quality at your imagination.

The agent can read neighboring files, research libraries, trace upstream causes. Don't fence that off — most of the time that exploration is what solves the problem. Instead, make the destination so concrete that no matter where it wanders, it comes back.

Concrete destination examples:
- "A user can create a schedule via the UI; the cron endpoint finds it and generates a report with email delivery via the provider already wired into `src/lib/email.ts`." (This is gravity — the agent knows exactly what "done" looks like.)
- "Implement report scheduling." (This is a wall; there's no gravity to pull back to.)

## Ceilings, not floors

When setting limits, always upper-bound, never lower-bound.

- "Write at minimum 3 commits." → agent pads with garbage commits to hit the floor.
- "Write at most 10 commits, one per logical slice; you can come in under." → agent naturally chunks work.

- "Run at least 5 test cases." → agent invents filler tests.
- "Run all existing tests plus any new ones required by the plan; aim for full coverage of the new code." → agent writes useful tests for what it built.

- "Cover at least 80% of edge cases." → agent pads cases that don't add value.
- "Cover the edge cases explicit in the plan; you may add others you notice during implementation." → agent focuses + catches real issues.

Floors incentivize waste. Ceilings signal "I've budgeted for depth; find the natural stopping point."

## The five layers every prompt should address

Not every layer needs heavy weight — calibrate based on task complexity. But every non-trivial plan touches all five.

### 1. Framing — what problem are we solving?

For most coded plans this is already in the plan file. But explicit reference matters:

```
Implement plan <name>. Read the plan file at <absolute-path> before writing code.
```

Without this the agent decides what problem to solve from your prompt alone and will often narrow the scope incorrectly.

### 2. Discovery — what does the agent need to know?

Two dimensions: internal (your codebase) and external (docs, dependencies).

Internal discovery should be framed as understanding goals, not search queries:
- "Understand how existing alert-rule evaluation works before writing the brand-health alert emission."
- NOT: "grep src/lib/automation/alert-evaluator.ts to see the pattern."

External: "If you need docs for d3-sankey, look at the npm page or the github examples directory." Let the agent decide if it needs them.

### 3. Evidence — what findings matter?

For coded plans this usually means: conventions the agent must follow.

- "Existing server actions return `{success, error?, data?}`."
- "Components in this codebase use TanStack Query for data fetching; raw `useEffect + fetch` is forbidden."
- "Schema changes use conditional-spread on Prisma inputs because of exactOptionalPropertyTypes."

Be specific; enumerate the conventions the agent will need.

### 4. Execution — actually implement

This layer is where most of the agent's tokens go. You mostly get out of the way. A 1-sentence framing is enough:

"Implement the plan: extend the schema, add the actions, wire the UI, write tests."

Let the agent choose the order, the specific file-to-file traversal, the refactorings.

### 5. Verification — prove it worked

The most load-bearing layer. Without it the agent's "done" is subjective.

```
Definition of Done:
- npx tsc --noEmit: 0 errors
- npx vitest run: all existing + new tests pass
- npx eslint .: 0 errors
- ≥2 commits with multi-paragraph bodies
```

These must be:

- **Binary** — yes/no, no vague "reasonable."
- **Specific** — "0 errors" not "few errors."
- **Verifiable** — the agent can run the command and read the output.

## The "why" is load-bearing

Today's LLMs have good theory-of-mind. Given the reasoning behind a rule, they generalize it correctly to edge cases. Given only the rule, they apply it brittlely.

Bad: "Do not use `as any`."
Good: "Do not use `as any`. We pay the tsc strict+ cost up front so that future refactors are safe without regressions. When you hit a narrow-by-cast urge, the right move is usually a type-predicate helper or an explicit Zod-parsed local; the `as any` hides real bugs."

The longer version costs 40 tokens but prevents the agent from working around it with `as unknown as T` or similar dodges.

## Specifying what NOT to touch

Parallel-dispatch plans have implicit file ownership. Make it explicit:

```
Scope:
- You own: src/actions/sentiment-keywords.ts (new), src/components/charts/keyword-cloud.tsx (new), src/components/sentiment-content.tsx (modify — NEW tab only)
- Do NOT touch: src/actions/sentiment.ts (another agent is modifying it concurrently)
- Do NOT touch: prisma/schema.prisma (no schema changes in this plan)
- Do NOT refactor: any file not listed above, even if it "could be better"
```

Without explicit not-touch lists, agents aggressively refactor adjacent code. This creates merge conflicts with parallel plans that were supposed to own those files.

## When you see failure, ask: was the prompt concrete enough?

Post-mortem every failed dispatch:

- Did the prompt list concrete files, or "implement the feature"?
- Did the prompt have a binary DoD, or vague "looks good"?
- Did the prompt specify not-touch files?
- Did the prompt start with SUBAGENT-STOP to bypass meta-skills?
- Did the prompt explain WHY the constraints matter?

Usually one of these is the cause. The agent itself is not the failure point in 9 of 10 cases.

## One test for prompt quality

Before dispatching: read your prompt and ask "if I handed this prompt to a mid-level developer with zero context on this project, would they know what to do?"

If yes → dispatch.
If no → you need more context. Either a longer prompt, or a smaller plan.

Codex is roughly as capable as a mid-level developer with the patience of a machine. Treat it that way.
