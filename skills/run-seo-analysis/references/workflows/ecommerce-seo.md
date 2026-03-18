# E-commerce SEO Workflow

Product SEO intelligence for Google Shopping and Amazon.

## When to use

User wants: product SEO, Amazon rankings, Google Shopping optimization, product keyword research, competitor product analysis, review analysis for products.

## The SEO practitioner's mental model

E-commerce SEO answers: "How do I get my products found in product search results?" This spans Google Shopping, Amazon search, and organic product-intent queries. The practitioner needs product keyword rankings, competitor pricing/positioning, review sentiment, and marketplace visibility.

## Workflow

### Phase 1: Product search landscape

```
resolve-geo(location: target_market, product: "merchant")
→ analyze-products(platform: "google_shopping", operation: "search", keyword: product_keyword, limit: 50)
```

**Platform decision:**
| Platform | When |
|----------|------|
| `google_shopping` | Google Shopping feed optimization |
| `amazon` | Amazon marketplace SEO |

### Phase 2: Product intelligence

```
analyze-products(platform: platform, operation: "product_info", productId: product_id)
→ analyze-products(platform: platform, operation: "reviews", productId: product_id, limit: 50)
→ analyze-products(platform: platform, operation: "sellers", productId: product_id)
```

### Phase 3: Amazon-specific analysis (if Amazon)

```
analyze-products(platform: "amazon", operation: "amazon_ranked_keywords", asin: asin, limit: 100)
→ analyze-products(platform: "amazon", operation: "amazon_product_competitors", asin: asin)
→ analyze-products(platform: "amazon", operation: "amazon_search_volume", keywords: [product_keywords])
→ analyze-products(platform: "amazon", operation: "amazon_related_keywords", keyword: seed)
```

**Amazon Labs operations:**
| Operation | What it reveals |
|-----------|----------------|
| `amazon_ranked_keywords` | Keywords your ASIN ranks for |
| `amazon_product_competitors` | Competing ASINs |
| `amazon_keyword_intersections` | Keyword overlap between ASINs |
| `amazon_rank_overview` | Ranking overview for ASINs |
| `amazon_search_volume` | Amazon search volume estimates |
| `amazon_related_keywords` | Related Amazon search terms |

### Phase 4: Product keyword research (web)

```
research-keywords(keywords: [product_keywords], dataType: "related", limit: 200)
→ analyze-serp(keyword: product_keyword, dataType: "shopping", engine: "google")
```

**Why web keywords too:** Many product searches happen on Google before Amazon. Optimize for both.

### Phase 5: Review analysis for insights

```
analyze-products(
    platform: "amazon",
    operation: "reviews",
    productId: asin,
    filterByStar: "critical",
    limit: 50
)
```

**Why critical reviews:** Reveals product weaknesses, common complaints, and opportunities to differentiate in listing copy.

### Phase 6: Compile e-commerce report

```
compile-report(target: product_or_brand, tool_names: ["analyze-products", "research-keywords", "analyze-serp"])
```

## Interpreting results

| Signal | Action |
|--------|--------|
| Low rankings for high-volume product keywords | Optimize product title, bullet points, description |
| Competitor ranks for keywords you don't | Add those keywords to product listing backend keywords |
| Negative review themes | Address in product description or improve product |
| Price significantly higher than competitors | Compete on value proposition, not price keywords |
| Missing from Google Shopping for target keywords | Fix product feed, verify merchant center setup |

## Cost profile

All analyze-products operations require Merchant API subscription.

| Operation | Relative cost |
|-----------|--------------|
| Product search | Low |
| Product info/reviews/sellers | Low |
| Amazon Labs operations | Medium |
| Full competitor analysis | Medium-High |

## Next workflow suggestions

- **Content optimization** → optimize product landing pages
- **Keyword research** → broader keyword strategy
- **Competitor analysis** → full competitive benchmarking
- **Rank tracking** → monitor product keyword rankings
