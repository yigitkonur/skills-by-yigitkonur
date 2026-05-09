# Session and State

Patterns for managing state across MCP sessions: learning from successful calls, handling long-running operations, scoping state correctly, scaling throughput with session pooling, and compacting conversations to preserve context window budget.

---

## 1. Log Successful Tool Calls to Build a Learning Database

When your MCP server handles a complex API, record every successful tool call and its parameters. When future calls fail, query this database for a working example to include in the error response.

```python
import json
from pathlib import Path

SUCCESS_LOG = Path("./successful_calls.jsonl")

@tool
def query_api(endpoint: str, params: dict) -> dict:
    try:
        result = api.call(endpoint, params)
        # Log the successful call
        SUCCESS_LOG.open("a").write(json.dumps({
            "endpoint": endpoint,
            "params": params,
            "timestamp": datetime.now().isoformat()
        }) + "\n")
        return result
    except APIError as e:
        # Find a similar successful call
        similar = find_similar_successful_call(endpoint, params)
        error_msg = f"API call failed: {e}"
        if similar:
            error_msg += (
                f"\n\nA similar successful call used these parameters:\n"
                f"{json.dumps(similar['params'], indent=2)}\n"
                f"Try adjusting your parameters to match this pattern."
            )
        return {"content": [{"type": "text", "text": error_msg}], "isError": True}
```

**The insight:** One practitioner reported this reduced API call errors by more than 50%. The model learns from its own (or other sessions') successful patterns.

**Implementation details:**
- Store in a simple JSONL file or SQLite database
- Index by endpoint and key parameter patterns
- Include timestamps to weight recent successes higher
- Consider embedding-based similarity for fuzzy matching

**Privacy note:** Be careful about logging sensitive parameters. Strip PII before storing.

**Source:** [u/Simple-Art-2338 on r/mcp](https://reddit.com/r/mcp/comments/1npfoo9/) -- "reduced my error more than 50%"

---

## 2. Return Task IDs for Long-Running Operations

When a tool call will take more than a few seconds, return a task ID immediately and let the model poll for results. This prevents blocking the conversation and avoids timeouts.

```python
from fastmcp import FastMCP
from fastmcp.server.tasks import TaskConfig

mcp = FastMCP("Report Server")

@mcp.tool(task=True)  # Decorator-based API -- runs as a background task
async def generate_report(data_id: str) -> dict:
    """Generate a comprehensive data report.
    Runs as a background task -- returns a task ID immediately.
    Use the task status endpoint to poll for completion."""
    # Long-running work happens here; FastMCP handles the task lifecycle
    report = await build_report(data_id)
    return {
        "status": "completed",
        "result": report,
        "message": f"Report for '{data_id}' is ready."
    }

# For more control, use TaskConfig:
# @mcp.tool(task=TaskConfig(mode="required"))
# async def heavy_analysis(data_id: str) -> dict: ...
```

**Why this matters:**
- Default tool call timeouts are typically 30-60 seconds
- Long-running operations block the conversation
- The model can do other work while waiting
- Progress updates keep the user informed

**Implementation options:**
- FastMCP's `@mcp.tool(task=True)` decorator or `@mcp.tool(task=TaskConfig(mode="required"))` for fine-grained control
- Simple async queue with Redis/SQLite backing
- Thread pool for CPU-bound work

**Source:** [FastMCP tasks docs](https://gofastmcp.com/servers/tasks); [FastMCP 3.0 -- What's New](https://www.jlowin.dev/blog/fastmcp-3-whats-new)

---

## 3. Scope State to Session, Not Global Variables

When your MCP server needs to maintain state (auth tokens, pagination cursors, user preferences), always scope it to the session identifier. Never use module-level globals.

**Bad -- global state shared across all sessions:**

```python
# Global state - shared across all sessions
current_page = 0
auth_token = None

@tool
def next_page():
    global current_page
    current_page += 1  # Race condition when multiple sessions are active
    return fetch_page(current_page)
```

**Good -- session-scoped state:**

```python
from collections import defaultdict

session_state = defaultdict(dict)

@tool
def next_page(ctx: Context):
    sid = ctx.session_id
    page = session_state[sid].get("page", 0) + 1
    session_state[sid]["page"] = page
    return fetch_page(page)

@tool
def set_preferences(ctx: Context, timezone: str, language: str):
    session_state[ctx.session_id]["prefs"] = {
        "timezone": timezone,
        "language": language
    }
    return {"status": "Preferences saved for this session."}
```

**State management guidelines:**
- **Short-lived state** (pagination, current context): In-memory dict keyed by session ID
- **Medium-lived state** (user prefs, cached results): Redis with TTL
- **Long-lived state** (user quotas, history): Database

**Clean up:** Set TTLs or implement session cleanup to prevent memory leaks. Treat session state like API state: create on first use, clear when done, never leak between users.

**Source:** [NearForm -- Implementing MCP](https://nearform.com/digital-community/implementing-model-context-protocol-mcp-tips-tricks-and-pitfalls/); [FastMCP state docs](https://gofastmcp.com)

---

## 4. Session Pooling for 10x Throughput

A shared pool of 10 sessions delivers ~10x higher throughput vs unique-session-per-request. Benchmarks from Stacklok's Kubernetes testing:

| Configuration | Req/s | Avg Response |
|---|---|---|
| Unique sessions | 30-36 | 500ms+ |
| Shared pool (10) | 290-300 | 5ms |
| stdio (single) | 0.64 | 20s |

The bottleneck is connection setup overhead -- TLS handshake, protocol negotiation, state initialization. Pooling amortizes this.

**Implementation:**

```typescript
import { createPool } from "generic-pool";

const sessionPool = createPool({
  create: async () => {
    const session = await mcpClient.connect(serverUrl);
    await session.initialize();
    return session;
  },
  destroy: async (session) => await session.close(),
}, { min: 2, max: 10, idleTimeoutMs: 60_000 });

async function callTool(name: string, args: Record<string, unknown>) {
  const session = await sessionPool.acquire();
  try {
    return await session.callTool({ name, arguments: args });
  } finally {
    sessionPool.release(session);
  }
}
```

**Externalize session state so any pooled connection can serve any request:**

```typescript
await redis.setex(`session:${sid}`, 3600, JSON.stringify(state));
const state = JSON.parse(await redis.get(`session:${sid}`));
```

Pool connections, externalize state, let the pool handle lifecycle.

**Source:** [Stacklok -- Performance Testing MCP Servers in Kubernetes](https://dev.to/stacklok/performance-testing-mcp-servers-in-kubernetes-transport-choice-is-the-make-or-break-decision-for-1ffb)

---

## 5. Conversation Compaction Priorities

Long MCP sessions accumulate messages until they overflow the context window. Naive truncation (drop oldest) loses critical schema context. Use priority-aware compaction instead.

**Priority categories:**

| Priority | What It Is | Policy |
|---|---|---|
| Anchor | Schema definitions, structural | Always keep |
| Important | Substantial query results, data | Keep |
| Contextual | Useful background, explanations | Summarize if full |
| Routine | Ordinary dialogue, confirmations | May drop |
| Transient | Acks, "ok", status pings | Drop first |

Compact bottom-up: drop Transient, then Routine, then summarize Contextual. Anchor and Important survive until session ends.

**Cache compaction with content hash:**

```typescript
import { createHash } from "crypto";

async function getCompactedContext(messages: Message[]): Promise<string> {
  const hash = createHash("sha256")
    .update(messages.map(m => m.content).join("|"))
    .digest("hex");
  const cached = await redis.get(`compaction:${hash}`);
  if (cached) return cached; // O(1) reuse
  const compacted = await summarize(messages);
  await redis.setex(`compaction:${hash}`, 3600, compacted);
  return compacted;
}
```

**Classify at creation time:**

```typescript
function classifyMessage(msg: McpMessage): Priority {
  if (msg.type === "schema" || msg.type === "tool_definition") return "anchor";
  if (msg.type === "tool_result" && msg.content.length > 500)  return "important";
  if (msg.type === "tool_result")                              return "contextual";
  if (msg.role === "assistant" && msg.content.length < 20)     return "transient";
  return "routine";
}
```

Classify upfront, compact bottom-up, cache results for O(1) reuse.

**Source:** [pgEdge -- Lessons Learned Writing an MCP Server for PostgreSQL](https://www.pgedge.com/blog/lessons-learned-writing-an-mcp-server-for-postgresql)
