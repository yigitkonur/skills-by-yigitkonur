# Tool Response Patterns

How to craft MCP tool responses that steer the model toward correct next steps, minimize token waste, and serve both the user and the agent. These 10 patterns treat every response as a prompt to the model.

## Pattern 1: Treat Every Tool Response as a Prompt to the Model

This is the single most important MCP design insight. Stop treating MCP servers like APIs with better descriptions. Every tool response is injected directly into the model's context and becomes part of its reasoning input.

**A raw API response:**
```json
{"members": [{"id": "u1", "name": "Jane"}, {"id": "u2", "name": "Bob"}], "total": 25}
```

**An MCP-optimized response:**
```json
{
  "members": [{"name": "Jane Doe", "activity_score": 92}, {"name": "Bob Smith", "activity_score": 45}],
  "total": 25,
  "summary": "Found 25 active members in the last 30 days. Top contributor: Jane Doe.",
  "next_steps": "Use bulkMessage() to contact these members, or filter by activity_score to focus on top contributors."
}
```

**The key insight:** Developers read docs, experiment, and remember. AI models start fresh every conversation with only tool descriptions to guide them - until they start calling tools. Then tool responses become the primary steering mechanism.

**What to include in responses:**
- A human-readable summary of the result
- Suggested next actions with specific tool names
- Context that helps the model interpret the data
- Pagination hints when results are truncated

**What to avoid:**
- Raw JSON dumps with no context
- Internal IDs without human-readable labels
- Technical metadata the model can't reason about

**Source:** [u/sjoti on r/mcp](https://reddit.com/r/mcp/comments/1lq69b3/) (279 upvotes, 40 comments). One commenter called this "HATEOAS at the language level."

---

## Pattern 2: Add a Response Format Enum to Every Data-Returning Tool

Give the agent control over response verbosity with a `response_format` parameter. This single pattern can cut token usage by 60-70%.

```python
from enum import Enum

class ResponseFormat(Enum):
    DETAILED = "detailed"
    CONCISE = "concise"

@tool
def get_customer(customer_id: str, response_format: ResponseFormat = ResponseFormat.CONCISE):
    data = fetch_customer(customer_id)

    if response_format == ResponseFormat.DETAILED:
        return {
            "name": data.name,
            "email": data.email,
            "recent_transactions": data.transactions,
            "notes": data.notes,
            "internal_id": data.id,
            "thread_ts": data.thread_ts  # for downstream tool calls
        }
    else:
        return {
            "name": data.name,
            "email": data.email,
            "summary": data.summary
        }
```

**Measured impact:** Concise responses use ~72 tokens vs ~206 tokens for detailed ones - a 65% reduction per call. Over a multi-step workflow with 10+ tool calls, this compounds dramatically.

**When the agent should use each mode:**
- **Concise** (default): For browsing, scanning, initial discovery
- **Detailed**: When the agent needs IDs or metadata for follow-up tool calls

This avoids creating two separate tools for the same data, keeping the tool count low.

**Source:** [Anthropic — Writing effective tools for AI agents](https://www.anthropic.com/engineering/writing-tools-for-agents); [modelcontextprotocol.io — writing effective tools](https://modelcontextprotocol.io)

---

## Pattern 3: Return Semantic Identifiers, Not Opaque UUIDs

Models reason in natural language. When you return `"id": "550e8400-e29b-41d4-a716-446655440000"`, the model can't reason about it, can't remember it across tool calls, and will likely hallucinate it when asked to pass it to another tool.

**Bad:**
```json
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "channel_id": "C04BKGH3L8P",
  "image_url": "https://cdn.example.com/avatars/256px/a7b3c9d1.jpg"
}
```

**Good:**
```json
{
  "project_name": "Q4 Marketing Campaign",
  "project_id": "q4-marketing",
  "channel_name": "#general",
  "profile_image": "Jane's avatar (square, professional headshot)"
}
```

**Practical approach:**
- Always include a human-readable name alongside any ID
- Use slug-style IDs when possible (`q4-marketing` vs UUID)
- Translate internal codes to descriptive labels
- If you must return UUIDs, pair them: `"project": {"id": "550e...", "name": "Q4 Marketing"}`
- For images, describe them textually rather than returning raw pixel-dimension URLs

Models retrieve and reason about natural language far better than opaque identifiers. When a subsequent tool call requires passing an ID, the model is more likely to use the correct one if it can associate it with a meaningful name.

**Source:** [Anthropic — Writing effective tools for AI agents](https://www.anthropic.com/engineering/writing-tools-for-agents); [modelcontextprotocol.io — writing effective tools](https://modelcontextprotocol.io)

---

## Pattern 4: Prepend Truncation Guidance When Results Are Cut Off

When you paginate or truncate results, don't just silently return partial data. Tell the model what happened and how to get more.

```python
@tool
def search_logs(query: str, limit: int = 50) -> dict:
    results = log_store.search(query, limit=limit + 1)
    truncated = len(results) > limit
    results = results[:limit]

    response = {
        "results": results,
        "count": len(results),
        "total_available": log_store.count(query),
    }

    if truncated:
        response["guidance"] = (
            f"Showing {limit} of {response['total_available']} results. "
            f"Consider filtering by date range (e.g., start_date='2025-01-01') "
            f"or adding more specific terms to narrow results."
        )

    return response
```

**Key details:**
- Place guidance **before** the data in the response so the model reads it first
- Suggest specific parameter values that would reduce the result set
- Include the total count so the model can decide if narrowing is worthwhile
- Claude Code caps tool responses at 25,000 tokens - plan for this limit

**Anti-pattern:** Silently returning the first N results with no indication that more exist. The model will assume the returned data is complete and draw incorrect conclusions.

**Source:** [Anthropic — Writing effective tools for AI agents](https://www.anthropic.com/engineering/writing-tools-for-agents); [modelcontextprotocol.io — writing effective tools](https://modelcontextprotocol.io)

---

## Pattern 5: Include Next-Step Hints in Successful Responses

Don't just return data - tell the model what it can do next. This is the "HATEOAS at the language level" pattern.

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
            f"Use add_custom_domain(project_id='{project.id}', domain='...') to set up a domain."
        ]
    }
```

**Why this works:** The model has no memory of your API's workflow. A developer would read your docs and know that after creating a project, the next step is to configure env vars and deploy. The model doesn't know this unless you tell it — and the tool response is the perfect place.

**Guidelines:**
- Keep hints specific: name the exact tool and include required parameter values
- Order hints by likelihood (most common next action first)
- Only include 2-4 hints to avoid overwhelming the context
- Use the actual parameter values from the current response (don't make the model guess)

**Real-world example:** One practitioner built a data visualization MCP server where a "planner tool" returns structured guidance about what order to call visualization tools. Every subsequent tool response reinforces the workflow with further guidance. They call this "flattening the agent back into the model."

**Source:** [u/sjoti on r/mcp](https://reddit.com/r/mcp/comments/1lq69b3/) (279 upvotes); [u/Biggie_2018 on r/mcp](https://reddit.com/r/mcp) — McKinsey [vizro-mcp](https://github.com/mckinsey/vizro)

---

## Pattern 6: Default to YAML Over JSON for LLM-Consumable Responses

JSON is the developer default, but YAML is the better default for MCP tool responses. It's more readable for LLMs and more token-efficient — no curly braces, no quotes on keys, no commas.

**JSON response (47 tokens):**
```json
{
  "component": "Button",
  "props": {
    "variant": "primary",
    "size": "large",
    "disabled": false
  },
  "children": ["Submit"]
}
```

**YAML equivalent (~30% fewer tokens):**
```yaml
component: Button
props:
  variant: primary
  size: large
  disabled: false
children:
  - Submit
```

The model processes both equally well, but the YAML version burns fewer context tokens.

**Offer a format parameter** so the agent can request JSON when it needs programmatic processing:

```typescript
import yaml from "js-yaml";

server.registerTool("get_design_tokens", {
  inputSchema: {
    file_key: z.string(),
    output_format: z.enum(["yaml", "json"]).default("yaml"),
  },
}, async ({ file_key, output_format }) => {
  const result = await fetchDesignTokens(file_key);
  const formatted = output_format === "json"
    ? JSON.stringify(result, null, 2)
    : yaml.dump(result, { lineWidth: -1 });

  return { content: [{ type: "text", text: formatted }] };
});
```

**When to stick with JSON:** When the response will be piped into another tool that expects JSON input, or when the agent explicitly requests it. Let the agent decide — just make YAML the default.

**Source:** [Figma-Context-MCP](https://github.com/GLips/Figma-Context-MCP) (defaults to YAML for all design data responses); community findings on token efficiency of serialization formats

---

## Pattern 7: Use TSV for Tabular Data to Save 30-40% of Tokens

When your tool returns table-shaped data — database query results, list outputs, CSV-like records — use TSV (tab-separated values) instead of JSON. LLMs parse TSV correctly without any extra prompting, and it saves 30-40% of tokens compared to the JSON equivalent.

**JSON array (high token cost):**
```json
[
  {"name": "Alice", "age": 30, "city": "New York", "role": "admin"},
  {"name": "Bob", "age": 25, "city": "San Francisco", "role": "editor"},
  {"name": "Carol", "age": 35, "city": "Chicago", "role": "viewer"}
]
```

Every row repeats every key. For 100 rows with 5 columns, that's 500 redundant key strings.

**TSV equivalent (~40% fewer tokens):**
```
name	age	city	role
Alice	30	New York	admin
Bob	25	San Francisco	editor
Carol	35	Chicago	viewer
```

Headers appear once. No braces, no quotes, no colons, no commas. The model understands this instantly.

**Implementation pattern:**

```typescript
function toTSV(rows: Record<string, unknown>[]): string {
  if (rows.length === 0) return "(no results)";
  const headers = Object.keys(rows[0]);
  const lines = [
    headers.join("\t"),
    ...rows.map(row => headers.map(h => String(row[h] ?? "")).join("\t"))
  ];
  return lines.join("\n");
}

server.registerTool("query_users", {
  inputSchema: { filter: z.string().optional() },
}, async ({ filter }) => {
  const users = await db.query(`SELECT name, age, city, role FROM users`);
  return {
    content: [{
      type: "text",
      text: `Found ${users.length} users:\n\n${toTSV(users)}`
    }]
  };
});
```

**When TSV breaks down:** Nested objects, arrays within cells, or values containing tabs/newlines. For those, fall back to YAML or JSON. But for the vast majority of database results and list outputs, TSV is the right default.

**Source:** [pgEdge — Lessons Learned Writing an MCP Server for PostgreSQL](https://www.pgedge.com/blog/lessons-learned-writing-an-mcp-server-for-postgresql) — discovered significant token savings switching query results from JSON to TSV

---

## Pattern 8: Use Content Annotations to Separate User-Facing and Assistant-Facing Data

MCP supports content annotations with `audience` and `priority` fields on every content block. Use them to embed debug info, telemetry, and internal context that the model can reason about without cluttering the user's view.

**Without annotations — everything goes to the user:**
```
Found 15 matching records.
Cache hit ratio: 0.95, latency: 150ms, query plan: seq_scan on users_idx.
3 results filtered by permission check. Auth token expires in 240s.
```

**With annotations — layered content:**

```typescript
server.registerTool("search_records", {
  inputSchema: { query: z.string() },
}, async ({ query }) => {
  const { results, meta } = await search(query);

  return {
    content: [
      {
        type: "text",
        text: `Found ${results.length} matching records.`,
        annotations: {
          priority: 1.0,
          audience: ["user", "assistant"],
        },
      },
      {
        type: "text",
        text: [
          `Debug: cache_hit=${meta.cacheHit}, latency=${meta.latencyMs}ms`,
          `Query plan: ${meta.queryPlan}`,
          `Filtered: ${meta.filteredCount} by permissions`,
          `Auth token TTL: ${meta.tokenTTL}s`,
        ].join("\n"),
        annotations: {
          priority: 0.3,
          audience: ["assistant"],
        },
      },
    ],
  };
});
```

The model sees everything and can use the debug data to optimize subsequent calls. The user only sees the clean summary.

**Priority levels to use:**
- `1.0` — Critical info the user asked for
- `0.7` — Supplementary context (pagination hints, next steps)
- `0.3` — Debug/telemetry data for the model only
- `0.1` — Verbose trace data, only relevant if something fails

**Note:** Client support for annotations varies. Well-behaved clients will respect `audience` and hide assistant-only content. Clients that ignore annotations will show everything — so keep assistant-only content informative but not confusing if a user happens to see it.

**Source:** [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) — everything server reference implementation; [MCP specification — content annotations](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)

---

## Pattern 9: Declare Output Schemas and Return structuredContent

MCP supports output schemas on tools — declare the shape of your response, and the SDK validates it at runtime. This gives the model a contract it can rely on and catches server bugs before they reach the agent.

**The critical rule:** If you declare an `outputSchema`, you **must** return `structuredContent`. The TypeScript SDK throws if you declare an output schema but only return text `content`. Always return both for backward compatibility.

```typescript
import { z } from "zod";

server.registerTool("get_weather", {
  description: "Get current weather for a city",
  inputSchema: {
    city: z.string().describe("City name"),
  },
  outputSchema: {
    temperature: z.number().describe("Temperature in Celsius"),
    conditions: z.string().describe("Weather conditions"),
    humidity: z.number().describe("Humidity percentage"),
  },
}, async ({ city }) => {
  const weather = await fetchWeather(city);

  return {
    // Text content for clients that don't support structured output
    content: [{
      type: "text",
      text: `${city}: ${weather.temperature}C, ${weather.conditions}, ${weather.humidity}% humidity`,
    }],
    // Structured content validated against outputSchema
    structuredContent: {
      temperature: weather.temperature,
      conditions: weather.conditions,
      humidity: weather.humidity,
    },
  };
});
```

**Why this matters:**
1. **Agent reliability** — the model knows the exact response shape before calling the tool, so it can plan multi-step workflows without exploratory calls
2. **Runtime validation** — the SDK rejects malformed responses at the server, not at the agent
3. **Backward compatibility** — older clients that don't understand `structuredContent` still get the text `content`

**Common mistake:** Declaring an output schema during development, then forgetting to populate `structuredContent`. The SDK will throw a validation error at runtime. If you're not ready to commit to a schema, don't declare one — add it when the response shape stabilizes.

**Source:** [modelcontextprotocol/typescript-sdk](https://github.com/modelcontextprotocol/typescript-sdk) (output schema validation logic); [MCP specification — tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)

---

## Pattern 10: Put Example Responses in Tool Descriptions

Include a concrete example response directly in your tool's description. The agent learns the response shape from the example and can plan subsequent tool calls without making a throwaway exploratory call first. One example in the description saves one round-trip at runtime.

**Without an example — the agent guesses or wastes a call:**
```typescript
server.registerTool("list_users", {
  description: "List users in the workspace",
  inputSchema: { role: z.string().optional() },
}, handler);
```

**With an example — the agent knows what to expect:**
```typescript
server.registerTool("list_users", {
  description: `List users in the workspace.

Returns a JSON object with:
- "users": array of {id, name, email, role}
- "total": total count (may exceed returned results)
- "has_more": whether more pages exist

Example response:
{
  "users": [
    {"id": "u_abc1", "name": "Jane Doe", "email": "jane@co.com", "role": "admin"},
    {"id": "u_abc2", "name": "Bob Smith", "email": "bob@co.com", "role": "member"}
  ],
  "total": 47,
  "has_more": true
}

Use "page" param to paginate. Pass user "id" values to get_user_details.`,
  inputSchema: {
    role: z.string().optional().describe("Filter by role: admin, member, viewer"),
    page: z.number().optional().describe("Page number, starts at 1"),
  },
}, handler);
```

**What this unlocks:**
- The agent can write code that destructures the response correctly on the first try
- It knows `has_more` exists and will paginate automatically
- It knows to pass `id` (not `name` or `email`) to downstream tools
- It won't make a dummy call just to discover the response format

**Keep examples minimal** — one or two records, not a full page of results. The agent extrapolates the pattern.

This is not pretty, but it works. The description gets long, and purists will object. But in practice, agents that see example responses make fewer errors and fewer exploratory calls. The token cost of a slightly longer description is far less than the cost of a wasted tool round-trip.

**Source:** [u/gauthierpia on r/AI_Agents](https://reddit.com/r/AI_Agents) — reported significant reduction in wasted tool calls after adding example responses to descriptions
