# Subagent Briefs

Copy-paste-ready brief templates for every subagent role. Every
research-doing brief embeds the run-research integration block —
the orchestrator's specific requirement is that the run-research
skill's discipline be baked into every research subagent prompt.

Read this in **Wave 1, 2, 3, 4** when writing a brief.

## Brief structure (7 canonical sections)

Every brief follows this structure. Maximum 5,000 words per brief —
density is the goal, not length.

1. **Context Block** — rich prose explaining why this mission
   exists. The subagent starts with zero prior knowledge.
2. **Mission Objective** — the observable end state. One core
   objective, not three. Outcomes, not procedures.
3. **Research Methodology** — the run-research integration block
   (mandatory for research-doing briefs; absent for Wave 3
   synthesis briefs and profile-page briefs).
4. **Definition of Done** — Binary, Specific, Verifiable (BSV)
   criteria. Closes with "100% completion required — partial =
   failure. Do not return until every criterion is met."
5. **Verification** — concrete commands or files demonstrating
   each DoD criterion is met.
6. **Failure Protocol** — what to do when stuck (report what was
   tried, what was found, why it failed, what would be tried next).
7. **Handback Format** — Summary / Files / Evidence / Observations.

## The run-research integration block

This block appears verbatim (or with minimal adaptation) in every
research-doing brief — Wave 1A, Wave 1B, Wave 2, and promoted-entity
Wave 4. It is absent from Wave 3 synthesis briefs and profile-page
briefs (those are local-files only).

```text
[RESEARCH METHODOLOGY — REQUIRED]

You have the `run-research` skill available. Use it to drive every
web/Reddit research call in this mission. Its discipline is
non-negotiable for this brief.

1. **First call**: invoke `get-research-consultancy` with a goal paragraph
   that names — topic, your specific use case (research <X> for
   <decider> in this corpus), known unknowns to skip, what NOT to
   research, freshness window (default: weight last 90 days), quote
   discipline (every numeric/versioned/priced claim cites a verbatim
   quote).

2. **Toolkit shape**: 3 tools — the planner plus one search tool and
   one extraction tool. There is no raw/smart split; each tool has a
   single fixed contract.
   - `get-research-consultancy`: goal-tailored brief — primary
     branch, keyword seeds, iteration hints, gaps to watch, stop
     criteria. Call this first, once per mission.
   - `web-search`: `keywords` only (1-50), never calls an LLM. Returns
     a ranked, de-duplicated, CTR-aggregated URL pool — no synthesis,
     no tiering, no `## Gaps`/`## Synthesis` sections. Use it for
     every reconnaissance round, including Reddit discovery via
     explicit `site:reddit.com/r/.../comments` keyword probes fed
     into the same tool (there is no separate reddit scope param).
   - `scrape-link`: `urls` plus a REQUIRED `extract` string (pipe-
     separated facets). Always runs LLM extraction and returns
     `## Source` / `## Matches` / `## Not found` / `## Follow-up
     signals` (and sometimes `## Contradictions`). Reddit permalinks
     auto-route through the Reddit API (full threaded post +
     comments) before extraction — use a quote-preserving `extract`
     for sentiment/threading work. Hard caps: ~5 URLs and 5-7 facets
     per call (~13s per URL).

3. **Parallel dispatch**: fire two `web-search` calls in one
   turn when scopes differ (e.g. open web + a `site:reddit.com/
   r/.../comments` probe set). The reconnaissance round runs in
   roughly the time of one call. This is the canonical pattern, not
   an exotic move.

4. **Multi-round**: 2-4 search rounds is normal. Harvest
   `## Follow-up signals` (from `scrape-link`) to seed round 2 with
   refined `web-search` keyword probes. Single-call sessions are
   under-researched.

5. **Citation discipline**: snippets are NOT evidence. Only scraped
   page content (via `scrape-link`) is citable. Every numeric /
   versioned / priced claim cites a verbatim quote with URL and
   scrape date.

6. **`## Not found` is mandatory reading**: it tells you which
   gaps to chase next round. Never skip a `## Not found` section.

7. **Operational thresholds**: `scrape-link` ≤ 5 URLs and ≤ 7
   facets per call (going wider risks timing out). `web-search`
   fans out cleanly across 2-4 parallel calls per round; beyond
   that, plan for persistence and subagent-extract from the
   persisted file.

8. **For full discipline**, the run-research skill's references
   are at:
   - `tools.md` — tool API plus operational thresholds
   - `prompting.md` — goal/extract writing (highest-leverage
     section)
   - `workflows.md` — workflow templates per question type
   - `synthesis.md` — citation, contradiction, output formats
   - `failure-modes.md` — provider cascade, timeout, persistence

Read those references when in doubt. Their discipline is the
contract this brief inherits.

[/RESEARCH METHODOLOGY]
```

The block is dense; every line earns its place. Adaptations
allowed (e.g., adjusting freshness window for security work),
but structure preserved.

## Wave 1A — Discovery agent brief template

```text
[CONTEXT BLOCK]

You are a discovery researcher in a deep-corpus-research session.
The orchestrator is building a navigable evidence corpus to support
a decision: <decider profile + use case from charter>.

Phase 0 wrote `_meta/01-charter.md`. You are Wave 1A, dispatched in
parallel with Wave 1B (the scope-mapping agent). You will not see
1B's output; the orchestrator merges after both return.

Your job is to enumerate every entity that should be evaluated and
tier each. The corpus structure assigns one folder per `core`
entity, plus rows in a discovered list for the long tail.

Read these paths:
- `_meta/01-charter.md` (the charter)

Mental model after reading: you understand the decider, the use
case, the apparent scope. You are about to discover entities — not
research them deeply.

[MISSION OBJECTIVE]

Produce `_meta/02-entities.md`: a tiered table of every candidate
entity in this category, status-checked, with one-line rationale
per row.

Hard constraints:
- Decompose the topic into 3-5 orthogonal sub-questions surfacing
  different candidate clusters.
- Status-check each candidate (active / dead / waitlist /
  acquired) with last-update evidence.
- Tier each candidate (`core` / `secondary` / `discovered-only`).
- Cap candidate count at ~50; tier the long tail.

Priority signal: coverage > depth. Better 25 candidates with
one-line evidence each than 8 candidates researched in detail
(that is Wave 2's job).

You own this mission end-to-end. Explore freely; trust your
judgment; adapt your approach as you learn more. The destination
is fixed; the path is yours.

[RESEARCH METHODOLOGY]
<paste the run-research integration block verbatim>

Adapt: freshness window = "last 12 months for entity recency; last
36 months for category coverage". Quote discipline = "vendor URL
plus last-update date verbatim per row".

[DEFINITION OF DONE]

- File `_meta/02-entities.md` exists with a markdown table of
  candidates.
- Every row has columns: slug, name, vendor/maintainer, URL, tier
  (core/secondary/discovered-only), status (active/dead/waitlist/
  acquired), surfaced-by (sub-question id), one-line rationale.
- ≥3 sub-questions used; each surfaced ≥3 distinct candidates.
- ≥1 sub-question targeted a non-incumbent angle (open-source,
  geographic, recent).
- Every candidate has a status with a source URL.
- Long tail beyond ~50 candidates is tiered to `discovered-only`.
- File ends with a "Watch list" section noting candidates that
  may promote in future passes.

100% completion required — partial = failure. Do not return until
every criterion is met. If a criterion is impossible, report that
finding with evidence; do not silently skip.

[VERIFICATION]

- `wc -l _meta/02-entities.md` — substantive (≥30 lines).
- Count rows by tier (`core` / `secondary` / `discovered-only`).
- Spot-check 3 random rows: URL resolves; status is sourced.

[FAILURE PROTOCOL]

If blocked: report what was attempted (every sub-question and tool
call), what was discovered (partial entity list), why it failed
(specific blocker), what would be tried next.

Never silently skip a sub-question. If a sub-question returns
nothing, report that as a finding.

[HANDBACK]

1. Summary — one paragraph: what was done.
2. File path: `_meta/02-entities.md`.
3. Evidence: count of candidates per tier; example rows.
4. Observations: anomalies, surprises, candidates whose tier was
   uncertain.
```

## Wave 1B — Scope-mapping agent brief template

```text
[CONTEXT BLOCK]

You are a scope-mapping researcher in a deep-corpus-research session.
The orchestrator is building a navigable evidence corpus to support
a decision: <decider profile + use case from charter>.

You are Wave 1B, dispatched in parallel with Wave 1A (the discovery
agent). You will not see 1A's output; the orchestrator merges after
both return.

Your job is to derive the axis catalog — the dimensions the decider
will compare entities along. The catalog becomes the section
structure for every entity pack and the folder structure of
`_cross/`. Without a sharp axis catalog, every downstream agent
researches the wrong things.

Read these paths:
- `_meta/01-charter.md` (the charter)

Mental model after reading: you understand the decider's specific
constraints. You are about to research the *category itself* — not
specific entities — to identify the decider-weighted dimensions.

[MISSION OBJECTIVE]

Produce `_meta/03-axes.md`: the axis catalog with name, native
primitive, decision weight, and suggested folder slug per axis.

Hard constraints:
- Answer the 7 decomposition questions for this category:
  1. Who is the decider (verify and refine)
  2. What is an entity (name it explicitly)
  3. What axes does the decider compare on (NOT features — axes)
  4. What native primitive describes each axis
  5. What does lock-in / exit / mistake-recovery look like
  6. What practitioner channels exist for this domain
  7. What recent shifts has this domain seen (last 12 months)
- Identify ≥6 distinct axes; reject feature-list framing.
- For every axis: name + native primitive + decision weight +
  suggested folder slug.
- Surface practitioner channels (specific subreddits, HN angles,
  professional forums) in a dedicated section.

Priority signal: clarity of axes > breadth. A sharp 6-axis catalog
beats a 15-axis feature list.

You own this mission end-to-end.

[RESEARCH METHODOLOGY]
<paste the run-research integration block verbatim>

Adapt: freshness window = "weight last 12 months for category
shifts". Tool steering: `web-search` keyword probes for "decision
axes deciders compare on for <topic>; native primitives per axis;
not feature lists; not marketing"; `scrape-link` with a matching
`extract` on 2-3 authoritative analyses.

[DEFINITION OF DONE]

- File `_meta/03-axes.md` exists with structured sections.
- ≥6 axes named; each has a native primitive; each has a decision
  weight (decision-flipping / important / nice-to-know); each has
  a kebab-case folder slug.
- Practitioner-channels section names ≥3 specific channels.
- Recent-shifts section captures changes from the last 12 months
  with cited URLs.
- All 7 decomposition questions answered explicitly.
- File ends with a one-paragraph note on whether the category fits
  a known archetype or needs a custom shape.

100% completion required — partial = failure.

[VERIFICATION]

- `grep -c '^## ' _meta/03-axes.md` — ≥7 sections.
- Spot-check: every axis has all four fields.
- Practitioner channels are specific (named subreddit, not "Reddit").

[FAILURE PROTOCOL]

Standard. If the category is so novel that the 7-question protocol
doesn't yield clear axes, surface that finding — the orchestrator
may rescope.

[HANDBACK]

1. Summary  2. File path  3. Evidence (axis count, slugs)
4. Observations (axes that surprised; norms differing from
   archetype expectation).
```

## Wave 2 — Per-entity research brief template

```text
[CONTEXT BLOCK]

You are a per-entity researcher in a deep-corpus-research session.
The orchestrator has completed Phase 0 (charter), Wave 1 (discovery
plus scope), Phase 2 (templates), and Phase 3 (architecture).

The decision being supported: <decider profile + use case>.
The entity you are researching: <entity name + slug>.
The category: <category name from charter>.
The axis catalog (your pack's section structure): <list of axes
with native primitives — embed inline from _meta/03-axes.md>.
The freshness window: weight last 90 days unless the axis specifies
otherwise.

Read these paths (in order):
- `_meta/01-charter.md` — decider, use case, freshness, quote
  discipline.
- `_meta/03-axes.md` — the axis catalog.
- `_meta/04-product-template.md` — the per-entity template
  prescribing what evidence belongs in each section.

Do NOT read other entity folders. Do NOT read `_cross/`. Do NOT
read other Wave 2 agents' outputs.

Mental model after reading: you know the decider's question, the
axes you must address, the per-axis primitives to capture, and the
practitioner channels worth searching.

[MISSION OBJECTIVE]

Produce a complete evidence pack for <entity> at `<entity-slug>/`.
Every axis in the catalog is addressed — with content OR with a
one-paragraph "insufficient evidence" entry naming the data gap.

Hard constraints:
- Owned write scope: `<entity-slug>/` ONLY.
- MAX 15 files in this folder.
- File naming: `<NN>-<axis-slug>.md`. NN scheme: 00 = overview,
  01-08 = axis content, 09 = sources/ledger. Pick axis-slug per
  your evidence (don't copy slugs verbatim from the template —
  your evidence shapes the slug).
- Every numeric / versioned / priced claim cites a verbatim quote
  with URL and scrape date.
- Every axis from `_meta/03-axes.md` is addressed in this pack.

Priority signal: evidence-grounded depth on every axis the decider
weighs > breadth of marketing-page facts.

You own this mission end-to-end. Explore freely; trust your
judgment; adapt your approach as you learn more.

[RESEARCH METHODOLOGY]
<paste the run-research integration block verbatim>

Adapt the goal paragraph for `get-research-consultancy`:
- Topic: <entity name>.
- Use case: research <entity> on every axis in this catalog for
  <decider use case>; focus on <decision-flipping axes>; treat
  <nice-to-know axes> as stretch.
- Skip: marketing-page hype not anchored to a verifiable claim;
  feature-list rehashes; vendor-published competitor comparisons.
- Freshness: weight last 90 days for product/pricing changes;
  longer window acceptable for stable security/compliance facts.
- Quote discipline: every numeric / versioned / priced claim
  cites a verbatim scraped quote.

Tool steering: parallel `web-search` calls (open web + explicit
`site:reddit.com/r/.../comments` probes) for reconnaissance;
`scrape-link` with a facet-rich `extract` on docs/changelog/pricing
pages (≤5 URLs and 5-7 facets per call); `scrape-link` with a
quote-preserving `extract` on Reddit threads for sentiment (≤5
threads per call).

[DEFINITION OF DONE]

- Folder `<entity-slug>/` exists.
- File `00-overview.md` exists with: entity description, vendor /
  maintainer, headline framing, capture date.
- Every axis in `_meta/03-axes.md` is addressed:
  - Either with a content file `<NN>-<axis-slug>.md`, OR
  - With a one-paragraph "insufficient evidence" entry inside an
    existing file in the same folder, naming the data gap
    explicitly.
- File `09-sources.md` exists with the claims ledger (each claim:
  type, evidence URL, scrape date, confidence).
- ≤15 total files in `<entity-slug>/`.
- Every numeric / versioned / priced claim has a verbatim quote
  with URL and date.
- Zero placeholder strings (`TODO`, `TBD`, `fill later`).
- Zero claims sourced from search snippets — every URL was actually
  scraped.

100% completion required — partial = failure. Do not return until
every criterion is met. If a criterion is impossible, report with
evidence — do not silently skip.

[VERIFICATION]

- `find <entity-slug>/ -type f -name '*.md' | wc -l` — must be ≤15.
- `grep -rEn '\b(TODO|TBD|fill later)\b' <entity-slug>/` — must
  return 0.
- For each axis, confirm presence: either a file with the axis-slug,
  or an "insufficient evidence" entry in another file.

[FAILURE PROTOCOL]

If blocked on a specific axis: log the gap in `09-sources.md` as
an "insufficient evidence" entry naming the data gap. Don't skip
silently.

If blocked overall: report what was attempted, what was discovered
(partial pack), why it failed, what would be tried next.

Never loop on the same failing approach. If a search round produces
nothing on an axis after two attempts, log the gap and move on.

[HANDBACK]

1. Summary — one paragraph: what was done.
2. Files modified: list with one-line note each.
3. Evidence: file count; axis-coverage map (which axis is in which
   file or "insufficient evidence" entry); verification command
   outputs.
4. Observations: surprises, ground for tier promotion or demotion,
   axes where the entity was particularly strong or weak.
```

## Wave 3 — Per-axis cross synthesis brief template

(No run-research integration block — Wave 3 is local-files only.)

```text
[CONTEXT BLOCK]

You are a per-axis cross-entity synthesizer in a deep-corpus-research
session. Wave 2 has completed. Every `core` entity has an evidence
pack at `<entity-slug>/`. Your job is to compare entities along ONE
axis: <axis name from _meta/03-axes.md>.

Read these paths:
- `_meta/01-charter.md` — decider, use case.
- `_meta/03-axes.md` — the axis catalog (focus on YOUR axis).
- `_meta/05-axis-templates.md` (or the specific axis template) —
  comparison axes, matrix columns, ranking dimensions for YOUR
  axis.
- For every `core` entity in `_meta/02-entities.md`:
  - `<entity-slug>/<NN>-<your-axis-slug>.md` — their evidence on
    this axis.
  - `<entity-slug>/09-sources.md` — for citation resolution.

You do NOT use web tools. Your evidence is the per-entity files.
If they are insufficient, log the gap; do not search the web from
here.

Mental model after reading: you know the decider's question on this
axis, every entity's evidence on this axis, and the contradictions
across entities.

[MISSION OBJECTIVE]

Produce the cross-entity comparison for <axis name> at
`_cross/<axis-slug>/`. The minimum: a `00-overall-comparison.md`
plus granular comparison files per scenario.

Hard constraints:
- Owned write scope: `_cross/<axis-slug>/` ONLY.
- MAX 12 files in this folder.
- File naming: `<NN>-<topic-slug>.md`; pick topic-slug per evidence.
- `00-overall-comparison.md` includes: matrix (entity ×
  comparison-column), ranking, recommendation, evidence confidence
  per row, scenario-specific guidance, what unknown would change
  the answer.
- Every cell in the matrix has a value or an explicit "no evidence"
  marker; never silently empty.
- Every claim cites the source file (e.g.,
  `<entity-slug>/<NN>-<axis>.md`).
- Surface every contradiction — do not silently pick.

Priority signal: ranking with conditions > flat ranking. The
decider's answer almost always depends on a variable (scale, team
size, budget, regulatory regime); name those variables and rank
conditionally.

[DEFINITION OF DONE]

- Folder `_cross/<axis-slug>/` exists.
- `00-overall-comparison.md` exists with matrix, ranking, evidence
  confidence, contradictions section, scenario-specific guidance,
  source citations to per-entity files.
- ≤12 total files; granular files address scenarios named in the
  axis template.
- Every entity in `_meta/02-entities.md` (`core` tier) appears in
  the matrix.
- Every contradiction across entities is surfaced — silent picking
  is a failure.
- Every claim cites a per-entity file path.

100% completion required — partial = failure.

[VERIFICATION]

- `find _cross/<axis-slug>/ -type f -name '*.md' | wc -l` — ≤12.
- Spot-check matrix: every `core` entity has a row; every
  comparison column has a value or "no evidence" marker.
- Spot-check 3 claims: each cites a per-entity file path.

[FAILURE PROTOCOL]

If a per-entity file is missing for an axis where it should exist:
log it as a Wave 2 gap; do not search the web. Surface to the
orchestrator.

If the axis itself turns out to be miscategorized (evidence shows
it's not actually decision-flipping for this decider): surface
that finding; the orchestrator may rescope.

[HANDBACK]

1. Summary — one paragraph: ranking and recommendation.
2. Files modified: list.
3. Evidence: matrix size; contradictions count; ranking with
   conditions.
4. Observations: per-entity gaps that need a Wave 2 follow-up.
```

## Optional Wave 4 brief templates

### Profile-page brief (no run-research)

```text
[CONTEXT BLOCK]

You are a profile-page writer. The corpus has Wave 2 + Wave 3
complete. Your job: synthesize the evidence pack for ONE entity
into a decision-grade profile page at the corpus root.

Read scope:
- `_meta/01-charter.md` — decider, use case.
- `<entity-slug>/` — the full evidence pack.
- `_cross/<axis-slug>/00-overall-comparison.md` for every axis
  this entity ranks on (for cross-context callouts).

Write scope: `<entity-slug>.md` at corpus root. ONLY this file.

[MISSION OBJECTIVE]

Produce `<entity-slug>.md`: a 300-700 line profile synthesizing the
evidence pack with the 10-section ordering from synthesis.md:
1. Metadata
2. Executive summary (3-5 sentences)
3. Headline findings (5-9 bullets)
4. Best-fit / do-not-choose-if (with conditions)
5. Pack map (links into evidence pack)
6. Deep profile (synthesis with links into pack)
7. Numbers table (5-10 quantitative facts with caveats)
8. Open gaps
9. Sources
10. Capture date

[DEFINITION OF DONE]
- File `<entity-slug>.md` exists at corpus root.
- 300-700 lines.
- 10 sections in the order above.
- Every non-trivial claim links to an evidence-pack file.
- Best-fit and do-not-choose-if scenarios have explicit conditions.
- Numbers table cites each number to its pack file.

100% completion required — partial = failure.

[VERIFICATION]
- `wc -l <entity-slug>.md` — 300-700 range.
- `grep -c '^## ' <entity-slug>.md` — ≥10 sections.
- Spot-check 5 claims: each links to a pack file.

[FAILURE PROTOCOL] Standard.

[HANDBACK]
1. Summary  2. File path  3. Verification outputs  4. Observations
```

### Promoted-entity Wave 4 brief

Same shape as the Wave 2 per-entity brief, with the entity name
updated and a context note: "this entity was promoted from
`secondary` mid-session because <Wave 2/3 finding>". Includes the
run-research integration block.

## Common brief failure modes

| Failure | Symptom | Fix |
|---|---|---|
| Mission too broad | Subagent returns shallow output across many axes | Split into multiple briefs; each owns a narrow scope |
| Conflicting write scopes | Two agents try to write to same folder | Re-dispatch with explicit "you own only `<path>`" |
| Missing run-research integration block | Subagent re-derives discipline shallowly; cites snippets as evidence | Always include the block verbatim |
| Soft DoD ("comprehensive coverage") | No way to verify completion | Every DoD criterion is BSV |
| No verification requirement | Allows silent gap-skipping | Every DoD criterion has a corresponding verification command |
| Brief tells the agent which keywords to use | Agent under-explores; misses adjacencies | Tell the agent what evidence shape; let run-research's prompting guide pick keywords |
| Read scope too broad | Agent reads everything; context bloat | Name specific paths, not directories |
| Ceiling stated as floor | Agent pads to reach minimum | State as ceiling with release valve |
| No "100% completion required" closing | Agent returns partial work | Always close DoD with that language |

## Brief discipline checklist (orchestrator self-check)

Before dispatching any brief, verify:

- [ ] Context block has rich prose (not bullet skeleton).
- [ ] Mission objective is observable, single, outcome-not-procedure.
- [ ] Research methodology section includes the run-research
      integration block (for research-doing briefs).
- [ ] Every DoD criterion is Binary, Specific, Verifiable.
- [ ] DoD closes with "100% completion required — partial =
      failure. Do not return until every criterion is met."
- [ ] Verification commands resolve every DoD criterion.
- [ ] Failure protocol is present.
- [ ] Handback format is specified.
- [ ] Read scope and write scope are explicit (paths named).
- [ ] No keyword-prescription, no tool-prescription.
- [ ] Brief is under 5,000 words.
