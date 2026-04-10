# Reasoning Levels: When to Use low/medium/high/xhigh

Higher reasoning = more thinking tokens burned before the agent writes its first line of code. More thinking tokens = longer process lifetime = higher chance the Codex process hits a timeout or memory ceiling and exits mid-task.

## Reliability Data (observed across 200+ spawns)

| Level  | Reliability | Avg Think Tokens | Typical Use              |
|--------|-------------|------------------|--------------------------|
| low    | ~100%       | 200-800          | Mechanical edits, moves  |
| medium | 50-70%      | 2k-8k            | Multi-file refactors     |
| high   | 30-50%      | 8k-30k           | Architecture decisions   |
| xhigh  | 10-30%      | 30k-80k+         | Novel design problems    |

The numbers are not theoretical. They come from real wave dispatches where identical tasks were retried at different levels. A task that completes at `low` in 40 seconds will attempt the same work at `high` but die at the 90-second mark because it spent 60 seconds thinking before touching a file.

## The Core Insight

Reasoning tokens are consumed BEFORE execution begins. The Codex process has a finite lifetime. Every token spent reasoning is a token not available for doing the actual work. When the process exits, partial work may exist on disk — but you wanted a completed task, not a partial one.

## Decision Flowchart

```
Is the task purely mechanical?
  (rename, move file, search-replace, extract method, add import)
  → YES → low
  → NO ↓

Does the task require reading multiple files to understand context?
  → NO → low
  → YES ↓

Does the task require making design decisions?
  (choosing between approaches, defining interfaces, structuring new code)
  → NO → medium
  → YES ↓

Is the design space well-constrained by your prompt?
  (you specified the interface, the approach, the structure)
  → YES → medium
  → NO ↓

Is this a novel architecture problem with no clear precedent in the codebase?
  → NO → medium
  → YES → high (accept the reliability hit)
```

Almost never use `xhigh`. If a task needs that much reasoning, break it into smaller tasks that each need `medium` or less.

## When Each Level Excels

### low (default for everything)
- Extract a type/function/view to a new file
- Add a new file following an existing pattern
- Wire up imports and references after an extraction
- Run a codemod-style transformation
- Fix a specific compiler error
- Write tests for an existing function

### medium (use when the agent must read before writing)
- Refactor a 400-line function into a controller with multiple helpers
- Implement a feature that touches 3-5 files with cross-references
- Write a new module that must integrate with existing protocols/interfaces
- Debug a failing test by reading the test, the implementation, and related code

### high (use sparingly, expect retries)
- Design a new subsystem interface from requirements
- Migrate from one architecture pattern to another
- Complex multi-step refactors where order of operations matters

### xhigh (almost never)
- Only when you have tried `high` and the agent consistently makes wrong design choices
- Accept that you may need 3-4 spawns to get one completion

## Practical Patterns

### Compensate with prompt quality, not reasoning level
A well-written prompt at `low` beats a vague prompt at `high`. Instead of raising the reasoning level, try:
- Specifying the exact files to read first
- Describing the target interface/structure
- Providing the mental model ("this follows the delegate pattern like X")
- Listing the exact steps as verification commands

### Retry strategy by level
- `low` task fails → check if it's a prompt clarity issue, not a reasoning issue
- `medium` task fails → try once more at `medium` with a better prompt; if still fails, try `high`
- `high` task fails → check partial work recovery before re-spawning
- `xhigh` task fails → break the task into 2-3 smaller tasks at `medium`

### Budget math
Codex process budget is roughly 100k-200k tokens total (input + output + reasoning). A `low` task uses ~5% on reasoning, leaving 95% for execution. A `high` task uses ~40% on reasoning, leaving 60%. An `xhigh` task can use 70%+ on reasoning, leaving barely enough to write code.

## Anti-Patterns

1. **Defaulting to high "just to be safe"** — This is backwards. Higher reasoning means LESS safe (lower completion rate). Default to `low`.

2. **Using xhigh for complex but well-defined tasks** — If you can describe exactly what needs to happen, the task is well-defined. Use `low` or `medium` and put the definition in the prompt.

3. **Raising reasoning level after a failure** — First check: was the prompt clear? Was the task too large? Did the agent have the right files? Reasoning level is the LAST knob to turn.

4. **Batch-spawning all tasks at high** — In parallel dispatch, higher reasoning increases the chance that ANY task kills the shared process, which kills ALL tasks. Keep parallel batches at `low`.

## Real Example

Wave 4 of a refactoring project needed to extract 7 controllers from a 2000-line ContentView. Every extraction was mechanical: read the section, create a new file, move the code, wire up the delegate. All 7 were spawned at `low`. Six completed successfully. One died due to an unrelated auth issue. The partial work was recovered. Total: 7/7 completed with zero reasoning waste.

Had these been spawned at `high`, the math says 3-4 would have completed. The rest would need retries. Same outcome, 2x the cost, 3x the wall-clock time.

**Default to low. Compensate with prompt quality.**
