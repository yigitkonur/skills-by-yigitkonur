# Synthesizing Research Findings

Synthesis transforms scattered data into decisions. The difference between a bibliography and a recommendation is synthesis — connecting dots, resolving contradictions, and naming the variable that changes the answer.

## Source Credibility

Not all sources carry equal weight. Use this hierarchy when sources conflict:

| Source | Trust level | Best for |
|---|---|---|
| Official docs (current version) | Highest | How things should work, exact API, config syntax |
| Official changelog / release notes | Very high | What changed, breaking changes, version-specific facts |
| GitHub Issues/PRs (maintainer responses) | High | Known bugs, intended behavior, workarounds |
| Scraped benchmarks with methodology | High | Performance claims (check conditions match yours) |
| deep-research synthesis | High for analysis, moderate for specific facts | Trade-off reasoning, architectural analysis |
| Highly-upvoted Reddit (100+ votes, specific details) | Moderate-high | How things actually work in production |
| Stack Overflow accepted + highly voted | Moderate-high | Common solutions (check date) |
| Recent blog by practitioner with specifics | Moderate | Single data point, useful if detailed |
| Low-engagement Reddit | Low-moderate | Unvalidated individual opinion |
| Vendor marketing / comparison pages | Low | Extract facts only, ignore assessments |

### Recency matters more for some topics

| Topic area | Advice half-life | Verify if older than |
|---|---|---|
| JS frameworks, CSS, Node ecosystem | 6–12 months | 6 months |
| Cloud service pricing | 3–6 months | 3 months |
| Security practices | 1–2 years | 1 year |
| Database features | 2–3 years | 2 years |
| Algorithms, data structures | 10+ years | Rarely |

## Resolving Contradictions

When sources disagree, don't just pick one. Understand why they disagree:

**Different versions** — The most common cause. Source A describes v3 behavior, source B describes v4. Check which version you're using. The more recent version's docs win.

**Different scale** — "Redis is fine" (from someone running 100 req/s) vs "Redis fell over" (from someone running 100K req/s). Both are right in their context. Match to your scale.

**Different context** — "Use JWT" (stateless API) vs "Use sessions" (monolith with server-side rendering). The architecture determines which is correct. Name the context variable.

**Official docs vs community experience** — Official docs describe intended behavior. Community reveals actual behavior — including undocumented limits, silent failure modes, and configuration gotchas the docs don't mention. Trust community for "does it work in practice?" Trust docs for "how is it supposed to work?"

**deep-research vs scraped facts** — Always trust scraped official docs over deep-research claims for specific facts (version numbers, pricing, API signatures). deep-research excels at analysis and trade-off reasoning, not at being a factual database.

**Nobody agrees** — This usually means the answer is genuinely context-dependent. Don't force a single recommendation. Present the options, name the variables that determine which is best, and apply them to the user's specific situation.

## Building Consensus Maps

For complex topics with many sources, map the landscape:

**Strong consensus (80%+ agree):** Present as the recommendation. Note minority objections if they're substantive.

**Moderate consensus (50-80% agree):** Present as "the common approach, with caveats." Explicitly list dissenting perspectives and the conditions under which they apply.

**No consensus (<50% agreement):** Present as "multiple valid approaches." List trade-offs for each. Recommend based on the user's specific constraints, not on vote count.

**Evolving consensus:** Old sources say X, new sources say Y. Present Y as the current direction. Explain what changed and why (new version, new tool, changed best practice).

## Output Patterns

### For decisions
```
RECOMMENDATION: [Clear choice]
CONFIDENCE: [High/Medium/Low] based on [N sources, agreement level]
WHY: [2-3 sentences connecting evidence to recommendation]
TRADE-OFFS:
  - Choosing this: [specific benefit, sourced] but [specific drawback, sourced]
  - Alternative would give: [what you'd gain] at the cost of [what you'd lose]
CONDITIONS: This assumes [your constraints]. If [variable] changes, reconsider [alternative].
```

### For bug fixes
```
LIKELY CAUSE: [Diagnosis with evidence chain]
FIX: [Specific steps, showing before → after]
VERIFIED BY: [Which sources confirm]
CAVEATS: [When this fix doesn't apply]
FALLBACK: [What to try if this doesn't work]
```

### For evaluations
```
| Criterion | Option A | Option B | Source |
|---|---|---|---|
| [Key factor] | [Data] | [Data] | [Where from] |
...

BEST FOR [context A]: Option A because [reason]
BEST FOR [context B]: Option B because [reason]
AVOID: [Option] when [condition] because [specific evidence]
```

## Handling Uncertainty

When you don't have enough data, say so clearly:
```
WHAT I FOUND: [Summary of limited findings]
GAPS: [What I couldn't find or verify]
CONFIDENCE: Low — [N] sources, [disagreement/sparse coverage]
PRELIMINARY DIRECTION: [Best guess based on available data]
TO INCREASE CONFIDENCE: [Specific next steps]
```

When the answer is "it depends," break down the dependencies:
```
The answer depends on [2-3 specific factors]:

IF [your scale] < 10K req/s AND [team size] < 5:
  → Use [simpler option] because [reason, evidence]

IF [your scale] > 10K req/s OR [need for feature X]:
  → Use [more complex option] because [reason, evidence]

YOUR SITUATION: Based on [known constraints], [recommendation] applies.
```

## Verification Checklist

Before finalizing any recommendation, verify:

- [ ] Key claims confirmed by 2+ independent sources
- [ ] No unresolved contradictions
- [ ] Version-specific claims checked against official docs/changelog
- [ ] Sources are actually independent (not citing each other)
- [ ] Recency appropriate for the technology area
- [ ] deep-research claims about specific facts verified via scrape

**Verification effort should match stakes:** Quick fact check → 1 source is fine. Library adoption → 2-3 sources. Architecture decision → full triangulation (official docs + practitioners + independent analysis). Security claim → never trust a single source.

## When deep-research Did the Heavy Lifting

If deep-research was your final synthesis step with a rich KNOWN field, its output forms the core of your answer. Don't re-do the analysis. Instead, supplement with:
- Specific Reddit quotes it may have missed
- Exact numbers from scraped pages
- Dissenting views from comment threads
- Any facts you verified that contradict its claims

This augmentation approach is faster and more accurate than re-synthesizing from scratch.
