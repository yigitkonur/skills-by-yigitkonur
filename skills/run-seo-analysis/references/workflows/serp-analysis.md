# SERP Analysis Workflow

Analyze search engine results pages, SERP features, and ranking landscapes.

## When to use

User wants: understand what ranks for a keyword, SERP features analysis, featured snippets, People Also Ask, local pack presence, AI overviews, paid vs organic breakdown, multi-engine analysis.

## The SEO practitioner's mental model

SERP analysis answers: "What does the search results page look like for my target keywords, and where are the opportunities?" Modern SERPs are complex — organic results, featured snippets, PAA boxes, AI overviews, local packs, videos, shopping results. Understanding the SERP landscape determines your content strategy.

## Workflow

### Phase 1: Organic landscape

```
resolve-geo(location: user's market, product: "serp")
→ analyze-serp(keyword: target_keyword, dataType: "organic", engine: "google", limit: 20)
```

**Key parameter decisions:**
| Parameter | Decision |
|-----------|----------|
| `mode` | `task` for bulk (50-80% cheaper) or `live` for immediate results |
| `device` | `desktop` (default) then `mobile` if mobile strategy matters |
| `resultFormat` | `advanced` (default, rich data) or `regular` (lighter) |
| `limit` | 10 for quick view, 20-50 for thorough, 100 for deep analysis |

### Phase 2: SERP features (run relevant ones in parallel)

```
analyze-serp(keyword: kw, dataType: "people_also_ask")
analyze-serp(keyword: kw, dataType: "related_searches")
analyze-serp(keyword: kw, dataType: "ai_overviews")  // Google only, may not trigger
analyze-serp(keyword: kw, dataType: "knowledge_graph")
```

**When to check each feature:**
| dataType | When | Why |
|----------|------|-----|
| `people_also_ask` | Always | Content ideas, FAQ schema opportunities |
| `related_searches` | Always | Keyword expansion, topic clusters |
| `ai_overviews` | Informational queries | Understand AI-generated answer landscape |
| `local_pack` | Local businesses | Local SEO opportunity assessment |
| `images` | Visual content keywords | Image SEO opportunities |
| `videos` | How-to, tutorial keywords | Video content strategy |
| `shopping` | Product keywords | E-commerce SERP share |
| `paid` | Commercial keywords | PPC competition level |
| `featured_snippets` | Informational keywords | Position 0 opportunities |
| `news` | Current events keywords | News carousel opportunities |

### Phase 3: Multi-engine (if relevant)

```
analyze-serp(keyword: kw, dataType: "organic", engine: "bing")
analyze-serp(keyword: kw, dataType: "organic", engine: "youtube")  // for video content
```

**Supported engines:** google, youtube, bing, yahoo, baidu, naver, seznam

### Phase 4: Competitive SERP intelligence

```
analyze-keywords(keywords: [keyword], dataType: "difficulty")
analyze-keywords(keywords: [keyword], dataType: "intent")
analyze-domain(target: top_ranking_domain, dataType: "overview")
```

**Why:** Combines SERP data with keyword metrics and top-ranker intelligence for a complete picture.

### Phase 5: Autocomplete and related discovery

```
analyze-serp(keyword: seed, dataType: "autocomplete", engine: "google", limit: 50)
```

**Why:** Autocomplete reveals actual user search behavior — long-tail variations that may have lower competition.

## Interpreting results: SERP opportunity signals

| SERP characteristic | Opportunity |
|--------------------|-------------|
| No featured snippet for informational query | Win position 0 with structured content |
| PAA box present with weak answers | Create better answer content |
| AI overview cites few sources | Opportunity to become a cited source |
| Local pack appears but you're not in it | Local SEO optimization needed |
| Video carousel appears | Create video content for this keyword |
| Low domain authority in top 10 | Realistic ranking opportunity |
| SERP dominated by forums/UGC | Authoritative content can outrank |

## Cost optimization

**Use `mode: task` for bulk SERP analysis.** This is the single biggest cost saver:
- `mode: live`: Immediate results, full price
- `mode: task`: Async results (poll with `manage-tasks`), 50-80% cheaper
- Use `priority: 2` for lower cost (slower processing)

**Batch strategy:** Analyze 5-10 keywords per session, not 100. Focus on decision-quality data.

## Next workflow suggestions

- **Keyword research** → expand from SERP insights
- **Content optimization** → create content targeting identified opportunities
- **Competitor analysis** → deep dive into top-ranking domains
- **Rank tracking** → monitor your positions for analyzed keywords
