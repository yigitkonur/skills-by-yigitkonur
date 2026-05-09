# Session and state

State is the easiest thing to get wrong in an MCP server. Global variables leak between sessions; in-memory state breaks under scale-to-zero deploys; sticky load balancers fight horizontal scaling; long-running tools time out and the agent gives up. The default is **stateless tools**; opt into stateful only when the workload actually demands it. Cross-link `transport-and-ops.md` for hosting-platform constraints, `agentic-patterns.md` for stage-gated workflows that lean on session state, and `../../common/iterative-loops.md` for the cross-surface state-token concept.

The headline rule: **stateless tools by default; opt-in to stateful via explicit session scoping or a state token returned to the client.**

---

## Stateless first — the default

A stateless tool reads input, computes a result, returns it. No `sessions[id] = ...`. No module-level globals. No reliance on prior calls. Restart the process between calls and nothing breaks. Stateless is what scales — horizontal pods, scale-to-zero, ephemeral session-per-request as HubSpot ships ([HubSpot remote MCP architecture, 2025-06-18](https://product.hubspot.com/blog/unlocking-deep-research-crm-connector-for-chatgpt)).

Most tools should be stateless. Search, fetch, lookup, create, update, delete by ID — none of these need session state. The state lives in the upstream system; the MCP is a thin translator.

```python
# Stateless: every input goes in, every result comes out, no hidden context.
@mcp.tool(description="Look up a customer by id.")
def get_customer(customer_id: str) -> dict:
    return crm.get_customer(customer_id) or {"error": f"customer {customer_id} not found"}
```

When you reach for "I need to remember something between calls," ask: can the caller pass it back as a parameter? That's the state-token pattern (below). Server-resident state is a last resort.

---

## Session lifecycle — what's actually happening

The MCP session has a fixed shape:

1. **Connect.** Client opens stdio pipe or Streamable HTTP connection.
2. **Initialize.** Client sends `initialize` request with its capabilities; server replies with its capabilities and `instructions` field. Both sides know what features are available.
3. **`initialized` notification.** Client signals it's ready.
4. **`tools/list`** (and `resources/list`, `prompts/list` if used). Client fetches the surface.
5. **Tool calls.** `tools/call` with name + arguments; server returns content + optional `structuredContent` + optional `isError`.
6. **Notifications.** Server can push `tools/list_changed`, `resources/updated`, `progress`. Client may ignore some — see `client-compatibility.md`.
7. **Disconnect.** Client closes the connection.

Where does state live across this? Three layers, in order of preference:

| Layer | Lifetime | Storage | When |
|---|---|---|---|
| **Per-call** | One tool invocation | Function-local | Default. Stateless. |
| **Per-session** | One client connection | In-memory dict keyed by `session_id`, or external store | When `tools/call` N depends on call N-1 within the same session |
| **Per-user across sessions** | The user's account | Database | When state must survive disconnect/reconnect |
| **Shared across users** | The whole tenant | Database with strict ACL | Rare; treat as risky — easy to leak data |

**Cleanup matters.** Per-session state needs TTLs or explicit cleanup on disconnect — leaked sessions become memory leaks. Subscribe to disconnect events on stdio (process exit) or HTTP (connection close, session timeout) and free the slot.

---

## Per-session state — the right way

When a tool legitimately needs to remember context inside one session (pagination cursors, current working directory, accumulated query filters), key it on the session ID. Never use module-level globals — they cross-contaminate when multiple clients connect.

```python
from collections import defaultdict
from fastmcp import Context, FastMCP

mcp = FastMCP("paginated")
session_state: dict[str, dict] = defaultdict(dict)

@mcp.tool(description="Advance one page through the current result set.")
def next_page(ctx: Context) -> dict:
    sid = ctx.session_id
    page = session_state[sid].get("page", 0) + 1
    session_state[sid]["page"] = page
    return fetch_page(page)

@mcp.tool(description="Reset pagination to page 1.")
def reset_pagination(ctx: Context) -> dict:
    sid = ctx.session_id
    session_state[sid].pop("page", None)
    return {"status": "Pagination reset for this session."}
```

For multi-process or multi-pod deployments, externalize:

```typescript
// Externalize session state so any pod can serve any request.
import Redis from "ioredis";
const redis = new Redis(process.env.REDIS_URL!);

server.tool("next_page", "Advance one page.", { /* ... */ }, async (_, ctx) => {
  const key = `session:${ctx.sessionId}`;
  const raw = await redis.get(key);
  const state = raw ? JSON.parse(raw) : { page: 0 };
  state.page += 1;
  await redis.set(key, JSON.stringify(state), "EX", 3600);
  return { content: [{ type: "text", text: JSON.stringify(await fetchPage(state.page)) }] };
});
```

Externalize once you cross any of: multi-pod horizontal scaling, scale-to-zero hosting (Cloudflare Workers without Durable Objects, Vercel Fluid Compute, Lambda), or HPA-managed autoscaling. Sticky session affinity fights the autoscaler — externalized state lets every pod serve every request.

---

## State storage — which layer fits

| Data | Store | TTL | Notes |
|---|---|---|---|
| Pagination cursor, current filter | In-memory dict on `session_id` | Session | Cheap, scoped, simple. Externalize when scaling out. |
| Active workflow stage (see `agentic-patterns.md`) | Redis on `session_id` | Session + 5 min slack | Resumable across reconnects within slack window |
| User preferences set this session | Redis on `user_id` | 1 hour | Survives reconnect |
| Recently-viewed records | Redis on `user_id` | 24 hours | Cache; invalidate on writes |
| User's permission scopes | Database, refreshed each session | Per session | Re-derive on connect; never cache long-term |
| Tenant-wide configuration | Database | Permanent | Read at boot, watch for changes |

Redis is the default external store for session-scoped state — fast, TTL-native, easy to provision. Postgres or another durable store for anything that must survive infra restarts. Cloudflare Durable Objects for per-session SQLite + hibernation (cross-link `transport-and-ops.md` § "Cloudflare Workers + McpAgent").

Hard rules:

- **Never store secrets, tokens, or PII in MCP session state.** Treat the MCP as adversarial-input-prone — session state should not become a leak vector.
- **TTL everything.** A session that times out without a TTL becomes a permanent memory leak.
- **Never share state across users without an ACL.** "We share a workspace" is not an ACL — ensure the read+write keys include the user ID.
- **Don't log raw session payloads.** Strip PII before structured logging.

---

## The state-token pattern — opaque token, server reconstructs

The cleanest stateful pattern: the server returns an opaque token, the client passes it back, the server reconstructs the context. Cross-link `../../common/iterative-loops.md` — this is the cross-surface state-token concept; the MCP-specific shape lives below.

The server does NOT have to keep session state for this; the token can carry the state itself, signed and encrypted. Or the server can keep state and the token is just a key into it. Either works — the agent sees the same opaque blob.

### Variant A — token carries the state (signed, encrypted, no server state)

```typescript
import { sign, verify } from "jsonwebtoken";
const SECRET = process.env.STATE_SECRET!;

// Tool 1 returns a token bearing accumulated state.
server.tool("search_invoices", "Search invoices.", {
  customer_id: z.string(),
  filters: z.record(z.unknown()).optional(),
  state_token: z.string().optional(),
}, async ({ customer_id, filters, state_token }) => {
  const prior = state_token ? verify(state_token, SECRET) as Record<string, unknown> : {};
  const merged = { ...prior, customer_id, filters: { ...(prior.filters as object || {}), ...filters } };
  const results = await searchInvoices(merged);
  const next_token = sign(merged, SECRET, { expiresIn: "1h" });
  return {
    content: [{ type: "text", text: JSON.stringify({ results, state_token: next_token }) }],
    structuredContent: { results, state_token: next_token },
  };
});
```

Token in, refined token out. The agent treats it as opaque — never inspects, never modifies. Works across stateless deploys (Lambda, Cloudflare without DO, Vercel) because every call carries everything it needs.

Trade-off: tokens grow linearly with accumulated context. Cap the size; reset state when the token exceeds ~2KB.

### Variant B — token is a key into server-side state

```typescript
import { randomUUID } from "crypto";
const sessionStore = new Map<string, Session>();   // or Redis

server.tool("start_workflow", "Begin a new workflow.", {
  goal: z.string(),
}, async ({ goal }) => {
  const token = randomUUID();
  sessionStore.set(token, { goal, stage: "initialized", started_at: Date.now() });
  return { content: [{ type: "text", text: JSON.stringify({ workflow_token: token, stage: "initialized" }) }] };
});

server.tool("advance_workflow", "Advance the workflow.", {
  workflow_token: z.string(),
  payload: z.record(z.unknown()).optional(),
}, async ({ workflow_token, payload }) => {
  const session = sessionStore.get(workflow_token);
  if (!session) {
    return { content: [{ type: "text", text: "Workflow token unknown or expired. Call start_workflow." }], isError: true };
  }
  session.stage = nextStage(session.stage);
  return { content: [{ type: "text", text: JSON.stringify({ workflow_token, stage: session.stage }) }] };
});
```

Trade-off: needs a store with shared state across pods. Cleaner when the state is large or contains data the agent shouldn't see.

### When to pick which

- **Variant A (signed token)** when state is small (<2KB), the deploy is stateless or scale-to-zero, and you want zero infra.
- **Variant B (server-side state)** when state is large, contains internal data the agent shouldn't see, or needs server-side mutation events (other agents / users updating the same workflow).

Cross-link `agentic-patterns.md` § "Server-enforced workflow stages" — the stage-gate pattern uses Variant B with the workflow stage as the keyed state.

---

## Long-running operations — task IDs

When a tool will take more than ~30–60 seconds, return a task ID immediately and let the agent poll. Default tool-call timeouts vary by client (Claude Desktop ~60s; Cursor ~60s; SDKs default 30s). Anything longer needs the polling pattern.

```python
from fastmcp import FastMCP
from fastmcp.server.tasks import TaskConfig

mcp = FastMCP("reports")

@mcp.tool(task=True)
async def generate_report(data_id: str) -> dict:
    """Generate a comprehensive report. Runs as a background task; returns a task_id immediately."""
    report = await build_report(data_id)
    return {"status": "completed", "report": report}
```

For platforms with hard timeouts (Lambda 15min, Vercel 800s on Pro Fluid), use SQS + webhook (cross-link `transport-and-ops.md` § "AWS Lambda + LWA"). The agent gets `{job_id, status: "queued", poll_tool: "get_report_status"}` and polls.

```typescript
server.tool("get_report_status", "Check on a previously enqueued report.", {
  job_id: z.string(),
}, async ({ job_id }) => {
  const job = await jobsTable.get(job_id);
  if (!job) return { content: [{ type: "text", text: `job_id ${job_id} unknown` }], isError: true };
  if (job.status === "queued" || job.status === "running") {
    return { content: [{ type: "text", text: JSON.stringify({
      status: job.status, progress: job.progress, retry_after_ms: 5000,
    })}] };
  }
  if (job.status === "failed") return { content: [{ type: "text", text: job.error }], isError: true };
  return { content: [{ type: "text", text: JSON.stringify({ status: "completed", result: job.result }) }] };
});
```

Cross-link `error-handling.md` for the polling-tool error envelope; cross-link `agentic-patterns.md` for the SERF taxonomy that gives the agent `retryable: true` semantics.

---

## Bad-vs-good session implementations

### Bad — global state shared across all sessions

```python
# Bad: race conditions, cross-session leakage.
current_page = 0
auth_token = None

@mcp.tool
def next_page():
    global current_page
    current_page += 1
    return fetch_page(current_page)
```

Two clients connect; one calls `next_page` three times; the other calls it once and gets page 5. State is leaking. Memory grows unbounded as sessions accumulate. There is no cleanup path.

### Good — per-session state with cleanup

```python
from collections import defaultdict

session_state: dict[str, dict] = defaultdict(dict)

@mcp.tool
def next_page(ctx: Context) -> dict:
    sid = ctx.session_id
    page = session_state[sid].get("page", 0) + 1
    session_state[sid]["page"] = page
    return fetch_page(page)

@mcp.on_disconnect
def cleanup(session_id: str) -> None:
    session_state.pop(session_id, None)
```

Per-session, scoped, cleaned. Two clients see independent pagination.

### Bad — stateful tool that breaks on horizontal scaling

```python
# Bad: works in dev (single process), breaks on Lambda / Cloud Run / scale-to-zero.
workflow_state: dict[str, str] = {}  # in-memory only

@mcp.tool
def advance(workflow_id: str) -> dict:
    workflow_state[workflow_id] = next_stage(workflow_state.get(workflow_id, "init"))
    return {"stage": workflow_state[workflow_id]}
```

When `advance` lands on a different pod than `start`, the second pod's `workflow_state` is empty.

### Good — externalized state via Redis or signed token

```python
import redis, json
r = redis.Redis(decode_responses=True)

@mcp.tool
def advance(workflow_id: str) -> dict:
    raw = r.get(f"workflow:{workflow_id}") or '{"stage":"init"}'
    state = json.loads(raw)
    state["stage"] = next_stage(state["stage"])
    r.set(f"workflow:{workflow_id}", json.dumps(state), ex=3600)
    return {"stage": state["stage"]}
```

Any pod can serve any call. Cleanup via TTL.

### Bad — long tool blocks the conversation

```python
# Bad: 5-minute report generation blocks the agent's whole loop.
@mcp.tool
def generate_huge_report(data_id: str) -> dict:
    time.sleep(300)
    return {"report": "..."}
```

The agent times out (most clients ~60s), retries, fails, gives up. The user sees nothing.

### Good — task pattern with poll-back

```python
@mcp.tool(task=True)
async def generate_huge_report(data_id: str) -> dict:
    return {"report": await build_report_async(data_id)}

@mcp.tool
def get_report_status(job_id: str) -> dict:
    job = task_store.get(job_id)
    return {"status": job.status, "progress": job.progress, "result": job.result if job.status == "completed" else None}
```

Agent enqueues, polls, completes. Conversation stays alive.

---

## Session pooling for throughput

Stacklok's Kubernetes benchmarks (cited in `transport-and-ops.md`) show a shared pool of 10 sessions delivers ~10× higher throughput than unique-session-per-request. The bottleneck is connection setup overhead — TLS handshake, protocol negotiation, state initialization. Pooling amortizes it.

```typescript
import { createPool } from "generic-pool";

const sessionPool = createPool({
  create: async () => {
    const session = await mcpClient.connect(serverUrl);
    await session.initialize();
    return session;
  },
  destroy: async (session) => session.close(),
}, { min: 2, max: 10, idleTimeoutMs: 60_000 });

async function callTool(name: string, args: Record<string, unknown>) {
  const session = await sessionPool.acquire();
  try { return await session.callTool({ name, arguments: args }); }
  finally { sessionPool.release(session); }
}
```

Externalize per-session state to Redis so any pooled connection can serve any request. Cross-link `transport-and-ops.md` § "Transport choice makes or breaks performance."

---

## Conversation compaction — when sessions go long

Long agent loops accumulate tool-call history until context overflows. Naive truncation drops important schema context. Use priority-aware compaction:

| Priority | What | Policy |
|---|---|---|
| Anchor | Schema definitions, system prompt | Always keep |
| Important | Substantial tool results, user-supplied data | Keep |
| Contextual | Useful background, prior tool descriptions | Summarize when context filling |
| Routine | Ordinary dialogue, confirmations | Drop second |
| Transient | "ok", acks, status pings | Drop first |

Compact bottom-up: drop Transient, then Routine, then summarize Contextual. Anchor and Important survive until the session ends. Cache compacted summaries by content hash so re-running the same conversation reuses the summary.

```typescript
async function getCompactedContext(messages: Message[]): Promise<string> {
  const hash = createHash("sha256").update(messages.map((m) => m.content).join("|")).digest("hex");
  const cached = await redis.get(`compaction:${hash}`);
  if (cached) return cached;
  const compacted = await summarize(messages);
  await redis.setex(`compaction:${hash}`, 3600, compacted);
  return compacted;
}
```

Cross-link `model-behavior.md` Pattern 9 for the ~50K-input-token threshold (Chroma 2025 "Context Rot" study).

---

## Cross-references

- `transport-and-ops.md` — hosting platform constraints (Cloudflare DO, Vercel Fluid, Lambda 15-min, Cloud Run 60-min); when scale-to-zero forces externalized state.
- `agentic-patterns.md` — server-enforced workflow stages, parameter dependency chains; the stage-gate pattern that lives on session state.
- `auth-identity.md` — token rotation across reconnects; OAuth 2.1 + refresh tokens.
- `error-handling.md` — task-status polling envelope and `retryable` semantics.
- `caching-economics.md` — when to cache tool results vs session state.
- `../../common/iterative-loops.md` — the cross-surface state-token concept (CLI iterative + MCP session); this file is the MCP-specific shape.
- `../decision-trees/scaling.md` — when transport / platform choice forces externalized state.
