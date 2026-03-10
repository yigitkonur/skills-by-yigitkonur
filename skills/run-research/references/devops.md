# DevOps & Infrastructure Research Guide

## Quick Reference: Which Tools For Which DevOps Problem

| Use Case | Primary Tool | Secondary Tool | Why This Combination |
|---|---|---|---|
| 01. CI/CD Pipeline Setup | `deep_research` | `search_reddit` + `scrape_pages` | Platform comparison + migration stories + pricing extraction |
| 02. Docker Optimization | `deep_research` | `search_google` + `search_reddit` | Build/runtime strategy + BuildKit discovery + before/after metrics |
| 03. Kubernetes Configuration | `deep_research` | `search_google` | Multi-dimensional K8s decisions + current benchmarks |
| 04. Monitoring & Alerting | `deep_research` | `search_google` + `search_reddit` | TCO analysis + SLO implementation + real cost experiences |
| 05. Log Aggregation | `deep_research` | `search_google` | TCO at scale + agent/platform comparisons |
| 06. SSL/TLS Certificates | `deep_research` | `search_google` | Lifecycle automation + cert-manager + TLS hardening |
| 07. CDN & Edge Config | `deep_research` | `search_google` + `scrape_pages` | Cache strategy + edge function comparisons + header extraction |
| 08. Database Tuning | `deep_research` | `search_google` + `scrape_pages` | Index strategy + autovacuum + EXPLAIN guide extraction |
| 09. Horizontal Scaling | `deep_research` | `search_google` | Phased roadmap + replica/sharding pattern discovery |
| 10. Infrastructure as Code | `deep_research` | `search_google` + `search_reddit` | Tool selection + state management + at-scale experiences |

---

## 01. CI/CD Pipeline Setup

**deep_research** -- include team size and repo structure:
```
WHAT I NEED: Comparison of GitHub Actions, GitLab CI, CircleCI for 50-engineer team with TypeScript monorepo.
SPECIFIC QUESTIONS:
1) How does caching differ across platforms for monorepo with 20+ packages?
2) Real costs at 50 engineers running ~200 builds/day?
3) Which handles matrix builds with least config overhead?
4) Lock-in risks and migration escape hatches?
FOCUS: Total cost including engineering time, not just compute
```

**search_reddit**: `["GitHub Actions vs GitLab CI real experience", "CircleCI pricing increase alternative", "best CI/CD caching strategy monorepo", "r/devops CI pipeline slow build times"]`

**scrape_pages**: `what_to_extract: "cache mechanisms | cache key syntax | cache size limits | pricing tiers | included minutes | overage cost"`

**Best Practices**: Search for migration stories ("migrated from X to Y") on Reddit. Include "monorepo" or "polyrepo" since caching strategies differ. Always `fetch_comments=True` -- best CI/CD advice is in replies. Use year-specific queries since platforms ship features quarterly.

---

## 02. Docker Optimization

**deep_research** -- include language runtime and current pain:
```
WHAT I NEED: Docker optimization for Node.js/TypeScript monorepo (8 services).
WHY: Images 800MB+, builds 12 min, 47 high/critical CVEs.
SPECIFIC QUESTIONS:
1) Optimal multi-stage pattern for Node.js TypeScript?
2) node:slim vs alpine vs distroless: which for production?
3) BuildKit cache mounts for npm/pnpm workspaces?
4) Correct COPY order for maximum layer cache hits?
```

**search_google**: `["Docker multi-stage build optimization 2025", "Docker slim base image alpine distroless chainguard", "BuildKit cache mount npm pip cargo best practices"]`

**Best Practices**: Attach your Dockerfile as file_attachment. Include package manager since caching differs. Search Reddit for Alpine gotchas: missing glibc, DNS issues, musl problems. Scrape official Docker docs for syntax accuracy. Search "BuildKit" explicitly since older guides predate it.

---

## 03. Kubernetes Configuration

**deep_research** -- include cloud provider and workload types:
```
WHAT I NEED: Service mesh decision (Istio vs Linkerd vs none) for 40 microservices on EKS.
SPECIFIC QUESTIONS:
1) Real CPU/memory overhead of Istio vs Linkerd per pod?
2) When is 'no service mesh' the right answer?
3) How does Istio Ambient mode change the calculus?
4) Team size/expertise needed to operate each?
FOCUS: Operational complexity and failure modes, not feature comparison
```

**search_google**: `["Kubernetes resource limits requests best practices 2025", "Istio vs Linkerd performance", "Kubernetes HPA custom metrics autoscaling guide", "nginx ingress vs traefik vs envoy gateway"]`

**Best Practices**: Include cloud provider (EKS/GKE/AKS). Mention workload types (web vs worker vs batch). Ask about failure modes and rollback, not just happy path. Attach HPA/resource manifests. Search for "production checklist" guides.

---

## 04. Monitoring & Alerting Setup

**deep_research** -- include scale metrics:
```
WHAT I NEED: Monitoring platform decision (Prometheus+Grafana vs Datadog vs New Relic)
for 30-person team, 50 services, 200 hosts, 5TB logs/month.
SPECIFIC QUESTIONS:
1) Realistic 3-year TCO at our scale?
2) Engineers required for self-hosted Prometheus+Grafana+Loki?
3) Best alerting for reducing on-call burden?
4) High-cardinality metrics without cost explosion?
```

**search_google**: `["Prometheus Grafana vs Datadog vs New Relic 2025", "monitoring alert fatigue reduction", "Datadog pricing high cardinality", "SLO SLI alerting strategy burn rate"]`

**Best Practices**: Include host count, service count, log volume for accurate TCO. Ask about both platform and alerting strategy -- they are deeply connected. "High cardinality" is the primary cost driver. Attach current alerting rules for improvement recommendations.

---

## 05. Log Aggregation Strategy

**deep_research** -- include daily volume:
```
WHAT I NEED: Log platform comparison for Kubernetes generating 500GB/day.
SPECIFIC QUESTIONS:
1) TCO of self-hosted ELK vs Loki vs managed OpenSearch at 500GB/day?
2) Query performance for grep-like, aggregation, correlation?
3) Recommended log shipping pipeline (agent, buffer, destination)?
4) Retention tiers (hot/warm/cold/archive)?
```

**search_google**: `["ELK vs Grafana Loki vs CloudWatch 2025", "centralized logging Kubernetes fluentbit vector agent", "log retention policy compliance GDPR SOC2"]`

**Best Practices**: Include daily log volume -- recommendations change dramatically at different scales. Search for agent comparisons (Fluent Bit vs Vector vs Alloy). Look for "Elasticsearch alternatives" to discover ClickHouse-based solutions. Include compliance terms if relevant.

---

## 06. SSL/TLS Certificate Management

**deep_research** -- include infrastructure type:
```
WHAT I NEED: Certificate management for 30-service Kubernetes platform.
SPECIFIC QUESTIONS:
1) cert-manager architecture for external TLS and internal mTLS?
2) Zero-downtime rotation strategy?
3) Monitoring as safety net for automation?
4) Service mesh mTLS vs cert-manager directly?
```

**search_google**: `["cert-manager Kubernetes ACME DNS challenge setup", "TLS 1.3 nginx hardening guide", "SSL certificate monitoring expiry alerting tools", "certificate rotation zero downtime"]`

**Best Practices**: Ask about monitoring separately from automation -- automation fails silently. Search for "certificate outage postmortem" to learn from others' incidents. Reference Mozilla SSL Configuration Generator for cipher suites. Include mobile context if certificate pinning is relevant.

---

## 07. CDN & Edge Configuration

**deep_research** -- include content types:
```
WHAT I NEED: CDN comparison (Cloudflare vs Fastly vs CloudFront) for SaaS with API and static assets.
SPECIFIC QUESTIONS:
1) Purge propagation comparison -- is Fastly's instant purge real?
2) Real costs at 10TB/month egress, 100M requests?
3) Edge function comparison for auth validation and A/B testing?
4) API response caching with Vary headers?
FOCUS: API caching and edge compute, not just static delivery
```

**search_google**: `["Cloudflare vs Fastly vs CloudFront 2025", "Cloudflare Workers vs CloudFront Functions", "CDN origin shield reduce origin load", "CDN cache rules best practices"]`

**Best Practices**: Include all content types (static, HTML, API, WebSocket). Specify freshness requirements per type. Ask about both cache rules and purge strategy together. Search for "origin shield" and "tiered caching" for advanced patterns.

---

## 08. Database Tuning & Indexing

**deep_research** -- attach EXPLAIN output:
```
WHAT I NEED: PostgreSQL index strategy for SaaS with 500M+ rows.
SPECIFIC QUESTIONS:
1) How to read EXPLAIN ANALYZE to identify right index type?
2) When to use partial vs full indexes on large tables?
3) Composite index column ordering and leftmost prefix rule?
4) Write overhead of each index type?
```

**search_google**: `["PostgreSQL EXPLAIN ANALYZE guide", "PostgreSQL index strategy composite partial covering", "PgBouncer vs PgCat vs Supavisor comparison", "PostgreSQL autovacuum tuning production"]`

**Best Practices**: Attach slowest EXPLAIN ANALYZE outputs. Include PostgreSQL version and hosting (RDS, Aurora). Specify workload type (OLTP, OLAP, mixed). Remember that indexing, pooling, and vacuum interact: more indexes = more vacuum work = more pool pressure.

---

## 09. Horizontal Scaling Strategy

**deep_research** -- include current traffic and growth:
```
WHAT I NEED: Scaling roadmap for SaaS at 500 rps, growing to 10K rps in 18 months.
SPECIFIC QUESTIONS:
1) Scaling investments at 1K, 2K, 5K, and 10K rps?
2) When to add PostgreSQL read replicas and handle replication lag?
3) Is sharding necessary at 10K rps or are there alternatives (Citus, Aurora)?
4) Caching strategies that defer database scaling?
FOCUS: Sequenced investments with trigger points, avoiding premature complexity
```

**search_google**: `["database read replica strategy PostgreSQL", "database sharding when how approaches", "PostgreSQL read replica lag handling", "distributed session management Redis vs JWT"]`

**Best Practices**: Search "sharding alternatives" -- sharding is often premature. "Read replica lag" is the number one operational challenge. Ask about consistency requirements per feature. Caching that defers scaling is often higher-ROI than infrastructure investment.

---

## 10. Infrastructure as Code Patterns

**deep_research** -- include team structure:
```
WHAT I NEED: Comparison of Terraform, Pulumi, CDK for 200+ AWS resources across 3 environments.
SPECIFIC QUESTIONS:
1) Team collaboration comparison (code review, state, access control)?
2) Testing story for each (unit, integration, policy)?
3) Module design and reuse comparison?
4) Lock-in risks and escape hatches?
FOCUS: Collaboration and maintainability, not feature lists
```

**search_google**: `["Terraform vs Pulumi vs CDK 2025", "Terraform state management best practices", "infrastructure drift detection tools", "Terraform testing framework 2025"]`

**Best Practices**: Include team structure (platform team + product teams) -- IaC architecture mirrors org structure. CDK is AWS-only while Terraform and Pulumi support multi-cloud. Ask about organizational patterns alongside technical ones. Search "Terraform at scale" for enterprise guidance.

---

## Universal DevOps Research Workflow

1. **`search_google`** (5-7 keywords) -- discover current tools, pricing, features (DevOps tooling evolves quarterly)
2. **`search_reddit`** in parallel -- target r/devops, r/docker, r/kubernetes for unfiltered experiences
3. **`scrape_pages`** (3-5 URLs) -- official docs for exact config syntax, pricing, limits
4. **`fetch_reddit`** (`fetch_comments=True`) -- inline YAML snippets, before/after metrics
5. **`deep_research`** (2 questions) -- one for tool selection, one for optimization of chosen approach

**Key principles:**
- Include scale metrics (team size, traffic, data volume) -- recommendations change by scale
- Include cloud provider and platform -- guidance is provider-specific
- Ask about TCO including engineering time, not just license/compute costs
- Target migration stories on Reddit -- they contain the most honest comparisons
- Use year-specific queries since DevOps tools ship major features quarterly
