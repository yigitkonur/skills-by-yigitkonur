# Composition Patterns

7 patterns for combining multiple MCP servers, building gateways, and creating composable server architectures.

---

## 1. Use a Meta-Server for Cross-Cutting Concerns

When running multiple MCP servers, don't duplicate auth, rate limiting, and logging in each one. Build a lightweight meta-server (gateway) that handles cross-cutting concerns and delegates to domain-specific servers.

```python
class MCPGateway:
    def __init__(self):
        self.servers = {}  # name -> MCP server connection
        self.middleware = [
            AuthMiddleware(),
            RateLimitMiddleware(max_requests=100, window_seconds=60),
            AuditLogMiddleware(),
        ]

    def register(self, name: str, server_config: dict):
        self.servers[name] = connect_mcp_server(server_config)

    async def handle_tool_call(self, tool_name: str, args: dict, ctx: Context):
        # Run middleware chain
        for mw in self.middleware:
            await mw.before(tool_name, args, ctx)

        # Route to correct server based on namespace
        server_name = tool_name.split("_")[0]  # e.g., "github" from "github_create_pr"
        server = self.servers[server_name]

        result = await server.call_tool(tool_name, args)

        for mw in reversed(self.middleware):
            result = await mw.after(tool_name, result, ctx)

        return result
```

**What the gateway handles:**
- **Authentication**: Verify user tokens before forwarding
- **Authorization**: Check per-tool permissions
- **Rate limiting**: Prevent abuse across all backend servers
- **Audit logging**: Single log stream for all tool calls
- **Response transformation**: Namespace tool names, filter sensitive fields

**FastMCP 3.0 approach:**
```python
mcp = FastMCP("Gateway")

# Mount sub-servers with namespace transforms
mcp.mount(github_server, namespace="github")
mcp.mount(jira_server, namespace="jira")
mcp.mount(slack_server, namespace="slack")

# Apply cross-cutting middleware
mcp.add_transform(AuthMiddleware(tag="all", scopes={"authenticated"}))
```

**The gateway pattern also enables:**
- Lazy loading of backend servers (only connect when first tool is called)
- Failover between redundant server instances
- Version routing (send 20% of traffic to v2)
- Tool visibility control per user/session

**Source:** [NearForm — Implementing MCP](https://nearform.com/digital-community/implementing-model-context-protocol-mcp-tips-tricks-and-pitfalls/); [FastMCP 3.0 blog](https://jlowin.dev/blog/fastmcp-3); [MCP specification](https://modelcontextprotocol.io)

---

## 2. Design Composable Servers That the LLM Orchestrates

Each MCP server should specialize in one domain. Let the LLM orchestrate multi-server workflows -- it's better at reasoning about workflow sequencing than any hardcoded router.

**Example: Threat Modeling Workflow**
```
User: "Analyze the security of our new payment API"

LLM orchestration:
1. Calls github_analyze(repo_url) → gets code structure, dependencies
2. Calls threat_framework(app_description=github_result.description) → gets STRIDE analysis scaffold
3. Uses the STRIDE data to generate a threat report
4. Calls create_jira_tickets(threats=identified_threats) → creates tracking tickets
```

**Server design for composability:**
```python
# Server 1: GitHub Analysis
@tool(description="Analyze a GitHub repository's structure, dependencies, and security-relevant patterns.")
def github_analyze(repo_url: str) -> dict:
    return {
        "description": "Payment processing API using Express.js with Stripe integration",
        "dependencies": [...],
        "identified_components": ["auth", "payment", "webhook_handler"],
        "next_steps": "Use threat_framework() with this description for security analysis."
    }

# Server 2: STRIDE Threat Framework
@tool(description="Get STRIDE threat analysis framework data for an application.")
def threat_framework(app_description: str) -> dict:
    return {
        "stride_categories": {...},
        "context_analysis": analyze_app_context(app_description),
        "report_template": "Generate a threat report using the above framework.",
        "data_for_report": {...}  # Raw data for LLM assembly
    }
```

**Key principles for composability:**
1. Each server exposes **data and scaffolds**, not finished outputs
2. Responses include `next_steps` that reference tools from OTHER servers
3. Return data in formats that other tools can consume as input
4. Don't make servers depend on each other directly -- let the LLM chain them

**Source:** [Matt Adams — MCP Server Design Principles](https://matt-adams.co.uk/2025/08/30/mcp-design-principles.html); [u/glassBeadCheney on r/mcp](https://reddit.com/r/mcp)

---

## 3. Wrap Complex APIs in One Tool + Resource Documentation

For APIs with 30+ endpoints, expose a single flexible tool and use MCP resources to provide on-demand documentation. This keeps the tool count at 1 while still handling the full API surface.

```python
@mcp.tool(description="Execute an API operation. Use resources at tool://{client}/{method} to see available methods and parameters.")
def api_call(client: str, method: str, params: dict = {}) -> dict:
    """Single tool wrapping the entire API surface."""
    api_client = get_client(client)
    return api_client.call(method, **params)

@mcp.resource("tool://all")
def list_all_clients() -> str:
    """List all available API clients and their methods."""
    return json.dumps({c.name: list(c.methods.keys()) for c in clients})

@mcp.resource("tool://{client}/{method}")
def get_method_docs(client: str, method: str) -> str:
    """Detailed documentation for a specific API method."""
    return get_client(client).get_method_docs(method)

@mcp.resource("tool://{client}/{method}/{parameter}")
def get_parameter_docs(client: str, method: str, parameter: str) -> str:
    """Detailed docs for a specific parameter of a method."""
    return get_client(client).get_param_docs(method, parameter)
```

**How the interaction flows:**
1. Model calls `api_call` with a guess at the method
2. If wrong, error response says "See tool://all for available methods"
3. Model reads the resource to discover correct method name
4. Model reads `tool://{client}/{method}` for parameter documentation
5. Model calls `api_call` correctly

Resources aren't preemptively pushed to context. The LLM reads them on-demand, so a seldom-used method with complex documentation doesn't waste tokens until it's actually needed.

**Trade-off:** Requires clients that support resource reading. Not all do. Test with your target client.

**Source:** [u/Dipseth on r/mcp](https://reddit.com/r/mcp)

---

## 4. Use the Provider + Transform Architecture for Maximum Flexibility

FastMCP 3.0 introduces a composable architecture where Providers source components and Transforms modify their behavior.

**Core concepts:**

| Concept | Description | Example |
|---------|-------------|---------|
| **Component** | Atomic unit (Tool, Resource, Prompt) | A `search_contacts` tool |
| **Provider** | Sources components from anywhere | Decorators, filesystem, OpenAPI spec, remote MCP |
| **Transform** | Modifies Provider behavior | Rename, namespace, filter, gate, version |
| **Composition** | Combine Providers + Transforms | Mount sub-servers, proxy remote tools |

**Provider types:**
```python
# Local functions
@tool
def my_tool(): ...

# From a directory of Python files
admin_provider = FileSystemProvider("./admin_tools", reload=True)

# From an OpenAPI spec
api_provider = OpenAPIProvider("https://api.example.com/openapi.json")

# From a remote MCP server
remote_provider = MCPClientProvider("https://remote-mcp.example.com")

# From instruction files (skills)
skills_provider = SkillsProvider("./skills/")
```

**Transform examples:**
```python
# Namespace all tools from a provider
mcp.mount(github_provider, prefix="github")
# Tools become: github_create_pr, github_list_repos, etc.

# Filter by version
mcp.add_transform(VersionFilter(select="latest"))

# Gate with authentication
mcp.add_transform(AuthGate(tags={"admin"}, scopes={"super-user"}))

# Rename for consistency
mcp.add_transform(RenameTransform({"old_name": "new_name"}))
```

**The Playbook pattern:** Compose Providers, Visibility, Auth, and Session State into multi-step workflows:
1. User authenticates
2. `unlock_admin_mode` updates session state
3. Admin tools become visible (Visibility Transform)
4. Subsequent calls use the newly available tools

This replaces ad-hoc glue code with declarative primitives.

**Source:** [FastMCP 3.0 blog](https://jlowin.dev/blog/fastmcp-3)

---

## 5. Generate MCP Servers from OpenAPI Specs

If you already have a well-documented REST API with an OpenAPI spec, you don't need to hand-code each MCP tool. Generate them. Notion's MCP server uses exactly this pattern -- it loads the OpenAPI spec and creates an `MCPProxy` that exposes every endpoint as a tool automatically.

```typescript
import { MCPProxy } from './proxy';

// Load spec and create proxy -- each endpoint becomes a tool
export async function initProxy(specPath: string, baseUrl?: string) {
  const openApiSpec = await loadOpenApiSpec(specPath, baseUrl);
  const proxy = new MCPProxy('Notion API', openApiSpec);
  return proxy;
}

// The proxy translates MCP tool calls into HTTP requests:
// tool("createPage", { parent: {...}, properties: {...} })
//   → POST /v1/pages { parent: {...}, properties: {...} }
//   → returns structured MCP response
```

**When to use this:**
- You have 20+ API endpoints and writing individual tools is tedious
- Your OpenAPI spec is accurate and well-maintained
- You want quick MCP access while iterating on the API itself

**Caveats:**
- Auto-generated tool descriptions inherit whatever's in your spec -- often too terse or too technical for LLM consumption
- One-to-one endpoint mapping creates tool sprawl. Consolidate related endpoints (e.g., merge `GET /users/{id}`, `PATCH /users/{id}`, `DELETE /users/{id}` into a single `manage_user` tool)
- Missing: semantic grouping, smart defaults, and context-aware parameter descriptions

**Recommended approach:** Use the proxy as a starting point, then iteratively refine the highest-traffic tools with hand-crafted descriptions:

```typescript
// After auto-generation, override specific tools for better LLM experience
proxy.overrideTool('search_pages', {
  description: 'Search Notion pages by title or content. Returns page IDs and titles.',
  parameters: {
    query: { type: 'string', description: 'Search text — matches titles and page content' },
    limit: { type: 'number', description: 'Max results (default: 10, max: 100)' }
  }
});
```

**Source:** [makenotion/notion-mcp-server](https://github.com/makenotion/notion-mcp-server)

---

## 6. Use a Gateway/Proxy for Multi-Server Orchestration

Running multiple MCP servers creates real operational problems: tool name collisions, resource waste from idle servers, no unified discovery, and cascading failures. A gateway proxy solves all of these by sitting between the client and your server fleet.

**What a gateway handles:** server-prefixed naming (`web__search`, `db__query`) to avoid collisions, on-demand server lifecycle, circuit breaking for unreachable servers, and unified `tools/list` across all servers.

```typescript
// Gateway configuration -- declare servers, let the gateway manage lifecycle
const gateway = new MCPGateway({
  servers: [
    {
      name: 'web',
      command: 'npx',
      args: ['-y', '@anthropic/web-search-mcp'],
      lazy: true,           // only start when a tool is called
      idleTimeout: 120_000, // stop after 2min of inactivity
      healthCheck: { interval: 30_000, timeout: 5_000 }
    },
    {
      name: 'db',
      command: 'npx',
      args: ['-y', 'postgres-mcp-server'],
      lazy: true,
      idleTimeout: 300_000,
      maxRetries: 3  // circuit breaker after 3 failures
    }
  ],
  naming: 'prefixed'  // web__search, db__query — prevents collisions
});

// Client sees one server with all tools
await gateway.start();
```

**Existing solutions:**
- **MCPJungle** -- Multi-server management with prefixed naming and health checks
- **MCPX** -- Discovery and installation tool for MCP servers
- **MetaMCP** -- Control plane for managing MCP server fleets

**When you need this:**
- 3+ MCP servers running simultaneously
- Tool names conflict across servers
- Resource-constrained environments where idle servers waste memory
- Production deployments needing circuit breaking and monitoring

**When you don't:** If you have 1-2 servers with no name conflicts, direct connections are simpler. Don't add a gateway for the sake of architecture.

**Source:** [MCPJungle](https://github.com/mcpjungle/MCPJungle); [MetaMCP](https://metamcp.com); [u/Rotemy-x10 on r/mcp](https://reddit.com/r/mcp)

---

## 7. Zero-Trust Policy Gateway

Wrap your MCP server in a policy execution gateway that evaluates every tool call against a declarative policy before dispatch. The gateway can validate permissions, enforce constraints, and sign job tickets -- all without modifying individual tool handlers.

**Architecture:**
```
LLM Client → Policy Gateway → Tool Handler
                   ↓
           policy.json (rules)
           HMAC ticket signing
           audit log
```

```typescript
import { createHmac } from "crypto";

interface Policy {
  allowed_tools: string[];
  per_tool: Record<string, {
    max_params?: Record<string, unknown>;
    require_context?: string[];  // Required session fields
    require_role?: string;
  }>;
}

async function loadPolicy(): Promise<Policy> {
  return JSON.parse(await fs.readFile("policy.json", "utf-8"));
}

class ExecutionGateway {
  private policy!: Policy;

  async init() { this.policy = await loadPolicy(); }

  async authorize(toolName: string, params: unknown, context: SessionContext): Promise<void> {
    if (!this.policy.allowed_tools.includes(toolName)) {
      throw new Error(`Tool "${toolName}" is not in the allowed_tools list.`);
    }

    const rule = this.policy.per_tool[toolName];
    if (rule?.require_role && context.role !== rule.require_role) {
      throw new Error(`Tool "${toolName}" requires role "${rule.require_role}". Current: "${context.role}".`);
    }
    if (rule?.require_context) {
      for (const field of rule.require_context) {
        if (!context[field]) throw new Error(`Missing required session context: ${field}`);
      }
    }
  }

  signJobTicket(toolName: string, params: unknown): string {
    const payload = JSON.stringify({ toolName, params, ts: Date.now() });
    return createHmac("sha256", process.env.GATEWAY_SECRET!).update(payload).digest("hex");
  }
}

// Wrap server dispatch
const gateway = new ExecutionGateway();
await gateway.init();

server.use(async (req, next) => {
  await gateway.authorize(req.tool, req.params, req.session);
  const ticket = gateway.signJobTicket(req.tool, req.params);
  auditLog.write({ ticket, ...req.session, tool: req.tool });
  return next();
});
```

**policy.json example:**
```json
{
  "allowed_tools": ["read_file", "list_directory", "create_issue", "deploy_staging"],
  "per_tool": {
    "deploy_staging": {
      "require_role": "deployer",
      "require_context": ["project_id", "branch"]
    },
    "create_issue": {
      "require_context": ["github_token"]
    }
  }
}
```

A centralized policy gateway decouples authorization logic from tool handlers, allows policy changes without code deployments, and provides a tamper-evident audit trail for all tool invocations.

**Source:** [Stacklok](https://stacklok.com) policy gateway pattern; zero-trust design principles for LLM tool execution
