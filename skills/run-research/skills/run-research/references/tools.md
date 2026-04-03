# Tool Reference

## web-search

### Parameters
| Parameter | Type | Required | Description |
|---|---|---|---|
| `keywords` | `string[]` | Yes | 1–100 search queries, each running as a separate parallel Google search |

### How results work
Each keyword returns ~10 URLs. Results are aggregated across all keywords, and URLs appearing in multiple searches are flagged as high-confidence consensus matches. The aggregated view at the top is often the most valuable part — it shows you the landscape before you read a single page.

5–7 keywords = 50–70 URLs (solid for most tasks). 15–20 keywords = thorough coverage. Up to 100 for exhaustive landscape scans.

### Writing effective keywords

Each keyword should attack a genuinely different angle. The goal is coverage, not repetition.

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
- Write 7 keywords that are minor rewrites of each other
- Skip search operators (they're the difference between noise and signal)
- Follow the tool's "Next Steps" suggestions instead of your research plan

---

## scrape-links

### Parameters
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `urls` | `string[]` | Yes | — | 1–50 URLs to scrape |
| `what_to_extract` | `string` | Recommended | — | Pipe-separated extraction targets |
| `use_llm` | `bool` | No | `true` | AI extraction. Keep true. |
| `timeout` | `int` | No | `30` | Timeout per URL in seconds (5–120) |

### Token budget
32K total tokens split across URLs:
- 1–2 URLs: 16–32K each (deep single-page analysis)
- 3–5 URLs: 6–10K each (standard — recommended for most tasks)
- 10+ URLs: <3K each (too shallow for detailed extraction)

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
- **SPA with JS rendering** — Increase timeout to 60–120s
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
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `queries` | `string[]` | Yes | — | 3–50 search queries, each targeting a different angle |
| `date_after` | `string` | No | — | Filter for posts after this date (YYYY-MM-DD) |

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
- Stop at search-reddit (titles aren't evidence — fetch the threads)

---

## get-reddit-post

### Parameters
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `urls` | `string[]` | Yes | — | 2–50 Reddit post URLs |
| `fetch_comments` | `bool` | No | `true` | Always set true |
| `use_llm` | `bool` | No | `false` | **Always set false.** Raw comments are clean structured API data. |

### Comment budget
~1000 comments total, distributed across posts:
- 2–3 posts: 330–500 comments each (maximum depth)
- 5–8 posts: 125–200 each (rich — recommended)
- 10–15 posts: 67–100 each (moderate)
- 20+: <50 each (too shallow)

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

### Why use_llm must be false
Reddit API data is already structured — threaded comments with author, score, OP markers, no HTML boilerplate. `use_llm=true` throws away the exact code snippets, version numbers, config values, and authority signals (library maintainer replying, etc.) that make Reddit research actionable. You can always summarize raw comments yourself; you can never recover exact values from a summary.

The only exception: 20+ posts where you need a quick consensus scan, not detailed analysis.

---

## deep-research

### Parameters
| Parameter | Type | Required | Description |
|---|---|---|---|
| `questions` | `object[]` | Yes | 1–10 research questions |
| `questions[].question` | `string` | Yes | Structured research question (min 10 chars) |
| `questions[].file_attachments` | `object[]` | No | Code files for context |

### Token budget
32K total, split across questions:
- 1 question: 32K (exhaustive single-topic deep dive)
- 2 questions: 16K each (deep — recommended for most tasks)
- 3 questions: ~10.7K each (thorough)
- 5 questions: 6.4K each (balanced)
- 10 questions: 3.2K each (rapid scan — usually too shallow)

**Recommendation:** 2–3 focused questions. Depth beats breadth.

### The structured template (mandatory for quality)

```
GOAL: [Specific outcome — not "tell me about X" but "determine whether X fits my constraints"]
WHY: [What decision this informs — the context that shapes the answer]
KNOWN: [Everything you've already learned — skip basics, fill gaps]
APPLY: [How you'll use the answer — implementation, debugging, architecture]

SPECIFIC QUESTIONS:
1) [Precise question targeting one dimension]
2) [Different angle or facet]
3) [Failure modes, edge cases, or counter-arguments]

PREFERRED SOURCES: [Optional — specific docs, sites, standards to prioritize]
FOCUS: [Optional — performance, security, cost, simplicity]
```

### The KNOWN field is everything

This is the single biggest quality lever. The difference between a generic textbook answer and a situation-specific analysis is what you put in KNOWN.

**Bad:** `KNOWN: I need to choose a WebSocket library.`

**Good:** `KNOWN: Comparing Socket.io (14.2M npm downloads), Pusher ($49/mo starter), Ably (99.999% SLA). Our stack: Next.js 15 App Router on Vercel (serverless). Socket.io needs a dedicated server which conflicts with Vercel's model. Reddit reports Pusher rate limits surprise teams at scale. We need <100ms for 500 concurrent users. Budget: <$200/mo.`

### When to attach files
- Bug diagnosis → the failing code + stack trace
- Library evaluation → `package.json`, framework config
- Architecture review → design docs, deployment config
- Performance → profiler output, slow code paths
- Security → auth middleware, route handlers

Attach 2–4 files per question max. Use `description` to tell deep-research what to focus on. Use `start_line`/`end_line` to scope large files.

### Hallucination risk
deep-research can synthesize brilliantly but may hallucinate specific version numbers, pricing, API signatures, or sources. Always verify these with `scrape-links` against official docs. Treat deep-research output as expert analysis, not as citation.

### What NOT to do
- Call it first with empty KNOWN (gather evidence first, then synthesize)
- Ask 10 questions at 3.2K tokens each (too shallow for all of them)
- Trust version numbers, pricing, or API details without scraping to verify
- Use it for simple factual lookups (web-search + scrape is faster)
