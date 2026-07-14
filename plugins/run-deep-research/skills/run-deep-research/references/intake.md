# Intake — the mandatory AskUserQuestion batch

The first action of every run, before any decomposition, template authoring, or
dispatch. One batched `AskUserQuestion` call locks the run's shape so no fan-out
budget is spent on the wrong executor, scale, or framing. This is the front door to
Phase 0 — the charter is written from its answers.

## The rule

- **One call, batched.** Ask all discrete decisions in a single `AskUserQuestion`
  invocation (up to 4 questions). The user answers once. Never drip-feed one question
  per turn.
- **Recommended default first.** Make the recommended option the first choice of each
  question and append `(Recommended)` to its label. The user can one-click the whole
  batch.
- **Pre-fill from the request.** If the user already stated a value (named 12 vendors,
  said "use codex", asked for a deep dive), do not re-ask that dimension — carry it
  into the charter and only ask what is still open. If every dimension is already
  pinned, skip the call and state the locked configuration in the charter.
- **Never start a wave before answers land.** Dispatching Wave 1 before intake is a
  hard-rule violation (SKILL.md Hard Rule 1).

## The four questions

Ask these four (drop any already settled by the request). Phrase headers ≤12 chars.

### 1. Executor — header `Executor`
How the per-task web research runs.

| Option | When it fits |
|---|---|
| **Claude subagents (Recommended)** | Default. Fan-out ≤ ~10, interleaved multi-turn research, stylistic control, codex unavailable. |
| **codex exec** | Large fan-out (≥15 jobs/wave), cheap parallel credits, detached burning, explicit per-wave effort routing. Requires `codex --version` + auth. |
| **Decide by fan-out size** | Let the orchestrator pick after Wave 1 reveals the entity count: Claude if the largest wave is <15 jobs, codex if ≥15. |

This question is the codex offer required by the workspace `AGENTS.md` ("always offer
codex, then wait"). If `codex exec` is chosen, a per-wave effort plan is authored in
Phase 0 — see `references/codex/effort-routing.md`.

### 2. Scale — header `Scale`
Corpus size; bounds entity count and file budget.

| Option | Entities | Files |
|---|---|---|
| **standard (Recommended)** | 10-40 | ~150-500 |
| compact | 5-10 | ~80-200 |
| deep | 40-100 | ~500-2000 |
| tiered | 100+ | full packs for the top tier only |

Pick `standard` as the default unless the request implies otherwise (a short list →
compact; "everything in the category" → deep/tiered).

### 3. Framing — header `Framing`
Vocabulary + which reference set loads. Resolved here, never switched mid-run.

| Option | When it fits |
|---|---|
| **Industry / vendor (Recommended for market work)** | "market analysis", "competitive landscape", "category map", vendor evaluation. Maximalist templates + profile pages by default. |
| **Domain-agnostic corpus** | Generic "compare N things for a decision" — OSS projects, models, hardware, papers, candidates, regulations. |

Lead with whichever the request signals; if genuinely ambiguous ("research 8 LLM
providers"), this question settles it.

### 4. Scope — header `Scope`
Entity source + output location + profile pages. Use `multiSelect: true` when several
sub-choices apply, or fold into one question with the dominant open item.

- **Entities:** "discover them for me" vs "use my named list."
- **Output folder:** confirm `<topic-slug>/` at the workspace root (the workspace
  `AGENTS.md` convention — topic folders live at root, no parent container).
- **Profile pages:** yes (default for `core` tier at `standard`+ in industry framing)
  / no.

## Mapping answers → charter

Write the answers straight into `_meta/01-charter.md`:

```
Decider:        <who is deciding + their use case>   (from conversation / free-text)
Scale:          <compact | standard | deep | tiered>
Framing:        <domain-agnostic | industry>
Executor:       <claude-subagents | codex | decide-after-wave-1>
Output root:    <topic-slug>/
Profile pages:  <yes | no>
Effort plan:    <only if codex — per-wave low/medium/high; see effort-routing.md>
```

The **decider** and **use case** are open-ended — capture them from the conversation
or the question's free-text notes, not from a multiple-choice option. Without them,
"good" and "bad" are undefined and the corpus has no closing condition.

## Headless / non-interactive fallback

When `AskUserQuestion` is unavailable (cron, subagent, piped run):

1. Apply the recommended defaults: Claude subagents · standard · framing inferred from
   the request (industry if any market/vendor signal, else domain-agnostic) ·
   discover entities · `<topic-slug>/` at root · profile pages per framing default.
2. Record every assumed value in the charter under a `## Assumed (no interactive
   intake)` heading so the user can correct on re-entry.
3. Proceed to Phase 0. The run stays fully resumable — a later interactive turn can
   override the charter and re-dispatch only the affected waves.

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| Skipping intake "because the request is clear" | If clear, pre-fill and skip only the settled dimensions — still confirm executor (the codex offer) unless the user named it |
| Asking one question per turn | Batch all open decisions into one `AskUserQuestion` call |
| Re-asking a dimension the user already stated | Carry it into the charter; ask only what is open |
| Starting Wave 1 before answers land | Hard-rule violation — intake gates the first wave |
| Choosing codex without the preflight | `codex --version` + auth gate first (`references/codex/codex-exec-contract.md`) before any codex wave |
