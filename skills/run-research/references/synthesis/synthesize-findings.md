# Synthesizing Research Findings

## Overview

Synthesis transforms raw research data (search results, scraped content, Reddit comments, deep_research analysis) into actionable recommendations. The difference between research and useful research is synthesis — connecting dots across sources, resolving contradictions, and distilling findings into decisions.

## The Synthesis Process

### Step 1: Collect and Categorize

After gathering data from multiple tools, categorize every finding:

| Category | Description | Example |
|----------|-------------|---------|
| Facts | Verifiable, objective data | "Redis max connections default: 10,000" |
| Opinions | Subjective assessments from practitioners | "Redis is easier to operate than Memcached" |
| Benchmarks | Quantitative measurements | "p99 latency: 2.1ms at 50K ops/sec" |
| Warnings | Negative experiences or known issues | "Redis Cluster has split-brain issues at 6+ nodes" |
| Recommendations | Specific actionable suggestions | "Use Redis Sentinel for HA below 100K ops/sec" |
| Contradictions | Conflicting claims from different sources | Source A: "use JSON"; Source B: "never use JSON" |

### Step 2: Weight Sources

Not all sources are equal. Apply this weighting framework:

| Source Type | Weight | Reasoning |
|-------------|--------|-----------|
| Official documentation | 0.9 | Authoritative but may lag behind reality |
| Official benchmarks | 0.8 | Controlled conditions, may not reflect production |
| deep_research synthesis | 0.7 | Good analysis but can hallucinate sources |
| Highly-upvoted Reddit (100+) | 0.6 | Community-validated but subject to bandwagon effect |
| Stack Overflow accepted answer | 0.6 | Peer-reviewed but may be outdated |
| Recent blog post by maintainer | 0.7 | Expert knowledge, current |
| Conference talk / paper | 0.7 | Well-researched but may be theoretical |
| Blog post by practitioner | 0.4 | Single data point, useful if specific |
| Low-engagement Reddit | 0.3 | Unvalidated individual opinion |
| Marketing / vendor content | 0.2 | Biased; extract facts only, ignore assessments |

### Recency Adjustment

Multiply weight by a recency factor for fast-moving technologies:

| Age | Multiplier | Apply When |
|-----|-----------|-----------|
| < 6 months | 1.0 | Always current |
| 6-12 months | 0.9 | Minor deprecation risk |
| 1-2 years | 0.7 | Check for major version changes |
| 2-3 years | 0.5 | Likely outdated for frameworks, valid for fundamentals |
| 3+ years | 0.3 | Only trust for language fundamentals and algorithms |

### Step 3: Resolve Contradictions

When sources disagree, use this resolution hierarchy:

```
Contradiction detected:
│
├── Both sources are from official docs
│   └── Check versions — the more recent one wins
│
├── Official docs vs community experience
│   └── Community experience often reveals undocumented behavior
│   └── Trust community for "does it work?" but docs for "how should it work?"
│
├── Two community sources disagree
│   ├── Check their contexts — are they talking about the same scale/version/setup?
│   ├── Check engagement — higher votes generally (not always) indicate more validation
│   ├── Check recency — newer information may reflect fixes or changes
│   └── If still unresolved → both viewpoints may be valid in different contexts
│
├── deep_research vs scraped facts
│   └── Always trust scraped facts over deep_research claims
│   └── deep_research synthesizes; scrape_pages extracts
│
└── Nobody agrees
    └── This usually means the answer is context-dependent
    └── Report all perspectives with their contexts
```

### Step 4: Build a Consensus Map

For complex topics, map the consensus landscape:

```
Strong consensus (80%+ sources agree):
  → Present as the recommended approach
  → Note any minority objections worth considering

Moderate consensus (50-80% agree):
  → Present as "the common approach, with caveats"
  → Explicitly list the dissenting perspectives

No consensus (< 50% agreement):
  → Present as "multiple valid approaches"
  → List trade-offs for each approach
  → Recommend based on the user's specific constraints

Evolving consensus:
  → Old sources say X, new sources say Y
  → Present Y as the current direction
  → Explain why the shift happened
```

### Step 5: Distill into Recommendations

Transform your synthesis into one of these output formats:

#### For decisions:
```
RECOMMENDATION: [clear choice]
CONFIDENCE: [high/medium/low] based on [N sources, consensus level]
KEY TRADE-OFFS:
  - Pro: [specific benefit, sourced]
  - Con: [specific drawback, sourced]
CONDITIONS: This recommendation assumes [constraints]
ALTERNATIVES: If [condition changes], consider [alternative]
```

#### For bug fixes:
```
LIKELY CAUSE: [diagnosis based on evidence]
FIX: [specific steps]
VERIFIED BY: [which sources confirm this fix]
CAVEATS: [conditions where this fix doesn't apply]
FALLBACK: If this doesn't work, try [alternative approach]
```

#### For evaluations:
```
RANKING: [ordered list with scores]
CRITERIA: [what the ranking is based on]
BEST FOR [context A]: [option]
BEST FOR [context B]: [different option]
AVOID: [option] because [specific reason from research]
```

## Synthesis Patterns for Common Scenarios

### Pattern: Conflicting Benchmarks

When different sources report different performance numbers:

1. Check benchmark conditions (hardware, data size, configuration)
2. Check versions tested (performance varies significantly across versions)
3. Prefer benchmarks that match YOUR conditions
4. If no match, report ranges: "Performance varies from X to Y depending on [factor]"

### Pattern: "Best Practice" vs Production Reality

When official guidance contradicts Reddit experiences:

1. Official guidance is the ideal; Reddit shows the practical
2. Present both: "The recommended approach is X, but practitioners report Y"
3. The gap often reveals missing context in the docs (setup requirements, scale thresholds)
4. When the gap is large, the official guidance may be aspirational

### Pattern: Technology Evolution

When advice changes over time:

1. Identify the inflection point (version, year, ecosystem change)
2. Present current state, not historical state
3. Note: "Prior to [version/year], the recommendation was X. Since [change], Y is preferred because [reason]"
4. Flag if the evolution is ongoing (unstable recommendation)

## Source Quality Signals

### High-Quality Source Indicators

- Specific version numbers mentioned
- Concrete metrics (not just "faster" but "2.3x faster at 10K requests/sec")
- Acknowledgment of trade-offs and limitations
- Reproducible benchmarks with methodology described
- Author has verifiable expertise (commits to the project, company affiliation)
- Recently updated (within 6 months for fast-moving tech)

### Low-Quality Source Indicators

- No dates or version numbers
- Vague claims ("much faster", "way better", "everyone uses")
- No acknowledgment of trade-offs
- Affiliate links or sponsored content markers
- Copy-pasted content from other sources
- Contradicts official documentation without explanation
- Author has no verifiable expertise

## Handling Uncertainty

### When You Don't Have Enough Data

```
Insufficient data for confident recommendation.
WHAT I FOUND: [summary of limited findings]
GAPS: [what I couldn't find]
NEXT STEPS:
  1. [specific search to fill gap 1]
  2. [specific search to fill gap 2]
PRELIMINARY LEANING: [tentative direction based on available data]
```

### When the Answer is "It Depends"

Don't just say "it depends." Break down the dependencies:

```
The answer depends on [2-3 specific factors]:

IF [factor A = value 1]:
  → Recommendation: [X]
  → Because: [reason from source]

IF [factor A = value 2]:
  → Recommendation: [Y]
  → Because: [reason from source]

YOUR SITUATION: Based on [known constraints], [X/Y] applies.
```

## Key Insight

Synthesis is not summarization. Summarization condenses information; synthesis creates new understanding by connecting disparate pieces. The most valuable synthesis resolves contradictions, surfaces hidden consensus, and translates general advice into context-specific recommendations. A research output that lists sources without synthesis is a bibliography, not a recommendation.

## Steering notes from production testing

### Source reconciliation

Before synthesis, map: all agree (high confidence), most agree (medium), conflict (needs resolution), single source (low).

### When deep_research covers it

If deep_research was final and covers all claims with sources, use it as synthesis core. Supplement with Reddit quotes and scraped facts it missed. Don't re-synthesize from scratch.

### Confidence language

| Agreement | Language |
|---|---|
| All agree + official docs | "Use X" |
| 2+ agree, no contradictions | "X is likely best because..." |
| Sources conflict | "Depends on [variable]. If A, use X. If B, use Y." |
| Single source | "X appears suitable, verify [claims]" |

### Consensus stability

Fast-moving ecosystems: add shelf-life warning. Static domains (databases, crypto): no warning needed.
