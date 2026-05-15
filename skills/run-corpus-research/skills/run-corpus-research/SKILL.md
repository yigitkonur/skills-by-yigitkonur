---
name: run-corpus-research
description: Use skill if you are orchestrating multi-file evidence-corpus research over 5+ entities with per-entity packs, cross-axis comparisons, and source-traceable claims.
---

# Run Corpus Research

Orchestrate a multi-file evidence corpus over a population of entities.
Output is a navigable folder tree — per-entity evidence packs,
cross-entity comparison rollups, source ledgers, profile pages, master
summary — never a single report.

The orchestrator does not search the web. The orchestrator architects,
dispatches, gates, and synthesizes. Searching is the subagents' job,
and they search via the `run-research` skill (which the orchestrator
embeds into every research-doing subagent brief).

## When to use

Use this skill if any of these match:

- *"compare 5+ tools / vendors / frameworks / providers"* across multiple axes
- *"research the <category> / <market> / <ecosystem>"* and produce a navigable corpus, not a one-pager
- *"build a category map / competitive landscape / vendor evaluation"* with source-traceable claims
- *"evaluate N options for <decision>"* where N ≥ 5 and a one-page summary is insufficient
- *"deep research on <space>"* with per-entity files, cross-axis files, and a master summary
- *"audit / shortlist <population>"* against a fixed axis catalog (cost, performance, fit, risk, longevity)
- *"every numeric / versioned / priced claim must cite a verbatim source quote"*
- *"the deliverable is a folder tree the team can navigate"*, not a single document

Do NOT use when:

- The question is one technical question with one or two options — use `run-research` (single-question, web + Reddit, single markdown).
- The user wants a single polished one-page summary or battlecard — use `run-research`; downstream skills polish.
- The work is a codex-template fanout (same template, many inputs) — use `use-codex` batch mode (the retired `run-batch-codex-research` shim points there).
- The question is local-codebase only — use Explore-class agents, not corpus orchestration.
- N < 5 entities — corpus overhead exceeds the value.

## Boundary against `run-industry-research`

`run-industry-research` is a specialization of this orchestration pattern
focused on **markets / industries / vendor categories** with the same
multi-file output. Both skills produce per-entity packs + cross-axis
comparisons + source ledgers; the difference is framing, not mechanics.

- If the user's framing is *"industry / market / vendor category /
  competitive landscape"* → prefer `run-industry-research`. It already
  bakes in the market-research vocabulary, deeper Reddit/practitioner
  templates, and a stricter source-verification ledger.
- If the user's framing is *"compare / research / evaluate N entities"*
  in any other domain (open-source projects, models, hardware, papers,
  candidates, locations, regulations, frameworks) → use this skill.
  It is the domain-agnostic corpus orchestrator.

When in doubt, ask the user one clarifying question about framing
before dispatching Wave 1. Do not run both skills.

## The orchestrator's mental model

Every deep-research question reduces to one shape: **a population of
entities, evaluated across a set of axes, producing per-entity evidence
packs + per-axis cross-entity comparisons + a master decision artifact.**

Strip away domain. What remains in every session:

- **A finite set of entities.** Things the decider is choosing among,
  evaluating, hiring, buying, visiting, depending on. The
  orchestrator's first task is to enumerate them.
- **A finite set of evaluation axes.** Dimensions the decider weighs.
  Each has a native primitive (a unit of measurement). The
  orchestrator's second task is to enumerate them.
- **A decider with a use case.** Without this, "good" and "bad" cannot
  be defined.
- **A decision artifact.** Without this, the research has no closing
  condition.

The orchestrator's four jobs in order:

1. **Decompose.** What are the entities, what are the axes? Read
   `references/thinking.md`. Without rigorous decomposition, no amount
   of evidence saves the corpus.

2. **Structure.** Design the folder tree, file-naming scheme, MAX-N
   ceilings — before any subagent dispatches. Read
   `references/filesystem.md`.

3. **Dispatch.** Write briefs that bind subagents to their specific
   scope, the run-research skill's discipline, and the file paths they
   own. Read `references/subagent-briefs.md` for copy-paste templates.

4. **Synthesize.** Read every output file personally; resolve
   contradictions; write the master summary. Read
   `references/synthesis.md`.

## Phase model

| Phase | Goal | Artifact |
|---|---|---|
| 0 — Charter | Clarify decider, scale, archetype hypothesis | `_meta/01-charter.md` |
| Wave 1 — Discovery + Scope | Enumerate entities AND derive axis catalog (parallel, 2 subagents) | `_meta/02-entities.md`, `_meta/03-axes.md` |
| 2 — Templates | Write the comprehensiveness contract | `_meta/04-product-template.md`, `_meta/05-axis-templates.md` |
| 3 — Architecture | Plan tree shape, MAX-N caps, entity tiers | `_meta/06-file-budget.md` |
| Wave 2 — Per-entity research | Fill `<entity-slug>/` for every `core` entity (parallel, ≤8 per sub-wave) | `<entity-slug>/<NN>-<axis>.md` files |
| Wave 3 — Per-axis cross synthesis | Compare entities along each axis (parallel, ≤8 per sub-wave) | `_cross/<axis-slug>/<NN>-<topic>.md` files |
| Wave 4 (optional) | Profile pages OR promoted-entity research | `<entity-slug>.md` at root, OR additional packs |
| 7 — Verification + Master summary | Resolve contradictions, write master, run gates (orchestrator-personal) | `_meta/00-master-summary.md` + verification log |

Wave 1, Wave 2, Wave 3, optional Wave 4 dispatch parallel subagents.
Phase 0, 2, 3, 7 are orchestrator-personal (no subagents). Subagents in
Wave 1, Wave 2, and promoted-entity Wave 4 invoke the run-research
skill; Wave 3 and profile-page Wave 4 subagents are local-files only
(no web research).

## Tool steering at a glance

The orchestrator chooses the tool for each use case in the brief; the
subagent executes via its run-research session.

| Use case | Wave | Tool dispatch |
|---|---|---|
| Find entities | 1A | Parallel `raw-web-search` (web + reddit) → optional `raw-scrape-links` on category indexes |
| Map axes | 1B | `smart-web-search` with extract = "decision axes" → `smart-scrape-links` on 2-3 authoritative analyses |
| Per-entity overview | 2 | `start-research` per entity → parallel `smart-web-search` (web + reddit) → `smart-scrape-links` on docs + `raw-scrape-links` on Reddit |
| Per-entity sentiment | 2 | `raw-scrape-links` on Reddit thread permalinks (preserves voting + threading) |
| Cross-entity synthesis | 3 | LOCAL-ONLY: read files, no web tools |
| Profile pages | 4 / orch | LOCAL-ONLY: read pack, write profile |
| Master summary | 7 | LOCAL-ONLY: orchestrator reads everything, writes |

For tool API and operational thresholds (URL counts, facet counts,
parallel calls), the subagent's brief points to the `run-research`
skill's own tool reference inside its installed copy.

## Reference routing

Load only the reference whose phase is active. Loading all references
at once exhausts context.

| Reference | Read when |
|---|---|
| `references/thinking.md` | Phase 0, every session — the decomposition protocol; what counts as an entity vs axis vs primitive |
| `references/templates.md` | Phase 0, 2, 3 — concrete formats for charter, product template, axis templates, file budget; tier-promotion mechanics |
| `references/orchestration.md` | Wave 1, 2, 3 — wave choreography, parallel-dispatch rules, tool steering, between-wave gate procedure |
| `references/filesystem.md` | Phase 3 — directory contract, MAX-N caps, file naming, context-sharing through files |
| `references/subagent-briefs.md` | Wave 1, 2, 3, 4 — copy-paste-ready brief templates with the run-research integration block |
| `references/synthesis.md` | Phase 7 — claims ledger discipline, profile-page template, master-summary structure, personal-read gate procedure |
| `references/verification.md` | Phase 7 — completion-gate commands and template-coverage audit |
| `references/failure-modes.md` | Any wave — recovery procedures for subagent timeouts, shallow output, MAX-N overflow, contradictions |

## Hard rules

- **The orchestrator does not search.** Searching is the subagents'
  job, via the run-research skill.
- **The orchestrator does not delegate synthesis.** Read every entity
  pack and every cross file personally before the master summary.
- **MAX 8 subagents per wave.** Beyond 8, run sequential sub-waves.
- **Disjoint write scopes.** Each subagent owns exactly one folder.
- **Every research-doing brief invokes run-research.** Embed its
  discipline in the brief — see `references/subagent-briefs.md` for
  the required block.
- **Every numeric / versioned / priced claim cites a verbatim quote.**
  Snippet citations are forbidden.
- **MAX-N caps are ceilings, not targets.** 15 per entity / 12 per
  cross-axis / 8 per meta. Below ceiling is normal; sparse evidence is
  acceptable.
- **No silent gap-skipping.** A section with insufficient evidence
  becomes a one-paragraph "insufficient evidence" entry naming the
  data gap — never a stub file, never absent.
- **Phase 2 templates before Wave 2 dispatch.** Templates are the
  comprehensiveness contract. Skipping is a hard failure.

## Anti-patterns

| Anti-pattern | Why it fails | Fix |
|---|---|---|
| Templates skipped or written after entity research | No comprehensiveness boundary; depth varies by agent | Phase 2 first, Wave 2 second. Always. |
| Template is thin or generic (≤15 sections) | Misses decider-weighted axes; produces shallow corpus | Re-do the deep category pre-pass; re-author maximalist template (~30+ sections) |
| Template prescribes exact filenames | Removes evidence-driven naming; agents pad to fit | Templates list sections + questions; agents pick filenames |
| Stub files for sections with no evidence | Pollution; no actual content | "Insufficient evidence" entry inside an existing file with the data gap named |
| Identical empty subfolders for every entity | Copy-paste research, no value | Create only evidence-justified files; address every template section |
| Cross-axis file is concatenation of per-entity summaries | Doesn't compare; just appends | Comparison template prescribes axes, ranking, scenarios; agents follow |
| Reddit evidence presented as "consensus" | Bias and small samples are erased | Preserve thread, username, date, quote, bias label |
| Source verification skipped because "it's clearly true" | Stale facts, contradicted vendor claims | Source ledger non-optional for `core` entities |
| Profile page duplicates evidence-pack content | Duplication; no synthesis added | Profile = readable narrative + links into pack; pack = atomic evidence files |
| Single-output thinking ("write me a report") | Loses navigability and source-traceability | Multi-file corpus is the contract; route to run-research if user wants single report |
| Orchestrator searches the web | Defeats wave model; pollutes orchestrator context | Orchestrator architects, dispatches, gates, synthesizes. Subagents search via run-research |
| Orchestrator delegates synthesis | Master summary becomes stitched per-agent paragraphs | Orchestrator personally reads every core pack and every cross folder before master summary |

## Self-correction triggers

If you notice yourself doing any of the following — **stop**:

- **Skipping Phase 2 templates** and dispatching Wave 2 directly →
  STOP. Templates are the comprehensiveness contract. Without them,
  depth varies by agent and the corpus loses comparability.
- **Writing a thin or generic product template** (≤15 sections) →
  STOP. The template should be maximalist. Re-do Phase 1's deep
  category pre-pass; re-author with ~30+ distinct sections.
- **Hardcoding filenames in the template** → STOP. Templates list
  sections + questions; agents pick filenames per their evidence.
  Filename divergence across entities is correct.
- **Letting subagents silently skip a template section** → STOP.
  Every section gets content OR an explicit one-paragraph
  "insufficient evidence" entry naming the data gap.
- **Dispatching more than 8 subagents in one wave** → STOP.
  Coordination overhead exceeds parallelism savings. Split into
  sub-waves. See `references/orchestration.md`.
- **Summarizing Reddit as "consensus"** without per-comment
  attribution → STOP. Apply the audience-evidence fields from
  `references/synthesis.md`.
- **Treating a vendor's marketing page as confirmed fact** → STOP.
  Re-classify per source hierarchy; vendor claims belong in the
  vendor-claim ledger row.
- **Searching the web yourself as the orchestrator** → STOP.
  Dispatch a subagent. Searching is the subagent's job, via
  run-research.
- **Delegating synthesis** → STOP. Read every core pack and every
  cross folder personally before writing the master summary.
- **Producing a single-report output** ("here's the markdown
  report") → STOP. This skill produces a multi-file corpus. If the
  user wants a single report, redirect to `run-research`.
- **Skipping the completion gate** ("looks done") → STOP. Run the
  verification commands in `references/verification.md`.
  Template-coverage audit, link check, source-ledger presence are
  non-negotiable.
- **Subagent stalled, timed out, or returned shallow output** → STOP
  improvising. Apply the recovery procedures in
  `references/failure-modes.md`.

## Quick start

The first five minutes of any session:

1. **Phase 0**: ask the user up to 3 clarifying questions (decider /
   use case / scale). Write `_meta/01-charter.md` initial draft. Read
   `references/thinking.md` and `references/templates.md` for the
   charter format.
2. **Wave 1**: dispatch two parallel subagents in one tool message —
   discovery + scope-mapping. Both invoke run-research. Use the brief
   template in `references/subagent-briefs.md`. Wait.
3. **Phase 2/3**: read Wave 1 outputs; write templates and
   architecture per `references/templates.md` and
   `references/filesystem.md`. Show the architecture to the user
   before Wave 2.

After that, the loop is: Wave 2 (per-entity, possibly multiple
sub-waves) → Wave 3 (per-axis cross) → optional Wave 4 → Phase 7
verification + master summary. Wave choreography lives in
`references/orchestration.md`; the Phase 7 gate procedure lives in
`references/verification.md` and `references/synthesis.md`.

If anything is unclear, the question is almost always upstream: read
`references/thinking.md` and clarify the decomposition before
dispatching more agents.
