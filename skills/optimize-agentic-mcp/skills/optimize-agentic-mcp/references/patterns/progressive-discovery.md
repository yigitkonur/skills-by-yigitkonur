# Progressive Discovery Patterns

8 patterns for managing large tool catalogs, dynamic tool registration, and reducing context window pressure when your MCP server exposes 20+ tools.

---

## 1. Use Meta-Tools for Large Tool Catalogs (list/describe/execute)

When your MCP server has more than ~40 tools, loading all their schemas into the prompt becomes prohibitively expensive. Replace static tool exposure with three meta-tools that let the agent discover tools on demand.

**The three meta-tools:**
```python
@tool
def list_tools(prefix: str = "/") -> list[str]:
    """List available tool categories or tools matching a prefix.
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

**Token impact (measured with Claude Sonnet 4):**

| Strategy | 40 tools | 100 tools | 200 tools | 400 tools |
|----------|----------|-----------|-----------|-----------|
| Static (all schemas in prompt) | 43,300 tokens | 128,900 | 261,700 | 405,100 |
| Progressive (meta-tools) | 1,600 tokens | 2,400 | 2,500 | 2,500 |

**Critical design details:**
- **Separate schema retrieval from discovery.** `list_tools` returns only names; `describe_tools` returns the full schema. This prevents sending 100 schemas when the model only needs one.
- **Use hierarchical prefixes** in tool IDs: `/hubspot/deals/create`, `/hubspot/contacts/search`. This makes `list_tools` queries precise.
- The initial context contains only ~1.5-2.5k tokens regardless of total tool count.

**Anti-pattern:** Loading all tool schemas statically into the prompt. Beyond ~200 tools, this exceeds Claude's context window and tasks cannot complete at all.

**Source:** [Speakeasy — Comparing Progressive Discovery and Semantic Search](https://www.speakeasy.com/blog/100x-token-reduction-dynamic-toolsets)

---

## 2. Use Semantic Search with Embeddings for 100+ Tools

For very large tool catalogs, replace hierarchical navigation with a single `find_tools` meta-tool that uses embedding similarity to find relevant tools from a natural language query.

```python
from sentence_transformers import SentenceTransformer
import faiss

class SemanticToolRouter:
    def __init__(self, tools):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
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

**When to use semantic vs progressive:**
- **Semantic**: Faster for simple, single-intent queries. ~1.3k initial tokens + ~3k per task.
- **Progressive**: Better for complex multi-step workflows where the agent needs full visibility of available actions. ~2.5k initial + ~2.5k per task.

**Implementation tips:**
- Pre-compute embeddings offline; only query the index at runtime
- Cache recent query-to-tool mappings for 5-10 minutes
- Store embeddings in FAISS (in-memory) or Pinecone (distributed)
- Keep full JSON schemas in a separate KV store, not in the embedding index

**Source:** [Speakeasy — Comparing Progressive Discovery and Semantic Search](https://www.speakeasy.com/blog/100x-token-reduction-dynamic-toolsets); [Klavis AI — Less is More](https://www.klavis.ai/blog/less-is-more-mcp-design-patterns-for-ai-agents)

---

## 3. Session-Based Progressive Tool Unlocking

Hide sensitive or advanced tools by default and reveal them only after authorization or a prerequisite action within the session.

```python
from fastmcp import FastMCP, Context
from fastmcp.server.auth import require_scopes

mcp = FastMCP("Enterprise Server")

# 1. Mount admin tools from a directory
admin_provider = FileSystemProvider("./admin_tools")
mcp.mount(admin_provider)

# 2. Hide them by default
mcp.disable(tags={"admin"})

# 3. Gatekeeper tool that unlocks admin tools for this session
@mcp.tool(auth=require_scopes("super-user"))
async def unlock_admin_mode(ctx: Context):
    """Authenticate and unlock administrative tools for this session.
    Requires super-user OAuth scope."""
    await ctx.enable_components(tags={"admin"})
    return "Admin mode unlocked. The following tools are now available: [list of admin tools]"
```

**How it works:**
1. The agent sees only safe, read-only tools initially
2. When a task requires admin capabilities, the agent calls `unlock_admin_mode`
3. The server verifies authorization and reveals the admin tools for this session only
4. Other sessions remain unaffected

**This pattern solves multiple problems:**
- **Security**: Destructive tools aren't visible until explicitly authenticated
- **Context efficiency**: The agent's initial tool list stays small
- **Progressive complexity**: Users start simple and escalate when needed

**Implementation via FastMCP 3.0:**
- `Visibility Transforms` control which components are visible per session
- `AuthMiddleware` gates groups of components by tag
- Session state tracks what each user has unlocked
- The unlock tool's response should list what was just made available

**Source:** [FastMCP 3.0 blog](https://jlowin.dev/blog/fastmcp-3); [FastMCP visibility docs](https://gofastmcp.com/servers/visibility)

---

## 4. Four-Stage Progressive Disclosure Pattern

Stage-wise tool exposure mirrors how a human explores an unfamiliar system. Each stage returns minimal data, keeping token consumption low until the agent truly needs the full definition.

**Interaction flow:**
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

**Implementation:**
```python
def handle_discovery(stage, **kwargs):
    if stage == "categories":
        return {"stage": "categories", "options": list_available_services()}

    elif stage == "actions":
        service = kwargs["service"]
        return {"stage": "actions", "service": service,
                "options": list_actions(service)}

    elif stage == "schema":
        return {"stage": "schema",
                "schema": get_action_schema(kwargs["service"], kwargs["action"])}
```

**Token budget at each stage:**
- Stage 1: ~100 tokens (category list)
- Stage 2: ~300-500 tokens (action names + summaries)
- Stage 3: ~500-2000 tokens (full schema for one action)
- Stage 4: Variable (execution result)

**vs. loading everything upfront:** Initial context stays at ~2% of the context window regardless of how many integrations you support.

**Best for:** Multi-tenant SaaS where each tenant enables different integrations. The agent discovers what's available for THIS user, not all possible tools.

**Source:** [Klavis AI — Less is More](https://www.klavis.ai/blog/less-is-more-mcp-design-patterns-for-ai-agents); [Speakeasy progressive discovery benchmarks](https://www.speakeasy.com/blog/100x-token-reduction-dynamic-toolsets)

---

## 5. Dynamic Tool List Changes Nuke the KV/Prefix Cache

Changing the tool list dynamically invalidates the KV/prefix cache for both Anthropic and OpenAI. The system prompt -- which includes tool definitions -- is cached as a prefix. Every tool add/remove evicts the cache entry and forces recomputation. **Dynamic pruning can be slower than a static list** if you change tools too frequently.

**When to change tools -- only at clear session boundaries:**
- After an explicit `init_mode` or `set_context` call from the user
- When transitioning between workflow phases (e.g., "explore" to "edit")
- On initial connection setup

**Do not** change the tool list on every request or per-message heuristics.

**Rule of thumb:**
```
If tool_list_change_frequency > 1 per ~20 requests:
    you're probably hurting more than helping.
If tool_list is stable for the session:
    prefix cache stays warm → faster TTFT, lower cost.
```

```typescript
// Good: change tools once at session boundaries
server.onRequest("set_mode", (params) => {
  if (params.mode === "admin") enableAdminTools(); // one invalidation
});

// Bad: change tools on every request
server.onRequest("tools/call", (params) => {
  pruneIrrelevantTools(params.context); // cache miss every time
});
```

Static tool lists are cache-friendly. Batch mutations at session boundaries.

**Source:** [Anthropic prompt caching docs](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching); [OpenAI function calling guide](https://platform.openai.com/docs/guides/function-calling)

---

## 6. Use `notifications/tools/list_changed` for Dynamic Tooling

When your server adds, removes, or modifies tools at runtime, emit the `notifications/tools/list_changed` event. This is the **official MCP protocol mechanism** for dynamic tooling. The client receives the notification, re-fetches `tools/list`, and sees the updated set. Without it, clients use stale definitions -- calling removed tools or missing new ones.

**SDK Support -- `RegisteredTool`:**

The TypeScript SDK's `RegisteredTool` handles notifications automatically. Each mutation triggers `sendToolListChanged()` internally:

```typescript
const tool = server.registerTool("query_db", {
  description: "Run a read-only SQL query",
  inputSchema: { query: z.string() },
}, async ({ query }) => {
  return { content: [{ type: "text", text: await db.query(query) }] };
});

// Each triggers notifications/tools/list_changed automatically:
tool.disable();  // hides from tools/list
tool.enable();   // makes visible again
tool.update({ description: "Read-only SQL (max 1000 rows)" });
tool.remove();   // permanently removes
```

**Manual notification:**

```typescript
await server.notification({
  method: "notifications/tools/list_changed",
});
```

Use this **at session boundaries** (see Pattern 5) to avoid prefix cache thrashing. The notification is cheap -- the cache invalidation it triggers on the LLM side is not.

**Source:** [MCP specification — notifications/tools/list_changed](https://modelcontextprotocol.io/specification/2025-11-25/server/tools); [modelcontextprotocol/typescript-sdk](https://github.com/modelcontextprotocol/typescript-sdk)

---

## 7. FastMCP Visibility Transforms

FastMCP 3.0 introduced a layered visibility system that lets you show or hide tools at the session level without re-registering anything. This is the production-ready way to implement progressive tool disclosure in Python MCP servers.

**Disable by tag (apply to every session):**
```python
from fastmcp import FastMCP

mcp = FastMCP("my-server")

# Disable all tools tagged "advanced" by default
mcp.disable(tags={"advanced"})
```

**Per-session overrides (inside a tool handler):**
```python
from fastmcp import FastMCP, Context

@mcp.tool(tags=["core"])
async def unlock_admin_mode(ctx: Context, role: str) -> str:
    """Unlock tools based on user role."""
    if role == "admin":
        await ctx.enable_components(tags={"advanced"})
        return "Admin tools unlocked."
    return "No additional tools available for this role."
```

**Disable by name:**
```python
mcp.disable(names={"dangerous_tool", "debug_tool"})
```

**Dynamic unlock via context tool:**
```python
@mcp.tool(tags=["core"])
async def enable_advanced_mode(ctx: Context, access_code: str) -> str:
    """Unlock advanced tools for this session. Requires a valid access code."""
    if not verify_access_code(access_code):
        return "Invalid access code."

    await ctx.enable_components(tags=["advanced"])
    return "Advanced tools unlocked. Available: analyze_deep, export_bulk, admin_override."
```

**Layer priority:** Global transforms -> session transforms -> tool-level annotations. Later layers override earlier ones, so a session transform can re-enable a tool that a global transform hid.

Without session-scoped visibility, you must re-register tools (which nukes the prefix cache) or maintain separate server instances per user tier. FastMCP transforms let you do progressive disclosure cleanly.

**Source:** [FastMCP 3.0 docs — visibility](https://gofastmcp.com/servers/visibility); [FastMCP context docs](https://gofastmcp.com/python-sdk/fastmcp-server-context)

---

## 8. Graceful Fallback for Hidden Tools

When you hide a tool via progressive disclosure, a stateful LLM may still "remember" that tool from earlier in the conversation and attempt to call it. Handle this gracefully rather than returning a generic not-found error.

**Detection and recovery pattern:**

```typescript
// Registry of all tools (including currently hidden ones)
const allTools = new Map<string, ToolDefinition>();
const visibleTools = new Set<string>();

// Override the default "tool not found" behavior
server.setToolNotFoundHandler(async (toolName: string, params: unknown) => {
  if (allTools.has(toolName)) {
    // Tool exists but is hidden -- explain and offer the path to unlock it
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
        })
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

**On-demand restoration:**

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

Without graceful fallback, a model that remembers a hidden tool will retry it repeatedly, wasting context on uninformative error messages. The `TOOL_NOT_CURRENTLY_VISIBLE` response guides recovery.

**Source:** Recommended pattern for progressive disclosure; community discussions on [r/mcp](https://reddit.com/r/mcp)
