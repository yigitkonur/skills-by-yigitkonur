---
name: run-industry-research
description: Use skill if you are researching an industry, market, SaaS, open-source, or product category and need a source-backed corpus with comparisons.
---

# Run Industry Research

Run deep, source-backed industry research into corpora with product or project evidence packs, cross-category comparisons, Reddit/practitioner context, and audit-ready synthesis.

## Trigger Boundary

Use this skill when the user asks for:

- comprehensive industry research, market landscape, category map, or competitive landscape
- deep product-category audits with many vendors, tools, frameworks, or open-source projects
- SaaS research, open-source technology ecosystem research, developer-tool landscape research, or provider comparison
- a reusable research folder with product pages, comparison rollups, pricing/unit economics, source ledgers, Reddit/audience evidence, and master summaries

Do not use this skill for:

- a single technical question or architecture decision; use `run-research`
- finding GitHub repositories only; use `run-github-scout`
- codebase-only analysis, code review, or implementation work
- a quick one-page market summary where a full corpus would be overkill

## Hard Limits

- Persistent research output must stay under **1000 files** unless the user explicitly raises the cap.
- No placeholder files. Every created file must contain source-backed, independently useful content.
- Design the output architecture before dispatching agents or writing product files.
- Use context-specific category names. Do not blindly reuse `01-pricing`, `05-security`, or `07-benchmarks` when the vertical needs different names.
- Separate confirmed facts, vendor/project claims, practitioner evidence, and inference.
- Search before synthesis. Never treat snippets as evidence.

## Decision Tree

1. **Clarify outcome if missing**
   - Ask: "What will you do with this research?"
   - Also clarify target audience, geography, and whether the result is for buying, strategy, implementation, investment, or content.
   - Skip questions when the user's intent is already clear.
2. **Choose corpus scale**
   - `compact`: 1-10 entities, 15-80 files.
   - `standard`: 10-40 entities, 80-350 files.
   - `deep`: 40-100 entities, 250-900 files.
   - `tiered`: 100+ entities. Keep full evidence packs for top-tier entities only; put long-tail discoveries in `_meta/discovered-*.md`.
3. **Choose research archetype**
   - SaaS/vendor/product category.
   - Open-source technology ecosystem.
   - Developer infrastructure or cloud platform market.
   - Data/API/provider market.
   - Regulated industry or compliance-heavy market.
   - Consumer app, hardware, or content ecosystem.
   - Read `references/category-taxonomies.md` and pick or adapt one taxonomy.
4. **Design file budget and architecture**
   - Read `references/research-architecture.md`.
   - Produce a tree plan with file-count budget before creating files.
   - Include `_meta/`, entity folders, top-level entity profiles, `_cross-product/` or `_cross-ecosystem/`, and a root `README.md`.
5. **Write mission briefs**
   - Read `references/mission-briefs.md`.
   - Assign each agent one product, project, domain, or cross-cutting criterion.
   - Include exact output ownership, source expectations, fallback chain, and definition of done.
6. **Research and write**
   - Use `run-research` methodology: planner, diverse web queries, Reddit/practitioner searches, scrape/read sources, loop on gaps.
   - Write evidence packs as research lands. Do not wait for all agents before processing completed outputs.
7. **Synthesize**
   - Read all local outputs personally.
   - Create root README, main entity profiles, cross-category rollups, source map, claims ledger, contradictions, and next-test backlog.
   - Read `references/evidence-and-synthesis.md` before final synthesis.
8. **Verify**
   - Count files; fail if over the agreed cap.
   - Run local markdown link checks.
   - Check every entity has required minimum evidence or is explicitly listed as long-tail/insufficient-evidence.
   - Check cross-product rollups cite both local files and original source URLs where possible.

## Output Architecture Contract

Default shape:

```text
[topic-slug]/
|-- README.md
|-- _meta/
|   |-- research-plan.md
|   |-- methodology-and-source-policy.md
|   |-- discovered-entities.md
|   `-- file-budget.md
|-- _cross-[scope]/
|   |-- 00-overview/
|   |-- [criterion-a]/
|   |-- [criterion-b]/
|   `-- 09-sources/
|-- [entity-slug]/
|   |-- 00-overview/
|   |-- [entity-specific-context]/
|   `-- 09-sources/
`-- [entity-slug].md
```

Resolve bracketed names into concrete kebab-case folder names before work starts. Each folder name must reveal the buyer or researcher question it answers.

## Required Evidence Layers

Every full entity evidence pack should usually include:

- overview, taxonomy, positioning, and evidence grade
- pricing, unit economics, funding, or sustainability when relevant
- product/platform/project capabilities
- integrations/ecosystem/developer experience
- operations, reliability, maintenance, or release posture
- security, compliance, licensing, governance, or risk
- audience, Reddit, GitHub issues, reviews, forums, or community voice
- benchmarks, performance, test plans, or reproducibility
- buyer fit, adoption fit, alternatives, and no-fit cases
- source map, claims ledger, contradictions, open gaps, and follow-up tests

Rename these layers for the vertical. For example, open-source research should use `license-governance-security`, not generic `security`; data-provider research should use `coverage-quality-rights`, not generic `platform`.

## Completion Gate

Do not call the corpus complete until all are true:

- File count is under cap and recorded in `_meta/file-budget.md`.
- Root `README.md` points to the highest-signal entry points.
- Every main profile links to its evidence pack.
- Cross-category rollups exist for every important decision criterion.
- Source map and claims ledger exist at entity and cross-category level, or the absence is explained.
- Reddit/practitioner evidence is direct when available, labeled adjacent when sparse, and never presented as consensus without attribution.
- All stale placeholders, broken local links, hidden junk files, and unresolved naming mismatches are fixed or documented.

## Reference Routing

| File | Read when |
|---|---|
| `references/research-architecture.md` | Designing the corpus tree, file budget, entity tiers, and validation gates. |
| `references/category-taxonomies.md` | Choosing context-specific folder/category names for SaaS, open source, developer tools, data providers, regulated industries, or consumer markets. |
| `references/mission-briefs.md` | Writing high-quality prompts for product, project, cross-product, Reddit, and source-verification agents. |
| `references/evidence-and-synthesis.md` | Applying source hierarchy, Reddit rules, pricing/unit-economics standards, source maps, claims ledgers, and final synthesis checks. |

## Output Contract

Show these artifacts as they are produced:

1. Scope classification and chosen corpus scale.
2. File-budget plan with expected entity count and maximum file count.
3. Output architecture tree with context-specific category names.
4. Agent mission map, if agents are used.
5. Research progress notes with source gaps and retry decisions.
6. Final corpus summary: file count, entry points, critical findings, unresolved gaps, and verification results.

## Guardrails

- Do not make landing-page-style reports. Build the actual research corpus.
- Do not collapse product facts, pricing, practitioner sentiment, and source verification into one undifferentiated file.
- Do not create raw dump folders unless the user explicitly asks. Summarize and source-map instead.
- Do not use the same category names for every vertical when better names are available.
- Do not outsource final synthesis. The orchestrator reads the files and resolves contradictions personally.
- Do not exceed 8 researcher agents per wave unless the user explicitly authorizes a larger wave.
