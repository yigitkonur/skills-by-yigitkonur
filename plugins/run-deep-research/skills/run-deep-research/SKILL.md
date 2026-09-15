---
name: run-deep-research
description: "Use if running deep multi-file research over 5+ entities or a market — wave-dispatched corpus."
---

# Run Deep Research

This skill orchestrates a **multi-file evidence corpus on disk**, never a single chat reply.
Per-entity evidence packs, cross-axis comparison rollups, source ledgers, optional
profile pages, and a master summary — all written into a navigable folder tree the
user can read, edit, link from, and re-enter later. The filesystem is the deliverable.

The orchestrator operates as the system architect, delegator, gatekeeper, and synthesizer.
The orchestrator does not search the web personally; instead, it decomposes the research
domain, structures the folder tree, dispatches focused research to **parallel background
subagents in orchestrated waves**, gates and audits between waves, and personally synthesizes
the final decision artifacts. Every research subagent inherits the `run-research` discipline
(3-tool research surface, `## Not found` harvesting, verified verbatim quotation citations,
and multi-round scope refinement).

The **filesystem is the context channel** between waves. Subagents do not see each other's
in-flight context; they read only the specific files named in their brief and write only to
their assigned directory.

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
- The user names 5+ vendors / projects upfront and asks for a structured side-by-side comparison

Do NOT use when:

| Situation | Use instead |
|---|---|
| One technical question, single answer | `run-research` |
| 1-4 entities, one polished single-page summary, no folder structure | `run-research` |
| Finding or shortlisting GitHub repos as the deliverable | `run-github-scout` |
| Codebase analysis, code review, or implementation work | not this skill |
| Polished single deliverable (HTML battlecard, slide deck) | downstream skills polish |

The fence: `run-research` answers **one question** and returns **one synthesis**;
this skill answers **N questions across N entities** and returns a **multi-file
corpus**. If the deliverable is a folder, you are in this skill. If it's a chat
reply or a single Markdown file, you are in `run-research`.

## Intake — always ask first (AskUserQuestion)

Before any decomposition, template authoring, or subagent dispatch, run **one batched
`AskUserQuestion` call** to lock the run's shape. This is mandatory — never start a
heavy pass on assumptions. Batch the discrete decisions into a single call so the user
answers once; make the recommended default the first option of each:

1. **Scale** — standard (10-40 entities, ~150-500 files) · compact (5-10 entities, ~80-200 files) · deep (40-100 entities) · tiered (100+ entities).
2. **Framing** — industry / vendor category (market analysis, pricing, profile pages) · domain-agnostic corpus (OSS projects, papers, architectures).
3. **Scope & Discovery** — discover entities vs use user's named list; confirm `<topic-slug>/` output folder and whether profile pages are wanted.
4. **Concurrency** — standard (6-8 parallel subagents per wave) · conservative (3-4 subagents) · high throughput (10-15 subagents).

Capture the **decider** and **use case** from the conversation (or free-text notes) —
these anchor `_meta/01-charter.md`; without them "good" and "bad" are undefined.
If `AskUserQuestion` is unavailable (non-interactive run), fall back to the stated
defaults and record the assumption in the charter. Full question wording, option sets,
recommended defaults, and the headless fallback: `references/intake.md`.

## The Universal Subagent Architecture

The research executes across a modular, 2-level multi-agent hierarchy:

```
                      ┌────────────────────────────────────────┐
                      │              ORCHESTRATOR              │
                      │  (Intake, Architecture, Gates, Master) │
                      └───────────────────┬────────────────────┘
                                          │
                  ┌───────────────────────┼───────────────────────┐
                  ▼                       ▼                       ▼
       ┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐
       │   WAVE 1 SUBAGENTS  │ │   WAVE 2 SUBAGENTS  │ │   WAVE 3 SUBAGENTS  │
       │ Discovery & Axes    │ │ Per-Entity Packs    │ │ Cross-Axis Rollups  │
       │ (run-research web)  │ │ (run-research web)  │ │ (local-only corpus) │
       └─────────────────────┘ └─────────────────────┘ └─────────────────────┘
```

- **Orchestrator**: Owns chartering, maximalist template authoring, file budget, wave dispatch, between-wave evaluation gating, and master summary synthesis.
- **Research Subagents (Waves 1, 2, 4-promoted)**: Autonomous background workers executing the `run-research` web discipline (`plan-research` → parallel `web-search` → `extract-evidence` with verbatim quotes and locator matching).
- **Synthesis Subagents (Wave 3, Wave 4 profiles)**: Local-only workers synthesizing comparative matrices, trade-offs, and rankings directly from existing corpus files without web searching.
- **Filesystem Blackboard**: Read scopes and write scopes are strictly disjoint. Subagents interact exclusively through committed files on disk.

## Phase & Wave Model

Eight structured phases, each protected by an artifact gate:

| Phase | Goal | Artifact gate |
|---|---|---|
| **0 — Charter** | Apply intake answers; clarify decider, use case, scale, framing, concurrency | `_meta/01-charter.md` scope statement + scale + framing + decider profile |
| **Wave 1 — Discovery & Scope** | Parallel dispatch of 2 subagents: 1A discovers/tiers entities; 1B derives axis catalog & native primitives. | `_meta/02-entities.md` (or `discovered-entities.md`) + `_meta/03-axes.md` + practitioner channel list |
| **2 — Template Authoring** | Orchestrator personally writes maximalist product & per-axis comparison templates. Target ~30+ vertical-specific sections. | `_meta/04-product-template.md` + `_meta/05-axis-templates.md` (or `_meta/_PRODUCT_TEMPLATE.md` + per-criterion templates) |
| **3 — Corpus Architecture** | Design tree shape, calculate file budgets, enforce MAX-N ceilings. Scaffold folders via `scripts/init-corpus.sh`. | `_meta/06-file-budget.md` + pre-created folder skeleton |
| **Wave 2 — Per-Entity Packs** | Fill `<entity-slug>/` for every `core` entity (parallel, ≤8 per sub-wave). Disjoint write scopes. Each covers all charter axes. | Populated `<entity-slug>/` packs; every section covered with evidence or specific "insufficient evidence" gap note |
| **Wave 3 — Cross-Axis Synthesis** | Compare entities along each axis. LOCAL-ONLY (no web tools). Each subagent owns one cross folder. | Populated `_cross/<axis-slug>/` or `_cross-<scope>/` with rankings + matrix + decision-flippers |
| **Wave 4 (Optional) — Profiles / Deepening** | Standalone `<entity-slug>.md` decision pages at corpus root (LOCAL-ONLY) OR research packs for promoted entities. | Profile pages OR new entity packs |
| **7 — Verification & Master Summary** | Orchestrator personally reads every file, resolves contradictions, writes master summary, and executes quality audit. | `_meta/00-master-summary.md` + passing 6-dimension evaluation audit |

## Output Architecture Contract

Domain-agnostic framing tree:

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
│   └── 07-dispatch-log.md                           (running log)
├── <entity-slug>/                                   (one per core entity; MAX 15 files)
│   ├── 00-overview.md
│   ├── 01-<axis-1>.md ... 0N-<axis-N>.md
│   └── 09-sources.md
├── <entity-slug>.md                                 (optional profile page at root)
└── _cross/
    └── <axis-slug>/                                (MAX 12 files)
        ├── 00-overall-comparison.md
        └── 01-<scenario>.md ...
```

Industry framing tree:

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
└── <entity-slug>.md                                 (profile page; Phase 6/Wave 4)
```

Folder and file naming rules, MAX-N ceilings, and numbered-prefix schemes: `references/filesystem.md`.
Category taxonomy archetypes: `references/industry/category-taxonomies.md`.

## How to Evaluate a Deep-Dive Corpus

Every deep research deliverable must pass the **6-Dimension Evaluation Audit** before completion:

1. **Structural & Budget Integrity**:
   - Strictly adhere to MAX-N caps (≤15 files/entity, ≤12 files/cross, ≤8 files/meta).
   - Zero temporary files, empty stubs, or placeholder strings (`TODO`, `TBD`, `fill later`).
   - All internal relative markdown links resolve correctly.
2. **Template Coverage & Gap Specificity (The 100% Rule)**:
   - Every `core` entity folder must address 100% of the axes locked in `_meta/03-axes.md`.
   - An axis must have either substantive evidence OR a concrete "insufficient evidence" entry explaining what was searched, which primary sources were checked, why data is unavailable, and what resolution is required.
3. **Evidentiary Rigor & Verbatim Quotations**:
   - Every numeric, performance, pricing, and version claim MUST cite a verbatim quotation with source URL and scrape date.
   - Search snippet citations are strictly forbidden — only fetched and verified page text counts.
   - Separate objective verified facts from vendor marketing claims and community sentiment.
4. **Community & Practitioner Attribution**:
   - Sentiment (Reddit, HN, forums) must never be summarized as vague "consensus".
   - Every community claim must cite author handle, date, score/upvotes, and post link.
5. **Cross-Axis Comparative Synthesis**:
   - Matrix cells in `_cross/` must be fully populated (no empty cells; use explicit `[No public data]` markers).
   - Rankings must be **conditional** (e.g., *"Vendor A for high-throughput, Vendor B for strict HIPAA compliance"*), naming operational variables rather than flat assertions.
   - Disagreements between sources must be explicitly surfaced and analyzed.
6. **Decider Actionability & Fresh-Context Legibility**:
   - The master summary (`_meta/00-master-summary.md`) must be self-contained and immediately actionable for a decider with zero prior context.
   - Must contain all 7 required sections: Document index, Critical findings, Cross-domain insights, Action items, Coverage scope, Open gaps, Recommendation.

Full evaluation rubric and automated audit commands: `references/evaluation.md` and `references/verification.md`.

## Hard Rules (Load-Bearing)

1. **Run the intake AskUserQuestion batch before any wave.** Scale, framing, and scope are locked at intake and recorded in the charter.
2. **The orchestrator does not search the web.** Web search is delegated to research subagents using the `run-research` discipline.
3. **The orchestrator does not delegate final synthesis.** The orchestrator personally reads every entity pack and cross file before writing the master summary.
4. **Templates first, files second.** Phase 2 (template authoring) MUST complete before any entity pack or cross file is written.
5. **Maximalist templates, not generic skeletons.** Target ~30+ vertical-specific sections.
6. **MAX 8 subagents per wave (domain-agnostic) / MAX 20 per wave (industry).** Split larger batches into sequential sub-waves.
7. **Disjoint write scopes.** Each subagent owns exactly one folder. No two subagents write to the same path.
8. **Every research brief embeds run-research.** Subagent briefs must include the `run-research` methodology block.
9. **Every numeric / versioned / priced claim cites a verbatim quote.** Snippet citations are forbidden.
10. **No placeholder or stub files.** Missing evidence becomes a specific data-gap paragraph inside an existing file, never an empty stub file.
11. **Two-level orchestration only.** Subagents do not spawn subagents.
12. **No single-report output.** This skill produces a multi-file navigable corpus. For a single report, use `run-research`.

## Self-Correction Triggers

- **Dispatching any wave before intake is answered** → STOP. Run intake first; lock scale, framing, decider profile.
- **Skipping Phase 2 templates and dispatching Wave 2** → STOP. Templates establish the comparability contract.
- **Writing a thin or generic template (≤15 sections)** → STOP. Re-author maximalist template (~30+ sections) per `references/industry/template-authoring.md`.
- **Letting a subagent silently omit a template section** → STOP. Every section requires evidence or a specific data-gap entry.
- **Summarizing Reddit as "consensus" without attribution** → STOP. Require username, date, score, quote, and permalink.
- **Searching the web yourself as orchestrator** → STOP. Dispatch a research subagent.
- **Delegating master summary synthesis** → STOP. Read all packs and cross folders personally.
- **Skipping the verification and evaluation gate** → STOP. Execute the audit checks in `references/evaluation.md` and `references/verification.md`.

## Reference Routing

Load only the reference whose phase is active:

| Reference | Read when |
|---|---|
| `references/intake.md` | Before Phase 0 — mandatory AskUserQuestion batch: scale, framing, scope, concurrency |
| `references/thinking.md` | Phase 0 — 7-question decomposition protocol, entities vs axes vs primitives |
| `references/templates.md` | Phase 0, 2, 3 — formats for charter, product templates, axis templates, file budgets |
| `references/orchestration.md` | Waves 1-4 — subagent wave choreography, parallel dispatch rules, between-wave gating |
| `references/filesystem.md` | Phase 3 — directory contract, MAX-N ceilings, file naming schemes |
| `references/subagent-briefs.md` | Waves 1-4 — copy-paste-ready subagent briefs with the run-research integration block |
| `references/synthesis.md` | Phase 7 — claims ledger discipline, 10-section profile pages, 7-section master summary |
| `references/evaluation.md` | Phase 7 & Between-Wave Gates — deep-dive evaluation rubric, 6-step audit workflow, triage protocols |
| `references/verification.md` | Phase 7 — concrete bash/ruby verification commands and automated integrity checks |
| `references/failure-modes.md` | Any wave — recovery protocols for timeouts, shallow outputs, contradictions, cap overflow |
| `references/industry/template-authoring.md` | **Keystone reference** (industry framing) — writing maximalist `_PRODUCT_TEMPLATE.md` and per-criterion comparison templates |
| `references/industry/industry-architecture.md` | Phase 3 (industry framing) — 4-layer industry tree, entity tiering, file budget derivation |
| `references/industry/category-taxonomies.md` | Phase 2 (industry framing) — archetype taxonomies (SaaS, OSS, dev-infra, data/API, regulated, consumer) |
| `references/industry/discovery.md` | Wave 1 (industry framing) — entity discovery sub-questions, tiering, deep category pre-pass |
| `references/industry/evidence-and-synthesis.md` | Waves 2-3 (industry framing) — source hierarchy, claims ledger schemas, Reddit rules, unit economics |
| `references/industry/profile-pages.md` | Wave 4 / Phase 6 (industry framing) — writing standalone `<entity-slug>.md` decision profiles |
| `references/industry/mission-briefs.md` | Waves 1-4 (industry framing) — industry-specific mission prompts for subagents |
| `references/industry/research-powerpack-and-explore.md` | Waves 1-3 (industry framing) — Research Power Pack API shapes (`plan-research`, `web-search`, `extract-evidence`) |
| `references/industry/worked-example-cloud-browsers.md` | Any phase (industry framing) — complete annotated walkthrough of a reference research corpus |
| `scripts/init-corpus.sh` + `scripts/init-corpus.md` | Phase 0 or 3 — deterministic corpus directory scaffolding |

## Quick Start (First 5 Minutes)

1. **Intake** — run the batched `AskUserQuestion` call (scale / framing / scope / concurrency). See `references/intake.md`.
2. **Phase 0** — write `_meta/01-charter.md` from intake answers + decider/use-case. See `references/thinking.md` and `references/templates.md`.
3. **Wave 1** — dispatch parallel discovery (1A) and scope-mapping (1B) subagents. Both invoke `run-research`. Read outputs personally upon return.
4. **Phase 2 & 3** — write maximalist templates (`references/templates.md` or `references/industry/template-authoring.md`); plan file budget (`references/filesystem.md`); optionally run `scripts/init-corpus.sh <topic-slug>`.
5. **Wave 2** — dispatch parallel per-entity subagents (≤8 per sub-wave) to fill `<entity-slug>/` packs.
6. **Wave 3** — dispatch parallel local-only subagents to build cross-axis comparisons in `_cross/`.
7. **Phase 7** — personally read all packs and cross files; write `_meta/00-master-summary.md`; run the 6-dimension evaluation audit in `references/evaluation.md` and `references/verification.md`.
