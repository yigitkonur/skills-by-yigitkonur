# Codex Prompt Skeleton

Every codex job in this skill receives a rendered prompt file at
`<workdir>/prompts/<wave>/<slug>.md`. The prompt follows a fixed
seven-section skeleton — derived from this skill's mission-brief shape
and adapted for codex's prompt-following behavior.

## The seven sections

Every codex job's prompt has these sections, in this order. Skipping a
section means codex either wanders or under-delivers — the sections are
load-bearing.

```
1. CONTEXT — what is this corpus, why this job exists, where this job fits in the wave
2. INPUT PATHS — every file codex may read; nothing more
3. OUTPUT PATH — exactly one file codex writes; its path
4. RESEARCH METHODOLOGY — the run-research integration block (web research, citation rules, multi-round discipline)
5. DEFINITION OF DONE — binary criteria; one section may have many criteria
6. FAILURE PROTOCOL — what to do when stuck or when a source is unavailable
7. HANDBACK FORMAT — what the output file must contain (frontmatter, structure)
```

Sections are written as markdown headings inside the prompt file so
codex's prompt-parsing finds them. Do not collapse sections; do not
reorder; do not embed multiple jobs in one prompt.

## Section 1 — CONTEXT

Three short paragraphs:

1. **What this corpus is.** One sentence: the population of entities,
   the decider, the use case. Lift from `_meta/01-charter.md`.
2. **Why this job exists.** One sentence: which wave, which slug, what
   the output file feeds into downstream.
3. **What this job is NOT.** One or two sentences: scope boundaries
   that prevent codex from drifting into adjacent jobs' territory.

Example:

```markdown
# Context

This corpus researches the cloud browser category for a buyer choosing
a vendor for a 30-engineer scraping team with a 2026 budget of $X.

You are Wave 2's per-entity research job for `browserbase`. Your output
becomes the input to Wave 3's `_cross/pricing/` and `_cross/security/`
comparison jobs. Other Wave 2 jobs are researching the other 13 `core`
entities in parallel; you will not see their outputs.

Your scope is `browserbase` alone. Do not research adjacent vendors,
do not produce comparison content — that is Wave 3's job.
```

## Section 2 — INPUT PATHS

A bulleted list of every file codex may read. The orchestrator picks
these explicitly; codex must not read other files in the corpus.

```markdown
# Input paths

Read these files. Do not read anything else from the corpus directory.

- `_meta/01-charter.md` — the decider, scale, archetype, axis catalog
- `_meta/02-entities.md` — the entity tier list and 1-line rationale per row (your row: `browserbase`)
- `_meta/_PRODUCT_TEMPLATE.md` — the comprehensiveness contract you must satisfy
- `_meta/methodology-and-source-policy.md` — source hierarchy, citation rules
```

Why this matters: codex's web research is bounded by the corpus's
existing context. Letting codex read everything means it ingests
context it doesn't need (cost) and may inadvertently echo other
entities' content (defeats the disjoint-write principle).

## Section 3 — OUTPUT PATH

The single file codex must write. One job, one output path. Specify
exactly:

```markdown
# Output path

Write your final answer to:

`<corpus-root>/browserbase/00-overview.md`

Do not write any other file. If the template forces a multi-file pack
for this entity, this prompt is misshaped — surface the issue in
HANDBACK FORMAT and exit; the orchestrator will redispatch the wave
with one job per template section.
```

The "one job, one file" contract is what makes skip-existing
deterministic. A job that writes 5 files is not idempotent — re-running
it can leave inconsistent state.

For per-entity packs that need many files, the orchestrator dispatches
**one job per template section per entity** instead of "one job per
entity that writes the whole pack". This is more codex jobs but every
job is independently retryable. The trade-off is recorded per-run in
`run.json`.

## Section 4 — RESEARCH METHODOLOGY (the run-research integration block)

Codex jobs in this skill inherit the run-research skill's discipline.
The block is verbatim except for the freshness-window adaptation per
wave:

```markdown
# Research methodology

Use the run-research discipline for every web/Reddit call.

1. First call: invoke `start-research` (if available) or its fallback
   with a goal paragraph naming — topic, your specific use case
   (research <X> for the corpus's decider), known unknowns to skip,
   what NOT to research, freshness window (default: weight last 90
   days), quote discipline (every numeric/versioned/priced claim cites
   a verbatim quote).

2. Toolkit: 5 tools in a 2×2 (raw/smart × search/scrape) plus the
   planner.
   - raw-web-search: URL pool plus audit
   - smart-web-search: tiered triage with ## Synthesis / ## Gaps /
     ## Suggested follow-up searches
   - raw-scrape-links: full markdown including Reddit threading
     (≤5 per call)
   - smart-scrape-links: per-URL extraction with ## Matches /
     ## Not found / ## Follow-up signals (≤5 URLs, ≤7 facets per call)

3. Parallel dispatch: fire two raw-web-search calls in one turn when
   scopes differ (web + reddit). The reconnaissance round runs in
   roughly the time of one call.

4. Multi-round: 2-4 search rounds is normal. Harvest follow-up signals
   and not-found sections to seed round 2.

5. Citation discipline: snippets are NOT evidence. Only scraped page
   content is citable. Every numeric / versioned / priced claim cites
   a verbatim quote with URL and scrape date.

6. ## Not found is mandatory reading: it tells you which gaps to
   chase next round.

If run-research tools are unavailable in this codex session, fall back
to WebSearch / WebFetch / curl; never skip the citation rules.
```

Adapt the freshness-window per wave:

- Wave 1 discovery: "last 12 months for entity recency; last 36 months for category coverage"
- Wave 2 per-entity: "last 90 days for active development; last 12 months for stability"
- Wave 3 cross-axis: LOCAL-ONLY (no web research); use ledger-driven synthesis from existing pack files

For Wave 3 (LOCAL-ONLY), replace Section 4 with:

```markdown
# Research methodology

This is a LOCAL-ONLY synthesis job. Do not call any web tool. Read the
input-path files; reconcile claims across them; write the comparison.
If a claim is contradicted across files, surface the contradiction in
the comparison file (do not silently pick a side).
```

## Section 5 — DEFINITION OF DONE

Binary, specific, verifiable criteria. The closing sentence is:

> 100% completion required — partial = failure. Do not return until every criterion is met. If a criterion is impossible, report that finding in HANDBACK; do not silently skip.

Per-entity-pack example:

```markdown
# Definition of done

- File `<corpus-root>/browserbase/00-overview.md` exists with
  frontmatter and structured sections
- Every section in `_meta/_PRODUCT_TEMPLATE.md` is addressed (content
  OR explicit "insufficient evidence" entry naming the data gap)
- Every numeric/versioned/priced claim cites a verbatim quote with URL
  and scrape date
- Reddit/practitioner evidence includes username, subreddit, date,
  bias label
- No stub files; no placeholder TBD/TODO content
- `09-sources.md` is populated with a source map and a claims ledger
  using the schemas from `_meta/methodology-and-source-policy.md`

100% completion required — partial = failure.
```

## Section 6 — FAILURE PROTOCOL

What codex does when stuck:

```markdown
# Failure protocol

If blocked:
1. Report what was attempted (every sub-question and tool call).
2. Report what was discovered (partial findings).
3. Report why it failed (specific blocker — provider down, paywall,
   no relevant sources).
4. Report what would be tried next with more time / different tools.

Never silently skip a template section. If a template section cannot
be researched from public sources, write a one-paragraph "insufficient
evidence" entry naming the specific data gap. That entry is itself the
finding for that section.

Never fabricate a citation. If you cannot scrape the source, mark the
claim as `unverified` in the claims ledger.
```

## Section 7 — HANDBACK FORMAT

What the output file's content must look like. The handback section is
shorter than the prompt's other sections because the output is a file
codex writes, not a chat response.

```markdown
# Handback format

The output file at `<output-path>` must contain:

- A short heading (`# Browserbase — Overview`)
- A 2-3 sentence positioning summary
- Section bodies addressing every required template subsection
- Inline citations as `[1]`, `[2]`, ... with a `## Sources` block at
  the bottom listing each cited URL with scrape date

If you produce additional summary / process notes, write them as a
final `## Observations` section in the output file. Do not write them
elsewhere.
```

## Length budget

Target 200-400 lines per prompt. Shorter prompts under-specify; longer
prompts have low signal-to-noise. The seven sections naturally bound
the size when each section's discipline is followed.

If a prompt is approaching 600 lines, the job is too big — split it
into multiple per-section jobs.

## Examples of full prompts

Render real prompts at dispatch time; do not commit static examples to
this skill. The dispatch logic in `wave-dispatch.md` shows how to
substitute the per-job variables (entity slug, axis slug, template
section, input paths) into the skeleton.

For the wave-by-wave content shape of each kind of prompt (discovery,
axes, entity pack, cross-axis, profile page, promoted research, source
distillation), the anchor is this skill's own
`references/subagent-briefs.md` (for domain-agnostic briefs) and
`references/industry/mission-briefs.md` (for industry framing). Lift the
section bodies from those Claude subagent briefs — codex jobs accept the
same prompt shapes.
