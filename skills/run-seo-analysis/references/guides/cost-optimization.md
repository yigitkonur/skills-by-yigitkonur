# Cost Optimization Guide

Most analysis calls hit paid DataForSEO APIs. Setup, reference, stored-result, and report-session helpers do not. Minimize cost without sacrificing insight quality.

## Core principles

1. **Start small, expand if needed.** Use `limit: 10-50` for initial exploration, only increase if the user needs more depth.
2. **Use task mode for SERP.** `analyze-serp(mode: "task")` is 50-80% cheaper than `mode: "live"`.
3. **Batch keywords.** One call with 500 keywords is far cheaper than 500 calls with 1 keyword each.
4. **Use the right tool.** Don't use `analyze-serp` when `analyze-keywords` gives you what you need.
5. **Cache-friendly patterns.** Use `forceRefresh: false` (default) to benefit from cached results.

## Cost tiers by tool

| Tier | Tools | Strategy |
|------|-------|----------|
| **Low** | resolve-geo, get-reference-data, compare-keywords, compare-backlinks, select-tools | Use freely |
| **Low-Medium** | analyze-keywords, analyze-domain (overview), analyze-content, generate-content, analyze-market-trends, research-trends | Reasonable for exploration |
| **Medium** | research-keywords, find-keyword-gaps, analyze-backlinks, track-backlinks, find-link-opportunities, analyze-competitors | Set appropriate limits |
| **Medium-High** | analyze-serp (live), track-rankings (bulk), analyze-products (Amazon Labs), analyze-app | Use task mode when available |
| **High** | audit-site (full crawl), analyze-serp (bulk live), analyze-ai-presence (llm_response), download-data (large) | Get user confirmation first |
| **Very High** | audit-site (full crawl + enableJs + 1000 pages) | Almost never needed — use instant first |

## Specific savings

### SERP analysis: task mode saves 50-80%

```
// Expensive
analyze-serp(keyword: kw, mode: "live")     // Full price, immediate

// Cheap
analyze-serp(keyword: kw, mode: "task")     // 50-80% off, async
→ manage-tasks(action: "ready", provider: "serp")  // Check when done
→ manage-tasks(action: "get", taskId: id)          // Retrieve results
```

### Keyword research: batch instead of individual

```
// Expensive: 10 API calls
research-keywords(keywords: ["kw1"], ...)
research-keywords(keywords: ["kw2"], ...)
... x10

// Cheap: 1 API call
research-keywords(keywords: ["kw1", "kw2", ..., "kw10"], ...)
```

### Site audits: start with instant

```
// Expensive: full crawl first
audit-site(target: domain, dataType: "full", maxPages: 1000, enableJs: true)

// Smart: instant first, expand only if needed
audit-site(target: domain, dataType: "instant", maxPages: 50)
// Review results, then if deeper analysis needed:
audit-site(target: domain, dataType: "full", maxPages: 200)
```

### Backlinks: use one_per_domain for deduplication

```
// Returns duplicate links from same domains
analyze-backlinks(target: domain, dataType: "backlinks", limit: 1000)

// Deduplicates — often half the rows with same insight
analyze-backlinks(target: domain, dataType: "backlinks", backlinkMode: "one_per_domain", limit: 500)
```

## When to ask user for confirmation

Ask before running:
- `audit-site` with `maxPages > 200` or `enableJs: true`
- `analyze-serp` with `mode: "live"` on more than 5 keywords
- `analyze-ai-presence` with `dataType: "llm_response"` (directly queries LLMs)
- `track-rankings` with `frequency: "daily"` (recurring cost)
- Any workflow touching more than 3 expensive tools in sequence

## Cost tracking

Every tool response includes cost data via `ToolResponse.withCost()`. Always report estimated spend to the user, especially after multi-tool workflows. The `compile-report` output includes cost summaries.

## Free operations

These don't hit paid APIs:
- `resolve-geo` — geo resolution from cached reference data
- `get-reference-data` — reference metadata (locations, languages, categories)
- `read-result-set` — reads already-fetched data from stored handles
- `select-tools` — tool menu configuration
- `start-report-workflow` — report session setup
- `compile-report` — compiles already-captured outputs

Treat these free operations as normal setup work, not optional luxuries. Skipping them to "save cost" usually causes worse downstream analysis.
