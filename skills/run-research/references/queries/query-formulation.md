# Query Formulation Guide

## Overview

The quality of your research depends on the quality of your queries. A well-formulated query finds the right answer in one search. A poorly formulated query burns 3–5 tool calls finding nothing useful. This reference covers query formulation for every tool in the Research Powerpack.

## Universal Query Principles

### Principle 1: Specificity Over Breadth

| Bad Query | Good Query | Why |
|-----------|-----------|-----|
| "how to fix react error" | `"Cannot read properties of undefined" react useEffect` | Exact error message matches specific solutions |
| "best database" | `PostgreSQL vs MongoDB IoT 50K writes/sec` | Specific context yields relevant comparisons |
| "docker optimization" | `Docker multi-stage build Node.js TypeScript slim image` | Stack-specific query finds applicable guides |

### Principle 2: One Angle Per Query

Each query should target ONE specific angle. Never combine angles in a single query — run them as separate parallel searches.

| Angles | Separate Queries |
|--------|-----------------|
| Overview + problems | Query 1: `"[topic] overview guide"` + Query 2: `"[topic] problems issues"` |
| Comparison + tutorial | Query 1: `"[A] vs [B] comparison"` + Query 2: `"[A] tutorial getting started"` |
| Current + historical | Query 1: `"[topic] 2025"` + Query 2: `"[topic] evolution changes"` |

### Principle 3: Include Context Tokens

Always include tokens that narrow the search to your context:

| Context Token | Purpose | Example |
|--------------|---------|---------|
| Language/framework | Limits to your stack | `TypeScript`, `React`, `Rust` |
| Version | Filters for your version | `v4`, `React 19`, `Node 22` |
| Year | Ensures recency | `2025`, `2024` |
| Scale indicator | Matches your scale | `production`, `large scale`, `enterprise` |
| Environment | Matches your deployment | `serverless`, `Kubernetes`, `Docker` |

### Principle 4: Vary Specificity Across Queries

Use a mix of narrow and broad queries to maximize coverage:

```
Narrow (exact match):  "TypeError: Cannot read properties of undefined" react hooks
Medium (targeted):     react hooks undefined error useEffect cleanup
Broad (discovery):     react hooks common errors fix 2025
```

## search_google Query Formulation

### Operator Quick Reference

| Operator | Syntax | Use Case |
|----------|--------|----------|
| Exact match | `"exact phrase"` | Error messages, function names |
| Site filter | `site:domain.com` | Restrict to specific sites |
| Exclude | `-term` or `-site:domain.com` | Remove noise |
| File type | `filetype:pdf` | Find papers, specs |
| OR | `term1 OR term2` | Match either variant |
| Title | `intitle:"phrase"` | Phrase must be in page title |

### Query Templates by Task

#### Bug Fixing
```python
keywords = [
    '"[exact error message]"',                              # Exact match
    '"[error type]" [framework] [version] fix',             # Type + context
    'site:stackoverflow.com "[error code]" [language]',     # SO-targeted
    'site:github.com/[org]/[repo]/issues "[symptom]"',      # GitHub issues
    '[framework] [symptom] solution [year]',                 # Recent solutions
]
```

#### Library Comparison
```python
keywords = [
    '[lib A] vs [lib B] benchmark [year]',                  # Direct comparison
    'best [category] library [language] [year]',            # Recommendations
    '[lib] alternatives [year]',                             # Find options
    'site:npmtrends.com [lib A] [lib B]',                   # Adoption metrics
    '[lib A] [lib B] migration guide',                       # Migration feasibility
    '"switched from [lib A]" [language]',                    # Migration stories
]
```

#### Configuration
```python
keywords = [
    '[tool] configuration reference options',                # Complete reference
    '[tool] [specific option] example',                      # Specific option
    '[tool] config [framework] [year]',                      # Framework-specific
    'site:[official-docs] [tool] configuration',             # Official docs
    '[tool] config best practices production',               # Production configs
]
```

#### Architecture
```python
keywords = [
    '[pattern A] vs [pattern B] [year]',                     # Pattern comparison
    'site:martinfowler.com [pattern]',                       # Authoritative source
    '[pattern] production experience case study',            # Real-world usage
    '[pattern] failure modes problems',                      # Failure analysis
    '[pattern] at scale [number] users',                     # Scale-specific
]
```

### Noise Reduction Strategies

Common noise sources and their exclusions:

```python
# Exclude content farms and low-quality sites
'-site:w3schools.com -site:geeksforgeeks.org'

# Exclude tutorials when seeking production advice
'-tutorial -beginner -introduction'

# Exclude marketing when seeking technical content
'-site:medium.com -"sponsored" -"affiliate"'

# Focus on specific quality sources
'site:stackoverflow.com OR site:github.com OR site:docs.rs'
```

## search_reddit Query Formulation

### Query Templates by Intent

#### Find opinions
```python
queries = [
    '[topic] experience production',          # Real-world usage
    '[topic] thoughts opinions',              # Community sentiment
    'what do you think about [topic]',        # Discussion threads
]
```

#### Find negative signal
```python
queries = [
    '[topic] regret problems',                # Dissatisfaction
    'switched from [topic] to',               # Migration away
    '[topic] not worth it',                    # Cost-benefit negative
    '[topic] wish I had known',               # Hindsight lessons
    'don\'t use [topic]',                      # Strong warnings
]
```

#### Find comparisons
```python
queries = [
    '[A] vs [B] [year]',                      # Direct comparison
    '[A] or [B] which do you recommend',      # Recommendation requests
    'migrated from [A] to [B] experience',    # Migration stories
]
```

#### Find solutions
```python
queries = [
    '"[error message]" r/[language]',         # Error in subreddit
    '[library] [problem] fix solved',         # Solved problems
    '[library] workaround [version]',         # Version-specific fixes
]
```

### Subreddit Selection Guide

Choose subreddits based on the expertise level you need:

| Expertise Level | Subreddits | Signal Quality |
|----------------|-----------|----------------|
| Senior/production | `r/ExperiencedDevs`, `r/softwarearchitecture` | High — production experience |
| Mid-level general | `r/programming`, `r/webdev` | Medium — mixed quality |
| Language-specific | `r/rust`, `r/golang`, `r/typescript` | High — focused expertise |
| Infrastructure | `r/devops`, `r/kubernetes`, `r/aws` | High — operational experience |
| Security | `r/netsec`, `r/AskNetsec` | High — security expertise |
| Beginner-friendly | `r/learnprogramming`, `r/learnjavascript` | Low — basic advice |

## deep_research Question Formulation

### The Structured Template

```
GOAL: [Specific, measurable outcome]
WHY: [Decision context — what problem triggers this research]
KNOWN: [Your current understanding — skip basics]
APPLY: [How you'll use the answer]
SPECIFIC QUESTIONS:
1) [Question targeting dimension A]
2) [Question targeting dimension B]
3) [Question about failure modes / edge cases]
PREFERRED SOURCES: [Optional — specific docs or standards]
FOCUS: [Optional — performance, security, cost, simplicity]
```

### Question Quality Checklist

Before submitting a deep_research question, verify:

- [ ] GOAL is specific (not "tell me about X")
- [ ] KNOWN section prevents repeating basics
- [ ] Each sub-question targets a different dimension
- [ ] At least one sub-question asks about failure modes
- [ ] Constraints are stated (stack, team size, scale)
- [ ] File attachments included for code-related questions

### Common Question Anti-Patterns

| Anti-Pattern | Example | Fix |
|-------------|---------|-----|
| Too vague | "How do I set up auth?" | "Auth architecture for Node.js SPA with JWT: cookie storage, refresh rotation, CSRF" |
| Too broad | "Tell me everything about Kubernetes" | "K8s HPA custom metrics for 40-service ECS cluster: resource limits, autoscaling, costs" |
| No constraints | "Best database for my app" | "PostgreSQL vs DynamoDB for IoT: 50K writes/sec, time-series queries, 2-dev team" |
| Duplicate angles | Two questions asking the same thing differently | Each question must target a distinct dimension |
| No code attachment | "Why is my API slow?" | Attach server.ts and db.ts with description of what to inspect |

## scrape_pages Extraction Target Formulation

### The Pipe-Separated Pattern

```
"[target 1] | [target 2] | [target 3] | [target 4] | [target 5]"
```

### Extraction Target Templates

| Scraping Task | Extraction Targets |
|--------------|-------------------|
| API docs | `"endpoints \| auth methods \| rate limits \| request format \| errors"` |
| Pricing page | `"tiers \| limits \| overage costs \| free tier \| enterprise features"` |
| Changelog | `"breaking changes \| new features \| deprecations \| migration steps"` |
| Library README | `"features \| install \| API examples \| requirements \| limitations"` |
| Config reference | `"options \| defaults \| types \| required fields \| examples"` |
| Security advisory | `"CVE \| CVSS \| affected versions \| patched version \| mitigation"` |
| Benchmark | `"results \| methodology \| hardware \| versions \| caveats"` |

## Keyword Expansion Strategy

When your initial query returns poor results, expand systematically:

### Synonym Expansion

| Original Term | Synonyms to Try |
|--------------|----------------|
| "slow" | performance, latency, lag, bottleneck, throughput |
| "error" | bug, crash, exception, failure, issue |
| "fix" | solution, workaround, resolve, patch, hotfix |
| "best" | recommended, top, preferred, production-ready |
| "compare" | vs, versus, comparison, benchmark, trade-offs |
| "setup" | configure, install, initialize, bootstrap |
| "problem" | issue, gotcha, pitfall, caveat, limitation |

### Abstraction Expansion

If specific queries fail, go one level more abstract:

```
Specific (failed):  "Prisma cold start Lambda function timeout"
Abstract:           "ORM cold start serverless optimization"
More abstract:      "database connection serverless best practices"
```

If abstract queries fail, go more specific:

```
Abstract (too noisy): "database performance"
Specific:             "PostgreSQL composite index query optimization"
More specific:        "PostgreSQL GIN index JSONB query performance"
```

## Key Insight

Query formulation is a skill, not a template. The templates in this guide are starting points — adapt them to your specific context. The single most impactful habit: before writing a query, ask yourself "What kind of page would answer my question?" then write the query that would find that page. If you'd find the answer on Stack Overflow, use exact error messages. If you'd find it in official docs, use `site:` operators. If you'd find it on Reddit, search for experiences and opinions.
