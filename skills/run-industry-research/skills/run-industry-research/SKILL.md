---
name: run-industry-research
description: Use skill if you are researching an industry, market, or vendor category with 5+ entities and need a multi-file evidence corpus with per-entity packs, cross-entity comparisons, and source ledgers.
---

# Run Industry Research

Build a source-backed industry research corpus: per-entity evidence packs, cross-entity comparison rollups, Reddit/practitioner context, source verification ledgers, and readable standalone decision pages. Output is a navigable folder tree, not a single report.

The discipline is **template-driven**. The orchestrator first studies the category deeply enough to write maximalist templates that define the *minimum* coverage every entity pack and every cross-criterion comparison must address. Templates are the comprehensiveness boundary; depth is forced by overcrowding the templates upfront.

## Trigger boundary

Use this skill when the user asks for:

- comprehensive industry research, market landscape, category map, or competitive landscape
- deep product-category audits with many vendors, tools, frameworks, or open-source projects
- SaaS research, open-source ecosystem research, developer-tool landscape, or provider comparison
- a reusable research folder with product pages, comparison rollups, pricing/unit economics, source ledgers, Reddit/audience evidence, and master summaries

Do not use this skill for:

- a single technical question or architecture decision — use `run-research`
- finding GitHub repositories only — use `run-github-scout`
- codebase analysis, code review, or implementation work
- a quick one-page market summary where a full corpus would be overkill
- producing a polished single deliverable (HTML battlecard, slide deck) — this skill produces evidence; downstream skills polish it

## Hard limits

- **Concurrency cap: 20 research agents per wave.** No exceptions. Beyond 20, dispatch a second wave.
- **No fixed file ceiling.** Total file count is bounded by the templates' minimum coverage × entity count, plus cross-criterion files. A `standard` corpus typically lands at 150-500 files; a `deep` corpus at 500-2000+. Discipline comes from the templates, not from a hard cap.
- **No placeholder files.** Every created file must contain source-backed, independently useful content. A template section with no evidence becomes a one-paragraph "insufficient evidence" entry inside an existing file, **not** a stub file.
- **Templates first, files second.** Phase 2 (template authoring) must complete before any entity-pack or cross-comparison file is written. Skipping template authoring is a hard failure.
- **Folder names and filenames are agent-chosen, not fixed.** The orchestrator decides folder names per vertical (Phase 2). Subagents decide the actual `01-xxx.md` filenames within those folders based on the evidence they find for THEIR entity. Two agents researching the same vertical may land different filenames inside the same numbered subfolder — that is correct.
- **Resolve concrete kebab-case names before file creation.** Reusing canonical slugs (`05-security`, `07-benchmarks`) without adapting them to the vertical is a failure.
- **Separate confirmed facts, vendor/project claims, practitioner evidence, and inference.** Never treat snippets as evidence.

## Tools and graceful degradation

This skill is MCP-enhanced. Tool preference order:

| Capability | First choice | Fallback 1 | Fallback 2 |
|---|---|---|---|
| Multi-source web research | `mcp__research-powerpack__start-research` | parallel `WebSearch` | `curl` from shell |
| Targeted query | `mcp__research-powerpack__web-search` | `WebSearch` | `curl` |
| Page extraction | `mcp__research-powerpack__scrape-links` | `WebFetch` | `curl` + parse |
| Codebase / local file search | `Explore` subagent (parallel) | `Grep` + `Glob` | `Read` |
| Parallel entity research | Parallel `Explore` subagents (≤20/wave) | Sequential `WebSearch` rounds | — |

Read `references/agents/research-powerpack-and-explore.md` for concrete invocation patterns and parameter recipes.

If MCP tools fail or are unavailable, use the fallback chain. Do not stop the workflow because one tool is missing.

## Phase model

Eight phases, each with an artifact gate. Skip a phase only when its artifact is not needed for the user's stated outcome — and state the reason explicitly.

| Phase | Goal | Artifact gate |
|---|---|---|
| **0 — Charter** | Clarify outcome, scale, archetype | Scope statement + corpus scale |
| **1 — Discovery** | Find the entities AND understand the category deeply enough to write templates | `_meta/discovered-entities.md` + a category-understanding note |
| **2 — Template authoring** | Pick context-specific category names AND write maximalist templates | `_meta/_PRODUCT_TEMPLATE.md` + `_meta/_COMPARISON_TEMPLATE_<criterion>.md` per criterion |
| **3 — Architecture** | Plan tree shape and file-count expectation | `_meta/file-budget.md` and tree plan |
| **4 — Evidence packs** | Per-entity research (parallel, ≤20/wave, agents fill template) | `[entity-slug]/` folders with agent-chosen filenames |
| **5 — Cross-entity synthesis** | Compare entities by criterion (parallel, ≤20/wave, agents fill comparison templates) | `_cross-<scope>/` rollups |
| **6 — Profile pages** | Readable standalone decision pages | `[entity-slug].md` at root for core entities |
| **7 — Verification** | Source ledger, link check, template-coverage audit | Completion gate passed |

### Phase 0 — Charter

Clarify outcome if missing:

1. Ask: "What will you do with this research?" Capture target audience, geography, decision type (buying, strategy, implementation, investment, content).
2. Skip questions when the user's intent is already clear from context.
3. Choose corpus scale (guidance, not hard cap):
   - `compact` — 1-10 entities, ~80-200 files
   - `standard` — 10-40 entities, ~150-500 files
   - `deep` — 40-100 entities, ~500-2000 files
   - `tiered` — 100+ entities, full packs for top tier only

**Artifact:** one-paragraph scope statement with chosen scale, presented to user before Phase 1.

### Phase 1 — Discovery (with deep category pre-pass)

Phase 1 has TWO outputs: the entity list AND the category understanding that feeds Phase 2 template authoring.

1. **Decompose the topic into 3-5 sub-questions.** Each sub-question surfaces a different candidate cluster.
2. **Run discovery searches** via `mcp__research-powerpack__start-research` (preferred) or parallel Explore subagents (fallback).
3. **Tier candidates** into `core`, `secondary`, `discovered-only`.
4. **Run a deep category pre-pass.** Before locking the entity list, study the category itself: what axes do buyers actually compare on? What pricing primitives are native here? What practitioner channels matter? What regulatory/compliance angles apply? This pre-pass is what enables you to write maximalist templates in Phase 2 — without it, the templates default to generic and miss vertical-specific axes.

Read `references/workflow/discovery.md` for the full discovery sub-workflow and the deep category pre-pass.

**Artifacts:**
- `_meta/discovered-entities.md` — every candidate, tiered, with source URL and 1-line rationale
- A short category-understanding note (1-2 paragraphs) summarizing what the vertical's buyers care about, captured in `_meta/research-plan.md` or surfaced in chat

### Phase 2 — Template authoring

This is the keystone phase. The orchestrator translates the deep category understanding into maximalist templates that define minimum coverage for every entity pack and every cross-criterion comparison.

1. **Pick the matching archetype** from `references/architecture/category-taxonomies.md` (SaaS, OSS ecosystem, dev infra, data/API provider, regulated, consumer/media). The archetype is the starting skeleton.
2. **Adapt the archetype to the vertical.** Rename slugs so each path says what the file answers in the buyer's language. Run the **category completeness check** before locking the slug list.
3. **Write `_meta/_PRODUCT_TEMPLATE.md`** — a maximalist menu of every subfolder, every section, every question that any product in the category should be evaluated against. Overcrowd it deliberately. Sparse evidence is acceptable; a missing section the buyer will care about is not. Read `references/architecture/template-authoring.md` for the maximalist-template recipe and the worked-example templates.
4. **Write `_meta/_COMPARISON_TEMPLATE_<criterion>.md` per cross-criterion** — one comparison template per axis (pricing, capabilities, integrations, security, audience, benchmarks, buyer-fit, sources). Each template prescribes the comparison axes, the matrix columns, the ranking dimensions, and the per-criterion source expectations. For `compact` scale, a single master `_meta/_COMPARISON_TEMPLATE.md` covering all criteria is acceptable.

**Templates set the comprehensiveness boundary.** When a Phase 4 agent fills a section, it can either provide source-backed content OR a one-paragraph "insufficient evidence" note with the specific data gap named. Skipping a section silently is a failure.

**Filenames are not in the template.** The template lists *sections* and the *questions each section must answer*. The Phase 4 agent decides the actual `01-meaningful-title.md` filename based on what the evidence supports for THAT specific entity. Two agents may land different filenames in the same numbered subfolder — that is correct, because their evidence shapes differ.

**Artifacts:**
- `_meta/_PRODUCT_TEMPLATE.md` — the master per-entity template (typically 200-400 lines, intentionally overcrowded)
- `_meta/_COMPARISON_TEMPLATE_<criterion>.md` — one per cross-criterion (each typically 100-250 lines), or a single master `_meta/_COMPARISON_TEMPLATE.md` for `compact` corpora
- The resolved category list, shown to the user before Phase 3

### Phase 3 — Architecture

Plan the tree before any entity-pack file creation.

1. Read `references/architecture/research-architecture.md` for the 4-layer shape (root, `_meta/`, entity packs, cross-entity).
2. Compute file-count expectation: `total_files ≈ root_and_meta + entity_count × template_section_count + cross_count × cross_template_section_count + profile_count`. The template section counts ARE the boundary — there is no separate "file budget cap".
3. Decide whether standalone `<entity>.md` profile pages at root are needed (default yes for `core` tier when scale is `standard` or larger). Read `references/architecture/profile-pages.md` for the profile page pattern.

**Artifact:** `_meta/file-budget.md` with the tree plan, expected file-count range derived from templates, and entity tier assignments. This is an estimate, not a cap.

### Phase 4 — Evidence packs

Research each `core` entity into its evidence pack, **driven by the Phase 2 templates**.

1. **Dispatch up to 20 entity-research agents in parallel per wave.** Each agent owns ONE entity folder; write scopes are disjoint. For >20 entities, run multiple waves.
2. **Each agent's brief includes the resolved template list** (`_meta/_PRODUCT_TEMPLATE.md`) plus the discovered-entities scope boundary and the source-hierarchy rules.
3. **Each agent uses sub-question decomposition** (3-5 questions per template section) and source-hierarchy rules from `references/workflow/evidence-and-synthesis.md`.
4. **Each agent decides filenames within sections.** The template prescribes the section "what evidence belongs here" — the agent picks the actual `01-meaningful-title.md` based on what they found.
5. **Insufficient-evidence handling.** When a section's evidence is too sparse for its own file, fold it into an existing file in the same subfolder as a one-paragraph note. Do NOT create stub files. Do NOT silently drop the section.
6. **Process completed agents as they return** — do not wait for the entire wave before reading outputs. Update `_meta/discovered-entities.md` if the wave reveals new candidates worth promoting.
7. **Maximum 2 retries per failed mission** with a narrower prompt each time.

**Artifact:** populated `[entity-slug]/` folders. Every section in `_PRODUCT_TEMPLATE.md` is addressed in every `core` pack — either with content or with an explicit "insufficient evidence" entry naming the data gap.

### Phase 5 — Cross-entity synthesis

Compare entities by criterion across the population, **driven by the per-criterion comparison templates**.

1. **Read every `core` entity pack personally** before synthesis. Do not delegate this read.
2. **Dispatch up to 20 Cross-Category Comparison Agents in parallel per wave** — one agent per criterion (pricing, capabilities, integrations, security, audience, benchmarks, buyer-fit, sources). Each agent owns one cross-criterion folder.
3. **Each agent's brief references the matching `_COMPARISON_TEMPLATE_<criterion>.md`** which prescribes axes, matrix columns, ranking dimensions, and source expectations specific to that criterion.
4. **Each cross file** must answer: which entities are directly comparable, adjacent, or not-comparable? Which wins for which scenario? Where do sources contradict? What test would change the recommendation?
5. **Reuse the source-hierarchy + claims-ledger discipline** from `references/workflow/evidence-and-synthesis.md`.

**Artifact:** populated `_cross-<scope>/` folder. Each criterion has at minimum a `00-overall-comparison.md` plus the granular comparison files mandated by its `_COMPARISON_TEMPLATE_<criterion>.md`.

### Phase 6 — Profile pages

Write the standalone `[entity-slug].md` decision pages at the corpus root for `core` tier entities.

1. **The profile is a synthesis, not a copy.** It is the buyer's first read — a readable narrative that summarizes the evidence pack and links into it for detail.
2. Read `references/architecture/profile-pages.md` for the section ordering and the rule that distinguishes profile pages from evidence-pack `00-overview/` files.
3. Profile pages may be 300-700 lines for substantial entities. They are intentionally larger than evidence-pack files because they synthesize multiple categories.

**Artifact:** `[entity-slug].md` at corpus root for every `core` entity, each linking to its evidence pack.

### Phase 7 — Verification

Run the completion gate before declaring done.

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

- **Template coverage** — every section of `_PRODUCT_TEMPLATE.md` is addressed in every `core` entity pack; every `_COMPARISON_TEMPLATE_<criterion>.md` section is addressed in its cross folder. Sections marked "insufficient evidence" must name the specific data gap.
- Root `README.md` points to highest-signal entry points.
- Every `core` entity has a profile page linking to its evidence pack.
- Source maps and claims ledgers exist at entity and cross-category level, or absences are explained.
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

Each folder name reveals the buyer or researcher question it answers. Numeric prefixes are for scan order, not semantic naming. Filenames within each numbered subfolder are agent-chosen based on the evidence found for that specific entity.

## Worked example

A complete reference corpus exists at `/Users/yigitkonur/research/browser-system/01-ai-native-cloud-browsers/` (12 vendor evidence packs + cross-product comparisons + profile pages, 293 files, with `_meta/comparison-template.md` (246 lines) and `_meta/product-folder-research-brief.md` (162 lines) as concrete examples of the templates this skill mandates).

Read `references/workflow/worked-example-cloud-browsers.md` for an annotated walkthrough — taxonomy choices, template-authoring process, mission brief examples, and the verification artifacts that proved the corpus complete. **Mirror its discipline; never copy its slugs.**

## Output contract

Show these artifacts at the phase that produces them:

1. **Phase 0** — scope statement + corpus scale.
2. **Phase 1** — discovered entities table (tier + source URL + 1-line rationale) AND a category-understanding note.
3. **Phase 2** — resolved category list AND the maximalist `_PRODUCT_TEMPLATE.md` AND each `_COMPARISON_TEMPLATE_<criterion>.md`. Show the templates inline (or summarized with link) — they are the comprehensiveness contract for the rest of the work.
4. **Phase 3** — file-count expectation derived from templates + tree shape.
5. **Phase 4** — agent dispatch map (which agent owns which entity), then evidence-pack progress notes as agents complete.
6. **Phase 5** — cross-criterion ranking summary.
7. **Phase 6** — profile-page index.
8. **Phase 7** — completion statement (path, files, entry points, gaps, verification, template coverage).

Never batch all artifacts to the end. Each artifact should appear when its phase produces it.

## Self-correction triggers

If you notice yourself doing any of the following — **stop**:

- **Skipping Phase 2 template authoring and going straight to entity-pack research** → STOP. Templates are the comprehensiveness boundary; without them, depth varies by entity and the corpus loses comparability. Write the templates first.
- **Writing a thin, generic `_PRODUCT_TEMPLATE.md`** → STOP. The template is supposed to be maximalist and overcrowded. If it has fewer than ~30 distinct sections, you have not done the deep category pre-pass. Re-do Phase 1's category understanding and re-author the template.
- **Reusing canonical slugs (`05-security`, `07-benchmarks`) without checking the archetype** → STOP. Open `references/architecture/category-taxonomies.md` and resolve vertical-specific names.
- **Letting subagents skip a template section silently** → STOP. Every template section must be addressed in every `core` pack — content OR a named "insufficient evidence" entry. The agent brief must enforce this.
- **Hardcoding subagent filenames in the template** → STOP. Templates list *sections and questions*; agents pick filenames based on the evidence they find. Two agents may land different filenames inside the same subfolder — that is correct.
- **Dispatching more than 20 agents in one wave** → STOP. Split into waves of ≤20.
- **Summarizing Reddit as "consensus" without per-comment attribution** → STOP. Apply the audience-evidence fields from `references/workflow/evidence-and-synthesis.md`.
- **Treating a vendor's own marketing page as confirmed fact** → STOP. Re-classify per the source hierarchy. Vendor claims belong in the vendor-claim row, not the confirmed-fact row.
- **Skipping the completion gate ("looks done")** → STOP. Run the verification commands. Template-coverage audit, link check, source-ledger presence are non-negotiable.
- **Producing a single-report output ("here's the markdown report")** → STOP. This skill produces a multi-file corpus, not a single report. If the user wants a single report, redirect to `run-research`.
- **Letting the orchestrator skip reading entity packs before cross-synthesis** → STOP. The orchestrator must read each `core` pack personally before Phase 5.

## Anti-patterns

| Anti-pattern | Why it fails | Fix |
|---|---|---|
| Templates skipped or written after entity research | No comprehensiveness boundary; depth varies by agent | Phase 2 first, Phase 4 second. Always. |
| Template is thin/generic (≤15 sections) | Misses vertical-specific axes; produces shallow corpus | Re-do Phase 1 deep category pre-pass; re-author maximalist template (target ~30+ sections) |
| Template prescribes exact filenames | Removes evidence-driven naming; agents pad to fit | Template lists sections + questions; agents pick filenames |
| Stub files for sections with no evidence | Pollution; no actual content | "Insufficient evidence" note inside an existing file with the data gap named |
| Identical empty subfolders for every entity | Copy-paste research, no value | Create only evidence-justified files; address every template section in content or "insufficient evidence" entry |
| Cross-product file is a concatenation of product summaries | Doesn't compare; just appends | Comparison template prescribes axes, ranking dimensions; agents follow the template |
| Pricing copied from page without unit economics | Vendors hide overages, gating, scenario costs | Preserve native units, model scenarios, name missing variables explicitly |
| Reddit evidence presented as consensus | Bias and small samples are erased | Preserve thread, username, date, quote, bias label per audience-evidence rules |
| Source verification skipped because "it's clearly true" | Stale facts, contradicted vendor claims | Source map + claims ledger are non-optional for `core` entities |
| Profile page duplicates evidence-pack content | Duplication; no synthesis added | Profile = readable narrative + links into pack; pack = atomic evidence files |
| Single-output thinking ("write me a report") | Loses navigability and source-traceability | Multi-file corpus is the contract; ask user to confirm if pushed |

## Reference routing

Load only the references whose phase is active. Loading all references at once exhausts context.

| File | Read when |
|---|---|
| `references/architecture/research-architecture.md` | Phase 3 — designing the corpus tree, file-count expectation derivation, entity tiers, and validation gates. |
| `references/architecture/category-taxonomies.md` | Phase 2 — choosing the archetype skeleton (SaaS, OSS, dev infra, data provider, regulated, consumer) before adapting to the vertical. |
| `references/architecture/template-authoring.md` | Phase 2 — writing the maximalist `_PRODUCT_TEMPLATE.md` and per-criterion `_COMPARISON_TEMPLATE_<criterion>.md` files. The keystone reference. |
| `references/architecture/profile-pages.md` | Phase 6 — writing the standalone `<entity>.md` decision pages. |
| `references/workflow/discovery.md` | Phase 1 — finding entities, decomposing into sub-questions, tiering candidates, AND running the deep category pre-pass that feeds template authoring. |
| `references/workflow/evidence-and-synthesis.md` | Phase 4-5 — applying source hierarchy, claims ledgers, Reddit/practitioner rules, pricing/unit-economics standards, cross-category structure. |
| `references/workflow/worked-example-cloud-browsers.md` | Any phase — an annotated walkthrough of the cloud-browsers corpus, including the actual `_meta/comparison-template.md` and `_meta/product-folder-research-brief.md` artifacts. Use to mirror the *discipline*; do not copy slugs. |
| `references/agents/mission-briefs.md` | Phase 1, 4, 5 — writing prompts for discovery, entity-pack, cross-comparison, audience, source-verification, and profile-writer agents. |
| `references/agents/research-powerpack-and-explore.md` | Phase 1, 4, 5 — concrete MCP tool calls (`start-research`, `web-search`, `scrape-links`) and parallel Explore subagent dispatch patterns (≤20 per wave). |

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
