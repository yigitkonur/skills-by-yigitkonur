# Index template — `nextjs-enhancement/tasks/00-INDEX.md`

Phase 4 output, updated at Phase 6. The single page a human reads to understand what the
run decided, in what order, and why. Written by the orchestrator after clustering findings.

```markdown
# Enhancement plan — <repo name>

**Planned:** <YYYY-MM-DD> · **Installed:** Next.js `<version>`, React `<version>`
**Archetype:** `<archetype>` · **Mode:** autonomous execution
**Inputs:** [`../00-recon.md`](../00-recon.md) · [`../01-applicability.md`](../01-applicability.md)

## Summary

<Two or three sentences: how many findings across how many domains became how many tasks,
what the headline problems are, and what is deliberately blocked on a human.>

| | Count |
|---|---|
| Findings filed | |
| Tasks planned | |
| Auto-apply eligible | |
| Blocked — needs human (one-way doors) | |
| Withheld — version-gated | |

## Execution order

Ordinals encode dependencies. A task never precedes something it depends on.

| # | Task | Domain | Sev | Reversibility | Auto | Depends on | Step |
|---|---|---|---|---|---|---|---|
| 01 | [<title>](01-slug.md) | | | | yes/no | none | <1-14> |
| 02 | [<title>](02-slug.md) | | | | | 01 | |

`Step` = the composition-recipe step from `references/gating/composition-recipe.md`.

## Dependency graph

```text
01 measurement baseline
  └─ 03 image LCP work
02 remove edge exports
  └─ 06 enable Cache Components  [BLOCKED — human]
       └─ 08 partial prefetching  [WITHHELD — not on this version]
```

Show only edges that bind in this repo.

## Fix waves

How the auto-apply tasks are clustered for dispatch — one row per wave, one agent per
cluster, disjoint file scopes.

| Wave | Agent | Tasks | Files owned | Gate to next wave |
|---|---|---|---|---|
| 1 | #1 | 01, 04 | `<globs>` | all wave-1 tasks `done` |

## Blocked on a human

One entry per `migration-required` task: what it is, the named exit cost, and where the
pre-flight checklist lives. These are prepared, not failed.

## Withheld — not available on this install

Carried from `01-applicability.md`'s withhold list, so a reader can see what was
*deliberately* not recommended and when to revisit.

| Feature | Why withheld | Revisit when |
|---|---|---|

## Not proposed — already correct

What the repo already does right (from recon). Prevents a future run from re-litigating it.

## Status (updated at Phase 6)

| Status | Count | Tasks |
|---|---|---|
| done | | |
| blocked | | |
| blocked-needs-human | | |
| pending | | |
| wontfix | | |

Regenerate with `scripts/status-report.py nextjs-enhancement/`.
```

## Rules

1. **Every task in `tasks/` appears in the table.** The index is the map; a missing row
   means a task nobody will find.
2. **Ordinals match filenames.** Row `03` links `03-<slug>.md`.
3. **Withheld and already-correct sections are mandatory**, even when empty — their absence
   reads as "nothing was considered", which is the opposite of the truth.
4. **The dependency graph shows only real edges.** Do not copy the generic graph from the
   priority matrix; prune to what binds here.
5. **Wave table is written before dispatch** and left in place afterwards as the record of
   what ran.
6. **No prose recommendations outside the tables.** The tasks are the plan; this file is
   navigation and accounting.
