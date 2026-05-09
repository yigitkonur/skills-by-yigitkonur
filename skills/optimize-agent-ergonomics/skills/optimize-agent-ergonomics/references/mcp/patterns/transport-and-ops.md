# Transport and Operations

Production-grade transport and deployment patterns for MCP servers: pick the right transport for the workload, keep stdout pure JSON-RPC, validate auth at the right layer, and pick the right hosting platform for cold-start, timeout, and response-cap constraints. Two distinct sections — pick a transport first, then pick a platform.

Cross-link to `auth-identity.md` for OAuth / OAuth 2.1 / DCR specifics; this file deals only with where auth happens, not with how it works.

---

## Transport

### 1. Pick stdio for local, HTTP for remote, SSE only for legacy clients

Three transports exist in practice. Pick by where the server runs and who calls it.

| Scenario | Transport | Why |
|---|---|---|
| Local single-user dev tool | `stdio` | Zero network overhead, simplest. Required for `claude mcp add` and Cursor stdio config. |
| Remote multi-user server | Streamable HTTP | Bidirectional, scales horizontally, works with HTTP load balancers, OAuth-friendly. |
| Browser client | Streamable HTTP | Standard HTTP infra, CDN/proxy compatible. |
| Legacy client that doesn't speak Streamable HTTP | SSE | Only because the spec deprecated SSE in 2025-06-18 and most clients moved to Streamable HTTP. |

**The rule.** If the server is local-only and the user is one human at a keyboard, ship stdio. If it is remote, multi-user, or behind a load balancer, ship Streamable HTTP. SSE only exists to keep older clients alive — do not start a new server on SSE in 2026.

**Source:** [modelcontextprotocol.io spec 2025-11-25 transports](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports); [NearForm — Implementing MCP](https://nearform.com/digital-community/implementing-model-context-protocol-mcp-tips-tricks-and-pitfalls/).

---

### 2. Keep stdout pure JSON-RPC — all logs to stderr

The number-one cause of mysterious MCP server failures: a stray `print()` or `console.log()` on stdout corrupts the JSON-RPC message stream. The client disconnects with `parse error` or worse, hangs.

The rule: **stdout contains ONLY valid JSON-RPC messages. Everything else goes to stderr.**

```python
import logging, sys

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

# NEVER print() in an MCP server.
logger.info("Server started")
logger.error("Tool failed", exc_info=True)
```

```javascript
const logger = {
  info:  (m, d) => console.error(`[INFO] ${m}`, d ?? ''),
  error: (m, e) => console.error(`[ERROR] ${m}`, e?.stack || e || ''),
};
// NEVER console.log() in an MCP server.
```

**Common traps.**
- Third-party libs that write to stdout — disable their logging or redirect.
- Debug `print()` left in production code.
- Framework startup banners — suppress them.
- Health-check responses written to stdout instead of HTTP.

**How to verify.**

```bash
node my-server.js 2>/dev/null | jq .
# Should parse cleanly. Any error → stdout pollution.
```

**Source:** [Stainless — Error Handling and Debugging MCP Servers](https://www.stainless.com/mcp/error-handling-and-debugging-mcp-servers); [NearForm — Implementing MCP](https://nearform.com/digital-community/implementing-model-context-protocol-mcp-tips-tricks-and-pitfalls/).

---

### 3. Auth at transport vs auth at tool — pick deliberately

Two valid layers to enforce auth. Pick by what the client sees on failure.

- **Transport-level** — gate on `Authorization: Bearer ...`, OAuth 2.1, mTLS, IP allowlist. Failure returns HTTP 401/403. The MCP client sees a connection error, not a tool error. Use for "this entire server is gated" semantics.
- **Tool-level** — accept the connection, validate scopes inside each tool handler, return `isError: true` with actionable text. Failure becomes a normal MCP tool result. Use for "tool list always works; some tools require additional auth."

```python
@server.tool("delete_account")
async def delete_account(user_id: str, ctx) -> dict:
    if "admin" not in ctx.principal.scopes:
        return {"content": [{"type": "text",
            "text": "delete_account requires admin scope. Re-authenticate at https://example.com/admin to grant it."}],
            "isError": True}
    # ...
```

**Why both.** Transport-level gates the entire server (good for B2B internal). Tool-level gates individual sensitive ops (good for "broad read scope, narrow write scope"). Combine them: transport-level proves the user is who they say, tool-level proves they are allowed to do this specific thing.

**Cross-link.** OAuth 2.1, PKCE, DCR, RFC 9728 PRM, CIMD, OBO and step-up consent live in `auth-identity.md`.

**Source:** [Cloudflare workers-oauth-provider](https://github.com/cloudflare/workers-oauth-provider); [HubSpot remote MCP architecture](https://product.hubspot.com/blog/unlocking-deep-research-crm-connector-for-chatgpt) (2025-06-18).

---

### 4. CORS — required for browser MCP clients

Streamable HTTP servers consumed by browser clients (Claude Desktop is not a browser; VS Code MCP web is) need CORS. Ship the right headers or browser fetches silently fail at the preflight.

```typescript
// Minimum viable CORS for an MCP server.
const cors = {
  "Access-Control-Allow-Origin":      "*",                       // or specific origins
  "Access-Control-Allow-Methods":     "POST, OPTIONS",
  "Access-Control-Allow-Headers":     "Content-Type, Authorization, MCP-Session-Id",
  "Access-Control-Expose-Headers":    "MCP-Session-Id",
  "Access-Control-Max-Age":           "86400",
};

if (req.method === "OPTIONS") {
  return new Response(null, { status: 204, headers: cors });
}
```

**Gotchas.**
- `Authorization` and `MCP-Session-Id` must both be in `Allow-Headers` — missing either breaks auth or session tracking.
- Wildcard `*` in `Allow-Origin` is incompatible with `Allow-Credentials: true`. Pick one.
- Preflight cache via `Max-Age` — set it. Browsers re-preflight every few seconds otherwise.

**Source:** [MDN — CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS); MCP spec 2025-11-25 transport security guidance.

---

### 5. Skeleton — stdio server

```python
# server.py
from fastmcp import FastMCP

mcp = FastMCP("local-tool")

@mcp.tool(description="Sum two numbers.")
def add(a: int, b: int) -> int:
    return a + b

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

Run via `claude mcp add local-tool python server.py` (Claude Code), `.cursor/mcp.json` block (Cursor), or `~/Library/Application Support/Claude/claude_desktop_config.json` (Claude Desktop). Single user, single process, single stdin/stdout pipe — no concurrency.

---

### 6. Skeleton — Streamable HTTP server

```python
# server.py
import os
from fastmcp import FastMCP

mcp = FastMCP("remote-tool")

@mcp.tool(description="Look up a record by id.")
def get_record(id: str) -> dict:
    return db.get(id) or {"error": "not found"}

if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="0.0.0.0",                                # never 127.0.0.1 in containers
        port=int(os.environ.get("PORT", 8080)),
    )
```

```typescript
// server.ts — Node, MCP SDK
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { createServer } from "http";

const server = new Server({ name: "remote-tool", version: "1.0.0" });
// register tools...

const transport = new StreamableHTTPServerTransport({
  sessionIdGenerator: () => crypto.randomUUID(),       // omit / undefined for stateless
});
await server.connect(transport);

createServer(transport.handler).listen(process.env.PORT ?? 8080);
```

The HTTP server accepts `POST /mcp` (request) and uses chunked transfer for streamed replies. No SSE upgrade. Behind nginx/Caddy/Cloudflare; HTTPS terminated at the proxy.

---

### 7. Skeleton — SSE handler (legacy fallback only)

```typescript
// SSE for clients that haven't migrated to Streamable HTTP.
// Same SDK; different transport class; same server.
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";

app.get("/sse",  (req, res) => server.connect(new SSEServerTransport("/messages", res)));
app.post("/messages", (req, res) => transport.handlePostMessage(req, res));
```

Mark this endpoint deprecated in your README. Log a warning when used so you can retire it once the client telemetry shows zero SSE traffic.

**Source:** [MCP spec 2025-06-18 changelog (SSE deprecation)](https://modelcontextprotocol.io/specification/2025-11-25/changelog).

---

### 8. Hot-reload during development

Kill-restart cycles are slow. FastMCP watches the file and restarts.

```bash
fastmcp dev inspector server.py
# Auto-restarts on save. Opens MCP Inspector at http://localhost:5173.
```

Workflow: edit description → save → server restarts → Inspector reconnects → click the tool → see new behaviour. Cuts MCP iteration time roughly in half.

**Source:** [FastMCP 3.0 — What's New](https://www.jlowin.dev/blog/fastmcp-3-whats-new).

---

### 9. Open external connections inside tool calls, not at startup

A DB connection or upstream API client opened at startup makes server boot dependent on the upstream being healthy. If the DB is down at startup, the server never registers tools and the agent gets a transport-level disconnection — no retry, no fallback.

```typescript
// Wrong: server fails to register tools when DB is down.
const db = new Pool({ connectionString: process.env.DATABASE_URL });
await db.connect();                                              // throws → server never starts
const server = new McpServer({ name: "analytics" });
```

```typescript
// Right: connect inside the tool. Tool listing always works.
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
  } finally { await db?.end(); }
});
```

For high-frequency tools, lazy-singleton: initialize on first call, cache, reconnect on stale. The tool surface remains discoverable when the upstream is degraded.

**Source:** [Docker Blog — MCP Server Best Practices](https://www.docker.com/blog/mcp-server-best-practices/).

---

### 10. Validate auth tokens at execution time, not at startup

Same principle as connections. Validating `API_TOKEN` at startup means tool discovery breaks when the token expires. Validate inside the tool; return an actionable `isError: true`.

```python
@server.tool("search_tickets")
async def search_tickets(query: str) -> list[TextContent]:
    api_token = os.environ.get("API_TOKEN")
    if not api_token:
        return [TextContent(type="text",
            text="API_TOKEN not set. Add it to the environment and restart the server.")]
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(URL, headers={"Authorization": f"Bearer {api_token}"})
            r.raise_for_status()
            return [TextContent(type="text", text=r.text)]
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            return [TextContent(type="text",
                text="Token expired. Re-authenticate at https://example.com/settings/tokens.")]
        raise
```

Tools with different auth requirements degrade independently. Token rotation works mid-session.

**Cross-link:** `auth-identity.md` covers refresh-token rotation and step-up consent.

**Source:** [Docker Blog — MCP Server Best Practices](https://www.docker.com/blog/mcp-server-best-practices/).

---

### 11. Never call `process.exit()` or `sys.exit()` inside a tool handler

A tool that calls `sys.exit()` kills the entire MCP server. From the agent's perspective: transport disconnect, no tool error, no retry path, no diagnostic. The server is gone; the agent gives up.

```python
# Wrong — server dies. All other tools become unreachable.
@server.tool("validate_config")
async def validate_config(path: str) -> list[TextContent]:
    if not load_config(path):
        sys.exit(1)
```

```python
# Right — structured error, server alive.
@server.tool("validate_config")
async def validate_config(path: str) -> list[TextContent]:
    if not load_config(path):
        return [TextContent(type="text",
            text=f"Config at '{path}' is invalid. Expected YAML with keys: host, port, db_name.")]
```

Wrap every tool handler in a top-level `try/except` that converts unhandled exceptions to `isError: true`. Server staying alive is non-negotiable.

**Source:** [Stainless — Error Handling](https://www.stainless.com/mcp/error-handling-and-debugging-mcp-servers).

---

### 12. Transport choice makes or breaks performance

Stdio collapses under concurrency; Streamable HTTP scales linearly. Numbers from Stacklok's K8s benchmarks:

| Transport | Concurrency | Success % | Req/s | Avg Response |
|---|---:|---:|---:|---:|
| stdio | 20 | 4% | 0.64 | 20s |
| SSE | 20 | 100% | 7.23 | 18ms |
| Streamable HTTP (shared pool) | 20 | 100% | 48.4 | 5ms |
| Streamable HTTP (shared pool) | 200 | 100% | 299.85 | 622ms |

**Why stdio collapses.** Single process, single stdin/stdout pipe, requests serialize. At concurrency 20 most requests time out — only ~4% succeed.

**Production rule.**
- Local dev, single user → stdio is fine.
- Shared team server → Streamable HTTP.
- Production / multi-tenant → Streamable HTTP + session pool + load balancer.

If you start on stdio and outgrow it, you will rewrite session management, add health endpoints, and rethink concurrency. Start on Streamable HTTP for anything that might go remote.

**Source:** [Stacklok — Performance Testing MCP Servers in Kubernetes](https://dev.to/stacklok/performance-testing-mcp-servers-in-kubernetes-transport-choice-is-the-make-or-break-decision-for-1ffb).

---

### 13. Observability — structured logs, metrics, health endpoints

MCP servers in production need the same observability as any other service. Structured JSON logs to stderr, prometheus-style metrics on `/metrics`, JSON health on `/health`.

```python
def log_tool_call(tool, params, result, ms):
    print(json.dumps({
        "ts":    datetime.utcnow().isoformat(),
        "level": "INFO",
        "event": "tool_call",
        "tool":  tool,
        "params": {k: v for k, v in params.items() if k not in SENSITIVE},
        "ok":    not result.get("isError", False),
        "ms":    ms,
        "tokens": len(json.dumps(result)) // 4,
    }), file=sys.stderr)
```

**Metrics worth emitting.** `tool_call_count{tool}`, `tool_duration_seconds{tool}` histogram, `tool_error_count{tool,error_type}`, `active_sessions`, `response_token_estimate{tool}` histogram. The last one — token estimates per response — flags tools that burn agent context budget on every call.

**Health endpoint.**

```python
@app.get("/health")
def health():
    checks = {"db": check_db(), "cache": check_redis(), "upstream": check_api()}
    return {"status": "healthy" if all(checks.values()) else "degraded", "checks": checks}
```

**Source:** [modelcontextprotocol.io best practices](https://modelcontextprotocol.io); [Pragmatic Engineer — MCP Deep Dive](https://newsletter.pragmaticengineer.com/p/mcp-deepdive).

---

### 14. Token-bucket rate limiting per tool category

Flat global limits over-restrict cheap reads or under-protect expensive AI calls. Bucket per category.

```typescript
const buckets: Record<string, TokenBucket> = {
  read:  new TokenBucket({ capacity: 120, refillRate: 10  }), // generous: cheap reads
  write: new TokenBucket({ capacity:  30, refillRate:  2  }), // moderate: side effects
  ai:    new TokenBucket({ capacity:  10, refillRate:  0.5 }), // tight: LLM calls
};
const category: Record<string, keyof typeof buckets> = {
  search_files: "read", list_resources: "read",
  update_record: "write", create_issue: "write",
  analyze_code: "ai", summarize: "ai",
};
function withRateLimit(cat: string, h: Function) {
  return async (...a: any[]) => {
    const b = buckets[cat];
    if (b && !b.consume()) return {
      content: [{ type: "text", text: JSON.stringify({
        error_category: "RATE_LIMITED",
        retryable: true, retry_after_ms: b.retryAfterMs,
      })}], isError: true };
    return h(...a);
  };
}
```

When the bucket is empty, return a structured error with `retry_after_ms` so the agent knows when to come back. Cross-link `error-handling.md` for retry envelope shape.

**Source:** [Docker Blog — MCP Best Practices](https://www.docker.com/blog/mcp-server-best-practices/).

---

### 15. Multi-level caching — L1 in-process, L2 Redis, L3 persistent

Agentic loops re-call the same tools with the same params. Cache aggressively but bound TTLs by data volatility.

```typescript
class MCPCache {
  private l1 = new LRUCache<string, Entry>({ max: 500, ttl: 60_000 });
  private l2: Redis | null = null;
  constructor(url?: string) { if (url) this.l2 = new Redis(url); }

  async get(k: string) {
    const a = this.l1.get(k); if (a && a.expiresAt > Date.now()) return a.value;
    if (this.l2) {
      const raw = await this.l2.get(k);
      if (raw) { const p = JSON.parse(raw); this.l1.set(k, p); return p.value; }
    }
    return null;
  }
  async set(k: string, v: unknown, ttl: number) {
    const e = { value: v, expiresAt: Date.now() + ttl };
    this.l1.set(k, e);
    if (this.l2) await this.l2.set(k, JSON.stringify(e), "PX", ttl);
  }
}
```

| Data | L1 TTL | L2 TTL | Notes |
|---|---|---|---|
| Repo file tree | 30s | 5min | Changes infrequently mid-session |
| Search results | 60s | 10min | Repeats heavily in agentic loops |
| User profile | 5min | 1hr | Rarely changes |
| Embeddings | skip L1 | 24hr | Expensive to recompute |
| Live metrics | 5s | 30s | Must be near-real-time |

Cache key includes ETag/version when available so you don't serve stale data.

**Source:** community discussion on GitHub MCP rate-limit mitigation, r/mcp.

---

### 16. Kubernetes deployment — rolling updates, HPA, graceful shutdown

Remote MCP servers under agentic load need autoscaling and zero-downtime deploys.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata: { name: mcp-server }
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate: { maxSurge: 1, maxUnavailable: 0 }   # zero downtime
  selector: { matchLabels: { app: mcp-server } }
  template:
    metadata: { labels: { app: mcp-server } }
    spec:
      containers:
      - name: mcp-server
        image: registry/mcp-server:latest
        ports: [{ containerPort: 3000 }]
        resources:
          requests: { cpu: "250m", memory: "256Mi" }
          limits:   { cpu: "1000m", memory: "512Mi" }
        livenessProbe:  { httpGet: { path: /health,       port: 3000 }, initialDelaySeconds: 10, periodSeconds: 30 }
        readinessProbe: { httpGet: { path: /health/ready, port: 3000 }, initialDelaySeconds:  5, periodSeconds: 10 }
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata: { name: mcp-server-hpa }
spec:
  scaleTargetRef: { kind: Deployment, name: mcp-server, apiVersion: apps/v1 }
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource: { name: cpu,    target: { type: Utilization, averageUtilization: 70 } }
  - type: Resource
    resource: { name: memory, target: { type: Utilization, averageUtilization: 80 } }
```

```typescript
// Graceful shutdown — drain in-flight tool calls before exit.
process.on("SIGTERM", async () => {
  await server.close();      // stop accepting new
  await drainInflight();     // wait for active calls
  process.exit(0);
});
```

Externalize session state to Redis so any pod can serve any request and HPA isn't blocked by sticky sessions.

**Source:** [Stacklok K8s benchmarks](https://dev.to/stacklok/performance-testing-mcp-servers-in-kubernetes-transport-choice-is-the-make-or-break-decision-for-1ffb).

---

## Deployment platforms

Each managed platform has hard constraints that decide whether your workload is even feasible. Read the matrix before picking; revisit when the workload changes.

### 17. Cloudflare Workers + McpAgent — stateful via Durable Objects

Two primitives: `McpAgent` (durable, per-session DO + SQLite + hibernation) and `createMcpHandler` (stateless plain Worker). Pick by whether each session needs persistent memory.

```typescript
import { McpAgent } from "agents/mcp";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";

export class MyMCP extends McpAgent<Env, State> {
  server = new McpServer({ name: "my-mcp", version: "1.0.0" });
  async init() {
    this.server.tool("ping", {}, async () => ({
      content: [{ type: "text", text: `pong ${this.state.counter ?? 0}` }],
    }));
  }
}

export default {
  fetch(req: Request, env: Env, ctx: ExecutionContext) {
    return MyMCP.serve("/mcp").fetch(req, env, ctx);
  },
};
```

**Hibernation kills idle costs.** `this.ctx.acceptWebSocket(ws, ["tag"])` evicts the DO from memory while keeping the WS open; rehydrate on next message via `ws.deserializeAttachment()`. A session with 60s of work + 10min of idle per hour bills ~11× more without hibernation.

**Limits worth knowing.** CPU 30s default, opt into 5min via `wrangler.toml [limits] cpu_ms = 300000`. No wall-clock limit — `await fetch()` can sit for hours. `serializeAttachment()` cap is **2,048 bytes**; larger state goes to `this.ctx.storage.sql`.

**Regulated workloads.** `jurisdiction: "fedramp"` pins the DO and SQLite to FedRAMP Moderate. `jurisdiction: "eu"` for GDPR.

**OAuth without a separate auth server.** `workers-oauth-provider` ships a conforming OAuth 2.1 AS in the Worker — DCR (RFC 7591), PKCE, token introspection, federation via `tokenExchangeCallback`. See `auth-identity.md`.

**Source:** [developers.cloudflare.com/agents/guides/remote-mcp-server/](https://developers.cloudflare.com/agents/guides/remote-mcp-server/); [github.com/cloudflare/workers-oauth-provider](https://github.com/cloudflare/workers-oauth-provider).

---

### 18. Vercel — Fluid Compute or 300s ceiling

`@vercel/mcp-adapter` supports stateless and Redis-backed stateful. Hard wall: execution duration depends on plan **and** Fluid Compute toggle.

| Plan | Default | Fluid Compute |
|---|---|---|
| Hobby | 60s | 300s |
| Pro | 60s | **800s** |
| Enterprise | 60s | **800s** |

The quickstart sets `maxDuration: 60`. Long-running tools silently 504 with `FUNCTION_INVOCATION_TIMEOUT` unless you override AND enable Fluid Compute in **Project Settings → Functions → Fluid Compute**.

```typescript
// app/api/[transport]/route.ts
import { createMcpHandler } from "@vercel/mcp-adapter";
const handler = createMcpHandler(/* ... */);
export const maxDuration = 800;   // requires Fluid Compute on
export { handler as GET, handler as POST };
```

**Response cap: 4.5 MB hard.** Exceeding returns `413 FUNCTION_PAYLOAD_TOO_LARGE`. Tool that returns screenshots, PDFs, parsed CSVs — offload to Vercel Blob/R2/S3, return a presigned URL in the MCP response.

```typescript
server.tool("export_report", { format: z.enum(["pdf","csv"]) }, async ({ format }) => {
  const blob = await renderReport(format);
  const { url } = await put(`reports/${nanoid()}.${format}`, blob, {
    access: "public", token: process.env.BLOB_READ_WRITE_TOKEN,
  });
  return { content: [{ type: "text", text: `Report ready: ${url} (expires in 1 hour)` }] };
});
```

**Source:** [vercel.com/blog/building-efficient-mcp-servers](https://vercel.com/blog/building-efficient-mcp-servers); [vercel.com/docs/functions/limitations](https://vercel.com/docs/functions/limitations).

---

### 19. Smithery.ai — runtime + `startCommand.type` mismatch fails silently

`smithery.yaml` has two runtimes: container and stdio. Mismatching `runtime` with `startCommand.type` deploys nothing.

```yaml
# Container runtime — must use type: http
runtime: container
build: { dockerfile: Dockerfile, dockerBuildPath: . }
startCommand:
  type: http
  configSchema:
    type: object
    required: ["TAVILY_API_KEY"]
    properties:
      TAVILY_API_KEY: { type: string, description: "Tavily API key from https://tavily.com" }
```

```yaml
# stdio runtime — JS bundle only, no Docker
runtime: stdio
startCommand:
  type: stdio
  commandFunction: |-
    (config) => ({ command: "node", args: ["dist/index.js"],
                   env: { TAVILY_API_KEY: config.TAVILY_API_KEY } })
```

`configSchema` (JSON Schema Draft-7) auto-renders the Smithery Connect UI. `required` becomes required inputs, `format: password` masks fields. Optional fields without `default` arrive as `undefined` — the server must tolerate that.

**Source:** [smithery.ai/docs/build](https://smithery.ai/docs/build).

---

### 20. AWS Lambda + LWA — `AWS_LWA_INVOKE_MODE=response_stream`

Streamable HTTP requires response streaming. Plain Lambda function URLs buffer — incompatible. Fix: Lambda Web Adapter with response streaming enabled.

```dockerfile
FROM public.ecr.aws/lambda/nodejs:20
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.9.1 /lambda-adapter /opt/extensions/lambda-adapter
ENV AWS_LWA_INVOKE_MODE=response_stream
ENV AWS_LWA_ASYNC_INIT=true
ENV PORT=8080
COPY dist/ ${LAMBDA_TASK_ROOT}/
CMD ["index.handler"]
```

| Limit | Value | Consequence |
|---|---|---|
| Lambda timeout | 15min hard | No override |
| Streamed body | 200 MB max | 6 MB buffered fallback |
| Bandwidth | uncapped first 6 MB, then **2 MB/s** | Large blobs throttle |
| Init timeout | 10s | `ASYNC_INIT=true` defers blocking work |

**The 15-min wall.** Tools that might exceed 15min must use SQS + webhook. Lambda enqueues, returns `{jobId, status: "queued"}` immediately, a separate worker processes, agent polls a `get_job_status` tool. Mandatory on Lambda; useful pattern everywhere.

```typescript
server.tool("index_repository", { repo_url: z.string() }, async ({ repo_url }) => {
  const jobId = crypto.randomUUID();
  await sqs.send(new SendMessageCommand({
    QueueUrl: process.env.INDEX_QUEUE,
    MessageBody: JSON.stringify({ jobId, repo_url }),
  }));
  return { content: [{ type: "text", text: JSON.stringify({
    jobId, status: "queued", poll_tool: "get_index_status", estimated_seconds: 180,
  })}] };
});
```

**Source:** [github.com/aws/aws-lambda-web-adapter](https://github.com/aws/aws-lambda-web-adapter); [docs.aws.amazon.com/lambda/latest/dg/configuration-response-streaming.html](https://docs.aws.amazon.com/lambda/latest/dg/configuration-response-streaming.html).

---

### 21. GCP Cloud Run — 60-minute HTTP timeout, the longest of any managed platform

Cloud Run caps requests at 3,600s (60min); default 300s. **Double Vercel Enterprise Fluid Compute (800s); 4× Lambda (900s).** When you need one managed platform that can run a single MCP tool call near an hour, Cloud Run is the only mainstream answer.

```bash
gcloud run deploy my-mcp \
  --source . --region us-central1 \
  --timeout 3600 \
  --no-allow-unauthenticated \
  --port 8080
```

**Two footguns kill first-time deploys.**
- **Bind `0.0.0.0`, not `127.0.0.1`.** Cloud Run routes external traffic to the container; localhost is invisible to the proxy.
- **Use `--no-allow-unauthenticated` + IAM `roles/run.invoker`.** Public unauth = remote MCP open to the world.

```python
import os
from fastmcp import FastMCP
mcp = FastMCP("my-mcp")
mcp.run(transport="http", host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
```

Local testing through auth: `gcloud run services proxy my-mcp --port=8080`. GPU is GA on Cloud Run mid-2025 — viable for ML MCPs that need <60-min bursts.

**Source:** [cloud.google.com/blog — build a remote MCP server on Cloud Run](https://cloud.google.com/blog/topics/developers-practitioners/build-and-deploy-a-remote-mcp-server-to-google-cloud-run-in-under-10-minutes).

---

### 22. Azure Container Apps — standalone or per-session Hyper-V isolation

ACA has a unique second mode: **dynamic sessions**. Hosts the *tool code* inside Hyper-V isolated per-session sandboxes. Use when tools execute untrusted or user-supplied code (data-science notebooks, code interpreters, untrusted scripts).

| Mode | You deploy | Per-session isolation | Use for |
|---|---|---|---|
| Standalone | Your MCP server container | No (standard ACA replicas) | Normal remote MCP |
| Dynamic sessions | Tool code | Yes — Hyper-V sandbox per session | Code-execution-as-a-service, multi-tenant hard isolation |

ACA docs explicitly recommend `min-replicas: 1` for interactive MCP servers — scale-to-zero cold starts (5-15s) break interactive agent loops. Standalone uses Entra ID built-in auth; dynamic sessions use scoped per-session-pool API keys.

```bash
az containerapp create \
  --name my-mcp --resource-group rg \
  --image myregistry/my-mcp:latest \
  --ingress external --target-port 8080 \
  --min-replicas 1 --max-replicas 10
```

**Source:** [learn.microsoft.com/azure/container-apps/mcp-overview](https://learn.microsoft.com/en-us/azure/container-apps/mcp-overview).

---

### 23. Fly.io Machines — stateful + per-machine volumes, fast launcher

`flyctl mcp launch` (0.3.125+) provisions a Fly Machine, sets a random bearer token as a secret, patches the local MCP client config (Claude Desktop or Cursor) to send that token.

```bash
fly mcp launch --claude --server myapp --secret API_KEY=sk-...
```

Server gets `FLY_MCP_TOKEN` in env; the adapter enforces `Authorization: Bearer ${FLY_MCP_TOKEN}`; client config is patched.

**Footgun.** Scale-to-zero (`auto_stop_machines = true`) + in-memory sessions are incompatible — first request after sleep gets a fresh Machine and loses session state. Externalize to Redis, Fly Postgres, or LiteFS, or set min-machine = 1.

Pricing floor: `shared-cpu-1x @ 256MB` ~$2/mo; `performance-1x @ 2GB` ~$32/mo. No enforced HTTP timeout.

**Source:** [fly.io/docs/blueprints/remote-mcp-servers/](https://fly.io/docs/blueprints/remote-mcp-servers/); [fly.io/blog/mcp-launch/](https://fly.io/blog/mcp-launch/).

---

### 24. Modal — stateless GPU serverless

Modal's containers scale to zero, scale cold, move between hosts. Per-session DO-style state isn't available. FastMCP must run in stateless mode.

```python
import modal
from fastmcp import FastMCP
from fastapi import FastAPI

app = modal.App("mcp-server")
image = modal.Image.debian_slim().pip_install("fastmcp", "fastapi")
mcp = FastMCP("my-mcp", stateless_http=True)

@mcp.tool()
async def analyze(code: str) -> str:
    return f"lines: {len(code.splitlines())}"

web_app = FastAPI()
web_app.mount("/mcp", mcp.streamable_http_app())

@app.function(image=image, gpu="H100", timeout=600)
@modal.asgi_app()
def fastapi_app():
    return web_app
```

GPU economics: H100 ~$0.001097/sec, A10 ~$0.000306/sec, CPU ~$0.0000131/core-sec. Use Modal when the workload is GPU-bound (model inference inside a tool, ML embeddings, image/video processing).

**Source:** [modal.com/docs/examples/mcp_server_stateless](https://modal.com/docs/examples/mcp_server_stateless); [modal.com/pricing](https://modal.com/pricing).

---

### 25. Railway / Render / Koyeb / Northflank — budget remote MCP

Generic container hosting with no MCP-specific quirks. Pick by ergonomics and price.

- **Railway** — easy deploy, no enforced HTTP cap, build limits 10min Free / 20min Trial. Service volume, 1 replica default. Good for prototypes; cross-link to `use-railway` skill for ongoing operations.
- **Render** — managed HTTPS, autoscaling, free tier. **Render's own MCP API key is account-wide** — leaked key = full account compromise. Treat it like a root token.
- **Koyeb / Northflank** — scale-to-zero stateless. Set `sessionIdGenerator: undefined` so cold starts don't strand sessions. Externalize state to Redis or set min-scale ≥ 1 if state matters.

```typescript
// Stateless mode for scale-to-zero hosts
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
const transport = new StreamableHTTPServerTransport({ sessionIdGenerator: undefined });
await server.connect(transport);
```

```bash
koyeb deploy . my-mcp/main --git github.com/me/my-mcp-server \
  --ports 8080:http --routes /:8080 --min-scale 0 --max-scale 5 --instance-type free
```

**Source:** [koyeb.com/tutorials/deploy-remote-mcp-servers-to-koyeb](https://www.koyeb.com/tutorials/deploy-remote-mcp-servers-to-koyeb-using-streamable-http-transport); [render.com/docs/mcp-server](https://render.com/docs/mcp-server).

---

### 26. Deno Deploy — TypeScript-native, KV-backed

Deno Deploy's sandbox quirks worth pre-learning:

- **`Deno.connect` to port 443 is blocked.** Use `Deno.connectTls` for TLS targets.
- **Memory cap:** 512 MB / deployment, 1 GB total free tier.
- **Bind `0.0.0.0`** requires `--dnsRebinding` plus an `MCP_ALLOWED_HOSTS` allowlist; wildcard `*` rejected.
- **SSRF guard:** `Deno.connect` and `fetch()` default-block private IPs (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), localhost, `.internal`.
- **Force JSON-only** with `MCP_JSON_RESPONSE=true` to disable SSE framing.
- **Auth env:** `MCP_HTTP_BEARER_TOKEN` configures the bearer check; `MCP_REQUIRE_HTTP_AUTH=true` refuses to start if the token env is unset — prevents accidental public deploys.

**Source:** [github.com/phughesmcr/deno-mcp-template](https://github.com/phughesmcr/deno-mcp-template); [docs.deno.com/deploy/pricing_and_limits](https://docs.deno.com/deploy/pricing_and_limits).

---

### 27. Hosted "tool-as-a-service" — Composio, Klavis, Arcade, Pica

You're not deploying an MCP server — you're consuming one. They handle OAuth, token rotation, rate-limiting, compliance. Pricing decision: Composio is ~29× more expensive than raw Lambda on pure compute math, but pays off when you need ≥5 third-party OAuth integrations (Gmail, Slack, Notion, Linear, GitHub, etc.).

| Service | Compliance | User-scoped auth | Self-host | Best fit |
|---|---|---|---|---|
| Composio | SOC 2 + ISO 27001 + VPC | Per-connection | No | Agent SaaS with 1,000+ integrations target |
| Klavis | SOC 2 Type II + GDPR | Strata progressive discovery | Docker / pipx | Training envs, white-label consumer products |
| Arcade.dev | SSO/SAML + dedicated tenant | First-class | OSS MIT SDK | Teams that need user-scoped auth + audit |
| Pica | Secret header | None | No | Quick prototypes, OpenAI Agent Builder demos |

**Source:** [composio.dev/pricing](https://composio.dev/pricing); [klavis.ai](https://www.klavis.ai/blog); [arcade.dev/pricing](https://arcade.dev/pricing/); [mcp.picaos.com](https://mcp.picaos.com/).

---

### 28. Platform-picker matrix

Compact reference. Pick the row, read the constraints.

| Platform | Session primitive | Streamable HTTP | Max duration | Response cap | Best for |
|---|---|---|---|---|---|
| Cloudflare Workers + McpAgent | Durable Object + SQLite + hibernation | Native | 5min CPU opt-in; no wall-clock limit | 100 MB Free/Pro, 500 MB Ent | Multi-tenant SaaS, personal CLI |
| Vercel Fluid Compute | BYO (Redis for resumability) | Native | 300s Hobby / **800s Pro+Ent** | **4.5 MB hard** | Team B2B, serverless-first |
| Smithery.ai | Managed per-server | Native when `type: http` | Container limits | Container limits | Marketplace / public servers |
| Modal | None (stateless only) | Via FastMCP + FastAPI | Function `timeout` | Function memory | Python/ML, GPU workloads |
| Fly.io Machines | Machine-local volumes | Native | No enforced HTTP timeout | No enforced cap | Stateful team-internal |
| Railway | Service volume, 1 replica default | Native | No hard cap | Build 10min Free | Prototypes, budget |
| AWS Lambda + LWA | None inline; SQS+webhook for long | `AWS_LWA_INVOKE_MODE=response_stream` | **15min hard** | 200 MB streamed / 6 MB buffered | Enterprise VPC, event-driven |
| Azure Container Apps | Standalone + Dynamic Sessions (Hyper-V) | Native (`transport: auto`) | No hard cap | No hard cap | Regulated enterprise, code-exec tools |
| GCP Cloud Run | Session affinity flag; state externalized | Native | **60min (3600s)** | No hard cap | Long-running single-call tools |
| Deno Deploy | Deno KV + event store | Via `MCP_JSON_RESPONSE=true` | Tier-dependent | 512 MB mem / 1 GB deploy | TypeScript-native, KV-backed |
| Koyeb / Northflank | Scale-to-zero stateless | Native; `sessionIdGenerator: undefined` | No hard cap | No hard cap | Scale-to-zero remote MCP |

**Headline picks.**

| Workload | Primary | Why | Backup |
|---|---|---|---|
| Personal CLI / hobby | Cloudflare Workers + McpAgent | Free DO tier (100K req/day), built-in OAuth, hibernation ≈ $0 idle | Deno Deploy |
| Team B2B internal | Cloudflare Workers or Fly Machines | Workers for stateless/light; Fly for stateful/container-heavy | Railway |
| Multi-tenant SaaS | Cloudflare Workers McpAgent | DO + SQLite + hibernation maps 1:1 to MCP session | Azure ACA |
| Marketplace / public | Smithery.ai container runtime | Purpose-built hosting + discovery + OAuth/configSchema | CF Workers + custom domain |
| Regulated enterprise | Azure ACA or CF Workers `jurisdiction: "fedramp"` | Entra ID + Hyper-V; CF has FedRAMP DOs | AWS Lambda in VPC |
| Python / ML GPU | Modal | Serverless GPU at $0.001/sec H100; native FastMCP example | Cloud Run GPU |
| Long-running (>5 min) | GCP Cloud Run | 60-minute HTTP timeout — the highest of any managed platform | Fly Machines (no enforced cap) |

---

### 29. Cross-cutting platform heuristics

- **Scale-to-zero + in-memory sessions = always broken.** Externalize state to Redis/KV/DO/Firestore, or set min-replica ≥ 1.
- **4.5 MB caps and 15-min timeouts are platform constants.** Design tools to fit the envelope or offload to signed URLs + polling. See `error-handling.md` for the polling-tool pattern.
- **Session state = per-session DO or external store.** Don't reach for "sticky load balancer" on Cloud Run / ACA / Fly if you also want autoscaling — affinity and HPA fight each other.
- **OAuth 2.1 is cheap on Cloudflare, expensive everywhere else.** `workers-oauth-provider` is the only first-party DCR-capable OAuth server bundled with the runtime. On Vercel/Lambda/Cloud Run, you wire Clerk/Auth0/Stytch/WorkOS by hand. Cross-link `auth-identity.md`.
- **Price by dominant axis.** GPU: Modal. Always-on stateful: Fly. Bursty stateless: Cloudflare/Vercel. Long single tool calls: Cloud Run. Regulated: ACA or CF FedRAMP.

---

## Cross-references

- `auth-identity.md` — OAuth 2.1, PKCE, DCR, RFC 9728 PRM, refresh-token rotation; the depth on auth-at-transport.
- `error-handling.md` — `isError: true` envelope shape, retry semantics, polling-tool pattern for long-running ops.
- `session-and-state.md` — session pooling, conversation compaction, success-call learning database.
- `caching-economics.md` — provider-side prompt caching (Claude 1h cache, OpenAI implicit cache, Gemini context cache).
- `../decision-trees/scaling.md` — when transport / platform choice triggers a scaling decision.
- `../decision-trees/production-readiness.md` — final pre-deploy checklist that includes transport + platform.
