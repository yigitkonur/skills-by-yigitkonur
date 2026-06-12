# Effort Routing

How to choose `low` / `medium` / `high` for each wave's codex jobs. This is
the **first-class wave-level lever** in this skill. Get it wrong and you
either burn budget on extraction waves or under-think synthesis waves.

Read this in **Phase 0** (designing the effort plan) and at every wave
transition (validating the chosen effort against the wave's actual
shape).

## The three levels

| Effort | Codex shape it fits |
|---|---|
| **`low`** | Mechanical extraction with a constrained answer shape. The question of "what to write" is mostly answered by the inputs; codex's job is to parse, normalize, and emit. No multi-round web research, no architectural decisions. |
| **`medium`** | Standard per-entity research. Multi-round web search, multi-source synthesis, evidence packs across multiple template sections, citation discipline. The canonical case. |
| **`high`** | Synthesis across many sub-findings, cross-entity comparison, corpus-structure design from a noisy candidate pool, decisive promoted-entity research where the recommendation flips on a few hard facts. |

## Mapping by wave type

### Wave 1 — Discovery + Scope

**Default: `high`.**

Why: discovery is a synthesis-shaped task. Even when the candidate pool
looks short, the job is "find every entity, tier each, derive the axis
catalog, identify practitioner channels, flag recent shifts" — that
spans web search, Reddit reconnaissance, source triage, and tiered
classification. Medium reliably under-thinks this and produces a thin
entity list that hobbles every downstream wave.

Exceptions:

- **The user already named the entity list explicitly** (e.g., "research these 12 vendors I named") and Wave 1 is just axis-catalog derivation → split the wave: skip the discovery job, keep the axis-derivation job at `high`.
- **Trivial domains** (≤3 entities, well-known category, no axis catalog needed) — usually means this skill is the wrong choice; route to `run-research` instead.

### Wave 2 — Per-entity packs

**Default: `medium`.**

Why: the canonical per-entity case. Codex reads the charter, the entity
row, the product template (Phase 2 output), and any earlier-wave files
the orchestrator shared. Codex does its own multi-round web research,
writes one file per template section, addresses every section (content
OR explicit "insufficient evidence" entry). Medium is the right level
for this shape — high burns budget without measurably improving the
pack, low under-researches and produces shallow files.

Exceptions:

- **A `core` entity is the *decisive* one for the user's decision** (e.g., "if Vendor X works for our use case, we stop researching"): override that one job to `high`. Record the override in the dispatch plan.
- **`secondary`-tier entities at compact scale** can drop to `low` if the template requires only a short overview, native pricing snapshot, and one-line audience signal. Most secondary entities should stay at `medium` — the cost delta vs `low` is usually less than the comparability gain.

### Wave 3 — Per-axis cross synthesis

**Default: `high`.**

Why: cross-entity comparison is structurally a synthesis task. Codex
reads N entities' axis-specific files plus the comparison template,
must rank, surface decision-flippers, model scenarios, and identify
contradictions across sources. This is multi-source comparison at
its purest — medium reliably under-ranks (just appends per-entity
summaries) and `high` is the cost-effective level.

Exceptions:

- **A purely tabular cross axis** (e.g., a "feature presence matrix" with binary cells) can drop to `medium` if every cell's evidence is already in the input packs and codex just has to read-and-extract. Rare.

### Wave 4 — Profile pages / promoted-entity research

**Profile pages: `medium`.** The profile is a synthesis of an already-built
pack — short job, narrative-shaped, but it must read the whole pack and
write a coherent decision page. Medium is the right level. Drop to `low`
only when the profile is intentionally formulaic (a short scorecard, not
a narrative).

**Promoted-entity research: `high`.** When Wave 2's reading reveals that
one entity is decision-critical and the existing pack is insufficient,
the promoted-research job is structurally a Wave 1 + Wave 2 hybrid for
one entity — broader exploration, deeper synthesis. `high`.

### Mechanical-extraction sub-waves

**Default: `low`.**

These are sub-waves the orchestrator inserts when the corpus needs a
high-volume, low-decision-density artifact:

- **Per-source distillation:** 40 source URLs from `_meta/discovered-sources.md`; one structured row per URL (title, claim, evidence quality). Forty parallel `low` jobs.
- **Reddit-thread quote extraction:** N Reddit permalinks; one row per thread (top voted comment, sentiment, bias label). Use `raw-scrape-links` inside the codex prompt and a fixed output schema.
- **Pricing-table normalization:** N vendors with public pricing pages; one normalized row per vendor (native unit, included quota, overage shape). 
- **Source-map maintenance:** read all per-entity source ledgers; emit one consolidated cross-corpus source map.

In all these, the answer shape is fixed by the orchestrator's prompt;
codex just fills cells. `low` is the cost-effective level.

## Three to four concrete examples (named explicitly)

### Example 1 — "Wave 3 cross-pricing comparison, 12 entities"

**Wave shape:** read 12 entities' `01-pricing.md` files plus the
`_meta/_COMPARISON_TEMPLATE_pricing.md` template; write
`_cross/pricing/00-overall-comparison.md` with native-unit matrix,
scenario-cost models, ranking, and decision-flippers.

**Effort: `high`.**

Why: this is comparison and synthesis across 12 sources with a 5+
column matrix and at least 3 scenario models. Medium produces a list
that reads "Vendor A: $X/mo. Vendor B: $Y/mo. ..." — that's not a
comparison.

### Example 2 — "Wave 2 per-entity pack, one SaaS vendor, ~8 axes"

**Wave shape:** read charter + entity row + `_PRODUCT_TEMPLATE.md`;
do multi-round web research; write `<entity-slug>/00-overview.md`
through `09-sources.md`.

**Effort: `medium`.**

Why: the canonical case. Multi-round web research, multi-source
synthesis, per-axis content. Medium is the right level. The 8 axes
are independent enough that high doesn't measurably improve the
output.

### Example 3 — "Source-distillation sub-wave, 40 URLs"

**Wave shape:** the orchestrator has `_meta/discovered-sources.md`
with 40 rows (URL, surfaced-by, capture-date). One codex job per
URL; output is one row appended to a shared `_cross/sources/01-distilled.md`
*OR* (better, for skip-existing) one `_meta/source-rows/<slug>.md`
file per URL.

**Effort: `low`.**

Why: 40 jobs × medium would be ~6× more expensive than 40 jobs ×
low, and the answer shape is constrained (a row in a table). 

### Example 4 — "Wave 1 entity-slate design from a 80-candidate pool"

**Wave shape:** the candidate pool has 80 names from initial
discovery. The orchestrator needs a tiered list of `core` /
`secondary` / `discovered-only` plus 1-line rationale per row.
Codex must reason about category boundaries, identify duplicates,
tier by evidence quality, surface adjacencies.

**Effort: `high`.**

Why: tiering across 80 candidates is structurally a synthesis task,
not extraction. The orchestrator does not know the right tiers up
front; codex has to derive them.

## The effort plan — record it at Phase 0

Write the effort plan into `_meta/01-charter.md` or a sibling
`_meta/effort-plan.md`. Show it to the user before any wave dispatches.
Example:

```markdown
## Effort plan

| Wave | Job count | Effort | Justification |
|---|---|---|---|
| 1 (discovery + axes) | 2 | high | Synthesis-shaped: tiered slate from noisy pool; axis catalog derivation |
| 2 (per-entity packs) | 14 | medium | Canonical per-entity research; 1 override to high for [decisive-vendor] |
| 2 override | 1 | high | [decisive-vendor] is the decision-critical pick |
| 3 (per-axis cross) | 8 | high | Cross-entity comparison; ranking + scenarios |
| 4 (profile pages) | 14 | medium | Narrative synthesis of already-built packs |

Approximate cost ratio: 4×(2 high) + 14×(1 medium) + 8×(3 high) + 14×(1 medium)
                     = 8 + 14 + 24 + 14 = 60 effort-units
(vs. all-medium baseline: 38 effort-units; vs. all-high upper bound: 114 effort-units)
```

Recording the plan up front turns effort into a budget conversation
the user can sign off on, not a per-job decision Claude makes
silently.

## Effort upgrade / downgrade triggers

After a wave's audit, the orchestrator may revise the effort plan for
the next wave:

- **Upgrade to `high` next wave** when this wave's outputs reveal
  decision-flipping uncertainty (vendor claims contradicted by Reddit;
  pricing scenarios where the user's specific use case is unclear).
- **Downgrade to `low`** when this wave's outputs show the next wave is
  more extraction than synthesis (e.g., Wave 3 turns out to be a binary
  feature matrix, not a ranking).
- **Insert a `low` sub-wave between Wave 2 and Wave 3** when source
  ledgers need normalization before the cross-axis wave can compare
  cleanly.

Never silently change effort mid-wave. Always update the recorded plan
in `_meta/effort-plan.md` and surface the change.

## Edge cases

- **Mixed-effort wave (don't, usually).** If a wave has 14 entities at
  `medium` plus 1 promoted entity at `high`, treat the promoted job as
  a side dispatch with its own per-job-override record in the plan, not
  a redefinition of the wave's effort.
- **`low` for a wave with web research.** Rare and risky — `low` codex
  jobs sometimes skip multi-round research altogether. Use only when the
  prompt prescribes exactly which URL to read and the answer shape is
  one row.
- **`high` everywhere as a safety default.** Burns 2-3× budget for
  marginal gains. The effort plan exists precisely to avoid this.
