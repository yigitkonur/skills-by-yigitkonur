# Reference index

Cross-reference of every reference file in this skill. The spine routes to references by purpose; this index routes by topic.

> **Reading the mode references:** each `modes/*.md` file is the recipe for one mode. Where the runtime currently implements only part of a recipe, the doc marks the gap with **Planned — not yet wired** plus the working manual workaround for today. Trust the Planned markers — aspirational behavior is preserved for the next implementation pass, but the runtime will not produce it.

## By topic

| Topic | File | Modes that read it |
|---|---|---|
| codex CLI flags policy | `universal/codex-flags.md` | every mode |
| codex-companion vendored dispatcher | `universal/codex-companion.md` | rescue (correlates jobs); review (reads to know what NOT to use) |
| Manifest schema + atomic writes | `universal/manifest-contract.md` | every mode |
| Monitor tool integration | `universal/monitor-contract.md` | every mode |
| Worktree naming, lifecycle, cleanup | `universal/worktree-contract.md` | exec, single, review, rescue |
| Failure mode taxonomy | `universal/failure-modes.md` | every mode |
| Dispatcher error-code catalog | `universal/errors.md` | every mode (envelope triage) |
| Concurrency cap policy | `universal/concurrency.md` | exec, batch, review, rescue |
| JSONL event types | `universal/json-streaming.md` | exec, batch, single, review |
| Idempotency / skip-existing | `universal/idempotency.md` | every mode |
| Output-size quality signals | `universal/output-size-signals.md` | batch (primary); audit-fleet-state surfaces in others |
| Prompt-discipline (Intent/Constraints/Success/...) | `universal/prompt-discipline.md` | exec, batch, single (review uses templates/review.tmpl.md directly) |
| State dir resolution | `universal/plugin-data.md` | every mode (preflight) |
| Anti-patterns | `universal/anti-patterns.md` | every mode |
| Upstream codex-plugin-cc bumps | `universal/upstream-codex-cc.md` | maintenance (not runtime) |

## By mode

### exec

Read in this order:
1. `modes/exec.md` — recipe.
2. `universal/worktree-contract.md` — naming, setup, cleanup.
3. `universal/monitor-contract.md` — fleet ticker contract.
4. `universal/json-streaming.md` — JSONL events to capture (`thread.started`, `turn.completed`).
5. `universal/concurrency.md` — `JOBS=N` policy.
6. `universal/manifest-contract.md` — entry schema for exec mode_state.
7. `templates/exec.tmpl.md` — per-task prompt skeleton.
8. `universal/failure-modes.md` — recovery on rate-limit / hung / dirty-worktree.
9. `universal/anti-patterns.md` — auto-merge / unbounded concurrency.

### batch

1. `modes/batch.md` — recipe.
2. `universal/idempotency.md` — skip-existing guard, archive-before-retry.
3. `universal/output-size-signals.md` — bottom-decile rule, MIN_BYTES.
4. `universal/monitor-contract.md` — runner-log tailer.
5. `universal/concurrency.md` — `JOBS=10` default + measure-before-raise.
6. `universal/manifest-contract.md`.
7. `templates/batch.tmpl.md` — template + placeholder.
8. `universal/json-streaming.md` — MCP-active dropout fallback (`-o` paired with `--json`).
9. `universal/failure-modes.md`.

### single

1. `modes/single.md` — recipe.
2. `universal/json-streaming.md` — filter pipeline.
3. `universal/monitor-contract.md` — single-task tail.
4. `universal/worktree-contract.md` — reuse-vs-fresh decision.
5. `universal/manifest-contract.md`.
6. `templates/single.tmpl.md`.
7. `universal/failure-modes.md`.

### review

1. `modes/review.md` — recipe + terminal states.
2. `universal/manifest-contract.md` — review mode_state.rounds[].
3. `universal/worktree-contract.md`.
4. `universal/monitor-contract.md` — `--review` per-tick line.
5. `templates/review.tmpl.md` — round-focus prompt.
6. `universal/json-streaming.md` — codex exec review JSONL.
7. `universal/failure-modes.md` — blocked/cap/failed recovery.

### rescue

1. `modes/rescue.md` — classification → explicit `--redo` → re-spawn.
2. `universal/manifest-contract.md` — entry schema, history rows.
3. `universal/codex-companion.md` — colocated state/job-record correlation.
4. Then the original mode's reference (whatever `manifest.mode` says).
5. `universal/failure-modes.md` — edge cases for in-flight, stale, unknown.

## By role

### "I'm authoring a per-task prompt"

- `universal/prompt-discipline.md` — the six sections.
- `templates/<mode>.tmpl.md` — per-mode skeleton.

### "I'm investigating why a run failed"

- `universal/failure-modes.md` — taxonomy.
- `universal/anti-patterns.md` — common mistakes.
- `modes/<mode>.md` §recovery — per-mode forensics.

### "I'm bumping the codex-plugin-cc version"

- `universal/upstream-codex-cc.md` — update procedure.

### "I'm writing a sister skill that needs to coexist"

- `universal/plugin-data.md` — state directory layout.
- `universal/manifest-contract.md` — schema, atomic writes.
- `universal/codex-companion.md` — what NOT to step on.

## File sizes

Reference files are short by design — typically 200–400 lines. Anything longer should be split into sub-references.

| Topic group | File count | Approx lines each |
|---|---|---|
| modes/ | 5 | 150–300 |
| universal/ | 13 | 100–300 |
| templates/ | 4 | 30–80 |
| index | 1 | 100 |
