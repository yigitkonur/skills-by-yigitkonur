# Local SEO Workflow

Local business visibility, reviews, and listing optimization.

## When to use

User wants: local search optimization, Google Business Profile analysis, review monitoring, business listings audit, local pack rankings, multi-location SEO.

## The SEO practitioner's mental model

Local SEO answers: "When someone nearby searches for my service, do they find me?" Local search is distinct from organic — proximity, reviews, and business listings drive results. The practitioner needs listing accuracy, review health, local keyword rankings, and local SERP presence.

## Workflow

### Phase 1: Business profile analysis

```
resolve-geo(location: business_location, product: "business")
→ analyze-business(platform: "google", dataType: "profile", target: place_id_or_query)
```

**Platform-specific identifiers:**
| Platform | `target` format |
|----------|----------------|
| Google | Place ID or business name + location |
| Yelp | Business URL path |
| TripAdvisor | URL path or location ID |
| Trustpilot | Domain or business URL |

### Phase 2: Review analysis

```
analyze-business(platform: "google", dataType: "reviews", target: place_id, sortBy: "newest", limit: 50)
→ analyze-business(platform: "google", dataType: "reviews", target: place_id, sortBy: "lowest_rating", limit: 20)
```

**Why both sorts:** Newest shows current sentiment trajectory. Lowest-rated reveals recurring complaints and reputation risks.

**Multi-platform review scan:**
```
analyze-business(platform: "yelp", dataType: "reviews", target: business_url)
analyze-business(platform: "trustpilot", dataType: "reviews", target: domain)
```

### Phase 3: Listing discovery and audit

```
analyze-business(platform: "google", dataType: "business_listings_search", keyword: "business type", location: city)
analyze-business(platform: "google", dataType: "listings", target: domain)
```

**Why:** Shows where the business appears in listing results and whether the listing information is accurate and consistent.

### Phase 4: Local SERP analysis

```
analyze-serp(keyword: "service + city", dataType: "local_pack", engine: "google")
analyze-serp(keyword: "service + city", dataType: "maps", engine: "google")
analyze-serp(keyword: "service near me", dataType: "organic", engine: "google", device: "mobile")
```

**Why mobile:** Local searches are predominantly mobile. Always check mobile SERP for local queries.

### Phase 5: Social media presence (optional)

```
analyze-business(dataType: "social_media", target: domain, socialPlatforms: ["facebook", "pinterest"])
```

### Phase 6: Local keyword research

```
research-keywords(keywords: ["service city", "service near me"], dataType: "related", limit: 200)
→ track-rankings(keywords: [local_keywords], target: domain, engine: "google")
```

### Phase 7: Compile local SEO report

```
compile-report(target: business_name, tool_names: ["analyze-business", "analyze-serp", "research-keywords"])
```

## Interpreting results

| Signal | Action |
|--------|--------|
| Average rating < 4.0 | Review management is critical — respond to negatives, encourage positives |
| Not appearing in local pack | Optimize Google Business Profile: categories, description, hours, photos |
| Inconsistent NAP across platforms | Fix name, address, phone consistency across all listings |
| Few reviews compared to competitors | Implement review generation strategy |
| Missing from key review platforms | Create and optimize profiles on missing platforms |
| Ranking for "near me" but not specific location keywords | Create location-specific landing pages |

## Cost profile

| Operation | Relative cost |
|-----------|--------------|
| Business profile/listings | Low |
| Reviews (per platform) | Low-Medium |
| Local SERP analysis | Medium |
| Multi-platform analysis | Medium (sum of platforms) |

## Next workflow suggestions

- **Site audit** → technical SEO for local landing pages
- **Content optimization** → create location-specific content
- **Rank tracking** → monitor local keyword positions
- **Competitor analysis** → benchmark against local competitors
