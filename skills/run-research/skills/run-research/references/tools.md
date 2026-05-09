# Tools — the 2×2 plus the planner

Use the Research Powerpack MCP server as the canonical tool surface.
Short aliases in this reference map to the current tool IDs:

| Alias | MCP tool |
|---|---|
| `start-research` | `mcp__research-powerpack__start-research` |
| `smart-web-search` | `mcp__research-powerpack__smart-web-search` |
| `raw-web-search` | `mcp__research-powerpack__raw-web-search` |
| `smart-scrape-links` | `mcp__research-powerpack__smart-scrape-links` |
| `raw-scrape-links` | `mcp__research-powerpack__raw-scrape-links` |

If the MCP server is unavailable, use built-in `WebSearch` for targeted
search and `WebFetch` for extraction. If those fail, use `curl` and parse
the result manually.

Five tools. Two axes (raw vs smart x search vs scrape). One planner.
The decisive choice:

- **If the output goes into context, prefer smart.** It returns less data
  and pre-digests it into structured sections.
- **If the output goes into a file or subagent, prefer raw.** It returns
  more data and lets the analysis happen where context budget is cheap.

Reddit comment threads are the canonical exception: `raw-scrape-links`
preserves comment threading (author, score, indent depth) that
`smart-scrape-links` compresses away. For sentiment work, raw on Reddit
beats smart even when output goes into context.

This file covers every parameter, every output format, every threshold
observed in real sessions. For prompting principles (how to write a good
`goal` or `extract`), read `prompting.md`.

---

## start-research

The planner. Call first, every session. Returns a goal-tailored brief.

### Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `goal` | string | Yes (always pass one) | One paragraph stating topic, use case, known unknowns, skip list, freshness window, quote discipline. See `prompting.md` for goal-writing. |
| `include_playbook` | bool | No (default false) | Attach the verbose 5-tool tactic reference on top of the brief. Default off; pass `true` only when the agent specifically needs the tactic playbook. |

### What it returns

The server returns a goal-tailored brief with these fields:

| Field | Meaning | How to use it |
|---|---|---|
| `goal_class` | `spec` \| `bug` \| `migration` \| `sentiment` \| `pricing` \| `security` \| `synthesis` \| `product_launch` \| `other` | Anchors the `extract` shape for downstream calls |
| `primary_branch` | `"reddit"` \| `"web"` \| `"both"` | The single highest-leverage decision in the session — dictates which scope and tool variants come first |
| `first_call_sequence` | Ordered list of 1–3 exact tool calls | Fire verbatim on round 1 |
| `keyword_seeds` | 25–50 ready queries | Feed as `keywords` to the first search call |
| `iteration_hints` | How to harvest new queries from scrape outputs | Apply from round 2 onward |
| `gaps_to_watch` | Gaps to close before claiming done | Each becomes an atomic file or documented unresolved-gap note |
| `stop_criteria` | Goalposts | Do not report done until all are met or explicitly unmet |

### When to call

- **First call every session that needs more than one tool call.** The
  brief's `gaps_to_watch` and `stop_criteria` are the only structured
  stopping condition the toolkit provides — they bind the loop.
- Call again if the goal materially shifts mid-session.

### When to skip

- Single targeted lookup ("what does flag X do") — overhead does not pay
  back.
- Production incident with a one-shot fact check — latency matters more
  than tailoring.

---

## raw-web-search

Fan out search keywords in parallel. Returns a ranked URL pool with
snippets. No LLM filtering, no synthesis.

### Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `keywords` | string[] | Yes | 1–50 search keywords; each runs as a separate parallel Google retrieval. Write Google retrieval probes — `site:` operators, exact phrases in quotes, `OR`/`AND`. See `prompting.md`. |

### What it returns

- Ranked markdown list of URLs with title, snippet, and CONSENSUS score
  (how many of your keywords surfaced this URL).

### When raw-web-search wins

- Output goes to a file or subagent for triage. Two parallel calls of 25
  keywords each can return >100KB in seconds — uncountable URLs. The
  expectation is that you subagent-extract the top 15.
- Multiple search rounds planned. The full URL pool is the cache for round
  two and beyond.
- Reddit permalink discovery — every `reddit.com/r/.../comments/<id>/` URL
  the search produces. The classifier in smart-search sometimes tiers
  comparable threads inconsistently; raw is more reliable for permalink
  harvesting.
- Domain reconnaissance — see which domains even cover this topic. Smart
  hides the long tail.
- Audit trail — every URL the session ever considered, persisted.

### When to skip

- Output goes directly into context. Use `smart-web-search` and let the
  classifier filter to a manageable size.

### Operational notes

- **Fire multiple `raw-web-search` calls in one turn when scopes differ.**
  Web-scoped keywords plus Reddit-scoped keywords as two parallel calls
  is the canonical reconnaissance pattern. Two parallel calls of 25
  keywords each runs in roughly the time of one call. Mixing scopes
  inside a single call's keyword set produces worse results because
  keywords compete for ranking budget.
- One `raw-web-search` round per session is underuse. **Two to four
  rounds is normal** — round 1 reconnaissance, then refined rounds after
  triage harvested new terms from scrape `## Follow-up signals` and
  smart-search `## Suggested follow-up searches`.
- Above ~25 keywords across 1–2 parallel calls, expect persistence to
  file. Plan a subagent-extract step from the start.
- CONSENSUS score is the most reliable triage signal. URLs that appear
  in 4+ keyword sets with score 100 are almost always the canonical
  authoritative page.

---

## smart-web-search

Fan out search keywords in parallel, then run LLM classification and
synthesis against `extract`.

### Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `keywords` | string[] | Yes | 1–50 keywords; same probe discipline as raw. |
| `extract` | string | Yes | Tells the *classifier* what relevance means for this goal. Drives tiering, gap analysis, refine-query suggestions. See `prompting.md`. |
| `scope` | `"web"` \| `"reddit"` \| `"both"` | No (default `"web"`) | Where to look — see scope semantics below. |
| `verbose` | bool | No (default false) | Attach per-row scoring, signals block, CONSENSUS labels. Costs ~1.5KB extra; only useful when triaging is genuinely hard. |

### Scope semantics

| `scope` | Effect | Use for |
|---|---|---|
| `"web"` | Open web, no augmentation | spec / bug / pricing / CVE / changelog / API |
| `"reddit"` | Appends `site:reddit.com`, filters to `/r/<sub>/comments/<id>/` permalinks, drops subreddit homepages | sentiment / migration / lived experience |
| `"both"` | Runs every keyword twice (web + Reddit-scoped), merges, tags row source | Only when opinion-heavy AND needs official sources — 2× cost, do not default to this |

### What it returns

- HIGHLY_RELEVANT / MAYBE_RELEVANT / OTHER tiers
- `## Synthesis` with `[rank]` citations — planning aid only; scrape the
  underlying URL before citing as evidence
- `## Gaps` — open questions with IDs
- `## Suggested follow-up searches` — refine queries tied to gap IDs

### When smart-web-search wins

- Output goes directly into context. Smart returns roughly 3–5× less data
  than raw because it filters before returning.
- You have a tight `extract` definition. The classifier needs a target;
  vague extracts produce vague tiers.
- One-shot research where the full URL pool is not needed as a cache.
- Topic where source authority matters — the classifier weights official
  docs and canonical sources higher than blog spam.
- Mixed-quality keyword set — smart drops weak keywords into OTHER
  quietly; raw forces you to read them.

### When to skip

- Reddit permalink discovery (raw is more reliable).
- Multi-round research where the URL pool is the cache (raw persists more).
- You will subagent-triage anyway — paying for the classifier just to
  re-triage in a subagent is double work.

### Operational notes

- `extract` must state what relevance means AND what irrelevance means.
  "MCP OAuth" produces useless tiering; "OAuth 2.1 in TypeScript MCP
  frameworks — runnable code, not marketing" produces tight tiers.
- **Fire multiple `smart-web-search` calls in parallel when scopes
  differ.** One `scope: "web"` call and one `scope: "reddit"` call in the
  same turn outperforms a single `scope: "both"` call because the
  classifier tunes its synthesis per-scope.
- `scope: "both"` doubles cost. Use only when one classification pass
  over a merged web+Reddit pool is genuinely wanted.
- Smart's synthesis is over titles and snippets, not page bodies. Do not
  cite from it; only scraped pages are evidence.
- 5–15 keywords for narrow questions; 25–35 for library comparisons;
  40–50 for open-ended synthesis (the soft ceiling).
- **Round 2 search after capture is the norm, not a luxury.** Feed
  `## Suggested follow-up searches` and harvested scrape signals back
  in. Do not paraphrase queries already run; the classifier tracks them.

---

## raw-scrape-links

Fetch URLs in parallel. Returns full markdown. Reddit auto-routes through
the Reddit API.

### Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `urls` | string[] | Yes | 1–50 fully-qualified HTTP/HTTPS URLs. Reddit post permalinks (`reddit.com/r/<sub>/comments/<id>/...`) auto-route through the Reddit API. Mix Reddit and non-Reddit URLs freely; both branches run concurrently. |

### What it returns

- Per URL, full markdown content. For Reddit post permalinks, threaded
  post plus the comment tree with author, score, indent depth, OP marker,
  and edit marker.

### Provider stack (in order)

- Reddit post permalinks → Reddit API
- Non-Reddit → Jina Reader → Jina Reader through Scrape.do proxy (when
  configured) → optional Kernel browser rendering for JS-heavy pages

### When raw-scrape-links wins

- Reddit threads (≤5 per call). Threading is not reconstructable from any
  other tool; this is the killer feature.
- Pages where the extraction shape is undecided. Capture full markdown;
  decide what matters later.
- Evidence-grade capture you might revisit. Raw markdown is canonical.
- Plan to subagent-extract afterward.

### When to skip

- You already know the facets you want and the URL is a long docs page.
  `smart-scrape-links` compresses better.

### Operational notes

- Reddit raw-scrape is reliably scoped (post + comments fits per call).
- Non-Reddit docs pages are unpredictable. A 2-page batch returned 80KB
  in one observed session due to repeated nav chrome. Plan persistence.
- Reddit threading: top-level comments, indented replies, vote counts, OP
  markers, edit markers — all preserved.
- For non-Reddit pages, expect 2 URLs ≈ persistence threshold on dense
  docs.

---

## smart-scrape-links

Fetch URLs in parallel, then run per-URL LLM extraction against `extract`.

### Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `urls` | string[] | Yes | 1–50 URLs; same auto-routing as raw-scrape. |
| `extract` | string | Yes | Pipe-separated SHAPE of what to pull from each page. The extractor classifies each page (docs / github-thread / reddit / blog / cve / changelog / etc.) and adapts emphasis. See `prompting.md`. |

### What it returns per URL

- `## Source` — URL, page type, page date, author
- `## Matches` — extracted facets, organized; verbatim where requested
- `## Not found` — what the page did NOT answer (the killer feature; read
  every time)
- `## Follow-up signals` — referenced URLs and concepts to chase next
  round
- `## Contradictions` — disagreements within the page or with prior
  context (sometimes; surfaced when relevant even when not explicitly
  requested)

### Common extraction shapes

| Page type / scenario | Extraction targets |
|---|---|
| API docs | `endpoints \| auth methods \| rate limits \| request format \| error codes` |
| Pricing page | `pricing tiers \| free tier limits \| overage costs \| included features \| enterprise contact` |
| Changelog | `breaking changes \| new features \| deprecations \| migration steps \| version dates` |
| Library README | `features \| install \| API examples \| requirements \| limitations \| license` |
| Benchmark | `results \| methodology \| hardware specs \| versions tested \| caveats` |
| Security advisory | `CVE ID \| CVSS score \| affected versions \| patched version \| mitigation steps` |
| Config reference | `options \| default values \| types \| required fields \| examples \| deprecated` |
| Bug fix article | `root cause \| fix code \| version affected \| workarounds \| environment conditions` |
| Reddit thread | `agreement reasons \| dissent reasons \| verbatim quotes with attribution \| migration drivers` |

### When smart-scrape-links wins

- Defined `extract` shape and ≤5 URLs.
- Long docs pages where only specific facts matter.
- Cross-source comparison — extract the same facets from N URLs, compare.
- Final evidence packs for synthesis.

### When to skip

- Reddit threads (raw preserves comment structure; threading is the
  evidence).
- Extraction shape genuinely undecided.

### Operational notes

- Hard ceiling: 5 URLs per call. 6 sometimes works. 9 times out.
- Hard ceiling: 7 facets per `extract`. Beyond, the extractor fragments
  attention and quality drops on every facet.
- Latency is real: ~13 seconds per URL on dense pages. Budget for it.
- The four output sections are unique to this tool. `## Not found` is the
  most underrated; it tells you what to research next. `## Follow-up
  signals` seeds the next search round for free. `## Contradictions` is
  gold for sentiment work.

---

## Operational thresholds (extracted from observed runs)

| Decision | Threshold | Source |
|---|---|---|
| `smart-scrape-links` URL ceiling | 5 URLs (timeouts at 9) | observed timeouts |
| `smart-scrape-links` facet ceiling | 5–7 per call | extraction fragments beyond |
| `raw-web-search` → context overflow | 25+ keywords across 2+ parallel calls | observed 130KB overflow |
| Persistence-to-file threshold | ~50KB output | runtime behaviour |
| Reddit `raw-scrape-links` sweet spot | ≤5 threads per call | comment volume |
| `smart-web-search` keyword fan-out | 15–50 keywords | classifier value > raw cost |
| `smart-scrape-links` latency | ~13 seconds per URL on dense pages | observed |
| Non-Reddit `raw-scrape-links` | ≤2 URLs on docs pages | repeated nav chrome bloat |

---

## Decision flowchart

### Need to find URLs?

```
├── Output goes into context, ≤25 keywords      → smart-web-search
├── Output goes into context, 25–50 keywords    → smart-web-search (it filters)
├── Output goes to file or subagent             → raw-web-search
├── Multiple search rounds planned              → raw-web-search (URL cache)
├── Reddit permalink discovery                  → raw-web-search
└── Domain reconnaissance                       → raw-web-search
```

### Need to scrape?

```
├── Reddit threads (≤5)                         → raw-scrape-links
├── Reddit threads (>5), need sentiment summary → smart-scrape-links
├── Docs page, defined extract, ≤5 URLs         → smart-scrape-links
├── Docs page, undecided extract                → raw-scrape-links + subagent
├── Mixed source types in one call              → smart-scrape-links (it adapts)
└── Provider cascade failed                     → see failure-modes.md
```

### Need to know if you are done?

Re-read the `start-research` brief's `gaps_to_watch` and `stop_criteria`.
If every gap is closed and the last search round surfaced no new terms,
stop. If not, run another round.

---

## Output sections (smart-* tools)

These four sections are unique to the smart tools. Internalize them.

**`## Source`** — URL, page type (`docs` / `github-thread` / `reddit` /
`marketing` / `cve` / `paper` / `announcement` / `qa` / `blog` /
`changelog` / `release-notes`), page date, author. Always present.

**`## Matches`** — extracted facets you asked for. Verbatim where you
asked for verbatim. Numbers, version strings, prices, error text, and
config keys preserved exactly when the `extract` instructed it.

**`## Not found`** — facets the page did NOT answer. Read every time.
Each line tells you which gap that source failed to close, which directly
determines the next search query. The most underrated section in the
toolkit.

**`## Follow-up signals`** — referenced URLs and concepts the extractor
surfaced as worth chasing. Free seed material for the next round. Often
produces URLs that would never have been searched for directly.

**`## Contradictions`** — surfaced when the page disagrees with itself or
with prior context in the call. Sometimes appears even when not explicitly
requested in `extract`. Gold for sentiment work — disagreement is more
informative than consensus.

---

## What NOT to do (cross-tool)

- Treat returned snippets or rank-cited synthesis as evidence. Both are
  leads; only scraped page content is citable.
- Write 50 keywords that are minor adjective-rotations of each other.
- Default to `scope: "both"` when one scope alone would do (doubles cost,
  no signal gain).
- Manually partition Reddit vs non-Reddit URLs across calls — auto-routing
  handles it.
- Use vague extraction targets ("tell me about this page"). Pipe-separated
  4–7 specific facets consistently outperform.
- Scrape 20+ URLs in one smart call (will time out).
- Scrape just to cite — only scrape when verification or discovery is the
  goal.
