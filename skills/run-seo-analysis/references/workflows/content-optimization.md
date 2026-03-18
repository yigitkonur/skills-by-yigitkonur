# Content Optimization Workflow

Content strategy, gap analysis, and AI-powered content generation.

## When to use

User wants: content strategy, content gaps, topic clusters, content quality analysis, AI content generation, meta tag optimization, content sentiment analysis, what to write about.

## The SEO practitioner's mental model

Content optimization answers: "What content should I create, improve, or remove to rank better?" The practitioner needs gap analysis (what's missing), quality analysis (what's underperforming), and competitive benchmarking (what's working for others). Content is the vehicle for keywords.

## Workflow

### Phase 1: Content landscape analysis

```
resolve-geo(location: user's market, product: "content")
→ analyze-content(keyword: topic, dataType: "search", limit: 50)
→ analyze-content(keyword: topic, dataType: "summary")
```

**What each reveals:**
| dataType | Returns | Use for |
|----------|---------|---------|
| `search` | Top content for a keyword | Understanding what exists |
| `summary` | Aggregated content metrics | Content landscape overview |
| `sentiment` | Positive/negative/neutral breakdown | Understanding audience reaction |
| `phrase_trends` | Trending phrases in content | Finding emerging subtopics |
| `rating` | Content quality/engagement scores | Identifying quality benchmarks |

### Phase 2: Keyword-content mapping

```
research-keywords(keywords: [topic_seeds], dataType: "related", limit: 200)
→ analyze-keywords(keywords: [top_candidates], dataType: "intent")
```

**Why intent is critical for content:** Intent determines content format:
| Intent | Content type to create |
|--------|----------------------|
| Informational | Blog posts, guides, how-tos, tutorials |
| Commercial | Comparison pages, reviews, "best of" lists |
| Transactional | Product pages, landing pages, pricing pages |
| Navigational | Optimize existing brand pages |

### Phase 3: Content gap analysis

```
find-keyword-gaps(
    targets: [user_domain, competitor1, competitor2],
    dataType: "domains",
    intersectionMode: "union",
    minVolume: 50,
    limit: 500
)
```

**Why:** Each gap keyword where competitors rank but you don't is a content opportunity. Group gaps by topic to plan content clusters.

### Phase 4: Content generation assistance

```
generate-content(input: keyword_or_topic, dataType: "subtopics")
→ generate-content(input: keyword_or_topic, dataType: "meta_tags")
→ generate-content(input: full_text, dataType: "grammar")
```

**Content generation options:**
| dataType | Use for | Key parameters |
|----------|---------|---------------|
| `text` | Generate full article | `targetLength` (1-1000 words), `creativityLevel` (0-1) |
| `paraphrase` | Rewrite existing text | Input: existing text |
| `meta_tags` | Title tags + meta descriptions | Input: topic or page content |
| `subtopics` | Topic cluster ideas | Input: main topic |
| `summary` | Summarize long content | Input: full text |
| `complete` | Complete partial text | `targetLength` (1-300 words) |
| `grammar` | Fix grammar issues | Input: text to check |

### Phase 5: Competitive content analysis

```
analyze-competitors(target: domain, dataType: "pages", limit: 50)
analyze-domain(target: competitor, dataType: "ranked_keywords", limit: 100, sortBy: "traffic")
```

**Why:** Top competitor pages reveal content strategy. Their highest-traffic keywords show what content drives results.

### Phase 6: Compile content strategy

```
compile-report(
    target: domain,
    tool_names: ["analyze-content", "research-keywords", "analyze-keywords", "find-keyword-gaps", "generate-content"]
)
```

## Interpreting results: content priorities

| Finding | Priority | Action |
|---------|----------|--------|
| High-volume keyword gaps with informational intent | High | Create comprehensive guides |
| Competitors ranking with thin content | High | Create better, deeper content |
| Negative sentiment in existing content landscape | Medium | Create positive, authoritative alternative |
| Rising phrase trends for your topic | Medium | Create timely content to capture trend |
| Missing meta tags or poor quality titles | Medium | Regenerate with `generate-content` |
| Content on declining topics | Low | Redirect or update with fresh angle |

## Cost profile

| Operation | Relative cost |
|-----------|--------------|
| analyze-content (per keyword) | Low |
| generate-content (text) | Low |
| research-keywords + analyze-keywords | Medium |
| find-keyword-gaps | Medium |

## Next workflow suggestions

- **Keyword research** → deeper keyword analysis for content planning
- **SERP analysis** → understand SERP features for target keywords
- **Rank tracking** → monitor content performance after publishing
- **Site audit** → ensure technical SEO supports content
