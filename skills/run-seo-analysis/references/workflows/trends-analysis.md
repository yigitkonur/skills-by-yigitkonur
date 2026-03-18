# Trends Analysis Workflow

Trend discovery, seasonal planning, and market intelligence.

## When to use

User wants: trending topics, rising searches, seasonal keyword patterns, market trend analysis, Google Trends data, trend-based content planning.

## The SEO practitioner's mental model

Trends analysis answers: "What's gaining or losing interest, and how do I time my content?" Trends reveal seasonal patterns, emerging topics, and declining interests — critical for content calendars and strategic planning.

## Tool selection: analyze-market-trends vs research-trends

| Tool | Use when | Mental model |
|------|----------|-------------|
| `analyze-market-trends` | "What's trending?" — market-level discovery | **Discovery**: find what's hot |
| `research-trends` | "How is this keyword trending?" — keyword-specific tracking | **Tracking**: measure specific topics |

## Workflow

### Phase 1: Market discovery

```
resolve-geo(location: target_market, product: "trends")
→ analyze-market-trends(dataType: "top_searches", timeRange: "30d", limit: 50)
→ analyze-market-trends(dataType: "rising_searches", timeRange: "7d", limit: 50)
```

**Why both:** Top searches = sustained high interest. Rising searches = accelerating interest (emerging opportunities).

**timeRange decisions:**
| Range | Use for |
|-------|---------|
| `1d` | Breaking news, viral topics |
| `7d` | Weekly trends, campaign timing |
| `30d` | Monthly planning, content calendar |
| `90d` | Quarterly strategy |
| `1y` | Annual patterns, seasonality |
| `5y` | Long-term market shifts |

### Phase 2: Keyword-specific trend tracking

```
research-trends(
    keywords: [keyword1, keyword2, keyword3],
    source: "google_trends",
    dataType: "explore",
    timeRange: "1y"
)
```

**Why:** Compares up to 5 keywords' popularity over time — reveals which topics are growing vs declining.

### Phase 3: Geographic and demographic breakdown

```
research-trends(keywords: [keyword], dataType: "subregion")
research-trends(keywords: [keyword], dataType: "demographics")
research-trends(keywords: [keyword], dataType: "related_queries")
research-trends(keywords: [keyword], dataType: "related_topics")
```

**What each reveals:**
| dataType | Insight |
|----------|---------|
| `subregion` | Where interest is concentrated geographically |
| `demographics` | Age/gender interest breakdown |
| `related_queries` | Related search terms (expand keyword list) |
| `related_topics` | Broader topic associations |

### Phase 4: Historical SERP context (optional)

```
analyze-market-trends(keywords: [keyword], dataType: "historical_serps", timeRange: "1y")
```

**Why:** Shows how SERP results changed over time for a keyword — reveals shifts in what Google considers relevant.

### Phase 5: Validate with search volume

```
research-keywords(keywords: [trending_keywords], dataType: "overview")
→ analyze-keywords(keywords: [trending_keywords], dataType: "difficulty")
```

**Why:** Trends show relative interest, not absolute volume. Validate with actual search volume data before investing in content.

### Phase 6: Compile trends report

```
compile-report(target: market_or_topic, tool_names: ["analyze-market-trends", "research-trends", "research-keywords"])
```

## Interpreting results

| Pattern | Meaning | Action |
|---------|---------|--------|
| Steady upward trend (1y) | Growing market interest | Invest in content now |
| Spike then decline | Fad or one-time event | Don't invest in evergreen content |
| Annual cycle (repeats yearly) | Seasonal topic | Plan content calendar around peaks |
| Flat trend with rising related queries | Topic stable but context shifting | Update existing content |
| Declining trend | Waning interest | Deprioritize or pivot angle |

## Cost profile

| Operation | Relative cost |
|-----------|--------------|
| analyze-market-trends | Low |
| research-trends (Google Trends) | Low |
| research-trends (DataForSEO Trends) | Low-Medium |
| historical_serps | Medium |

## Next workflow suggestions

- **Keyword research** → deep dive on trending keywords
- **Content optimization** → create content for trending topics
- **Competitor analysis** → see who's capturing trending traffic
- **SERP analysis** → understand current SERP for trending terms
