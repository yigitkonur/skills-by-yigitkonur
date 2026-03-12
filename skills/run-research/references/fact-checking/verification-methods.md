# Verification and Fact-Checking Methods

## Overview

Every piece of research output should be treated as a hypothesis until verified. This is especially important for deep_research output (which can hallucinate sources), old Reddit comments (which may be outdated), and blog posts (which may be wrong). This reference covers systematic verification methods.

## The Verification Hierarchy

### Level 1: Trivial Verification (< 30 seconds)

For facts that are easy to check and low-risk if wrong:
- Check official documentation directly
- Verify version numbers against package managers (npm, PyPI)
- Confirm API endpoints against official API reference

**When to use:** Simple factual claims ("X library supports Y feature")

### Level 2: Cross-Reference Verification (1-2 minutes)

For facts that matter and could be wrong:
- Verify with 2-3 independent sources
- Check that sources are actually independent (not citing each other)
- Confirm recency of all sources

**When to use:** Technical claims that influence decisions ("X is faster than Y")

### Level 3: Deep Verification (3-5 minutes)

For facts that are critical and hard to reverse if wrong:
- Verify with official source + 2 independent practitioners
- Check for contradicting evidence explicitly
- Verify under YOUR specific conditions (version, scale, setup)

**When to use:** Architecture decisions, security claims, performance guarantees

## What to Verify

### Always Verify

| Claim Type | Verification Method | Tool Flow |
|-----------|-------------------|-----------|
| Performance numbers | Check benchmark methodology and conditions | search_google → scrape_pages (benchmark source) |
| Version compatibility | Check official release notes | scrape_pages (changelog/releases) |
| Security recommendations | Check OWASP, NIST, or CWE references | search_google → scrape_pages (official security docs) |
| Breaking changes | Check official changelog | scrape_pages (GitHub releases) |
| Pricing / limits | Check current pricing page | scrape_pages (vendor pricing page) |
| deep_research citations | Verify cited sources exist | search_google (exact title/URL) |
| "Best practice" claims | Cross-reference with multiple sources | search_google + search_reddit |

### Verify If It Matters

| Claim Type | When to Verify | Skip If |
|-----------|---------------|---------|
| Reddit opinion | It influences a decision | You're just gathering sentiment |
| Blog tutorial steps | You're following them exactly | You're just getting inspiration |
| Library recommendations | You're adopting for production | You're doing a quick prototype |
| Configuration values | They go to production | They're for local dev only |

### Safe to Trust Without Verification

- Official documentation for current stable version
- Stack Overflow accepted answers with 100+ upvotes (still check date)
- deep_research analysis of well-known concepts (verify novel claims)
- MDN Web Docs for browser APIs
- Language specifications for language behavior

## Detecting Outdated Information

### Staleness Indicators

| Indicator | What It Means | Action |
|-----------|--------------|--------|
| No date on the page | Could be ancient | Search for the topic + current year |
| References deprecated APIs | Written before breaking change | Find current equivalent |
| Uses old syntax/patterns | Pre-dates language updates | Check current best practice |
| Mentions old versions | May not apply to current version | Verify with current version docs |
| No recent comments/engagement | Community may have moved on | Search for current discussion |

### Technology Staleness Rates

Different technologies become outdated at different rates:

| Technology Area | Half-Life of Advice | Verify If Older Than |
|----------------|--------------------|--------------------|
| JavaScript frameworks (React, Next.js) | 6-12 months | 6 months |
| CSS features | 1-2 years | 1 year |
| Node.js ecosystem | 6-12 months | 6 months |
| Python ecosystem | 1-2 years | 1 year |
| Rust ecosystem | 6-12 months | 6 months |
| Go ecosystem | 1-2 years | 1 year |
| Database features | 2-3 years | 2 years |
| Algorithms/data structures | 10+ years | Rarely |
| Design patterns | 5-10 years | 3 years |
| Security practices | 1-2 years | 1 year |
| Cloud services pricing | 3-6 months | 3 months |
| CI/CD tools | 6-12 months | 6 months |

## Verification Workflows

### Verifying deep_research Claims

deep_research can synthesize information well but may hallucinate sources or misattribute claims:

```
1. Identify key claims in deep_research output
2. For each critical claim:
   a. search_google: Search for the exact claim + source
   b. scrape_pages: Read the cited source (if it exists)
   c. Compare: Does the source actually say what deep_research claims?
3. Flag any claims that can't be verified
4. For unverified claims, search_reddit for community experience
```

### Verifying Reddit Recommendations

Reddit comments are opinions, not facts. Even highly-upvoted ones can be wrong:

```
1. Check comment date — is it still current?
2. Check commenter context — do they mention their scale, team size, use case?
3. Cross-reference: search_google for the same recommendation from official docs
4. Look for corrections in reply chains
5. Check if newer comments update or contradict the recommendation
```

### Verifying Configuration Values

Config values from blog posts, Reddit, and Stack Overflow are often environment-specific:

```
1. scrape_pages: Read official documentation for the config option
2. Compare: Does the recommended value match the documented default/range?
3. Check: Are there version-specific changes to this config?
4. Verify: Does the config make sense for YOUR scale/setup?
5. Test: Apply in non-production environment first
```

### Verifying Benchmark Data

Benchmarks are the most commonly misleading data:

```
1. Check methodology: How was the benchmark run?
2. Check conditions: Hardware, data size, concurrency, configuration
3. Check version: Was the current version benchmarked?
4. Check fairness: Were all options configured optimally?
5. Check reproducibility: Can you run the same benchmark?
6. Check relevance: Does the benchmark scenario match YOUR use case?
```

## Red Flags by Source Type

### deep_research Red Flags

- Extremely specific numbers without sources ("exactly 47% faster")
- Citations to papers or docs you can't find
- Recommendations that contradict well-known community consensus
- Overly confident language on contested topics

### Reddit Red Flags

- Single comment with no engagement as the sole source
- Comment from 3+ years ago on fast-moving technology
- Claims without specifics ("just use X, it's way better")
- Promotional tone (may be astroturfing)

### Blog Post Red Flags

- No publish date
- No author credentials or background
- Affiliate links or "sponsored" markers
- Contradicts official documentation without explanation
- Copy-pasted from another source
- Uses outdated API syntax

### Stack Overflow Red Flags

- Answer with low votes but accepted (OP may have had low standards)
- Very old answer on a frequently-changing topic
- Answer that starts with "I haven't tested this but..."
- Multiple answers with contradicting approaches and similar votes

## Triangulation Method

The gold standard for verification — confirm a claim from 3 independent source types:

```
Claim: "Redis Cluster max nodes is 1000"

Source 1 (Official): redis.io documentation → confirms or denies
Source 2 (Community): Reddit/SO → practitioners report real limits
Source 3 (Independent): Benchmark article → tested actual limits

All 3 agree → High confidence
2 of 3 agree → Moderate confidence, note the outlier
All disagree → Context-dependent, report all views
```

## Key Insight

Verification costs time but prevents costly mistakes. The 80/20 rule applies: verify the 20% of claims that will influence 80% of your decision. Don't verify obvious facts or low-stakes preferences. Do verify anything that touches production architecture, security, performance guarantees, or irreversible choices. When deep_research makes a claim that sounds too good or too specific, that's exactly when to verify.

## Steering notes from production testing

### Validation sufficiency

Sufficient when: (1) 2+ independent sources confirm each key claim, (2) no unresolved contradictions, (3) version claims verified against official docs, (4) sources are actually independent. Stop when additional calls no longer change the conclusion.

### Astroturfing detection

Red flags: vendor blog self-comparisons, new Reddit accounts praising one product, vendor-only benchmarks, comparisons omitting weaknesses.

### deep_research verification

Always verify against scraped docs: version numbers, pricing, API signatures, deprecation status, benchmarks.
