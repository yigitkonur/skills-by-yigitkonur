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

Use when one agent owns one product, vendor, framework, project, or provider.

```text
## Context

We are building a source-backed industry research corpus for [topic]. The final tree has a hard cap of [N] files, so create only evidence-justified files. Your entity is [entity]. The goal is not a generic overview; it is an audit-ready evidence pack that can feed a top-level profile and cross-category comparison rollups.

## Mission

Create or enhance [entity-slug]/ with independently useful evidence files covering the categories assigned below. Separate confirmed facts, vendor/project claims, practitioner evidence, and inference.

## Local Context To Read

- Root README.
- `_meta/research-plan.md`.
- `_meta/methodology-and-source-policy.md`.
- Existing `[entity-slug].md`, if present.
- Existing `[entity-slug]/` files, if present.
- Relevant `_cross-[scope]/` files if they already exist.

## Output Ownership

You own only:

- `[entity-slug]/[context]/01-meaningful-title.md`
- `[entity-slug]/README.md`

Do not edit other entity folders. Do not rewrite root synthesis unless asked.

## Research Guidance

Use official docs, pricing pages, changelogs, status pages, SDK repos, legal/security pages, review sites, Reddit, HN, GitHub issues, forums, and practitioner blogs. Search for negative signal: complaints, migrations, alternatives, pricing pain, reliability failures, abandoned project, license risk, and "switched from".

## Definition Of Done

- [ ] Every non-trivial claim cites a source URL or local source file.
- [ ] Pricing/economics use native units first and normalize only when variables permit.
- [ ] Practitioner evidence includes source, date, author/user, and bias label where possible.
- [ ] Source map and claims ledger exist or are explicitly marked insufficient evidence.
- [ ] No placeholder files were created.

## Handback Format

List files created/edited, key findings, unresolved gaps, and source-quality concerns.
```

## Cross-Category Comparison Agent

Use when one agent compares all core entities by one decision criterion.

```text
## Context

We are building cross-category rollups from completed entity evidence packs. Your job is not to re-research every entity from scratch; it is to read the local evidence packs, verify important claims against original URLs where needed, and produce comparison files for [criterion].

## Mission

Create `_cross-[scope]/[criterion]/00-overall-comparison.md` plus any justified granular files. The output must help a buyer, strategist, or technical lead decide how entities rank for [criterion].

## Local Context To Read

- Root README.
- `_meta/research-plan.md`.
- `_meta/discovered-entities.md`.
- All core entity profiles.
- Relevant context folders inside each core entity.

## Output Ownership

You own only:

- `_cross-[scope]/[criterion]/00-overall-comparison.md`
- `_cross-[scope]/[criterion]/01-*.md`

## Definition Of Done

- [ ] Comparison separates direct, adjacent, and not-comparable entities.
- [ ] Rankings include confidence levels and conditions that could change them.
- [ ] Every row cites local evidence and original source URLs where available.
- [ ] Missing variables are stated instead of guessed.
- [ ] A "tests that would change the recommendation" section is included.
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
- Default maximum is 8 agents per wave.
- Keep write scopes disjoint.
- Do not let agents create subagents.
- Retry a failed mission at most twice, with a narrower prompt each time.
- The orchestrator must read all outputs personally before final synthesis.
