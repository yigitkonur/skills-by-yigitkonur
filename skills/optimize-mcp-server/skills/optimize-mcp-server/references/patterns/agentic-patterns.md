# Agentic Patterns

6 patterns for building reliable multi-step agent workflows with structural enforcement, state-based routing, and safe coordination between agents.

---

## 1. Parameter Dependency Chains

Force tools to be called in the correct sequence by requiring outputs from earlier tools as mandatory inputs to later ones. This turns implicit workflow ordering into a structural constraint enforced by the schema, not just by documentation.

Without this pattern, an agent may skip steps or call `deploy_service` before `run_tests`. With it, the server issues a schema validation error if the prerequisite token is absent -- making the shortcut impossible.

```typescript
// Step 1: run_tests returns a signed token
server.tool("run_tests", "Run test suite. Returns test_token required for deployment.", {
  suite: z.string(),
}, async ({ suite }) => {
  const results = await runTestSuite(suite);
  if (results.failed > 0) {
    return { content: [{ type: "text", text: `Tests failed: ${results.failed} failures` }], isError: true };
  }
  // Sign a token proving tests passed
  const testToken = sign({ suite, passed: true, ts: Date.now() }, process.env.TOKEN_SECRET!);
  return {
    content: [{ type: "text", text: `All ${results.passed} tests passed.\ntest_token: ${testToken}\n\nNow call deploy_service with this test_token.` }]
  };
});

// Step 2: deploy_service REQUIRES the token from step 1
server.tool("deploy_service", "Deploy to production. Requires test_token from run_tests.", {
  service_name: z.string(),
  environment: z.enum(["staging", "production"]),
  test_token: z.string().describe("Token returned by run_tests. Required."),
}, async ({ service_name, environment, test_token }) => {
  const payload = verify(test_token, process.env.TOKEN_SECRET!);
  if (!payload?.passed) {
    return { content: [{ type: "text", text: "Invalid test_token. Run run_tests first." }], isError: true };
  }
  await deployService(service_name, environment);
  return { content: [{ type: "text", text: `Deployed ${service_name} to ${environment}.` }] };
});
```

**Why it's better than documentation:** A description saying "call run_tests before deploy" relies on the model reading and following instructions. A required `test_token` parameter makes skipping structurally impossible -- the call will fail schema validation before the handler even runs.

Agentic workflows that modify production systems need hard ordering guarantees. Structural dependency chains are the only reliable way to enforce them across all LLMs.

**Source:** [MCP specification](https://modelcontextprotocol.io/specification/2025-11-25/server/tools); community patterns from [r/mcp](https://reddit.com/r/mcp)

---

## 2. HATEOAS: State-Based Available Actions

Include a dynamic `_available_actions` field in every tool response, computed from the current resource state. The LLM learns what it can do next by reading the response -- not by consulting documentation or guessing.

This is the HATEOAS (Hypermedia as the Engine of Application State) pattern adapted for LLM tool responses. Instead of hyperlinks, you return structured action descriptors.

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
    return [
      { tool: "start_deployment", description: "Start the service", required_params: ["deployment_id"] },
    ];
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
      text: JSON.stringify({
        ...deployment,
        _available_actions: getAvailableActions(deployment),
      }, null, 2)
    }]
  };
});
```

**Benefits over static documentation:**
- Actions are **always accurate** -- they reflect actual current state, not theoretical capabilities
- The agent never attempts an invalid state transition (e.g., scaling a stopped deployment)
- Reduces need for a "what can I do?" discovery tool
- Works without any system-prompt context about the workflow

Without HATEOAS, agents frequently call tools in invalid states and must parse error messages to understand what went wrong. With it, valid transitions are self-evident from the data.

**Source:** REST HATEOAS principle adapted for LLM tools; [Nordic APIs — HATEOAS: The API Design Style That Was Waiting for AI](https://nordicapis.com/hateoas-the-api-design-style-that-was-waiting-for-ai/); [r/mcp](https://reddit.com/r/mcp)

---

## 3. Guard Tools: Precondition Validation via Boolean Params

Add boolean precondition parameters to destructive tools. The agent must affirm these conditions before the server proceeds. Unlike confirmation dialogs (which just delay), guard params shift **responsibility** -- the agent is declaring that preconditions have been verified, and the server can optionally validate the claim.

```typescript
server.tool(
  "delete_environment",
  "Permanently delete a deployment environment. Set tests_verified=true only after running validate_environment. Set backup_confirmed=true only after create_backup completes.",
  {
    environment_id: z.string(),
    tests_verified: z.boolean()
      .describe("Set true only after validate_environment returned no critical errors."),
    backup_confirmed: z.boolean()
      .describe("Set true only after create_backup returned a valid backup_id."),
    backup_id: z.string().optional()
      .describe("The backup_id from create_backup. Required when backup_confirmed=true."),
  },
  async ({ environment_id, tests_verified, backup_confirmed, backup_id }) => {
    if (!tests_verified) {
      return {
        content: [{ type: "text", text: "Blocked: tests_verified is false. Run validate_environment first and confirm no critical errors." }],
        isError: true,
      };
    }
    if (!backup_confirmed || !backup_id) {
      return {
        content: [{ type: "text", text: "Blocked: backup_confirmed is false or backup_id is missing. Run create_backup first." }],
        isError: true,
      };
    }
    // Optionally: cryptographically verify the backup_id is genuine
    const backupValid = await verifyBackupExists(backup_id);
    if (!backupValid) {
      return {
        content: [{ type: "text", text: `Blocked: backup_id "${backup_id}" not found or expired. Re-run create_backup.` }],
        isError: true,
      };
    }

    await deleteEnvironment(environment_id);
    return { content: [{ type: "text", text: `Environment ${environment_id} deleted.` }] };
  }
);
```

**Layered trust model:**
- **Soft guard** -- boolean params in schema; agent self-reports; server accepts on good faith
- **Medium guard** -- server checks a signed token or ID from a prerequisite tool (see Pattern 1)
- **Hard guard** -- server independently re-runs the precondition check itself before executing

Choose the layer based on the stakes: a destructive cloud operation warrants a hard guard; a local file operation may only need soft.

Boolean guard params force the agent to explicitly acknowledge preconditions rather than rushing through a workflow. They produce audit-log evidence of what the agent claimed was true before a destructive action.

**Source:** Safety patterns discussed in [r/mcp](https://reddit.com/r/mcp); defense-in-depth principles for agentic tool execution

---

## 4. SERF: Machine-Readable Error Taxonomy for Agents

Return errors in a structured, machine-readable format with a fixed taxonomy so the LLM can programmatically decide whether to retry, switch tools, escalate, or stop -- rather than parsing free-text error messages.

The SERF framework (Structured Error Recovery Framework) was proposed in arXiv:2603.13417 ("Bridging Protocol and Production", Srinivasan, 2026) as a standard for agentic error handling.

```typescript
type SERFCategory =
  | "INVALID_PARAMS"      // Schema/validation failure — do not retry as-is
  | "RESOURCE_NOT_FOUND"  // Target doesn't exist — check ID, don't retry
  | "RESOURCE_EXHAUSTED"  // Quota/rate limit — retry after delay
  | "PERMISSION_DENIED"   // Auth failure — escalate or try different credentials
  | "RATE_LIMITED"        // Explicit rate limit — retry after retry_after_ms
  | "INTERNAL_ERROR";     // Server-side failure — retry with backoff

interface SERFError {
  error_category: SERFCategory;
  message: string;           // Human-readable description
  retryable: boolean;
  retry_after_ms?: number;   // Set for RATE_LIMITED and RESOURCE_EXHAUSTED
  suggested_actions: string[]; // Machine-readable next steps
  param_hints?: Record<string, string>; // For INVALID_PARAMS: field -> fix hint
}

function serfError(category: SERFCategory, message: string, opts: Partial<SERFError> = {}) {
  const defaults: Record<SERFCategory, Partial<SERFError>> = {
    INVALID_PARAMS:     { retryable: false, suggested_actions: ["fix_params_and_retry"] },
    RESOURCE_NOT_FOUND: { retryable: false, suggested_actions: ["search_for_resource", "list_resources"] },
    RESOURCE_EXHAUSTED: { retryable: true,  suggested_actions: ["retry_after_delay", "reduce_request_size"] },
    PERMISSION_DENIED:  { retryable: false, suggested_actions: ["check_permissions", "use_different_credentials"] },
    RATE_LIMITED:       { retryable: true,  suggested_actions: ["wait_and_retry"] },
    INTERNAL_ERROR:     { retryable: true,  suggested_actions: ["retry_with_backoff", "report_issue"] },
  };
  return {
    content: [{ type: "text", text: JSON.stringify({ ...defaults[category], ...opts, error_category: category, message }) }],
    isError: true,
  };
}

// Usage:
return serfError("RATE_LIMITED", "GitHub API rate limit exceeded", {
  retry_after_ms: 60_000,
  suggested_actions: ["wait_60s_then_retry"],
});
```

**Agent behavior contract:** Errors always include `retryable` (bool) and `error_category` (SERF taxonomy). Agents should: if `retryable=false`, stop and report to user; if `RATE_LIMITED`, wait `retry_after_ms`; if `INVALID_PARAMS`, inspect `param_hints`.

LLMs retry errors inconsistently when errors are natural-language prose. SERF gives agents deterministic retry logic, preventing both premature give-ups and infinite retry loops.

**Source:** [arXiv:2603.13417](https://arxiv.org/abs/2603.13417) -- "Bridging Protocol and Production" (Srinivasan, 2026)

---

## 5. Shared Context: Append-Only Event Log for Multi-Agent Coordination

When multiple agents share an MCP server, they need a coordination mechanism that avoids last-write-wins conflicts and preserves the full history of what each agent has done. An append-only event log is the simplest primitive that gives you both.

**Why not shared mutable state?** Two agents reading-then-writing to the same record will silently clobber each other's work. Locks help but introduce deadlock risk. The append-only log sidesteps both: agents only write new entries, never update old ones, so concurrent writes are safe.

```typescript
interface LogEntry {
  id: string;
  agent_id: string;
  timestamp: string;          // ISO 8601
  type: "observation" | "decision" | "action" | "result" | "handoff";
  payload: unknown;
  confidence?: number;        // 0.0-1.0, optional
  supersedes?: string;        // ID of a previous entry this revises
}

// In-memory log (replace with Redis or Postgres for persistence)
const eventLog: LogEntry[] = [];

server.tool("log_event", "Append an event to the shared coordination log", {
  agent_id: z.string(),
  type: z.enum(["observation", "decision", "action", "result", "handoff"]),
  payload: z.unknown(),
  confidence: z.number().min(0).max(1).optional(),
  supersedes: z.string().optional().describe("ID of a prior log entry this entry revises"),
}, async ({ agent_id, type, payload, confidence, supersedes }) => {
  const entry: LogEntry = {
    id: crypto.randomUUID(),
    agent_id,
    timestamp: new Date().toISOString(),
    type,
    payload,
    confidence,
    supersedes,
  };
  eventLog.push(entry);
  return { content: [{ type: "text", text: `Logged event ${entry.id}` }] };
});

server.tool("read_log", "Read shared coordination log, optionally filtered", {
  since: z.string().optional().describe("ISO timestamp — only return entries after this time"),
  agent_id: z.string().optional().describe("Filter to a specific agent's entries"),
  type: z.string().optional().describe("Filter to a specific event type"),
  limit: z.number().default(50),
}, async ({ since, agent_id, type, limit }) => {
  let entries = eventLog;
  if (since) entries = entries.filter(e => e.timestamp > since);
  if (agent_id) entries = entries.filter(e => e.agent_id === agent_id);
  if (type) entries = entries.filter(e => e.type === type);
  return { content: [{ type: "text", text: JSON.stringify(entries.slice(-limit), null, 2) }] };
});
```

**Coordination pattern:** Each agent should `read_log` at session start to understand what others have done, and `log_event` (type: `handoff`) when passing work to another agent. The `supersedes` field allows a correction entry without erasing history.

Multi-agent pipelines that use simple shared variables inevitably produce race conditions. The append-only log pattern makes agent coordination safe without requiring locks or transactions.

**Source:** Multi-agent coordination patterns from [r/mcp](https://reddit.com/r/mcp) and [r/AI_Agents](https://reddit.com/r/AI_Agents); event sourcing principles

---

## 6. Server-Enforced Workflow Stages

Maintain a `WorkflowStage` enum on the server and reject tool calls that arrive out of sequence. This enforces multi-step workflows without relying on the agent to follow documented instructions -- the server itself gates progress.

This differs from prompt-based guidance (which uses response text to *guide* the agent through stages) -- here the server *blocks* out-of-order calls with an error, making the wrong path structurally impossible.

```typescript
type WorkflowStage =
  | "initialized"
  | "data_loaded"
  | "analysis_complete"
  | "changes_validated"
  | "committed";

const STAGE_ORDER: WorkflowStage[] = [
  "initialized", "data_loaded", "analysis_complete", "changes_validated", "committed"
];

const sessions = new Map<string, WorkflowStage>();

function assertStage(sessionId: string, required: WorkflowStage, allowedPrevious: WorkflowStage[]) {
  const current = sessions.get(sessionId) ?? "initialized";
  if (!allowedPrevious.includes(current)) {
    const next = STAGE_ORDER[STAGE_ORDER.indexOf(current) + 1];
    throw {
      message: `Stage gate: current stage is "${current}". Must complete "${next}" before calling this tool.`,
      current_stage: current,
      required_stage: required,
      next_required_tool: stageToTool[next],
    };
  }
}

const stageToTool: Record<WorkflowStage, string> = {
  initialized: "load_data",
  data_loaded: "analyze_data",
  analysis_complete: "validate_changes",
  changes_validated: "commit_changes",
  committed: "(workflow complete)",
};

server.tool("commit_changes", "Commit validated changes. Requires validation stage.", {
  session_id: z.string(),
  dry_run: z.boolean().default(false),
}, async ({ session_id, dry_run }) => {
  try {
    assertStage(session_id, "committed", ["changes_validated"]);
  } catch (e: any) {
    return { content: [{ type: "text", text: JSON.stringify(e) }], isError: true };
  }

  const result = await commitChanges(session_id, dry_run);
  sessions.set(session_id, "committed");
  return { content: [{ type: "text", text: `Changes committed. ${result.summary}` }] };
});
```

**Why stage gates matter:** Without server-enforced stages, agents routinely skip prerequisite steps -- calling `deploy` before `validate`, or `commit` before `analyze`. The agent may appear confident, but it has no structural reason to follow the correct order. Stage gates eliminate this class of error entirely.

Documentation and prompt guidance are suggestions. Stage gates are enforcement. For consequential workflows (deployments, financial operations, data migrations), server-side stage enforcement is the only reliable safeguard.

**Source:** State machine enforcement patterns; community discussions on [r/mcp](https://reddit.com/r/mcp)
