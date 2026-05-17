---
name: run-industry-research
description: Use skill if you are running market, category, or competitive research on 5+ vendors and need a folder corpus with evidence packs, comparison tables, and source ledgers.
---

# Run Industry Research

Build a source-backed **industry research corpus**: per-entity evidence packs, cross-entity comparison tables, practitioner/Reddit context, source ledgers, and standalone profile pages. Output is a navigable folder tree — never a single report.

The discipline is **template-driven**. Phase 2 writes maximalist `_PRODUCT_TEMPLATE.md` + per-criterion `_COMPARISON_TEMPLATE_*.md` files that define the *minimum* coverage every entity pack and every cross-criterion comparison must address. Templates are the comprehensiveness boundary; depth is forced by overcrowding the templates upfront, not by hoping each agent searches deeply.

## When to use

*Italicized phrases below match real triggers. If any one fits, this skill applies.*

- *"market analysis of [category]" / "competitive landscape" / "category map" / "competitor research"*
- *"compare [5+ players] in the [X] space" / "evaluate [N] vendors / tools / providers"*
- *"build a research corpus / evidence pack / decision corpus on [category]"*
- *"deep research on [SaaS / OSS / dev-infra / data-API / regulated] category" with per-vendor pages*
- *"give me pricing + capability + integration + security + audience matrices across [vendors]"*
- *"navigable folder of product pages, comparison rollups, source ledgers, and profile pages"*
- *user names 5+ vendors/projects upfront and asks for a structured side-by-side*

### Do NOT use when

- *one technical question, one bug, one library, one architecture decision* → use `run-research`
- *1–4 entity comparison or a single-page summary with no corpus structure* → use `run-research`
- *generic N-entity decision corpus where the question is "compare N things for a decision" without market/vendor framing* → use `run-corpus-research`
- *finding or shortlisting GitHub repos as the deliverable* → use `run-github-scout`
- *codebase analysis, code review, or implementation work* → not this skill
- *the user wants a polished single deliverable (HTML battlecard, slide deck)* — this skill produces evidence; downstream skills polish it

`run-research` answers one technical question. `run-corpus-research` is the generic N-entity decider. `run-industry-research` is the **market/category/vendor** specialization with maximalist templates and source ledgers. `run-github-scout` is repo-shortlist only.

## Pinned defaults

| Key | Default |
|---|---|
| Trigger threshold | 5+ named or discoverable entities, market/category framing, reusable corpus output |
| Default scale | `standard` for 10–40 entities; `compact` for 5–10 entities |
| Hard wave cap | 20 research agents per wave |
| Recommended wave size | 6–8 agents when integration quality or context pressure matters |
| Profile pages | Default yes for `core` tier at `standard` scale or larger |
| File count policy | Bounded by template-section-count × entity-count, plus cross-criterion files. No fixed cap. |
| Source ledger policy | Per-entity ledgers in `[entity]/09-sources/`; cross-corpus ledgers in `_cross-[scope]/09-sources/` |

## Hard rules (load-bearing)

These break the corpus when ignored. Keep them at the top of mind.

1. **Templates first, files second.** Phase 2 (template authoring) MUST complete before any entity-pack or cross-comparison file is written. Skipping template authoring is a hard failure — depth varies per entity, comparability is lost.
2. **Maximalist templates, not generic skeletons.** A thin `_PRODUCT_TEMPLATE.md` (≤15 sections) means Phase 1's deep category pre-pass was skipped. Re-do it. Target ~30+ vertical-specific sections.
3. **Concurrency cap: 20 research agents per wave.** No exceptions. Beyond 20, dispatch a second wave.
4. **No placeholder files.** A template section with no evidence becomes a one-paragraph "insufficient evidence" entry inside an existing file in the same subfolder, naming the specific data gap. **Never** a stub file.
5. **Folder names are vertical-specific, filenames are agent-chosen.** The orchestrator chooses subfolder names per category (Phase 2). Subagents pick the actual `01-meaningful-title.md` filenames inside those folders based on the evidence THEIR entity surfaces. Two agents may land different filenames in the same numbered subfolder — that is correct, because their evidence shapes differ.
6. **Reusing canonical slugs (`05-security`, `07-benchmarks`) without adapting them to the vertical is a failure.** Open `references/architecture/category-taxonomies.md` and resolve vertical-specific names.
7. **Separate confirmed facts, vendor/project claims, practitioner evidence, and inference.** Never treat snippets as evidence. Never present Reddit as "consensus" without per-comment attribution.
8. **No single-report output.** This skill produces a multi-file corpus. If the user wants a single report, redirect to `run-research`.
9. **Two-level orchestration only.** Agents do not create subagents.
10. **Orchestrator reads every `core` entity pack personally** before Phase 5 cross-synthesis. Do not delegate this read.

## Tools and graceful degradation

This skill is Research Power Pack–enhanced. Tool names vary by runtime; before Phase 1, verify available tool names and record the result in `_meta/methodology-and-source-policy.md`.

| Capability | Portable API | Use when | Fallback |
|---|---|---|---|
| Research planning | `start-research` | Set scope, gaps, stop criteria | parallel `WebSearch`, then `curl` |
| Classified web search | `web-search` / `smart-web-search` | Triage with extraction/synthesis in context | `WebSearch`, then `curl` |
| Raw result harvesting | `raw-web-search` | Build an unfiltered URL pool for later triage | `WebSearch`, then `curl` |
| Classified page extraction | `scrape-links` / `smart-scrape-links` | Structured matches, gaps, follow-up signals | `WebFetch`, then `curl` |
| Raw source capture | `raw-scrape-links` | Preserve full markdown / Reddit threads for files/agents | `WebFetch`, then `curl` |
| Local corpus search | `Explore` or `rg`/`find` + read tools | Search generated files, source URLs, duplicates, links | manual file reads |
| Parallel entity research | web-capable research agents (≤20/wave) | Independent entity or criterion work, disjoint write scopes | sequential search rounds |

Use **smart** tools for classified extraction or synthesis that goes into context. Use **raw** tools for unfiltered result harvesting, source capture, Reddit thread preservation, or evidence passed to files/agents.

Read `references/agents/research-powerpack-and-explore.md` for concrete invocation patterns and parameter recipes. If MCP tools fail or are unavailable, use the fallback chain — never stop the workflow because one tool is missing.

## Phase model

Eight phases, each with an artifact gate. Skip a phase only when its artifact is not needed for the user's stated outcome — and state the reason.

| Phase | Goal | Artifact gate |
|---|---|---|
| **0 — Charter** | Clarify outcome, scale, archetype | Scope statement + corpus scale |
| **1 — Discovery** | Find entities AND understand the category deeply | `_meta/discovered-entities.md` + category-understanding note |
| **2 — Template authoring** | Pick context-specific category names AND write maximalist templates | `_meta/_PRODUCT_TEMPLATE.md` + `_meta/_COMPARISON_TEMPLATE_<criterion>.md` per criterion |
| **3 — Architecture** | Plan tree shape and file-count expectation | `_meta/file-budget.md` + tree plan |
| **4 — Evidence packs** | Per-entity research (parallel, ≤20/wave) | `[entity-slug]/` folders, agent-chosen filenames |
| **5 — Cross-entity synthesis** | Compare entities by criterion (parallel, ≤20/wave) | `_cross-<scope>/` rollups |
| **6 — Profile pages** | Standalone decision pages | `[entity-slug].md` at root for `core` entities |
| **7 — Verification** | Source ledger, link check, template-coverage audit | Completion gate passed |

### Phase 0 — Charter

1. Ask: "What will you do with this research?" Capture target audience, geography, decision type (buying, strategy, implementation, investment, content). Skip when intent is clear from context.
2. Choose corpus scale (guidance, not hard cap):
   - `compact` — 5–10 entities, ~80–200 files
   - `standard` — 10–40 entities, ~150–500 files
   - `deep` — 40–100 entities, ~500–2000 files
   - `tiered` — 100+ entities, full packs for top tier only
3. Once topic slug is known, optional deterministic scaffold: `bash scripts/init-corpus.sh <topic-slug> [entity-slug ...]`. Creates root/meta starter files and empty directories only — no entity evidence placeholders. See `scripts/init-corpus.md` for usage.

**Artifact:** one-paragraph scope statement with chosen scale, presented to user before Phase 1.

### Phase 1 — Discovery (with deep category pre-pass)

Two outputs: the entity list AND the category understanding that feeds Phase 2 template authoring. **Think first:** which candidate clusters would a generic top-10 search miss?

1. **Decompose the topic into 3–5 sub-questions.** Each surfaces a different candidate cluster.
2. **Run discovery searches** via `start-research` (preferred) or web-capable research agents with `WebSearch`/`WebFetch` (fallback).
3. **Tier candidates** into `core`, `secondary`, `discovered-only`.
4. **Run a deep category pre-pass.** Before locking the entity list, study the category itself: what axes do buyers actually compare on? What pricing primitives are native here? What practitioner channels matter? What regulatory/compliance angles apply? This pre-pass is what enables maximalist templates in Phase 2 — without it, templates default to generic and miss vertical-specific axes.

Read `references/workflow/discovery.md` for the full discovery sub-workflow and the deep category pre-pass.

**Artifacts:**
- `_meta/discovered-entities.md` — every candidate, tiered, with source URL and 1-line rationale
- A short category-understanding note (1–2 paragraphs) on what the vertical's buyers care about, captured in `_meta/research-plan.md` or surfaced in chat

### Phase 2 — Template authoring (keystone)

Translate the deep category understanding into maximalist templates. **Think first:** which buyer axes, native units, risks, and practitioner channels make this vertical different?

1. **Pick the matching archetype** from `references/architecture/category-taxonomies.md` (SaaS, OSS ecosystem, dev infra, data/API provider, regulated, consumer/media). The archetype is the starting skeleton.
2. **Adapt the archetype to the vertical.** Rename slugs so each path says what the file answers in the buyer's language. Run the **category completeness check** before locking the slug list.
3. **Write `_meta/_PRODUCT_TEMPLATE.md`** — a maximalist menu of every subfolder, every section, every question that any product in the category should be evaluated against. Overcrowd it deliberately. Sparse evidence is acceptable; a missing section the buyer cares about is not.
4. **Write `_meta/_COMPARISON_TEMPLATE_<criterion>.md` per cross-criterion** — one comparison template per axis (pricing, capabilities, integrations, security, audience, benchmarks, buyer-fit, sources). Each prescribes comparison axes, matrix columns, ranking dimensions, and per-criterion source expectations. For `compact` scale, a single master `_meta/_COMPARISON_TEMPLATE.md` covering all criteria is acceptable.

Read `references/architecture/template-authoring.md` for the maximalist-template recipe and worked-example templates. **This is the keystone reference.**

**Templates set the comprehensiveness boundary.** A Phase 4 agent filling a section either provides source-backed content OR a one-paragraph "insufficient evidence" note with the data gap named. Filenames are not in the template — agents pick `01-meaningful-title.md` based on what their evidence supports.

**Artifacts:**
- `_meta/_PRODUCT_TEMPLATE.md` — master per-entity template (typically 200–400 lines, intentionally overcrowded)
- `_meta/_COMPARISON_TEMPLATE_<criterion>.md` — one per cross-criterion (each typically 100–250 lines), or a single master `_meta/_COMPARISON_TEMPLATE.md` for `compact` corpora
- The resolved category list, shown to the user before Phase 3

### Phase 3 — Architecture

Plan the tree before any entity-pack file creation.

1. Read `references/architecture/research-architecture.md` for the 4-layer shape (root, `_meta/`, entity packs, cross-entity).
2. Compute file-count expectation: `total_files ≈ root_and_meta + entity_count × template_section_count + cross_count × cross_template_section_count + profile_count`. The template section counts ARE the boundary — there is no separate hard cap.
3. Decide whether standalone `<entity>.md` profile pages at root are needed (default yes for `core` tier when scale ≥ `standard`). Read `references/architecture/profile-pages.md` for the profile-page pattern.

**Artifact:** `_meta/file-budget.md` with the tree plan, expected file-count range derived from templates, and entity tier assignments. This is an estimate, not a cap.

### Phase 4 — Evidence packs

Research each `core` entity into its evidence pack, **driven by the Phase 2 templates**. **Think first:** which template sections must every entity prove with sources or mark as insufficient evidence?

1. **Dispatch up to 20 entity-research agents in parallel per wave.** Each owns ONE entity folder; write scopes are disjoint. For >20 entities, run multiple waves.
2. **Each agent's brief includes the resolved template list** (`_meta/_PRODUCT_TEMPLATE.md`) plus discovered-entities scope and source-hierarchy rules.
3. **Sub-question decomposition** (3–5 questions per template section) and source-hierarchy rules from `references/workflow/evidence-and-synthesis.md`.
4. **Agents decide filenames within sections.** The template prescribes the section "what evidence belongs here" — the agent picks the actual filename based on what they found.
5. **Insufficient-evidence handling.** Fold sparse-evidence sections into an existing file in the same subfolder as a one-paragraph note. **No stub files. Never silently drop a section.**
6. **Process completed agents as they return.** Do not wait for the whole wave. Update `_meta/discovered-entities.md` if new candidates emerge worth promoting.
7. **Maximum 2 retries per failed mission**, with a narrower prompt each time.

Read `references/agents/mission-briefs.md` for entity-pack, audience, source-verification, and profile-writer brief templates.

**Artifact:** populated `[entity-slug]/` folders. Every section in `_PRODUCT_TEMPLATE.md` is addressed in every `core` pack — content OR explicit "insufficient evidence" with the data gap named.

### Phase 5 — Cross-entity synthesis

Compare entities by criterion across the population, **driven by the per-criterion comparison templates**. **Think first:** which entities are directly comparable, adjacent, or not comparable for this criterion?

1. **Read every `core` entity pack personally** before synthesis. Do not delegate this read.
2. **Dispatch up to 20 Cross-Category Comparison Agents in parallel per wave** — one agent per criterion (pricing, capabilities, integrations, security, audience, benchmarks, buyer-fit, sources). Each owns one cross-criterion folder.
3. **Each brief references the matching `_COMPARISON_TEMPLATE_<criterion>.md`** which prescribes axes, matrix columns, ranking dimensions, and source expectations specific to that criterion.
4. **Each cross file** must answer: which entities are directly comparable, adjacent, or not-comparable? Which wins for which scenario? Where do sources contradict? What test would change the recommendation?
5. **Reuse the source-hierarchy + source-map + claims-ledger schemas** from `references/workflow/evidence-and-synthesis.md`.

**Artifact:** populated `_cross-<scope>/` folder. Each criterion has at minimum a `00-overall-comparison.md` plus the granular comparison files mandated by its `_COMPARISON_TEMPLATE_<criterion>.md`.

### Phase 6 — Profile pages

Write the standalone `[entity-slug].md` decision pages at the corpus root for `core` tier entities.

1. **The profile is a synthesis, not a copy.** It is the buyer's first read — a readable narrative that summarizes the evidence pack and links into it for detail.
2. Read `references/architecture/profile-pages.md` for section ordering and the rule that distinguishes profile pages from evidence-pack `00-overview/` files.
3. Profile pages may be 300–700 lines for substantial entities. They are intentionally larger than evidence-pack files because they synthesize multiple categories.

**Artifact:** `[entity-slug].md` at corpus root for every `core` entity, each linking to its evidence pack.

### Phase 7 — Verification

Run the completion gate before declaring done. **Think first:** which verification failure would invalidate the corpus as a decision aid?

```bash
# Template-coverage audit (THE comprehensiveness check)
# For each entity, every template section is addressed (with content OR an "insufficient evidence" entry)

# File count (informational, not capped)
find <topic-slug> -type f | wc -l

# No hidden junk
find <topic-slug> -name '.DS_Store' -o -name 'Thumbs.db' -o -name '*.tmp' -o -name '*.bak'

# Local markdown link integrity (Ruby one-liner in research-architecture.md)
```

Verify:

- **Template coverage** — every section of `_PRODUCT_TEMPLATE.md` is addressed in every `core` entity pack; every `_COMPARISON_TEMPLATE_<criterion>.md` section is addressed in its cross folder. "Insufficient evidence" entries name the specific data gap.
- Root `README.md` points to highest-signal entry points.
- Every `core` entity has a profile page linking to its evidence pack.
- Source maps and claims ledgers exist at entity and cross-category level using the required schemas.
- Reddit/practitioner evidence is direct when available, labeled adjacent when sparse, never presented as consensus without attribution.
- All stale placeholders, broken local links, and naming mismatches are fixed.

**Artifact:** completion statement covering corpus path, total files, entity count, top entry points, critical findings, unresolved gaps, and verification results.

## Output architecture contract

Default shape (concrete names from Phase 2):

```text
[topic-slug]/
├── README.md
├── _meta/
│   ├── research-plan.md
│   ├── _PRODUCT_TEMPLATE.md                            ← Phase 2 maximalist template
│   ├── _COMPARISON_TEMPLATE_[criterion-a].md           ← Phase 2 per-criterion template
│   ├── _COMPARISON_TEMPLATE_[criterion-b].md           ← (one per cross-criterion)
│   ├── methodology-and-source-policy.md
│   ├── discovered-entities.md
│   └── file-budget.md
├── _cross-[scope]/
│   ├── 00-overview/
│   ├── [criterion-a]/
│   ├── [criterion-b]/
│   └── 09-sources/
├── [entity-slug]/
│   ├── 00-overview/
│   ├── [vertical-context-1]/
│   ├── [vertical-context-2]/
│   └── 09-sources/
└── [entity-slug].md           ← profile page (Phase 6)
```

Each folder name reveals the buyer or researcher question it answers. Numeric prefixes are scan order, not semantic naming. Filenames within each numbered subfolder are agent-chosen based on the evidence found for that specific entity.

## Worked example

Read `references/workflow/worked-example-cloud-browsers.md` for a self-contained walkthrough of taxonomy choices, template excerpts, mission brief shape, verification artifacts, and the optional owner-local corpus path. **Mirror its discipline; never copy its slugs.**

## Output contract

Show these artifacts at the phase that produces them. Never batch all artifacts to the end.

1. **Phase 0** — scope statement + corpus scale.
2. **Phase 1** — discovered entities table (tier + source URL + 1-line rationale) AND a category-understanding note.
3. **Phase 2** — resolved category list AND the maximalist `_PRODUCT_TEMPLATE.md` AND each `_COMPARISON_TEMPLATE_<criterion>.md`. Show inline (or summarized with link) — they are the comprehensiveness contract for the rest of the work.
4. **Phase 3** — file-count expectation derived from templates + tree shape.
5. **Phase 4** — agent dispatch map (which agent owns which entity), then evidence-pack progress notes as agents complete.
6. **Phase 5** — cross-criterion ranking summary.
7. **Phase 6** — profile-page index.
8. **Phase 7** — completion statement (path, files, entry points, gaps, verification, template coverage).

## Self-correction triggers

Stop and correct when any of these appears:

- **Skipping Phase 2 and going straight to entity-pack research** → STOP. Templates are the comprehensiveness boundary; without them, depth varies and comparability is lost. Write the templates first.
- **Thin, generic `_PRODUCT_TEMPLATE.md` (≤15 sections)** → STOP. Re-do Phase 1's category understanding and re-author the template at ~30+ sections.
- **Reusing canonical slugs without checking the archetype** → STOP. Open `references/architecture/category-taxonomies.md` and resolve vertical-specific names.
- **Subagent skipping a template section silently** → STOP. Every section addressed in every `core` pack — content OR named "insufficient evidence" entry.
- **Hardcoding subagent filenames in the template** → STOP. Templates list *sections and questions*; agents pick filenames.
- **Dispatching more than 20 agents in one wave** → STOP. Split into waves of ≤20.
- **Summarizing Reddit as "consensus" without per-comment attribution** → STOP. Apply audience-evidence fields from `references/workflow/evidence-and-synthesis.md`.
- **Treating a vendor's marketing page as confirmed fact** → STOP. Re-classify per the source hierarchy.
- **Skipping the completion gate ("looks done")** → STOP. Run the verification commands. Template-coverage audit, link check, source-ledger presence are non-negotiable.
- **Producing single-report output ("here's the markdown report")** → STOP. This skill produces a corpus. If the user wants a single report, redirect to `run-research`.
- **Orchestrator skipping the read of entity packs before cross-synthesis** → STOP. The orchestrator must read each `core` pack personally before Phase 5.

## Anti-patterns

| Anti-pattern | Why it fails | Fix |
|---|---|---|
| Templates skipped or written after entity research | No comprehensiveness boundary; depth varies | Phase 2 first, Phase 4 second. Always. |
| Template thin/generic (≤15 sections) | Misses vertical-specific axes; shallow corpus | Re-do Phase 1 deep pre-pass; re-author at ~30+ sections |
| Template prescribes exact filenames | Removes evidence-driven naming; agents pad to fit | Template lists sections + questions; agents pick filenames |
| Stub files for sections with no evidence | Pollution; no actual content | "Insufficient evidence" note inside an existing file with the data gap named |
| Identical empty subfolders for every entity | Copy-paste research, no value | Create only evidence-justified files; address every section in content or "insufficient evidence" entry |
| Cross-product file is a concatenation of product summaries | Doesn't compare; just appends | Comparison template prescribes axes, ranking dimensions; agents follow it |
| Pricing copied from page without unit economics | Vendors hide overages, gating, scenario costs | Preserve native units, model scenarios, name missing variables explicitly |
| Reddit evidence presented as consensus | Bias and small samples are erased | Preserve thread, username, date, quote, bias label per audience-evidence rules |
| Source verification skipped because "it's clearly true" | Stale facts, contradicted vendor claims | Source map + claims ledger non-optional for `core` entities |
| Profile page duplicates evidence-pack content | Duplication; no synthesis added | Profile = readable narrative + links into pack; pack = atomic evidence files |
| Single-output thinking ("write me a report") | Loses navigability and source-traceability | Multi-file corpus is the contract; ask user to confirm if pushed |

## Reference routing

Load only the references whose phase is active. Loading all at once exhausts context.

| File | Read when |
|---|---|
| `references/architecture/research-architecture.md` | Phase 3 — designing the corpus tree, file-count expectation derivation, entity tiers, validation gates. |
| `references/architecture/category-taxonomies.md` | Phase 2 — choosing the archetype skeleton (SaaS, OSS, dev infra, data provider, regulated, consumer) before adapting to the vertical. |
| `references/architecture/template-authoring.md` | Phase 2 — writing the maximalist `_PRODUCT_TEMPLATE.md` and per-criterion `_COMPARISON_TEMPLATE_<criterion>.md` files. **Keystone reference.** |
| `references/architecture/profile-pages.md` | Phase 6 — writing the standalone `<entity>.md` decision pages. |
| `references/workflow/discovery.md` | Phase 1 — finding entities, decomposing into sub-questions, tiering candidates, AND running the deep category pre-pass that feeds template authoring. |
| `references/workflow/evidence-and-synthesis.md` | Phase 4–5 — applying source hierarchy, source-map and claims-ledger schemas, Reddit/practitioner rules, pricing/unit-economics standards, cross-category structure. |
| `references/workflow/worked-example-cloud-browsers.md` | Any phase — annotated walkthrough of the cloud-browsers corpus including the actual template artifacts. Use to mirror the *discipline*; do not copy slugs. |
| `references/agents/mission-briefs.md` | Phase 1, 4, 5 — writing prompts for discovery, entity-pack, cross-comparison, audience, source-verification, and profile-writer agents. |
| `references/agents/research-powerpack-and-explore.md` | Phase 1, 4, 5 — portable Research Power Pack API shapes (`start-research`, smart/raw search and scrape) plus web-capable research agent and local-corpus Explore patterns (≤20 per wave). |
| `scripts/init-corpus.md` | Phase 0 or 3 — deterministic corpus scaffolding via `scripts/init-corpus.sh`; root/meta starter files only, never entity evidence placeholders. |

## Guardrails

- Do not make landing-page-style reports. Build the actual research corpus.
- Do not collapse product facts, pricing, practitioner sentiment, and source verification into one undifferentiated file.
- Do not create raw dump folders unless the user explicitly asks. Summarize and source-map instead.
- Do not use the same category names for every vertical when better names are available.
- Do not outsource final synthesis. The orchestrator reads the files and resolves contradictions personally.
- Do not exceed 20 researcher agents per wave. Run multiple waves instead.
- Do not let agents create subagents. Two-level orchestration only.
- Do not start Phase 4 entity research before the Phase 2 templates are written and shown to the user.
- Do not declare completion without running the Phase 7 verification, including the template-coverage audit.
