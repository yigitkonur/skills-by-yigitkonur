# Agents, MCP, and Skills

## Custom agents

Define agents with specialized personas, tool sets, and MCP servers:

```typescript
const session = await client.createSession({
  onPermissionRequest: approveAll,
  customAgents: [
    {
      name: "code-reviewer",
      displayName: "Code Reviewer",
      description: "Reviews code for quality and security",
      prompt: "You are a senior code reviewer. Focus on security, performance, and maintainability.",
      tools: ["bash", "view", "grep"],  // restrict available tools
      infer: true,                       // model auto-routes to this agent
    },
    {
      name: "test-writer",
      displayName: "Test Writer",
      description: "Writes comprehensive tests",
      prompt: "You write thorough unit and integration tests.",
      tools: null,                       // null = all tools available
      infer: true,
      mcpServers: {                      // agent-specific MCP servers
        playwright: {
          type: "local",
          command: "npx",
          args: ["@playwright/mcp@latest"],
          tools: ["*"],
        },
      },
    },
  ],
  agent: "code-reviewer",  // activate this agent at session start
});
```

### CustomAgentConfig

```typescript
interface CustomAgentConfig {
  name: string;                              // unique identifier
  displayName?: string;                      // human-readable name
  description?: string;                      // shown to model for routing
  tools?: string[] | null;                   // null/undefined = all tools
  prompt: string;                            // system prompt for this agent
  mcpServers?: Record<string, MCPServerConfig>; // agent-specific MCP servers
  infer?: boolean;                           // default true — auto-route based on user intent
}
```

### Agent RPC methods

```typescript
// List available agents
const agents = await session.rpc.agent.list();
// { agents: [{ name, displayName, description }] }

// Get current agent
const current = await session.rpc.agent.getCurrent();
// { agent: { name, displayName, description } | null }

// Switch to an agent
await session.rpc.agent.select({ name: "test-writer" });

// Deselect (back to default)
await session.rpc.agent.deselect();
```

### Agent events

```typescript
session.on("subagent.selected", (event) => {
  console.log(`Agent activated: ${event.data.agentName}`);
  console.log(`Tools: ${event.data.tools}`); // string[] | null
});

session.on("subagent.deselected", () => {
  console.log("Back to default agent");
});

session.on("subagent.started", (event) => {
  console.log(`Sub-agent started: ${event.data.agentName}`);
  console.log(`Description: ${event.data.agentDescription}`);
});

session.on("subagent.completed", (event) => {
  console.log(`Sub-agent done: ${event.data.agentName}`);
});

session.on("subagent.failed", (event) => {
  console.error(`Sub-agent error: ${event.data.error}`);
});
```

## MCP servers

Configure MCP servers per-session to extend the model's tool set.

### Local/stdio MCP server

```typescript
const session = await client.createSession({
  onPermissionRequest: approveAll,
  mcpServers: {
    github: {
      type: "local",        // or "stdio"
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-github"],
      tools: ["*"],          // "*" = all tools; or list specific names
      env: {
        GITHUB_TOKEN: process.env.GITHUB_TOKEN,
      },
      cwd: "/path/to/workdir",
      timeout: 30000,
    },
  },
});
```

### Remote HTTP/SSE MCP server

```typescript
mcpServers: {
  "remote-api": {
    type: "http",            // or "sse"
    url: "https://api.githubcopilot.com/mcp/",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    tools: ["*"],
    timeout: 30000,
  },
}
```

### MCPServerConfig types

```typescript
interface MCPLocalServerConfig {
  type?: "local" | "stdio";
  command: string;
  args: string[];
  env?: Record<string, string>;
  cwd?: string;
  tools: string[];     // ["*"] for all, or specific tool names
  timeout?: number;
}

interface MCPRemoteServerConfig {
  type: "http" | "sse";
  url: string;
  headers?: Record<string, string>;
  tools: string[];
  timeout?: number;
}
```

### MCP in custom agents

Agents can have their own MCP servers that activate only when the agent is selected:

```typescript
customAgents: [{
  name: "mcp-agent",
  prompt: "Use MCP tools to complete tasks.",
  mcpServers: {
    "agent-server": {
      type: "local",
      command: "node",
      args: ["/path/to/server.mjs"],
      tools: ["*"],
    },
  },
}]
```

### MCP on resume

MCP servers can be added or changed when resuming a session:

```typescript
const session = await client.resumeSession("my-session", {
  onPermissionRequest: approveAll,
  mcpServers: {
    newServer: {
      type: "local",
      command: "my-server",
      args: [],
      tools: ["*"],
    },
  },
});
```

## Skills

Skills are markdown files that inject instructions into the model's context.

### Skill directory structure

```
skills-dir/
  my-skill/
    SKILL.md
```

### SKILL.md format

```markdown
---
name: my-skill
description: A skill that adds project-specific context
---

# Instructions

Always use our internal API client from `src/api/client.ts`.
Never use `fetch` directly — always go through the API layer.
```

### Session configuration

```typescript
const session = await client.createSession({
  onPermissionRequest: approveAll,
  skillDirectories: ["/path/to/skills"],
  disabledSkills: ["skill-to-disable"], // disable by name
});
```

### Skill events

```typescript
session.on("skill.invoked", (event) => {
  console.log(`Skill: ${event.data.name}`);
  console.log(`Path: ${event.data.path}`);
  console.log(`Content: ${event.data.content}`);
  console.log(`Allowed tools: ${event.data.allowedTools}`);
});
```

## CLI extensions (.mjs)

Extensions run inside the Copilot CLI process and extend its capabilities.

### File location

```
.github/extensions/<name>/extension.mjs
```

### Minimal extension

```javascript
import { approveAll } from "@github/copilot-sdk";
import { joinSession } from "@github/copilot-sdk/extension";

const session = await joinSession({
  onPermissionRequest: approveAll,
  tools: [{
    name: "my_tool",
    description: "Does something useful",
    parameters: {
      type: "object",
      properties: { input: { type: "string" } },
      required: ["input"],
    },
    handler: async (args) => `Result: ${args.input}`,
  }],
  hooks: {
    onPreToolUse: async (input) => ({ permissionDecision: "allow" }),
  },
});
```

### Extension rules

- Only `.mjs` files (TypeScript `.ts` not supported)
- Use `session.log()` for output — **never** `console.log()` (stdout is JSON-RPC)
- Tool names must be globally unique across all extensions
- Extensions reload on `/clear` — all in-memory state is lost
- Do not call `session.send()` synchronously from `onUserPromptSubmitted` — use `setTimeout`

### Extension session API

```typescript
// session from joinSession has full CopilotSession API:
await session.send({ prompt: "..." });
await session.sendAndWait({ prompt: "..." });
await session.log("message", { level: "info", ephemeral: true });
session.on("assistant.message", (event) => { /* ... */ });
session.workspacePath; // string | undefined
session.rpc;          // typed RPC access
```

### Scaffold a new extension

From within the CLI, use the built-in tool:
```
extensions_manage({ operation: "scaffold", name: "my-extension" })
```

Then reload:
```
extensions_reload({})
```

## Steering notes

> Common mistakes agents make with MCP/agents/skills.

- **CLI extensions and session MCP servers are different mechanisms**. CLI extensions run through `.github/extensions/.../extension.mjs` + `joinSession()`. Session MCP servers are configured with `mcpServers` on `createSession()` / `resumeSession()`.
- **Extension tool names must be globally unique**. If two extensions define a tool with the same name, the second one silently overwrites the first.
- **MCP server configuration** follows the standard MCP protocol. The SDK passes the config directly to the CLI, which spawns the MCP server process.
- **Custom agents** are configured with `customAgents` and can be activated at start with `agent` or switched at runtime with `session.rpc.agent.select(...)`.
- **Skills are loaded from `skillDirectories`** and can be disabled with `disabledSkills`. They are not referenced through a separate `sessionConfig.skills` field in the API shown here.
