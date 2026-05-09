# Templates and Charter

The orchestrator's between-wave artifacts. Read this in **Phase 0,
2, 3** when writing the charter, product template, axis templates,
and file budget — the artifacts that bind every downstream subagent.

These are the comprehensiveness contracts. Without them, subagents
make shallow choices unilaterally; with them, every brief inherits
the discipline.

## The four artifacts

| Artifact | Phase | Audience |
|---|---|---|
| `_meta/01-charter.md` | 0 (initial) → Wave 1 (resolved) | Wave 1 subagents + orchestrator across waves |
| `_meta/04-product-template.md` | 2 | Wave 2 subagents (per-entity researchers) |
| `_meta/05-axis-templates.md` | 2 | Wave 3 subagents (per-axis synthesizers) |
| `_meta/06-file-budget.md` | 3 | Orchestrator (and the user, before Wave 2 dispatch) |

## The charter (`_meta/01-charter.md`)

Write in Phase 0 (initial draft); update after Wave 1 (resolved
version with axis catalog locked). The charter answers all 7
decomposition questions explicitly. Without all 7 answered, do not
dispatch Wave 1; the brief will be vague and the entity/axis lists
will be wrong.

### Format

```markdown
# Research charter

**Capture date:** YYYY-MM-DD
**Status:** initial / resolved (after Wave 1)

## Decider profile

[role; constraint; what they will do with this corpus; geography
or jurisdiction; budget if relevant; risk tolerance; reversibility
shape — one paragraph]

## Decision framing

[the decision being made; what success looks like; what the decider
already knows and need not be re-confirmed]

## Entity definition

[what counts as one entity in this session; what does not count;
adjacencies that are out-of-scope and the boundary rule used]

## Axis catalog

| Axis | Native primitive | Decision weight | Folder slug |
|---|---|---|---|
| <axis-1> | <unit> | decision-flipping / important / nice-to-know | <axis-1-slug> |
| <axis-2> | <unit> | ... | <axis-2-slug> |

(Initial draft has placeholders; resolved version after Wave 1B.)

## Practitioner channels

[specific subreddits, HN angles, professional forums, trade
publications, GitHub repos, mailing lists, Discord servers — by
name, not generic "Reddit and HN"]

## Recent shifts (last 12 months)

[changes in the domain that calibrate the freshness window — name
events with dates and citations after Wave 1B]

## Lock-in / exit / mistake-recovery shape

[what does it cost to switch away; what does a wrong choice cost;
what does mistake-recovery look like for the decider]

## Skip list

[topics, axes, regimes the corpus deliberately excludes — and why]

## Freshness window

[default: weight last 90 days; longer for stable axes; shorter for
fast-moving regulatory or pricing axes — one rule per axis if
needed]

## Quote discipline

Every numeric / versioned / priced claim cites a verbatim quote
with URL and scrape date. Snippet citations are forbidden.
```

### Authoring discipline

- **Specificity about the decider, not generic.** "Engineering
  manager picking infrastructure for a 30-person team with a 2026
  Q3 budget of $X" beats "someone choosing a tool".
- **Explicit skip list.** Without it, seeds wander into adjacent
  topics. Listing what to skip is half the discipline.
- **Native primitives per axis.** Comparison without primitives is
  incoherent. The Wave 1B agent's job is to fill primitives if the
  initial charter has placeholders.

## The product template (`_meta/04-product-template.md`)

Write in Phase 2 after Wave 1 returns. The product template lists
every section every entity pack must address — the comprehensiveness
boundary for Wave 2.

### Authoring discipline

- **Maximalist, not minimalist.** Target ~30+ distinct sections
  across all axes. If under 15 sections, the deep category pre-pass
  was insufficient — return to Wave 1B and re-derive axes.
- **Sections + questions, not filenames.** Each section names a
  topic and the specific questions that section must answer. Agents
  pick filenames matching their evidence shapes.
- **Per-section "what evidence belongs here".** Without this,
  agents under-specify; with it, agents know whether a piece of
  evidence belongs in section A or section B.
- **Sparse evidence is acceptable; missing axes are not.** A
  section with thin evidence becomes a one-paragraph "insufficient
  evidence" entry. A skipped axis is a failure.

### Format

```markdown
# Product template

The comprehensiveness contract for every Wave 2 per-entity research
mission. Every section here is addressed in every `core` entity
pack — content OR explicit "insufficient evidence" entry naming
the data gap.

## 00 — Overview

What this section answers:
- Who or what is the entity (one paragraph)?
- Vendor / maintainer / provider / publisher of record
- Headline framing (positioning quote verbatim)
- Capture date and current status

What evidence belongs here:
- Official "about" or "overview" page (verbatim quote with URL)
- One-line entity description
- Capture date

Native primitive: n/a (overview is descriptive)

## 01 — <axis-1-name>

What this section answers:
- <question 1 — specific, evidence-shaped>
- <question 2 — specific, evidence-shaped>
- <question 3 — specific, evidence-shaped>
- <question 4 — specific, evidence-shaped>

What evidence belongs here:
- <source class 1, e.g., official docs page on /pricing>
- <source class 2, e.g., changelog announcements>
- <source class 3, e.g., practitioner thread on r/<sub>>

Native primitive: <unit>
Decision weight: <decision-flipping / important / nice-to-know>
Cross-references: feeds `_cross/<axis-1-slug>/`

## 02 — <axis-2-name>

[same shape]

## 03 — <axis-3-name>

[same shape — continue for every axis in `_meta/03-axes.md`]

## 09 — Sources / claims ledger

What this section answers: every claim's provenance.

Format (one row per load-bearing claim):

| Claim | Type | Evidence URL | Scrape date | Confidence | Caveat |
|---|---|---|---|---|---|
| <claim> | confirmed fact / vendor claim / practitioner / inference / contradicted / unverified | <URL> | YYYY-MM-DD | High / Medium / Low | <caveat or n/a> |
```

### How to know the product template is good

- ≥30 distinct sections (counting axis sub-sections).
- Every section names specific questions, not just topics.
- Every axis from `_meta/03-axes.md` has a section.
- Per-section evidence-class hints are concrete (e.g., "vendor
  docs `/pricing`", not "the website").
- Native primitives appear per axis section.
- Cross-references are explicit (which `_cross/<axis-slug>/` does
  this section feed).

### How to know the product template is bad

- Fewer than 15 sections.
- Sections named only by category ("Pricing", "Security",
  "Performance") without per-question prompts.
- Filenames prescribed (template lists `01-pricing.md`).
- Generic "research deeply" without specifying evidence shape.
- No native primitives.
- No cross-references.

## The axis templates (`_meta/05-axis-templates.md`)

Per-axis comparison templates for Wave 3 synthesizers. One per axis
from the catalog. Can be a single file with an H2 per axis, or
split per axis if the file would exceed reasonable length.

### Authoring discipline

- **Each axis specifies its comparison columns.** What dimensions
  distinguish entities along this axis? List them.
- **Each axis specifies its ranking dimension.** What does "wins
  on this axis" mean? Conditional ranking is the norm; flat ranking
  is rare.
- **Each axis specifies scenario splits.** When does the answer
  flip? Name the variables.
- **Each axis prescribes minimum cross files.** At minimum:
  `00-overall-comparison.md`. Plus scenario / contradiction /
  decision-flipper files up to the MAX 12 cap.

### Format (per axis)

```markdown
## Axis template: <axis-name>

Folder: `_cross/<axis-slug>/`
Native primitive: <unit>
Decision weight: <decision-flipping / important / nice-to-know>

### Comparison columns

The matrix in `00-overall-comparison.md` has columns:

| Entity | <column 1> | <column 2> | <column 3> | <column 4> | Source |

Each column captures: <what evidence shape goes in each cell>.
Empty cells are not allowed; an explicit "no evidence" marker
serves where evidence is missing.

### Ranking dimension

How "wins on this axis" is defined: <ranking logic>.

The ranking is conditional on:
- <variable 1> (changes ranking when X)
- <variable 2> (changes ranking when Y)

### Scenario splits

| Scenario | Best fit | Why |
|---|---|---|
| <scenario A> | <entity> | <evidence-cited reasoning> |
| <scenario B> | <entity> | <evidence-cited reasoning> |
| <scenario C> | <entity> | <evidence-cited reasoning> |

### Contradictions to surface

When entities' evidence conflicts on this axis, surface in
`02-contradictions.md` with both quotes and source URLs. Tier by
source credibility; never silently pick.

### Required cross files

Minimum:
- `00-overall-comparison.md` (matrix + ranking + recommendation
  + evidence confidence + contradictions section + scenario
  guidance + what would change the answer)

Often:
- `01-<scenario-cluster>.md` (one or more scenario-specific files)
- `02-contradictions.md` (when contradictions exist)
- `03-decision-flippers.md` (variables that flip the ranking)

Up to the MAX 12 cap; the agent picks based on evidence richness.

### Sources

Wave 3 cites per-entity evidence files
(`<entity-slug>/<NN>-<axis-slug>.md`) and entity-level sources
(`<entity-slug>/09-sources.md`). No web research in Wave 3 — local
files only.
```

### How to know an axis template is good

- Comparison columns named with evidence-shape hints.
- Ranking is conditional with variables named.
- ≥3 scenarios listed.
- Contradiction-handling rule explicit.
- Required minimum cross files listed.

### How to know an axis template is bad

- "Compare entities on <axis>" without column structure.
- Flat ranking with no conditions.
- No scenarios.
- No contradiction-handling guidance.

## The file budget (`_meta/06-file-budget.md`)

Write in Phase 3 after templates lock. The file budget IS NOT a
hard cap; it is a sanity check that the templates' minimum coverage
is feasible within the MAX-N ceilings.

### Format

```markdown
# File budget

## Tree shape

[ASCII tree: _meta/, <entity-slug>/ folders for every core entity,
_cross/<axis-slug>/ folders for every axis]

## Expected file count

- _meta/: 8 files (charter, entities, axes, product template, axis
  templates, file budget, dispatch log, master summary)
- per `core` entity: <axis count + 2> files
  (overview + axes + sources)
- _cross/<axis-slug>/: 4-12 files per axis (overall + scenarios +
  contradictions + decision-flippers)
- profile pages (if Wave 4 includes profiles): 1 per `core` entity
  at corpus root

Estimated total: <range, e.g., 80-150 files>

## MAX-N caps

| Folder | MAX-N | Used in this budget |
|---|---|---|
| `<entity-slug>/` | 15 files | <expected per entity> |
| `_cross/<axis-slug>/` | 12 files | <expected per axis> |
| `_meta/` | 8 files | 8 |
| Subagents per wave | 8 | 8 |

If expected file count exceeds the cap on any folder, adjust
template structure (split a busy axis into multiple sub-axes;
combine related thin sections) before Wave 2 dispatch.

## Tier assignments

[Read from `_meta/02-entities.md`; mark each entity as core /
secondary / discovered-only with one-line rationale per row.]

## Wave dispatch plan

- Wave 2: <N> subagents in <ceil(N/8)> sub-waves, one per `core`
  entity
- Wave 3: <M> subagents in <ceil(M/8)> sub-waves, one per axis
- Wave 4 (optional): <profile pages | promoted-entity research>
  with explicit count

## Pre-creation status

[Folders pre-created on YYYY-MM-DD via the script in templates.md
section "Pre-creating folders before Wave 2".]
```

## Pre-creating folders before Wave 2

After the file budget locks, pre-create the empty folder skeleton
so agents see the tree shape they are expected to fill. Empty
folders are commitments.

```bash
CORPUS=<corpus-root-absolute-path>
mkdir -p "$CORPUS/_meta" "$CORPUS/_cross"

# Read core entity slugs from _meta/02-entities.md
# (orchestrator extracts manually or via shell parsing)
CORE_ENTITIES="<slug1> <slug2> <slug3> ..."
for entity in $CORE_ENTITIES; do
  mkdir -p "$CORPUS/$entity"
done

# Read axis slugs from _meta/03-axes.md
AXES="<axis-1-slug> <axis-2-slug> <axis-3-slug> ..."
for axis in $AXES; do
  mkdir -p "$CORPUS/_cross/$axis"
done

# Verify
find "$CORPUS" -type d
```

## Tier-promotion mechanics

When a `secondary` entity reveals decision-flipping evidence during
Wave 2 or 3:

1. Update `_meta/02-entities.md`: change tier from `secondary` to
   `core`; add a note "promoted in Wave <N> due to <specific
   evidence>".
2. Add the entity to `_meta/06-file-budget.md` with the same
   template-coverage requirements as other `core` entities.
3. Dispatch a Wave 4 mission (Wave-2-style brief) for the promoted
   entity, including the run-research integration block.
4. After the promoted entity's pack lands, run a sub-wave of Wave 3
   for any axis whose comparison meaningfully changes (the
   orchestrator decides which axes need re-synthesis).

When a `core` entity must be demoted (rare):

1. Update `_meta/02-entities.md`: change tier; add a note
   explaining why (acquired and folded into <parent>; discontinued;
   discovered to be out-of-category).
2. The existing `<entity-slug>/` folder remains for traceability;
   do not delete files written.
3. The master summary explicitly notes the demotion and reasoning.

## Updating templates mid-session

Discouraged but sometimes necessary.

- **Minor gap (one missing question per axis)**: orchestrator
  amends the template; subsequent agents use the amended version;
  existing agents are not retried unless the gap is decision-
  flipping. Log the amendment in `_meta/07-dispatch-log.md`.
- **Major gap (missing axis)**: the charter was wrong. Stop. Return
  to Wave 1B; re-derive the axis catalog; re-author the relevant
  templates; re-dispatch Wave 2 for the missing axis.

Template revisions are always logged in
`_meta/07-dispatch-log.md` with the wave / sub-wave that triggered
the revision.

## The dispatch log (`_meta/07-dispatch-log.md`)

Maintain across waves. Format:

```markdown
# Dispatch log

## Wave 1 (<YYYY-MM-DD>)

- Subagent 1A (discovery): dispatched <time>; returned <time>;
  produced `_meta/02-entities.md`; <N> candidates in tier core /
  <M> in secondary / <K> in discovered-only.
- Subagent 1B (scope-mapping): dispatched <time>; returned <time>;
  produced `_meta/03-axes.md`; <N> axes named.

## Phase 2 (<YYYY-MM-DD>)

- Wrote `_meta/04-product-template.md`: <N> sections.
- Wrote `_meta/05-axis-templates.md`: <N> axis templates.
- Templates shown to user: <YYYY-MM-DD HH:MM>.

## Wave 2 (<YYYY-MM-DD>)

- Sub-wave 1 (entities <list>): dispatched <time>; <K> returned
  successfully; <L> retried (reason); <M> failed.
- Sub-wave 2 (entities <list>): ...
- Tier promotions: <entity X promoted in Wave 2 because <evidence>>.
- Template amendments: <none / list>.

## Wave 3 (<YYYY-MM-DD>)

- Sub-wave 1 (axes <list>): dispatched <time>; <K> returned.
- Sub-wave 2 (axes <list>): ...
- Contradictions surfaced: <count>.
- Insufficient-evidence patterns: <axes where multiple entities had
  insufficient-evidence entries>.

## Phase 7 (<YYYY-MM-DD>)

- Verification commands run: <list>.
- Failed checks: <list>.
- Master summary written: <YYYY-MM-DD HH:MM>.
```

This log is the orchestrator's working state. It feeds the master
summary's "Coverage scope" section. Subagents do not read it (their
read scopes are explicit and narrower).
