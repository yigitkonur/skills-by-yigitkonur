# Tools — Design, Descriptions, Responses

The single largest leverage point in an MCP server is the tool itself. Three things determine whether the model picks it, fills it correctly, and recovers when something goes wrong: how you scope the tool, how you describe it, and what you return. This file consolidates all three. Read alongside `schema-design.md` for input schemas, `error-handling.md` for the error response shape, and `progressive-discovery.md` for hiding tools the agent does not yet need.

---

## Tool design

### Design around user intent, not API endpoints

The most common anti-pattern is wrapping each REST endpoint as its own tool. That forces the model to orchestrate multi-step workflows a developer would have automated.

API-centric (bad):

```
get_members()          → list of member IDs
get_member_activity()  → activity for one member
get_member_posts()     → posts for one member
get_member_comments()  → comments for one member
```

The model calls `get_members`, then loops through results calling three tools per member. 20+ tool calls, blown context budget, error-prone.

Intent-centric (good):

```python
@tool(description="Get activity insights for all members in a space. Returns members sorted by engagement with their posts, comments, and last active date.")
def get_space_activity(space_id: str, days: int = 30, sort_by: str = "total_activity") -> dict:
    members = api.get_members(space_id)
    for m in members:
        m.activity = api.get_activity(m.id, days=days)
        m.posts = api.get_posts(m.id, days=days)
    return {
        "members": sorted(members, key=lambda m: m.activity.total, reverse=True),
        "summary": f"Found {len(members)} members active in the last {days} days.",
        "next_steps": "Use bulk_message(member_ids=[...]) to contact specific members.",
    }
```

One tool call, server-side orchestration, agent-friendly summary. The server knows the API better than the model ever will — let the server orchestrate.

**Consolidate when:** three or more API calls always happen together for a common use case. They belong in one tool.

### The intent verb test

Pick the verb you'd say out loud when reaching for the tool. `search_customers`, `create_invoice`, `deploy_project`. If the natural verb is not in the name, rename. The verb carries disproportionate weight in selection.

### Be a smart database, not a smart analyst

Your server should provide rich, structured data and let the LLM do the analysis. Don't use brittle keyword matching or opaque server-side scoring.

Wrong mental model — "smart analyst":

```python
def analyze_threats(description: str):
    threats = []
    if "payment" in description:
        threats.append("Payment fraud")
    if "user" in description:
        threats.append("Identity spoofing")
    return {"threats": threats[:5]}
```

Right mental model — "smart database":

```python
def get_threat_framework(app_description: str):
    return {
        "stride_categories": {
            "spoofing": {
                "description": "Identity spoofing attacks",
                "traditional_threats": ["User impersonation", "Credential theft"],
                "ai_ml_threats": ["Deepfake attacks", "Prompt injection"],
                "mitigation_patterns": ["MFA", "Certificate-based auth"],
                "indicators": ["login", "auth", "session", "token"],
            },
            # ... all categories with COMPLETE data
        },
        "context_analysis": analyze_app_context(app_description),
        "report_template": "Use the above framework data to generate a threat report.",
    }
```

The LLM is better at semantic analysis than your keyword matcher. Your server is better at data retrieval and structured output than the LLM. Play to each side's strengths.

**Bounded exception:** read-only research workflows can use a small server-side planner turn (see `agentic-patterns.md` Pattern 7). Keep it explicit, bounded, and observable. Never hide destructive actions behind opaque scoring.

### Consolidate multi-step workflows into single atomic tools

When a common task requires four-plus API calls in sequence, wrap the whole workflow into one tool.

Before — four separate tools:

```python
create_project(name, repo)       # Tool 1
add_env_vars(pid, vars)          # Tool 2
create_deployment(pid, branch)   # Tool 3
add_domain(pid, domain)          # Tool 4
```

After — one workflow tool:

```python
@tool(description="Deploy a new project end-to-end. Creates the project, configures env vars, deploys from the specified branch, and sets up a custom domain.")
def deploy_project(repo_url: str, domain: str, env_vars: dict, branch: str = "main") -> dict:
    pid = create_project(repo_url)
    add_env_vars(pid, env_vars)
    deployment = create_deployment(pid, branch)
    add_domain(pid, domain)
    return {
        "status": "success",
        "project_id": pid,
        "deployment_url": deployment.url,
        "domain": domain,
        "message": f"Project deployed to {domain} from {branch} branch.",
    }
```

3-4× fewer tool descriptions, fewer failure points, simpler agent reasoning, conversational responses instead of raw status codes.

**Don't consolidate when:** steps are genuinely independent (user might want env vars without deployment), individual steps need human confirmation, or the workflow varies significantly by use case.

### Use a planner tool to teach the workflow

For servers with multiple tools that must be called in sequence, expose an explicit planner tool that returns the workflow as structured guidance.

```python
@tool(description="Get the recommended workflow plan for the current task. Call this FIRST before using any other tools.")
def create_plan(task_description: str) -> dict:
    return {
        "workflow": [
            {"step": 1, "tool": "load_data", "required_params": ["file_path"]},
            {"step": 2, "tool": "analyze_columns"},
            {"step": 3, "tool": "create_chart", "required_params": ["chart_type", "x", "y"]},
            {"step": 4, "tool": "export_dashboard"},
        ],
        "instructions": "Follow these steps in order. Each tool's response will provide guidance for the next step.",
        "important": "Do not skip steps. Step 2 output is required for step 3.",
    }
```

Mark planner descriptions with "Call this FIRST" — the model treats it as a strong signal to invoke before anything else. McKinsey's `vizro-mcp` uses this exact pattern.

### Design tool workflows for 3-5 calls, not 20+

Frontier models handle 20+ sequential tool calls; smaller and open-source models degrade after 5-7 — they forget earlier results, hallucinate parameters, or loop. If the server requires 15 tool calls to complete a common task, the design locks itself into expensive frontier models.

Design tools so common goals complete in 3-5 calls. This means each tool does more meaningful work per invocation, not that you have fewer tools.

### CRUD — combined vs separate decision

When you have multiple entity types each needing create/read/update/delete, you face a design choice.

**Combine when:** many entity types (4+ entities × 4 ops = 16+ tools). Most models degrade with 20+ tools in the prompt. Combining gives you 4 tools instead of 16.

**Keep separate when:** few entity types (3 or fewer), per-operation user approval needed (reads auto-approved, deletes confirmed), or operations have radically different parameter shapes.

```python
@tool(description="Manage users. Actions: 'list' (filter by role/status), 'get' (by user_id), 'create' (name+email required), 'update' (user_id + fields to change), 'delete' (irreversible).")
def manage_user(
    action: Literal["list", "get", "create", "update", "delete"],
    user_id: str | None = None,
    filters: dict | None = None,
    data: dict | None = None,
) -> dict:
    match action:
        case "list":   return {"users": db.users.find(filters or {})}
        case "get":    return {"user": db.users.find_one(user_id)}
        case "create": return {"user": db.users.insert(data), "status": "created"}
        case "update": db.users.update(user_id, data); return {"user": db.users.find_one(user_id), "status": "updated"}
        case "delete": db.users.delete(user_id); return {"status": "deleted", "user_id": user_id}
```

| Factor | Combine | Separate |
|---|---|---|
| Entity types | >3 | 3 or fewer |
| Total tool count | Approaching 20+ | Under 15 |
| Approval granularity | Same for all ops | Different per operation |
| Parameter overlap | High | Low |

### Toolhost / facade pattern for many related operations

When the server exposes 20+ closely related operations, expose a single dispatcher tool that routes via an `operation` parameter. This is the GoF Facade pattern applied to MCP — shared logic (auth, logging, error handling) lives in the facade.

```python
OPERATIONS = {
    "list_users":    {"handler": list_users,    "args": ["filters", "page"]},
    "get_user":      {"handler": get_user,      "args": ["user_id"]},
    "create_user":   {"handler": create_user,   "args": ["name", "email", "role"]},
    "list_projects": {"handler": list_projects, "args": ["owner_id", "status"]},
    "export_data":   {"handler": export_data,   "args": ["entity", "format"]},
}

@tool(description=f"Admin API gateway. Operations: {', '.join(OPERATIONS.keys())}. Pass the operation name and its arguments.")
def admin_toolhost(operation: str, args: dict = {}) -> dict:
    if operation not in OPERATIONS:
        return {"error": f"Unknown operation. Available: {list(OPERATIONS.keys())}"}
    op = OPERATIONS[operation]
    missing = [a for a in op["args"] if a not in args and a not in OPTIONAL_ARGS]
    if missing:
        return {"error": f"Missing required args for {operation}: {missing}"}
    try:
        return {"operation": operation, "status": "success", "result": op["handler"](**args)}
    except Exception as e:
        return {"operation": operation, "status": "error", "error": str(e)}
```

**Use when:** 20+ operations sharing common auth/validation, closely related domain. **Avoid when:** fewer than five operations, individual approval flows, radically different parameter shapes.

The tradeoff is discoverability — your description string must enumerate all available operations.

### Expose a code execution sandbox for batch operations

For data-heavy tasks (batch processing, pagination, custom analytics), expose a single `execute_code` tool that runs LLM-generated Python in a sandbox.

```json
{
  "name": "execute_code",
  "description": "Run Python code in a secure sandbox with access to pre-authenticated API clients (salesforce_client, s3_client). Use for batch operations, data processing, or any task requiring loops/parallelism.",
  "input_schema": {
    "type": "object",
    "properties": {
      "code": {"type": "string", "description": "Python code to execute."},
      "timeout": {"type": "integer", "default": 300}
    },
    "required": ["code"]
  }
}
```

Security requirements (non-negotiable): isolated containers with `--no-new-privileges`, dropped capabilities, read-only filesystem, CPU/memory cgroup limits, network egress whitelist, pre-authenticated API clients (never expose raw keys), no `eval`/`exec` on untrusted strings, hard timeouts. See `security.md` for the full hardening list.

**Use when:** batch exports, heavy pagination, custom analytics, file transformations — anywhere the final output is a file or URL rather than a conversational response.

---

## Tool descriptions

### Descriptions are prompt engineering

A `tools/list` description is text the LLM reads at decision time. Write for the model, not for a human reading docs. Names, parameter labels, error hints — all of it is the prompt the agent uses to figure out whether to call the tool. The cross-surface principles live in `../../common/descriptions-as-prompts.md`. This section is the MCP-specific deep dive.

### Use XML tags to separate purpose from instructions

Models parse tool descriptions as their only guide. Structuring with XML tags significantly improves selection accuracy because the model can distinguish "what it's for" from "how to use it."

```xml
<usecase>Retrieves member activity for a space, including posts, comments, and last active date. Useful for tracking user activity.</usecase>
<instructions>Returns members sorted by total activity. Defaults to last 30 days.</instructions>
```

This works because LLMs already have strong XML parsing priors from training. Flat paragraphs muddle purpose and usage; tagged sections let the model match intent to `<usecase>` and extract parameters from `<instructions>`.

### Write descriptions like briefing a new hire

The model has zero institutional knowledge. Every conversation starts fresh with only descriptions to guide it.

- State the tool's single, clear purpose explicitly
- Define domain-specific terminology
- Make implicit conventions explicit ("dates are YYYY-MM-DD")
- Include a brief usage example
- Specify what the tool does NOT do to prevent misuse

```python
@tool(
    name="search_contacts",
    description="""Search the CRM for contacts matching criteria.

    Returns contact records with name, email, and company.
    Use this when the user asks to find, look up, or search for people.
    Do NOT use this for updating contacts — use update_contact instead.

    Example: search_contacts(query="Jane at Acme") returns matching contacts.
    Supports partial name matching and company name filtering.""",
)
```

### Namespace tools to prevent collisions across servers

When multiple servers connect to the same agent, tool name collisions cause silent failures. Namespace every tool with a consistent prefix.

```
asana_search_tasks
asana_create_task
jira_search_issues
jira_create_issue
```

Pick one scheme — `{service}_{action}` or `{service}_{resource}_{action}` — and use it consistently. Generic names like `search`, `create`, `update` collide the moment a second server connects.

Use only `[a-z0-9_]` in tool names. Several MCP clients (early Claude Desktop, others) crash entire connections when names contain `/`, `-`, `.`, spaces, or unicode. Lint at registration time:

```typescript
const SAFE_TOOL_NAME = /^[a-z][a-z0-9_]{0,63}$/;
function registerTool(name: string, ...rest: any[]) {
  if (!SAFE_TOOL_NAME.test(name)) {
    throw new Error(`Invalid tool name "${name}". Use lowercase letters, digits, underscores; must start with a letter; max 64 chars.`);
  }
  server.tool(name, ...rest);
}
```

### Front-load verb + resource in the first five words

LLMs skim descriptions like humans skim headlines — first words carry disproportionate weight. If your description starts with "This tool is used to…" the model has already wasted attention before reaching the signal.

Structure: **Verb + Resource + key scope**, then stop. Keep descriptions under ~100 tokens.

Good:

```json
{"name": "search_customers",
 "description": "Search customers by name, email, or account ID. Returns top 20 matches with account status. Use list_customers for unfiltered pagination."}
```

Anti-pattern:

```json
{"name": "search_customers",
 "description": "This tool provides the ability to search through the customer database using various criteria including but not limited to name, email address, and account identifier. It will return a paginated list of results sorted by relevance score with additional metadata about each customer's current account status and tier level."}
```

50+ tokens before the model learns what the tool does.

**Rule:** first 5 words → selection. Next 20 words → parameters. Everything after → diminishing returns.

### Include exclusionary guidance — when NOT to use the tool

Positive descriptions are necessary but insufficient. With overlapping tools, the model needs explicit negative routing.

```json
{"name": "get_customer",
 "description": "Fetch a single customer by ID. Returns full profile with contact info and billing history. Do NOT use for searching — use search_customers instead."}

{"name": "search_customers",
 "description": "Search customers by name or email. Returns top 20 matches. Do NOT use for bulk export; use export_customers for datasets over 100 records."}

{"name": "export_customers",
 "description": "Export all customers matching a filter as CSV. Async — returns a job ID. Do NOT use for single lookups; use get_customer instead."}
```

Without exclusionary hints, models default to the "biggest" tool — the one that could technically handle every case. Figma's MCP server uses `"Do NOT use unless explicitly requested by the user"` on its `depth` parameter to prevent expensive deep-tree calls by default.

### Truth in the schema, hints in the description

The schema carries machine-enforceable truth (types, required fields, enums, ranges). The description carries context the schema cannot express (side effects, auth scope, rate limits, latency, idempotency, failure modes). Don't duplicate.

```json
{
  "name": "update_invoice_status",
  "description": "Transition an invoice to a new status. Changing to 'sent' triggers an email to the customer (irreversible side effect). Changing to 'paid' requires payment_id. Rate limited to 10 calls/min per invoice.",
  "inputSchema": {
    "type": "object",
    "required": ["invoice_id", "status"],
    "properties": {
      "invoice_id": {"type": "string", "description": "UUID of the invoice"},
      "status":     {"type": "string", "enum": ["draft", "sent", "paid", "void"]},
      "payment_id": {"type": "string", "description": "Required when status is 'paid'"}
    }
  }
}
```

The description adds three things the schema cannot: side effect (`sent` triggers email), conditional requirement (`payment_id` for `paid`), rate limit (10/min).

**Schema = what's valid. Description = what's wise.**

### Use the `instructions` field as the server's briefing doc

The MCP `initialize` response includes an `instructions` field — free-form text the client surfaces as system-level context. This is the most reliable place to explain overall capabilities, recommended workflows, and inter-tool relationships. Unlike `prompts` (silently ignored by many clients), `instructions` is consistently read by Claude Desktop, Cursor, and other major clients.

```typescript
const server = new McpServer({
  name: "acme-crm",
  version: "1.0.0",
  instructions: `
# Acme CRM MCP Server

## Capabilities
- Customer management (CRUD + search)
- Invoice lifecycle (create → send → pay → void)
- Activity log queries

## Recommended workflows
1. Look up customer → search_customers → get_customer
2. Send invoice → create_invoice → add_line_items → send_invoice
3. Check payment → get_invoice → get_payment

## Constraints
- All write ops require a valid session (call authenticate first)
- Invoice sends are irreversible and trigger customer emails
- Rate limit: 60 requests/min across all tools
  `.trim(),
});
```

Treat this like an agent-instructions file — a briefing the agent reads once at session start.

### Add correct AND incorrect call examples in descriptions

A well-placed example eliminates an entire class of misuse. One correct example plus one common mistake — more bloats the prompt without proportional benefit.

```json
{
  "name": "search_orders",
  "description": "Search orders by customer, date range, or status. Max 50 results.\n\nExample — search by date range:\n{\"customer_id\": \"cust_123\", \"after\": \"2024-01-01\", \"before\": \"2024-03-01\"}\n\nExample — common mistake (wrong date format):\n{\"customer_id\": \"cust_123\", \"after\": \"Jan 1 2024\"}\nDates must be ISO 8601 (YYYY-MM-DD). Natural language dates fail.\n\nExample response:\n{\"orders\": [{\"id\": \"ord_456\", \"status\": \"shipped\", \"total\": 99.50}], \"has_more\": true}"
}
```

The example response is equally valuable. When agents see the shape of the output, they can plan downstream calls without exploratory requests.

### Over-verbose descriptions reduce tool call rate

Descriptions over ~200 tokens cause LLMs to call the tool *less* often, not more. Over-long descriptions compete with the model's generative attention — long enough to read like a mini-essay, the model sometimes "answers" using the description's text instead of calling the tool.

Measure description token cost at registration:

```typescript
function registerWithLengthCheck(name, description, schema, handler) {
  const tokens = estimateTokens(description);
  if (tokens > 200) {
    console.warn(`Tool "${name}" description is ${tokens} tokens (limit: 200). Consider trimming.`);
  }
  server.tool(name, description, schema, handler);
}
```

Move parameter-level guidance into individual parameter `description` fields rather than the tool description. The model reads parameter descriptions when filling arguments — exactly when parameter guidance is needed.

```typescript
{
  query: z.string().describe("Search term. Supports regex if prefixed with 're:'"),
  file_type: z.string().optional().describe("Filter by extension, e.g. '.ts' or '.py'"),
}
```

The 200-token rule: short enough to scan, specific enough to select.

---

## Tool responses

### Treat every tool response as a prompt to the model

This is the single most important MCP design insight. Stop treating MCP servers like APIs with better descriptions. Every tool response is injected directly into the model's context and becomes part of its reasoning input.

A raw API response:

```json
{"members": [{"id": "u1", "name": "Jane"}, {"id": "u2", "name": "Bob"}], "total": 25}
```

An MCP-optimized response:

```json
{
  "members": [{"name": "Jane Doe", "activity_score": 92}, {"name": "Bob Smith", "activity_score": 45}],
  "total": 25,
  "summary": "Found 25 active members in the last 30 days. Top contributor: Jane Doe.",
  "next_steps": "Use bulk_message() to contact these members, or filter by activity_score to focus on top contributors."
}
```

**What to include:** human-readable summary, suggested next actions with specific tool names, context that helps interpret the data, pagination hints when truncated.

**What to avoid:** raw JSON dumps with no context, internal IDs without human-readable labels, technical metadata the model can't reason about.

### Content blocks — the response shape

MCP tool results return a `content` array. The block types: `text` (most common), `image` (base64 + mimeType), `audio`, `resource` (a `uri` referring to data the client can fetch separately), and `file` (extension via `_meta`). Each block carries optional `annotations` (`audience`, `priority` — see below).

```typescript
return {
  content: [
    { type: "text", text: "Summary text the user reads first." },
    { type: "image", mimeType: "image/png", data: base64Encoded },
  ],
  isError: false,
};
```

For tabular or large data, prefer a single `text` block with a human-readable header followed by serialized data — see the YAML / TSV recommendations below.

### Structured content vs text

MCP supports `outputSchema` on tools — declare the response shape, and the SDK validates at runtime. The agent gets a contract it can rely on; the SDK catches server bugs before they reach the agent.

**Critical rule:** when declaring an `outputSchema`, return `structuredContent`. Always return `content` too for backward compatibility.

```typescript
server.registerTool("get_weather", {
  description: "Get current weather for a city",
  inputSchema:  { city: z.string() },
  outputSchema: {
    temperature: z.number(),
    conditions:  z.string(),
    humidity:    z.number(),
  },
}, async ({ city }) => {
  const w = await fetchWeather(city);
  return {
    content: [{ type: "text", text: `${city}: ${w.temperature}C, ${w.conditions}, ${w.humidity}% humidity` }],
    structuredContent: { temperature: w.temperature, conditions: w.conditions, humidity: w.humidity },
  };
});
```

When the implementation is not ready to commit to a schema, don't declare one — add it when the response shape stabilizes.

### The `isError` flag

The result object carries `isError: true` when the tool ran but failed. This is **distinct from a protocol-level error**. Protocol errors are reserved for transport/framework failures (bad JSON, unknown method, server crash) and the LLM typically never sees them — the client swallows them. Use `isError: true` for all business logic failures so the model can reason about and recover from the failure. See `error-handling.md` for the full pattern.

```json
{
  "result": {
    "content": [{"type": "text", "text": "Cannot terminate instance while running. Call stop_instance(instance_id='i-abc123') first, then retry."}],
    "isError": true
  }
}
```

### Add a response_format enum to data-returning tools

Give the agent control over verbosity. This single pattern can cut token usage 60-70%.

```python
class ResponseFormat(Enum):
    DETAILED = "detailed"
    CONCISE  = "concise"

@tool
def get_customer(customer_id: str, response_format: ResponseFormat = ResponseFormat.CONCISE):
    data = fetch_customer(customer_id)
    if response_format == ResponseFormat.DETAILED:
        return {
            "name": data.name, "email": data.email,
            "recent_transactions": data.transactions, "notes": data.notes,
            "internal_id": data.id, "thread_ts": data.thread_ts,
        }
    return {"name": data.name, "email": data.email, "summary": data.summary}
```

Concise: ~72 tokens. Detailed: ~206 tokens. Over a 10-step workflow this compounds dramatically.

### Return semantic identifiers, not opaque UUIDs

Models reason in natural language. `"id": "550e8400-e29b-41d4-a716-446655440000"` is unreasonable, unmemorable, and likely to be hallucinated when passed to a downstream tool.

Bad:

```json
{"project_id": "550e8400-e29b-41d4-a716-446655440000", "channel_id": "C04BKGH3L8P"}
```

Good:

```json
{"project_name": "Q4 Marketing Campaign", "project_id": "q4-marketing", "channel_name": "#general"}
```

Always include a human-readable name alongside any ID. Use slug-style IDs when possible. When UUIDs are unavoidable, pair them: `{"project": {"id": "550e...", "name": "Q4 Marketing"}}`.

### Prepend truncation guidance when results are cut off

Don't silently return partial data. Tell the model what happened and how to get more.

```python
@tool
def search_logs(query: str, limit: int = 50) -> dict:
    results = log_store.search(query, limit=limit + 1)
    truncated = len(results) > limit
    results = results[:limit]
    response = {"results": results, "count": len(results), "total_available": log_store.count(query)}
    if truncated:
        response["guidance"] = (
            f"Showing {limit} of {response['total_available']} results. "
            f"Filter by date_range or add specific terms to narrow."
        )
    return response
```

Place guidance **before** data so the model reads it first. Include the total count so the model can decide if narrowing is worthwhile. Claude Code caps tool responses at 25,000 tokens — plan for the limit.

### Include next-step hints in successful responses

HATEOAS at the language level. The model has no memory of the API's workflow. A developer would read docs; the model relies on the response.

```python
@tool
def create_project(name: str, repo_url: str) -> dict:
    project = api.create_project(name=name, repo=repo_url)
    return {
        "status": "success",
        "project_id": project.id,
        "project_name": name,
        "message": f"Project '{name}' created successfully.",
        "next_steps": [
            f"Use add_environment_variables(project_id='{project.id}') to configure env vars.",
            f"Use create_deployment(project_id='{project.id}', branch='main') to deploy.",
            f"Use add_custom_domain(project_id='{project.id}', domain='...') to set up a domain.",
        ],
    }
```

Keep hints specific (name the exact tool, include parameter values), order by likelihood (most common first), keep to 2-4 hints to avoid overwhelming context, use actual values from the current response.

### Default to YAML over JSON for LLM-consumable responses

JSON is the developer default; YAML is the better default for MCP responses. ~30% fewer tokens — no curly braces, no quotes on keys, no commas — and the model parses both equally well.

JSON (47 tokens):

```json
{"component": "Button", "props": {"variant": "primary", "size": "large", "disabled": false}, "children": ["Submit"]}
```

YAML (~30% fewer):

```yaml
component: Button
props:
  variant: primary
  size: large
  disabled: false
children:
  - Submit
```

Offer a format parameter so the agent can request JSON when it needs programmatic processing. Default YAML — let the agent override.

### Use TSV for tabular data

Tab-separated values save 30-40% tokens vs JSON for rows. Headers appear once; LLMs parse TSV correctly without prompting.

JSON (high cost):

```json
[
  {"name": "Alice", "age": 30, "city": "New York", "role": "admin"},
  {"name": "Bob",   "age": 25, "city": "San Francisco", "role": "editor"}
]
```

TSV (~40% less):

```
name	age	city	role
Alice	30	New York	admin
Bob	25	San Francisco	editor
```

When TSV breaks down: nested objects, arrays within cells, values containing tabs/newlines. For those, fall back to YAML or JSON.

### Use content annotations to separate user-facing and assistant-facing data

MCP supports `audience` and `priority` annotations on every content block. Embed debug info, telemetry, and internal context the model can reason about without cluttering the user's view.

```typescript
return {
  content: [
    { type: "text",
      text: `Found ${results.length} matching records.`,
      annotations: { priority: 1.0, audience: ["user", "assistant"] } },
    { type: "text",
      text: `Debug: cache_hit=${meta.cacheHit}, latency=${meta.latencyMs}ms\nFiltered: ${meta.filteredCount} by permissions`,
      annotations: { priority: 0.3, audience: ["assistant"] } },
  ],
};
```

Priority levels: `1.0` critical user info, `0.7` supplementary context, `0.3` debug/telemetry for the model only, `0.1` verbose trace data. Client support varies — well-behaved clients respect `audience`; clients that ignore annotations show everything, so keep assistant-only content informative-but-not-confusing if a user happens to see it.

### What NOT to put in responses

- **Raw API JSON** with no context — the model loses tokens to noise it can't reason about
- **Stack traces** — log them server-side, return a clean message (see `security.md`)
- **Secrets, tokens, PII** — sanitize before the response leaves the server
- **Internal log lines** — those belong on stderr / your log pipeline, not in the agent's context window
- **Wall-clock timestamps** in cached prefixes — invalidates the prompt cache (see `caching-economics.md`)

### Return normalized inputs in every response

When the server accepts flexible input formats and normalizes internally (e.g., `"yesterday"` → `"2024-01-15"`), include the normalized values in the response. This teaches the agent the canonical format, improving every subsequent call.

```json
{
  "result": {"events": [{"title": "Standup", "time": "09:00"}]},
  "normalized_inputs": {"date": "2025-01-15", "note": "Interpreted 'yesterday' as 2025-01-15"}
}
```

After seeing this once, the agent starts using `"2025-01-15"` directly. Every response is a training signal.

### Return a search frontier, not just the first SERP

For research, SEO, and discovery tools, the first result page is rarely the finished product. Return the *current frontier* for the next step.

```json
{
  "summary": "Current SERP is strong on overviews but weak on implementation examples.",
  "results": ["10 search results here"],
  "coverage_gaps": ["Few concrete implementation examples", "Low source diversity"],
  "recommended_next_queries": [
    {"query": "...", "reason": "Fill implementation gap", "expected_signal": "production patterns"}
  ],
  "recommended_next_tool": "fetch_pages",
  "server_actions_taken": [{"type": "internal_planner_turn", "purpose": "derive next-query candidates"}],
  "stop_conditions": ["Stop if two consecutive waves add no novel authoritative sources."]
}
```

Distinguish what the server **already did** from what the agent **should do next**. Bound internal continuation with spend, time, and wave caps. Disclose any internal planner turns — keep the system debuggable.

---

## Cross-references

- `schema-design.md` — input schemas the agent fills in
- `error-handling.md` — error response shape (`isError` + structured content)
- `progressive-discovery.md` — hiding tools the agent doesn't yet need
- `agentic-patterns.md` — multi-step workflows, parameter dependency chains
- `client-compatibility.md` — which clients respect annotations, structured content, etc.
- `../../common/descriptions-as-prompts.md` — cross-surface principles for descriptions
- `../decision-trees/tool-count.md` — when to consolidate, when to split
