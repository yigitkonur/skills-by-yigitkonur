# Custom Agents — Reference

Custom agents are named agent definitions registered on a session. Each agent carries its own system prompt, an optional restricted tool list, and optional private MCP servers. When a user's prompt matches an agent's expertise the Copilot runtime delegates to that agent as a **sub-agent**, running it in an isolated context and streaming lifecycle events back to the parent session.

---

## `CustomAgentConfig` Type

```typescript
interface CustomAgentConfig {
    name: string;                              // required — unique identifier
    displayName?: string;                      // shown in events / UI
    description?: string;                      // used by runtime for intent matching
    prompt: string;                            // required — system-level instruction for this agent
    tools?: string[] | null;                   // restrict tool access; null/omitted = all tools
    mcpServers?: Record<string, MCPServerConfig>; // agent-private MCP servers
    infer?: boolean;                           // default true — allow runtime auto-selection
}
```

Key constraints:
- `name` must be unique within the `customAgents` array.
- `prompt` is injected as a system-level instruction, not a user message. Write it as a persona or role definition.
- `tools: []` gives the agent zero tools. `tools: null` or omitting the field grants all session-level tools.
- `description` is the primary signal the runtime uses for intent-based delegation. Make it specific.
- `infer: false` prevents automatic selection; the agent is only activated via explicit RPC calls.

---

## Registering Agents in SessionConfig

Pass `customAgents` when calling `client.createSession()`. All agents are available for the lifetime of the session.

```typescript
import { CopilotClient } from "@github/copilot-sdk";

const client = new CopilotClient();
await client.start();

const session = await client.createSession({
    model: "gpt-4.1",
    onPermissionRequest: async () => ({ kind: "approved" }),
    customAgents: [
        {
            name: "researcher",
            displayName: "Research Agent",
            description: "Explores codebases and answers questions using read-only tools",
            tools: ["grep", "glob", "view"],
            prompt: "You are a research assistant. Analyze code and answer questions. Do not modify any files.",
        },
        {
            name: "editor",
            displayName: "Editor Agent",
            description: "Makes targeted code changes to files",
            tools: ["view", "edit", "bash"],
            prompt: "You are a code editor. Make minimal, surgical changes to files as requested.",
        },
    ],
});
```

Agents are also accepted on `client.resumeSession()` — pass the same `customAgents` array in `ResumeSessionConfig`.

---

## Pre-Selecting an Agent at Session Creation

Set `agent` in `SessionConfig` to activate a specific agent immediately, before any prompt is sent. The value must match the `name` field of one entry in `customAgents`.

```typescript
const session = await client.createSession({
    onPermissionRequest: async () => ({ kind: "approved" }),
    customAgents: [
        { name: "researcher", prompt: "You are a research assistant." },
        { name: "editor",     prompt: "You are a code editor." },
    ],
    agent: "researcher",  // active from the first prompt
});
```

This is equivalent to calling `session.rpc.agent.select({ name: "researcher" })` immediately after creation, but avoids the extra round-trip and guarantees no events are missed during startup.

---

## Runtime Agent Selection RPCs

Use `session.rpc.agent` to control the active agent imperatively after the session is created.

```typescript
// List all registered custom agents
const { agents } = await session.rpc.agent.list();
// agents: Array<{ name, displayName, description }>

// Get the currently active agent (null = default/no custom agent)
const { agent } = await session.rpc.agent.getCurrent();

// Select a custom agent by name
const result = await session.rpc.agent.select({ name: "researcher" });
// result.agent: { name, displayName, description }

// Deselect — return to the default agent
await session.rpc.agent.deselect();
```

`select` and `deselect` take effect on the next prompt sent to the session.

---

## Agent Prompt as System-Level Instruction

The `prompt` field is injected into the system message before the conversation starts. Treat it as a persona or behavioral contract:

```typescript
{
    name: "security-auditor",
    prompt: `You are a security engineer performing a code audit.
Focus exclusively on OWASP Top 10 vulnerabilities.
Always cite the specific OWASP category (e.g., A03:2021) when reporting an issue.
Do not suggest refactors unrelated to security.
Output findings as a bulleted list with severity: critical | high | medium | low.`,
}
```

Write prompts in second-person imperative ("You are…", "Always…", "Never…"). The prompt is additive — the SDK's own system message foundation is still present unless you use `systemMessage: { mode: "replace", content: "..." }` on the session.

---

## Agent-Specific Tool Restrictions

`tools` is an allowlist. The agent can only invoke tools whose names appear in the array.

```typescript
customAgents: [
    {
        name: "read-only",
        description: "Safe exploration — no writes",
        tools: ["grep", "glob", "view"],          // no bash, no edit
        prompt: "You explore and analyze. Never modify files.",
    },
    {
        name: "full-access",
        description: "Handles complex multi-step tasks",
        tools: null,                               // inherits all session tools
        prompt: "You handle complex tasks with any available tool.",
    },
]
```

Tool names in the allowlist must match the exact tool identifier used by the Copilot runtime (e.g., `"bash"`, `"edit"`, `"grep"`, `"glob"`, `"view"`). MCP tools use their namespaced names (see `mcp-servers.md`).

---

## Multiple Agents and Agent Switching

Define any number of agents. The runtime selects among them based on intent. You can also switch programmatically mid-session.

```typescript
// Define three specialized agents
const session = await client.createSession({
    onPermissionRequest: async () => ({ kind: "approved" }),
    customAgents: [
        {
            name: "planner",
            description: "Breaks down tasks into steps and creates execution plans",
            tools: ["view", "grep"],
            prompt: "You create detailed plans. Produce a numbered action list before any work begins.",
            infer: true,
        },
        {
            name: "implementer",
            description: "Writes and modifies code according to a plan",
            tools: ["view", "edit", "bash"],
            prompt: "You implement plans. Execute each step precisely.",
            infer: true,
        },
        {
            name: "reviewer",
            description: "Reviews diffs and checks correctness",
            tools: ["view", "bash"],
            prompt: "You review changes. Check for bugs, style issues, and test coverage.",
            infer: false,  // only activated explicitly
        },
    ],
});

// Explicit switch: move to reviewer after implementation
await session.rpc.agent.select({ name: "reviewer" });
const review = await session.sendAndWait({ prompt: "Review the changes just made." });

// Return to default
await session.rpc.agent.deselect();
```

---

## Agent with MCP Server Combination

Attach private MCP servers to a single agent. Those servers are only available when that agent is active.

```typescript
customAgents: [
    {
        name: "db-analyst",
        description: "Analyzes database schemas and queries data",
        prompt: "You are a database expert. Use the postgres MCP server to inspect schemas and run queries.",
        tools: null,  // all tools including MCP tools
        mcpServers: {
            postgres: {
                type: "local",
                command: "npx",
                args: ["-y", "@modelcontextprotocol/server-postgres", "postgresql://localhost/mydb"],
                tools: ["*"],
            },
        },
    },
]
```

Session-level `mcpServers` (in `SessionConfig`) are available to all agents. Agent-level `mcpServers` are private to that agent and layered on top.

---

## `infer: true` — Automatic Agent Selection

By default every agent has `infer: true`. The runtime matches user intent to agent descriptions and automatically delegates.

```typescript
// Allow auto-selection (default)
{ name: "test-runner", description: "Runs test suites and reports failures", infer: true }

// Prevent auto-selection — only invoked via session.rpc.agent.select()
{ name: "dangerous-cleanup", description: "Deletes unused files and dead code", infer: false }
```

Use `infer: false` for destructive or irreversible agents. The runtime will never auto-activate them — the caller must explicitly call `session.rpc.agent.select({ name: "dangerous-cleanup" })`.

---

## Sub-Agent Lifecycle Events

When the runtime delegates to a sub-agent, the parent session emits these events:

| Event | When emitted | Key data fields |
|---|---|---|
| `subagent.selected` | Runtime picks an agent | `agentName`, `agentDisplayName`, `tools` |
| `subagent.started` | Sub-agent begins execution | `toolCallId`, `agentName`, `agentDisplayName`, `agentDescription` |
| `subagent.completed` | Sub-agent finishes successfully | `toolCallId`, `agentName`, `agentDisplayName` |
| `subagent.failed` | Sub-agent errors | `toolCallId`, `agentName`, `agentDisplayName`, `error` |
| `subagent.deselected` | Runtime returns to parent | — |

Subscribe and track activity:

```typescript
session.on((event) => {
    switch (event.type) {
        case "subagent.started":
            console.log(`Agent started: ${event.data.agentDisplayName} (call ${event.data.toolCallId})`);
            break;
        case "subagent.completed":
            console.log(`Agent done: ${event.data.agentDisplayName}`);
            break;
        case "subagent.failed":
            console.error(`Agent failed: ${event.data.agentName} — ${event.data.error}`);
            break;
    }
});
```

Use `toolCallId` to correlate start/complete/fail events when multiple sub-agents run concurrently.

---

## Agent Description Quality

The runtime's intent matching depends entirely on the `description` field. Vague descriptions cause poor delegation.

```typescript
// BAD — too vague, runtime cannot distinguish this from any other agent
{ description: "Helps with code" }

// GOOD — specific expertise, runtime knows exactly when to delegate
{ description: "Analyzes Python test coverage and identifies untested code paths" }
{ description: "Queries and summarizes Postgres database schemas" }
{ description: "Reviews pull request diffs for OWASP security issues" }
```

---

## Combining with Session-Level Tool Restrictions

Session-level `availableTools` and `excludedTools` apply to the session's default agent. Agent-level `tools` applies only to that specific custom agent. They compose: an agent with `tools: ["bash", "edit"]` will only see those two tools regardless of what the session's `availableTools` allows.

```typescript
const session = await client.createSession({
    availableTools: ["bash", "edit", "view", "grep", "glob"],  // session-level
    customAgents: [
        {
            name: "reader",
            tools: ["view", "grep", "glob"],  // further restricted subset
            prompt: "Read-only agent.",
        },
    ],
});
```
