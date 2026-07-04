# Tools — the planner + search + scrape

Use the Research Powerpack MCP server as the canonical tool surface.
Short aliases in this reference map to the current tool IDs:

| Alias | MCP tool |
|---|---|
| `get-research-consultancy` | `mcp__research-powerpack__get-research-consultancy` |
| `web-search` | `mcp__research-powerpack__web-search` |
| `scrape-link` | `mcp__research-powerpack__scrape-link` |

If the MCP server is unavailable, use built-in `WebSearch` for targeted
search and `WebFetch` for extraction. If those fail, use `curl` and parse
the result manually.

Three tools. One planner, one search, one scrape. There is no raw-vs-smart
axis anymore — `web-search` is always the cheap, unfiltered, keywords-only
recon tool, and `scrape-link` always runs LLM extraction against a
required `extract`. The only per-call decision left is *what* to search
for and *what* to extract, not *which variant* of a tool to call.

Reddit is reached through `web-search` keyword probes
(`site:reddit.com/r/.../comments`), not a scope parameter. Reddit post
permalinks passed to `scrape-link` still route through the Reddit API
first — full threaded post plus comment tree — before extraction runs on
top. For sentiment or dissent work, write an `extract` that explicitly
asks for verbatim quotes with author/score attribution so the threading
detail survives into the extracted output (e.g. `verbatim quotes with
author + score | agreement reasons | dissent reasons | migration
drivers`).

This file covers every parameter, every output format, every threshold
observed in real sessions. For prompting principles (how to write a good
`goal` or `extract`), read `prompting.md`.

---

## get-research-consultancy

The planner. Call first, every session. Returns a goal-tailored brief.

### Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `goal` | string | Yes (always pass one) | One paragraph stating topic, use case, known unknowns, skip list, freshness window, quote discipline. See `prompting.md` for goal-writing. |
| `include_playbook` | bool | No (default false) | Attach the verbose 3-tool tactic reference on top of the brief. Default off; pass `true` only when the agent specifically needs the tactic playbook. |

### What it returns

The server returns a goal-tailored brief with these fields:

| Field | Meaning | How to use it |
|---|---|---|
| `goal_class` | `spec` \| `bug` \| `migration` \| `sentiment` \| `pricing` \| `security` \| `synthesis` \| `product_launch` \| `other` | Anchors the `extract` shape for downstream calls |
| `primary_branch` | `"reddit"` \| `"web"` \| `"both"` | The single highest-leverage decision in the session — dictates whether round-1 keywords lead with `site:reddit.com/r/.../comments` probes, plain web probes, or both |
| `first_call_sequence` | Ordered list of 1–3 exact tool calls (only `web-search` / `scrape-link` steps) | Fire verbatim on round 1 |
| `keyword_seeds` | 25–50 ready queries | Feed as `keywords` to the first `web-search` call |
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

## web-search

Fan out search keywords in parallel. Returns a ranked, de-duplicated,
CTR-aggregated URL pool with snippets. No LLM filtering, no tiering, no
synthesis — every call returns the same shape regardless of how many
keywords you pass.

### Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `keywords` | string[] | Yes | 1–50 search keywords; each runs as a separate parallel Google retrieval. Write Google retrieval probes — `site:` operators, exact phrases in quotes, `OR`/`AND`. See `prompting.md`. |

There is no `extract`, `scope`, or `verbose` parameter. Reddit discovery
is done entirely by writing `site:reddit.com/r/.../comments` probes
inside `keywords` — mix them into the same call as web probes only when
you deliberately want a merged consensus list; otherwise split into
separate calls (see below).

### What it returns

- Ranked markdown list of URLs with title, snippet, and a CONSENSUS score
  (how many of your keywords surfaced this URL). Multiple keywords
  aggregate into one consensus list per call — there are no
  HIGHLY_RELEVANT/MAYBE/OTHER tiers, no `## Synthesis`, no `## Gaps`, and
  no `## Suggested follow-up searches`. `web-search` never reads page
  bodies and never runs an LLM.

### Operational notes

- **Fire multiple `web-search` calls in one turn when intents differ.**
  Plain web-probe keywords plus `site:reddit.com/r/.../comments` keywords
  as two parallel calls is the canonical reconnaissance pattern. Two
  parallel calls of 25 keywords each runs in roughly the time of one call.
  Mixing intents inside a single call's keyword set produces worse
  results because keywords compete for ranking budget.
- One `web-search` round per session is underuse. **Two to four rounds is
  normal** — round 1 reconnaissance, then refined rounds after capture
  harvested new terms from `scrape-link`'s `## Follow-up signals` and
  `## Not found`.
- Above ~25 keywords across 1–2 parallel calls, expect persistence to
  file. Plan a subagent-extract step from the start if the pool is going
  to be large.
- CONSENSUS score is the most reliable triage signal. URLs that appear in
  4+ keyword sets with score 100 are almost always the canonical
  authoritative page.
- Reddit permalink discovery is always keyword-driven now: every
  `reddit.com/r/.../comments/<id>/` URL a `site:reddit.com/r/.../comments`
  probe surfaces is a candidate for `scrape-link`.

---

## scrape-link

Fetch URLs in parallel, then always run per-URL LLM extraction against a
required `extract`. There is no no-LLM full-markdown scrape path anymore
— every call classifies and extracts.

### Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `urls` | string[] | Yes | 1–50 fully-qualified HTTP/HTTPS URLs. Reddit post permalinks (`reddit.com/r/<sub>/comments/<id>/...`) auto-route through the Reddit API for the full threaded post + comment tree, then extraction runs on top. Mix Reddit and non-Reddit URLs freely; both branches run concurrently. |
| `extract` | string | Yes | Pipe-separated SHAPE of what to pull from each page. The extractor classifies each page (docs / github-thread / reddit / blog / cve / changelog / etc.) and adapts emphasis. For Reddit, write an extract that explicitly requests verbatim quotes with author/score attribution to preserve threading detail. See `prompting.md`. |

### Provider stack (in order)

- Reddit post permalinks → Reddit API (threaded post + comments) → LLM
  extraction against `extract`
- Non-Reddit → Jina Reader → Jina Reader through Scrape.do proxy (when
  configured) → optional Kernel browser rendering for JS-heavy pages →
  LLM extraction against `extract`

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
| Reddit thread | `verbatim quotes with author + score \| agreement reasons \| dissent reasons \| migration drivers` |

### Operational notes

- Hard ceiling: 5 URLs per call. 6 sometimes works. 9 times out.
- Hard ceiling: 7 facets per `extract`. Beyond, the extractor fragments
  attention and quality drops on every facet.
- Latency is real: ~13 seconds per URL on dense pages. Budget for it.
- Reddit threading (author, score, indent depth, OP marker, edit marker)
  is preserved in the Reddit API fetch step, but only survives into the
  output if `extract` asks for it verbatim with attribution. A vague
  Reddit `extract` ("summarize the discussion") loses the threading
  detail that made raw Reddit capture valuable before — always write a
  quote-preserving `extract` for sentiment/dissent work.
- The five output sections are unique to this tool. `## Not found` is the
  most underrated; it tells you what to research next. `## Follow-up
  signals` seeds the next search round for free. `## Contradictions` is
  gold for sentiment work.
- `extract` must state what relevance means AND what irrelevance means.
  Vague extraction targets ("tell me about this page") consistently
  underperform 4–7 specific pipe-separated facets.

---

## Operational thresholds (extracted from observed runs)

| Decision | Threshold | Source |
|---|---|---|
| `scrape-link` URL ceiling | 5 URLs (timeouts at 9) | observed timeouts |
| `scrape-link` facet ceiling | 5–7 per call | extraction fragments beyond |
| `web-search` → context overflow | 25+ keywords across 2+ parallel calls | observed 130KB overflow |
| Persistence-to-file threshold | ~50KB output | runtime behaviour |
| Reddit `scrape-link` sweet spot | ≤5 threads per call | comment volume |
| `web-search` keyword fan-out | 15–50 keywords | full range useful since there is no classifier to pay for |
| `scrape-link` latency | ~13 seconds per URL on dense pages | observed |
| Non-Reddit `scrape-link` batch size | ≤2 URLs on docs pages before bloat | repeated nav chrome bloat |

---

## Decision flowchart

### Need to find URLs?

```
├── General recon (docs, blogs, changelogs, GitHub)  → web-search with plain probes
├── Reddit permalink discovery                        → web-search with
│                                                          site:reddit.com/r/.../comments probes
├── Both needed in the same round                      → two parallel web-search calls
│                                                          (one plain, one site:reddit probes)
└── Multiple search rounds planned                     → web-search, keep the full pool as cache
```

### Need to scrape?

```
├── Any URL with a defined extract, ≤5 URLs      → scrape-link
├── Reddit threads, sentiment/dissent work        → scrape-link with a quote-preserving
│                                                    extract (verbatim quotes + author/score)
├── Mixed source types in one call                → scrape-link (it adapts per page type)
├── Extraction shape genuinely undecided          → write a broad extract and refine next round
└── Provider cascade failed                       → see failure-modes.md
```

### Need to know if you are done?

Re-read the `get-research-consultancy` brief's `gaps_to_watch` and
`stop_criteria`. If every gap is closed and the last search round
surfaced no new terms, stop. If not, run another round.

---

## Output sections (`scrape-link`)

These five sections are unique to `scrape-link`. Internalize them.

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

- Treat returned snippets as evidence. Snippets are leads; only scraped
  page content is citable.
- Write 50 keywords that are minor adjective-rotations of each other.
- Manually partition Reddit vs non-Reddit URLs across `scrape-link`
  calls — auto-routing handles it.
- Use vague extraction targets ("tell me about this page"). Pipe-separated
  4–7 specific facets consistently outperform.
- Scrape 20+ URLs in one `scrape-link` call (will time out).
- Scrape just to cite — only scrape when verification or discovery is the
  goal.
- Write a Reddit `extract` that doesn't ask for verbatim attribution —
  you'll lose the threading detail that made the thread worth scraping.
