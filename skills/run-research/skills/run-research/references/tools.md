# Tool Reference

Research Powerpack v6 exposes exactly three tools. There is **no** `search-reddit` and **no** `get-reddit-post` — those collapsed into `web-search scope:"reddit"` and `scrape-links` (reddit URLs are auto-detected).

---

## start-research

### Parameters
| Parameter | Type | Required | Description |
|---|---|---|---|
| `goal` | `string` | No | Research goal — 1–2 sentences, specific about what "done" looks like. Required for a tailored brief; omit for the generic 3-tool playbook. |
| `include_playbook` | `bool` | No (default `false`) | Attach the verbose 3-tool tactic reference on top of the brief. Only pass `true` when the agent needs the playbook; the default stub already names the tools and loop. |

### What it returns
When `goal` is provided AND the LLM planner is online, the server returns a **goal-tailored brief** with these fields:

| Field | Meaning | How to use it |
|---|---|---|
| `goal_class` | `spec` \| `bug` \| `migration` \| `sentiment` \| `pricing` \| `security` \| `synthesis` \| `product_launch` \| `other` | Anchors the `extract` shape for downstream calls |
| `primary_branch` | `"reddit"` \| `"web"` \| `"both"` | Dictates `scope` on the first `web-search` |
| `first_call_sequence` | Ordered list of 1–3 exact tool calls | Fire verbatim on round 1 |
| `keyword_seeds` | 25–50 ready queries | Feed as `queries` to the first `web-search` |
| `iteration_hints` | How to harvest new queries from scrape outputs | Apply from round 2 onward |
| `gaps_to_watch` | Gaps to close before claiming done | Each becomes an atomic file or documented unresolved-gap note |
| `stop_criteria` | Goalposts | Do not report done until all are met or explicitly unmet |

Degraded modes:
- No `goal` → generic 3-tool playbook (no tailored brief)
- Planner offline → compact stub naming the 3 tools, loop, and reddit-branch rule

### When to call
- **First call every session.** It is a strong recommendation, not a runtime gate — other tools work without it, you just use them worse.
- Call again only if the goal materially shifts mid-session.

---

## web-search

### Parameters
| Parameter | Type | Required | Description |
|---|---|---|---|
| `queries` | `string[]` | Yes | Up to 50 search queries, each running as a separate parallel Google search |
| `extract` | `string` | Yes | Semantic instruction for the classifier — what "relevant" means for THIS goal |
| `raw` | `bool` | No (default `false`) | Skip classifier, return raw ranked URL list |
| `scope` | `"web"` \| `"reddit"` \| `"both"` | No (default `"web"`) | Where to look — see table below |
| `verbose` | `bool` | No (default `false`) | Attach per-row scoring metadata + CONSENSUS labels on low-threshold hits (costs ~1.5KB extra) |

### Scope semantics

| scope | Effect | Use for |
|---|---|---|
| `"web"` | Open web, no augmentation | spec / bug / pricing / CVE / changelog / API |
| `"reddit"` | Appends `site:reddit.com`, filters to `/r/<sub>/comments/<id>/` permalinks, drops subreddit homepages | sentiment / migration / lived experience |
| `"both"` | Runs every query twice (web + reddit-scoped), merges, tags row source | Only when opinion-heavy AND needs official sources — 2× cost, don't default to this |

### What the classifier returns (default, `raw:false`)

- **Tiered sections**: `HIGHLY_RELEVANT`, `MAYBE_RELEVANT`, `OTHER` (or a compressed prose summary when the result set is small)
- **`## Synthesis`** — grounded conclusions with `[rank]` citations. Planning aid only — scrape the underlying URL before citing in an atomic file.
- **`## Gaps`** — open questions with ids
- **`## Suggested follow-up searches`** — refine queries tied to gap ids

Gaps + refine queries ARE your iteration plan. Feed them into round 2 verbatim, plus any new terms harvested from `scrape-links` `## Follow-up signals` sections.

5–15 queries = solid for narrow bugs. 25–35 = library comparisons. 40–50 = open-ended synthesis (the soft ceiling).

### Writing effective queries

Each query should attack a genuinely different angle. Goal: coverage, not repetition.

**The 7-angle framework:**
1. Direct topic — `"Next.js middleware authentication 2026"`
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

**For bugs:** Always lead with the exact error message in quotes. Highest-precision query possible.

**For comparisons:** Include "vs", "comparison", "benchmark" — and also "switched from X", "regret X", "problems with X" for critical negative signal.

**For reddit scope:** At least 25% of queries should carry negative signal (`"regret"`, `"switched from"`, `"broke in production"`, `"don't use"`). People who succeed rarely post — people who fail explain exactly what went wrong.

### Call aggressively + in parallel

One `web-search` per session is underuse. Normal is 2–4 rounds. Safe to fire orthogonal `web-search` calls in **parallel within one turn** for unrelated subtopics or when the brief's `primary_branch` is `"both"` (one call per scope).

### What NOT to do
- Treat returned URLs as answers (they're leads — scrape to read)
- Write 50 queries that are minor rewrites of each other
- Skip search operators (difference between noise and signal)
- Default to `scope: "both"` when one scope alone would do (doubles cost for no signal gain)

---

## scrape-links

### Parameters
| Parameter | Type | Required | Description |
|---|---|---|---|
| `urls` | `string[]` | Yes | HTTP/HTTPS URLs to fetch. Reddit post permalinks (`reddit.com/r/<sub>/comments/<id>/...`) are auto-detected and routed through the Reddit API; everything else flows through the HTTP scraper. Mix freely — both branches run in parallel. |
| `extract` | `string` | Yes | Pipe-separated SHAPE of what to pull from each page |

### Reddit routing (v6)

- Reddit post permalinks are auto-routed to the Reddit API → threaded post + full comment tree with authors, scores, and OP markers preserved.
- Non-reddit URLs flow through the HTTP scraper.
- Mix reddit + non-reddit URLs in one call — both branches run concurrently; results merge in original input order.
- Never manually partition your URL list — auto-detection handles it.
- Prefer contextually grouped batches: fire multiple parallel `scrape-links` calls when URL sets are unrelated (e.g. docs in one call, reddit threads in another) rather than one giant mixed batch.

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
| Reddit thread | `"agreement reasons\|dissent reasons\|verbatim quotes with attribution\|migration drivers"` |

### What each response contains

Per URL, the extractor returns:
- **`## Source`** — URL, page type (docs / github-thread / reddit / marketing / cve / paper / announcement / qa / blog / changelog / release-notes), page date, author
- **`## Matches`** — verbatim-preserved facts (numbers, versions, stacktraces, exact quotes)
- **`## Not found`** — explicit gaps the page did not answer
- **`## Follow-up signals`** — new terms + referenced-but-unscraped URLs that feed the next research loop

Harvest `## Follow-up signals` terms for the next round's `web-search`.

### Composition pattern

Typically follows `web-search`. Pick the 3–10 most promising URLs from search results (HIGHLY_RELEVANT + top 2–3 MAYBE_RELEVANT). Group thematically similar pages in the same call — they share the extraction prompt context.

For reddit threads: select posts with (a) 10+ comments, (b) visible disagreement in replies, (c) specific stack/environment details from the OP. Skip 1–3 comment threads and posts older than 18 months for active tech.

### Signals to look for in Reddit comment trees

- **"EDIT: this fixed it"** — confirmed solution
- **"After X months in production..."** — battle-tested
- **"I switched from X to Y because..."** — migration with reasons
- **"Don't do what the top comment says..."** — critical correction
- **Specific numbers** — p99 latency, memory usage, cost, scale
- **Library maintainer replies** — authority signals

### Failure modes
- **Anti-bot / Cloudflare** — try cached or CDN versions
- **SPA with JS rendering** — may fail on heavily client-rendered pages
- **Paywall** — find alternative free source
- **Truncated output** — reduce URL count or narrow extraction targets
- **Reddit 404 / removed post** — the Reddit branch returns a real API error per URL; other URLs in the same call complete normally

### What NOT to do
- Manually partition reddit vs. non-reddit URLs (auto-detection handles it)
- Use vague extraction targets ("tell me about this page")
- Scrape 20+ URLs at once (too shallow per page)
- Scrape just to cite — only scrape when you need to verify or discover
