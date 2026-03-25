# search_google / mcp__research_powerpack__web_search — Breadth-First Discovery

## What It Does

Runs 1–100 parallel web searches simultaneously. Each keyword executes as a separate search returning ranked URLs. Returns **URLs only** — never page content. You MUST follow up with `scrape_pages` to get actual content.

The skill shorthand is `search_google`. In Codex, call the wrapper `mcp__research_powerpack__web_search`.

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `keywords` | `string[]` | Yes | — | 1–100 search keywords. Each runs as a separate parallel search. |

Supports all Google search operators: `site:`, `"exact phrase"`, `-exclude`, `filetype:`, `OR`, `intitle:`.

## Token Budget

- Returns ~10 URLs per keyword
- 3 keywords = 30 URLs, 7 keywords = 70 URLs, 100 keywords = 1000 URLs
- Output is lightweight (URLs + titles only), so budget is rarely a concern

## When to Use

- **First step** in most research workflows — discover where answers live
- Finding documentation, blog posts, GitHub issues, Stack Overflow answers
- Locating official sources for specific technologies
- Gathering candidate URLs for `scrape_pages` extraction

## When NOT to Use

- When you need page content (use `scrape_pages` after)
- When you need community opinions (start with `search_reddit` instead)
- When you already know the URL — go straight to `scrape_pages`

## Query Formulation Rules

### The 7-Angle Strategy

Every search_google call should cover at least 5 of these 7 angles. Each keyword MUST target a different angle — never repeat the same query reworded.

| Angle | Purpose | Example |
|-------|---------|---------|
| 1. Broad topic | Cast a wide net | `"Next.js middleware authentication"` |
| 2. Specific technical term | Find precise documentation | `"Next.js middleware matcher config"` |
| 3. Problems / debugging | Find solutions to known issues | `"Next.js middleware redirect loop fix"` |
| 4. Best practices | Find authoritative guidance | `"Next.js middleware best practices 2025"` |
| 5. Comparison (A vs B) | Find trade-off analysis | `"Next.js middleware vs API routes authentication"` |
| 6. Tutorial / guide | Find step-by-step walkthroughs | `"Next.js middleware tutorial edge runtime"` |
| 7. Advanced patterns | Find production-grade solutions | `"Next.js middleware chain multiple matchers production"` |

### Search Operator Cheat Sheet

```
"exact phrase"           → Match exact string (use for error messages)
site:github.com          → Restrict to a domain
site:docs.rs             → Restrict to Rust docs
-site:medium.com         → Exclude a domain
filetype:pdf             → Only PDF results
OR                       → Match either term
intitle:"migration guide"→ Term must appear in page title
after:2024               → Results after a date (approximate)
```

### Operator Combinations for Common Tasks

| Task | Keywords Example |
|------|-----------------|
| Find official docs | `site:docs.python.org "asyncio" "TaskGroup"` |
| Find GitHub issues | `site:github.com/[org]/[repo]/issues "[error message]"` |
| Find recent content | `"[topic]" 2025 best practices` |
| Exclude noise | `"[topic]" -site:pinterest.com -site:medium.com -tutorial` |
| Compare options | `"[option A] vs [option B]" benchmark comparison` |
| Find changelogs | `site:github.com "[library]" CHANGELOG "breaking change"` |

## Output Format

Returns a list of search results, each containing:
- URL
- Page title
- Short description snippet (from Google)

The snippet is NOT the page content. It is Google's summary and often incomplete or misleading. Always scrape the actual page.

## Composing with Other Tools

### Standard Flow: search_google → scrape_pages

```
1. search_google: 5-7 diverse keywords
2. Review URLs: Pick top 3-5 most relevant
3. scrape_pages: Extract structured content from those URLs
```

This is the minimum viable research workflow. search_google finds; scrape_pages reads.

### Extended Flow: search_google → scrape_pages → search_reddit

```
1. search_google: Find authoritative sources (docs, blogs, SO)
2. scrape_pages: Extract facts and recommendations
3. search_reddit: Validate findings against practitioner experience
```

Adds community validation to the authoritative sources.

### Discovery Flow: search_google → deep_research

```
1. search_google: Quick scan for what exists
2. deep_research: Structured analysis of the topic
   (informed by knowing what sources are available)
```

Use when the search_google results reveal the topic is complex enough to warrant deep_research.

## Failure Modes

| Failure | Symptoms | Fix |
|---------|----------|-----|
| Zero results | Empty or near-empty result set | Broaden query: remove quotes, use fewer terms |
| SEO spam in results | Top results are low-quality aggregator sites | Add `-site:` exclusions; use `site:` to target specific domains |
| Outdated results | Top results from 3+ years ago | Add current year to query; use `after:` operator |
| Geo-blocked results | Missing results available in other regions | Rephrase without regional terms |
| Duplicate results | Same page appears under different URLs | Deduplicate before passing to scrape_pages |

## Anti-Patterns

| Anti-Pattern | Why It's Wrong | Fix |
|--------------|---------------|-----|
| Single keyword search | Misses angles for non-trivial research | Use 5-7 keywords unless this is a narrow fact-check |
| Stopping at search_google | URLs are not answers | Always follow with scrape_pages |
| Repeating the same query reworded | Wastes searches; returns duplicates | Each keyword must target a different angle |
| Not using operators | Drowns in noise | Use `site:`, `"quotes"`, `-exclude` |
| Ignoring result position | Later results may be more relevant for niche queries | Review all results, not just top 3 |
| Not adding year/version | Gets stale advice | Include year for fast-moving ecosystems |

## Examples

### Bug Research Keywords

```python
keywords = [
    '"TypeError: Cannot read properties of undefined" react hooks',
    '"Cannot read properties of undefined" useEffect cleanup',
    'react hooks undefined error fix 2025',
    'site:stackoverflow.com react undefined props',
    'react hooks stale closure undefined fix',
]
```

### Library Comparison Keywords

```python
keywords = [
    'Prisma vs Drizzle vs Kysely benchmark 2025',
    'TypeScript ORM comparison production experience',
    'site:npmtrends.com prisma drizzle kysely',
    'best TypeScript ORM serverless cold start',
    '"Drizzle ORM" migration from Prisma guide',
    'TypeScript ORM type safety complex queries comparison',
]
```

### Architecture Decision Keywords

```python
keywords = [
    'microservices vs modular monolith decision framework 2025',
    'site:martinfowler.com monolith first',
    '"modular monolith" production experience case study',
    'microservices operational cost small team',
    'monolith to microservices migration when worth it',
    '"Conway law" software architecture team size',
]
```

## Key Insight

search_google is your breadth tool. It tells you WHERE answers live, not WHAT they say. The most common agent mistake is treating search_google results as research output. They are research input — the starting point for scrape_pages extraction and Reddit validation.

## Steering notes from production testing

### "Next Steps (DO NOT SKIP)" banner

`search_google` appends this section suggesting tool calls. **Follow the skill's workflow, not these banners.**

### Results: ~10 per keyword

5-7 keywords = 50-70 results (recommended). 10+ keywords has diminishing returns.

### Most effective patterns (from testing)

1. Exact error in quotes: `"ERR_HTTP_HEADERS_SENT"` -- highest precision
2. Site-targeted: `site:docs.ably.com presence API` -- cuts SEO noise
3. GitHub issues: `site:github.com socket.io reconnection` -- real bugs
4. Version-pinned: `"Next.js 15" websocket 2025` -- filters stale
5. Exclusion: `websocket node -tutorial -beginner` -- removes noise

### Year tokens

Active ecosystems (React, Next.js, Bun): always add current year. Stable (PostgreSQL, Redis): less critical.
