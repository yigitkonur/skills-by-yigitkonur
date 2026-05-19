---
name: run-research-and-save-files
description: Use skill if you are running research on 5+ entities or a market/category and need a multi-file evidence corpus persisted to a navigable folder tree.
---

# Run Research And Save Files

This skill produces a **multi-file evidence corpus on disk**, never a single chat reply.
Per-entity evidence packs, cross-axis comparison rollups, source ledgers, optional
profile pages, and a master summary — all written into a navigable folder tree the
user can read, edit, link from, and re-enter later. The filesystem is the deliverable.

The orchestrator does not search the web personally. The orchestrator decomposes,
architects the folder tree, dispatches research subagents in waves, gates between
waves, and synthesizes the final master summary. Subagents do the actual web
research, each invoking the `run-research` skill for its discipline (5-tool
research surface, `## Not found` harvesting, citation rules, parallel scope
dispatch). The filesystem is the only context channel between waves — subagents
do not see each other's outputs except through files the orchestrator names in
the next brief.

## When to use this skill

Trigger on any of these phrasings:

- *"research / compare / evaluate 5+ tools / vendors / projects / frameworks"*
- *"market analysis of [category] / competitive landscape / category map / competitor research"*
- *"build a research corpus / evidence pack / decision corpus on [category]"*
- *"deep research on [SaaS / OSS / dev-infra / data-API / regulated category]"* with per-vendor pages
- *"give me pricing + capability + integration + security + audience matrices across [vendors]"*
- *"navigable folder of product pages, comparison rollups, source ledgers, and profile pages"*
- *"every numeric / versioned / priced claim must cite a verbatim source quote"*
- *"the deliverable is a folder tree the team can navigate"*, not a chat reply
- *"audit / shortlist [population]"* against a fixed axis catalog (cost, performance, fit, risk, longevity)
- The user names 5+ vendors / projects upfront and asks for a structured side-by-side

Do NOT use when:

| Situation | Use instead |
|---|---|
| One technical question, single answer | `run-research` |
| 1-4 entities, one polished single-page summary, no folder structure | `run-research` |
| Finding or shortlisting GitHub repos as the deliverable | `run-github-scout` |
| One codex template fanned out across N inputs (single-cli-fanout job) | `run-codex-2` batch mode |
| The user wants the same shape but delegated to `codex exec` for the web research | `run-research-and-save-files-by-codex` |
| Codebase analysis, code review, or implementation work | not this skill |
| Polished single deliverable (HTML battlecard, slide deck) | downstream skills polish |

The fence: `run-research` answers **one question** and returns **one synthesis**;
this skill answers **N questions across N entities** and returns a **multi-file
corpus**. If the deliverable is a folder, you are in this skill. If it's a chat
reply or a single Markdown file, you are in `run-research`.

## The orchestrator's mental model

Every deep-research question reduces to one shape: **a population of entities,
evaluated across a set of axes, producing per-entity evidence packs + per-axis
cross-entity comparisons + a master decision artifact.** Strip away the domain
and that shape remains.

The four invariants in every session:

- **A finite set of entities.** The unit researched one folder per (products,
  candidates, projects, providers, papers, plans). The orchestrator's first job
  is to enumerate and tier them.
- **A finite set of evaluation axes.** Dimensions the decider weighs (cost,
  performance, fit, risk, longevity, compliance). Each has a native primitive
  (currency-per-period, milliseconds, score). Without native primitives,
  comparison is incoherent.
- **A decider with a use case.** Without this, "good" and "bad" are undefined.
- **A decision artifact.** Without this, the research has no closing condition.

The orchestrator's four jobs in order:

1. **Decompose** — what are the entities, what are the axes? See `references/thinking.md`. Without rigorous decomposition, no amount of evidence saves the corpus.
2. **Structure** — design the folder tree, file-naming scheme, MAX-N ceilings before any subagent dispatches. See `references/filesystem.md`.
3. **Dispatch** — write briefs that bind subagents to their specific scope, the run-research skill's discipline, and the exact file paths they own. See `references/subagent-briefs.md`.
4. **Synthesize** — read every output file personally; resolve contradictions; write the master summary. See `references/synthesis.md`.

## Filesystem as context channel

This is the load-bearing principle of every wave-based orchestrated session.

- Each subagent receives **only the files the orchestrator names in its brief**.
- Each subagent writes **only to the folder the orchestrator assigned**.
- The orchestrator reads outputs **after each wave** and decides what the next wave reads.
- No subagent sees another's working notes, search history, or mid-stream outputs — only the persisted files the orchestrator chooses to share.

This is what makes the wave model scale. With more than two or three subagents
in conversation, in-memory context collapses. With files, the wave model
composes cleanly to dozens of entities and multiple sub-waves. Treat
`<corpus-root>/` as the shared blackboard; treat each subagent's prompt as a
narrow read-write contract against that blackboard.

Operational consequences:

- Briefs name **input paths** (what the subagent reads) and **output paths**
  (what the subagent writes), explicitly and exhaustively.
- Write scopes between sibling subagents in the same wave are **disjoint** — no
  two agents own the same folder.
- Between waves, the orchestrator **reads every file produced**. This is not
  delegable.
- If a subagent needs evidence from another subagent's output, that evidence is
  passed through a file the orchestrator surfaces in the next wave's brief —
  never through "ask the other agent."

## Two framings, same skeleton

The methodology is domain-agnostic. The output structure has two named
defaults — pick once at Phase 0 and stay consistent. Both produce the same kind
of multi-file evidence corpus; the difference is vocabulary and which reference
files are loaded.

| Framing | Trigger | Default output flavor | Load first |
|---|---|---|---|
| **Domain-agnostic corpus** | *"compare / research / evaluate N entities"* in any domain (OSS projects, models, hardware, papers, candidates, locations, regulations, frameworks) | `_cross/<axis>/` rollups; `_meta/04-product-template.md` + `_meta/05-axis-templates.md` | `references/thinking.md`, `references/filesystem.md`, `references/orchestration.md`, `references/templates.md` |
| **Industry / vendor category** | *"market analysis / competitive landscape / category map / competitor research / vendor evaluation"* | `_cross-<scope>/` rollups; `_meta/_PRODUCT_TEMPLATE.md` + `_meta/_COMPARISON_TEMPLATE_<criterion>.md` per criterion; profile pages by default | `references/industry/category-taxonomies.md`, `references/industry/template-authoring.md` (keystone), `references/industry/industry-architecture.md`, `references/industry/discovery.md`, `references/industry/evidence-and-synthesis.md`, `references/industry/mission-briefs.md`, `references/industry/profile-pages.md`, `references/industry/research-powerpack-and-explore.md`, `references/industry/worked-example-cloud-browsers.md` |

If the user's framing is ambiguous (e.g., "research 8 LLM providers" — both
fits), ask one clarifying question about whether the deliverable is a vendor /
buyer corpus or a more academic decision artifact, then pick a framing and do
not switch mid-session. Switching framings mid-run forces a corpus rewrite.

## Pinned defaults

| Key | Default |
|---|---|
| Trigger threshold | 5+ entities, multi-axis evaluation, folder-tree output |
| Default scale | `compact` 5-10 entities, ~80-200 files; `standard` 10-40 entities, ~150-500 files; `deep` 40-100 entities, ~500-2000 files; `tiered` 100+ entities, full packs for top tier only |
| Hard wave cap | 8 subagents per wave for domain-agnostic framing; 20 per wave for industry framing |
| Recommended wave size | 6-8 agents when integration quality or context pressure matters |
| Subagent retry policy | 2 retries max per failed subagent, with a narrower prompt each time |
| Profile pages | Default yes for `core` tier at `standard` scale or larger (industry framing); optional for domain-agnostic |
| File count policy | Bounded by template-section-count × entity-count + cross-axis files. No fixed numeric cap; templates are the boundary. |
| Source ledger policy | Per-entity ledgers in `<entity-slug>/09-sources/` (or `09-sources.md` for compact corpora); cross-corpus ledgers in `_cross-<scope>/09-sources/` |

## Phase model

Eight phases, each with an artifact gate. Skip a phase only when its artifact
is not needed for the user's stated outcome — and state the reason.

| Phase | Goal | Artifact gate |
|---|---|---|
| **0 — Charter** | Clarify decider, scale, archetype; pick framing | `_meta/01-charter.md` scope statement + corpus scale + framing label |
| **Wave 1 — Discovery + Scope** | Enumerate entities AND derive axis catalog (parallel, 2 subagents in domain-agnostic framing; web-capable research agents in industry framing). Includes the **deep category pre-pass** (industry) — buyer axes, native pricing units, practitioner channels, regulatory regimes. | `_meta/02-entities.md` (or `discovered-entities.md`) + `_meta/03-axes.md` + category-understanding note |
| **2 — Template authoring** | Write maximalist `_meta/04-product-template.md` + `_meta/05-axis-templates.md` (domain-agnostic) OR `_meta/_PRODUCT_TEMPLATE.md` + per-criterion `_meta/_COMPARISON_TEMPLATE_<criterion>.md` (industry). Templates set the comprehensiveness boundary. | Templates locked AND shown to the user |
| **3 — Architecture** | Plan tree shape, MAX-N caps, entity tiers, file-count expectation derived from templates. Optionally scaffold via `scripts/init-corpus.sh`. | `_meta/06-file-budget.md` / `_meta/file-budget.md` |
| **Wave 2 — Per-entity packs** | Fill `<entity-slug>/` for every `core` entity (parallel, ≤8 per sub-wave domain-agnostic; ≤20 per sub-wave industry). Each subagent owns one folder; write scopes disjoint. Each invokes run-research. | Populated `<entity-slug>/` folders; every template section addressed (content OR explicit "insufficient evidence" entry naming the data gap) |
| **Wave 3 — Per-axis cross synthesis** | Compare entities along each axis. LOCAL-ONLY (no web tools). Each agent owns one cross folder. | Populated `_cross/<axis-slug>/` or `_cross-<scope>/` folders with ranking + matrix + decision-flippers |
| **Wave 4 (optional) — Profile pages OR promoted research** | Standalone `<entity-slug>.md` decision pages at corpus root (LOCAL-ONLY) OR additional research packs for promoted entities (web-capable, invokes run-research) | Profile pages OR new entity packs |
| **7 — Verification + Master summary** | Orchestrator personally reads every file. Resolves contradictions. Writes `_meta/00-master-summary.md`. Runs verification gate. | `_meta/00-master-summary.md` + verification log; template-coverage audit passes |

Wave 1, Wave 2, optional Wave 4-promoted dispatch **research-doing** subagents
that invoke run-research. Wave 3 and profile-page Wave 4 are **LOCAL-ONLY**
synthesis — read files, no web tools.

Phases 0, 2, 3, 7 are **orchestrator-personal** — no subagents.

Full wave choreography, brief structure, between-wave gates: `references/orchestration.md`.

## Tool steering at a glance

The orchestrator chooses the tool category for each use case in the brief; the
subagent executes via its run-research session.

| Use case | Wave | Tool dispatch |
|---|---|---|
| Find entities | 1A / Discovery | Parallel `raw-web-search` (web + reddit) → optional `raw-scrape-links` on category indexes |
| Map axes / deep category pre-pass | 1B / Discovery | `smart-web-search` with extract = "decision axes / native pricing units / practitioner channels" → `smart-scrape-links` on 2-3 authoritative analyses |
| Per-entity overview | 2 | `start-research` per entity → parallel `smart-web-search` (web + reddit) → `smart-scrape-links` on docs + `raw-scrape-links` on Reddit |
| Per-entity sentiment | 2 | `raw-scrape-links` on Reddit thread permalinks (preserves voting + threading) |
| Cross-entity synthesis | 3 | LOCAL-ONLY: read files, no web tools |
| Profile pages | 4 / orch | LOCAL-ONLY: read pack, write profile |
| Master summary | 7 | LOCAL-ONLY: orchestrator reads everything, writes |

For tool API, fallback chains, and operational thresholds (URL counts, facet
counts, parallel calls), the subagent's brief points to the run-research skill's
own tool reference. For industry-framing graceful degradation (Powerpack →
WebSearch → curl chain), see `references/industry/research-powerpack-and-explore.md`.

## Output architecture contract

Domain-agnostic framing default tree:

```
<corpus-root>/
├── README.md                                       (entry point)
├── _meta/                                           (MAX 8 files)
│   ├── 00-master-summary.md                        (Phase 7)
│   ├── 01-charter.md                               (Phase 0; Wave 1 resolves)
│   ├── 02-entities.md                              (Wave 1A output)
│   ├── 03-axes.md                                  (Wave 1B output)
│   ├── 04-product-template.md                      (Phase 2)
│   ├── 05-axis-templates.md                        (Phase 2)
│   ├── 06-file-budget.md                           (Phase 3)
│   └── 07-dispatch-log.md                          (running log)
├── <entity-slug>/                                   (one per core; MAX 15 files)
│   ├── 00-overview.md
│   ├── 01-<axis-1>.md ... 0N-<axis-N>.md
│   └── 09-sources.md
├── <entity-slug>.md                                 (optional profile at root)
└── _cross/
    └── <axis-slug>/                                (MAX 12 files)
        ├── 00-overall-comparison.md
        └── 01-<scenario>.md ...
```

Industry framing default tree:

```
<topic-slug>/
├── README.md
├── _meta/
│   ├── research-plan.md
│   ├── _PRODUCT_TEMPLATE.md                        (Phase 2 maximalist template)
│   ├── _COMPARISON_TEMPLATE_<criterion>.md         (Phase 2 per-criterion)
│   ├── methodology-and-source-policy.md
│   ├── discovered-entities.md
│   └── file-budget.md
├── _cross-<scope>/
│   ├── 00-overview/
│   ├── <criterion-a>/
│   ├── <criterion-b>/
│   └── 09-sources/
├── <entity-slug>/
│   ├── 00-overview/
│   ├── <vertical-context-1>/
│   ├── <vertical-context-2>/
│   └── 09-sources/
└── <entity-slug>.md                                 (profile page; Phase 6)
```

Concrete folder + file naming rules, MAX-N ceilings, numbered-prefix scheme,
and the agent-chosen-filename rule: `references/filesystem.md`. Vertical-specific
category names (SaaS, OSS, dev-infra, data/API, regulated, consumer):
`references/industry/category-taxonomies.md`.

Numeric prefixes are scan order, not semantic naming. Filenames within each
numbered subfolder are agent-chosen based on the evidence found for that
specific entity. Two researcher subagents may legitimately land different
filenames in the same numbered subfolder — that is correct.

## Hard rules (load-bearing)

These break the corpus when ignored. Keep them at the top of mind.

1. **The orchestrator does not search.** Searching is the subagents' job, via
   the `run-research` skill embedded in their brief.
2. **The orchestrator does not delegate synthesis.** Read every entity pack and
   every cross file personally before the master summary.
3. **Templates first, files second.** Phase 2 (template authoring) MUST
   complete before any entity-pack or cross-comparison file is written.
   Skipping templates is a hard failure — depth varies per agent and
   comparability is lost.
4. **Maximalist templates, not generic skeletons.** A thin `_PRODUCT_TEMPLATE.md`
   (≤15 sections) means Phase 1's deep category pre-pass was skipped. Re-do it.
   Target ~30+ vertical-specific sections.
5. **MAX 8 subagents per wave (domain-agnostic) / MAX 20 per wave (industry).**
   Beyond the cap, run sequential sub-waves. Coordination overhead exceeds
   parallelism savings above the cap.
6. **Disjoint write scopes.** Each subagent owns exactly one folder. No two
   subagents in the same wave write to the same path.
7. **Every research-doing brief invokes run-research.** Embed the
   run-research integration block in the brief verbatim — see
   `references/subagent-briefs.md`.
8. **Every numeric / versioned / priced claim cites a verbatim quote.** Snippet
   citations are forbidden.
9. **No placeholder / stub files.** A template section with no evidence becomes
   a one-paragraph "insufficient evidence" entry inside an existing file in the
   same subfolder, naming the specific data gap. **Never** a stub file.
10. **Folder names are vertical-specific, filenames are agent-chosen.** The
    orchestrator chooses subfolder names per category (Phase 2). Subagents
    pick the `01-meaningful-title.md` filenames inside those folders based on
    the evidence they surface.
11. **Separate confirmed facts, vendor/project claims, practitioner evidence,
    and inference.** Never treat snippets as evidence. Never present Reddit as
    "consensus" without per-comment attribution.
12. **Two-level orchestration only.** Subagents do not create their own
    subagents.
13. **No single-report output.** This skill produces a multi-file corpus. If
    the user wants a single report, redirect to `run-research`.
14. **MAX-N caps are ceilings, not targets.** 15 per entity / 12 per
    cross-axis / 8 per meta. Below ceiling is normal; sparse evidence is
    acceptable. See `references/filesystem.md`.

If any rule is violated, the rest of this skill stops applying — stop, recover,
and resume only after the violation is corrected.

## Self-correction triggers

If you notice yourself doing any of the following — **stop**:

- **Skipping Phase 2 templates** and dispatching Wave 2 directly → STOP. Templates are the comprehensiveness contract.
- **Writing a thin or generic product template** (≤15 sections) → STOP. Re-do Phase 1's deep category pre-pass; re-author with ~30+ distinct sections. See `references/industry/template-authoring.md`.
- **Hardcoding filenames in the template** → STOP. Templates list sections + questions; agents pick filenames per their evidence.
- **Letting subagents silently skip a template section** → STOP. Every section gets content OR an explicit one-paragraph "insufficient evidence" entry naming the gap.
- **Dispatching more than the cap** (8 domain-agnostic / 20 industry) **in one wave** → STOP. Coordination overhead exceeds parallelism savings. Split into sub-waves. See `references/orchestration.md`.
- **Summarizing Reddit as "consensus"** without per-comment attribution → STOP. Apply the audience-evidence fields from `references/synthesis.md` / `references/industry/evidence-and-synthesis.md`.
- **Treating a vendor's marketing page as confirmed fact** → STOP. Re-classify per source hierarchy; vendor claims belong in the vendor-claim ledger row.
- **Searching the web yourself as the orchestrator** → STOP. Dispatch a subagent. Searching is the subagent's job, via run-research.
- **Delegating synthesis** → STOP. Read every core pack and every cross folder personally before writing the master summary.
- **Producing a single-report output** ("here's the markdown report") → STOP. This skill produces a multi-file corpus. If the user wants a single report, redirect to `run-research`.
- **Skipping the completion gate** ("looks done") → STOP. Run the verification commands in `references/verification.md`. Template-coverage audit, link check, source-ledger presence are non-negotiable.
- **Subagent stalled, timed out, or returned shallow output** → STOP improvising. Apply the recovery procedures in `references/failure-modes.md`.

## Anti-patterns

| Anti-pattern | Why it fails | Fix |
|---|---|---|
| Templates skipped or written after entity research | No comprehensiveness boundary; depth varies by agent | Phase 2 first, Wave 2 second. Always. |
| Template is thin or generic (≤15 sections) | Misses decider-weighted axes; produces shallow corpus | Re-do the deep category pre-pass; re-author maximalist template (~30+ sections) |
| Template prescribes exact filenames | Removes evidence-driven naming; agents pad to fit | Templates list sections + questions; agents pick filenames |
| Stub files for sections with no evidence | Pollution; no actual content | "Insufficient evidence" entry inside an existing file naming the data gap |
| Identical empty subfolders for every entity | Copy-paste research, no value | Create only evidence-justified files; address every template section |
| Cross-axis file is concatenation of per-entity summaries | Doesn't compare; just appends | Comparison template prescribes axes, ranking, scenarios; agents follow |
| Pricing copied from page without unit economics | Vendors hide overages, gating, scenario costs | Preserve native units, model scenarios, name missing variables explicitly |
| Reddit evidence presented as "consensus" | Bias and small samples are erased | Preserve thread, username, date, quote, bias label |
| Source verification skipped because "it's clearly true" | Stale facts, contradicted vendor claims | Source ledger non-optional for `core` entities |
| Profile page duplicates evidence-pack content | Duplication; no synthesis added | Profile = readable narrative + links into pack; pack = atomic evidence files |
| Single-output thinking ("write me a report") | Loses navigability and source-traceability | Multi-file corpus is the contract; route to run-research if user wants single report |
| Orchestrator searches the web | Defeats wave model; pollutes orchestrator context | Orchestrator architects, dispatches, gates, synthesizes. Subagents search via run-research |
| Orchestrator delegates synthesis | Master summary becomes stitched per-agent paragraphs | Orchestrator personally reads every core pack and every cross folder before master summary |

## Output contract

Show these artifacts at the phase that produces them. Never batch all artifacts
to the end.

1. **Phase 0** — scope statement + corpus scale + framing (domain-agnostic / industry).
2. **Wave 1** — discovered entities table (tier + source URL + 1-line rationale) AND axis catalog AND category-understanding note (industry framing).
3. **Phase 2** — resolved category list AND the maximalist product template AND each cross-axis / cross-criterion template. Show inline (or summarized with link) — they are the comprehensiveness contract for the rest of the work.
4. **Phase 3** — file-count expectation derived from templates + tree shape.
5. **Wave 2** — agent dispatch map (which agent owns which entity), then evidence-pack progress notes as agents complete.
6. **Wave 3** — cross-axis / cross-criterion ranking summary.
7. **Wave 4** (optional) — profile-page index.
8. **Phase 7** — completion statement (path, files, entry points, gaps, verification, template coverage).

## Reference routing

Load only the reference whose phase is active. Loading all references at once
exhausts context.

| Reference | Read when |
|---|---|
| `references/thinking.md` | Phase 0, every session — the decomposition protocol; what counts as an entity vs axis vs primitive |
| `references/templates.md` | Phase 0, 2, 3 — concrete formats for charter, product template, axis templates, file budget; tier-promotion mechanics (domain-agnostic framing) |
| `references/orchestration.md` | Wave 1, 2, 3 — wave choreography, parallel-dispatch rules, tool steering, between-wave gate procedure |
| `references/filesystem.md` | Phase 3 — directory contract, MAX-N caps, file naming, context-sharing through files |
| `references/subagent-briefs.md` | Wave 1, 2, 3, 4 — copy-paste-ready brief templates with the run-research integration block |
| `references/synthesis.md` | Phase 7 — claims ledger discipline, profile-page template, master-summary structure, personal-read gate procedure |
| `references/verification.md` | Phase 7 — completion-gate commands and template-coverage audit |
| `references/failure-modes.md` | Any wave — recovery procedures for subagent timeouts, shallow output, MAX-N overflow, contradictions |
| `references/industry/industry-architecture.md` | Phase 3 (industry framing) — 4-layer industry tree, file-count derivation from templates, entity tiering, validation gates |
| `references/industry/category-taxonomies.md` | Phase 2 (industry framing) — archetype skeletons (SaaS, OSS, dev-infra, data/API, regulated, consumer) before adapting to the vertical |
| `references/industry/template-authoring.md` | **Keystone reference** (industry framing). Phase 2 — writing the maximalist `_PRODUCT_TEMPLATE.md` and per-criterion `_COMPARISON_TEMPLATE_<criterion>.md` files |
| `references/industry/profile-pages.md` | Wave 4 / Phase 6 (industry framing) — writing standalone `<entity>.md` decision pages |
| `references/industry/discovery.md` | Wave 1 (industry framing) — sub-question decomposition, tiering, deep category pre-pass |
| `references/industry/evidence-and-synthesis.md` | Wave 2-3 (industry framing) — source hierarchy, source-map and claims-ledger schemas, Reddit/practitioner rules, pricing/unit-economics standards, cross-category structure |
| `references/industry/worked-example-cloud-browsers.md` | Any phase (industry framing) — annotated walkthrough of the cloud-browsers corpus including actual template artifacts. Mirror its *discipline*; do not copy slugs. |
| `references/industry/mission-briefs.md` | Wave 1, 2, 3, 4 (industry framing) — prompts for discovery, entity-pack, cross-comparison, audience, source-verification, profile-writer agents |
| `references/industry/research-powerpack-and-explore.md` | Wave 1, 2, 3 (industry framing) — portable Research Power Pack API shapes (`start-research`, smart/raw search and scrape) plus web-capable research agent and local-corpus Explore patterns (≤20 per wave) |
| `scripts/init-corpus.sh` + `scripts/init-corpus.md` | Phase 0 or 3 — deterministic corpus scaffolding; root/meta starter files only, never entity evidence placeholders |

## Quick start

The first five minutes of any session:

1. **Phase 0** — ask up to 3 clarifying questions (decider / use case / scale / framing). Write `_meta/01-charter.md` initial draft. Read `references/thinking.md` and `references/templates.md` (or `references/industry/discovery.md` + `references/industry/template-authoring.md` for industry framing) for the charter format. State the framing choice explicitly.
2. **Wave 1** — dispatch parallel discovery + scope subagents in one tool message. Both invoke run-research. Use brief templates in `references/subagent-briefs.md` (domain-agnostic) or `references/industry/mission-briefs.md` (industry). Wait for both. Read every output personally.
3. **Phase 2/3** — read Wave 1 outputs; write templates per `references/templates.md` or `references/industry/template-authoring.md` (industry, keystone); plan architecture per `references/filesystem.md` or `references/industry/industry-architecture.md`. Optionally scaffold with `scripts/init-corpus.sh <topic-slug>` (see `scripts/init-corpus.md`). Show the architecture to the user before Wave 2.

After that, the loop is: Wave 2 (per-entity, possibly multiple sub-waves) →
Wave 3 (per-axis cross) → optional Wave 4 → Phase 7 verification + master
summary. Wave choreography lives in `references/orchestration.md`; the Phase 7
gate procedure lives in `references/verification.md` and `references/synthesis.md`.

If anything is unclear, the question is almost always upstream: read
`references/thinking.md` and clarify the decomposition before dispatching more
agents.

## Guardrails

- Do not make landing-page-style reports. Build the actual research corpus.
- Do not collapse product facts, pricing, practitioner sentiment, and source verification into one undifferentiated file.
- Do not create raw dump folders unless the user explicitly asks. Summarize and source-map instead.
- Do not use the same category names for every vertical when better names are available.
- Do not outsource final synthesis. The orchestrator reads the files and resolves contradictions personally.
- Do not exceed the per-wave cap. Run multiple waves instead.
- Do not let agents create subagents. Two-level orchestration only.
- Do not start Wave 2 entity research before Phase 2 templates are written and shown to the user.
- Do not declare completion without running the Phase 7 verification, including the template-coverage audit.

## Bottom line

Decompose into entities × axes → architect the folder tree → dispatch
research subagents in waves through filesystem-bound briefs → between waves,
read everything personally → write the master summary → run the verification
gate. The filesystem is the deliverable, the context channel, and the audit
trail in one. If the deliverable is anything other than a folder of source-backed
evidence files, this is the wrong skill.
