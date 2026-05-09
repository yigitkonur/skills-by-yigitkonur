# Resources and prompts — beyond tools

MCP exposes three primitive types: tools (model-initiated, side-effect-capable), **resources** (URI-addressable read-only data), and **prompts** (user-initiated workflow templates). Most servers ship only tools — and most servers should add resources or prompts if the workload calls for them. Cross-link `tools.md` for the model-initiated path; this file covers the other two.

The decision is not "tools vs resources vs prompts" in the abstract — it's "what does the agent need to do, and which primitive matches?" Resources are for browsable read-only context that should not consume context budget by default. Prompts are for repeatable workflows the user kicks off. Tools remain the default for everything actionable.

---

## Resources — URI-addressable read-only data

A resource is a piece of read-only data the client can fetch by URI. Unlike a tool call, the data is not pushed into context until the client (or the model, on capable clients) explicitly reads it. Resources are the right primitive for tool documentation, file contents, schemas, configuration, and anything else the agent might want **on demand** rather than **on every call**.

### When resources beat tools

- **Read-only and stable.** Documentation, schema definitions, config files, project files. If the right answer is "here's the data" with no parameters beyond a path, it's a resource.
- **Same data referenced from multiple places.** Tool descriptions can point at `docs://tools` rather than each repeating the schema in their description.
- **Caching matters.** Resources support ETags and the `resources/subscribe` notification flow — clients can cache and revalidate without re-reading.
- **The data is large.** A resource is fetched once, on demand. A tool that returns the same payload pollutes context every call.

### When tools win

- **The "read" has parameters beyond a URI.** Filtering, pagination, sorting, free-text search.
- **The data must be fetched dynamically.** Live metrics, real-time stock prices, computed views.
- **The model needs to choose when to read.** Tools fire on the model's reasoning; resources fire on user/client action (on most clients, anyway).

### How to expose a static resource

```python
from fastmcp import FastMCP
mcp = FastMCP("acme")

@mcp.resource("docs://tools")
def tool_docs() -> str:
    """Complete documentation for every tool in this server."""
    return Path("./docs/tools.md").read_text()

@mcp.resource("schema://invoice")
def invoice_schema() -> str:
    """JSON Schema for the invoice object."""
    return Path("./schemas/invoice.json").read_text()
```

A static URI maps to a function. The client lists resources via `resources/list`, reads via `resources/read`. The body is a `text` block (with `mimeType`) or `blob` (base64) — pick by content type.

### How to expose a resource template

When the URI carries variables, use a template. One definition serves many addresses:

```typescript
import { ResourceTemplate } from "@modelcontextprotocol/sdk/server/index.js";

server.registerResource(
  "recipes",
  new ResourceTemplate("recipe://{cuisine}/{name}", {
    list: undefined,                                              // not enumerable
    complete: {
      cuisine: (v) => CUISINES.filter((c) => c.startsWith(v)),    // tab-completion
      name:    (v) => listRecipesByPrefix(v),
    },
  }),
  { title: "Recipes", description: "Recipe by cuisine + name" },
  async (uri, vars) => {
    const cuisine = String(vars.cuisine);
    const name    = String(vars.name);
    if (!CUISINES.includes(cuisine)) {
      throw new Error(`Unknown cuisine "${cuisine}". Valid: ${CUISINES.join(", ")}`);
    }
    return {
      contents: [{
        uri: uri.href,
        mimeType: "text/markdown",
        text: await loadRecipe(cuisine, name),
      }],
    };
  },
);
```

The `complete` field powers autocomplete in clients that support it (VS Code's MCP extension, Cursor v1.6+). The `list` field is `undefined` because enumerating every recipe is wasteful; clients fetch by exact URI. Cross-link `client-compatibility.md` Pattern 1 — Claude Desktop and several other clients silently ignore resource templates as of 2026-02. Test on the target before committing.

### Pagination and large resources

If a resource exceeds ~25,000 tokens, paginate via URI parameters. Encode `?page=N` or `?cursor=X` in the URI. The MCP spec does not bake pagination into resources — you implement it via the URI path or query. Keep page size small (≤5,000 tokens) so clients can revalidate cheaply.

```typescript
new ResourceTemplate("logs://{service}/{date}/{page}", { list: undefined });
```

### Caching and content types

Always set `mimeType` correctly: `text/plain`, `text/markdown`, `application/json`, `image/png`, `application/pdf`. Clients use it to decide rendering. Set `Content-Type` headers on HTTP transports to match. Long-lived resources should advertise an `etag` in `_meta`; the client can revalidate via `resources/read` with `If-None-Match` semantics where the protocol supports it. Subscribers (clients that support it) get `resources/updated` notifications when the underlying data changes — don't enable this for resources you can't push notifications for.

### The error-message-points-at-resource pattern

Reduce default context cost by leaving detailed docs in a resource and pointing tools at it on failure:

```python
@mcp.resource("docs://search")
def search_docs() -> str:
    return DETAILED_USAGE_AND_EDGE_CASES

@mcp.tool(description="Search the knowledge base. See docs://search for query syntax.")
def search(query: str) -> dict:
    if not query.strip():
        return {
            "content": [{"type": "text",
                "text": "Query cannot be empty. See docs://search for valid query patterns."}],
            "isError": True,
        }
    # ...
```

Tools list stays lean. The model fetches `docs://search` only when something goes wrong. Practitioners report 90%+ first-call success on this pattern; the resource is touched only on the rare failure. Test on the target client — on clients that don't auto-fetch resources, the model still has to ask for it explicitly.

**Source:** [MCP spec — resources](https://modelcontextprotocol.io/specification/2025-11-25/server/resources); [u/kiedi5 on r/mcp](https://reddit.com/r/mcp) — "Does anyone use MCP prompts or resources?" (2025).

---

## Prompts — user-initiated workflow templates

A prompt is a server-defined template that the **user** triggers, typically from a slash-menu or palette in the client. The client fills in arguments, the server returns a list of messages (often combining instructions, parameters, and embedded resources), and the client injects them into the conversation as if the user typed them. Prompts solve "I keep typing the same complex instruction."

### When prompts beat tools

- **The user is the trigger.** "Run a code review on this file" — the user picks the prompt, not the model.
- **The workflow is repeatable and parameterized.** Bug-analysis, code-review, refactor-with-tests, scaffold-new-component.
- **The prompt embeds resources or canned instructions** the user shouldn't have to assemble.

### When tools win

- **The model decides when to call.** Search, fetch, lookup — these belong as tools.
- **The action has side effects.** Prompts are read-only injection; tools are how you write.
- **Frequent invocation.** Prompts are slow to invoke (user must pick from a menu); tools fire automatically.

### How to expose a prompt

```python
from fastmcp import FastMCP
mcp = FastMCP("dev-tools")

@mcp.prompt
def analyze_bug(error_message: str, file_path: str, severity: str = "medium") -> list[dict]:
    """Structured bug analysis. Embeds the file as a resource alongside instructions."""
    return [
        {
            "role": "user",
            "content": {
                "type": "text",
                "text": (
                    f"Analyze this bug systematically.\n"
                    f"Error: {error_message}\n"
                    f"File: {file_path}\n"
                    f"Severity: {severity}\n\n"
                    f"1. Identify the root cause.\n"
                    f"2. Check for related issues in nearby code.\n"
                    f"3. Propose a fix with test cases.\n"
                    f"4. Assess the risk of the fix."
                ),
            },
        },
        {
            "role": "user",
            "content": {
                "type": "resource",
                "resource": { "uri": f"file://{file_path}", "mimeType": "text/plain" },
            },
        },
    ]
```

The client lists prompts via `prompts/list`, fetches a filled instance via `prompts/get`. The user invokes by name (Claude Code: `/mcp__dev-tools__analyze_bug`; VS Code: `/mcp.dev-tools.analyze_bug`; Goose: agent panel; client conventions vary).

### Prompt argument constraints

Cross-link `client-compatibility.md` Pattern 3: **Zed silently drops any prompt with more than one argument.** Collapse multi-argument prompts to a single JSON-string payload if Zed support matters:

```python
@mcp.prompt
def code_review(payload: str) -> list[dict]:
    """payload is a JSON string: {"path": "...", "language": "...", "strict": true}"""
    args = json.loads(payload)
    # ...
```

Most other clients (Claude Desktop, Claude Code, Cursor, Continue, VS Code, Goose) accept multi-argument prompts. Test on the target.

### Common prompt shapes

- **`/explain` workflow** — embeds the relevant source file, asks for a step-through explanation tuned to a stated reader level.
- **`/refactor` workflow** — takes target file + goal, embeds related files via `roots/list`, primes the model with the project's coding standards from `docs://style`.
- **`/scaffold` workflow** — creates a new module from a template, parameterized by name and type.
- **`/test` workflow** — embeds the target file and any test fixtures, asks for unit tests in the project's preferred framework.

### Persistence limits

Most clients do not persist filled-in prompt arguments across sessions as of 2026-02. Claude Desktop supports prompts but cannot save the parameter values; the user re-fills each time. Treat prompts as one-shot, not as saved configurations. Cross-link `client-compatibility.md` for the per-client matrix.

**Source:** [MCP spec — prompts](https://modelcontextprotocol.io/specification/2025-11-25/server/prompts); [u/mettavestor on r/mcp](https://reddit.com/r/mcp) — "I integrated prompts in my sequential thinking MCP designed for coding" (2025).

---

## Tool vs resource vs prompt — the decision rubric

Pick the primitive based on three questions, in this order.

**1. Who is the trigger?**

| Trigger | Primitive |
|---|---|
| Model decides | **Tool** |
| User picks from a menu | **Prompt** |
| Client reads on demand (or user attaches via UI) | **Resource** |

**2. Are there side effects?**

| Side effects | Primitive |
|---|---|
| Yes (writes, sends, deletes) | **Tool** (gates if needed — see `prompt-gates.md`) |
| No (data lookup) | **Resource** if URI-addressable; else **Tool** with `readOnlyHint: true` |
| No (instruction injection) | **Prompt** |

**3. What's the input shape?**

| Input | Primitive |
|---|---|
| Complex parameters (filters, pagination, free-text search) | **Tool** |
| URI path / query variables only | **Resource** (template) |
| Stable user-facing argument list | **Prompt** |

### Worked examples

| Workload | Best primitive | Why |
|---|---|---|
| `search_invoices(filters, page, cursor)` | **Tool** | Complex parameters, model picks when to call |
| `docs://api/v2/customer` | **Resource** | Stable URL, no parameters, browsable, large |
| `recipe://{cuisine}/{name}` | **Resource template** | URI-shaped lookup, autocomplete useful |
| `delete_environment(env_id, approval_token)` | **Tool** (gated) | Side effect, model-initiated, requires gate |
| `/code-review file=X strict=true` | **Prompt** | User-initiated, repeatable, embeds the file |
| `live_metrics(service)` | **Tool** | Live data, model picks when to refresh |
| `project://standards.md` | **Resource** | Read-only, referenced from many tool descriptions |
| `/scaffold-component name=Button` | **Prompt** | User decides to start, parameterized |

### The hybrid pattern

When data is browsable AND queryable, expose both:

```python
# Resource: browse one customer by ID
@mcp.resource("customers://{customer_id}")
def get_customer(customer_id: str) -> str: ...

# Tool: search across customers with filters and pagination
@mcp.tool(description="Search customers by name, email, or status.")
def search_customers(query: str, status: str = "active", limit: int = 10) -> dict: ...
```

The agent uses `search_customers` for discovery, then reads `customers://abc-123` for details. Resource keeps the per-record context cost low; the tool handles the parameterized case.

### The community reality check

Most production MCP servers ship tools only — partly because client support for resources and prompts is uneven (cross-link `client-compatibility.md`). If portability matters more than ergonomics, default to tools and add resources/prompts as a nice-to-have after verifying the target clients support them. The compatibility matrix is the limiting factor: Claude Desktop supports static resources but ignores templates; Zed has no resources at all; Cline ignores resources and most prompts.

For a multi-client deployment, the safest path:

1. Tools that work everywhere — the must-have surface.
2. Static resources for documentation referenced from error messages — works on most clients, degrades gracefully on the rest.
3. Prompts only when the user-initiated UX is the point — and test on the target before committing.

---

## Cross-references

- `tools.md` — model-initiated tools, the most-used primitive, with full design and response patterns.
- `client-compatibility.md` — per-client support for resources, prompts, templates, completions, subscriptions.
- `progressive-discovery.md` — using resources to keep tool descriptions lean while still surfacing detail on demand.
- `agentic-patterns.md` — the OpenAPI-with-resources pattern for very large APIs.
- `../decision-trees/tool-count.md` — when to consolidate tools vs split them; resources can absorb some of the surface a tool would otherwise occupy.
