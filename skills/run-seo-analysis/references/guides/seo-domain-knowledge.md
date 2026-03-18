# SEO Domain Knowledge

Essential SEO concepts an agent needs to interpret tool results and advise users. This is not a tutorial — it's the minimum domain expertise to avoid giving bad advice.

## Core metrics and what they mean

| Metric | What it measures | Good range | Red flags |
|--------|-----------------|------------|-----------|
| **Domain Authority/Rank** | Overall site trust/authority (0-100) | 30+ competitive, 50+ strong | <10 = very new or penalized |
| **Organic Traffic** | Estimated monthly visits from search | Context-dependent | Sudden drops = penalty or technical issue |
| **Organic Keywords** | Keywords the site ranks for | More = broader visibility | Rapid decline = deindexation risk |
| **Keyword Difficulty** (0-100) | How hard to rank for a keyword | 0-30 easy, 30-60 moderate, 60+ hard | >80 = only massive sites can compete |
| **Search Volume** | Monthly searches for a keyword | Context-dependent | 0 volume doesn't mean no traffic (long-tail) |
| **CPC** | Cost per click in ads | Higher = more commercial value | Very low CPC + high volume = informational |
| **Referring Domains** | Unique domains linking to you | Quality > quantity | Many from same IP subnet = suspicious |
| **Backlink Spam Score** | Toxicity of a backlink (0-100) | <30 acceptable | >60 = likely toxic, consider disavow |
| **Lighthouse Performance** (0-100) | Page speed and Core Web Vitals | >90 good, >50 needs work | <30 = critical performance issue |

## Search intent: the most misunderstood concept

Search intent is WHY someone searches, not WHAT they search. Getting intent wrong means creating content no one clicks.

| Intent | Signals | Wrong content |
|--------|---------|--------------|
| **Informational** | "how to", "what is", "guide" | A product page (user wants to learn, not buy) |
| **Navigational** | Brand names, "login", "site name" | A blog post (user wants a specific page) |
| **Commercial** | "best", "vs", "review", "top 10" | An FAQ page (user wants comparisons) |
| **Transactional** | "buy", "price", "discount", "download" | An informational article (user wants to act) |

**Rule:** Always check intent before recommending content strategy. High-volume + wrong intent = wasted effort.

## Backlink health: what matters

| Factor | Healthy | Unhealthy |
|--------|---------|-----------|
| Anchor text distribution | Mix of branded, naked URL, generic, partial match | >30% exact-match keyword anchors |
| Domain diversity | Links from many unique domains | Many links from few domains |
| IP diversity | Links from varied IP subnets | Cluster from same subnet (PBN signal) |
| Link velocity | Steady, organic growth | Sudden spikes or drops |
| Follow ratio | 60-80% dofollow | <40% dofollow or 99%+ dofollow (both suspicious) |

## Technical SEO: what breaks rankings

| Issue | Impact | Severity |
|-------|--------|----------|
| Slow page speed (<50 Lighthouse) | User experience, Core Web Vitals ranking signal | High |
| Duplicate title tags/meta descriptions | Confuses search engines, dilutes click-through | High |
| Redirect chains (3+ hops) | Wastes crawl budget, loses link equity per hop | High |
| Non-indexable pages (unintended) | Content invisible to search engines | Critical |
| Broken internal links | Wastes crawl budget, poor user experience | Medium |
| Missing schema markup | No rich results, reduced SERP visibility | Medium |
| Mobile usability issues | Mobile-first indexing means mobile IS your site | High |
| Thin content (<300 words, no value) | Panda-style quality issues | Medium |

## SERP features: opportunities by type

| Feature | Optimization approach |
|---------|---------------------|
| Featured snippet | Concise answer paragraph, list, or table near top of content |
| People Also Ask | Answer related questions with clear H2/H3 + concise answer |
| Local pack | Google Business Profile optimization, local citations |
| Image pack | Descriptive alt text, image sitemaps, unique images |
| Video carousel | YouTube SEO, video schema markup |
| AI overview | Authoritative, well-structured, citable content |
| Shopping results | Product feed optimization, Merchant Center |

## Common SEO misconceptions (don't repeat these)

| Misconception | Reality |
|--------------|---------|
| "More keywords = better" | Quality targeting > quantity; keyword stuffing penalizes |
| "Backlinks are everything" | Links matter, but content quality and technical health matter equally |
| "Meta keywords matter" | Google has ignored meta keywords since ~2009 |
| "Exact-match domains rank better" | No meaningful advantage; brand authority matters more |
| "Social signals boost rankings" | No direct ranking signal; indirect benefits from traffic and links |
| "You need to submit to search engines" | Crawlers find sites via links; submission is unnecessary for established sites |
| "SEO is a one-time task" | SEO requires ongoing effort: content updates, link building, technical maintenance |

## Seasonal patterns to know

| Industry | Peak months | Plan content |
|----------|------------|-------------|
| Retail/E-commerce | Nov-Dec (holiday) | Start Aug-Sep |
| Tax/Finance | Jan-Apr | Start Nov-Dec |
| Travel | Jun-Aug (summer), Dec (winter) | 3 months ahead |
| B2B | Jan-Mar (budget cycle), Sep-Oct | Year-round, spike at Q starts |
| Education | Aug-Sep (back to school), Jan (new year) | 2 months ahead |
