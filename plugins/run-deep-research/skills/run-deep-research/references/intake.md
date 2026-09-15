# Intake — The Mandatory Research Intake Batch

The first action of every run, before any decomposition, template authoring, or
subagent dispatch. One batched `AskUserQuestion` call locks the run's shape so no
research budget is spent on the wrong scope, scale, or framing. This is the front
door to Phase 0 — the charter is written directly from its answers.

## The Rule

- **One call, batched.** Ask all discrete decisions in a single `AskUserQuestion`
  invocation (up to 4 questions). The user answers once. Never drip-feed questions
  turn by turn.
- **Recommended default first.** Make the recommended option the first choice of each
  question and append `(Recommended)` to its label.
- **Pre-fill from the request.** If the user already stated a value (e.g. named 8 specific
  tools, requested a market analysis, or specified an output folder), do not re-ask that
  dimension — carry it into the charter and only ask what is still open. If every dimension
  is already pinned, skip the call and state the locked configuration in the charter.
- **Never dispatch a wave before intake completes.** Dispatching Wave 1 before intake
  is a hard-rule violation (SKILL.md Hard Rule 1).

## The Four Intake Questions

Ask these four dimensions (drop any already settled by the user's prompt). Phrase headers ≤12 chars.

### 1. Scale — header `Scale`
Corpus size; bounds entity count, wave concurrency, and file budget.

| Option | Entities | Files |
|---|---|---|
| **standard (Recommended)** | 10-40 entities | ~150-500 markdown files |
| **compact** | 5-10 entities | ~80-200 markdown files |
| **deep** | 40-100 entities | ~500-2000 markdown files |
| **tiered** | 100+ entities | Full evidence packs for top tier only |

Pick `standard` as the default unless the request implies otherwise (a short list of 5 → compact; "all players in the space" → deep/tiered).

### 2. Framing — header `Framing`
Vocabulary and reference set. Resolved here, never switched mid-run.

| Option | When it fits |
|---|---|
| **Industry / vendor (Recommended for market work)** | "market analysis", "competitive landscape", "category map", vendor evaluation. Maximalist templates + profile pages by default. |
| **Domain-agnostic corpus** | Generic "compare N items for a decision" — OSS projects, models, hardware, papers, candidates, regulations, architectures. |

Lead with whichever the request signals; if ambiguous (e.g., "research 8 LLM frameworks"), this question settles it.

### 3. Scope & Discovery — header `Scope`
Entity discovery strategy + output location + profile page preference.

- **Entity Source:** "discover them for me" (Wave 1A discovery agent) vs "use my named list."
- **Output Location:** confirm `<topic-slug>/` directory at the workspace root.
- **Profile Pages:** yes (decision profile pages at `<entity-slug>.md`) / no (evidence packs only).

### 4. Wave Concurrency — header `Concurrency`
Batch sizing for parallel subagent dispatch.

| Option | Concurrency |
|---|---|
| **Standard (6-8 parallel subagents) (Recommended)** | Balanced rate-limit safety and high throughput. |
| **Conservative (3-4 parallel subagents)** | Safer for resource-constrained environments or strict rate limits. |
| **High throughput (10-15 parallel subagents)** | Faster fan-out for large tiered corpora in capable multi-agent harnesses. |

## Mapping Answers → Charter

Write the answers straight into `_meta/01-charter.md`:

```markdown
# Research Charter

Decider:          <who is deciding + their specific use case>   (from conversation / prompt)
Scale:            <compact | standard | deep | tiered>
Framing:          <domain-agnostic | industry>
Output root:      <topic-slug>/
Profile pages:    <yes | no>
Wave concurrency: <standard (6-8) | conservative (3-4) | high (10-15)>
Quote discipline: Verbatim quotes required for all numeric, priced, or versioned claims
```

The **decider** and **use case** are the load-bearing pillars of the charter. Without
them, "good" and "bad" are undefined and the corpus has no evaluation closing condition.

## Headless / Non-Interactive Fallback

When `AskUserQuestion` is unavailable (cron, subagent, non-interactive CI run):

1. Apply the recommended defaults: standard scale · framing inferred from request (industry if market/vendor keywords, else domain-agnostic) · discover entities · `<topic-slug>/` at workspace root · profile pages per framing default · standard wave concurrency (6-8).
2. Record every assumed value in the charter under a `## Assumed (no interactive intake)` heading so the user can review and override on re-entry.
3. Proceed to Phase 0. The run stays fully resumable — subsequent interactive turns can refine the charter and re-dispatch targeted waves.

## Anti-Patterns

| Anti-pattern | Fix |
|---|---|
| Skipping intake "because the request is clear" | If clear, pre-fill settled dimensions and confirm only what is open |
| Asking one question per turn | Batch all open decisions into one `AskUserQuestion` call |
| Re-asking a dimension the user already stated | Carry it into the charter; ask only open choices |
| Starting Wave 1 before answers land | Hard-rule violation — intake gates the first wave |
| Ambiguous decider profile | Always anchor the specific decider role and time horizon |
