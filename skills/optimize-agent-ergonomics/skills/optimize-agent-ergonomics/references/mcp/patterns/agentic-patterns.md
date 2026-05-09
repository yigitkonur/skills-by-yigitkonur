# Agentic patterns and tool composition

Multi-step agent workflows succeed or fail on two dimensions: how each tool steers the next step (agentic patterns), and how independent tools combine into reliable pipelines (composition). This file covers both. Cross-surface universal concepts — "submit → validate → repair → resubmit" — live in `../../common/iterative-loops.md`. This file is the MCP-specific deep dive: structural enforcement, HATEOAS responses, sampling-vs-elicitation gates, gateway architectures, and the rule that tools should not call other tools server-side.

---

## Agentic patterns

### Parameter dependency chains

Force tools to be called in the correct sequence by requiring outputs from earlier tools as mandatory inputs to later ones. This turns implicit ordering into a structural constraint enforced by the schema, not by documentation.

Without this, an agent may skip steps or call `deploy_service` before `run_tests`. With it, the server issues a schema validation error if the prerequisite token is absent — making the shortcut impossible.

```typescript
// Step 1: run_tests returns a signed token
server.tool("run_tests", "Run test suite. Returns test_token required for deployment.", {
  suite: z.string(),
}, async ({ suite }) => {
  const results = await runTestSuite(suite);
  if (results.failed > 0) {
    return { content: [{ type: "text", text: `Tests failed: ${results.failed} failures` }], isError: true };
  }
  const testToken = sign({ suite, passed: true, ts: Date.now() }, process.env.TOKEN_SECRET!);
  return {
    content: [{
      type: "text",
      text: `All ${results.passed} tests passed.\ntest_token: ${testToken}\n\nNow call deploy_service with this test_token.`,
    }],
  };
});

// Step 2: deploy_service REQUIRES the token from step 1
server.tool("deploy_service", "Deploy to production. Requires test_token from run_tests.", {
  service_name: z.string(),
  environment:  z.enum(["staging", "production"]),
  test_token:   z.string().describe("Token returned by run_tests. Required."),
}, async ({ service_name, environment, test_token }) => {
  const payload = verify(test_token, process.env.TOKEN_SECRET!);
  if (!payload?.passed) {
    return { content: [{ type: "text", text: "Invalid test_token. Run run_tests first." }], isError: true };
  }
  await deployService(service_name, environment);
  return { content: [{ type: "text", text: `Deployed ${service_name} to ${environment}.` }] };
});
```

A description saying "call run_tests before deploy" relies on the model reading and following instructions. A required `test_token` parameter makes skipping structurally impossible — the call fails schema validation before the handler runs. Use this for production-modifying workflows.

### HATEOAS — state-based available actions

Include a dynamic `_available_actions` field in every tool response, computed from the current resource state. The LLM learns what it can do next by reading the response, not by guessing or consulting documentation.

```typescript
type Action = { tool: string; description: string; required_params?: string[] };

function getAvailableActions(deployment: Deployment): Action[] {
  if (deployment.status === "running") {
    return [
      { tool: "get_metrics", description: "View live metrics", required_params: ["deployment_id"] },
      { tool: "rollback_deployment", description: "Roll back to previous version", required_params: ["deployment_id"] },
      { tool: "scale_deployment", description: "Adjust instance count", required_params: ["deployment_id", "replicas"] },
    ];
  }
  if (deployment.status === "failed") {
    return [
      { tool: "get_logs", description: "Inspect failure logs", required_params: ["deployment_id"] },
      { tool: "rollback_deployment", description: "Restore last known good version", required_params: ["deployment_id"] },
    ];
  }
  if (deployment.status === "stopped") {
    return [{ tool: "start_deployment", description: "Start the service", required_params: ["deployment_id"] }];
  }
  return [];
}

server.tool("get_deployment", "Get deployment status", {
  deployment_id: z.string(),
}, async ({ deployment_id }) => {
  const deployment = await fetchDeployment(deployment_id);
  return {
    content: [{
      type: "text",
      text: JSON.stringify({ ...deployment, _available_actions: getAvailableActions(deployment) }, null, 2),
    }],
  };
});
```

Actions are always accurate — they reflect actual current state, not theoretical capabilities. The agent never attempts an invalid state transition (scaling a stopped deployment), reduces the need for a "what can I do?" discovery tool, and works without system-prompt context about the workflow.

### Guard tools — precondition validation via boolean params

Add boolean precondition parameters to destructive tools. The agent must affirm preconditions before the server proceeds. Unlike a confirmation dialog (which delays), guard params shift **responsibility** — the agent declares preconditions verified, and the server can optionally re-check.

```typescript
server.tool(
  "delete_environment",
  "Permanently delete an environment. Set tests_verified=true only after running validate_environment. Set backup_confirmed=true only after create_backup completes.",
  {
    environment_id: z.string(),
    tests_verified: z.boolean().describe("Set true only after validate_environment returned no critical errors."),
    backup_confirmed: z.boolean().describe("Set true only after create_backup returned a valid backup_id."),
    backup_id: z.string().optional().describe("backup_id from create_backup. Required when backup_confirmed=true."),
  },
  async ({ environment_id, tests_verified, backup_confirmed, backup_id }) => {
    if (!tests_verified) {
      return { content: [{ type: "text", text: "Blocked: tests_verified=false. Run validate_environment first." }], isError: true };
    }
    if (!backup_confirmed || !backup_id) {
      return { content: [{ type: "text", text: "Blocked: backup_confirmed=false or backup_id missing. Run create_backup first." }], isError: true };
    }
    const backupValid = await verifyBackupExists(backup_id);
    if (!backupValid) {
      return { content: [{ type: "text", text: `Blocked: backup_id "${backup_id}" not found or expired.` }], isError: true };
    }
    await deleteEnvironment(environment_id);
    return { content: [{ type: "text", text: `Environment ${environment_id} deleted.` }] };
  },
);
```

Layered trust:
- **Soft guard** — boolean params; agent self-reports; server accepts on good faith
- **Medium guard** — server checks a signed token / ID from a prerequisite tool (parameter dependency chain)
- **Hard guard** — server independently re-runs the precondition check before executing

Match the layer to the stakes. Destructive cloud operations warrant a hard guard.

### Server-enforced workflow stages

Maintain a `WorkflowStage` enum on the server and reject calls that arrive out of sequence. This differs from prompt-based guidance (which uses response text to *guide*) — here the server *blocks* out-of-order calls with an error.

```typescript
type WorkflowStage = "initialized" | "data_loaded" | "analysis_complete" | "changes_validated" | "committed";

const STAGE_ORDER: WorkflowStage[] = ["initialized", "data_loaded", "analysis_complete", "changes_validated", "committed"];
const sessions = new Map<string, WorkflowStage>();

const stageToTool: Record<WorkflowStage, string> = {
  initialized: "load_data",
  data_loaded: "analyze_data",
  analysis_complete: "validate_changes",
  changes_validated: "commit_changes",
  committed: "(workflow complete)",
};

function assertStage(sessionId: string, allowedPrevious: WorkflowStage[]) {
  const current = sessions.get(sessionId) ?? "initialized";
  if (!allowedPrevious.includes(current)) {
    const next = STAGE_ORDER[STAGE_ORDER.indexOf(current) + 1];
    throw {
      message: `Stage gate: current stage is "${current}". Must complete "${next}" first.`,
      current_stage: current,
      next_required_tool: stageToTool[next],
    };
  }
}

server.tool("commit_changes", "Commit validated changes. Requires changes_validated stage.", {
  session_id: z.string(),
  dry_run: z.boolean().default(false),
}, async ({ session_id, dry_run }) => {
  try {
    assertStage(session_id, ["changes_validated"]);
  } catch (e: any) {
    return { content: [{ type: "text", text: JSON.stringify(e) }], isError: true };
  }
  const result = await commitChanges(session_id, dry_run);
  sessions.set(session_id, "committed");
  return { content: [{ type: "text", text: `Changes committed. ${result.summary}` }] };
});
```

Documentation and prompt guidance are suggestions; stage gates are enforcement. For consequential workflows (deployments, financial operations, data migrations), server-side stage enforcement is the only reliable safeguard. See `session-and-state.md` for how to persist the stage map across reconnects.

### When to use sampling vs elicitation vs prompt-gates

Three distinct mechanisms for human-in-the-loop. Pick the right one.

| Mechanism | Use when | Key constraint |
|---|---|---|
| **Sampling** (`sampling/createMessage`) | The server needs LLM reasoning mid-execution and you don't want to ship an API key | Most clients ignore this — capability-check first |
| **Elicitation form-mode** (`elicitation/create`) | Clarify a missing argument, confirm an irreversible action, gather progressive input | Flat objects only; never for passwords/SSN/credentials (spec MUST-NOT) |
| **Elicitation URL-mode** | OAuth flows, payment confirmation, secret entry — secrets the LLM must not see | Requires `elicitation.url` capability; only VS Code Insiders had it as of 2025-12 |
| **Prompt-gate** (your own tool returns `requires_approval: true`) | Human confirmation in a workflow without depending on advanced protocol features | Always works; minimal client coupling |

See `prompt-gates.md` for the prompt-gate pattern. See `advanced-protocol.md` for sampling and elicitation deep dives. Always degrade gracefully when a capability is missing — a server that crashes on unsupported clients is worse than a server that announces "this client doesn't support sampling, please summarize manually."

### SERF — machine-readable error taxonomy

Return errors in a structured, machine-readable format with a fixed taxonomy so the LLM can programmatically decide whether to retry, switch tools, escalate, or stop — rather than parsing free-text. See `error-handling.md` for the full implementation; the agentic point is that an agent loop needs `retryable: true|false` to make the next decision.

```typescript
return {
  content: [{ type: "text", text: JSON.stringify({
    error_category: "RATE_LIMITED",
    message: "GitHub API rate limit exceeded",
    retryable: true,
    retry_after_ms: 60_000,
    suggested_actions: ["wait_60s_then_retry"],
  })}],
  isError: true,
};
```

### Shared context — append-only event log for multi-agent coordination

Multiple agents sharing one MCP server need a coordination mechanism that avoids last-write-wins conflicts and preserves history. An append-only event log is the simplest primitive that gives both. Locks introduce deadlock risk; the log sidesteps both — agents only write new entries, never update old ones.

```typescript
interface LogEntry {
  id: string;
  agent_id: string;
  timestamp: string;
  type: "observation" | "decision" | "action" | "result" | "handoff";
  payload: unknown;
  confidence?: number;
  supersedes?: string;
}

const eventLog: LogEntry[] = []; // replace with Redis or Postgres for persistence

server.tool("log_event", "Append an event to the shared coordination log", {
  agent_id: z.string(),
  type: z.enum(["observation", "decision", "action", "result", "handoff"]),
  payload: z.unknown(),
  confidence: z.number().min(0).max(1).optional(),
  supersedes: z.string().optional(),
}, async (input) => {
  const entry: LogEntry = { id: crypto.randomUUID(), timestamp: new Date().toISOString(), ...input };
  eventLog.push(entry);
  return { content: [{ type: "text", text: `Logged event ${entry.id}` }] };
});

server.tool("read_log", "Read shared coordination log, optionally filtered", {
  since: z.string().optional(),
  agent_id: z.string().optional(),
  type: z.string().optional(),
  limit: z.number().default(50),
}, async ({ since, agent_id, type, limit }) => {
  let entries = eventLog;
  if (since) entries = entries.filter(e => e.timestamp > since);
  if (agent_id) entries = entries.filter(e => e.agent_id === agent_id);
  if (type) entries = entries.filter(e => e.type === type);
  return { content: [{ type: "text", text: JSON.stringify(entries.slice(-limit), null, 2) }] };
});
```

Coordination pattern: each agent calls `read_log` at session start to understand prior work, and `log_event(type: "handoff")` when passing work to another agent. The `supersedes` field allows a correction entry without erasing history.

### Bounded server-side continuation for research loops

For open-ended research, search, and SEO workflows, the server can spend a small internal planning budget deciding what the next search wave should be. This is an advanced pattern — the default still favors explicit, transparent tool boundaries. But when the workflow is **read-only, repetitive, and frontier-building**, a bounded internal planner can outperform "return raw SERP and hope the agent figures out the next 12 queries."

```typescript
server.tool("research_serp", "Search the web and return the current frontier for deeper research.", {
  query: z.string(),
  continuation_mode: z.enum(["none", "suggest", "prefetch"]).default("suggest"),
  max_followups: z.number().min(1).max(5).default(3),
}, async ({ query, continuation_mode, max_followups }) => {
  const serp = await searchWeb(query, 10);
  const planner = await internalModel.planNextSearchWave({
    seedQuery: query,
    currentResults: serp,
    goals: ["find missing search intents", "increase source diversity"],
    maxQueries: max_followups,
  });
  const prefetched = continuation_mode === "prefetch"
    ? await Promise.all(planner.recommended_queries.map(q => searchWeb(q.query, 5)))
    : [];
  return {
    structuredContent: {
      seed_query: query,
      summary: planner.summary,
      results: serp,
      coverage_gaps: planner.coverage_gaps,
      recommended_next_queries: planner.recommended_queries,
      server_actions_taken: [
        { type: "internal_planner_turn", purpose: "derive next-search frontier" },
        ...(continuation_mode === "prefetch" ? [{ type: "prefetch_followup_searches", count: prefetched.length }] : []),
      ],
      prefetched_results: prefetched,
      stop_conditions: [
        "Stop if next wave adds <2 novel high-quality domains.",
        "Stop if two consecutive waves target the same intent with no new evidence.",
      ],
    },
    content: [{ type: "text", text: JSON.stringify({ summary: planner.summary, recommended_next_queries: planner.recommended_queries }, null, 2) }],
  };
});
```

**Safe operating rules:** read-only or low-risk only. Bound with hard caps (max waves, max searches, max spend, max wall-clock). Always emit `server_actions_taken`, `budget_remaining`, `stop_conditions`. Never hide irreversible external actions behind an internal planner. Evaluate with transcripts before claiming it's better.

---

## Tool composition

### The "tools should not call other tools server-side" rule

The MCP composition rule that shapes everything else: a tool's handler should **not** invoke another tool. Composition happens through the agent.

Why this matters:
- The agent maintains the audit trail. If tool A silently calls tool B, B's invocation never appears in the agent's transcript — the user sees the effect without seeing the cause.
- Permission decisions are per-call. If the user has approved A but not B, server-side B-from-A bypasses consent.
- Failure handling diverges. The agent's loop knows how to recover from B failing as a top-level call; B failing inside A's handler turns into a generic error.
- Caching, rate limits, and observability are all keyed on tool calls. Hidden calls bypass all of it.

Instead, return a `next_action` (or `_available_actions` per HATEOAS) pointing at the next tool. The agent calls it explicitly. Composition is *declared* in the response, *executed* by the agent.

There's a narrow exception — bounded read-only internal continuation (the research-loop pattern above). Treat it as the exception, never the default. Disclose every internal action in `server_actions_taken`.

### Composition vs orchestration

| | Composition | Orchestration |
|---|---|---|
| Driver | The model | The server |
| Mechanism | `next_action` / HATEOAS hints | Tool A calls tool B |
| Transparency | Every step in the agent transcript | Hidden inside one transcript entry |
| Auth | Per-call user approval | Server's own credentials |
| Recovery | Agent loop handles failure | Server-internal exception |
| MCP-canonical | Yes | Anti-pattern (with the read-only exception above) |

Compose. Don't orchestrate.

### Use a meta-server for cross-cutting concerns

When running multiple MCP servers, don't duplicate auth, rate limiting, and logging in each. Build a lightweight meta-server (gateway) that handles cross-cutting concerns and delegates to domain-specific servers.

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

    async def handle_tool_call(self, tool_name: str, args: dict, ctx):
        for mw in self.middleware:
            await mw.before(tool_name, args, ctx)
        server_name = tool_name.split("_")[0]  # "github" from "github_create_pr"
        result = await self.servers[server_name].call_tool(tool_name, args)
        for mw in reversed(self.middleware):
            result = await mw.after(tool_name, result, ctx)
        return result
```

What the gateway handles: authentication, authorization, rate limiting, audit logging, response transformation (namespacing, sensitive-field filtering). Also enables lazy loading of backend servers, failover between redundant instances, version routing, and per-session tool visibility.

FastMCP 3.0 namespace mounting:

```python
mcp = FastMCP("Gateway")
mcp.mount(github_server, namespace="github")
mcp.mount(jira_server,   namespace="jira")
mcp.mount(slack_server,  namespace="slack")
mcp.add_transform(AuthMiddleware(tag="all", scopes={"authenticated"}))
```

### Design composable servers the LLM orchestrates

Each MCP server should specialize in one domain. Let the LLM orchestrate multi-server workflows — it's better at reasoning about workflow sequencing than any hardcoded router.

Example — threat modeling:

```
User: "Analyze the security of our new payment API"

LLM orchestration:
1. github_analyze(repo_url) → code structure + dependencies
2. threat_framework(app_description=…) → STRIDE analysis scaffold
3. (model assembles threat report from STRIDE + code structure)
4. create_jira_tickets(threats=[…]) → tracking
```

Server design for composability:

```python
@tool(description="Analyze a GitHub repository's structure, dependencies, and security-relevant patterns.")
def github_analyze(repo_url: str) -> dict:
    return {
        "description": "Payment processing API using Express.js with Stripe integration",
        "dependencies": [...],
        "identified_components": ["auth", "payment", "webhook_handler"],
        "next_steps": "Use threat_framework() with this description for security analysis.",
    }

@tool(description="Get STRIDE threat analysis framework data for an application.")
def threat_framework(app_description: str) -> dict:
    return {
        "stride_categories": {...},
        "context_analysis": analyze_app_context(app_description),
        "report_template": "Generate a threat report using the above framework.",
        "data_for_report": {...},
    }
```

Principles: each server exposes data and scaffolds (not finished outputs); responses include `next_steps` referencing OTHER servers' tools; data formats consumable by other tools as input; servers don't depend on each other directly — let the LLM chain them.

### Wrap complex APIs in one tool + resource documentation

For APIs with 30+ endpoints, expose a single flexible tool and use MCP resources to provide on-demand documentation. Tool count stays at 1 while still handling the full surface.

```python
@mcp.tool(description="Execute an API operation. Use resources at tool://{client}/{method} to see available methods and parameters.")
def api_call(client: str, method: str, params: dict = {}) -> dict:
    return get_client(client).call(method, **params)

@mcp.resource("tool://all")
def list_all_clients() -> str:
    return json.dumps({c.name: list(c.methods.keys()) for c in clients})

@mcp.resource("tool://{client}/{method}")
def get_method_docs(client: str, method: str) -> str:
    return get_client(client).get_method_docs(method)
```

Interaction: model calls `api_call` with a guess; if wrong, error says "see tool://all"; model reads the resource to discover the method; model reads the method's resource for parameters; model calls correctly. Resources aren't preemptively pushed to context — they're read on demand. See `resources-and-prompts.md` for resource patterns. Tradeoff: requires clients that support resource reading.

### Generate MCP servers from OpenAPI specs

If you already have a well-documented REST API, you don't need to hand-code each tool. Generate them. Notion's MCP server uses this — `MCPProxy` loads an OpenAPI spec and exposes every endpoint.

```typescript
import { MCPProxy } from "./proxy";

export async function initProxy(specPath: string, baseUrl?: string) {
  const openApiSpec = await loadOpenApiSpec(specPath, baseUrl);
  return new MCPProxy("Notion API", openApiSpec);
}
```

When to use: 20+ endpoints, well-maintained OpenAPI spec, want quick MCP access while iterating. Caveats: auto-generated descriptions inherit whatever's in your spec (often too terse for LLM consumption); 1-to-1 endpoint mapping creates tool sprawl — consolidate related endpoints (e.g., merge `GET /users/{id}`, `PATCH /users/{id}`, `DELETE /users/{id}` into `manage_user`). Use the proxy as a starting point, then refine high-traffic tools by hand.

### Gateway/proxy for multi-server orchestration

Multiple MCP servers create real operational problems: tool name collisions, idle-server resource waste, no unified discovery, cascading failures. A gateway proxy solves all of them by sitting between the client and your server fleet.

```typescript
const gateway = new MCPGateway({
  servers: [
    {
      name: "web", command: "npx", args: ["-y", "@anthropic/web-search-mcp"],
      lazy: true, idleTimeout: 120_000,
      healthCheck: { interval: 30_000, timeout: 5_000 },
    },
    {
      name: "db", command: "npx", args: ["-y", "postgres-mcp-server"],
      lazy: true, idleTimeout: 300_000, maxRetries: 3,
    },
  ],
  naming: "prefixed",  // web__search, db__query — prevents collisions
});
await gateway.start();
```

Existing solutions: **MCPJungle** (multi-server with prefixed naming + health checks), **MCPX** (discovery + installation), **MetaMCP** (control plane for fleets). Use when 3+ servers run simultaneously, names conflict, resource-constrained environments need lifecycle management, or production needs circuit breaking.

If you have 1-2 servers with no name conflicts, direct connections are simpler. Don't add a gateway for the sake of architecture.

### Zero-trust policy gateway

Wrap your server in a policy execution gateway that evaluates every tool call against a declarative policy before dispatch. The gateway validates permissions, enforces constraints, and signs job tickets — all without modifying individual tool handlers.

```typescript
import { createHmac } from "crypto";

interface Policy {
  allowed_tools: string[];
  per_tool: Record<string, {
    require_role?: string;
    require_context?: string[];
  }>;
}

class ExecutionGateway {
  private policy!: Policy;
  async init() { this.policy = JSON.parse(await fs.readFile("policy.json", "utf-8")); }

  async authorize(toolName: string, params: unknown, context: SessionContext): Promise<void> {
    if (!this.policy.allowed_tools.includes(toolName)) {
      throw new Error(`Tool "${toolName}" not in allowed_tools.`);
    }
    const rule = this.policy.per_tool[toolName];
    if (rule?.require_role && context.role !== rule.require_role) {
      throw new Error(`Tool "${toolName}" requires role "${rule.require_role}".`);
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
```

`policy.json`:

```json
{
  "allowed_tools": ["read_file", "list_directory", "create_issue", "deploy_staging"],
  "per_tool": {
    "deploy_staging": {"require_role": "deployer", "require_context": ["project_id", "branch"]},
    "create_issue":   {"require_context": ["github_token"]}
  }
}
```

A centralized policy gateway decouples authorization from tool handlers, allows policy changes without code deployments, and provides a tamper-evident audit trail. See `security.md` for input/output sanitization and `auth-identity.md` for the OAuth wiring underneath.

### FastMCP Provider + Transform

FastMCP 3.0 introduces a composable architecture where Providers source components and Transforms modify their behavior.

| Concept | Description | Example |
|---|---|---|
| **Component** | Atomic unit (Tool, Resource, Prompt) | `search_contacts` tool |
| **Provider** | Sources components from anywhere | Decorators, filesystem, OpenAPI, remote MCP |
| **Transform** | Modifies Provider behavior | Rename, namespace, filter, gate, version |
| **Composition** | Combine Providers + Transforms | Mount sub-servers, proxy remote tools |

```python
# Local
@tool
def my_tool(): ...

# From a directory
admin_provider = FileSystemProvider("./admin_tools", reload=True)

# From OpenAPI
api_provider = OpenAPIProvider("https://api.example.com/openapi.json")

# From a remote MCP
remote_provider = MCPClientProvider("https://remote-mcp.example.com")

# Transform examples
mcp.mount(github_provider, prefix="github")             # github_create_pr, github_list_repos
mcp.add_transform(VersionFilter(select="latest"))
mcp.add_transform(AuthGate(tags={"admin"}, scopes={"super-user"}))
mcp.add_transform(RenameTransform({"old_name": "new_name"}))
```

The Playbook pattern composes Providers, Visibility, Auth, and Session State into multi-step workflows: user authenticates → `unlock_admin_mode` updates session state → admin tools become visible (Visibility Transform) → subsequent calls use the new tools. Replaces ad-hoc glue code with declarative primitives.

---

## Cross-references

- `../../common/iterative-loops.md` — universal submit → validate → repair concepts
- `session-and-state.md` — persisting workflow stage maps and session context
- `prompt-gates.md` — the prompt-gate human-in-the-loop pattern
- `advanced-protocol.md` — sampling, elicitation, roots, cancellation
- `error-handling.md` — SERF taxonomy, isError mechanics
- `tools.md` — tool design, descriptions, response shapes
- `security.md` — sanitization, sandbox, audit
- `auth-identity.md` — OAuth 2.1, OBO, step-up consent
