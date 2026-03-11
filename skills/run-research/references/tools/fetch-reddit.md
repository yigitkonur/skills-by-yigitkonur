# fetch_reddit — Deep Comment Thread Extraction

## What It Does

Fetches full post content and comment trees from 2–50 Reddit URLs. Extracts the complete discussion including nested reply chains where the best insights, corrections, code snippets, and dissenting opinions live. Auto-allocates a comment budget across posts for balanced depth.

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `urls` | `string[]` | Yes | — | 2–50 Reddit post URLs. Min 2 required. |
| `fetch_comments` | `bool` | No | `true` | Fetch comment trees. Always set to true. |
| `use_llm` | `bool` | No | `false` | AI summarization. Keep false for exact content. |
| `max_comments` | `int` | No | `100` | Override comment budget per post. |
| `what_to_extract` | `string` | No | — | Extraction/synthesis targets when use_llm=true. |

## Comment Budget Auto-Allocation

Total budget: 1000 comments distributed across posts.

| Posts | Comments per Post | Depth Level |
|-------|------------------|-------------|
| 2 | 500 | Maximum depth — full thread with all replies |
| 5 | 200 | Deep — captures most discussion threads |
| 10 | 100 | Balanced — top-level + key reply chains |
| 20 | 50 | Broad — top-level comments and first replies |
| 50 | 20 | Scan — top comments only |

**Recommendation:** 5–10 posts for most tasks. This gives 100–200 comments per post — enough to capture the full discussion including dissenting views.

## use_llm Modes: Critical Decision

### use_llm=false (DEFAULT — use this most of the time)

Preserves raw comment content exactly. This is critical when you need:
- Exact code snippets (indentation, syntax, imports)
- Precise version numbers (`v4.2.1`, not "version 4")
- Configuration values (`pool_size=25`, not "a pool size of about 25")
- Exact library names and import paths
- Specific error messages
- Numerical benchmarks ("p99 went from 890ms to 120ms")

### use_llm=true (ONLY when explicitly needed)

Use ONLY when:
- Processing 20+ posts and need a synthesis overview
- The user explicitly asks for a summary
- You don't need exact values, code, or version numbers
- You want consensus extraction across many threads

When use_llm=true, set `what_to_extract` for focused synthesis:
```
what_to_extract = "consensus recommendations | dissenting opinions | specific version numbers | code patterns"
```

**The rule:** If in doubt, keep `use_llm=false`. You can always summarize raw comments yourself; you cannot recover exact values from a summary.

## When to Use

- After `search_reddit` — to read the full threads you found
- Extracting exact code examples from community discussions
- Reading dissenting opinions and corrections in reply chains
- Getting specific config values, benchmarks, and version numbers
- Finding "EDIT: solved" markers with verified fixes
- Understanding the full context of a recommendation (not just the title)

## When NOT to Use

- For finding threads — use `search_reddit` first to discover URLs
- For non-Reddit URLs — use `scrape_pages` instead
- When titles alone answer your question — search_reddit is sufficient
- For real-time breaking news — Reddit search may be faster

## Reading Comment Threads Effectively

### Where the Value Lives

| Comment Position | What It Contains | How to Use It |
|-----------------|-----------------|---------------|
| Top-level, highest voted | Conventional wisdom — often correct but sometimes incomplete | Good starting point, but don't stop here |
| 2nd or 3rd reply | Corrections, edge cases, updated information | Check for "Actually..." and "This changed in..." |
| Deeply nested replies | Specific debugging steps, config values, workarounds | The most actionable content |
| Downvoted comments | Sometimes contain valid minority opinions | Worth reading if they have substantive arguments |
| OP follow-up | "EDIT: solved" — confirmed fix | Most reliable signal of a working solution |
| Late replies | May contain newer, more accurate information | Check timestamps — a 2024 reply on a 2022 thread may be more relevant |

### Signals to Look For

- **"EDIT: this fixed it"** — Confirmed solution
- **"After X months in production..."** — Battle-tested experience
- **"I switched from X to Y because..."** — Migration story with reasons
- **"Don't do what the top comment says..."** — Critical correction
- **"We had the same issue at [scale]..."** — Scale-specific experience
- **Specific numbers** — p99 latency, memory usage, cost figures

## Composing with Other Tools

### Standard Reddit Pipeline: search_reddit → fetch_reddit

```
1. search_reddit: 5-7 diverse queries
2. Review thread titles and upvote counts
3. Select 5-10 highest-signal threads
4. fetch_reddit: Full comment extraction
   - fetch_comments=true
   - use_llm=false
```

### Decision Validation: deep_research → search_reddit → fetch_reddit

```
1. deep_research: Get structured analysis
2. search_reddit: Find community opinions on the recommendation
3. fetch_reddit: Read full threads for dissenting views
4. Compare: Does community experience match deep_research analysis?
```

### Fix Extraction: search_google → search_reddit → fetch_reddit

```
1. search_google: Find official docs and SO answers
2. search_reddit: Find "same error" threads
3. fetch_reddit: Extract exact fix steps from comments
4. Cross-reference: Do Reddit fixes match official guidance?
```

## Failure Modes

| Failure | Symptoms | Fix |
|---------|----------|-----|
| Deleted posts | Stub JSON, empty body | Try archived version or find alternative thread |
| Archived threads | Old posts with no new comments | Use date_after in search_reddit to find recent threads |
| Shallow threads | Few comments, no discussion | Fetch more threads; widen search_reddit queries |
| Truncated deep threads | Nested comments cut off at depth 5 | Focus on high-level comments; deep nests rarely add value |
| Rate limiting | Delays 1–5 minutes | Reduce batch size; process in two rounds |
| Biased sample | All threads from one subreddit | Ensure search_reddit covers multiple subreddits |

## Anti-Patterns

| Anti-Pattern | Why It's Wrong | Fix |
|--------------|---------------|-----|
| fetch_comments=false | Loses 90% of the value — insights are in replies | Always set fetch_comments=true |
| use_llm=true by default | Loses exact code, versions, numbers | Keep use_llm=false; only true for 20+ post synthesis |
| Fetching 50 posts | 20 comments each = surface-level only | Use 5-10 posts for meaningful depth |
| Only reading top comments | Misses corrections and edge cases | Read 2nd and 3rd level replies |
| Ignoring timestamps | Old comments may be outdated | Check comment dates, especially for fast-moving tech |
| Not checking for "solved" | Missing confirmed fixes | Search for "EDIT:", "solved", "fixed" in OP comments |

## URL Selection Strategy

When selecting URLs from search_reddit results:

| Selection Criteria | Priority |
|-------------------|----------|
| Thread with 50+ comments | High — rich discussion |
| Title matches your exact problem | High — directly relevant |
| Recent thread (< 1 year old) | High — current information |
| Thread from r/ExperiencedDevs | High — production experience |
| Thread with "experience" or "production" in title | High — real-world data |
| Thread with "vs" in title | Medium — comparison discussion |
| Thread with low comment count but exact match | Medium — niche but relevant |
| Old thread with recent comments | Medium — may have updated info |
| Thread from general subreddit | Low — less focused discussion |

## Key Insight

fetch_reddit is your depth tool for community knowledge. The best insights on Reddit are never in the post title or the top comment — they're in the corrections, the dissenting replies, the "actually, after 6 months in production..." follow-ups, and the "EDIT: solved it by doing X" updates. Always keep use_llm=false unless you're processing 20+ posts, because the exact numbers, code snippets, and version strings are what make Reddit research actionable rather than anecdotal.

## Steering notes from production testing

### Comment budget distribution

| Threads | Comments/thread | Quality |
|---|---|---|
| 2-3 | 330-500 | Very deep |
| 5-8 | 125-200 | Rich (recommended) |
| 10-15 | 67-100 | Moderate |
| 20+ | <50 | Shallow |

### Thread selection

**Prioritize:** 10+ comments, high upvotes, recent (12-18 months). **Skip:** 1-3 comments, self-promotion, 2+ years old (for active tech).

### Raw expert voices

`use_llm=false` preserves exact quotes and authority signals (e.g., a library co-founder's comment). `use_llm=true` synthesizes patterns across 15+ threads.
