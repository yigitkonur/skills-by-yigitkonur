# Competitor Analysis Workflow

Full competitive intelligence workflow using MCP Marketers tools.

## When to use

User wants: identify competitors, compare domains, competitive benchmarking, market positioning, find competitor weaknesses, keyword/backlink gaps.

## The SEO practitioner's mental model

Competitor analysis answers: "Who am I competing with in search, where are they beating me, and what can I learn from them?" The practitioner needs to identify true SEO competitors (not just business competitors), compare key metrics, and find actionable gaps to exploit.

## Workflow

### Phase 1: Identify competitors

```
resolve-geo(location: user's market, product: "domain")
→ analyze-competitors(target: user_domain, dataType: "domain", engine: "google", limit: 20)
```

**Why `domain` first:** Identifies domains competing for the same organic keywords — often different from the user's perceived business competitors. The top 5-10 organic competitors are your real SEO competition.

**Alternative approaches:**
| Scenario | dataType | When |
|----------|----------|------|
| Organic competitors | domain | Default starting point |
| SERP-level competitors for specific keywords | serp | When focused on specific keyword clusters |
| Subdomain competitors | subdomains | When analyzing multi-subdomain sites |
| Page-level competitors | pages | When comparing specific content pieces |
| Category competitors | categories_for_domain | When understanding topical overlap |

### Phase 2: Head-to-head comparison

```
compare-domains(
  targets: [user_domain, competitor1, competitor2, competitor3],
  dataType: "overview"
)
```

**What to compare:**
| Metric | What it reveals |
|--------|----------------|
| Organic traffic | Overall search visibility |
| Organic keywords | Content breadth |
| Domain rank/authority | Link authority and trust |
| Backlinks count | Link building investment |
| Referring domains | Link diversity |

### Phase 3: Keyword gap analysis

```
find-keyword-gaps(
  targets: [user_domain, competitor1, competitor2],
  dataType: "domains",
  intersectionMode: "union",
  minVolume: 50,
  limit: 1000
)
```

**Why this is the most valuable step:** Directly reveals keywords competitors rank for that you don't — each is a concrete content opportunity.

**Interpreting intersection modes:**
| Mode | Reveals |
|------|---------|
| `union` | ALL keywords any competitor ranks for (broadest view) |
| `intersect` | Keywords ALL competitors share (market must-haves) |

### Phase 4: Backlink comparison

```
compare-backlinks(targets: [user_domain, competitor1, competitor2])
→ find-link-opportunities(
    target: user_domain,
    competitors: [competitor1, competitor2, competitor3],
    dataType: "domain_intersection",
    limit: 200
)
```

**Why:** Link opportunities = sites that link to competitors but not to you. These are the most achievable link targets because they've already demonstrated willingness to link to your niche.

### Phase 5: Technology and content comparison (optional)

```
compare-domains(targets: [user_domain, competitor1], dataType: "technologies")
analyze-competitors(target: competitor1, dataType: "pages", limit: 50)
```

**Why:** Technology comparison reveals CMS, CDN, analytics differences that may explain performance gaps. Top pages reveal competitor content strategy.

### Phase 6: Compile competitive intelligence report

```
compile-report(
  target: user_domain,
  tool_names: ["analyze-competitors", "compare-domains", "find-keyword-gaps", "compare-backlinks", "find-link-opportunities"]
)
```

## Interpreting results: key signals

| Signal | What it means | Action |
|--------|--------------|--------|
| Competitor has 3x your organic traffic but similar authority | They have better content/keyword targeting | Focus on keyword gaps |
| Competitor has 5x your backlinks | They have stronger link building | Run link opportunity analysis |
| Many shared keywords but you rank lower | On-page optimization issues | Run site audit on those pages |
| Competitor ranks for keywords you don't target | Content gaps | Create content for those keywords |
| Competitor's top pages are all blog content | Content-led SEO strategy | Invest in content marketing |

## Cost profile

| Operation | Relative cost |
|-----------|--------------|
| analyze-competitors (one domain) | Low-Medium |
| compare-domains (3-5 domains) | Medium |
| find-keyword-gaps (3 domains) | Medium |
| compare-backlinks (3 domains) | Low |
| find-link-opportunities | Medium |

## Next workflow suggestions

- **Keyword research** → expand on gap keywords
- **Backlink analysis** → deep dive into competitor link profiles
- **Content optimization** → create content for identified gaps
- **Site audit** → fix technical issues competitors don't have
