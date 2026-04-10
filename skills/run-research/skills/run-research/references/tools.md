# Tool Reference

## web-search

### Parameters
| Parameter | Type | Required | Description |
|---|---|---|---|
| `queries` | `string[]` | Yes | Up to 100 search queries, each running as a separate parallel Google search |
| `extract` | `string` | Yes | What you are looking for — LLM classifies results by relevance and generates a synthesis |
| `raw` | `bool` | No (default `false`) | Skip LLM classification and return traditional ranked URL list |

### How results work
Each query returns ~10 URLs. Results are aggregated, deduplicated, and the LLM classifies each into 3 tiers: **highly relevant**, **maybe relevant**, and **other**. Output includes a synthesis paragraph and a tiered markdown table.

Set `raw=true` to bypass classification and get the ranked consensus list.

5–7 queries = 50–70 URLs (solid for most tasks). 15–20 queries = thorough coverage. Up to 100 for exhaustive landscape scans.

### Writing effective queries

Each query should attack a genuinely different angle. The goal is coverage, not repetition.

**The 7-angle framework:**
1. Direct topic — `"Next.js middleware authentication 2025"`
2. Specific technical term — `"Next.js middleware matcher config"`
3. Problems / debugging — `"Next.js middleware redirect loop fix"`
4. Best practices — `"Next.js middleware best practices production"`
5. Comparison — `"Next.js middleware vs API routes authentication"`
6. Official docs — `site:nextjs.org middleware`
7. Advanced / production — `"Next.js middleware chain multiple matchers production"`

**Operators that cut through noise:**
- `"exact phrase"` — error messages, function names
- `site:docs.python.org` — restrict to authoritative domains
- `-site:medium.com -site:w3schools.com` — exclude content farms
- `intitle:"migration guide"` — phrase must appear in title
- `filetype:pdf` — find specs and papers
- `OR` — match variant terms
- Year tokens (`2025`, `2026`) — filter stale results for fast-moving ecosystems

**For bugs:** Always lead with the exact error message in quotes. This is the highest-precision query possible.

**For comparisons:** Include "vs", "comparison", "benchmark" — and also "switched from X", "regret X", "problems with X" for the critical negative signal.

### What NOT to do
- Treat the returned URLs as answers (they're leads — scrape to read)
- Write 7 queries that are minor rewrites of each other
- Skip search operators (they're the difference between noise and signal)

---

## scrape-links

### Parameters
| Parameter | Type | Required | Description |
|---|---|---|---|
| `urls` | `string[]` | Yes | Up to 100 URLs to scrape |
| `extract` | `string` | Yes | What to pull from each page — pipe-separated extraction targets |

### Writing extraction targets

This is the single biggest quality lever. Pipe-separated targets with 4–8 specific categories consistently outperform vague requests.

| Scraping task | Extraction targets |
|---|---|
| API docs | `"endpoints\|auth methods\|rate limits\|request format\|error codes"` |
| Pricing | `"pricing tiers\|free tier limits\|overage costs\|included features\|enterprise"` |
| Changelog | `"breaking changes\|new features\|deprecations\|migration steps\|version"` |
| Library README | `"features\|install\|API examples\|requirements\|limitations\|license"` |
| Benchmark | `"results\|methodology\|hardware specs\|versions tested\|caveats"` |
| Security advisory | `"CVE ID\|CVSS score\|affected versions\|patched version\|mitigation steps"` |
| Config reference | `"options\|default values\|types\|required fields\|examples\|deprecated"` |
| Bug fix article | `"root cause\|fix code\|version affected\|workarounds\|environment conditions"` |

### Composition pattern
Always follows `web-search`. Pick the 3–10 most promising URLs from search results. Group thematically similar pages together — they share the extraction prompt context.

### Failure modes
- **Anti-bot / Cloudflare** — Try cached or CDN versions of the URL
- **SPA with JS rendering** — May fail on heavily client-rendered pages
- **Paywall** — Find alternative free source
- **Truncated output** — Reduce URL count or narrow extraction targets

### What NOT to do
- Scrape Reddit URLs (use `get-reddit-post` — it handles threading)
- Use vague extraction targets ("tell me about this page")
- Scrape 20+ URLs at once (too shallow per page)
- Scrape just to cite — only scrape when you need to verify or discover

---

## search-reddit

### Parameters
| Parameter | Type | Required | Description |
|---|---|---|---|
| `queries` | `string[]` | Yes | Up to 100 search queries — `site:reddit.com` is appended automatically |

Returns a flat list of unique Reddit post URLs. No ranking, no LLM — just URL discovery. Pipe results into `get-reddit-post` to fetch the actual content.

### Writing Reddit queries

The key insight: search for failures, not just successes. Negative signal is more informative because people who succeed rarely post — people who fail explain exactly what went wrong.

**Query diversity matrix — cover at least 4 of these 8 categories:**
1. Direct topic — `"Prisma ORM production experience"`
2. Recommendations — `"best TypeScript ORM 2025"`
3. Specific tools — `"Drizzle ORM gotchas"`
4. Comparisons — `"Prisma vs Drizzle vs Kysely"`
5. Alternatives — `"alternative to Prisma serverless"`
6. Subreddit-targeted — `r/typescript ORM recommendation`
7. Negative signal — `"Prisma regret cold start problems"`
8. Year-specific — `"TypeScript ORM 2025"`

**Negative signal queries (use at least 25% of these):**
- `"[X] regret"` / `"switched from [X]"` / `"problems with [X]"`
- `"don't use [X]"` / `"[X] not worth it"` / `"[X] broke in production"`
- `"wish I had known [X]"` / `"migrated from [X] to [Y]"`

**Key subreddits by domain:**
| Domain | Subreddits |
|---|---|
| Senior perspectives | r/ExperiencedDevs, r/softwarearchitecture |
| Web development | r/webdev, r/reactjs, r/nextjs |
| Backend | r/node, r/golang, r/rust, r/python |
| DevOps | r/devops, r/kubernetes, r/aws |
| Security | r/netsec, r/AskNetsec |

### What NOT to do
- Only search for positive sentiment (miss failure modes)
- Target a single subreddit (echo chamber)
- Stop at search-reddit (URLs aren't evidence — fetch the threads)

---

## get-reddit-post

### Parameters
| Parameter | Type | Required | Description |
|---|---|---|---|
| `urls` | `string[]` | Yes | Up to 100 Reddit post URLs |

Returns raw posts with full threaded comment trees including author, score, and OP markers. No LLM processing — you get the real community voice.

### Where the value lives in comment threads
| Position | What it contains |
|---|---|
| Top-level, highest voted | Conventional wisdom — good starting point but sometimes incomplete |
| 2nd/3rd replies | Corrections, edge cases, "actually this changed in v4..." |
| Deeply nested | Specific debugging steps, config values, workarounds |
| OP follow-up | "EDIT: solved" — confirmed fix, most reliable signal |
| Late replies on old threads | May contain newer, more accurate information |

### Signals to look for
- **"EDIT: this fixed it"** — confirmed solution
- **"After X months in production..."** — battle-tested
- **"I switched from X to Y because..."** — migration with reasons
- **"Don't do what the top comment says..."** — critical correction
- **Specific numbers** — p99 latency, memory usage, cost, scale

### Thread selection from search-reddit results
Prioritize: 10+ comments, high upvotes, recent (within 12–18 months), from senior-focused subreddits. Skip: 1–3 comments, self-promotion posts, 2+ years old for active tech.

### Why raw comments matter
Reddit API data is already structured — threaded comments with author, score, OP markers, no HTML boilerplate. Raw threaded comments preserve the exact code snippets, version numbers, config values, and authority signals (library maintainer replying, etc.) that make Reddit research actionable. You can always summarize raw comments yourself; you can never recover exact values from a summary.
