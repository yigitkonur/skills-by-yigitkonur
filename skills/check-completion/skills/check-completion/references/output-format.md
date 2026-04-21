# Output Format — Audit Table and Completion Report

The two headline deliverables of this skill. Format rules, column definitions, and templates. The audit table is produced at the end of Phase 1; the completion report is produced at the end of Phase 2. They share structure — the report is the audit with every row advanced to a terminal status.

## Phase 1 — Audit table

### Full template

```markdown
## Audit

Scope: <one-line scope declaration — which scope and why it was chosen>

Sources scanned:
- Messages: <N candidate tasks extracted>
- Tool trace: <N Edit/Write/Bash calls relevant>
- TodoList: <state summary, or "no TodoList in session">
- Git: <N commits since base, N uncommitted changes>
- Tests / CI: <last run result and scope, or "no test run this session">
- Bash history: <N filesystem ops extracted>

| # | Task | Status | Evidence | Blocking? | Action Required |
|---|------|--------|----------|-----------|-----------------|
| 1 | <task> | `Implemented` | <evidence citation> | No | — |
| 2 | <task> | `Implemented but Broken` | <evidence> | No | <concrete action> |
| 3 | <task> | `Blocked` | <what's blocking> | **Yes** | <next step> |
| … | … | … | … | … | … |

Totals: <X Implemented, Y non-terminal, Z terminal-non-Implemented>
```

### Column rules

#### `#`
Integer, starting from 1, in reading order. Does not reshuffle based on priority — that's Phase 2's job. Priority ordering of remediation does not change the audit-table numbering.

#### `Task`
One short line describing the task. Use the wording the user or the plan used, when possible — don't rewrite. Verb-first if the original didn't have one ("Add OAuth callback" not "OAuth callback").

Task cells should be independent — a reader of one row should understand the task without cross-referencing other rows. If tasks are tightly coupled, merge them into one row OR use explicit cross-references (`row #5 depends on row #3`).

#### `Status`
Exactly one of the 22 statuses from `status-taxonomy.md`. Wrap in backticks. No qualifiers, hedges, or made-up statuses.

❌ `Mostly Implemented` (not a real status)
❌ `Implemented? (maybe)` (hedging)
❌ `Implemented + Untested` (two statuses in one cell)
✅ `` `Implemented but Untested` ``

If you genuinely can't pick one, the task needs to be split or re-described before classification.

#### `Evidence`
One line (two max) citing specific, concrete evidence per `evidence-patterns.md`. Use the citation style:

```
test output: pnpm test — 47 passed
commit abc1234 + tool call (Edit): src/auth.ts at message 8
message 14: user asked; no subsequent work
file state: src/session.ts exists but has no tests
```

Evidence must match the status. An `Implemented` row with evidence "wrote the code" is misclassified — downgrade to `Implemented but Untested`.

#### `Blocking?`
`**Yes**` (bold) if this row blocks other rows from progressing. `No` otherwise. Blocking rows rise to the top of Phase 2's priority order.

A row is Blocking if:

- It's status `Blocked` and another task in the list depends on it
- It's `Incorrectly Implemented` and incorrect behavior propagates to other tasks
- It's `Crashed` on a foundation others build on

Don't over-mark Blocking — a strict blocker is one that genuinely prevents other rows from reaching `Implemented`.

#### `Action Required`
Concrete, executable sentence per non-`Implemented` row. Every non-`Implemented` row has one. `Implemented` rows use `—`.

Good:
- `Fix null handling at src/session.ts:L42; re-run pnpm test`
- `Implement retry logic per spec at worker.ts:L50; verify with pnpm test:integration`
- `Run pnpm test to verify the code written at src/auth.ts:L30-L67`

Bad:
- `Look into it` (vague)
- `Revisit later` (non-actionable)
- `Fix the bug` (which bug?)

### Intro paragraph rules

Before the table:

- **One-line scope declaration** — tell the reader what's audited
- **Source-scan summary** — six bullets (or fewer if sources unavailable; state which)
- NO editorial preamble, narrative framing, or meta-commentary

After the table:

- **Totals line** — X Implemented / Y non-terminal / Z terminal-non-Implemented

NO "this is a great audit!" or "I'll start fixing things now." The next action is Phase 2, which emits its own artifacts.

## Phase 2 — Completion Report

### Full template

```markdown
## Completion Report

Started: <N tasks audited, M needing remediation>
Finished: <X now Implemented, Y terminal-non-Implemented (documented), Z unchanged>

Remediation time: <optional — useful for the user to calibrate future audits>

| # | Task | Started | Ended | Evidence |
|---|------|---------|-------|----------|
| 1 | <task> | `Implemented` | `Implemented` | (unchanged) |
| 2 | <task> | `Implemented but Broken` | `Implemented` | <fresh evidence after fix> |
| 3 | <task> | `Blocked` | `Blocked — unresolvable` | <blocker doc per blocker-handling.md> |
| 7 | <emergent task added during Phase 2> | `Not Planned` | `Implemented` | <evidence> |
| … | … | … | … | … |

### Blockers remaining

<Bulleted list of rows ending in `Blocked — unresolvable`, each with dependency + next step + owner>

### Deferred

<Bulleted list of rows ending in `Deferred to Human` / `Deprioritized` / `Cancelled` / `Out of Scope`, with rationale>
```

### Column rules

#### `#`
Same as the audit table. Emergent tasks added during Phase 2 use the next unused number. Reading order is preserved.

#### `Task`
Same as the audit table.

#### `Started`
The status from the Phase 1 audit table. Helps the reader see the starting state.

#### `Ended`
The terminal status reached by the end of Phase 2. One of:
- `Implemented`
- `Blocked — unresolvable` (per `blocker-handling.md`)
- `Deferred to Human`
- `Deprioritized`
- `Cancelled`
- `Out of Scope`

Non-terminal statuses in the Ended column indicate an incomplete audit — re-read `remediation-workflow.md` and finish.

#### `Evidence`
Per `evidence-patterns.md`. For upgraded rows (e.g., `Implemented but Broken` → `Implemented`), the evidence MUST be fresh (post-fix verification) — not a citation from Phase 1.

### Sections after the table

- **Blockers remaining** — every `Blocked — unresolvable` with full documentation. Do not bury this.
- **Deferred** — everything terminal-non-Implemented, with rationale. Shows the user what's explicitly out of scope.

## Evidence citation style (both phases)

Consistent with `evidence-patterns.md`:

```
<source>: <specific quote or output>
```

Examples:

| Citation | Meaning |
|---|---|
| `test output: pnpm test — 47 passed, 0 failed` | Test run output |
| `build output: cargo build — exit 0` | Build success |
| `file state: src/session.ts:L42 has null guard` | File inspection |
| `commit abc1234: "fix(session): add null guard"` | Commit reference |
| `message 14: user said "skip the export"` | Conversation citation |
| `tool call (Edit): src/auth.ts at message 8` | Tool trace |
| `observed behavior: curl /api/foo → 200 {ok: true}` | Manual verification |
| `bash: rm -rf stale/ at message 22` | Filesystem op |

Inline in the row. One per row minimum; more if the status requires multi-part evidence (e.g., `Implemented but Broken` cites both the prior-pass and the current-fail).

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| Status cells with qualifiers like "Implemented-ish" | Pick a real status; add context to Evidence if needed |
| Multiple statuses in one cell | Split the row or pick the more-pessimistic one |
| Evidence column says "checked" or "looks good" | Cite the specific thing you checked |
| Action Required is "fix it" or "address" | Rewrite with the concrete step — what command, which file |
| Blocking column has `Yes` for every non-`Implemented` row | Only mark Blocking when another row genuinely depends on this one |
| Completion report has `Partially Implemented` in the Ended column | Not terminal — go back to Phase 2 and finish the row |
| Completion report buries blockers at the bottom with no "Blockers remaining" section | Promote them — they are the user's immediate action items |
| Report uses "Thanks for the patience!" or similar filler | Delete it. Actions speak. |

## Length budget

Audit tables scale with task count. Typical ranges:

| Tasks | Table size | Intro | Total length |
|---|---|---|---|
| 5-10 | ~20 lines | ~8 lines | ~30 lines |
| 10-25 | ~35 lines | ~8 lines | ~45 lines |
| 25-50 | ~70 lines | ~10 lines | ~85 lines |
| 50+ | ~100+ lines | ~12 lines | ~115+ lines |

If an audit crosses 100 tasks, the scope may be too broad — see `scope-disambiguation.md` for splitting strategies.
