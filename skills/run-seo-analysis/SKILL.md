---
name: run-seo-analysis
description: Use skill if you are running SEO workflows with MCP Marketers tools — site audits, keyword research, backlink analysis, competitor intelligence, SERP analysis, rank tracking, or content optimization.
---

# SEO Analysis — MCP Marketers

Use this skill to run disciplined, multi-tool SEO analysis workflows using the MCP Marketers server's 32 tools. Do not call tools in isolation. Most analysis calls hit paid DataForSEO APIs, while setup/report/read helpers are free or cached — cost awareness and correct chaining are still critical.

## Activation boundaries

### Use this skill when

- Running a technical SEO audit on a website
- Discovering and analyzing keywords for a domain or topic
- Analyzing or comparing backlink profiles
- Investigating competitors and domain overlaps
- Analyzing SERP features and ranking landscapes
- Tracking keyword ranking positions over time
- Planning content strategy based on keyword gaps and trends
- Monitoring brand visibility in AI/LLM responses
- Analyzing local business presence and reviews
- Optimizing app store listings or e-commerce product SEO

### Do not use this skill when

- Writing application code or building MCP servers — use `build-mcp-use-server` instead
- Reviewing a pull request — use `review-pr` instead
- Researching a coding bug or library choice — use `run-research` instead
- Planning work without running SEO tools — use `plan-work` instead
- Auditing a local HTML snapshot, `file://` page, or private localhost preview with no public ingress. This skill requires a publicly reachable HTTP/HTTPS target or a different local audit workflow.

## Runtime assumptions and preflight

This skill assumes the MCP Marketers tool surface is already connected, authenticated, and billable in the current runtime. Before Step 0, confirm the checks that apply to the selected workflow:

| Check | What must be true before the first analysis call |
|---|---|
| Tool surface | The runtime exposes the workflow's starting tool and any mandatory follow-up helpers named in the first reference file. If the user wants a compiled deliverable, also confirm `start-report-workflow` and `compile-report`. If you choose an async mode such as `mode: "task"`, also confirm `manage-tasks`. |
| Input type | Site crawl workflows need a publicly reachable HTTP/HTTPS target. Domain/business/app/product workflows need a valid identifier for that tool family (domain, place ID/query, `appId`, ASIN/product ID). Keyword/SERP/trends/AI-query workflows can run with keywords or queries only and do not require a public site unless later steps add one. |
| Billing | The current environment is allowed to make paid DataForSEO-backed calls for the workflow you plan to run. |

Hard blockers: missing starting tool, unsupported input type, local-only crawl target, or no billing authority. Stop before the first paid analysis call when any hard blocker is present. If a later helper tool is missing, continue only when the workflow reference explicitly gives a fallback; otherwise stop and report the missing tool instead of improvising with unrelated tools.

## Core operating rules

1. **Resolve geography first.** If the user mentions a non-US location, run `resolve-geo` before any analysis tool. Most tools silently default to US/English — wrong geo wastes paid API calls. `resolve-geo` itself is a free setup step.
2. **Start report workflows for deliverables.** Run `start-report-workflow` before analysis if the user wants a compiled report. All tool outputs auto-capture. Compile at the end with `compile-report`. These report helpers are free orchestration steps.
3. **Follow nextSteps without abandoning the base workflow.** Tool `nextSteps` refine the current workflow; they do not replace the Workflow Selector. Finish the core sequence first, then take high-priority `nextSteps` that stay inside the same workflow branch.
4. **Batch keywords.** One call with 500 keywords is far cheaper than 500 calls with 1 keyword. Use `analyze-keywords` and `research-keywords` with arrays.
5. **Use task mode for SERP.** `analyze-serp(mode: "task")` saves 50-80% over `mode: "live"`. Use `manage-tasks` to poll results.
6. **Set explicit limits.** Defaults are generous (100-1000). Lower `limit` when you only need top results.
7. **Handle large result sets.** When a tool returns >50 rows and creates a dataset handle, use `read-result-set` to paginate/filter/aggregate. Use `export-result-set` for downloads.
8. **Never orphan a tool call.** A single `audit-site` or `research-keywords` without follow-up tools is incomplete analysis. Chain to the next step.
9. **Confirm before expensive operations.** Ask the user before running `audit-site` with `maxPages > 200` or `enableJs: true`, `analyze-serp` in live mode on >5 keywords, or `analyze-ai-presence(dataType: "llm_response")`.
10. **Track costs.** Analysis responses include cost data. Report estimated spend after multi-tool workflows and distinguish free orchestration calls from paid analysis calls.

## Workflow selector

Before starting, identify the user's goal in this table. Read the first reference file listed, then follow the tool sequence.

These tool sequences omit `start-report-workflow` and `manage-tasks` for brevity. Insert `start-report-workflow` before the first analysis call whenever the user wants a compiled deliverable. Insert `manage-tasks` whenever you deliberately choose an async/task mode and need to wait for the result before continuing.

| User goal | Start with | Tool sequence | Key references (read first before starting) |
|---|---|---|---|
| Site health / technical audit | `audit-site` | `resolve-geo -> audit-site(instant) -> audit-site(lighthouse) -> audit-site(redirect_chains, duplicate_tags) -> analyze-domain(overview) -> compile-report` | `references/workflows/site-audit.md` |
| Find keyword opportunities | `research-keywords` | `resolve-geo -> research-keywords(related) -> analyze-keywords(difficulty) -> analyze-keywords(intent) -> analyze-serp(organic) -> find-keyword-gaps -> compile-report` | `references/workflows/keyword-research.md` |
| Competitor intelligence | `analyze-competitors` | `resolve-geo -> analyze-competitors(domain) -> compare-domains(overview) -> find-keyword-gaps -> compare-backlinks -> find-link-opportunities -> compile-report` | `references/workflows/competitor-analysis.md` |
| Backlink profile / link building | `analyze-backlinks` | `resolve-geo -> analyze-backlinks(backlinks) -> analyze-backlinks(spam_scores, referring_domains, anchors) -> track-backlinks(growth_summary) -> find-link-opportunities -> compile-report` | `references/workflows/backlink-analysis.md` |
| SERP features / ranking landscape | `analyze-serp` | `resolve-geo -> analyze-serp(organic) -> analyze-serp(people_also_ask, related_searches) -> analyze-keywords(difficulty) -> compile-report` | `references/workflows/serp-analysis.md` |
| Track ranking positions | `track-rankings` | `resolve-geo -> track-rankings(current) -> track-rankings(changes) -> analyze-serp(organic, for movers) -> compile-report` | `references/workflows/rank-tracking.md` |
| Content strategy / gaps | `analyze-content` | `resolve-geo -> analyze-content(search) -> research-keywords(related) -> analyze-keywords(intent) -> find-keyword-gaps -> generate-content(subtopics) -> compile-report` | `references/workflows/content-optimization.md` |
| AI/LLM brand visibility | `analyze-ai-presence` | `analyze-ai-presence(mentions) -> analyze-ai-presence(top_domains) -> analyze-ai-presence(keyword_data) -> analyze-serp(ai_overviews) -> compile-report` | `references/workflows/ai-presence.md` |
| Local business SEO | `analyze-business` | `resolve-geo -> analyze-business(profile) -> analyze-business(reviews) -> analyze-serp(local_pack) -> research-keywords(related) -> compile-report` | `references/workflows/local-seo.md` |
| App store optimization | `analyze-app` | `resolve-geo -> analyze-app(info) -> analyze-app(keyword_rankings) -> analyze-app(competitors) -> analyze-app(reviews) -> compile-report` | `references/workflows/aso.md` |
| E-commerce product SEO | `analyze-products` | `resolve-geo -> analyze-products(search) -> analyze-products(product_info, reviews) -> platform-specific follow-ups -> research-keywords(related) -> compile-report` | `references/workflows/ecommerce-seo.md` |
| Market trends / rising topics | `analyze-market-trends` | `resolve-geo -> analyze-market-trends(rising_searches) -> research-trends(explore) -> research-keywords(related) -> analyze-keywords(difficulty) -> compile-report` | `references/workflows/trends-analysis.md` |
| Full comprehensive report | Combine workflows | `start-report-workflow -> site-audit sequence -> keyword sequence -> backlink sequence -> competitor sequence -> compile-report` | Read all relevant workflow refs |

## Execution sequence

### 0) Route and orient

1. Confirm the MCP Marketers tool surface is available for the chosen workflow. Minimum surface: the starting tool, any mandatory helpers in the first workflow reference, `compile-report` plus `start-report-workflow` if the user wants a compiled deliverable, and `manage-tasks` if you plan to use async/task modes.
2. Confirm the chosen workflow's input is supported. Crawl-based site audits need a publicly reachable HTTP/HTTPS target. Domain/business/app/product workflows need the correct identifier format. Keyword/SERP/trends/AI-query workflows do not need a public site unless later steps introduce one.
3. Find the user's goal in the Workflow Selector table.
4. Read the **first** reference file listed for that workflow.
5. If the user specifies a non-US location, run `resolve-geo` first.
6. If the user wants a deliverable, run `start-report-workflow` first.

### 1) Run the primary tool

Call the starting tool from the Workflow Selector with appropriate parameters. Consult `references/guides/parameter-guide.md` for non-obvious parameter choices.

### 2) Chain to follow-up tools

Follow the tool sequence from the Workflow Selector. At each step:
- Check the tool response's `nextSteps` for additional relevant tools
- Use `read-result-set` if the response created a dataset handle
- Adjust parameters based on results (e.g., narrow `limit` after initial broad scan)

Use this prioritization rule:
- First: complete the static tool sequence for the chosen workflow
- Second: take `nextSteps` marked or described as direct continuations of the current phase
- Third: defer optional branch suggestions until the core workflow is complete

Example `nextSteps` shape:

```json
{
  "nextSteps": [
    {
      "tool": "audit-site",
      "params": { "dataType": "lighthouse", "pageUrl": "https://example.com/" },
      "reason": "Validate performance and CWV after the instant crawl found critical issues",
      "priority": "high"
    },
    {
      "tool": "audit-site",
      "params": { "dataType": "duplicate_tags", "taskId": "task_123" },
      "reason": "Inspect duplicate metadata from the same crawl",
      "priority": "medium"
    }
  ]
}
```

In that example, run the high-priority `lighthouse` step if it matches the current site-audit branch, then continue with other site-audit follow-ups. Do not jump to unrelated workflows just because they appear in `nextSteps`.

### 3) Interpret results with domain knowledge

Do not return raw tool output. Interpret findings using SEO domain expertise from `references/guides/seo-domain-knowledge.md`. Flag severity levels: critical issues that need immediate action vs. medium-priority optimizations vs. nice-to-haves.

### 4) Compile and deliver

Run `compile-report` to gather all tool outputs into a unified report. Summarize key findings, prioritized actions, and estimated API cost.

## Tool quick-reference

When unsure which tool to use, consult `references/guides/tool-selection-matrix.md` for the full mapping of user questions to tools and follow-ups.

When optimizing for API cost, consult `references/guides/cost-optimization.md` for tier-based cost strategy and specific savings patterns.

## Pitfalls

| Pitfall | Fix |
|---|---|
| Forgetting geo resolution | Run `resolve-geo` before any location-sensitive tool |
| Using `mode: live` for bulk SERP | Use `mode: task` — saves 50-80% |
| Unbounded keyword lists | Set `limit`, `minVolume`, `maxDifficulty` |
| Running audit-site with default maxPages on huge sites | Set `maxPages: 50` for quick, `maxPages: 200` for standard |
| Comparing >5 domains at once | `compare-domains` and `compare-backlinks` cap at 5 |
| Ignoring nextSteps | Use high-priority `nextSteps` that continue the current workflow branch after the base sequence is underway |
| Not starting a report workflow | Call `start-report-workflow` first if user wants a deliverable |
| Keyword research without intent check | Always follow with `analyze-keywords(dataType: intent)` |
| Confusing the two trends tools | `analyze-market-trends` = "what's trending?" (discovery); `research-trends` = "how is this keyword trending?" (tracking) |
| Running expensive tools without confirmation | Ask before `audit-site(enableJs: true)`, `analyze-serp(mode: live, bulk)`, or `analyze-ai-presence(llm_response)` |

## Reference routing

### Workflows

| File | Read when |
|---|---|
| `references/workflows/site-audit.md` | Technical SEO audit, site health, page speed, crawl issues |
| `references/workflows/keyword-research.md` | Keyword ideas, search volume, difficulty, intent analysis |
| `references/workflows/competitor-analysis.md` | Competitive intelligence, domain comparison, keyword gaps |
| `references/workflows/backlink-analysis.md` | Link profile analysis, link building, disavow preparation |
| `references/workflows/serp-analysis.md` | SERP features, ranking landscape, search results analysis |
| `references/workflows/rank-tracking.md` | Ranking position monitoring, change detection |
| `references/workflows/content-optimization.md` | Content strategy, content gaps, topic clusters |
| `references/workflows/ai-presence.md` | AI/LLM brand visibility, mentions, citations |
| `references/workflows/local-seo.md` | Local business SEO, reviews, Google Business |
| `references/workflows/aso.md` | App store optimization, mobile app analytics |
| `references/workflows/ecommerce-seo.md` | Product SEO, Amazon/Google Shopping optimization |
| `references/workflows/trends-analysis.md` | Trend discovery, rising searches, seasonal patterns |

### Guides

| File | Read when |
|---|---|
| `references/guides/tool-selection-matrix.md` | Unsure which tool fits the task |
| `references/guides/cost-optimization.md` | Planning workflows with many API calls |
| `references/guides/seo-domain-knowledge.md` | Interpreting results, advising users, understanding SEO metrics |
| `references/guides/parameter-guide.md` | Setting non-obvious parameters, understanding defaults and limits |
