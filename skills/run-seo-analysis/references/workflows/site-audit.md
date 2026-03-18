# Site Audit Workflow

Complete technical SEO audit workflow using MCP Marketers tools.

## When to use

User wants: site health check, technical SEO audit, crawl issues, page speed analysis, Core Web Vitals, duplicate content, redirect chains, indexation problems.

## The SEO practitioner's mental model

A technical SEO audit answers: "What's broken on my site that prevents search engines from crawling, indexing, and ranking it effectively?" The practitioner needs a systematic sweep across crawlability, indexability, performance, and content quality — not just one metric.

## Workflow

### Phase 1: Domain overview (context first)

```
resolve-geo(location: user's market, product: "domain")
→ analyze-domain(target: domain, dataType: "overview")
```

**Why first:** Establishes baseline metrics (traffic, authority, keyword count) so audit findings have context. A site with 100 pages needs a different audit than one with 100,000.

**Key parameters:**
- `engine`: google (default) or bing based on user's market
- `forceRefresh: true` if user suspects stale data

### Phase 2: Quick crawl (instant audit)

```
audit-site(target: domain, dataType: "instant", maxPages: 100, device: "desktop")
```

**Why instant first:** Returns results in seconds. Gives immediate signal on major issues before committing to a full crawl. Check the summary for critical/error/warning counts.

**Key parameters:**
- `maxPages`: 50 for quick scan, 100 for standard, 500+ for thorough (cost scales linearly)
- `device`: "desktop" first, then "mobile" if mobile-specific issues suspected
- `enableJs: false` (default) — only enable for JS-heavy SPAs (significantly increases cost and time)

### Phase 3: Deep analysis (run in parallel where possible)

These can run concurrently — they hit different API endpoints:

```
audit-site(target: domain, dataType: "lighthouse", pageUrl: homepage)
audit-site(target: domain, dataType: "duplicate_tags", taskId: from_phase2)
audit-site(target: domain, dataType: "redirect_chains", taskId: from_phase2)
audit-site(target: domain, dataType: "non_indexable", taskId: from_phase2)
audit-site(target: domain, dataType: "links", taskId: from_phase2)
```

**What each reveals:**
| dataType | Finds | Priority |
|----------|-------|----------|
| `lighthouse` | Core Web Vitals, performance, accessibility, SEO score | High |
| `duplicate_tags` | Duplicate title tags and meta descriptions | High |
| `redirect_chains` | Redirect loops, long chains (3+ hops) | High |
| `non_indexable` | Pages blocked by robots.txt, noindex, canonicals | High |
| `links` | Broken internal/external links, orphan pages | Medium |
| `keyword_density` | Over-optimized pages, keyword stuffing | Medium |
| `microdata` | Schema markup errors, missing structured data | Medium |

**Key parameters for lighthouse:**
- `pageUrl`: Test the homepage first, then top traffic pages
- `lighthouseCategories`: ["performance", "seo", "accessibility"] to focus
- `device`: Test both "desktop" and "mobile"

### Phase 4: Content quality (if scope includes content)

```
audit-site(target: domain, dataType: "keyword_density", taskId: from_phase2, keywordLength: 2)
audit-site(target: domain, dataType: "content_parsing", pageUrl: top_page)
audit-site(target: domain, dataType: "microdata", taskId: from_phase2)
```

### Phase 5: Cross-reference with domain intelligence

```
analyze-domain(target: domain, dataType: "ranked_keywords", limit: 50, sortBy: "traffic")
analyze-domain(target: domain, dataType: "technologies")
```

**Why:** Ranked keywords reveal which pages drive traffic (protect these). Technologies reveal CMS, analytics, CDN — useful for diagnosing performance issues.

### Phase 6: Compile findings

```
compile-report(target: domain, tool_names: ["audit-site", "analyze-domain"])
```

## Interpreting results: what to flag

| Finding | Severity | What to tell the user |
|---------|----------|----------------------|
| Lighthouse performance < 50 | Critical | "Your site is slow — this directly impacts rankings and user experience" |
| >10% duplicate title tags | High | "Search engines can't distinguish these pages — consolidate or rewrite" |
| Redirect chains >3 hops | High | "Each hop loses link equity and slows crawling — flatten to direct redirects" |
| >5% non-indexable pages that should be indexed | High | "These pages are invisible to search engines — check robots.txt and canonicals" |
| Broken internal links >2% | Medium | "Broken links waste crawl budget and hurt user experience" |
| Missing schema markup on key pages | Medium | "Structured data helps rich results — add schema for products, articles, FAQs" |
| Mobile Lighthouse < Desktop by >20 points | Medium | "Mobile experience significantly worse — prioritize mobile optimization" |

## Cost profile

| Operation | Relative cost | Notes |
|-----------|--------------|-------|
| instant audit (100 pages) | Low | Best starting point |
| lighthouse (per page) | Medium | Run on 3-5 key pages, not all |
| full crawl (1000 pages) | High | Only when user needs comprehensive data |
| full crawl + enableJs | Very High | Only for JS-heavy SPAs |

## Next workflow suggestions

After a site audit, common follow-ups:
- **Backlink analysis** → if authority/link issues found
- **Keyword research** → if thin content or missing keyword targeting found
- **Competitor analysis** → to benchmark audit findings against competitors
- **Rank tracking** → to monitor improvements after fixing audit issues
