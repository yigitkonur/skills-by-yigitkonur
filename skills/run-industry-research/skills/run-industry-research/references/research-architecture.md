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

## File Budget

The default hard cap is 1000 persistent files.

Before writing, estimate:

```text
total_files =
  root_and_meta_files
  + entity_count * average_entity_files
  + cross_context_count * average_cross_files
  + top_level_profile_count
```

Recommended budgets:

| Corpus scale | Entity count | Full entities | Avg files per full entity | Cross files | Target total |
|---|---:|---:|---:|---:|---:|
| Compact | 1-10 | all | 8-20 | 10-30 | 15-80 |
| Standard | 10-40 | 10-25 | 10-25 | 30-80 | 80-350 |
| Deep | 40-100 | 20-60 | 10-30 | 50-150 | 250-900 |
| Tiered | 100+ | top 20-50 | 10-25 | 50-150 | under 1000 |

If the estimate exceeds 1000:

1. Tier entities into `core`, `secondary`, and `discovered-only`.
2. Give full evidence packs only to `core`.
3. Give compact profiles to `secondary`.
4. Put discovered-only entities in `_meta/discovered-entities.md`.
5. Combine narrow context files into one broader file only when it stays independently useful.

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
| Every product has identical empty folders. | Create only evidence-justified files. |
| Cross-product comparisons repeat product summaries. | Compare by buyer criterion and cite product packs. |
| Pricing is copied from pages without unit economics. | Preserve native units, normalize where possible, state missing variables. |
| Reddit evidence is summarized as consensus. | Preserve thread, username, date, quote, and bias label. |
| Source verification is missing. | Add source maps, claims ledgers, contradictions, and open test backlogs. |
| Tree exceeds 1000 files. | Tier entities and collapse long-tail into discovery lists. |
