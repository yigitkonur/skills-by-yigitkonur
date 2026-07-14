# Thinking Filesystem-First

This file teaches how to think about any deep-research question
filesystem-first: decompose into entities × axes, design the folder
tree, identify native primitives, classify tiers, set MAX-N ceilings.
Domain-independent. The agent figures out the domain specifics from
first principles.

Read this in **Phase 0**, every session. Without rigorous
decomposition, the corpus structure will be wrong and no amount of
evidence will save it.

## The universal shape

Strip away domain. What remains in every deep-research session:

- **A finite set of entities.** They might be products, candidates,
  repositories, locations, services, providers, plans, processes,
  papers, organizations. The unit you research one folder per. The
  orchestrator's first task is to enumerate them.
- **A finite set of evaluation axes.** Dimensions the decider weighs.
  Cost, performance, reliability, fit, risk, longevity, reputation,
  compliance — the specific axes are domain-dependent, but the
  *existence of an axis catalog* is universal.
- **Native primitives per axis.** Cost has units (currency per period,
  per call, per square unit). Performance has units (milliseconds,
  throughput, score). Durability has units (years, MTBF). Without
  native primitives, comparison is incoherent.
- **A buyer or decider with a use case.** Without this, "good" and
  "bad" cannot be defined. Two deciders evaluating the same entities
  for different use cases produce different rankings.
- **A decision or output artifact.** Without this, the research has
  no closing condition.

If any of these five is unclear before researching, **stop and
clarify**. Researching with an unclear entity-set or axis-set produces
a corpus that cannot be merged or compared.

## The decomposition protocol — 7 questions before any folder exists

Before designing any folder structure, answer these in writing in
`_meta/01-charter.md`:

1. **Who is the decider?** Their role, their constraint, what they
   will do with this corpus. Specific, not generic. "Engineering
   manager picking infrastructure for a 30-person team with a 2026
   budget of $X" beats "someone choosing a tool".

2. **What is an entity in this session?** The unit researched one
   folder per. Two entities are separate if the decider would compare
   them head-to-head; they are the same entity if the decider treats
   them as variants of one option.

3. **What axes does the decider compare on?** Not features — *axes
   the decider weighs*. If the decider does not compare on an axis,
   do not include it. Marketing pages list features the vendor wants
   you to notice; the decider weighs a smaller, sharper set.

4. **What native primitive describes each axis?** Without this,
   comparison is incoherent. Cost has currency-per-period or
   cost-per-unit-of-work. Speed has time-units or throughput-units.
   Quality has scoring-units. Identify primitives per axis BEFORE
   researching any specific entity.

5. **What does the decider's lock-in / exit / mistake-recovery look
   like?** This shapes which axes are "decision-flipping" vs
   "nice-to-know". A reversible monthly subscription tolerates a
   wider recommendation than a one-shot non-refundable commitment.

6. **What practitioner channels exist for this domain?** Where do
   people who actually use these entities discuss them honestly?
   Specific subreddits, HN threads, professional forums, review
   aggregators, trade publications. Without naming these, audience
   evidence will be thin and biased.

7. **What recent shifts has this domain seen?** Last 12 months.
   Before researching specific entities, calibrate the freshness
   window. Old evidence in fast-moving domains is often net-negative.

The output of this protocol is a *decision matrix* — entities × axes
— written to `_meta/01-charter.md`. The folder tree IS this matrix.

## What is an "entity"?

An entity is the unit that gets one folder. First-principles tests:

- **The head-to-head test.** If the decider would compare two of them
  head-to-head, they are separate entities.
- **The exclusion test.** If choosing one means not choosing the
  other, they are separate entities.
- **The variant test.** If two offerings are variants the decider
  treats as one option (e.g., "the basic plan and the pro plan of
  the same provider" when the decider would just pick the right
  plan), they are one entity, with the variants captured as
  axis-level evidence.

Adjacencies are not entities. If a candidate solves the same problem
with a fundamentally different approach the decider rejects upfront,
it is not an entity in this corpus — it is an out-of-scope row in
`_meta/02-entities.md`.

When the orchestrator is unsure: include the candidate as `secondary`
and let Wave 2 evidence decide. Promoting a `secondary` to `core`
mid-session is normal; downgrading a `core` is rare but allowed.

## What is an "axis"?

An axis is a dimension along which the decider compares entities.
First-principles tests:

- **The decision-weight test.** Does the decider weigh this when
  comparing entities? If not, it is not an axis.
- **The native-primitive test.** Does this dimension have a unit of
  measurement? Without one, the axis is a feature category, not an
  axis.
- **The differentiation test.** Do entities differ measurably along
  this axis? If every entity scores identical, the axis is not
  decision-relevant for this corpus.

Common axis types (vocabulary, not domain-specific examples):

- Cost (native primitive: currency per unit of consumption)
- Performance (native primitive depends on workload: latency,
  throughput, score)
- Reliability (uptime, MTBF, incident rate)
- Compliance / risk (binary or graded against named regimes)
- Fit (match between decider's specific need and entity's capability)
- Sustainability / longevity (organizational health, change of
  ownership, deprecation signal)
- Audience evidence (what practitioners say, with vote-weighted
  attribution)
- Lock-in / reversibility (cost of switching away)

The orchestrator picks the axis catalog FROM THE 7 DECOMPOSITION
QUESTIONS, not from a pre-baked archetype. Different domains produce
different axis catalogs.

## Axis dependency — when one axis derives from another

Some axes are not independent. They derive from other axes plus
context. Examples (vocabulary, not domain-specific):

- **Total cost of ownership** derives from headline cost + hidden
  cost dimensions (overages, integrations, switching, support).
- **Effective performance** derives from raw performance + fit-for-
  workload (a fast option is slow if it does not match the
  workload).
- **Practical reliability** derives from claimed reliability + lived
  experience + recovery characteristics.

When an axis derives from others, capture both:

- The component axes (each in its own folder under `_cross/`)
- The derived axis (its own folder under `_cross/` too, with a
  `00-overall-comparison.md` that explicitly composes from the
  components)

Wave 3 synthesis subagents read both component and derived axes
when their assigned axis is one of these. The orchestrator's master
summary explicitly names which axes are derived and what they
derive from.

## The native-primitive question

Every axis has primitives. Without them, comparison is incoherent.

When researching cost, the question is not "what does it cost" — it
is "what is the native unit of cost in this domain". Currency per
month is one primitive; cost per unit of consumption is another;
cost per seat is another. Each domain has 1-3 native primitives that
the decider mentally normalizes against.

When researching performance, the question is not "is it fast" — it
is "what workload + which metric matters here". Throughput-bound
domains use different primitives from latency-bound ones.

When researching quality, the question is not "is it good" — it is
"what credible scoring exists, and against what reference". Awards,
ratings, benchmarks, certifications, peer-review citations: each
domain has its own quality primitives.

The orchestrator's Phase 2 templates list, per axis, the *expected
primitive*. The Wave 2 brief tells the researcher to capture the
primitive value verbatim per entity. Without this, Wave 3 cross
synthesis becomes incoherent.

## Tier classification

Three tiers per `_meta/02-entities.md`:

- **`core`** — directly comparable, decider would seriously consider,
  source-rich. Output: full evidence pack (`<entity-slug>/`) plus
  standalone profile page (`<entity-slug>.md` at root).
- **`secondary`** — adjacent or source-limited or early-stage.
  Output: compact profile or a subset of axes only. May be promoted
  to `core` if Wave 2 evidence reveals decision-flipping signal.
- **`discovered-only`** — surfaced in Wave 1 but not worth deep
  treatment. Output: single row in `_meta/02-entities.md`.

**Promotion rule**: a `secondary` entity that turns out to change
the ranking, the cost economics, the adoption interpretation, or the
category boundaries during Wave 2/3 should be promoted to `core`.
Add a Wave 4 mission for it.

**Demotion rule**: rare. A `core` entity revealed to be dead, sold,
or out-of-category during Wave 2 can drop to `discovered-only` with
a note in `_meta/02-entities.md`.

## The folder-first principle — and why

Design the folder tree before any researcher dispatches. There are
three reasons this matters:

**Reason 1 — context channel.** Subagents do not see the
orchestrator's conversation. The filesystem is the only context
channel between waves. If the structure is wrong upstream, every
downstream agent's brief is wrong.

**Reason 2 — comprehensiveness contract.** The folder structure (one
folder per axis, one folder per entity) is the contract. A subagent
cannot silently skip an axis if every axis has a named folder waiting
for content.

**Reason 3 — readability.** Each folder name should answer "what
question does this folder answer?". Path readability is a feature,
not a bonus. A reader landing in
`_cross/cost-and-unit-economics/02-overage-modeling.md` should know
what they are about to read from the path alone.

Numbered prefixes (`<NN>-`) are for scan order, not semantic naming.
The naming pattern is `<NN>-<topic-slug>.md`. The orchestrator
decides NN; the agent decides topic-slug based on what their evidence
supports.

Two researcher subagents may legitimately land different filenames
inside the same numbered subfolder, because their evidence shapes
differ. That is correct, not a bug.

## Maximalist templates as comprehensiveness boundary

Templates are the comprehensiveness boundary; they define the
*minimum* coverage every entity pack and every cross-axis comparison
must address. Sparse evidence is acceptable; a missing section the
decider will care about is not.

Phase 2 produces two template artifacts:

- **`_meta/04-product-template.md`** — the master per-entity
  template. Lists every axis subfolder, every section, every
  question every entity pack must address. Overcrowd it deliberately.
  Target ~30+ distinct sections. Thin templates produce shallow
  corpora.

- **`_meta/05-axis-templates.md`** (or one file per axis) — per-axis
  comparison templates. Each axis prescribes its comparison axes,
  matrix columns, ranking dimensions, and source expectations.

**The template never prescribes filenames.** It lists *sections* and
*the questions each section must answer*. The agent picks the
filename based on evidence.

When a Phase 2 section's evidence is sparse, the agent's options
are:

- **Content with caveats.** Provide what evidence supports, name the
  uncertainty, link to the source.
- **One-paragraph "insufficient evidence" entry inside an existing
  file in the same subfolder.** Name the specific data gap. Do not
  create a stub file.

Skipping a section silently is a failure.

## The 7-question decomposition produces the axis catalog

The output of the 7 decomposition questions IS the axis catalog.
Each "axis the decider weighs" becomes a folder in
`_cross/<axis-slug>/` and a section in every entity pack.

If a section in `<entity-slug>/` does not correspond to an axis in
`_cross/`, something is wrong. Either:

- The section is decision-irrelevant — drop it.
- The axis was missed in Phase 1 scope-mapping — return to Wave 1B
  and re-derive the axis catalog.

Symmetric correspondence between per-entity sections and per-axis
cross folders is the property that makes Wave 3 synthesis tractable.

## The decider's mental model

Before Wave 2 dispatches, write down — for the orchestrator's own
reference, in `_meta/01-charter.md` — what the decider will actually
DO with the corpus:

- Read the master summary first; if the recommendation matches their
  prior, they may stop there.
- Open the profile page of the recommended entity; if convinced, they
  may stop there.
- Compare 2-3 finalists across the most decision-flipping axis (e.g.,
  `_cross/cost-and-unit-economics/00-overall-comparison.md`).
- Drop into specific entity packs only when a decision-flipping
  question is unresolved.

This mental model affects the corpus design:

- **Master summary length**: 2-4 pages. Decider-reads-first.
- **Profile pages**: 300-700 lines. The decider's second read.
- **Entity-pack files**: short, atomic, navigable. The decider's
  third-or-fourth read, only when a specific question needs an
  answer.
- **Cross-axis comparison files**: organized by scenario, not by
  entity. Decider compares finalists per axis.

If the decider would never read a particular file (or a particular
section), it should not exist. Producing files no one reads is the
most expensive failure mode in corpus research.

## First-principles thinking for novel domains

The skill is domain-independent because the universal shape — entities
× axes — applies anywhere. But novel domains need careful first-
principles work to identify what counts as an entity and what counts as
an axis. The pattern, applied without picking a specific domain:

**Step 1: Identify the decider's verb.** What is the decider doing?
Picking? Hiring? Buying? Visiting? Depending on? Investing in?
Subscribing to? The verb tells you what counts as an entity. (Picking
→ choices; hiring → candidates; visiting → places; depending →
providers.)

**Step 2: Enumerate options the decider would consider.** Two things
qualify as separate entities if the decider would compare them
head-to-head. Two things are one entity (with variants) if the
decider treats them as one option (and would pick the right variant
after choosing the entity).

**Step 3: Name what the decider weighs.** Not features the entity
advertises — *axes the decider weighs*. The list usually includes
some of: cost (in some unit), quality (by some metric), fit-to-need
(matching specific decider constraints), risk (failure modes the
decider must defend against), longevity (likelihood the entity will
still be available when the decider needs it), and lock-in (cost of
choosing wrong).

**Step 4: Identify native primitives.** Cost has units. Quality has
units. Risk has units (probability × impact). Without native
primitives, comparison is incoherent. If you cannot name the unit for
an axis, the axis is not yet well-defined.

**Step 5: Find the practitioner channels.** Where do people who
actually use these entities discuss them honestly? Specific
subreddits, HN threads, professional forums, review aggregators,
trade publications, GitHub issue trackers, Discord servers, mailing
lists. The channel exists for every domain that has practitioners;
the orchestrator's job is to name the specific venue.

**Step 6: Calibrate the freshness window.** Last 12 months for
fast-moving domains; longer for stable domains. The shifts the
orchestrator identifies in this step also become Wave 1A discovery
sub-questions.

**Step 7: Name the decider's reversibility.** A reversible monthly
subscription tolerates a wider recommendation than a one-shot
non-refundable commitment. This shapes which axes are
decision-flipping vs nice-to-know.

The output of this seven-step protocol is the charter. Write it
(format in `templates.md`); show it to the user; iterate before
dispatching Wave 1. The charter is the contract for the entire
session — every downstream subagent inherits its discipline.

### When the protocol reveals a domain mismatch

Sometimes the seven-step protocol reveals that the question is not
actually a corpus-research question. Signals:

- **No clear decider verb.** The user wants information, not a
  decision. → Use `run-research` for single-question research.
- **No comparison head-to-head.** The "entities" are unrelated
  topics, not options the decider chooses among. → 10 separate
  research sessions, not one corpus.
- **Single entity, deep dive.** The decider has already chosen and
  wants depth on one option. → Use `run-research` with a
  comprehensive goal.
- **Native primitives don't exist or are not researchable.** The
  axes are subjective enough that no source can settle them. →
  Either accept that the corpus will surface tradeoffs without
  ranking, or commission expert input.

If any of these is true, surface to the user. A wrong-shape session
produces a corpus the decider cannot use.

## Mistakes the orchestrator must catch before researching

Before dispatching Wave 2, audit the charter for these failure modes:

- **Entity set includes adjacencies the decider would not compare.**
  Adjacents belong in `_meta/02-entities.md` as `discovered-only`,
  not as `core`.
- **Axis set is a feature list, not a decider-weighted dimension
  list.** Vendors publish feature matrices; deciders weigh a
  different, sharper set.
- **Native primitives are missing.** Comparison will be incoherent
  if axes do not have units.
- **Lock-in is undefined.** Recommendations will lack reversibility
  framing.
- **No practitioner channel identified.** Audience evidence will be
  thin and biased.
- **Freshness window not specified.** Recent regressions will go
  unnoticed; stale evidence will dominate.
- **Decider use case is generic.** Generic charters produce generic
  corpora that do not help the actual decision.

If any of these is unfixed, do not dispatch Wave 2. Return to Wave 1
or Phase 0 to clarify.

## When the corpus shape does not fit

Sometimes the question that arrived is not a corpus-research
question. Signals:

- **N < 5 entities.** Use `run-research` for single-decision work.
- **One entity, deep dive.** Use `run-research` with a comprehensive
  goal; the corpus structure adds overhead without value.
- **The decider needs a one-page brief, not navigable evidence.**
  Use `run-research`.
- **The "entities" do not actually compete.** If you are researching
  10 unrelated topics, you have 10 sessions, not one corpus.

If the request fits one of these, decline gracefully and recommend
the alternative skill.

## When to escalate to a Wave 4

Default is 3 waves. Add Wave 4 when:

- A `secondary` entity revealed decision-flipping evidence in Wave 2
  and warrants a full pack.
- Profile pages are mandated by the user (every `core` entity gets
  one).
- A Wave 3 cross-axis synthesis surfaced a contradiction that
  requires targeted re-research.

Beyond Wave 4 is rare. Most well-charted sessions fit in 3-4 waves.
If a session balloons to Wave 5+, the upstream charter is almost
certainly wrong — return to Phase 0 instead of adding more waves.
