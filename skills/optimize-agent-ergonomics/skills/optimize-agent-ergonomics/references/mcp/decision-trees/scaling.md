# Decision tree — scaling

Scale by working backwards from the load profile, not by reaching for Kubernetes by default. A single MCP server is fine for the single-user case; gateway patterns, session pooling, and async become necessary at specific bottlenecks. This tree picks the smallest architecture that still works for the workload. Source: `optimize-agentic-mcp/references/decision-trees/scaling.md`.

## Decision branches

```
START: What is the load profile?
|
+-- Single-user local
|   +-- No scaling concern
|   +-- One process, stdio, no session externalization
|   +-- Focus on tool design quality, not architecture
|   --> session-and-state.md (session scoping); ../patterns/transport-and-ops.md
|
+-- Per-user remote (each user has their own session)
|   +-- Session-scoped state in-memory
|   +-- Horizontal scale by user
|   +-- Load balancer with session affinity OR externalize state to Redis
|   +-- --> ../patterns/session-and-state.md, ../patterns/transport-and-ops.md
|
+-- Multi-tenant remote (many tenants share one server)
|   +-- Per-tenant isolation (cache keys, audit logs, rate limits)
|   +-- Per-call auth check (token validation per tool call)
|   +-- Sharding by tenant if one tenant dominates load
|   +-- Externalize state to Redis or DB
|   +-- --> security-posture.md (multi-tenant), ../patterns/session-and-state.md
|
+-- High-frequency tools (one tool fires 10x more than the others)
|   +-- Caching is mandatory
|   +-- Three-level cache: L1 in-memory, L2 Redis, L3 persistent
|   +-- Provider-side prompt caching to keep the agent's prefix stable
|   +-- --> ../patterns/caching-economics.md
|
+-- Long-running tools (any tool taking >30s)
|   +-- Return task ID immediately; agent polls for result
|   +-- OR use sampling / elicitation / async patterns
|   +-- Don't block the channel
|   +-- --> ../patterns/advanced-protocol.md, ../patterns/agentic-patterns.md
|
+-- Multiple servers (3+ servers shipping together)
    +-- Gateway with prefixed naming (web__search, db__query)
    +-- Unified tools/list across servers
    +-- Lazy startup + idle timeout
    +-- Circuit breaking on unreachable upstreams
    --> ../patterns/transport-and-ops.md, ../patterns/registry-and-distribution.md
```

## Load distribution patterns

### Session pooling

When throughput is the bottleneck and most calls are stateless after auth:

- Maintain a shared pool of sessions (e.g., 10).
- Any pooled session can serve any request.
- Session state lives in Redis; the pool just holds a connection slot.
- Empirically ~10x throughput vs unique sessions per request (30 r/s → 300 r/s benchmark from the source tree).

### Externalized state

Move per-session state out of the process:

- Redis for short-lived working state (active workflows, in-progress tool tasks).
- DB for cross-session persistence.
- Each request can be served by any process; load balancer can drop session affinity.

### Background tasks for long ops

Anything reliably >30s:

```python
# FastMCP-style; check your SDK
@mcp.tool(task=True)
async def deep_index(repo_url: str) -> str:
    task_id = enqueue(repo_url)
    return f"Indexing started; task_id={task_id}. Poll with `get_index_status(task_id=...)` every 30s."
```

The agent gets the task_id immediately, can do other work, and polls. Don't hold the channel open for 5 minutes — the load balancer probably won't either.

### Multi-agent coordination

When two agents share state on the same workflow, **never** use shared mutable state. Use an append-only event log:

- Event types: `observation`, `decision`, `action`, `result`, `handoff`.
- Agents `read_log` at session start, `log_event` for every action.
- Use a `supersedes` field for corrections without erasing history.

Avoids last-write-wins conflicts and race conditions. Pattern detail: `../patterns/agentic-patterns.md`.

## When to split into multiple servers

A single server is right until one of the following:

- Domains are unrelated (the agent never composes a tool from server A with one from server B).
- Auth boundaries differ (one server is internal-only; another is public).
- Scaling profiles differ wildly (server A: 5 r/s; server B: 500 r/s).
- Codebase ownership splits across teams.
- Tool count exceeds the model's cap even after consolidation.

When splitting, choose the **gateway pattern** rather than parallel direct connections:

- Names prefixed by server (`tickets__create`, `payments__refund`).
- One unified `tools/list` and one auth flow for the agent.
- Lazy starts (start on first call, stop after idle timeout — say 2 minutes).
- Circuit-break on unreachable upstreams; mark tools as temporarily unavailable in `tools/list`.

Deep dive: `../patterns/transport-and-ops.md` (gateway specifics).

## Load-shape-driven choices

| Load profile | First investment | Second investment |
|---|---|---|
| 1 user, dev tool | None | None |
| 100 users, single tenant | Session affinity in LB | Externalize state to Redis |
| 10k users, multi-tenant | Per-tenant rate limits | Per-tenant cache rows; sharding |
| One tool 10x hotter than others | Cache that tool | Per-category rate-limit bucket |
| Tool takes >30s | Background-task pattern | Sampling / elicitation if available |
| 3+ servers | Gateway with prefix names | Lazy startup + circuit breakers |

## Caching strategy

When caching is mandatory (high-frequency tools, multi-tenant repeat reads):

- **L1** — in-process, ~30s TTL, scoped to session.
- **L2** — Redis, ~5min TTL, scoped to user/tenant, key includes a version tag.
- **L3** — persistent DB, ~1hr+ TTL, for genuinely long-lived data (embeddings, model outputs).
- **Cache key**: never include the user's bearer token (lifetimes diverge). Key on user id, tenant id, normalized params.
- **Invalidation**: on writes, invalidate the matching read keys; emit a structured log.

Provider-side prompt caching is a separate concern — keep the agent's prefix byte-identical so the provider's cache hits. Source: `../patterns/caching-economics.md`.

## Production scaling decisions

| Decision | Default | Re-evaluate when |
|---|---|---|
| Replica count | 3 | P95 latency >100ms or CPU >70% sustained |
| HPA targets | CPU 70%, memory 80% | Bursty agentic load with low average CPU |
| Resource limits | 250m–1000m CPU, 256–512 Mi mem | OOM kills, throttling |
| Graceful shutdown | Drain on SIGTERM | Mid-call drops on deploy |
| Rate-limit refill | per-category (read/write/ai/external) | Single bucket starves cheap reads |
| Session state location | In-memory + LB affinity | Cross-pod recovery on pod restart |

## Anti-patterns

- **Reaching for Kubernetes on day one.** A single container is fine until it isn't.
- **Holding the channel for 5 minutes.** Background tasks; agent polls.
- **Shared mutable state across agents.** Append-only log only.
- **Session affinity *and* unbounded in-memory state.** Pod dies, work is lost.
- **No caching on multi-tenant repeat reads.** The same tool firing for 10 tenants reading the same upstream is 10x cost for one fetch.
- **Cache key includes the bearer token.** Lifetimes don't match; cache thrashes.
- **Splitting servers prematurely.** Two servers that share auth, sessions, and rate-limits should usually be one.
- **One gateway with no circuit breakers.** Unreachable upstream takes down every tool.

## Cross-references

- Transport, deployment platforms, gateway specifics: `../patterns/transport-and-ops.md`.
- Session lifecycle, state cleanup: `../patterns/session-and-state.md`.
- Caching economics and provider prompt caching: `../patterns/caching-economics.md`.
- Long-running ops via sampling / elicitation: `../patterns/advanced-protocol.md`.
- Multi-agent event-log pattern: `../patterns/agentic-patterns.md`.
- Multi-tenant security model: `security-posture.md`.

## When to re-evaluate

- Adding the 3rd MCP server — gateway becomes worthwhile.
- Throughput drops under load — session pooling.
- Tool calls start timing out — background-task pattern.
- A second agent needs the first agent's work — append-only event log.
- Moving to Kubernetes — externalize all state.
- One tool dominates load — split it into a separate server with its own scaling profile.
