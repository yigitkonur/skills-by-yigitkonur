# Tool Description Patterns

How to write tool descriptions that maximize selection accuracy and minimize misuse. These 11 patterns cover structure, naming, schema design, and the critical balance between informativeness and verbosity.

## Pattern 1: Use XML Tags to Separate Purpose from Instructions

Models parse tool descriptions as their only guide for when and how to use a tool. Structuring descriptions with XML tags significantly improves selection accuracy because models can distinguish the "what it's for" from the "how to use it."

```xml
<usecase>Retrieves member activity for a space, including posts, comments, and last active date. Useful for tracking activity of users.</usecase>
<instructions>Returns members sorted by total activity. Includes last 30 days by default.</instructions>
```

This pattern works because LLMs already have strong XML parsing priors from training data. A flat paragraph describing both purpose and usage gets muddled; tagged sections let the model quickly match intent to the `<usecase>` block and extract parameters from `<instructions>`.

In testing, this reduced tool selection errors noticeably compared to free-text descriptions, especially when multiple tools have overlapping capabilities.

**Source:** [u/sjoti on r/mcp](https://reddit.com/r/mcp/comments/1lq69b3/) — XML tags in descriptions "work wonders"

---

## Pattern 2: Write Descriptions Like Briefing a New Hire

The model has zero institutional knowledge. Every conversation starts fresh with only tool descriptions to guide it. Write descriptions as if explaining a tool to a competent new hire on their first day:

- State the tool's **single, clear purpose** explicitly
- Define any domain-specific terminology
- Make implicit conventions explicit (e.g., "dates are in YYYY-MM-DD format")
- Include a brief usage example showing expected input/output
- Specify what the tool does NOT do to prevent misuse

```python
@tool(
    name="search_contacts",
    description="""Search the CRM for contacts matching criteria.

    Returns contact records with name, email, and company.
    Use this when the user asks to find, look up, or search for people.
    Do NOT use this for updating contacts - use update_contact instead.

    Example: search_contacts(query="Jane at Acme") returns matching contacts.
    Supports partial name matching and company name filtering."""
)
```

Small, measured refinements to tool descriptions have shown large accuracy gains. Anthropic's Claude Sonnet 3.5 saw significant SWE-bench score improvements, with description quality contributing as one of several factors.

**Source:** [Anthropic — Writing effective tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents); [Anthropic — SWE-bench Sonnet](https://www.anthropic.com/engineering/swe-bench-sonnet)

---

## Pattern 3: Namespace Tools to Prevent Collisions Across MCP Servers

When multiple MCP servers are connected to the same agent, tool name collisions cause silent failures or unpredictable routing. Namespace every tool with a consistent prefix.

```
asana_search_tasks
asana_create_task
jira_search_issues
jira_create_issue
```

**Naming scheme options:**
- `{service}_{action}` - e.g., `github_create_pr`
- `{service}_{resource}_{action}` - e.g., `asana_projects_search`

Pick one scheme and use it consistently. Different LLMs respond better to different schemes, so test with your target model.

**Anti-pattern:** Generic names like `search`, `create`, `update` that collide the moment you connect a second MCP server.

Agents use tool names as the first disambiguation signal. Without namespacing, the model must rely entirely on description text to distinguish between `search` (contacts) and `search` (files), which fails under context pressure.

**Source:** [Anthropic — Writing effective tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents); [MCP writing effective tools tutorial](https://modelcontextprotocol.info/docs/tutorials/writing-effective-tools/)

---

## Pattern 4: Use Unambiguous Parameter Names

Generic parameter names like `user`, `id`, or `data` force the model to infer meaning from context. Specific names like `user_id`, `project_name`, or `start_date` are self-documenting and reduce hallucination.

**Bad:**
```json
{
  "user": "string",
  "id": "string",
  "type": "string"
}
```

**Good:**
```json
{
  "user_email": "string - the email address of the user to look up",
  "project_id": "string - UUID of the project (use list_projects to find this)",
  "event_type": "string - one of: 'meeting', 'reminder', 'deadline'"
}
```

**Additional tips:**
- Use enums with `minimum`/`maximum` constraints to tighten validation
- Mark fields as `required` to prevent the model from guessing defaults
- Add descriptions to each parameter, not just the tool itself
- Reference other tools in parameter descriptions when values come from them (e.g., "use list_projects to get this ID")

Models treat parameter schemas as part of the prompt. Rich schemas with enums and descriptions act as inline documentation that reduces round-trips and retries by ~25%.

**Source:** [MCP writing effective tools tutorial](https://modelcontextprotocol.info/docs/tutorials/writing-effective-tools/); [NearForm — Implementing MCP: Tips, tricks and pitfalls](https://www.nearform.com/digital-community/implementing-mcp-tips-tricks-and-pitfalls/)

---

## Pattern 5: Enforce Strict Input Schemas with Enums and Constraints

Don't rely on description text alone to communicate valid input values. Use JSON Schema constraints to enforce them at the protocol level.

```python
from enum import Enum

class SortOrder(str, Enum):
    ASC = "ascending"
    DESC = "descending"

class DateRange(str, Enum):
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    LAST_90_DAYS = "last_90_days"
    ALL_TIME = "all_time"

@tool
def search_activity(
    space_id: str,
    sort: SortOrder = SortOrder.DESC,
    date_range: DateRange = DateRange.LAST_30_DAYS,
    limit: int = 25  # constrained via Field(ge=1, le=100)
) -> dict:
    """Search member activity in a space."""
```

**What this gives you:**
- Models see the enum values in the schema and pick from them
- Invalid values are caught before execution, producing clear validation errors
- Default values reduce the number of parameters the model must decide on
- Type hints auto-generate JSON Schema via frameworks like FastMCP

**Anti-pattern:** Accepting `str` for everything and hoping the model sends valid values. This leads to silent failures or vague errors deep in business logic.

**Source:** [NearForm — Implementing MCP: Tips, tricks and pitfalls](https://www.nearform.com/digital-community/implementing-mcp-tips-tricks-and-pitfalls/); [MCP best practices](https://modelcontextprotocol.info/docs/best-practices/)

---

## Pattern 6: Front-Load Verb + Resource in the First Five Words

LLMs skim tool descriptions the same way humans skim headlines — the first few words carry disproportionate weight in tool selection. If your description starts with filler ("This tool is used to..."), the model has already wasted its attention budget before reaching the actual signal.

Structure every description as: **Verb + Resource + key scope**, then stop. Keep total descriptions under ~100 tokens.

```json
{
  "name": "search_customers",
  "description": "Search customers by name, email, or account ID. Returns top 20 matches with account status. Use list_customers for unfiltered pagination."
}
```

```json
{
  "name": "create_invoice",
  "description": "Create a draft invoice for a customer. Requires customer_id and at least one line item. Does not send — use send_invoice to deliver."
}
```

**Anti-pattern:**
```json
{
  "name": "search_customers",
  "description": "This tool provides the ability to search through the customer database using various criteria including but not limited to name, email address, and account identifier. It will return a paginated list of results sorted by relevance score with additional metadata about each customer's current account status and tier level."
}
```

The anti-pattern is 50+ tokens before the model learns what the tool actually does.

**Key principle:** First 5 words -> selection. Next 20 words -> parameters. Everything after that -> diminishing returns.

**Source:** Community best practices; Anthropic prompt engineering guidance on concise tool descriptions

---

## Pattern 7: Include Exclusionary Guidance — Tell the Model When NOT to Use a Tool

Positive descriptions ("Use this to...") are necessary but insufficient. When your server exposes multiple tools with overlapping domains, the model needs explicit negative routing to avoid misselection.

```json
{
  "name": "get_customer",
  "description": "Fetch a single customer by ID. Returns full profile with contact info and billing history. Do NOT use for searching — use search_customers instead."
}
```

```json
{
  "name": "search_customers",
  "description": "Search customers by name or email. Returns top 20 matches. Do NOT use for bulk export; use export_customers for datasets over 100 records."
}
```

```json
{
  "name": "export_customers",
  "description": "Export all customers matching a filter as CSV. Async — returns a job ID. Do NOT use for single lookups; use get_customer instead."
}
```

Without exclusionary hints, models tend to default to the "biggest" tool — the one that could technically handle every case.

**Real-world example:** Figma's MCP server uses `"Do NOT use unless explicitly requested by the user"` on its `depth` parameter to prevent agents from making expensive deep-tree calls by default.

Exclusionary guidance acts as a routing table. Without it, tools with overlapping scope create ambiguity, and ambiguity means the model guesses — often wrong.

**Source:** [u/Ok-Birthday-5406 on r/mcp](https://reddit.com/r/mcp); [Figma MCP server](https://github.com/nicholasblexrud/figma-mcp-server) parameter descriptions

---

## Pattern 8: Truth in the Schema, Hints in the Description

The schema and description serve different roles. The schema carries **machine-enforceable truth**: types, required fields, enums, ranges. The description carries **context the schema cannot express**: side effects, auth scope, rate limits, latency, idempotency, and failure modes.

Don't duplicate what the schema already says. If your enum declares `["draft", "sent", "paid"]`, don't repeat those values in the description. Instead, use that space to tell the model what happens when it picks each one.

```json
{
  "name": "update_invoice_status",
  "description": "Transition an invoice to a new status. Changing to 'sent' triggers an email to the customer (side effect, not reversible). Changing to 'paid' requires payment_id. Rate limited to 10 calls/min per invoice.",
  "inputSchema": {
    "type": "object",
    "required": ["invoice_id", "status"],
    "properties": {
      "invoice_id": {
        "type": "string",
        "description": "UUID of the invoice"
      },
      "status": {
        "type": "string",
        "enum": ["draft", "sent", "paid", "void"]
      },
      "payment_id": {
        "type": "string",
        "description": "Required when status is 'paid'"
      }
    }
  }
}
```

The description adds three things the schema cannot:
1. **Side effect** — `sent` triggers an email
2. **Conditional requirement** — `payment_id` needed for `paid`
3. **Rate limit** — 10 calls/min per invoice

**Anti-pattern:** Descriptions that restate types ("invoice_id is a string") or list enum values already visible in the schema. This wastes tokens and creates drift risk when the schema changes but the description doesn't.

**Key principle:** Schema = what's valid. Description = what's wise.

**Source:** [u/GentoroAI on r/mcp](https://reddit.com/r/mcp/comments/1ooqeqy/)

---

## Pattern 9: Use the `instructions` Field as Your Server's skills.md

The MCP `initialize` response includes an `instructions` field — a free-form string that clients surface to the model as system-level context. This is the most reliable place to explain your server's overall capabilities, recommended workflows, and inter-tool relationships.

Unlike the spec's `prompts` feature (which many clients silently ignore), `instructions` is consistently read by Claude Desktop, Cursor, and other major MCP clients.

```typescript
const server = new McpServer({
  name: "acme-crm",
  version: "1.0.0",
  instructions: `
# Acme CRM MCP Server

## Available Capabilities
- Customer management (CRUD + search)
- Invoice lifecycle (create -> send -> pay -> void)
- Activity log queries

## Recommended Workflows
1. **Look up a customer** -> search_customers -> get_customer
2. **Send an invoice** -> create_invoice -> add_line_items -> send_invoice
3. **Check payment status** -> get_invoice -> get_payment

## Important Constraints
- All write operations require a valid session (call authenticate first)
- Invoice sends are irreversible and trigger customer emails
- Rate limit: 60 requests/min across all tools
  `.trim()
});
```

Treat this like a `skills.md` or `AGENTS.md` — a briefing document the agent reads once at session start to understand the full landscape before making its first tool call.

Individual tool descriptions tell the model what each tool does. The `instructions` field tells the model how the tools fit together. Without it, agents discover workflows by trial and error — burning tokens and making avoidable mistakes.

**Source:** [MCP specification — instructions field](https://modelcontextprotocol.io/specification/2025-11-25); [MotherDuck dev diary](https://motherduck.com/blog/dev-diary-building-mcp/); [u/hasmcp on r/mcp](https://reddit.com/r/mcp)

---

## Pattern 10: Add Correct AND Incorrect Call Examples in Descriptions

Including concrete examples in tool descriptions — both happy-path and common mistakes — measurably improves task completion. A well-placed example eliminates an entire class of misuse.

Keep it to one correct example and one edge case or mistake. More than that bloats the prompt without proportional benefit.

```json
{
  "name": "search_orders",
  "description": "Search orders by customer, date range, or status. Returns max 50 results.\n\nExample — search by date range:\n{\"customer_id\": \"cust_123\", \"after\": \"2024-01-01\", \"before\": \"2024-03-01\"}\n\nExample — common mistake (wrong date format):\n{\"customer_id\": \"cust_123\", \"after\": \"Jan 1 2024\"}\nDates must be ISO 8601 (YYYY-MM-DD). Natural language dates will fail.\n\nExample response:\n{\"orders\": [{\"id\": \"ord_456\", \"status\": \"shipped\", \"total\": 99.50}], \"has_more\": true}"
}
```

The example response is equally valuable. When agents see the shape of the output, they can plan downstream tool calls without making a dummy request first.

**What to include in examples:**
- One happy-path call with realistic parameter values
- One common mistake with a brief explanation of why it fails
- One example response showing the actual return shape

**What NOT to include:**
- Exhaustive parameter combinations (that's what the schema is for)
- Lengthy prose explanations alongside examples (the example should speak for itself)

Models learn calling conventions from examples faster than from prose. A single concrete example outperforms a paragraph of rules — and including a wrong example inoculates against the most frequent failure mode.

**Source:** [Anthropic — Writing effective tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents); [u/gauthierpia on r/AI_Agents](https://reddit.com/r/AI_Agents); [u/GentoroAI on r/mcp](https://reddit.com/r/mcp/comments/1ooqeqy/)

---

## Pattern 11: Over-Verbose Descriptions Reduce Tool Call Rate

Tool descriptions over ~200 tokens cause LLMs to call the tool less often, not more. Community evaluations show over-verbose descriptions can significantly reduce tool invocation rates — even when the tool is the correct one to use.

The hypothesis: over-long descriptions compete with the model's generative attention. When a description is long enough to read like a mini-essay, the model sometimes "answers" the question using the description's text instead of calling the tool.

### The 200-Token Rule

```typescript
// Measure description token cost before registering
function registerWithLengthCheck(name: string, description: string, schema: z.ZodObject<any>, handler: Function) {
  const tokens = estimateTokens(description);
  if (tokens > 200) {
    console.warn(`Tool "${name}" description is ${tokens} tokens (limit: 200). Consider trimming.`);
  }
  server.tool(name, description, schema, handler);
}
```

### Optimal Format: Verb + Object + Key Constraint

```
// Too long (320 tokens):
"This tool allows you to search through the repository's codebase using semantic or
keyword-based queries. It supports both exact string matching and fuzzy semantic
search using vector embeddings. The results will include file paths, line numbers,
and surrounding context..."

// Optimal (~35 tokens):
"Search codebase by keyword or semantic query. Returns file paths, line numbers, and
snippets. Use for finding functions, variables, or concepts. Filter by file type or
directory with optional params."
```

### What Belongs in Schema, Not Description

Move parameter-level guidance into the `description` field of individual parameters rather than the tool description. The model reads parameter descriptions when filling in arguments — that's exactly when you want parameter guidance to appear.

```typescript
{
  query: z.string().describe("Search term. Supports regex if prefixed with 're:'"),
  file_type: z.string().optional().describe("Filter by extension, e.g. '.ts' or '.py'"),
}
```

A 400-token description costs more in tokens AND gets called less often. The optimal tool description is short enough to scan and specific enough to select.

**Source:** Community evaluations on tool selection accuracy from [r/mcp](https://reddit.com/r/mcp); [Anthropic prompt engineering guide](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering)
