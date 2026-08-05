# Dispatch rules — wave mechanics for both phases

How many agents, in what order, owning what. Both phases share three invariants:

1. **Disjoint write scopes.** No two agents in a wave may write the same path. This is what
   makes parallelism safe.
2. **The filesystem is the only channel between phases.** Agents never see each other's
   context — only files the orchestrator names in their briefs.
3. **Phases 1, 2, 4, and 6 are orchestrator-personal.** Recon, applicability, planning, and
   reconciliation are never delegated. Delegating judgement produces a plan nobody owns.

## Phase 3 — audit wave

| | |
|---|---|
| Agent | `nextjs-perf-auditor` |
| Count | one per `APPLICABLE*` domain (≤14) |
| Concurrency | **full parallel, single message** |
| Write scope | `nextjs-enhancement/findings/<domain>/` only |
| Repo access | read-only |
| Brief | `references/subagent-briefs/audit-brief-template.md` |

**Why full parallel is safe here.** These agents only read the repo and write to disjoint
folders — no shared lock, no daemon, no port. This is the opposite of browser-driven audits,
where a shared Chrome instance forces staggering. Staggering here would cost wall-clock for
no reliability gain.

**Never dispatch for `NOT-APPLICABLE`.** That verdict exists to prevent wasted agents.

**Zero findings is success.** An agent reporting a clean domain has done its job.

### Gate before Phase 4

Read every finding file personally. Verify: evidence has real `file:line` + literal text;
all six false-positive checks are ticked; no finding proposes a feature the probe called
absent; no agent wrote outside its folder. A finding failing any of these is dropped or
sent back — never silently promoted into a task.

## Phase 5 — fix waves

| | |
|---|---|
| Agent | `nextjs-perf-fixer` |
| Count | one per task cluster (≤20) |
| Concurrency | parallel **within** a wave; waves are sequential |
| Write scope | the cluster's owned files + its own task files |
| Repo access | read-write on owned files only |
| Brief | `references/subagent-briefs/fix-brief-template.md` |

### Clustering

Cluster by **shared target files**, not by domain — two tasks editing the same file must
belong to one agent or they will conflict. Then:

- Split a cluster that would exceed ~10 files or ~6 tasks.
- Merge clusters that overlap more than ~70% on files.
- A task with no file overlap and no dependency can go in any wave.

### Wave ordering

Read directly off `references/gating/composition-recipe.md` and each task's `Depends on`:

1. **Wave 1 — prerequisites and cleanups.** Deprecation removals, renames, Edge-runtime
   removal. Cheap, reversible, and often blockers for later work.
2. **Wave 2 — structural work.** Data shape, boundaries, bundle, assets.
3. **Wave 3 — work that assumes the architecture.** Prefetching, transitions, Activity
   cleanup — only after their prerequisites are `done`.

**Gate between waves:** read the task files, confirm every dependency is `done`, then
dispatch. Never chain waves blindly.

`migration-required` tasks never enter a wave — they stay `blocked-needs-human`.

### Gate after each wave

Confirm each task is `done` or `blocked` (never half-applied), `git status` is clean, and
no agent touched a file outside its cluster. Then run `scripts/status-report.py` to catch
dependency violations — a `done` task whose dependency is not `done` means the ordering was
wrong and must be re-planned before continuing.

## Caps and stop conditions

| Rule | Value |
|---|---|
| Audit agents | ≤14 (one per domain) |
| Fix agents | ≤20 |
| Files per fix task | ~10 — split beyond that |
| Retries per failed task | 0 — revert, mark blocked, move on |
| Failure threshold | >⅓ of tasks fail verification → stop the run |

Never retry a failed approach in the same run. A failure is evidence the plan was wrong,
not that the agent was unlucky.

## Brief hygiene

Every brief carries: the target repo root, its exact write scope, the read scope (specific
files, not "the references folder"), the applicability verdict, the definition of done, and
the handback shape. A brief missing its write scope is the single most common cause of
agents trampling each other — never dispatch without it.
