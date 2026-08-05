# Safety rails — the autonomous execution contract

This skill plans **and executes** without a mid-run approval prompt. That is only
defensible because the rails below are hard stops, not guidance. A fix agent that violates
one has failed the task regardless of whether the code works.

## Rail 1 — one-way doors are never auto-executed

Any task whose `Reversibility:` is `migration-required` (per
`references/gating/lockin-reversibility.md`) is written to `tasks/` with
`Status: blocked-needs-human` and its pre-flight checklist inline. The skill **reports**
it; it does not perform it.

Always in this class: enabling `cacheComponents` · changing public URL or locale-routing
policy · canonical/308 redirect changes · Edge→Node migration of live route logic ·
adopting `"use cache: remote"` or a custom cache handler · repo-wide barrel or TypeScript
toolchain migrations · anything that alters a CMS schema.

The completion report lists these separately as "prepared, awaiting human decision" —
they are a deliverable, not a failure.

## Rail 2 — git-guarded execution

Before Phase 5 begins:

1. **Refuse to start on a dirty working tree.** Report the dirty paths and stop. The user's
   uncommitted work must never be entangled with generated changes.
2. **Work on a branch** — `nextjs-fluidity/<YY-MM-DD>` — never directly on the default branch.
3. **One commit per task**, message `perf(<domain>): <task title>` with a
   `Task: nextjs-enhancement/tasks/NN-<slug>.md` trailer, so any single task can be
   reverted in isolation.
4. **Never push, never open a PR, never merge.** Landing the work is the user's call.

## Rail 3 — verification gates completion

A task reaches `Status: done` only after its own **Verification command** has been run and
passed. Not "the edit looks right" — run it.

On failure: revert that task's commit (`git revert` or `git checkout --` the touched
paths), set `Status: blocked`, and paste the failure output into the task's
`Fix tracking` block. Never leave a half-applied task marked done, and never weaken a
verification to make it pass.

If a task has no runnable verification, it is not ready to execute — it stays `pending`
with a note, and the completion report says so.

## Rail 4 — severity and blast-radius floor

| Severity | Reversibility | Auto-apply? |
|---|---|---|
| critical / major | fully-reversible | yes |
| critical / major | component-level-revert | yes, if single-domain and verification exists |
| any | migration-required | **no** — `blocked-needs-human` |
| minor | fully-reversible **and** single-file | yes |
| minor | anything else | write the task, do not apply |
| informational | — | never a task on its own |

A change touching more than ~10 files in one task must be split before it may execute.

## Rail 5 — no side effects the task did not declare

Fix agents may not: install, upgrade, or remove dependencies · modify lockfiles ·
run `next build` / `next dev` unless a verification command explicitly calls for it ·
edit CI configuration, `vercel.json`, or environment files · touch `.env*` · run codemods
that rewrite files outside the task's declared scope · reformat untouched code.

Scripts shipped with this skill are read-only, except `scaffold-plan.py --apply`, which
only creates the artifact directory tree.

## Rail 6 — never fabricate a finding or a fix

Zero findings is a valid audit result. An agent that finds nothing writes nothing.

Every task's evidence must be a real `file:line` with the literal matched text. Every
recipe must come from the domain's `references/fix/<domain>.md`. If a repo's situation is
not covered by a recipe, the task says so and stays `pending` — inventing an API or
extrapolating a pattern is a failure, not initiative.

## Rail 7 — respect deliberate divergence

A repo that has already made a considered choice is not broken. Config that differs from
the corpus default **with an adjacent explanatory comment**, a custom implementation where
a library exists, or an intentionally disabled optimization are `informational` at most.
See `references/workflow/false-positives.md`.

The question is never "does this match the reference config?" — it is "does this cause a
measurable problem, or violate a documented constraint?"

## Rail 8 — stop conditions

Halt the run, write what exists, and report when:

- the working tree is dirty at Phase 5 (rail 2)
- the capability probe returns `unresolved` **and** the repo has no `node_modules` —
  finish the audit, mark everything `version-inferred`, execute nothing
- more than a third of fix tasks fail verification — something systemic is wrong; stop
  rather than continue reverting
- a task's change would conflict with another task's already-applied change in the same
  file (re-plan instead of racing)
- the repo is not a Next.js App Router project at all

## What the user gets when the rails trigger

Silence is not acceptable. The completion report always states: applied and verified ·
prepared but blocked on a human (with the reason and the checklist) · failed verification
and reverted (with output) · skipped and why. A run where every task is blocked is still a
successful run if the plan is sound and the reasons are honest.
