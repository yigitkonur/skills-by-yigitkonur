# Transport and Operations

Patterns for production-grade MCP server deployment: clean stdout, transport selection, hot reload, observability, graceful error handling, lazy connections, lazy token validation, transport benchmarks, rate limiting, caching, health checks, and Kubernetes deployment.

---

## 1. Keep stdout Pure JSON-RPC -- All Logs to stderr

The number one cause of mysterious MCP server failures: a stray `print()` or `console.log()` on stdout corrupts the JSON-RPC message stream.

**The rule:** stdout must contain ONLY valid JSON-RPC messages. Everything else goes to stderr.

**Python:**

```python
import logging
import sys

# Configure all logging to stderr
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    stream=sys.stderr
)

logger = logging.getLogger(__name__)

# NEVER use print() in an MCP server
# Use logger instead
logger.info("Server started")
logger.error("Tool failed", exc_info=True)
```

**Node.js:**

```javascript
const logger = {
    info: (msg, data) => console.error(`[INFO] ${msg}`, data ?? ''),
    error: (msg, err) => console.error(`[ERROR] ${msg}`, err?.stack || err || '')
};

// NEVER use console.log() in an MCP server
// Use console.error() or the logger
logger.info("Server started");
```

**Common traps:**
- Third-party libraries that write to stdout (disable their logging or redirect)
- Debugging `print` statements left in production code
- Framework startup banners (suppress them)
- Health check responses written to stdout instead of HTTP

**How to verify:**

```bash
node my-server.js 2>/dev/null | jq .
# Should parse cleanly - any error means stdout pollution
```

**Source:** [Stainless -- Error Handling And Debugging MCP Servers](https://www.stainless.com/mcp/error-handling-and-debugging-mcp-servers); [NearForm -- Implementing MCP](https://nearform.com/digital-community/implementing-model-context-protocol-mcp-tips-tricks-and-pitfalls/)

---

## 2. Use Streamable HTTP, Not Deprecated SSE

The SSE (Server-Sent Events) transport is deprecated. New MCP servers should use Streamable HTTP for remote connections and stdio for local ones.

**Transport selection guide:**

| Scenario | Transport | Why |
|----------|-----------|-----|
| Local tool (same machine) | `stdio` | Simplest, no network overhead |
| Remote server | Streamable HTTP | Bidirectional, supports streaming, future-proof |
| Browser client | Streamable HTTP | Works with standard HTTP infrastructure |
| Legacy integration | SSE (if forced) | Only if the client does not support Streamable HTTP yet |

**Streamable HTTP advantages over SSE:**
- Bidirectional communication (SSE is server-to-client only)
- Works with standard HTTP load balancers and proxies
- Supports proper session management
- Compatible with OAuth authentication flows
- Better suited for production deployment behind CDNs

**Implementation:**

```python
from fastmcp import FastMCP

mcp = FastMCP("My Server")

# For local development
if __name__ == "__main__":
    mcp.run(transport="stdio")

# For remote deployment
# mcp.run(transport="http", host="0.0.0.0", port=8000)
```

**When deploying remotely:**
- Put behind a reverse proxy (nginx, Caddy)
- Enable HTTPS (required for production)
- Set appropriate CORS headers for browser clients
- Configure session affinity in load balancers

**Source:** [NearForm -- Implementing MCP](https://nearform.com/digital-community/implementing-model-context-protocol-mcp-tips-tricks-and-pitfalls/); [MCP specification -- transport](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports)

---

## 3. Use Hot Reload During Development

Kill-restart cycles during MCP server development are slow and break your flow. FastMCP supports automatic file watching and server restart.

```bash
# Auto-restarts on file changes and opens MCP Inspector
fastmcp dev inspector server.py
```

**Development workflow:**

```
1. Start:     fastmcp dev inspector server.py
2. Open:      MCP Inspector at http://localhost:5173
3. Edit:      Modify tool descriptions, add parameters, fix bugs
4. Automatic: Server restarts, Inspector reconnects
5. Test:      Call tools in Inspector to verify changes
6. Repeat
```

**Additional development tools:**
- `fastmcp dev` -- Development server with hot reload
- MCP Inspector (`npx @modelcontextprotocol/inspector@latest`) -- GUI for testing tool calls
- `claude mcp add <name> <command>` -- Quick local registration in Claude Code

**In FastMCP 3.0, tool decorators return the original function for direct testing:**

```python
@tool
def add(a: int, b: int) -> int:
    return a + b

# Direct call in tests (no MCP overhead)
result = add(2, 3)

# Remote call via MCP
await client.call_tool("add", {"a": 2, "b": 3})
```

**Pro tip:** Keep the Inspector open while iterating on tool descriptions. You can immediately see how schema changes affect the tool discovery payload.

**Source:** [FastMCP 3.0 -- What's New](https://jlowin.dev/blog/fastmcp-3); [NearForm -- Implementing MCP](https://nearform.com/digital-community/implementing-model-context-protocol-mcp-tips-tricks-and-pitfalls/)

---

## 4. Add Structured Observability from Day One

MCP servers in production need the same observability as any other service. Do not wait for problems to add logging and metrics.

**Structured logging (JSON to stderr):**

```python
import json
import sys
from datetime import datetime

def log_tool_call(tool_name: str, params: dict, result: dict, duration_ms: float):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "level": "INFO",
        "event": "tool_call",
        "tool": tool_name,
        "params": {k: v for k, v in params.items() if k not in SENSITIVE_FIELDS},
        "success": not result.get("isError", False),
        "duration_ms": duration_ms,
        "tokens_estimate": len(json.dumps(result)) // 4
    }
    print(json.dumps(entry), file=sys.stderr)
```

**Key metrics to emit:**
- `tool_call_count` by tool name (which tools are used most?)
- `tool_call_duration_seconds` histogram (are any tools slow?)
- `tool_error_count` by tool name and error type (which tools fail most?)
- `active_sessions` gauge (how many concurrent users?)
- `response_token_estimate` histogram (which tools produce the largest responses?)

**Health checks:**

```python
@app.get("/health")
def health():
    checks = {
        "database": check_db_connection(),
        "cache": check_redis(),
        "external_api": check_api_reachable()
    }
    healthy = all(checks.values())
    return {"status": "healthy" if healthy else "degraded", "checks": checks}
```

**Non-obvious insight:** Track token estimates per response. A tool that returns 20k tokens on every call is burning context window and money. This metric helps you identify tools that need a `response_format` enum or pagination.

**Source:** [modelcontextprotocol.io](https://modelcontextprotocol.io) best practices; [Pragmatic Engineer -- MCP Deep Dive](https://newsletter.pragmaticengineer.com/p/mcp-deepdive)

---

## 5. Never Call process.exit() or sys.exit() Inside Tool Handlers

Calling `process.exit()` (Node) or `sys.exit()` (Python) inside a tool handler kills the entire MCP server process. The agent does not get a tool error -- it gets a transport-level disconnection. It cannot retry, cannot fall back, cannot even tell the user what went wrong.

**What happens from the agent's perspective:**

```
Agent -> call tool "deploy" -> transport error: connection reset
Agent -> retry? Server is gone. No tool listing available.
Agent -> "I'm unable to reach the MCP server."
```

**Wrong -- kills the server:**

```python
@server.tool("validate_config")
async def validate_config(path: str) -> list[TextContent]:
    config = load_config(path)
    if not config:
        print("Fatal: invalid config", file=sys.stderr)
        sys.exit(1)  # Server dies. All tools gone.
```

**Right -- structured error, server stays alive:**

```python
@server.tool("validate_config")
async def validate_config(path: str) -> list[TextContent]:
    config = load_config(path)
    if not config:
        return [TextContent(
            type="text",
            text=f"Config at '{path}' is invalid or missing. "
                 f"Expected YAML with keys: host, port, db_name."
        )]
        # isError: true is set via raise or return convention
```

**The principle:** If a tool cannot do its job, return `isError: true` with actionable guidance. Keep the server alive so other tools remain available.

**Also catch unhandled exceptions in tool handlers:**

```python
async def safe_handler(func, **kwargs):
    try:
        return await func(**kwargs)
    except Exception as e:
        return [TextContent(type="text", text=f"Internal error: {type(e).__name__}: {e}")]
```

**Source:** [u/rhuanbarreto on r/softwarearchitecture](https://reddit.com/r/softwarearchitecture); [Stainless -- Error Handling And Debugging MCP Servers](https://www.stainless.com/mcp/error-handling-and-debugging-mcp-servers)

---

## 6. Open External Connections Inside Tool Calls, Not at Startup

Open database connections, API clients, and external service handles inside each tool call, not at server startup. Accept the slight latency hit for dramatically higher reliability.

**Wrong -- connection at startup blocks everything:**

```typescript
// Server fails to start if DB is down
const db = new Pool({ connectionString: process.env.DATABASE_URL });
await db.connect(); // Throws -> server never registers tools

const server = new McpServer({ name: "analytics" });
server.tool("query_metrics", schema, async (params) => {
  const result = await db.query(params.sql);
  return { content: [{ type: "text", text: JSON.stringify(result.rows) }] };
});
```

**Right -- connect per tool call:**

```typescript
const server = new McpServer({ name: "analytics" });

server.tool("query_metrics", schema, async (params) => {
  let db;
  try {
    db = new Pool({ connectionString: process.env.DATABASE_URL });
    const result = await db.query(params.sql);
    return { content: [{ type: "text", text: JSON.stringify(result.rows) }] };
  } catch (err) {
    return {
      content: [{ type: "text", text: `Database error: ${err.message}. Check DATABASE_URL.` }],
      isError: true,
    };
  } finally {
    await db?.end();
  }
});
```

**The trade-off is worth it:**
- Tool listing always works, even when external services are down
- Connection errors surface as structured tool errors the agent can reason about
- Each tool is independently resilient -- a broken database does not kill your file tools
- Connection pooling can still be used; just initialize the pool lazily on first tool call

**For high-frequency tools**, use a lazy singleton pattern: initialize the connection on first use, cache it, and handle reconnection inside the tool if it goes stale.

**Source:** [Docker Blog -- MCP Server Best Practices](https://www.docker.com/blog/mcp-server-best-practices/)

---

## 7. Validate Authentication Tokens at Execution Time, Not Startup

Defer token validation to the moment a tool actually needs it. If you validate at startup, an expired or invalid token prevents the MCP client from even discovering what tools are available.

**Wrong -- startup validation (server crashes if token is bad):**

```python
api_token = os.environ["API_TOKEN"]
httpx.get("https://api.example.com/me",
          headers={"Authorization": f"Bearer {api_token}"}).raise_for_status()  # -> crash
server = Server("my-server")  # Never reached
```

**Right -- validate at execution time:**

```python
server = Server("my-server")

@server.tool("search_tickets")
async def search_tickets(query: str) -> list[TextContent]:
    api_token = os.environ.get("API_TOKEN")
    if not api_token:
        return [TextContent(
            type="text",
            text="API_TOKEN not set. Add it to your environment and restart the server."
        )]

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.example.com/tickets",
                params={"q": query},
                headers={"Authorization": f"Bearer {api_token}"},
            )
            resp.raise_for_status()
            return [TextContent(type="text", text=resp.text)]
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            return [TextContent(
                type="text",
                text="Token expired or invalid. Re-authenticate at https://example.com/settings/tokens"
            )]
        raise
```

**What this buys you:**
- Tool discovery always works regardless of auth state
- Token errors are actionable ("re-authenticate at URL") instead of opaque connection failures
- Tokens that rotate or expire mid-session are handled naturally
- Tools with different auth requirements degrade independently

**Same principle applies to:** API keys, OAuth tokens, service account credentials, SSL certs.

**Source:** [Docker Blog -- MCP Server Best Practices](https://www.docker.com/blog/mcp-server-best-practices/)

---

## 8. Transport Choice Makes or Breaks Performance

Transport selection is not a minor config decision -- it determines whether your MCP server can handle production concurrency at all. Real benchmarks from Kubernetes load testing:

| Transport | Concurrency | Success % | Req/s | Avg Response Time |
|---|:---:|:---:|:---:|:---:|
| stdio | 20 | 4% | 0.64 | 20s |
| SSE | 20 | 100% | 7.23 | 18ms |
| Streamable HTTP (shared pool) | 20 | 100% | 48.4 | 5ms |
| Streamable HTTP (shared pool) | 200 | 100% | 299.85 | 622ms |

**Why stdio collapses under concurrency:** stdio uses a single process with stdin/stdout pipes. Every request is serialized. At concurrency 20, requests queue behind each other, most time out, and only 4% succeed. It is designed for single-user local development only.

**Why Streamable HTTP wins:**
- Shared session pooling amortizes connection overhead
- Stateless request/response model maps naturally to HTTP load balancing
- Standard infrastructure (reverse proxies, Kubernetes ingress, health checks) works out of the box
- Scales linearly: 300 req/s at concurrency 200 with sub-second response times

**Production recommendation:**

```
Local dev, single user     -> stdio is fine
Shared team server         -> Streamable HTTP
Production / multi-tenant  -> Streamable HTTP + session pooling + load balancer
```

If you are building a new MCP server today, start with Streamable HTTP transport. The migration cost from stdio to HTTP later is non-trivial -- you will need to rethink session management, add health endpoints, and handle concurrent state.

**Source:** [Stacklok -- Performance Testing MCP Servers in Kubernetes](https://dev.to/stacklok/performance-testing-mcp-servers-in-kubernetes-transport-choice-is-the-make-or-break-decision-for-1ffb)

---

## 9. Token Bucket Rate Limiting per Tool Category

Do not apply a single global rate limit to your MCP server. Different tool categories have radically different cost profiles. Use per-category token buckets.

```typescript
interface BucketConfig {
  capacity: number;    // Max tokens in bucket
  refillRate: number;  // Tokens added per second
}

class TokenBucket {
  private tokens: number;
  private lastRefill: number;

  constructor(private config: BucketConfig) {
    this.tokens = config.capacity;
    this.lastRefill = Date.now();
  }

  consume(cost = 1): boolean {
    const now = Date.now();
    const elapsed = (now - this.lastRefill) / 1000;
    this.tokens = Math.min(this.config.capacity, this.tokens + elapsed * this.config.refillRate);
    this.lastRefill = now;

    if (this.tokens < cost) return false;
    this.tokens -= cost;
    return true;
  }

  get retryAfterMs(): number {
    return Math.ceil(((1 - this.tokens) / this.config.refillRate) * 1000);
  }
}

const rateLimiters: Record<string, TokenBucket> = {
  read:  new TokenBucket({ capacity: 120, refillRate: 10 }), // generous: cheap reads
  write: new TokenBucket({ capacity: 30,  refillRate: 2  }), // moderate: writes have side effects
  ai:    new TokenBucket({ capacity: 10,  refillRate: 0.5 }), // tight: AI calls are expensive
};

const toolCategory: Record<string, keyof typeof rateLimiters> = {
  search_files:   "read",
  list_resources: "read",
  update_record:  "write",
  create_issue:   "write",
  analyze_code:   "ai",
  summarize:      "ai",
};

function withRateLimit(category: string, handler: Function) {
  return async (...args: any[]) => {
    const bucket = rateLimiters[category];
    if (bucket && !bucket.consume()) {
      return {
        content: [{ type: "text", text: JSON.stringify({
          error_category: "RATE_LIMITED",
          message: `Rate limit for ${category} tools exceeded.`,
          retryable: true,
          retry_after_ms: bucket.retryAfterMs,
          suggested_actions: ["wait_and_retry"],
        }) }],
        isError: true,
      };
    }
    return handler(...args);
  };
}
```

**Recommended starting limits:**

| Category | Capacity | Refill Rate | Rationale |
|---|---|---|---|
| read | 120 | 10/s | Local cache; near-free |
| write | 30 | 2/s | DB writes; moderate cost |
| ai | 10 | 0.5/s | LLM inference; expensive |
| external_api | 20 | 1/s | Third-party rate limits |

**Why it matters:** Flat global limits either over-restrict cheap reads or under-protect expensive AI calls. Categorical buckets let you tune each independently and surface informative retry-after values to the agent.

**Source:** [r/mcp](https://reddit.com/r/mcp) community discussion on production server throttling; [Docker Blog -- MCP Server Best Practices](https://www.docker.com/blog/mcp-server-best-practices/)

---

## 10. Multi-Level Caching for MCP Responses

Tool calls that read data frequently return the same result within a session. Add a three-level cache hierarchy to eliminate redundant upstream calls without serving stale data.

```typescript
import { LRUCache } from "lru-cache";
import Redis from "ioredis";

interface CacheEntry { value: unknown; expiresAt: number; }

class MCPCache {
  // L1: in-process memory -- fastest, session-local
  private l1 = new LRUCache<string, CacheEntry>({ max: 500, ttl: 60_000 });

  // L2: Redis -- shared across instances, survives restarts
  private l2: Redis | null = null;

  // L3: persistent DB cache for expensive computations (e.g., embeddings)
  private l3Ttl = 86_400_000; // 24 hours

  constructor(redisUrl?: string) {
    if (redisUrl) this.l2 = new Redis(redisUrl);
  }

  async get(key: string): Promise<unknown | null> {
    // L1 hit
    const l1 = this.l1.get(key);
    if (l1 && l1.expiresAt > Date.now()) return l1.value;

    // L2 hit
    if (this.l2) {
      const raw = await this.l2.get(key);
      if (raw) {
        const parsed = JSON.parse(raw);
        this.l1.set(key, parsed); // warm L1
        return parsed.value;
      }
    }

    return null;
  }

  async set(key: string, value: unknown, ttlMs: number): Promise<void> {
    const entry = { value, expiresAt: Date.now() + ttlMs };
    this.l1.set(key, entry);
    if (this.l2) {
      await this.l2.set(key, JSON.stringify(entry), "PX", ttlMs);
    }
  }
}

const cache = new MCPCache(process.env.REDIS_URL);

// Wrap any tool with caching
async function cachedToolHandler(cacheKey: string, ttlMs: number, fn: () => Promise<unknown>) {
  const cached = await cache.get(cacheKey);
  if (cached) return cached;
  const result = await fn();
  await cache.set(cacheKey, result, ttlMs);
  return result;
}
```

**Cache TTL strategy by data type:**

| Data Type | L1 TTL | L2 TTL | Notes |
|---|---|---|---|
| Repo file tree | 30s | 5min | Changes infrequently mid-session |
| Search results | 60s | 10min | Queries repeat in agentic loops |
| User profile | 5min | 1hr | Rarely changes |
| Embeddings / AI analysis | N/A (skip L1) | 24hr | Expensive to recompute |
| Live metrics / status | 5s | 30s | Must be near-real-time |

**Cache key design -- include version/ETag when available:**

```typescript
const key = `github:issues:${owner}/${repo}:${etag}`;
```

**Why it matters:** Agentic loops repeatedly call the same tools with identical params. Without caching, a 10-step agent workflow that queries file listings on each step can generate 10x the upstream API calls needed.

**Source:** [r/mcp](https://reddit.com/r/mcp) discussion on GitHub MCP server rate limit mitigation; [Docker Blog -- MCP Server Best Practices](https://www.docker.com/blog/mcp-server-best-practices/)

---

## 11. Health Checks with KPI Targets

Implement structured health checks that return per-component status and KPI metrics. This enables infrastructure monitoring, load-balancer routing, and agent-driven diagnostics with a single tool.

```typescript
interface ComponentHealth {
  status: "healthy" | "degraded" | "unhealthy";
  latency_ms?: number;
  error?: string;
  details?: Record<string, unknown>;
}

server.tool("health_check", "Check server health and KPIs. Returns per-component status.", {
  include_metrics: z.boolean().default(false)
    .describe("Set true to include request-rate and latency percentile metrics"),
}, async ({ include_metrics }) => {
  const [dbHealth, cacheHealth, upstreamHealth] = await Promise.allSettled([
    checkDatabase(),
    checkRedis(),
    checkUpstreamAPI(),
  ]);

  const components: Record<string, ComponentHealth> = {
    database: resolveHealth(dbHealth),
    cache: resolveHealth(cacheHealth),
    upstream_api: resolveHealth(upstreamHealth),
  };

  const allHealthy = Object.values(components).every(c => c.status === "healthy");
  const anyUnhealthy = Object.values(components).some(c => c.status === "unhealthy");

  const result: Record<string, unknown> = {
    status: anyUnhealthy ? "unhealthy" : allHealthy ? "healthy" : "degraded",
    components,
    uptime_seconds: process.uptime(),
  };

  if (include_metrics) {
    result.metrics = {
      requests_per_second: metrics.rps,
      p50_latency_ms: metrics.p50,
      p95_latency_ms: metrics.p95,
      p99_latency_ms: metrics.p99,
      error_rate_percent: metrics.errorRate,
    };
    result.kpi_targets = {
      target_rps: "> 1000",
      target_p95_ms: "< 100",
      target_error_rate: "< 0.1%",
    };
  }

  return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
});
```

**Production KPI targets:**

| KPI | Target | Why |
|---|---|---|
| Throughput | > 1,000 req/s | Handles bursty agentic loops |
| P95 latency | < 100ms | Keeps agentic sessions responsive |
| P99 latency | < 500ms | Prevents cascading timeouts |
| Error rate | < 0.1% | LLM context is not wasted on error recovery |
| Tool success rate | > 99% | Low failure rate means fewer retries |

**Why it matters:** Agents that call tools blindly during a degraded server state waste context budget on retries. A structured health tool lets orchestrators skip to a fallback server or pause the session until degradation resolves.

**Source:** [modelcontextprotocol.io](https://modelcontextprotocol.io) observability guidance; [Stacklok -- Performance Testing MCP Servers in Kubernetes](https://dev.to/stacklok/performance-testing-mcp-servers-in-kubernetes-transport-choice-is-the-make-or-break-decision-for-1ffb)

---

## 12. Kubernetes Deployment for MCP Servers

Remote MCP servers running as HTTP services need production-grade Kubernetes deployment with rolling updates, horizontal scaling, and proper resource limits.

**Deployment manifest:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-server
  labels:
    app: mcp-server
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0          # Zero-downtime: never reduce below desired count
  selector:
    matchLabels:
      app: mcp-server
  template:
    metadata:
      labels:
        app: mcp-server
    spec:
      containers:
      - name: mcp-server
        image: your-registry/mcp-server:latest
        ports:
        - containerPort: 3000
        env:
        - name: MCP_SESSION_SECRET
          valueFrom:
            secretKeyRef:
              name: mcp-secrets
              key: session-secret
        resources:
          requests:
            cpu: "250m"
            memory: "256Mi"
          limits:
            cpu: "1000m"
            memory: "512Mi"
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: mcp-server-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: mcp-server
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

**Session affinity for stateful servers:**

```yaml
apiVersion: v1
kind: Service
spec:
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 3600  # 1 hour session stickiness
```

Alternatively, externalize session state to Redis and drop the affinity requirement -- enabling true horizontal scalability.

**Graceful shutdown -- handle SIGTERM to complete in-flight tool calls:**

```typescript
process.on("SIGTERM", async () => {
  await server.close();   // Stop accepting new connections
  await drainInflight();  // Wait for active tool calls to complete
  process.exit(0);
});
```

**Why it matters:** MCP servers under agentic load need autoscaling. Without proper rolling update config, deployments interrupt active agent sessions and corrupt in-progress tool calls.

**Source:** [Stacklok -- Performance Testing MCP Servers in Kubernetes](https://dev.to/stacklok/performance-testing-mcp-servers-in-kubernetes-transport-choice-is-the-make-or-break-decision-for-1ffb); [modelcontextprotocol.io](https://modelcontextprotocol.io) deployment guide
