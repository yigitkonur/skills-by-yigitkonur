# Tool Selection Matrix

Quick reference: which tool for which task.

## By SEO task

| Task | Primary tool | Key dataType | Follow-up tools |
|------|-------------|-------------|-----------------|
| **Site health check** | `audit-site` | instant, lighthouse | analyze-domain (overview) |
| **Find keyword ideas** | `research-keywords` | related, suggestions | analyze-keywords (difficulty) |
| **Check keyword metrics** | `analyze-keywords` | difficulty, intent, overview | analyze-serp (organic) |
| **Compare keywords** | `compare-keywords` | — | research-keywords (expand winner) |
| **Find keyword gaps** | `find-keyword-gaps` | domains, pages | analyze-keywords (validate gaps) |
| **Domain overview** | `analyze-domain` | overview | analyze-competitors, audit-site |
| **Compare domains** | `compare-domains` | overview, traffic | find-keyword-gaps |
| **Find competitors** | `analyze-competitors` | domain, serp | compare-domains, find-keyword-gaps |
| **Check backlinks** | `analyze-backlinks` | backlinks, referring_domains | track-backlinks, find-link-opportunities |
| **Compare link profiles** | `compare-backlinks` | — | find-link-opportunities |
| **Track link changes** | `track-backlinks` | new_backlinks, lost_backlinks | analyze-backlinks (full profile) |
| **Find link opportunities** | `find-link-opportunities` | domain_intersection | analyze-backlinks (evaluate targets) |
| **SERP analysis** | `analyze-serp` | organic, ai_overviews | analyze-keywords, track-rankings |
| **Track rankings** | `track-rankings` | current, changes | analyze-serp (diagnose changes) |
| **Content analysis** | `analyze-content` | search, sentiment | generate-content, research-keywords |
| **Generate content** | `generate-content` | text, meta_tags, subtopics | analyze-content (validate) |
| **AI brand visibility** | `analyze-ai-presence` | mentions, top_domains | analyze-serp (compare with SERP) |
| **Local business SEO** | `analyze-business` | profile, reviews | analyze-serp (local_pack) |
| **App store optimization** | `analyze-app` | keyword_rankings, competitors | research-keywords (web keywords) |
| **Product SEO** | `analyze-products` | search, reviews | research-keywords (product keywords) |
| **Trending topics** | `analyze-market-trends` | top_searches, rising_searches | research-keywords (validate) |
| **Keyword trends** | `research-trends` | explore, related_queries | analyze-keywords (metrics) |
| **Resolve location** | `resolve-geo` | — | Any location-dependent tool |
| **API reference data** | `get-reference-data` | locations, languages, categories | resolve-geo |

## By user question

| User asks... | Start with | Then |
|-------------|------------|------|
| "How's my site doing?" | analyze-domain (overview) | audit-site (instant), analyze-backlinks |
| "What keywords should I target?" | research-keywords (related) | analyze-keywords (difficulty + intent) |
| "Who are my competitors?" | analyze-competitors (domain) | compare-domains, find-keyword-gaps |
| "Are my backlinks healthy?" | analyze-backlinks (spam_scores) | analyze-backlinks (referring_domains) |
| "How do I rank for X?" | track-rankings (current) | analyze-serp (organic) |
| "What content should I create?" | find-keyword-gaps | analyze-content, generate-content |
| "Am I visible in ChatGPT?" | analyze-ai-presence (mentions) | analyze-ai-presence (top_domains) |
| "How are my Google reviews?" | analyze-business (reviews) | analyze-business (profile) |
| "What's trending in my industry?" | analyze-market-trends (rising) | research-trends (explore) |
| "How does my app rank?" | analyze-app (keyword_rankings) | analyze-app (competitors) |
| "How do my products rank?" | analyze-products (search) | analyze-products (reviews) |

## Utility tools (use as needed)

| Tool | When to use |
|------|------------|
| `resolve-geo` | Before ANY location-sensitive analysis (always first if non-US) |
| `get-reference-data` | When you need valid location codes, language codes, categories, or filter options |
| `manage-tasks` | When using `mode: task` — check async results |
| `start-report-workflow` | When user wants a compiled deliverable |
| `compile-report` | At the end of any multi-tool workflow |
| `read-result-set` | When a tool returns a dataset handle (>50 rows) |
| `export-result-set` | When user wants CSV/JSON/TSV download |
| `download-data` | When downloading from a signed storage URL |
| `select-tools` | When using dynamic tool menu mode |

## Chaining rules

1. **Always start with context:** `resolve-geo` (if non-US) → `analyze-domain` (if domain-focused) or `research-keywords` (if keyword-focused)
2. **Follow nextSteps:** Every tool response includes suggested next tools — follow them
3. **End with compilation:** `compile-report` gathers all tool outputs into a unified report
4. **Large datasets:** If >50 rows returned, use `read-result-set` to paginate/filter/aggregate before showing to user
