# Research Strategy Patterns

## Overview

Three strategy patterns cover 95% of research tasks. Each pattern defines which tools to use, in what order, and why that order matters. Picking the wrong pattern wastes tool calls; picking the right one gets you to an answer in 3–5 steps.

## Pattern Selection Decision Tree

```
What is the research task?
│
├── I have a specific error or bug
│   └── Pattern A: Bug Fix Research
│       Start with search_google (error messages are highly searchable)
│
├── I need to make a decision between options
│   └── Pattern B: Decision / Architecture Research
│       Start with deep_research (need synthesis before facts)
│
├── I need to evaluate a library or dependency
│   └── Pattern C: Library / Dependency Research
│       Start with search_google (discover candidates first)
│
├── I need to understand how something works
│   └── Pattern D: Understanding / Learning Research
│       Start with deep_research (need conceptual framework)
│
├── I need to verify a claim or check a fact
│   └── Pattern E: Fact Verification Research
│       Start with search_google (find authoritative sources)
│
└── I need to stay current on a technology
    └── Pattern F: Landscape Scan
        Start with search_reddit (community pulse check)
```

## Pattern A: Bug Fix Research

**Use when:** Runtime error, compiler error, crash, unexpected behavior, deprecation warning, build failure.

**Why this order:** Error messages are the most searchable content on the internet. Start with exact-match searches, then extract fixes, then validate.

### Steps

```
Step 1: search_google (5-7 keywords)
   - Exact error message in "quotes"
   - Error message + framework/language version
   - Error message + "fix" or "solution"
   - Error code (if any) + library name
   - Simplified error description without project-specific paths
   Target: 50-70 candidate URLs

Step 2: scrape_pages (top 3-5 URLs)
   - Extract: "error cause | fix steps | code example | version affected | workarounds"
   Target: Concrete fix candidates

Step 3: search_reddit (3-5 queries)
   - "[error message]" in relevant subreddit
   - "[library] [symptom]" for broader matches
   - "[library] breaking change [version]" if version-related
   Target: Community experiences, edge cases

Step 4: DONE for most bugs.
   If still unresolved:
   → deep_research with the buggy code file attached
   → Ask for systematic diagnosis, not just "what's wrong"
```

**Tool calls:** 3-4. **Coverage:** StackOverflow, GitHub Issues, blogs, Reddit.

### When to Escalate

- Error message returns zero relevant results → broaden search terms
- Fix doesn't work → search_reddit for "tried X didn't work"
- Bug involves multiple systems → deep_research with all files attached
- Bug is intermittent → deep_research with reproduction details

## Pattern B: Decision / Architecture Research

**Use when:** Choosing between options, designing a system, evaluating trade-offs, making irreversible decisions.

**Why this order:** Decisions need synthesis first (deep_research), then community validation (Reddit), then official facts (search_google + scrape_pages).

### Steps

```
Step 1: deep_research (2-3 structured questions)
   - Use the full structured template
   - Attach relevant code files showing current architecture
   - Ask about trade-offs, failure modes, and scaling concerns
   Target: Multi-dimensional analysis with recommendations

Step 2: search_reddit (5-7 queries)
   - "[option A] vs [option B]" in relevant subreddits
   - "[option A] production experience"
   - "[option A] regret" or "switched from [option A]"
   - "best [category] for [your constraints]"
   Target: Practitioner validation of deep_research claims

Step 3: fetch_reddit (5-7 best threads)
   - fetch_comments=true, use_llm=false
   - Look for dissenting comments and experience-based warnings
   Target: Detailed counter-arguments and edge cases

Step 4: search_google (3-5 queries for official sources)
   - Official benchmarks, documentation, migration guides
   - Site-targeted: site:docs.x.com, site:github.com/x
   Target: Authoritative facts to resolve remaining uncertainties

Step 5: scrape_pages (3-5 authoritative URLs)
   - Extract: "features | limitations | pricing | compatibility | migration path"
   Target: Concrete data points for final decision
```

**Tool calls:** 5. **Coverage:** Expert analysis, community validation, official docs.

### Decision Matrix Construction

After completing Pattern B, build a decision matrix:

| Criterion | Option A | Option B | Source |
|-----------|----------|----------|--------|
| Performance | [metric] | [metric] | deep_research / scrape_pages |
| Team familiarity | [rating] | [rating] | Your knowledge |
| Community support | [rating] | [rating] | search_reddit |
| Migration cost | [estimate] | [estimate] | deep_research |
| Risk factors | [list] | [list] | fetch_reddit (dissenting views) |

## Pattern C: Library / Dependency Research

**Use when:** Evaluating a library, finding alternatives, checking maintenance health, comparing competing solutions.

**Why this order:** Start broad (discover candidates), then get community signal, then extract facts, then synthesize.

### Steps

```
Step 1: search_google (5-7 queries)
   - "[lib A] vs [lib B] [year]"
   - "best [category] library [language] [year]"
   - "[lib] alternatives"
   - "[lib] benchmark" or "[lib] performance"
   - site:github.com "[lib]" stars
   Target: Candidate list and comparison resources

Step 2: search_reddit (5-7 queries)
   - "[lib] production experience" in language-specific subreddits
   - "[lib] problems" or "[lib] issues"
   - "switched from [lib]" or "migrated from [lib]"
   - "r/[language] [category] recommendation"
   Target: Real-world adoption stories and warnings

Step 3: scrape_pages (3-5 URLs)
   - GitHub repos: "stars | last commit | open issues | contributors"
   - Package pages: "downloads | version | dependencies | size"
   - Doc sites: "features | API surface | examples | limitations"
   Target: Quantitative metrics for comparison

Step 4: deep_research (1-2 questions)
   - Synthesize all findings into recommendation with your constraints
   - Attach your code to get integration-specific advice
   Target: Final recommendation with trade-off analysis
```

**Tool calls:** 4. **Coverage:** Comparisons, community trust, maintenance health, fit.

## Pattern D: Understanding / Learning Research

**Use when:** Need to understand how something works internally, learn a new concept, or build a mental model.

**Why this order:** Start with synthesis (deep_research explains concepts well), then verify with authoritative sources.

### Steps

```
Step 1: deep_research (1-2 questions)
   - "How does [X] work internally?"
   - Include WHAT I KNOW to skip basics
   Target: Conceptual framework and mental model

Step 2: search_google (3-5 queries)
   - "[X] internals explained"
   - "[X] architecture deep dive"
   - "site:[official-docs] [X] how it works"
   Target: Authoritative explanations to verify deep_research

Step 3: scrape_pages (2-3 URLs)
   - Extract: "architecture | algorithm | data flow | edge cases"
   Target: Detailed technical explanations
```

**Tool calls:** 3. **Coverage:** Synthesized explanation + authoritative verification.

## Pattern E: Fact Verification Research

**Use when:** Need to verify a specific claim, check if something is still current, or confirm a technical detail.

**Why this order:** Go directly to authoritative sources. Don't synthesize — verify.

### Steps

```
Step 1: search_google (3-5 queries)
   - "[claim] [official source]"
   - site:[official-docs.com] "[specific feature]"
   Target: Authoritative source URLs

Step 2: scrape_pages (2-3 URLs)
   - Extract: "[specific fact] | version | date | conditions | caveats"
   Target: Exact facts with context

Step 3: (Optional) search_reddit if claim is contested
   - "[claim] true or false"
   - "[claim] [year]"
   Target: Community consensus on contested claims
```

**Tool calls:** 2-3. **Coverage:** Authoritative facts + optional community validation.

## Pattern F: Landscape Scan

**Use when:** Staying current on a technology area, checking what's changed recently, exploring what's new.

**Why this order:** Reddit is the best pulse-check for what's currently happening in a technology space.

### Steps

```
Step 1: search_reddit (5-7 queries)
   - "best [category] [year]"
   - "[technology] state of [year]"
   - "what changed in [technology] [year]"
   Target: Current community sentiment and trends

Step 2: fetch_reddit (3-5 top threads)
   - fetch_comments=true, use_llm=false
   Target: Detailed current opinions

Step 3: search_google (3-5 queries)
   - "[technology] roadmap [year]"
   - "[technology] changelog latest"
   Target: Official announcements and roadmaps

Step 4: scrape_pages (2-3 URLs)
   - Extract: "new features | deprecations | roadmap | release dates"
   Target: Concrete upcoming changes
```

**Tool calls:** 4. **Coverage:** Community pulse + official announcements.

## Pattern Mixing

Complex research tasks often require combining patterns. Common combinations:

| Starting Pattern | When to Mix | Add Pattern |
|-----------------|-------------|------------|
| Pattern A (Bug) | Fix doesn't work after 3 attempts | Pattern B (deeper analysis) |
| Pattern B (Decision) | Need library-specific evaluation | Pattern C (for each option) |
| Pattern C (Library) | Found a critical bug in a candidate | Pattern A (for that bug) |
| Pattern D (Understanding) | Concept has multiple competing approaches | Pattern B (to choose) |
| Pattern E (Verification) | Claim is contested | Pattern B (deeper analysis) |

## Effort Calibration

Match research depth to question importance:

| Question Impact | Pattern | Tool Calls | Time |
|----------------|---------|------------|------|
| Quick factual check | E | 2-3 | 1-2 min |
| Standard bug fix | A | 3-4 | 2-3 min |
| Library evaluation | C | 4 | 3-5 min |
| Architecture decision | B | 5 | 5-8 min |
| Major technology choice | B + C | 8-10 | 10-15 min |

## Key Insight

The pattern you choose determines your research efficiency more than the queries you write. A perfectly crafted query in the wrong pattern wastes a tool call. The two most common mistakes: using Pattern A (bug fix) when Pattern B (decision) is needed (symptom: surface-level fix that doesn't address root cause), and using Pattern B when Pattern E (verification) suffices (symptom: over-researching a simple factual question).
