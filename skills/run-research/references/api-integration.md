# API & Integration Research Guide

## Quick Reference: Which Tools For Which Integration Problem

| Use Case | Primary Tool | Secondary Tool | Key Signal |
|---|---|---|---|
| 01. Third-Party API Integration | `deep_research` | `search_reddit` | Resilient client patterns, rate limit strategies |
| 02. Webhook Implementation | `deep_research` | `search_google` | Unified security + reliability architecture |
| 03. OAuth Flow Implementation | `deep_research` | `search_google` | Security-first flow with provider deviations |
| 04. Payment Processing Integration | `deep_research` | `search_google` | Multi-dimensional (technical + compliance + cost) |
| 05. Email Service Integration | `deep_research` | `search_google` | Deliverability-first architecture with DNS setup |
| 06. File Storage Service Integration | `deep_research` | `search_google` | End-to-end upload/delivery/cost architecture |
| 07. Search Engine Integration | `deep_research` | `search_google` | Use-case-specific engine selection, relevance tuning |
| 08. Rate Limiting Design | `deep_research` | `search_google` | Complete distributed design with abuse prevention |
| 09. API Versioning Strategy | `deep_research` | `search_google` | Long-term operational implications mapped out |
| 10. GraphQL Schema Design | `deep_research` | `search_google` | Schema + performance + security as connected system |

---

## 01. Third-Party API Integration

### Recommended Tools
- **deep_research**: Synthesizes rate limits, pagination, error handling, and idempotency.
- **search_reddit**: Undocumented behaviors, rate-limit surprises, client library warnings.

### Query Templates
```python
# deep_research
"Stripe API integration in TypeScript: rate limits/backoff, pagination at scale,
idempotency key strategy, retryable vs terminal errors."

# search_google
keywords = ["Stripe API pagination cursor-based best practices",
            "third-party API error handling patterns TypeScript"]
```

### Best Practices
- Use `site:` operator for provider docs; search error codes directly for exact solutions.
- Follow up `search_reddit` with `fetch_reddit` -- real gold is in comment chains.

---

## 02. Webhook Implementation

### Recommended Tools
- **deep_research**: Cross-domain synthesis -- signatures, idempotency, queuing, dead letters.
- **search_google**: Provider-specific signing schemes, retry policies, timeout expectations.

### Query Templates
```python
# deep_research
"Webhook receiver for multi-provider SaaS (Stripe, GitHub, Twilio). Unified signature
verification, async processing, idempotency table, dead letter queue, event ordering."

# search_google
keywords = ["webhook signature verification HMAC SHA256 Node.js",
            "webhook security SSRF prevention allowlist validation"]
```

### Best Practices
- Ask **separate questions for architecture vs security** -- different domains.
- Specify runtime (Lambda vs Express) and search "webhook SSRF", "replay attack" for threats.

---

## 03. OAuth Flow Implementation

### Recommended Tools
- **deep_research**: Unified analysis across OAuth spec, provider implementations, and security.
- **search_google**: Provider-specific quirks deviating from the RFC.

### Query Templates
```python
# deep_research
"OAuth2 + PKCE for TypeScript SPA + Node.js backend. PKCE generation, secure token
storage, token refresh with multiple tabs, provider differences (Google, GitHub, OIDC)."

# search_google
keywords = ["OAuth2 PKCE implementation TypeScript 2025",
            "OAuth2 token storage secure httponly cookie vs memory"]
```

### Best Practices
- Specify **app type** (SPA vs SSR vs mobile) -- token storage differs dramatically.
- Always include "PKCE" -- now mandatory. Ask about failure modes ("token expires", "scopes revoked").

---

## 04. Payment Processing Integration

### Recommended Tools
- **deep_research**: Multi-dimensional analysis -- economics, implementation, and compliance.
- **search_google**: Pricing pages, PCI compliance guides, feature comparisons.

### Query Templates
```python
# deep_research (use 2 questions)
"Q1: Stripe vs Paddle vs LemonSqueezy for B2B SaaS. Fee structure, MoR implications,
subscription feature gaps, migration risks."
"Q2: Stripe subscription lifecycle. Webhook sequence for CRUD. DB sync. Proration. Dunning."

# search_google
keywords = ["Stripe vs Paddle vs LemonSqueezy SaaS billing 2025",
            "PCI DSS compliance requirements SaaS 2025"]
```

### Best Practices
- Ask **platform decision separately** from implementation. Search "merchant of record" for the key difference.
- Include PCI compliance ("SAQ A vs SAQ D") as a first-class concern.

---

## 05. Email Service Integration

### Recommended Tools
- **deep_research**: Connects API integration with deliverability and DNS authentication.
- **search_google**: Provider comparisons, SPF/DKIM/DMARC guides, warm-up procedures.

### Query Templates
```python
# deep_research (use 2 questions)
"Q1: Email provider for B2B SaaS at 50K-200K/month. SendGrid vs Postmark vs SES.
Separate transactional vs notification? DNS auth. Bounce handling. IP warm-up."
"Q2: Template rendering. MJML vs React Email vs Maizzle. Dark mode. Testing tools."

# search_google
keywords = ["SendGrid vs Postmark vs Amazon SES comparison 2025",
            "email deliverability SPF DKIM DMARC configuration guide"]
```

### Best Practices
- Separate **provider selection from implementation**. Specify volume for tier recommendations.
- Never mix transactional and marketing email on one provider/IP -- damages deliverability.

---

## 06. File Storage Service Integration

### Recommended Tools
- **deep_research**: End-to-end architecture -- uploads, access control, CDN, lifecycle.
- **search_google**: Cost comparisons (egress), SDK docs, security guides.

### Query Templates
```python
# deep_research
"File storage for SaaS: images, PDFs, videos up to 500MB. S3 vs R2 vs GCS. Presigned
URLs. Multipart upload. Access control. Lifecycle policies."

# search_google
keywords = ["S3 vs Cloudflare R2 vs GCS comparison 2025",
            "S3 presigned URL upload security best practices"]
```

### Best Practices
- Include **file types and sizes** -- 5MB images vs 500MB videos require different architecture.
- Search for egress cost comparisons and include CORS -- browser upload needs CORS config.

---

## 07. Search Engine Integration

### Recommended Tools
- **deep_research**: Use-case-specific recommendations based on dataset size, query patterns, team constraints.
- **search_google**: Independent benchmark data cutting through vendor marketing.

### Query Templates
```python
# deep_research (use 2 questions)
"Q1: Search engine for e-commerce, 500K products. Elasticsearch vs Meilisearch vs Typesense
vs Algolia. Instant search, faceted filtering, custom relevance. Index sync with PostgreSQL."
"Q2: Elasticsearch relevance tuning for docs. Custom analyzers for code/technical terms.
Multi_match structure. function_score for recency. Relevance measurement."

# search_google
keywords = ["Elasticsearch vs Meilisearch vs Typesense vs Algolia 2025",
            "search engine typo tolerance fuzzy matching comparison"]
```

### Best Practices
- Specify **dataset size, query volume, team size** -- the three factors most influencing selection.
- Include "self-hosted vs managed" -- "no search ops engineer" eliminates Elasticsearch for most teams.

---

## 08. Rate Limiting Design

### Recommended Tools
- **deep_research**: Complete design -- algorithm selection, distributed implementation, failure handling, abuse prevention.
- **search_google**: Algorithm-specific Redis implementations and HTTP header standards.

### Query Templates
```python
# deep_research (use 2 questions)
"Q1: Rate limiting for multi-tenant API. Token bucket vs sliding window. Atomic Redis Lua.
Multi-dimensional limits. Fail-open vs fail-closed. HTTP headers."
"Q2: Bypass prevention. Evasion techniques. Multi-factor limiting (key + IP + fingerprint).
Escalation from throttling to blocking."

# search_google
keywords = ["Redis rate limiting Lua script atomic implementation",
            "rate limiting HTTP headers X-RateLimit Retry-After standard"]
```

### Best Practices
- Ask about algorithm and implementation **separately** -- theory and Redis patterns differ.
- Include failure mode questions -- fail-open vs fail-closed shapes the entire architecture.

---

## 09. API Versioning Strategy

### Recommended Tools
- **deep_research**: Decision framework with 5-year operational implications for each approach.
- **search_google**: Case studies from Stripe, GitHub, Twilio managing versioning at scale.

### Query Templates
```python
# deep_research (use 2 questions)
"Q1: Versioning for public REST API. URL vs header vs date-based: 5-year implications.
Stripe's approach internally. Additive-changes-only. Deprecation. SDK generation impact."
"Q2: Backward compatibility rules. Breaking vs non-breaking taxonomy. Contract testing
(Pact, Prism, Optic). Behaviorally significant but technically non-breaking changes."

# search_google
keywords = ["Stripe API versioning date-based changelog",
            "breaking vs non-breaking API changes definition"]
```

### Best Practices
- Specify whether API is **public or internal** -- the single most important factor.
- Include consumer profile (mobile vs web) and contract testing for automated enforcement.

---

## 10. GraphQL Schema Design

### Recommended Tools
- **deep_research**: Complete architecture connecting schema, performance, and security controls.
- **search_google**: Official spec, production patterns (federation v2, persisted queries), security.

### Query Templates
```python
# deep_research (use 2 questions)
"Q1: GraphQL schema for multi-entity SaaS. Schema-first vs code-first for TypeScript. N+1
with dataloaders. Relay cursor pagination. Authorization (resolver vs middleware vs directive)."
"Q2: Performance and security. Query complexity analysis reflecting DB cost. Depth limiting.
Persisted queries. Field monitoring. Attacks (batching, alias DOS, introspection)."

# search_google
keywords = ["GraphQL N+1 dataloader implementation TypeScript",
            "GraphQL security depth limiting query complexity"]
```

### Best Practices
- **Separate schema design from security** -- different domains needing focused questions.
- Attach your schema definition; search specific patterns ("dataloader", "cursor pagination").

## Steering notes

1. **Scrape official API docs always.** Blog posts have stale details. Verify endpoints/params with `scrape_pages`.
2. **Pin to API version.** `"Stripe API v2024-12-18"`, `"GitHub API v4"`.
3. **GitHub Issues for real problems:** `site:github.com [vendor SDK] [error]`.
4. **Webhook verification** varies by vendor -- research vendor-specific flows.
5. **Rate limits** are often inaccurate in docs. Reddit and GitHub Issues are best sources.
