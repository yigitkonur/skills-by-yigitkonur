# Backlink Analysis Workflow

Comprehensive backlink profile analysis and link building intelligence.

## When to use

User wants: backlink audit, link profile health, toxic links, link building opportunities, anchor text analysis, link velocity tracking, disavow file preparation.

## The SEO practitioner's mental model

Backlink analysis answers: "How strong is my link profile, is anything hurting me, and where can I build more links?" Links remain a top ranking factor. The practitioner needs profile health (spam, toxicity), competitive context (who links to competitors but not me), and growth trends (gaining or losing links).

## Workflow

### Phase 1: Profile overview

```
resolve-geo(location: user's market, product: "backlinks")
→ analyze-backlinks(target: domain, dataType: "backlinks", mode: "domain", sortBy: "authority", limit: 100)
```

**Why start here:** Gives the top 100 highest-authority backlinks — immediately shows link quality. Follow with referring domains for diversity.

### Phase 2: Profile health

Run these in parallel:
```
analyze-backlinks(target: domain, dataType: "referring_domains", limit: 200)
analyze-backlinks(target: domain, dataType: "anchors", limit: 100)
analyze-backlinks(target: domain, dataType: "spam_scores")
analyze-backlinks(target: domain, dataType: "referring_networks", networkAddressType: "subnet")
```

**What each reveals:**
| dataType | Insight | Watch for |
|----------|---------|-----------|
| `referring_domains` | Link diversity | Low diversity = fragile profile |
| `anchors` | Anchor text distribution | Over-optimized exact-match anchors |
| `spam_scores` | Toxic link percentage | >10% spam links = potential penalty risk |
| `referring_networks` | IP/subnet concentration | Many links from same subnet = PBN risk |

### Phase 3: Growth tracking

```
track-backlinks(target: domain, dataType: "growth_summary", period: "month")
→ track-backlinks(target: domain, dataType: "new_backlinks", period: "month", limit: 50)
→ track-backlinks(target: domain, dataType: "lost_backlinks", period: "month", limit: 50)
```

**Why:** Velocity matters as much as count. Rapid loss signals a problem; steady growth signals authority building.

### Phase 4: Competitive comparison

```
compare-backlinks(targets: [user_domain, competitor1, competitor2])
→ find-link-opportunities(
    target: user_domain,
    competitors: [competitor1, competitor2],
    dataType: "domain_intersection",
    limit: 200
)
```

**Why:** Link opportunities from competitor analysis are the highest-conversion outreach targets — these sites already link to your niche.

### Phase 5: Compile findings

```
compile-report(target: domain, tool_names: ["analyze-backlinks", "track-backlinks", "compare-backlinks", "find-link-opportunities"])
```

## Interpreting results: health signals

| Signal | Severity | Meaning |
|--------|----------|---------|
| Spam score >10% of profile | High | Disavow toxic links |
| Anchor text >30% exact-match | High | Over-optimization risk — diversify |
| Single subnet has >20% of links | High | PBN/link farm risk |
| Lost >10% of links in past month | Medium | Investigate lost links (site changes? removed content?) |
| <50 referring domains | Medium | Thin profile — prioritize link building |
| No links from .edu/.gov/major publishers | Low | Missing authority signals |

## Parameter guide

| Parameter | When to use | Values |
|-----------|------------|--------|
| `mode` | Always set explicitly | `domain` (whole site) vs `page` (specific URL) |
| `backlinkMode` | Deduplication | `one_per_domain` for unique referring domains |
| `backlinksStatusType` | Lost link analysis | `lost` to find removed links |
| `sortBy` | Prioritization | `authority` (quality), `date` (recency), `traffic` (value) |
| `searchAfterToken` | Deep pagination | Use for paginating beyond offset 20000 |

## Cost profile

| Operation | Relative cost |
|-----------|--------------|
| analyze-backlinks (single domain) | Low-Medium |
| analyze-backlinks (bulk 1000 domains) | High |
| track-backlinks (monthly) | Low |
| compare-backlinks (3-5 domains) | Low |
| find-link-opportunities | Medium |

## Next workflow suggestions

- **Competitor analysis** → understand competitor link strategies
- **Site audit** → fix technical issues that waste link equity
- **Rank tracking** → correlate link changes with ranking changes
- **Content optimization** → create link-worthy content
