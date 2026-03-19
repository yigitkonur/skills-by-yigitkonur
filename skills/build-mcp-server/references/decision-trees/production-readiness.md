# Production Deployment Checklist

Moving an MCP server from development to production requires decisions about transport, observability, health checks, deployment platform, rate limiting, and caching. This tree routes through each concern.

## Decision Tree

```
START: Choose your transport
|
+-- Local tool (same machine as client)
|   +-- Use stdio -- simplest, no network overhead
|   +-- Keep stdout clean (logs to stderr only)
|
+-- Remote server (network-accessible)
    +-- Use Streamable HTTP (NOT deprecated SSE)
    |   Bidirectional, works with load balancers, supports OAuth
    +-- Put behind reverse proxy (nginx/Caddy) with HTTPS
    +-- Configure CORS for browser clients
    +-- Set session affinity in load balancer (or externalize state)
    +-- --> transport-and-ops.md

NEXT: Set up observability
|
+-- Structured JSON logging to stderr (never stdout)
|   Log: tool_name, params (minus sensitive), success/fail, duration_ms
+-- Key metrics to emit:
|   +-- tool_call_count by tool name
|   +-- tool_call_duration_seconds histogram
|   +-- tool_error_count by tool + error type
|   +-- active_sessions gauge
|   +-- response_token_estimate histogram (find bloated responses)
+-- --> transport-and-ops.md

NEXT: Health checks
|
+-- Implement /health endpoint with per-component status
|   (database, cache, upstream APIs each report healthy/degraded/unhealthy)
+-- Add KPI metrics when include_metrics=true:
|   +-- Target: >1000 req/s throughput
|   +-- Target: <100ms P95 latency
|   +-- Target: <0.1% error rate
+-- Wire to liveness + readiness probes if on Kubernetes
+-- --> transport-and-ops.md

NEXT: Deploying to Kubernetes?
|
+-- YES
|   +-- 3+ replicas with RollingUpdate (maxUnavailable: 0)
|   +-- HorizontalPodAutoscaler on CPU (70%) and memory (80%)
|   +-- Resource limits: 250m-1000m CPU, 256-512Mi memory
|   +-- Graceful shutdown: handle SIGTERM, drain in-flight calls
|   +-- Session affinity OR externalized state (Redis)
|   +-- --> transport-and-ops.md
+-- NO
    +-- Containerized single-instance or serverless is fine
    +-- Still implement health checks and graceful shutdown

NEXT: Rate limiting
|
+-- Use per-category token buckets (not flat global limit)
|   +-- read:  120 capacity, 10/s refill (cheap, local cache)
|   +-- write: 30 capacity, 2/s refill (DB writes, side effects)
|   +-- ai:    10 capacity, 0.5/s refill (expensive LLM calls)
|   +-- external_api: 20 capacity, 1/s refill (third-party limits)
+-- Return retry_after_ms in rate limit errors
+-- --> transport-and-ops.md

NEXT: Caching
|
+-- Three-level cache: L1 in-memory, L2 Redis, L3 persistent DB
+-- TTL by data type:
|   +-- File trees: 30s L1 / 5min L2
|   +-- Search results: 60s L1 / 10min L2
|   +-- User profiles: 5min L1 / 1hr L2
|   +-- Embeddings: skip L1 / 24hr L2
|   +-- Live metrics: 5s L1 / 30s L2
+-- Include version/ETag in cache keys when available
+-- --> transport-and-ops.md
```

## Key Decision Factors

| Factor | Options | Recommendation |
|---|---|---|
| Transport | stdio vs Streamable HTTP | stdio for local; Streamable HTTP for remote |
| Observability | None vs structured logging + metrics | Always add from day one; track token estimates |
| Health checks | Simple vs per-component with KPIs | Per-component; include metrics for production |
| Deployment | Single instance vs Kubernetes | K8s for production; HPA for bursty agentic load |
| Rate limiting | Global vs per-category buckets | Per-category; different tools have different costs |
| Caching | None vs multi-level | Multi-level; agentic loops repeat identical calls |

## When to Re-evaluate

- When response token estimates show a tool returning >10k tokens consistently (add pagination)
- When error rate exceeds 0.1% (investigate and add circuit breakers)
- When P95 latency exceeds 100ms (profile and add caching or optimize)
- When a new tool category is added (assign it a rate limit bucket)
- When moving from single instance to multi-instance (externalize state)
