# Keyword Research Workflow

Systematic keyword discovery and analysis using MCP Marketers tools.

## When to use

User wants: keyword ideas, search volume data, keyword difficulty, search intent, keyword gaps, content planning, topic clusters, question-based keywords.

## The SEO practitioner's mental model

Keyword research answers: "What are people searching for that my site could rank for?" The practitioner needs volume (demand), difficulty (competition), intent (what the searcher wants), and gaps (what competitors rank for but I don't). The output is a prioritized keyword list that drives content and optimization decisions.

## Workflow

### Phase 1: Seed discovery

```
resolve-geo(location: user's market, product: "keywords")
→ research-keywords(keywords: [seeds], dataType: "related", source: "labs", limit: 500)
```

**Why `related` first:** Broadest discovery — finds semantically related keywords from seed terms. Use `source: "labs"` for the richest data (includes difficulty, intent, SERP features).

**Parameter decisions:**
| Scenario | source | dataType | Notes |
|----------|--------|----------|-------|
| Broad discovery from seeds | labs | related | Best starting point, rich metrics |
| Questions people ask | labs | questions | Great for FAQ/blog content |
| Autocomplete suggestions | labs | suggestions | Long-tail, natural language |
| Keywords a site ranks for | labs | for_site | Requires `target` domain |
| Category-based discovery | labs | for_category | Requires category code from `get-reference-data` |
| Historical volume trends | google_ads | historical_data | For seasonal planning |
| Ad traffic estimates | google_ads | ad_traffic | For PPC/commercial intent |
| Clickstream volume data | clickstream | clickstream_search_volume | Alternative volume source |

### Phase 2: Validate and score

```
analyze-keywords(keywords: [top_candidates], dataType: "difficulty")
→ analyze-keywords(keywords: [top_candidates], dataType: "intent")
```

**Why both:** Difficulty tells you if you CAN rank; intent tells you if you SHOULD target it. A high-volume, low-difficulty keyword with wrong intent is a trap.

**Intent categories:**
| Intent | Meaning | Content type |
|--------|---------|-------------|
| informational | Learning/researching | Blog posts, guides, how-tos |
| navigational | Looking for a specific site | Brand pages, homepage |
| commercial | Comparing/evaluating | Comparison pages, reviews |
| transactional | Ready to buy/act | Product pages, landing pages |

### Phase 3: SERP validation

```
analyze-serp(keyword: top_keyword, dataType: "organic", engine: "google", limit: 20)
```

**Why:** Validates whether the SERP is realistically contestable. If the top 10 are all Wikipedia, government sites, and Fortune 500 companies, difficulty score alone doesn't tell the full story.

**What to check:**
- Domain authority of top 10 results
- SERP features present (featured snippets, PAA, local pack)
- Content types ranking (articles, products, videos)

### Phase 4: Gap analysis (competitive context)

```
find-keyword-gaps(
  targets: [user_domain, competitor1, competitor2],
  dataType: "domains",
  intersectionMode: "union",
  minVolume: 100,
  maxDifficulty: 60,
  limit: 1000
)
```

**Why:** Reveals keywords competitors rank for but you don't — the biggest growth opportunities. Use `intersectionMode: "union"` for the broadest gap view, `"intersect"` to find keywords ALL competitors share.

### Phase 5: Trend validation (optional but valuable)

```
research-trends(keywords: [top_5_candidates], source: "google_trends", dataType: "explore", timeRange: "1y")
```

**Why:** Ensures you're not targeting a declining keyword. A keyword with 10K monthly volume but -40% YoY trend is a poor investment.

### Phase 6: Compile deliverable

```
compile-report(target: domain_or_topic, tool_names: ["research-keywords", "analyze-keywords", "analyze-serp", "find-keyword-gaps"])
```

## Interpreting results: what to prioritize

| Signal | Action |
|--------|--------|
| High volume + low difficulty + matching intent | Top priority — target immediately |
| High volume + high difficulty + matching intent | Long-term target — build authority first |
| Low volume + low difficulty + high commercial intent | Quick wins — often convert well despite low volume |
| High volume + wrong intent | Skip unless you can match the intent |
| Declining trend (-20%+ YoY) | Deprioritize unless seasonal |
| Keyword gaps (competitors rank, you don't) | High priority — proven demand in your niche |

## Cost profile

| Operation | Relative cost | Notes |
|-----------|--------------|-------|
| research-keywords (500 seeds) | Medium | Batch seeds to reduce calls |
| analyze-keywords (1000 keywords) | Medium | Batch up to 1000 per call |
| analyze-serp (per keyword, live) | Medium-High | Use `mode: task` to save 50-80% |
| find-keyword-gaps (3 domains) | Medium | One call covers the gap analysis |

## Common mistakes

- **Too many seeds, too few filters:** Set `minVolume` and `maxDifficulty` to avoid drowning in low-value keywords
- **Ignoring intent:** Volume without intent matching leads to traffic that doesn't convert
- **Skipping SERP validation:** Difficulty scores are estimates — the actual SERP tells the truth
- **One-time research:** Keywords should be refreshed quarterly; trends shift

## Next workflow suggestions

- **Content optimization** → create/optimize content for winning keywords
- **Rank tracking** → monitor positions for targeted keywords
- **Competitor analysis** → deeper dive into competitor strategy
- **SERP analysis** → detailed SERP feature analysis for specific keywords
