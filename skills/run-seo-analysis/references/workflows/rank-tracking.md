# Rank Tracking Workflow

Monitor keyword rankings over time with change detection and alerting.

## When to use

User wants: track rankings, monitor position changes, set up daily/weekly rank checks, bulk ranking snapshot, compare rankings across engines.

## The SEO practitioner's mental model

Rank tracking answers: "Are my SEO efforts working? Where am I gaining or losing?" It's the feedback loop — without tracking, optimization is guesswork. The practitioner needs current positions, changes over time, and correlation with SEO actions.

## Workflow

### Phase 1: Initial ranking snapshot

```
resolve-geo(location: user's market, product: "rank_tracker")
→ track-rankings(
    keywords: [keyword_list],
    target: domain,
    dataType: "current",
    engine: "google",
    mode: "live",    // for <=5 keywords
    depth: 100
)
```

**Mode selection:**
| Keywords count | Mode | Notes |
|---------------|------|-------|
| 1-5 | `live` | Immediate results |
| 6-100 | `task` | Async, use `manage-tasks` to check |
| 100-700 | `bulk` | Most efficient for large lists |

**Key parameters:**
- `depth`: How deep to search (10-700). Use 100 for standard, 50 for quick
- `include_serp_features: true`: Tracks featured snippets, PAA, local pack presence
- `csv_data`: Alternative to `keywords` — upload CSV with keyword column (max 700 rows)

### Phase 2: Check for changes (if baseline exists)

```
track-rankings(
    keywords: [keyword_list],
    target: domain,
    dataType: "changes",
    engine: "google"
)
```

**Why `changes`:** Compares current positions against the previous snapshot — shows gains, losses, and new entries.

### Phase 3: Set up recurring tracking (if user wants ongoing monitoring)

```
track-rankings(
    keywords: [keyword_list],
    target: domain,
    frequency: "weekly",   // or "daily"
    engine: "google"
)
```

**Frequency decisions:**
| Frequency | When | Cost |
|-----------|------|------|
| `once` | One-time snapshot | Lowest |
| `daily` | Active campaigns, volatile keywords | Highest |
| `weekly` | Standard monitoring, stable keywords | Medium |

### Phase 4: Multi-engine tracking (if relevant)

```
track-rankings(keywords: [kw], target: domain, engine: "bing")
track-rankings(keywords: [kw], target: domain, engine: "yahoo")
```

**Supported engines:** google, bing, yahoo, baidu, naver, seznam

### Phase 5: Export and analyze

```
read-result-set(handle: result_handle, operation: "aggregate", group_by: "keyword", metrics: ["avg"])
→ export-result-set(handle: result_handle, format: "csv")
```

## Interpreting results

| Change | Meaning | Action |
|--------|---------|--------|
| Position improved 1-3 spots | Normal fluctuation | Monitor, don't react |
| Position improved 5+ spots | SEO effort paying off | Document what worked |
| Position dropped 1-3 spots | Normal fluctuation | Monitor for trends |
| Position dropped 5+ spots | Potential issue | Check for algorithm updates, lost links, technical issues |
| New in top 100 | Newly indexed or newly ranking | Optimize to push higher |
| Dropped out of top 100 | Deindexed or major ranking loss | Investigate immediately |

## Cost profile

| Operation | Relative cost |
|-----------|--------------|
| live tracking (5 keywords) | Low |
| task tracking (100 keywords) | Medium |
| bulk tracking (700 keywords) | Medium-High |
| daily subscription (100 keywords) | High (recurring) |

## Next workflow suggestions

- **SERP analysis** → understand why rankings changed
- **Site audit** → diagnose technical issues causing drops
- **Competitor analysis** → see if competitors are gaining
- **Backlink analysis** → check if link changes correlate with ranking changes
