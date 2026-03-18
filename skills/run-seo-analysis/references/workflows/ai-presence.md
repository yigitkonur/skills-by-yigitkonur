# AI Presence Monitoring Workflow

Analyze and improve brand visibility in AI/LLM responses.

## When to use

User wants: brand visibility in ChatGPT/Perplexity/Gemini/Claude, AI mentions tracking, AI citations analysis, LLM response monitoring, AI-era SEO strategy.

## The SEO practitioner's mental model

AI presence analysis answers: "When someone asks an AI about my industry/product, does it mention my brand?" This is the emerging frontier of SEO — as users shift from search engines to AI assistants, visibility in LLM responses becomes a new ranking surface. The practitioner needs mentions tracking, citation analysis, and competitive benchmarking across AI platforms.

## Workflow

### Phase 1: Brand mention analysis

```
analyze-ai-presence(
    query: "brand_name OR product_name",
    dataType: "mentions",
    limit: 100
)
```

**Why start here:** Gives an immediate picture of how often your brand appears in AI responses. Establish a baseline before optimizing.

### Phase 2: Aggregated metrics

```
analyze-ai-presence(query: brand, dataType: "aggregated_metrics", dateFrom: "2024-01-01")
→ analyze-ai-presence(query: brand, dataType: "cross_aggregated_metrics")
```

**What each reveals:**
| dataType | Insight |
|----------|---------|
| `aggregated_metrics` | Mention volume over time, trending direction |
| `cross_aggregated_metrics` | Cross-platform comparison |

### Phase 3: Domain and page analysis

```
analyze-ai-presence(query: brand, dataType: "top_domains", limit: 50)
→ analyze-ai-presence(query: brand, dataType: "top_pages", includeSubdomains: true)
```

**Why:** Reveals which domains AI models cite most frequently for your topic. If competitors dominate citations, you know where to focus.

### Phase 4: Live LLM responses (optional, higher cost)

```
analyze-ai-presence(
    query: "best [product category]",
    dataType: "llm_response",
    llmPlatforms: ["chatgpt", "perplexity", "gemini"]
)
```

**Why:** Directly queries AI platforms and captures their responses. See exactly what they say about your brand/industry.

**Platform support:** chatgpt, perplexity, gemini, claude

### Phase 5: Keyword-level AI data

```
analyze-ai-presence(query: industry_keyword, dataType: "keyword_data", limit: 50)
```

**Why:** Shows which keywords trigger AI responses that mention your domain — the AI equivalent of "which keywords do I rank for."

### Phase 6: Compare with traditional SERP

```
analyze-serp(keyword: same_keyword, dataType: "ai_overviews", engine: "google")
analyze-serp(keyword: same_keyword, dataType: "organic", engine: "google")
```

**Why:** Compares your AI visibility with traditional search visibility. Gaps reveal where you're strong in one channel but weak in another.

### Phase 7: Compile AI presence report

```
compile-report(
    target: brand,
    tool_names: ["analyze-ai-presence", "analyze-serp"]
)
```

## Interpreting results

| Signal | Meaning | Action |
|--------|---------|--------|
| Brand mentioned in <10% of relevant queries | Low AI visibility | Focus on becoming a cited authority source |
| Competitor mentioned 3x more | Competitor dominates AI citations | Analyze their cited pages, create better content |
| High mentions but from wrong context | Brand association issues | Create authoritative content to shape narrative |
| Strong traditional SERP but weak AI presence | Channel gap | Optimize content for AI citation (structured, authoritative) |
| Rising mention trend | Growing AI visibility | Monitor and amplify what's working |

## How to improve AI visibility

1. **Create authoritative, well-structured content** — AI models favor comprehensive, well-organized pages
2. **Build citations from authoritative sources** — AI models weight cited sources by authority
3. **Use clear, factual language** — AI models prefer unambiguous, verifiable claims
4. **Maintain fresh content** — AI models increasingly favor recently updated content
5. **Earn links from high-authority domains** — citation authority correlates with link authority

## Cost profile

| Operation | Relative cost |
|-----------|--------------|
| mentions/aggregated_metrics | Low |
| top_domains/top_pages | Low |
| keyword_data | Medium |
| llm_response (live) | High |
| scrape_conversation | High |

## Next workflow suggestions

- **Content optimization** → optimize content for AI citation
- **Backlink analysis** → build authority for AI citation
- **Competitor analysis** → compare AI presence with competitors
- **Keyword research** → identify AI-relevant keywords
