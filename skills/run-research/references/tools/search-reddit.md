# search_reddit — Community Signal Discovery

## What It Does

Runs 3–50 parallel Reddit searches. Returns post titles and URLs sorted by relevance. Surfaces real practitioner experiences, war stories, failure reports, and unfiltered opinions that official documentation never contains.

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `queries` | `string[]` | Yes | — | 3–50 search queries. Each targets a different angle. Min 3 required. |
| `date_after` | `string` | No | — | Filter for posts after this date (YYYY-MM-DD). |

Supports operators: `intitle:`, `"exact phrase"`, `OR`, `-exclude`. Auto-adds `site:reddit.com`.

## Token Budget

- Returns post titles + URLs (lightweight output)
- Budget is rarely a concern — the constraint is query diversity, not tokens

## When to Use

- Finding real-world experiences with a technology
- Discovering failure modes, edge cases, and warnings
- Getting unfiltered opinions on library/tool comparisons
- Finding "switched from X to Y" migration stories
- Checking community sentiment before adopting a technology
- Finding dissenting opinions that challenge conventional wisdom

## When NOT to Use

- When you need page content from non-Reddit sources → `search_google`
- When you need the full comment threads → follow up with `fetch_reddit`
- For finding official documentation → `search_google` + `scrape_pages`
- For questions with definitive technical answers → `deep_research`

## Query Formulation Rules

### The Negative Signal Strategy

The most valuable research insight: **search for failures, not successes**. Negative experiences are more informative than praise because:
- People who succeed rarely post about it
- People who fail explain exactly what went wrong
- Warnings prevent you from repeating others' mistakes

| Negative Query Pattern | What It Finds |
|----------------------|--------------|
| `"[technology] regret"` | Post-adoption dissatisfaction with specific reasons |
| `"switched from [X]"` | Migration stories with before/after comparison |
| `"problems with [X]"` | Known issues and failure modes |
| `"don't use [X]"` | Strong warnings with justification |
| `"wish I had known [X]"` | Hindsight lessons from production use |
| `"[X] broke in production"` | Real failure scenarios |
| `"[X] not worth it"` | Cost/benefit analysis from practitioners |
| `"migrated from [X] to [Y]"` | Detailed migration experiences |

### Subreddit Targeting

Include subreddit names in queries to focus results:

| Domain | Subreddits |
|--------|-----------|
| General dev | `r/programming`, `r/ExperiencedDevs`, `r/cscareerquestions` |
| Web dev | `r/webdev`, `r/reactjs`, `r/nextjs`, `r/sveltejs` |
| Backend | `r/node`, `r/golang`, `r/rust`, `r/python`, `r/java` |
| DevOps | `r/devops`, `r/kubernetes`, `r/docker`, `r/aws` |
| Security | `r/netsec`, `r/AskNetsec`, `r/devsecops` |
| Databases | `r/PostgreSQL`, `r/redis`, `r/mongodb` |
| Frontend | `r/frontend`, `r/css`, `r/typescript` |
| Architecture | `r/softwarearchitecture`, `r/ExperiencedDevs` |
| Open source | `r/opensource`, `r/selfhosted` |
| macOS/apps | `r/macapps`, `r/mac` |

### Query Diversity Matrix

For comprehensive coverage, use queries from at least 4 of these 8 categories:

| Category | Query Pattern | Example |
|----------|-------------|---------|
| 1. Direct topic | `"[topic]"` | `"Prisma ORM"` |
| 2. Recommendations | `"best [category]"` | `"best TypeScript ORM 2025"` |
| 3. Specific tools/repos | `"[exact tool name]"` | `"Drizzle ORM production"` |
| 4. Comparisons | `"[X] vs [Y]"` | `"Prisma vs Drizzle"` |
| 5. Alternatives | `"alternative to [X]"` | `"alternative to Prisma"` |
| 6. Subreddit targeting | `r/[sub] [topic]` | `r/typescript ORM recommendation` |
| 7. Problems/issues | `"[X] problems"` | `"Prisma cold start problems"` |
| 8. Year-specific | `"[topic] 2025"` | `"TypeScript ORM 2025"` |

## Operator Reference

```
intitle:"exact phrase"    → Phrase must appear in post title
"exact match"             → Exact string match anywhere
OR                        → Match either term
-exclude                  → Exclude term from results
r/subreddit              → Target specific subreddit (include in query text)
```

## Composing with Other Tools

### Opinion Mining: search_reddit → fetch_reddit

```
1. search_reddit: 5-7 diverse queries
2. Review: Pick 5-10 highest-signal threads
3. fetch_reddit: Get full comment trees
   - fetch_comments=true (ALWAYS)
   - use_llm=false (preserve exact quotes)
```

This is the standard Reddit research workflow. search_reddit finds; fetch_reddit reads.

### Community Validation: search_google → scrape_pages → search_reddit

```
1. search_google: Find authoritative recommendation
2. scrape_pages: Extract the recommendation
3. search_reddit: Check if practitioners agree
4. If disagreement: fetch_reddit for details
```

Adds real-world validation to official/expert recommendations.

### Sentiment Check: search_reddit (quick)

```
1. search_reddit: 3-5 queries covering both positive and negative
2. Scan titles: Count positive vs negative sentiment
3. Decision: If mostly negative → investigate further
```

Quick sentiment check before deeper research.

## Failure Modes

| Failure | Symptoms | Fix |
|---------|----------|-----|
| Too few results | Niche topic with little Reddit discussion | Broaden subreddit scope; use more general terms |
| Echo chamber | All results from same subreddit, same opinion | Target multiple subreddits for diverse perspectives |
| Stale results | Top results from 3+ years ago | Use `date_after` parameter; add year to queries |
| Survivorship bias | Only success stories, no failures | Explicitly search for negative signal (see strategy above) |
| Private subreddits | No results from quarantined/private subs | Use alternative query terms; try different subreddits |

## Anti-Patterns

| Anti-Pattern | Why It's Wrong | Fix |
|--------------|---------------|-----|
| Only positive queries | Misses failure modes and warnings | Always include negative signal queries |
| Not using date_after | Gets outdated advice for fast-moving tech | Filter for recent posts when relevance depends on recency |
| Stopping at search_reddit | Titles don't contain full analysis | Follow up with fetch_reddit for comment threads |
| Single subreddit focus | Echo chamber effect — biased results | Target 2-3 different subreddits per topic |
| Too few queries | Misses important angles | Use 5-7 queries covering different categories |
| Generic queries | Returns low-relevance results | Use specific tool/library names and technical terms |

## Query Examples

### Library Evaluation (7 queries)

```python
queries = [
    "Prisma vs Drizzle production experience",
    "switched from Prisma to Drizzle why",
    "r/typescript ORM recommendation 2025",
    "Prisma cold start serverless problems",
    "Drizzle ORM issues gotchas",
    "best TypeScript ORM 2025",
    "Prisma regret complex queries",
]
```

### Architecture Decision (7 queries)

```python
queries = [
    "microservices regret went back to monolith",
    "modular monolith experience production",
    "r/ExperiencedDevs microservices small team",
    "microservices operational cost hidden",
    "monolith to microservices when worth it",
    "r/softwarearchitecture modular monolith 2025",
    "microservices vs monolith team size threshold",
]
```

### Bug Investigation (5 queries)

```python
queries = [
    '"[exact error message]" r/node',
    "[library] [version] breaking change",
    "[library] [symptom] workaround fix",
    "r/[language] [error type] debugging",
    "[library] regression update broke",
]
```

## Key Insight

Reddit is your reality-check tool. Official docs tell you how things should work. Blog posts tell you how things can work. Reddit tells you how things actually work in production — including the parts that break, the hidden costs, and the migration regrets. Always search for negative signal alongside positive. The developers who warn you away from a technology are often more useful than those who recommend it.

## Steering notes from production testing

### Negative signal queries are essential

At least 25% of queries should be negative: `"regret switching to [X]"`, `"problems with [X] production"`, `"[X] not worth it"`, `"switched from [X] to"`.

### Subreddit targeting

| Domain | Subreddits |
|---|---|
| Node.js/backend | r/node, r/javascript |
| React/Next.js | r/reactjs, r/nextjs |
| DevOps | r/devops, r/sysadmin |
| Security | r/netsec, r/cybersecurity |
| Senior perspectives | r/ExperiencedDevs |

### Real diversity example (8 queries, 68 posts)

1. `"Socket.io vs Pusher vs Ably 2025"` -- comparison
2. `r/node "real-time" library 2025` -- subreddit-targeted
3. `"switched from socket.io" regret` -- negative signal
4. `websocket scaling "10000 connections"` -- scale-specific
5. `intitle:"Ably" r/javascript review` -- vendor opinions
6. `"Pusher" pricing "not worth"` -- cost pain
7. `r/nextjs websocket server component 2025` -- framework-specific
8. `"managed websocket" vs "self-hosted"` -- architecture

### Query count: 8-12 recommended (80-120 posts)
