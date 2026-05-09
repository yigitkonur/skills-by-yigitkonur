# Progressive discovery

How to expose only the tools the agent needs right now and reveal more on demand. The cross-surface principle — fewer well-designed entry points beat thirty narrow tools — lives in `../../common/agent-cognitive-load.md`. This file is the MCP-specific deep dive: meta-tools, semantic search, session-scoped visibility, four-stage disclosure, and graceful fallback for hidden tools.

---

## The "30 tools is too many" rule

Frontier models handle 20+ sequential tool calls; smaller and open-source models degrade after 5-7 — they forget earlier results, hallucinate parameters, or loop. The same applies to **tool list size**: every additional schema costs context, and beyond 20-30 tools the model spends more attention selecting than executing.

Token cost of static tool exposure (measured with Claude Sonnet 4):

| Tool count | Static schemas in prompt | Token cost |
|---|---|---|
| 40 | All schemas | 43,300 |
| 100 | All schemas | 128,900 |
| 200 | All schemas | 261,700 |
| 400 | All schemas | 405,100 |

Beyond ~200 tools, the static surface exceeds Claude's context window and tasks cannot complete at all.

The fix isn't fewer tools — sometimes you really do have 200 distinct operations. The fix is **deferring schema exposure** until the agent asks. The patterns below trade slightly more reasoning steps for radically smaller initial context. Source: speakeasy.com/blog/100x-token-reduction-dynamic-toolsets.

---

## Pattern 1 — meta-tools (list / describe / execute)

Replace static tool exposure with three meta-tools. The agent discovers what exists, fetches schemas only when needed, then dispatches.

```python
@tool
def list_tools(prefix: str = "/") -> list[str]:
    """List available tools matching a prefix.
    Example: list_tools('/hubspot/deals/') returns deal-related tools."""
    return tool_registry.list(prefix)

@tool
def describe_tools(tool_id: str) -> dict:
    """Get the full input schema for a specific tool.
    Call this before execute_tool to understand required parameters."""
    return tool_registry.get_schema(tool_id)

@tool
def execute_tool(tool_id: str, arguments: dict) -> dict:
    """Execute a tool by ID with the given arguments.
    Call describe_tools first to get the correct schema."""
    return tool_registry.execute(tool_id, arguments)
```

Token impact:

| Strategy | 40 tools | 100 tools | 200 tools | 400 tools |
|---|---|---|---|---|
| Static (all schemas in prompt) | 43,300 | 128,900 | 261,700 | 405,100 |
| Progressive (meta-tools) | 1,600 | 2,400 | 2,500 | 2,500 |

Initial context stays at ~1.5-2.5k tokens regardless of catalog size.

Critical design details:

- **Separate schema retrieval from discovery.** `list_tools` returns only names; `describe_tools` returns the full schema. This prevents sending 100 schemas when the model only needs one.
- **Use hierarchical prefixes** in tool IDs: `/hubspot/deals/create`, `/hubspot/contacts/search`. Makes `list_tools` queries precise.
- **Cache schemas in the agent's tail.** When the agent fetches `describe_tools(...)`, the schema lands in messages — after the cache breakpoint. The cached prefix doesn't grow. See `caching-economics.md` § Ship thin tool stubs.

The anti-pattern: loading all tool schemas statically into the prompt past 200 tools. Tasks cannot complete; the model loses argument-tracking accuracy.

---

## Pattern 2 — semantic search with embeddings

For very large tool catalogs, replace hierarchical navigation with a single `find_tools` meta-tool that uses embedding similarity to retrieve relevant tools from a natural-language query.

```python
from sentence_transformers import SentenceTransformer
import faiss

class SemanticToolRouter:
    def __init__(self, tools):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.tools = tools
        texts = [f"{t.name}: {t.description}" for t in tools]
        embeddings = self.model.encode(texts)
        self.index = faiss.IndexFlatIP(embeddings.shape[1])
        self.index.add(embeddings)

    def search(self, query: str, top_k: int = 3) -> list:
        emb = self.model.encode([query])
        scores, idx = self.index.search(emb, top_k)
        return [self.tools[i] for i in idx[0]]

@tool
def find_tools(query: str) -> list[dict]:
    """Find tools matching a natural language intent.
    Example: find_tools('list recent HubSpot deals')"""
    matches = router.search(query, top_k=5)
    return [{"id": t.id, "name": t.name, "description": t.description} for t in matches]
```

When to choose semantic over hierarchical:

| Approach | Strengths | Cost |
|---|---|---|
| Semantic search | Faster for simple, single-intent queries; good when the user's wording is unpredictable | ~1.3k initial + ~3k per task; embedding maintenance |
| Progressive (Pattern 1) | Better for complex multi-step workflows where the agent needs full visibility | ~2.5k initial + ~2.5k per task |

Implementation notes:

- Pre-compute embeddings offline; only query the index at runtime.
- Cache recent query-to-tool mappings for 5-10 minutes.
- Store embeddings in FAISS (in-memory) or Pinecone (distributed).
- Keep full JSON schemas in a separate KV store, not in the embedding index.

Source: speakeasy.com (above); klavis.ai/blog/less-is-more-mcp-design-patterns-for-ai-agents.

---

## Pattern 3 — session-scoped tool unlocking (FastMCP visibility)

Hide sensitive or advanced tools by default and reveal them only after authentication or a prerequisite action. This solves three problems simultaneously: security (destructive tools aren't visible until authenticated), context efficiency (initial tool list stays small), and progressive complexity.

```python
from fastmcp import FastMCP, Context
from fastmcp.server.auth import require_scopes

mcp = FastMCP("Enterprise Server")

# Mount admin tools from a directory and disable by default
admin_provider = FileSystemProvider("./admin_tools")
mcp.mount(admin_provider)
mcp.disable(tags={"admin"})

@mcp.tool(auth=require_scopes("super-user"))
async def unlock_admin_mode(ctx: Context) -> str:
    """Authenticate and unlock administrative tools for this session.
    Requires super-user OAuth scope."""
    await ctx.enable_components(tags={"admin"})
    return "Admin mode unlocked. New tools available: delete_*, drop_*, force_*."
```

Layer priority: global transforms → session transforms → tool-level annotations. Later layers override earlier ones — a session transform can re-enable a tool that a global transform hid.

Without session-scoped visibility, the server must re-register tools (which nukes the prompt cache) or maintain separate server instances per user tier.

Disable by name when the tag system is overkill:

```python
mcp.disable(names={"dangerous_tool", "debug_tool"})
```

Dynamic unlock with role check:

```python
@mcp.tool(tags=["core"])
async def enable_advanced_mode(ctx: Context, role: str) -> str:
    """Unlock advanced tools based on role."""
    if role == "admin":
        await ctx.enable_components(tags={"advanced"})
        return "Admin tools unlocked."
    return "No additional tools available for this role."
```

Source: gofastmcp.com/servers/visibility; jlowin.dev/blog/fastmcp-3.

---

## Four-stage progressive disclosure

Stage-wise tool exposure mirrors how a human explores an unfamiliar system. Each stage returns minimal data, keeping token consumption low until the agent truly needs the full definition.

Interaction flow:

```
1. discover_categories()
   → ["GitHub", "Slack", "Database", "CRM"]

2. get_category_actions("GitHub")
   → [{"name": "create_pr", "summary": "Create a pull request"},
      {"name": "search_repos", "summary": "Search repositories"},
      {"name": "list_issues", "summary": "List issues with filters"}]

3. get_action_details("GitHub", "create_pr")
   → Full JSON schema with all parameters, types, descriptions

4. execute_action("GitHub", "create_pr", {"repo": "...", "title": "...", "body": "..."})
   → Result
```

Implementation:

```python
def handle_discovery(stage: str, **kwargs):
    if stage == "categories":
        return {"stage": "categories", "options": list_available_services()}
    if stage == "actions":
        service = kwargs["service"]
        return {"stage": "actions", "service": service, "options": list_actions(service)}
    if stage == "schema":
        return {"stage": "schema", "schema": get_action_schema(kwargs["service"], kwargs["action"])}
    raise ValueError(f"Unknown stage: {stage}")
```

Token budget per stage:

- Stage 1 (`categories`): ~100 tokens
- Stage 2 (`actions`): ~300-500 tokens (action names + summaries)
- Stage 3 (`schema`): ~500-2000 tokens (full schema for one action)
- Stage 4 (`execute`): variable (execution result)

vs. loading everything upfront: initial context stays at ~2% of the context window regardless of how many integrations you support.

Best for multi-tenant SaaS where each tenant enables different integrations. The agent discovers what's available for *this* user, not all possible tools.

---

## Tool-list-changed notifications

When the server adds, removes, or modifies tools at runtime, emit `notifications/tools/list_changed`. This is the official MCP protocol mechanism for dynamic tooling. The client receives the notification, re-fetches `tools/list`, and sees the updated set. Without it, clients use stale definitions — calling removed tools or missing new ones.

The TypeScript SDK's `RegisteredTool` triggers `sendToolListChanged()` automatically:

```typescript
const tool = server.registerTool("query_db", {
  description: "Run a read-only SQL query",
  inputSchema: { query: z.string() },
}, async ({ query }) => {
  return { content: [{ type: "text", text: await db.query(query) }] };
});

// Each triggers notifications/tools/list_changed automatically:
tool.disable();
tool.enable();
tool.update({ description: "Read-only SQL (max 1000 rows)" });
tool.remove();
```

Manual notification:

```typescript
await server.notification({
  method: "notifications/tools/list_changed",
});
```

**Critical timing.** Tool-list changes invalidate the prefix cache (see `caching-economics.md` § Never renegotiate the tool list mid-session). Send these notifications **at session boundaries** — after explicit `init_mode` calls, between workflow phases, never on every request. A rule of thumb: if the change frequency exceeds 1 per ~20 requests, the dynamic strategy is hurting more than helping. Source: anthropic prompt caching docs; openai function-calling guide.

---

## Graceful fallback for hidden tools

When a tool is hidden via session-scoped visibility, a stateful LLM may still "remember" it from earlier in the conversation and try to call it. Handle this gracefully rather than returning a generic not-found error.

```typescript
const allTools = new Map<string, ToolDefinition>();
const visibleTools = new Set<string>();

server.setToolNotFoundHandler(async (toolName: string, params: unknown) => {
  if (allTools.has(toolName)) {
    // Tool exists but is hidden — explain and offer the unlock path
    const tool = allTools.get(toolName)!;
    return {
      content: [{
        type: "text",
        text: JSON.stringify({
          error: "TOOL_NOT_CURRENTLY_VISIBLE",
          tool_name: toolName,
          message: `"${toolName}" exists but is not active in your current session mode.`,
          how_to_unlock: tool.unlockVia
            ? `Call ${tool.unlockVia} first to activate this tool.`
            : "Contact your administrator to enable this capability.",
          current_alternatives: visibleTools.has("search_tools")
            ? [`Call search_tools to discover available alternatives to ${toolName}.`]
            : [],
        }),
      }],
      isError: true,
    };
  }
  // Truly unknown tool
  return {
    content: [{ type: "text", text: `Unknown tool: "${toolName}". Call list_tools to see available tools.` }],
    isError: true,
  };
});
```

Without this, a model that remembers a hidden tool retries it repeatedly, wasting context on uninformative errors. The `TOOL_NOT_CURRENTLY_VISIBLE` envelope guides recovery in one round-trip.

On-demand restoration:

```typescript
server.tool("restore_tool", "Restore a temporarily hidden tool for this session", {
  tool_name: z.string(),
  reason: z.string().describe("Why this tool is needed now"),
}, async ({ tool_name, reason }) => {
  if (!allTools.has(tool_name)) {
    return { content: [{ type: "text", text: `"${tool_name}" does not exist.` }], isError: true };
  }
  visibleTools.add(tool_name);
  await server.notifyToolsChanged();
  return { content: [{ type: "text", text: `"${tool_name}" restored for this session.` }] };
});
```

---

## When to use which pattern

| Catalog size | Workflow shape | Pattern |
|---|---|---|
| ≤ 20 tools | Mixed | Static exposure — don't add machinery |
| 20-50 tools, hierarchical | Multi-step workflows | Meta-tools (`list_tools` / `describe_tools` / `execute_tool`) |
| 50-200 tools, mostly intent-based | Single-step queries | Semantic search (`find_tools`) |
| 5-20 always-on + a long tail | Auth-gated escalation | Session-scoped visibility (FastMCP transforms) |
| Multi-tenant integrations | Each tenant enables different services | Four-stage progressive disclosure |
| Live, mutable tool registry | Tools come and go | `notifications/tools/list_changed` + graceful fallback |

The patterns compose. A real production server might use semantic search for the long tail, session-scoped visibility for admin tools, and progressive disclosure for tenant-enabled integrations — all at once.

---

## Cross-references

- `tools.md` — the underlying tool design; descriptions, response shapes, the `execute_code` sandbox
- `caching-economics.md` — why dynamic tool lists invalidate the prompt cache and how thin stubs avoid it
- `agentic-patterns.md` — the planner-tool pattern and HATEOAS responses that pair with progressive discovery
- `../decision-trees/tool-count.md` — the diagnostic flow: when to consolidate vs. progressive-disclose vs. split
- `../../common/agent-cognitive-load.md` — universal principles: token budgets, fewer-but-better tools
- `client-compatibility.md` — which clients honor `notifications/tools/list_changed`
