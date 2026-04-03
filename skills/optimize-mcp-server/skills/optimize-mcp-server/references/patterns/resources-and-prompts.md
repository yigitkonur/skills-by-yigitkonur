# Resources and Prompts

Patterns for using MCP resources and prompts effectively. Resources provide URI-addressable read-only data; prompts provide user-triggered workflow templates. Together they complement tools by reducing token waste, enabling on-demand documentation, and creating repeatable workflow entry points.

---

## 1. Use Resources as On-Demand Documentation Referenced in Errors

Expose tool documentation as MCP resources, then reference them in error messages. The model fetches docs only when it needs help, keeping initial context lean.

```python
@mcp.resource("docs://tools")
def get_tool_docs() -> str:
    """Complete documentation for all tools, including examples and edge cases."""
    return Path("tool_documentation.md").read_text()

@mcp.tool(description="Search for contacts. See docs://tools for detailed usage.")
def search_contacts(query: str) -> dict:
    if not query.strip():
        return {
            "content": [{
                "type": "text",
                "text": "Query cannot be empty. See docs://tools for usage examples and valid query formats."
            }],
            "isError": True
        }
    # ...
```

**How this plays out:**
1. Initial context has only brief tool descriptions
2. Model calls tool correctly ~90% of the time with just the description
3. On failure, the error message references `docs://tools`
4. The model (or client) fetches the resource to get detailed guidance
5. Armed with full docs, the model retries successfully

**Real-world validation:** One practitioner put tool documentation in a markdown file exposed as a resource, then added "see docs://tools for more information" to error messages. "It seems to work really well and LLMs use the tools correctly more often now."

**Important nuance:** Not all clients automatically fetch resources. Some (like Goose) do; others may need the model to explicitly request it. Test with your target client.

**Source:** [u/kiedi5 on r/mcp](https://reddit.com/r/mcp) -- "Does anyone use MCP prompts or resources?" thread; u/emicklei confirmed the pattern works with syntax error recovery

---

## 2. Use Resource Templates with URI Patterns for Scalable Data Access

Instead of creating static resources for every data variant, use URI-based resource templates. One template definition serves hundreds of variants.

```typescript
server.registerResource(
  "recipes",
  new ResourceTemplate("file://recipes/{cuisine}", {
    list: undefined,
    complete: {
      cuisine: (value) => CUISINES.filter(c => c.startsWith(value)),
    },
  }),
  { title: "Cuisine-Specific Recipes", description: "Markdown recipes per cuisine" },
  async (uri, vars) => {
    const cuisine = vars.cuisine as string;
    if (!CUISINES.includes(cuisine)) {
      throw new Error(`Unknown cuisine: ${cuisine}. Valid: ${CUISINES.join(', ')}`);
    }
    return {
      contents: [{
        uri: uri.href,
        mimeType: "text/markdown",
        text: formatRecipesAsMarkdown(cuisine)
      }],
    };
  },
);
```

**Key features:**
- **URI pattern matching**: `file://recipes/{cuisine}` resolves dynamically
- **Completions**: Auto-suggest valid values when the user types (supported in VS Code MCP extension and some other clients)
- **Server-side validation**: Reject invalid values with clear errors
- **Single definition**: Handles Italian, Japanese, Mexican, etc. without separate resource registrations

**When resources beat tools for data access:**
- Data is read-only and changes infrequently
- Same data is referenced by multiple tools/prompts
- The data benefits from caching (resources support ETags)
- You want URI-addressable content for cross-server referencing

**When to use tools instead:** When the "read" has parameters beyond a URI path (complex filters, pagination, sorting).

**Source:** [MCP specification -- resources](https://modelcontextprotocol.io/specification/2025-11-25/server/resources); [modelcontextprotocol.io](https://modelcontextprotocol.io) resource templates documentation

---

## 3. Use MCP Prompts for Repeatable Workflow Entry Points

Prompts are user-controlled templates that combine instructions, parameters, and attached resources into a reusable workflow trigger. They solve the problem of "I keep typing the same complex instruction."

```python
@mcp.prompt
def analyze_bug(
    error_message: str,
    file_path: str,
    severity: str = "medium"
) -> list[dict]:
    """Structured bug analysis workflow with access to the relevant source file."""
    return [
        {
            "role": "user",
            "content": {
                "type": "text",
                "text": (
                    f"Analyze this bug systematically:\n"
                    f"Error: {error_message}\n"
                    f"File: {file_path}\n"
                    f"Severity: {severity}\n\n"
                    f"1. Identify the root cause\n"
                    f"2. Check for related issues in nearby code\n"
                    f"3. Propose a fix with test cases\n"
                    f"4. Assess risk of the fix"
                )
            }
        },
        {
            "role": "user",
            "content": {
                "type": "resource",
                "resource": {
                    "uri": f"file://{file_path}",
                    "mimeType": "text/plain"
                }
            }
        }
    ]
```

**Prompts vs tools:**
- **Prompts** are user-initiated (the user selects them from a menu)
- **Tools** are model-initiated (the model decides to call them)
- Prompts can embed resources directly, providing data alongside instructions
- Prompts act like "saved workflows" the user can trigger repeatedly

**Real-world uses:**
- Sequential thinking MCP with prompts for architecture design, bug analysis, refactoring
- Test generation prompts that include the source file as a resource
- Code review prompts with embedded style guides

**Current limitation:** Most clients do not fully support prompt template values persistence yet. Claude Desktop supports prompts but cannot persist saved parameter values across sessions.

**Source:** [u/mettavestor on r/mcp](https://reddit.com/r/mcp) -- "I integrated prompts in my sequential thinking MCP designed for coding"; [MCP specification -- prompts](https://modelcontextprotocol.io/specification/2025-11-25/server/prompts)

---

## 4. When to Use Resources vs Tools

Resources and tools are both data access mechanisms, but they serve different purposes. Picking the wrong one wastes tokens or limits functionality.

| Dimension | Resource | Tool |
|-----------|----------|------|
| **Trigger** | User/client-initiated | Model-initiated |
| **Mutability** | Read-only | Can read AND write |
| **Addressing** | URI-based (`file://docs/api.md`) | Name-based (`search_docs`) |
| **Parameters** | Only URI path variables | Full JSON Schema input |
| **Caching** | Supports ETags, subscriptions | Each call is independent |
| **Token cost** | Typically lower (focused data) | Higher (schema in context) |
| **Client support** | Inconsistent across clients | Universal |

**Use a resource when:**
- Data is read-only and does not change per-request
- Content is reused across multiple tool calls (e.g., documentation, config)
- You want URI-addressable content for cross-server references
- The data is >80% read-only (project files, schemas, templates)

**Use a tool when:**
- The operation has side effects (creates, updates, deletes)
- Parameters are complex (filters, pagination, sorting)
- The model needs to decide when to access the data
- You need arbitrary input validation beyond URI matching

**The hybrid pattern -- expose data as a resource for browsing, provide a tool for complex queries:**

```python
# Resource: simple access by ID
@mcp.resource("customers://{customer_id}")
def get_customer(customer_id: str): ...

# Tool: complex search with filters
@mcp.tool
def search_customers(query: str, status: str = "active", limit: int = 10): ...
```

**Community reality check:** Most builders only use tools because client support for resources is inconsistent. Resources work well in Goose and some clients but Claude Desktop/Code support is limited. If portability matters, default to tools and add resources as a nice-to-have.

**Source:** [u/Dipseth on r/mcp](https://reddit.com/r/mcp) -- uses resource templates for API documentation; [u/dankelleher on r/mcp](https://reddit.com/r/mcp) -- "Does anyone use MCP prompts or resources?" thread
