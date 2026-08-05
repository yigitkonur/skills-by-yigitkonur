# Completion report template — `nextjs-enhancement/02-completion-report.md`

Phase 6 output. Orchestrator-personal. The honest account of what actually happened —
applied, blocked, failed, skipped. Written after `scripts/status-report.py` runs.

**Report faithfully.** A run where most tasks are blocked is still a good run if the plan
is sound and the reasons are true. A run that claims success it cannot evidence is not.

```markdown
# Completion report — <repo name>

**Run:** <YYYY-MM-DD> · **Branch:** `nextjs-fluidity/<YY-MM-DD>`
**Plan:** [`tasks/00-INDEX.md`](tasks/00-INDEX.md)

## Outcome

<Two or three sentences. What changed, what did not, what a human must decide next.
Lead with the outcome, not the process.>

| Status | Count |
|---|---|
| done (applied + verified) | |
| blocked (verification failed, reverted) | |
| blocked-needs-human (one-way doors) | |
| pending (not attempted) | |
| wontfix | |

## Applied and verified

| # | Task | Files | Commit | Verification rung | Evidence |
|---|---|---|---|---|---|
| 01 | <title> | `<paths>` | `<sha>` | build/runtime/measured | `<what was observed>` |

Each row's `Evidence` is what was actually seen — a command's output, a header, a panel
state. Never "looks good".

## Prepared, awaiting human decision

One-way doors are deliverables, not failures.

| # | Task | Why blocked | Exit cost | Checklist |
|---|---|---|---|---|
| | | `migration-required` | <named cost> | in the task file |

## Failed verification and reverted

| # | Task | What failed | Output | Revert commit |
|---|---|---|---|---|

Include the real output. Do not summarise a failure into a shrug.

## Withheld — not available on this install

Carried from `01-applicability.md`. States what this skill knows but deliberately did not
recommend, and when to revisit.

## Not proposed — already correct

What the repo already does right. Prevents future re-litigation.

## Measurement

- Baseline captured at Phase 1? yes/no
- Metrics re-measured after fixes? yes/no
- If no: **say the performance effect is unverified.** Do not imply a metric moved.

| Metric | Before | After | Delta |
|---|---|---|---|
| LCP p75 | | | |
| INP p75 | | | |
| CLS p75 | | | |
| Build time | | | |

Omit rows with no real numbers rather than filling them with estimates.

## What to do next

1. Review and decide the `blocked-needs-human` tasks.
2. Re-run any `blocked` task after fixing its root cause.
3. Merge the branch if the applied changes hold.
4. Re-run this skill after the next Next.js upgrade — the withheld list is the reason.

## Run integrity

- Working tree clean before execution: yes/no
- All changes on the run branch: yes/no
- Nothing pushed, merged, or deployed: confirmed
- Dependencies/lockfile untouched: confirmed
- Rails triggered: `<list, or "none">`
```

## Rules

1. **Every task in `tasks/` is accounted for.** Any task absent from every section is a
   reporting failure.
2. **Verification evidence is quoted, not characterised.**
3. **Unmeasured is stated, never implied.** If no baseline existed, say the effect is
   unverified — and say task 01 exists to fix that for next time.
4. **Failures keep their output.** A reverted task's report includes why.
5. **Rails that fired are named.** A halted run explains which stop condition triggered
   and what remains on disk.
6. **No forward-looking praise.** Describe what happened; recommendations belong in "what
   to do next".
