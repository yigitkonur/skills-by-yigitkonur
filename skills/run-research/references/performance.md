# Performance Optimization Research Guide

## Quick Reference: Which Tools For Which Performance Problem

| Use Case | Primary Tool | Secondary Tool | Key Signal |
|---|---|---|---|
| 01. Profiling Data Interpretation | `deep_research` | `scrape_pages` | Cross-tool synthesis, decision heuristics |
| 02. Algorithm & Data Structure Selection | `deep_research` | `search_google` | Workload-specific comparison, benchmark data |
| 03. Database Query Optimization | `deep_research` | `search_reddit` | Systematic methodology, EXPLAIN walkthroughs |
| 04. Caching Layer Implementation | `deep_research` | `search_reddit` | Complete architecture with failure modes |
| 05. Memory Usage Optimization | `deep_research` | `search_google` | Prioritized optimization plan, profiling tools |
| 06. Frontend Bundle Optimization | `search_google` | `search_reddit` | Bundler-specific techniques, dependency swaps |
| 07. Lazy Loading & Code Splitting | `deep_research` | `search_reddit` | Threshold-based decision framework |
| 08. Connection Pooling Tuning | `search_google` | `fetch_reddit` | Pool sizing formulas, exact config values |
| 09. Concurrent Processing Design | `deep_research` | `search_reddit` | Hybrid architecture, backpressure design |
| 10. Network Request Optimization | `deep_research` | `scrape_pages` | Layered protocol optimization, timeout chains |

---

## 01. Profiling Data Interpretation

### Recommended Tools
- **deep_research**: Cross-tool synthesis connecting flamegraphs, benchmarks, and browser profiling.
- **scrape_pages**: Decision criteria from authoritative sources (Brendan Gregg, Chrome DevTools docs).

### Query Templates
```python
# deep_research
"Systematic methodology for interpreting CPU profiling output (flamegraphs, perf stat,
criterion, Chrome DevTools). What percentage makes a function worth optimizing?"

# search_google
keywords = ["how to read flamegraph wide flat stack frames interpretation",
            "Chrome DevTools performance profile long task main thread interpretation"]
```

### Best Practices
- Ask for **decision trees**, not explanations. Frame as "how do I decide if X is significant?"
- Request **concrete thresholds** over vague guidance. Keep `use_llm=False` on Reddit for exact numbers.

---

## 02. Algorithm & Data Structure Selection

### Recommended Tools
- **deep_research**: Workload-specific analysis with comparison matrix (latency, memory, cache, concurrency).
- **search_google**: Empirical benchmark data capturing cache locality and real-world performance.

### Query Templates
```python
# deep_research
"Comparison of ordered map implementations in Rust: BTreeMap, skip list, ART, sorted Vec.
1-10M entries, 8-byte keys. Realistic ns/op? Cache miss rates? Concurrent read support?"

# search_google
keywords = ["BTree vs HashMap benchmark real world performance comparison",
            "cache-friendly data structures benchmark L1 L2 cache misses"]
```

### Best Practices
- Be **extremely specific about workload**: key size, entry count, read/write ratio, concurrency.
- List **specific candidates** for direct comparison rather than surveying the field.

---

## 03. Database Query Optimization

### Recommended Tools
- **deep_research**: Systematic methodology connecting indexing, query structure, ORM patterns, and configuration.
- **search_google**: Database-engine-specific documentation (EXPLAIN node types, index selection).

### Query Templates
```python
# deep_research
"Systematic approach to optimizing slow PostgreSQL queries in Django with 50M+ rows.
EXPLAIN ANALYZE to fix. Partial/covering/expression indexes? N+1 detection? Denormalize vs optimize?"

# search_google
keywords = ["PostgreSQL EXPLAIN ANALYZE interpret Seq Scan vs Index Scan when",
            "composite index column order selectivity PostgreSQL performance"]
```

### Best Practices
- **Attach actual slow queries and EXPLAIN output** -- generic advice is far less valuable.
- Always include database engine AND version; include ORM name for N+1 solutions.
- On Reddit, keep `use_llm=False` to preserve SQL, EXPLAIN output, and timing numbers.

---

## 04. Caching Layer Implementation

### Recommended Tools
- **deep_research**: Complete caching design covering invalidation, consistency, failure modes, and monitoring.
- **search_reddit**: Honest failure reports and cautionary tales about production caching.

### Query Templates
```python
# deep_research
"Caching architecture for Django REST API at 5K req/s with 99:1 read/write ratio.
Cache-aside vs write-through? Cascading invalidation? Stampede prevention? Redis failure?"

# scrape_pages
urls = ["https://redis.io/docs/latest/develop/use/patterns/"]
what_to_extract = "caching patterns | invalidation strategies | TTL recommendations | failure handling"
```

### Best Practices
- Specify your **read/write ratio** -- it determines the optimal caching pattern.
- Describe **data relationships** -- cascading invalidation is the hardest part.
- Ask about **failure modes explicitly** -- "what happens when Redis goes down?"

---

## 05. Memory Usage Optimization

### Recommended Tools
- **deep_research**: Prioritized optimization plan considering interaction between techniques.
- **search_google**: Language-runtime-specific techniques (arenas in Rust, GC tuning in Go).

### Query Templates
```python
# deep_research
"Reduce memory in Rust JSON processing from 8GB to 2GB RSS. Streaming vs DOM vs zero-copy?
Arena allocators? String interning? Profiling with DHAT vs heaptrack? Prioritized by impact."

# search_google
keywords = ["Rust arena allocator benchmark reduce allocations",
            "struct of arrays vs array of structs cache performance memory"]
```

### Best Practices
- Include **current usage AND target** to focus on changes big enough to matter.
- Always include your **language/runtime** -- memory optimization is completely runtime-specific.
- Ask for **prioritization** -- which optimization gives the biggest return first.

---

## 06. Frontend Bundle Optimization

### Recommended Tools
- **search_google**: Bundler-specific optimization techniques, analysis tools, and tree-shaking guides.
- **search_reddit**: Specific dependency swaps and real measured bundle reductions.

### Query Templates
```python
# deep_research
"Reduce Next.js 14 bundle from 1.8MB to 500KB gzipped. Top 10 largest contributors?
modularizeImports, optimizePackageImports? Barrel files defeating tree-shaking?"

# search_google
keywords = ["barrel file tree shaking problem webpack bundle bloat",
            "Next.js bundle size reduction guide dynamic imports"]
```

### Best Practices
- **Attach `package.json` and bundler config** for specific recommendations.
- State current size and target to focus on impactful changes.
- Search for specific problems: "barrel file tree shaking", "moment.js bundle size".

---

## 07. Lazy Loading & Code Splitting

### Recommended Tools
- **deep_research**: Decision framework with specific KB thresholds for splitting decisions.
- **search_reddit**: Failure modes (ChunkLoadError, over-splitting) from production.

### Query Templates
```python
# deep_research
"Code splitting for Next.js 14 with 40+ routes. Minimum KB justifying lazy loading?
Suspense boundary structure? Chunk loading failure handling?"

# search_reddit
queries = ["code splitting strategy route vs component level",
           "too many chunks performance worse code splitting"]
```

### Best Practices
- Ask for **specific thresholds** ("what KB size justifies splitting?").
- Ask about **failure handling** -- stale deployment chunks are the most overlooked aspect.
- Search for **"over-splitting" discussions** -- this anti-pattern causes real regressions.

---

## 08. Connection Pooling Tuning

### Recommended Tools
- **search_google**: Pool sizing formulas (HikariCP wiki is the canonical reference).
- **scrape_pages**: Extract formulas and parameters from HikariCP wiki and PgBouncer docs.

### Query Templates
```python
# search_google
keywords = ["PostgreSQL connection pool size formula HikariCP optimal",
            "database connection pool too large performance degradation"]

# scrape_pages
urls = ["https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing"]
what_to_extract = "pool sizing formula | configuration parameters | timeout settings"
```

### Best Practices
- Include **deployment model** -- workers x instances x pool_size = total connections.
- Key formula: `pool_size = ((core_count * 2) + effective_spindle_count)`.
- Timeout ordering: pool timeout < app request timeout; keep-alive < LB idle timeout.

---

## 09. Concurrent Processing Design

### Recommended Tools
- **deep_research**: Complete concurrent architecture with backpressure, error handling, and monitoring.
- **search_google**: Empirical comparisons between concurrency models with real workloads.

### Query Templates
```python
# deep_research
"Concurrent architecture for Rust pipeline: HTTP -> CPU transform -> PostgreSQL + S3.
Tokio vs rayon vs hybrid? Thread pool sizing for mixed IO/CPU? Backpressure design?"

# search_google
keywords = ["thread pool vs async comparison when to use which",
            "thread pool size formula CPU bound IO bound mixed workload"]
```

### Best Practices
- Describe workload: **IO ratio, CPU intensity, throughput target**.
- Sizing: CPU-bound = `num_cpus`, IO-bound = `num_cpus * (1 + wait_time/compute_time)`.
- Ask about **backpressure explicitly** -- the most overlooked aspect of pipeline design.

---

## 10. Network Request Optimization

### Recommended Tools
- **deep_research**: Layered optimization covering DNS, TCP, TLS, HTTP, and application protocol interactions.
- **scrape_pages**: Exact configuration directives from web server and load balancer docs.

### Query Templates
```python
# deep_research (use 2 questions)
"Q1: HTTP/2 optimization for microservices. Multiplexing vs TCP HOL blocking? Keep-alive
timeout chain across app -> proxy -> LB -> target?"
"Q2: Compression for API responses 500B-2MB. Brotli vs gzip vs zstd for JSON? Break-even size?"

# scrape_pages
urls = ["https://nginx.org/en/docs/http/ngx_http_v2_module.html"]
what_to_extract = "HTTP/2 directives | keep-alive timeout defaults | compression parameters"
```

### Best Practices
- Attach your **nginx/Envoy config** for infrastructure-specific recommendations.
- Timeout chain ordering: app keepalive < pool idle < LB idle < server keepalive.
- Compression: skip below ~860 bytes; Brotli quality 4 for static, gzip-6 for dynamic JSON above 1KB.

## Steering notes

1. **Performance claims are context-dependent.** Verify: benchmark methodology, environment match, vendor vs independent.
2. **Set budget first.** Define targets (p99 <200ms, bundle <150KB) before researching.
3. **Reddit has real production stories** benchmarks don't capture.
4. **CPU-bound vs I/O-bound** need different research approaches.
5. **Benchmark credibility:** Who published? What measured? What environment? When?
