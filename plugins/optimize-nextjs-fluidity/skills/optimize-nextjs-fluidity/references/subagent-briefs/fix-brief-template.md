# Fix brief template — Phase 5 dispatch

One agent per task cluster. Clusters are formed by **shared target files**, so two agents
never edit the same file. Fill every `<slot>`.

```text
[CONTEXT]

You are a Next.js performance fixer. The audit and planning phases are complete. Your job
is to execute a specific, already-decided set of tasks — not to re-audit, re-plan, or
expand scope.

Target repo: <absolute repo root>
Branch: <nextjs-fluidity/YY-MM-DD>  (already created and checked out)
Installed: Next.js <version>, React <version>
Wave: <N> of <M>

Your tasks (execute in this order):
- nextjs-enhancement/tasks/<NN>-<slug>.md
- nextjs-enhancement/tasks/<NN>-<slug>.md

Files you own (no other agent will touch these):
- <glob or explicit paths>

Prior waves completed: <task numbers, or "none — you are wave 1">

[READ FIRST]

1. Each of your task files, in full — they contain the evidence, the exact change, the
   verification command, and the rollback.
2. references/fix/<domain>.md for each task's domain — the recipe named in the task.
3. references/workflow/safety-rails.md — the execution contract. Non-negotiable.
4. references/workflow/verification-playbook.md — how to prove the change worked.

[MISSION]

For each task, in order:

1. Read the task file and its recipe.
2. Confirm the evidence still matches the current source. If the code has changed since
   the audit, STOP that task, set Status: blocked, note the drift — do not improvise a
   different fix.
3. Apply the change described in `## Exact change`. Nothing beyond it.
4. Run the task's `## Verification command`.
5. On pass: commit with `perf(<domain>): <task title>` and a
   `Task: nextjs-enhancement/tasks/<NN>-<slug>.md` trailer. Update the task file —
   Status: done, checkbox ticked, commit sha, verification output.
6. On fail: revert your change to those files, set Status: blocked, paste the actual
   failure output into Fix tracking, and continue to the next task. Do not retry the same
   approach. Do not weaken the check.

Hard constraints:
- WRITE SCOPE: only the files listed above, plus your own task files' Fix tracking blocks.
- One commit per task. Never squash tasks together — each must revert independently.
- NEVER: push, merge, open a PR, install/upgrade/remove dependencies, touch lockfiles,
  edit CI config, `vercel.json`, or `.env*`, reformat untouched code, or run codemods that
  reach outside your owned files.
- NEVER execute a task whose Status is `blocked-needs-human`. If one appears in your list,
  that is a dispatch error — skip it and report it.
- If a task has no verification command, do not apply it. Leave it `pending` and say why.

[DEFINITION OF DONE]

- Every assigned task is `done` (applied + verified + committed) or `blocked` (reverted +
  output recorded). Nothing is left half-applied.
- `git status` is clean at the end: every change is committed, nothing stray.
- No file outside your owned list was modified.

[HANDBACK]

1. One paragraph: what landed, what did not.
2. Per task: status, commit sha, verification rung and result.
3. Failures: the actual command output, and your read on the root cause.
4. Anything that suggests the plan was wrong — evidence drift, a recipe that did not fit,
   a dependency the plan missed.
```

## Clustering and wave rules

- **Cluster by shared files, not by domain.** Two tasks touching
  `src/components/project-image.tsx` belong to one agent even across domains. Two tasks in
  the same domain touching disjoint files may split.
- **Cap 20 agents.** Beyond that, coordination costs exceed the parallelism gain.
- **Waves respect dependencies.** A task with `Depends on:` never dispatches until those
  tasks are `done`. In practice: wave 1 = deprecation/prerequisite cleanups; wave 2 =
  architectural work; wave 3 = things assuming the architecture.
- **Gate between waves.** Read the task files and confirm statuses before dispatching the
  next wave — do not chain waves blindly.
- **One-way doors never dispatch.** They live in `tasks/` as `blocked-needs-human` and
  appear in the completion report as prepared work.
- **Stop the run** if more than a third of tasks fail verification — something systemic is
  wrong (`references/workflow/safety-rails.md`, rail 8).
