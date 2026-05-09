# Mission Briefs

How to write agent prompts for industry-scale research without losing ownership, source quality, or file budget control.

## Brief Structure

Every mission brief should contain:

1. Context.
2. Mission objective.
3. Local context to read.
4. Output ownership.
5. Research guidance.
6. Definition of done.
7. Handback format.

Include this fallback chain in every brief:

```text
If MCP tools fail, use WebFetch/WebSearch. If those fail, use curl from the shell. Do not stop because one tool is unavailable.
```

## Product Or Vendor Evidence Pack Agent

Use when one agent owns one product, vendor, framework, project, or provider. Each agent receives the Phase 2 `_meta/_PRODUCT_TEMPLATE.md` as the comprehensiveness contract.

```text
## Context

We are building a source-backed industry research corpus for [topic]. Your entity is [entity]. The goal is an audit-ready evidence pack that feeds a top-level profile page and cross-category comparison rollups. Templates set the comprehensiveness boundary — every section in `_meta/_PRODUCT_TEMPLATE.md` MUST be addressed.

## Local Context To Read (in order)

1. **`_meta/_PRODUCT_TEMPLATE.md`** — the per-entity comprehensiveness contract. This is your section list. Every section must be addressed.
2. **`_meta/comparison-template.md` or `_meta/_COMPARISON_TEMPLATE_*.md`** — so you understand what cross-comparison will need from your pack.
3. Root `README.md` and `_meta/research-plan.md` — corpus framing.
4. `_meta/methodology-and-source-policy.md` — source rules.
5. `_meta/discovered-entities.md` — entity scope and adjacent products.
6. Existing `[entity-slug].md` profile, if present.
7. Existing `[entity-slug]/` files, if present.

## Mission

Fill every section in `_meta/_PRODUCT_TEMPLATE.md` for `[entity]`. For each section:

- Provide source-backed content as one or more `01-meaningful-title.md` files in the matching subfolder, OR
- Fold the section into an existing file in the same subfolder as a one-paragraph "insufficient evidence" note that names the specific data gap

Do NOT skip any template section silently. Do NOT create stub files for sections without evidence.

## Filename rule

The template lists *sections and questions*. You decide the actual `01-meaningful-title.md` filenames within each section based on what evidence supports for THIS entity. Two agents may legitimately land different filenames in the same numbered subfolder — that is correct.

## Output Ownership

You own only:

- `[entity-slug]/[subfolder]/[your-chosen-filename].md` files
- `[entity-slug]/README.md` (the pack index)

Do not edit other entity folders. Do not rewrite root synthesis or profile pages.

## Research Guidance

Use official docs, pricing pages, changelogs, status pages, SDK repos, legal/security pages, review sites, Reddit, HN, GitHub issues, forums, and practitioner blogs. Run sub-question decomposition (3-5 questions per template section). At least 25% of searches should target negative signal: complaints, migrations, alternatives, pricing pain, reliability failures, abandoned project, license risk, "switched from".

If MCP tools fail, fall back to WebSearch/WebFetch. Do not stop because one tool is unavailable.

## Definition Of Done

- [ ] Every section in `_meta/_PRODUCT_TEMPLATE.md` is addressed in this entity's pack
- [ ] Sections without evidence have explicit "insufficient evidence" entries naming the data gap
- [ ] Every non-trivial claim cites a source URL or local source file
- [ ] Pricing/economics use native units first and normalize only when variables permit
- [ ] Practitioner evidence includes source, date, author/user, and bias label
- [ ] Source map and claims ledger exist (or absences are explained)
- [ ] No stub files; no placeholder TBD/TODO content
- [ ] `[entity-slug]/README.md` indexes every file in the pack

## Handback Format

List files created/edited, the template section each file addresses, key findings, unresolved gaps, and source-quality concerns.
```

## Cross-Category Comparison Agent

Use when one agent compares all core entities by one decision criterion. Each agent receives the matching `_meta/_COMPARISON_TEMPLATE_<criterion>.md` (or the master `_meta/_COMPARISON_TEMPLATE.md` for compact corpora) as the comprehensiveness contract.

```text
## Context

We are building cross-category rollups from completed entity evidence packs. Your job is to read the local evidence packs, verify important claims against original URLs where needed, and produce comparison files for [criterion]. The Phase 2 `_meta/_COMPARISON_TEMPLATE_<criterion>.md` prescribes the matrix axes, ranking dimensions, and required granular files.

## Local Context To Read (in order)

1. **`_meta/_COMPARISON_TEMPLATE_<criterion>.md`** — the comparison comprehensiveness contract.
2. Root `README.md` and `_meta/research-plan.md` — corpus framing.
3. `_meta/discovered-entities.md` — full entity scope.
4. All `core` entity packs, especially the `[criterion]` subfolder of each.
5. Existing `_cross-[scope]/[criterion]/` files, if any (do not overwrite without reason).

## Mission

Produce every required granular file from the template, plus the `00-overall-comparison.md` headline file. Address every required matrix axis and every required ranking dimension. Include the "tests that would change the recommendation" section.

## Output Ownership

You own only:

- `_cross-[scope]/[criterion]/00-overall-comparison.md`
- `_cross-[scope]/[criterion]/01-*.md` … (every granular file the template requires)

Do not edit entity packs. Do not edit other cross-criterion folders.

## Definition Of Done

- [ ] Every required granular file from the template exists
- [ ] Every required matrix axis is populated
- [ ] Every required ranking dimension is populated, with confidence levels
- [ ] Comparison separates direct, adjacent, and not-comparable entities
- [ ] Every row cites the relevant entity-pack file AND the original source URL with capture date
- [ ] Missing variables are stated explicitly, not guessed
- [ ] A "tests that would change the recommendation" section is included in `00-overall-comparison.md`

## Handback Format

List files created/edited, the template section each file addresses, key findings, contradictions discovered between entity packs, and unresolved gaps.
```

## Reddit And Audience Agent

Use when practitioner signal is broad enough to deserve a dedicated mission.

```text
## Context

This mission is about public practitioner experience: Reddit, HN, GitHub issues, forums, review sites, migration posts, and complaints. Official docs are useful only for checking what practitioners are reacting to.

## Mission

Create audience evidence files that preserve direct voices with attribution and separate direct evidence from adjacent evidence.

## Research Guidance

Search product-specific and category-wide terms. At least 25% of searches should target negative signal: "regret", "switched from", "pricing", "down", "support", "broken", "alternatives", "license", "abandoned", "migration".

## Definition Of Done

- [ ] Thread/source inventory includes URL, date, venue, relevance, and direct/adjacent label.
- [ ] Direct quotes include username/author, date, venue, and permalink where available.
- [ ] Promotional or founder-biased comments are labeled, not silently removed.
- [ ] Sparse evidence is stated directly.
- [ ] No non-Reddit source is over-quoted; summarize when needed.
```

## Discovery Agent

Use in **Phase 1** to find the entities that belong in the corpus, before any pack research starts. One agent per sub-question, dispatched in parallel.

```text
## Context

We are building an industry research corpus for [topic]. Phase 1 (discovery) is finding the entities that belong in the scope. The corpus will have a `_meta/discovered-entities.md` file as the canonical entity catalog. Your work feeds that file.

## Mission

Discover candidates in the [topic] category that match this sub-question:
"[sub-question text]"

Sub-questions are designed to surface different candidate clusters. Other agents are running other sub-questions in parallel. Your job is depth on this one.

## Search Approach

Run at least 5 distinct WebSearch queries with varied phrasing. Pattern shapes to use:
- "[category] best 2025"
- "[category] alternatives to [known incumbent]"
- "[category] open source"
- "[category] vs [known competitor]"
- "[category] reddit"
- "[category] launched 2024" / "Show HN [category]" for recency

For each candidate found, WebFetch the homepage to verify:
- Status: active (last update <6 months) / dead (>18 months) / waitlist (gated, no public docs) / acquired
- One-line description in their own words
- Apparent positioning (incumbent / challenger / niche / adjacent)

## Output Ownership

You own only:
- Your handback report. You do NOT write to `_meta/discovered-entities.md` directly — the orchestrator merges discovery findings.

## Definition Of Done

- [ ] At least 5 distinct WebSearch queries run with varied phrasing
- [ ] At least 3 distinct candidates returned (or explicit "no further candidates" with rationale)
- [ ] Each candidate has: name, vendor URL, one-line, status (active/dead/waitlist/acquired), apparent tier
- [ ] No marketing-only candidate included without a status check
- [ ] Adjacent vs. direct distinction stated for each candidate

## Handback Format

```markdown
## Sub-question: [text]

| Candidate | URL | Vendor | One-line | Status | Tier candidate | Adjacent? |
|---|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... | ... |

## Search log
- Query: "..." → top results: [list]
- Query: "..." → top results: [list]

## Notes
- Candidates that almost made it (and why excluded)
- Searches that returned no new candidates
- Any candidates whose status was hard to verify
```

Cap report at 600 words.
```

## Profile-Writer Agent

Use in **Phase 6** for `tiered` corpora (100+ entities) where the orchestrator cannot personally write every profile page. For `compact` and `standard` corpora, the orchestrator should write profile pages directly — this agent is for scale, not default.

```text
## Context

We are writing standalone `<entity>.md` decision pages at the corpus root. Each profile is the buyer's first read — a readable narrative synthesizing the evidence pack. The evidence pack is the source; the profile is the synthesis. Your entity is [entity].

## Local Context To Read

- `[entity-slug]/README.md` (pack index)
- Every file in `[entity-slug]/` (the full evidence pack)
- `_cross-[scope]/00-overview/00-overall-comparison.md` (where this entity ranks)
- `references/architecture/profile-pages.md` (the profile-page pattern this skill enforces)

## Mission

Write `[entity-slug].md` at corpus root, following the profile-page pattern in `references/architecture/profile-pages.md`. Section ordering:

1. One-line positioning statement
2. Research metadata (capture date, confidence, source-corpus link)
3. Executive summary (3-5 paragraphs)
4. Headline findings (5-10 bullets, each linking to an evidence-pack file)
5. Best-fit scenarios (concrete with conditions)
6. Do-not-choose-if (concrete failure scenarios)
7. Evidence-pack map (table linking each subfolder)
8. Deep profile (synthesis sections combining 2+ pack files each)
9. Numbers worth memorizing (quantitative table with caveats)
10. Open gaps (linked to `09-sources/`)
11. Sources (link to source map and claims ledger)

## Length Target

Match evidence density. Range 300-700 lines. Compact pack → shorter profile. Substantial pack → longer profile. Padding is a failure; under-synthesis is a failure.

## Linking Discipline

Every non-trivial claim must link to an evidence-pack file. Use the synthesis-with-links pattern: the profile carries the narrative; the pack carries the evidence.

## Output Ownership

You own only:
- `[entity-slug].md` at corpus root.

Do not edit the evidence pack. Do not edit other profile pages. Do not add cross-product comparison content (that lives in `_cross-<scope>/`).

## Definition Of Done

- [ ] Length is 300-700 lines (or justified outlier)
- [ ] Every section listed above is present (or its absence is justified)
- [ ] At least 30 markdown links into the evidence pack
- [ ] Best-fit and do-not-choose-if scenarios are concrete (have conditions, not generic)
- [ ] Tone is buyer-first, not vendor-pitch
- [ ] Numbers table includes caveats per row
- [ ] No content duplicated verbatim from the evidence pack

## Handback Format

Report files written, total line count, link count into the pack, and any pack files you noticed had thin or contradictory evidence (the orchestrator may need to address before final synthesis).
```

## Source Verification Agent

Use when the corpus is large enough that source integrity needs a separate pass.

```text
## Mission

Audit source quality across the corpus. Create source maps, claims ledgers, contradiction files, and follow-up test backlogs.

## Definition Of Done

- [ ] Every high-impact claim is classified as confirmed, vendor claim, practitioner report, inference, contradicted, or unverified.
- [ ] Time-sensitive facts include capture date.
- [ ] Broken, gated, JS-only, unavailable, and contradictory sources are labeled.
- [ ] Follow-up tests are concrete and buyer-actionable.
```

## Agent Wave Rules

- Dispatch independent missions in parallel.
- **Maximum 20 agents per wave.** No exceptions. For >20 entities or criteria, run multiple waves.
- Keep write scopes disjoint. Each agent owns exactly one folder.
- Do not let agents create subagents. Two-level orchestration only.
- Retry a failed mission at most twice, with a narrower prompt each time.
- Process completed agents as they return — do not wait for the slowest.
- The orchestrator must read all outputs personally before final synthesis.

## Template-Driven Briefs

All entity-pack and cross-comparison briefs reference the Phase 2 templates:

- Entity-pack agents receive `_meta/_PRODUCT_TEMPLATE.md` as the comprehensiveness contract. They MUST address every section (with content or with a one-paragraph "insufficient evidence" entry naming the data gap). They MAY pick `01-meaningful-title.md` filenames within each section based on the evidence they find.
- Cross-comparison agents receive the matching `_meta/_COMPARISON_TEMPLATE_<criterion>.md`. They MUST produce every required granular file in the template and address every required matrix axis and ranking dimension.
- Profile-writer agents receive `references/architecture/profile-pages.md` plus the entity's completed pack.

Briefs that do not pass templates to subagents produce non-comparable corpora.
