# App Store Optimization (ASO) Workflow

Mobile app analytics and app store optimization intelligence.

## When to use

User wants: app store optimization, app keyword research, app reviews analysis, app competitor analysis, app ranking charts, ASO strategy.

## The SEO practitioner's mental model

ASO answers: "How do I get more organic downloads from app store search?" Similar principles to SEO but for Google Play and Apple App Store. The practitioner needs keyword rankings, competitor analysis, review sentiment, and category positioning.

## Workflow

### Phase 1: App intelligence

```
resolve-geo(location: target_market, product: "app")
→ analyze-app(store: "google_play", dataType: "info", appId: app_id)
```

**Store-specific notes:**
| Store | Key differences |
|-------|----------------|
| `google_play` | More keyword-driven, faster indexing |
| `app_store` | Category-weighted, `device` param (iphone/ipad) |

### Phase 2: ASO keyword research

```
analyze-app(store: store, dataType: "keyword_research", keyword: seed_keyword, limit: 50)
→ analyze-app(store: store, dataType: "keyword_rankings", appId: app_id)
→ analyze-app(store: store, dataType: "aso_keywords", appId: app_id, limit: 100)
```

### Phase 3: Competitor analysis

```
analyze-app(store: store, dataType: "competitors", appId: app_id, limit: 20)
→ analyze-app(store: store, dataType: "keyword_overlap", appIds: [your_app, competitor_app])
→ analyze-app(store: store, dataType: "aso_competitors", appId: app_id)
```

### Phase 4: Reviews and ratings

```
analyze-app(store: store, dataType: "reviews", appId: app_id, depth: "comprehensive", limit: 100)
```

**Why:** Reviews reveal user pain points, feature requests, and keyword usage. Top negative reviews indicate ASO risks (low ratings hurt rankings).

### Phase 5: Category and chart performance

```
analyze-app(store: store, dataType: "charts", collection: "top_free", category: category_id, limit: 50)
→ analyze-app(store: store, dataType: "category_rankings", appId: app_id)
```

### Phase 6: Compile ASO report

```
compile-report(target: app_name, tool_names: ["analyze-app"])
```

## Interpreting results

| Signal | Action |
|--------|--------|
| Low keyword rankings for high-volume terms | Optimize app title, subtitle, and description |
| Competitor ranks for keywords you don't | Add those keywords to metadata |
| Rating below 4.0 | Address top complaints, then request re-reviews |
| Declining chart position | Investigate competitor launches, review quality, update frequency |
| High keyword overlap with competitor | Differentiate on unique features in description |

## Cost profile

All analyze-app operations require App Data API subscription. Costs scale with depth and limit.

## Next workflow suggestions

- **Keyword research** → web keyword research for app landing page
- **Competitor analysis** → web competitor analysis for app developer
- **Content optimization** → optimize app landing page content
