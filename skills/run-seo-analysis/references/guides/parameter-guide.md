# Parameter Guide

Key parameters across tools — defaults, recommended values, and when to change them.

## Universal parameters

### Public crawl targets

| Requirement | Rule | What to do if it fails |
|-----------|------|------------------------|
| `audit-site` or other crawl-based site/domain target | Must be a publicly reachable `http://` or `https://` URL/domain | Stop and ask for a public staging URL or tunnel |
| Local fixture or `file://` page | Unsupported for external crawl analysis | Use a different local audit method outside this skill |
| `localhost` or private preview | Usually unreachable by the external crawl provider | Expose it publicly first, then rerun |

Other workflows can use non-crawl identifiers instead of a public site: plain domains for competitor/backlink/rank tracking, place IDs or business queries for local SEO, `appId` values for ASO, and ASIN/product IDs for e-commerce.

### Location and language

| Parameter | Default | When to change |
|-----------|---------|---------------|
| `location` | US (if unset) | Always set explicitly for non-US markets |
| `language` | "en" | Always set for non-English markets |

**Always run `resolve-geo` first** to get canonical codes. Free-text like "Germany" may resolve differently across tools.

### Limits and pagination

| Parameter | Default | Min | Max | Strategy |
|-----------|---------|-----|-----|----------|
| `limit` | 100 (most tools) | 1 | 1000 | Start low (20-50) for exploration, increase for comprehensive analysis |
| `offset` | 0 | 0 | 20000 | Use for pagination of large result sets |
| `page_size` | 20 (read-result-set) | 1 | 200 | 20-50 is optimal for readability |

### Sorting

| sortBy value | When to use |
|-------------|------------|
| `volume` | Find highest-demand keywords |
| `difficulty` | Find easiest-to-rank keywords (order: asc) |
| `cpc` | Find highest commercial-value keywords |
| `traffic` | Find highest-traffic pages or keywords |
| `authority` | Find highest-quality backlinks |
| `date` | Find most recent backlinks |

## Tool-specific parameter decisions

### audit-site

| Parameter | Default | Recommended | Notes |
|-----------|---------|-------------|-------|
| `maxPages` | 100 | 50 (quick), 200 (standard), 500 (thorough) | Cost scales linearly |
| `enableJs` | false | false (unless SPA) | 3-5x cost increase when true |
| `device` | "desktop" | Run both if mobile matters | Mobile-first indexing |
| `maxCrawlDepth` | unlimited | 3-5 for most sites | Prevents crawling irrelevant deep pages |

### analyze-serp

| Parameter | Default | Recommended | Notes |
|-----------|---------|-------------|-------|
| `mode` | "live" | "task" for bulk | 50-80% cost savings |
| `priority` | 1 | 2 for non-urgent | Lower cost in task mode |
| `resultFormat` | "advanced" | "advanced" | Rich data; "regular" for lighter response |
| `expandQuery` | true | true | Adds related query probes |
| `screenshot` | false | false (unless needed) | Additional cost per screenshot |

### research-keywords

| Parameter | Default | Recommended | Notes |
|-----------|---------|-------------|-------|
| `source` | "labs" | "labs" for richest data | google_ads for ad metrics, clickstream for alternative volume |
| `minVolume` | none | 50-100 | Filters out zero/low-value keywords |
| `maxDifficulty` | none | 60-70 for most sites | Skip keywords you can't realistically rank for |
| `sortBy` | "volume" | "volume" or "traffic" | "difficulty" with order: "asc" for quick wins |
| `expandQuery` | true | true | Enriches seed keywords automatically |

### analyze-backlinks

| Parameter | Default | Recommended | Notes |
|-----------|---------|-------------|-------|
| `mode` | "domain" | "domain" usually | "page" for specific URL analysis |
| `backlinkMode` | "as_is" | "one_per_domain" for overview | Reduces duplicate links from same referring domain |
| `backlinksStatusType` | "all" | "live" for current profile | "lost" for investigating link loss |
| `sortBy` | "authority" | "authority" for quality | "date" for recency, "traffic" for value |

### track-rankings

| Parameter | Default | Recommended | Notes |
|-----------|---------|-------------|-------|
| `mode` | "task" | "live" (<=5 kw), "task" (6-100), "bulk" (>100) | Match mode to keyword count |
| `depth` | 100 | 50 (quick), 100 (standard), 200 (deep) | Higher depth = higher cost |
| `frequency` | "once" | "once" unless ongoing monitoring | "daily"/"weekly" = recurring costs |
| `include_serp_features` | false | true when SERP presence matters | Tracks featured snippets, PAA, etc. |

### analyze-ai-presence

| Parameter | Default | Recommended | Notes |
|-----------|---------|-------------|-------|
| `dataType` | "mentions" | Start with "mentions" | Progress to aggregated_metrics, top_domains |
| `expandQuery` | true | true for eligible types | Enriches AI-presence queries |
| `includeSubdomains` | true | true | Important for top_pages analysis |
| `sampleSynthesis` | none | Enable for multi-provider comparison | AI synthesis of cross-platform responses |

## Filter syntax

Many tools support `filters` as arrays of condition triplets:

```
filters: [["field_name", "operator", "value"]]
```

**Operators:** eq, neq, gt, gte, lt, lte, contains

**Common filter patterns:**
```
// Keywords with volume > 1000
filters: [["search_volume", "gt", 1000]]

// Backlinks from dofollow only
filters: [["dofollow", "eq", true]]

// Pages with title containing keyword
filters: [["title", "contains", "keyword"]]
```

## Engine support matrix

| Engine | analyze-serp | research-keywords | track-rankings | analyze-keywords |
|--------|-------------|------------------|---------------|-----------------|
| Google | Full support | Full (labs, google_ads) | Yes | Yes |
| Bing | Organic, paid | Yes (bing source) | Yes | Difficulty only |
| Yahoo | Organic | No | Yes | No |
| YouTube | Videos, comments | No | No | No |
| Baidu | Organic | No | Yes | No |
| Naver | Organic | No | Yes | No |
| Seznam | Organic | No | Yes | No |
