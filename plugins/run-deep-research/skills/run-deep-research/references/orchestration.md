# Orchestration

Wave-based dispatch. The orchestrator launches research subagents in
parallel within a wave; waves run sequentially. Filesystem is the
context channel between waves.

Read this in **Wave 1, 2, 3, 4** when planning dispatches and writing
briefs. For brief templates themselves, see `subagent-briefs.md`.

## The 3-wave default

| Wave | Subagents | Output |
|---|---|---|
| 1 — Discovery + Scope | 2 (parallel: discovery + scope-mapping) | `_meta/02-entities.md`, `_meta/03-axes.md` |
| 2 — Per-entity research | N (parallel, ≤8 per sub-wave; one per `core` entity) | `<entity-slug>/<NN>-<axis>.md` files (≤15 per folder) |
| 3 — Per-axis cross synthesis | M (parallel, ≤8 per sub-wave; one per axis) | `_cross/<axis-slug>/<NN>-<topic>.md` files (≤12 per folder) |
| 4 (optional) | Profile-writers OR promoted-entity researchers | `<entity-slug>.md` profile pages OR additional packs |

After every wave: the orchestrator reads the outputs personally
before dispatching the next wave. This is non-negotiable; subagents
do not see each other's outputs except through files the orchestrator
explicitly references in their brief.

## Phase 0 — Charter (orchestrator-personal, ≤3 user questions)

Phase 0 produces `_meta/01-charter.md` initial draft. Before Wave 1
dispatches.

Procedure:

1. **Read the user's request carefully.** Identify what is stated
   and what is unstated. Apply the 7-question decomposition from
   `thinking.md`; mark each question as "answered by the user",
   "implicit but inferable", or "needs clarification".
2. **Ask up to 3 clarifying questions**, only on the genuinely
   unstated and decision-relevant. Common ones:
   - "What will you do with this research?" (always, if unstated)
   - "Who is the decider — role and constraint?" (if generic)
   - "What is the time horizon for the decision?" (if open-ended)
   Skip questions whose answer is obvious from the request.
3. **Write `_meta/01-charter.md` initial draft** per the format in
   `templates.md`. Answer all 7 decomposition questions explicitly.
   Where Wave 1B will resolve a placeholder (axis catalog, native
   primitives), say so explicitly.
4. **Show the charter to the user before Wave 1 dispatches.** The
   user may correct the charter; corrections cost less here than
   later. Save user feedback alongside the charter.

The charter is updated after Wave 1 to a "resolved" status with the
axis catalog locked.

## Wave 1 — Discovery + Scope (parallel, 2 subagents)

Wave 1 dispatches **two parallel subagents in one tool message**.
Both invoke the run-research skill. Both run independently; their
write scopes are disjoint.

### Subagent 1A — Discovery agent

**Goal**: enumerate every entity that should be evaluated, tier
each, status-check each.

**Inputs read** (paths the brief explicitly names):
- `_meta/01-charter.md` (the orchestrator's initial charter)

**Output written**:
- `_meta/02-entities.md` (a tiered table: `core` / `secondary` /
  `discovered-only`)

**Methodology**: the brief decomposes discovery into 3-5 orthogonal
sub-questions (incumbents / challengers / open-source / geographic
outliers / recent entrants). Each sub-question surfaces a different
candidate cluster.

**Tool steering inside the subagent's run-research session**:
- Parallel `web-search` calls per sub-question, mixing open-web
  keyword probes with explicit `site:reddit.com/r/.../comments`
  probes for reddit-sourced candidates. Two `web-search` calls in
  one turn.
- Optional `scrape-link` on category-index pages or curated lists
  (pass an `extract` string naming what to pull from each index).
- Status-check each candidate via `scrape-link` with extract
  = "active / dead / waitlist / acquired with last-update date".

**Stop criteria**: every sub-question surfaced ≥3 candidates; every
candidate has a status; the long tail beyond 50 candidates is tiered
to `discovered-only`.

### Subagent 1B — Scope-mapping agent

**Goal**: derive the axis catalog by answering the 7 decomposition
questions for THIS specific category.

**Inputs read**:
- `_meta/01-charter.md`

**Output written**:
- `_meta/03-axes.md` (the axis catalog: name, native primitive,
  decision weight, suggested folder slug)

**Methodology**: the brief tells the subagent to research the
*category itself*, not specific entities. Identify the axes deciders
weigh, the native primitives per axis, the practitioner channels for
this domain, the recent (last 12 months) shifts, the lock-in / exit
shape.

**Tool steering**:
- `web-search` keyword probes for "decision axes deciders compare
  on for <topic>; native primitives per axis; not feature lists; not
  marketing" — then `scrape-link` with a matching `extract` on 2-3
  authoritative analyses (practitioner blog posts, analyst writeups,
  well-cited HN threads).
- `web-search` with explicit `site:reddit.com/r/.../comments` probes
  to capture practitioner-channel naming.

**Stop criteria**: every axis has a name, a native primitive, and a
decision weight (decision-flipping / important / nice-to-know).

### Orchestrator gate after Wave 1

The orchestrator reads `_meta/02-entities.md` and `_meta/03-axes.md`,
merges and resolves:

- Promote/demote entities the scope agent surfaced as canonical.
- Lock the axis list (becomes the section structure for every
  entity pack).
- Update `_meta/01-charter.md` with the resolved charter.

Then write Phase 2 templates and Phase 3 architecture (no subagents
for these — orchestrator-personal).

## Phase 2 — Templates (orchestrator-personal, no subagents)

Phase 2 produces `_meta/04-product-template.md` and
`_meta/05-axis-templates.md`. After Wave 1 returns and the charter
is resolved.

Procedure:

1. **Read `_meta/02-entities.md` and `_meta/03-axes.md`** (Wave 1
   outputs).
2. **Read the seven decomposition answers in the resolved charter.**
3. **Write the product template** per the format in `templates.md`:
   - Maximalist (~30+ sections).
   - One axis per axis in the catalog.
   - Per-section "what questions" and "what evidence belongs here".
   - Native primitives per axis section.
   - Cross-references to `_cross/<axis-slug>/`.
   - No filenames.
4. **Write the axis templates** per the format in `templates.md`:
   - One axis per axis in the catalog.
   - Comparison columns specified.
   - Ranking dimension specified (conditional, with named variables).
   - ≥3 scenario splits.
   - Required minimum cross files listed.
5. **Show the templates to the user before Wave 2.** The user may
   request additions; their feedback is the comprehensiveness audit.
6. **Log the template count and date in `_meta/07-dispatch-log.md`.**

Skipping Phase 2 is a hard failure. Wave 2 dispatched without
templates produces shallow, non-comparable packs.

## Phase 3 — Architecture (orchestrator-personal, no subagents)

Phase 3 produces `_meta/06-file-budget.md` and pre-creates the
folder skeleton. After templates lock.

Procedure:

1. **Compute expected file counts** per entity (≈ axis count + 2
   for overview and sources) and per axis (≈ 4-6 for overall +
   scenarios + contradictions).
2. **Verify expected counts fit MAX-N ceilings** (15 / 12 / 8). If
   any folder would exceed cap, adjust template structure (split a
   busy axis into multiple sub-axes; combine related thin sections).
3. **Lay out the wave dispatch plan**: Wave 2 sub-waves needed,
   Wave 3 sub-waves needed, optional Wave 4 missions, retry budget.
4. **Write `_meta/06-file-budget.md`** per the format in
   `templates.md`.
5. **Pre-create empty folders** per the script in `templates.md`
   ("Pre-creating folders before Wave 2"). Empty folders are
   commitments.
6. **Show the architecture to the user before Wave 2 dispatch.**

## Wave 2 — Per-entity research (parallel, ≤8 per sub-wave)

Wave 2 dispatches **N parallel subagents, ≤8 per wave**, one per
`core` entity. Each invokes the run-research skill.

### Brief shape

(Full template in `subagent-briefs.md`.) Each Wave 2 brief includes:

- **Charter context**: the resolved charter, the entity name, the
  axis list with native primitives, the practitioner-channel list.
- **The run-research integration block**: mandatory; tells the
  subagent how to drive the toolkit.
- **Owned write scope**: `<entity-slug>/` — and only that folder.
- **Read scope**: `_meta/01-charter.md`, `_meta/03-axes.md`,
  `_meta/04-product-template.md`. Not other `<entity-slug>/`
  folders; not other agents' work.
- **DoD**: every axis in the charter is addressed in this entity's
  pack — content OR an explicit "insufficient evidence" entry
  naming the data gap.
- **MAX-N**: 15 files per `<entity-slug>/` folder.
- **File-naming protocol**: `<NN>-<axis-slug>.md`; agent picks
  axis-slug per their evidence.

### Sub-waves when N > 8

If `core` entity count > 8, run multiple Wave 2 sub-waves. Process
completed agents as they return; do not gate on the slowest.

The order of sub-waves is whatever order makes sense (alphabetical,
by tier within `core`, by source-richness). Do not optimize; just
ship sub-waves of ≤8.

### Tool steering inside the subagent

Each Wave 2 subagent's run-research session:

- Call `get-research-consultancy` with goal = "build full evidence pack for
  <entity> on every axis in the charter for <decider use case>;
  quote discipline = every numeric/versioned/priced claim verbatim".
- Wave 2 reconnaissance: parallel `web-search` calls — open-web
  keyword probes plus explicit `site:reddit.com/r/.../comments`
  probes — different scopes, one turn.
- Per-axis evidence capture: `scrape-link` with a facet-rich
  `extract` on docs, changelog, pricing pages (≤5 URLs per call);
  `scrape-link` on Reddit threads with a quote-preserving `extract`
  (≤5 threads per call).
- Round 2: harvest `## Follow-up signals`; fire refined `web-search`
  probes.

The orchestrator's brief sets the dispatch shape (parallel scopes,
extract page-type hints, freshness window). The brief should not
over-prescribe specific keywords; the run-research skill teaches
the agent how to write keyword fan-outs.

## Wave 3 — Per-axis cross synthesis (parallel, ≤8 per sub-wave)

Wave 3 dispatches **M parallel subagents, ≤8 per wave**, one per
axis in the charter. **Wave 3 subagents do NOT use run-research** —
their work is local-files synthesis, not web research.

### Brief shape

Each Wave 3 brief includes:

- **Read scope**: every `<entity-slug>/<NN>-<axis-slug>.md` file for
  this axis across all `core` entities, plus the corresponding
  `09-sources.md` (or equivalent) per entity for citation
  resolution.
- **Write scope**: `_cross/<axis-slug>/` — and only that folder.
- **Per-axis comparison template**: from `_meta/05-axis-templates.md`
  — what comparison axes, matrix columns, ranking dimensions to use.
- **DoD**: every entity is read; every contradiction is surfaced;
  the matrix has a value per (entity, comparison-column) cell or an
  explicit "no evidence" marker; ranking is source-backed with cited
  evidence.
- **MAX-N**: 12 files per `_cross/<axis-slug>/` folder.
- **File-naming protocol**: `<NN>-<topic-slug>.md`; agent picks
  topic-slug.

### What Wave 3 produces

For each axis, the minimum:

- `00-overall-comparison.md` — the matrix, ranking, recommendation,
  evidence confidence, scenario-specific guidance, what would change
  the answer.
- Granular comparison files per scenario (e.g., `01-by-scale.md`,
  `02-contradictions.md`, `03-decision-flippers.md`) up to the MAX
  12 cap.

### Why no run-research in Wave 3

Wave 3's job is synthesis over evidence already captured in Wave 2.
Web search at this stage means the Wave 2 brief left a gap — the
right move is to send the relevant Wave 2 agent back, not to have
the Wave 3 synthesizer do mid-stream web research.

If Wave 3 reveals an evidence gap not in `## Not found` sections of
Wave 2 outputs: log it in `_meta/07-dispatch-log.md`, and consider a
targeted Wave 4 mission to fill the gap.

## Optional Wave 4 — Profile pages OR promoted-entity research

Default sessions stop after Wave 3. Add Wave 4 when:

- The decider needs profile pages (decision-grade per-entity
  summaries with section ordering: metadata, executive summary,
  headline findings, best-fit, do-not-choose-if, pack map, deep
  profile, numbers table, open gaps, sources).
- A `secondary` entity revealed decision-flipping evidence and
  warrants promotion to `core` plus a full pack.

### Profile-page Wave 4

One subagent per `core` entity (parallel, ≤8 per sub-wave). Each
reads its `<entity-slug>/` pack and writes `<entity-slug>.md` at the
corpus root.

Profile-page subagents do NOT use run-research (no web research).
They synthesize from local files.

### Promoted-entity Wave 4

Wave-2-style brief, one subagent per promoted entity. Uses
run-research. Writes to its newly-`core` `<entity-slug>/` folder.

Then, if profile pages are part of the deliverable, the promoted
entity also gets a profile in a subsequent Wave 4 sub-wave (or in
the same wave alongside the profile-writers).

## The between-wave gate procedure

After every wave's subagents return, run the gate procedure
personally — do not delegate. This is the most-skipped step and
the most common cause of corpora that look done but are not.

Procedure:

1. **Read every output file.** Not skim. Read.
2. **Cross-reference against each subagent's DoD.** For each
   criterion, verify it was met (with evidence). Flag silent
   gap-skips.
3. **Update `_meta/07-dispatch-log.md`** with:
   - Per agent: dispatched, returned, retries, met-DoD, missed-DoD.
   - Discoveries that affect downstream waves: tier promotions,
     missed entities, axis revisions.
   - Template amendments if any.
4. **Decide**: next wave, retry on this wave, or escalate.
   - **Next wave** if every subagent met its DoD (or remaining
     gaps are non-decision-flipping and can be surfaced in the
     master summary).
   - **Retry** if a subagent silently skipped a section or returned
     shallow output. Send back with specific gaps named (max 2
     retries per agent per mission).
   - **Escalate** if a charter error has been revealed (return to
     Phase 0 or Wave 1; do not paper over with more research).
5. **Update the charter** if anything in the wave's outputs requires
   it (tier promotions, axis additions/revisions, freshness window
   adjustments). Charter revisions are logged in
   `_meta/07-dispatch-log.md`.

After Wave 1: lock the axis catalog; resolve the charter.
After Wave 2: verify template coverage per entity; flag
insufficient-evidence patterns.
After Wave 3: verify cross-folder coverage; surface contradictions
for the master summary.
After Wave 4 (if run): verify profiles or promoted-entity packs;
re-run Wave 3 sub-waves for any axis whose comparison meaningfully
changed.

## Parallel-dispatch rules

- **MAX 8 subagents per wave.** Beyond 8, coordination overhead
  exceeds parallelism savings. For larger investigations, run
  sequential sub-waves.
- **Disjoint write scopes.** Each subagent owns exactly one folder.
  Two subagents writing to the same folder produces conflicts.
- **Self-contained briefs.** Subagents do not see the orchestrator's
  conversation. Every brief carries all context the agent needs.
- **No subagent-of-subagent for the orchestration layer.** The
  run-research skill internally may spawn read-only Explore
  subagents for triage of large persisted outputs — that is bounded
  inside the subagent's own session and acceptable.
- **Process completed agents as they return.** Do not gate on the
  slowest. Start integrating early-returners' outputs while
  late-returners finish.
- **MAX 2 retries per agent per mission.** If the second attempt
  fails, log the gap and move on (or escalate to the user).

## Tool steering by use case

| Use case | Wave | Tool dispatch (inside the subagent's run-research session) |
|---|---|---|
| Find entities (Wave 1A) | 1 | Parallel `web-search` per sub-question (open web + explicit `site:reddit.com/r/.../comments` probes); `scrape-link` on category indexes |
| Map axes (Wave 1B) | 1 | `web-search` keyword probes for decision axes; `scrape-link` with a matching `extract` on 2-3 authoritative analyses |
| Per-entity overview (Wave 2) | 2 | `get-research-consultancy` per entity → parallel `web-search` (open web + reddit-scoped probes) → `scrape-link` on docs and Reddit threads with a facet-rich `extract` |
| Per-entity sentiment (Wave 2) | 2 | `scrape-link` on Reddit thread permalinks with a quote-preserving `extract`; Reddit API fetches the full threaded post + comments before extraction |
| Per-entity pricing/security (Wave 2) | 2 | `scrape-link` with page-type-aware `extract` per run-research's prompting guide |
| Cross-entity synthesis (Wave 3) | 3 | LOCAL-ONLY: read files; no web tools |
| Profile pages (Wave 4 / orch) | 4/7 | LOCAL-ONLY: read pack files, write profile |
| Master summary (Phase 7) | 7 | LOCAL-ONLY: orchestrator reads everything, writes |

The orchestrator's job is to choose the right tool for the right
step in the brief; the subagent then executes via its run-research
session. The brief should not over-prescribe (do not tell the agent
which exact keywords to use) but should set the dispatch shape
(parallel scopes, extract page-type hints, freshness window).

## What the orchestrator does NOT do

- **Does not search the web.** Subagents search.
- **Does not scrape pages.** Subagents scrape.
- **Does not delegate synthesis.** The orchestrator personally reads
  every `<entity-slug>/` core pack and every `_cross/<axis-slug>/`
  folder before writing the master summary. Subagents may write
  per-axis cross syntheses, but the master summary is the
  orchestrator's signature artifact.
- **Does not let subagents recurse.** Two-level orchestration only,
  with the bounded-internal exception for run-research's own triage.

## When a wave fails

- **A subagent times out**: split scope (smaller mission) or retry
  with a narrower brief. MAX 2 retries.
- **A subagent returns shallow output**: depth-gate review (per
  `failure-modes.md`); send back with specific gaps named.
- **The wave reveals the charter was wrong**: stop. Return to
  Phase 0 or Wave 1B; re-derive the axis catalog. Do not mask
  charter errors with more research.
- **Two subagents disagree on a fact**: surface in synthesis; tier
  by source credibility per run-research's synthesis discipline;
  never silently pick.

## The orchestrator's between-wave log

Maintain `_meta/07-dispatch-log.md` as a running log:

- Per wave: dispatched-N, returned-N, retry-N, failed-N.
- Per subagent: brief summary, which DoD criteria were met, any
  gaps the subagent surfaced.
- Between-wave decisions: tier promotions/demotions, charter
  revisions, axis additions/removals.

This log is for the orchestrator's own state-tracking. It also
feeds the Phase 7 master summary (the "Coverage scope" section
references it).

## Quick reference

```
PHASE 0 (orchestrator interactive):
  Write _meta/01-charter.md (initial)

WAVE 1 (parallel, 2 subagents — both invoke run-research):
  → _meta/02-entities.md
  → _meta/03-axes.md
  Orchestrator reads and locks charter.

PHASE 2 (orchestrator):
  Write _meta/04-product-template.md
  Write _meta/05-axis-templates.md

PHASE 3 (orchestrator):
  Write _meta/06-file-budget.md

WAVE 2 (parallel ≤8, possibly multiple sub-waves — invoke run-research):
  → <entity-slug>/<NN>-<axis>.md per core entity

WAVE 3 (parallel ≤8, possibly multiple sub-waves — local-only):
  → _cross/<axis-slug>/<NN>-<topic>.md per axis

WAVE 4 (optional):
  → <entity-slug>.md profiles (local-only) OR
  → additional <entity-slug>/ packs (invoke run-research)

PHASE 7 (orchestrator):
  Read everything personally
  Write _meta/00-master-summary.md
  Run verification commands
```
