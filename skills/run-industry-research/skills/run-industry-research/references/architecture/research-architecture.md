# Research Architecture

How to design a large industry research corpus before dispatching researchers or creating files.

## The Core Shape

A strong industry corpus has four layers:

| Layer | Purpose | Typical files |
|---|---|---|
| Root entry point | Shows what to read first and what the corpus covers. | `README.md` |
| Meta | Scope, methodology, file budget, discovery list, templates, briefs. | `_meta/*.md` |
| Entity evidence packs | Deep product, vendor, framework, project, company, or provider research. | `[entity]/00-*` through `[entity]/09-*` |
| Cross-category synthesis | Comparisons by buyer criterion, source verification, rankings, contradictions. | `_cross-product/*` or `_cross-ecosystem/*` |

Use top-level `[entity].md` files when the user wants readable main pages. These should summarize and link to the detailed evidence pack, not duplicate every detail.

## File-count expectation

There is **no fixed hard cap** on file count. The comprehensiveness boundary comes from the Phase 2 templates (`_meta/_PRODUCT_TEMPLATE.md` plus the per-criterion comparison templates), not from a numeric cap. The file-count expectation is derived from the templates and used as a planning estimate, not a constraint.

Compute the estimate after Phase 2 (templates locked):

```text
total_files ≈
  root_and_meta_files
  + core_entity_count × product_template_section_count
  + secondary_entity_count × (compact_section_count)
  + cross_criterion_count × cross_template_required_file_count
  + profile_page_count
  + discovery / claims-ledger / open-gaps files
```

Reasonable expectations by corpus scale:

| Corpus scale | Entity count | Core entities | Avg files per core entity | Cross-criterion folders | Typical total range |
|---|---:|---:|---:|---:|---:|
| Compact | 1-10 | all | 8-20 | 5-8 | 80-200 |
| Standard | 10-40 | 10-25 | 12-25 | 8-12 | 150-500 |
| Deep | 40-100 | 20-60 | 15-30 | 10-15 | 500-2000 |
| Tiered | 100+ | top 20-50 | 15-30 | 10-15 | 1000-3000 |

If the estimate is much larger than the user expected:

1. **Tier aggressively.** Demote entities from `core` to `secondary` if their evidence is thin. Demote `secondary` to `discovered-only` if surfaces are vendor-marketing-only.
2. **Tighten the templates.** A truly maximalist template still has a ceiling — if your `_PRODUCT_TEMPLATE.md` lists 80 sections, ask whether 30 of them could collapse without losing the buyer's decision.
3. **Combine narrow files.** If two adjacent template sections each have 1-2 paragraphs of evidence, fold them into one file with two H2 headers.
4. **Move long-tail discovery to `_meta/discovered-entities.md`.** Don't build packs for entities that don't deserve them.

The orchestrator sets the user's expectation in Phase 0 (`compact` / `standard` / `deep` / `tiered`) and adjusts in Phase 3 once templates are locked. **The templates' minimum coverage is the discipline; the file count is the consequence.**

## Standard Tree

```text
[topic-slug]/
|-- README.md
|-- _meta/
|   |-- research-plan.md
|   |-- methodology-and-source-policy.md
|   |-- discovered-entities.md
|   |-- file-budget.md
|   `-- templates-or-briefs.md
|-- _cross-[scope]/
|   |-- 00-overview/
|   |   |-- 00-overall-comparison.md
|   |   |-- 01-category-map.md
|   |   |-- 02-ranking-by-scenario.md
|   |   `-- 03-evidence-grade-scorecard.md
|   |-- [criterion-one]/
|   |   |-- 00-overall-comparison.md
|   |   `-- 01-specific-question.md
|   `-- 09-sources/
|       |-- 00-overall-comparison.md
|       |-- 01-source-map.md
|       |-- 02-claims-ledger.md
|       `-- 03-contradictions-and-gaps.md
|-- [entity-slug]/
|   |-- 00-overview/
|   |-- [context-one]/
|   |-- [context-two]/
|   `-- 09-sources/
`-- [entity-slug].md
```

## Entity Tiers

| Tier | Criteria | Output |
|---|---|---|
| Core | Directly comparable, high buyer relevance, enough sources, likely decision candidate. | Full evidence pack plus main profile. |
| Secondary | Relevant but adjacent, early, region-specific, or source-limited. | Compact profile or fewer context files. |
| Discovered-only | Mentioned in searches but not worth full treatment yet. | Row in `_meta/discovered-entities.md`. |

Promote a secondary entity to core when it changes rankings, pricing economics, adoption interpretation, or category boundaries.

## Main Profile Pattern

Each top-level `[entity].md` should be a readable synthesis:

1. Research metadata.
2. Executive summary.
3. Evidence pack map.
4. Positioning and taxonomy.
5. Deep profile.
6. Pricing, sustainability, or unit economics where relevant.
7. Product, platform, project, or capability analysis.
8. Integrations or ecosystem.
9. Operations, maintenance, reliability, or support.
10. Security, compliance, licensing, governance, or legal risk.
11. Audience and practitioner signal.
12. Benchmarks, performance, or reproducibility.
13. Buyer/adoption fit.
14. Source map.
15. Open gaps and follow-up tests.

Rename sections where the vertical requires it, but keep the evidence logic.

## Validation Commands

Run equivalent checks before completion:

```bash
find [topic-slug] -type f | wc -l
find [topic-slug] -name '.DS_Store' -o -name 'Thumbs.db' -o -name '*.tmp' -o -name '*.bak' -o -name '*~'
```

Run a local markdown link checker. A minimal Ruby version:

```bash
ruby - <<'RUBY'
require 'pathname'
root = Pathname.new(ARGV.fetch(0))
missing = []
Dir[root.join('**/*.md')].sort.each do |file|
  text = File.read(file)
  text.scan(/\[[^\]]+\]\(([^)]+)\)/) do |m|
    target = m[0]
    next if target =~ /\A(?:https?:|mailto:|#)/
    path = target.split('#', 2).first
    next if path.nil? || path.empty?
    full = Pathname.new(file).dirname.join(path.gsub('%20', ' ')).cleanpath
    missing << [file, target, full.to_s] unless full.exist?
  end
end
puts "missing_local_links=#{missing.size}"
missing.each { |file, target, full| puts "#{file} -> #{target} => #{full}" }
RUBY
```

## Common Architecture Failures

| Failure | Fix |
|---|---|
| Every product has identical empty folders. | Create only evidence-justified files. Address every template section in content OR explicit "insufficient evidence" entry. |
| Cross-product comparisons repeat product summaries. | Compare by buyer criterion and cite product packs. Comparison template prescribes axes; agents follow the template. |
| Pricing is copied from pages without unit economics. | Preserve native units, normalize where possible, state missing variables. |
| Reddit evidence is summarized as consensus. | Preserve thread, username, date, quote, and bias label. |
| Source verification is missing. | Add source maps, claims ledgers, contradictions, and open test backlogs. |
| Templates skipped or written after entity research. | Phase 2 first, Phase 4 second. Always. Re-author templates from the deep category pre-pass if they were written prematurely. |
| Subagents skip template sections silently. | Mission brief explicitly requires every template section addressed in content or in an "insufficient evidence" entry. |
| Tree size surprises the user. | Set expectation in Phase 0; refine after Phase 2 templates lock; adjust by tiering or template tightening, not by file-cap pressure. |
