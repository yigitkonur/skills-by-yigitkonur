# Code Mode

Complete reference for code mode — executing tool calls as code, executor types, tool namespaces, and search_tools.

---

## Why Code Mode

Based on Anthropic's research, code mode improves agent performance by:

- **Batch operations** — Multiple tool calls in a single code execution instead of one-at-a-time
- **Reduce context** — Less back-and-forth between agent and tools
- **Complex logic** — Conditionals, loops, error handling within tool orchestration
- **Natural workflow** — Developers think in code, not in sequential tool calls

Instead of the agent issuing individual `callTool` requests, it writes a code block that calls multiple tools programmatically.

---

## MCPClientOptions — codeMode

```typescript
interface MCPClientOptions {
  codeMode?: boolean | CodeModeConfig;
}
```

| Value | Meaning |
|---|---|
| `true` | Enable with default VM executor |
| `false` / omitted | Disabled (default) |
| `CodeModeConfig` | Enable with custom executor and options |

### CodeModeConfig Interface

```typescript
interface CodeModeConfig {
  enabled: boolean;
  executor?: "vm" | "e2b" | CodeExecutorFunction | BaseCodeExecutor;
  executorOptions?: VMExecutorOptions | E2BExecutorOptions;
}
```

| Field | Type | Default | Description |
|---|---|---|---|
| `enabled` | `boolean` | — | Whether code mode is active |
| `executor` | `string \| function \| class` | `"vm"` | Executor type or custom implementation |
| `executorOptions` | `object` | — | Executor-specific options |

---

## Executor Types

### VM Executor (Default)

Local execution using Node.js `vm` module:

- **Zero latency** — Runs in-process
- **No external dependencies** — No API keys or cloud services
- **No cost** — No per-execution charges
- **Basic isolation** — Not suitable for untrusted code

```typescript
import { MCPClient } from "mcp-use";

// Simplest: boolean shorthand
const client = new MCPClient(
  {
    mcpServers: {
      filesystem: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-filesystem", "./data"],
      },
    },
  },
  { codeMode: true }
);
```

#### VMExecutorOptions

```typescript
interface VMExecutorOptions {
  timeoutMs?: number;       // Default: 30000 (30 seconds)
  memoryLimitMb?: number;   // Optional memory limit in MB
}
```

```typescript
const client = new MCPClient(config, {
  codeMode: {
    enabled: true,
    executor: "vm",
    executorOptions: {
      timeoutMs: 60000,       // 1 minute
      memoryLimitMb: 512,     // 512 MB
    },
  },
});
```

| Option | Type | Default | Description |
|---|---|---|---|
| `timeoutMs` | `number` | `30000` | Max execution time per code block |
| `memoryLimitMb` | `number` | — | Memory limit (optional) |

### E2B Executor

Remote execution in E2B cloud sandboxes:

- **True isolation** — Full Linux sandbox per execution
- **Full Linux environment** — Any package, any tool
- **Suitable for untrusted code** — Sandbox is destroyed after execution
- **Requires API key** — E2B account and `@e2b/code-interpreter` package

```bash
yarn add @e2b/code-interpreter
```

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient(config, {
  codeMode: {
    enabled: true,
    executor: "e2b",
    executorOptions: {
      apiKey: process.env.E2B_API_KEY!,
      timeoutMs: 300000,    // 5 minutes (default)
    },
  },
});
```

#### E2BExecutorOptions

```typescript
interface E2BExecutorOptions {
  apiKey: string;           // Required — E2B API key
  timeoutMs?: number;       // Default: 300000 (5 minutes)
}
```

| Option | Type | Default | Description |
|---|---|---|---|
| `apiKey` | `string` | — | **Required.** E2B API key |
| `timeoutMs` | `number` | `300000` | Max execution time per code block |

### Custom Executor (Function)

Provide a function that receives code and returns an `ExecutionResult`:

```typescript
import { MCPClient } from "mcp-use";

type CodeExecutorFunction = (
  code: string,
  timeout?: number
) => Promise<ExecutionResult>;

const client = new MCPClient(config, {
  codeMode: {
    enabled: true,
    executor: async (code: string, timeout?: number): Promise<ExecutionResult> => {
      const startTime = Date.now();
      try {
        const result = await myCustomRuntime.execute(code, { timeout });
        return {
          result: result.value,
          logs: result.console,
          error: null,
          execution_time: (Date.now() - startTime) / 1000,
        };
      } catch (error) {
        return {
          result: null,
          logs: [],
          error: error instanceof Error ? error.message : String(error),
          execution_time: (Date.now() - startTime) / 1000,
        };
      }
    },
  },
});
```

### Custom Executor (Class)

Extend `BaseCodeExecutor` for full control:

```typescript
import { BaseCodeExecutor, MCPClient } from "mcp-use";

class MyExecutor extends BaseCodeExecutor {
  async execute(code: string, timeout?: number): Promise<ExecutionResult> {
    // Ensure all MCP servers are connected
    await this.ensureServersConnected();

    // Get tool namespaces for injection
    const namespaces = this.getToolNamespaces();

    // Create search_tools function
    const searchTools = this.createSearchToolsFunction();

    const startTime = Date.now();
    try {
      // Execute code with access to tool namespaces and search_tools
      const result = await myRuntime.execute(code, {
        timeout,
        globals: { ...namespaces, search_tools: searchTools },
      });

      return {
        result: result.value,
        logs: result.console ?? [],
        error: null,
        execution_time: (Date.now() - startTime) / 1000,
      };
    } catch (error) {
      return {
        result: null,
        logs: [],
        error: error instanceof Error ? error.message : String(error),
        execution_time: (Date.now() - startTime) / 1000,
      };
    }
  }

  async cleanup(): Promise<void> {
    // Release resources
    await myRuntime.shutdown();
  }
}

const executor = new MyExecutor(client);
const client = new MCPClient(config, {
  codeMode: {
    enabled: true,
    executor,
  },
});
```

#### BaseCodeExecutor Abstract Class

```typescript
abstract class BaseCodeExecutor {
  constructor(client: MCPClient);
  abstract execute(code: string, timeout?: number): Promise<ExecutionResult>;
  abstract cleanup(): Promise<void>;
  protected getToolNamespaces(): ToolNamespaceInfo[];
  protected async ensureServersConnected(): Promise<void>;
  public createSearchToolsFunction(): SearchToolsFunction;
}
```

| Method | Description |
|---|---|
| `execute(code, timeout?)` | Execute a code string and return the result |
| `cleanup()` | Release resources (called on client close) |
| `getToolNamespaces()` | Get `serverName → tools` mapping for injection |
| `ensureServersConnected()` | Verify all MCP server sessions are active |
| `createSearchToolsFunction()` | Create a `search_tools()` function for code injection |

---

## ExecutionResult Interface

```typescript
interface ExecutionResult {
  result: unknown;           // The return value from the executed code
  logs: string[];            // Console output (log, error, warn, etc.)
  error: string | null;      // Error message if execution failed, null otherwise
  execution_time: number;    // Execution duration in seconds
}
```

| Field | Type | Description |
|---|---|---|
| `result` | `unknown` | The return value of the executed code |
| `logs` | `string[]` | Console output (log, error, warn, etc.) |
| `error` | `string \| null` | Error message, or `null` on success |
| `execution_time` | `number` | Execution duration in seconds |

---

## Tool Namespaces in Code Mode

In code mode, tools are exposed as `serverName.toolName(args)`:

```typescript
// Inside code mode execution:

// GitHub server tools
const prs = await github.list_pull_requests({
  owner: "facebook",
  repo: "react",
});

// Filesystem server tools
const files = await filesystem.list_directory({ path: "/data" });

// Database server tools
const rows = await sqlite.read_query({
  sql: "SELECT * FROM users LIMIT 10",
});

// Access the namespace list
console.log("Available servers:", __tool_namespaces);
// => ["github", "filesystem", "sqlite"]
```

---

## search_tools() Function

Discover available tools at runtime within code mode:

```typescript
// Signature
async function search_tools(
  query?: string,
  detailLevel?: "names" | "descriptions" | "full"
): Promise<ToolSearchResponse>;
```

### Detail Levels

| Level | Fields Returned | Use Case |
|---|---|---|
| `"names"` | `name`, `server` | Quick overview of available tools |
| `"descriptions"` | + `description` | Find relevant tools by description |
| `"full"` | + `input_schema` | Get complete tool schemas for calling |

### ToolSearchResponse

```typescript
interface ToolSearchMeta {
  total_tools: number;
  namespaces: string[];
  result_count: number;
}

interface ToolSearchResult {
  name: string;
  server: string;
  description?: string;     // if detailLevel >= "descriptions"
  input_schema?: object;    // if detailLevel === "full"
}

interface ToolSearchResponse {
  meta: ToolSearchMeta;
  results: ToolSearchResult[];
}
```

### Usage Examples

```typescript
// Find all tools (default: full schemas)
const allResult = await search_tools();
console.log(`Total: ${allResult.meta.total_tools}`);
console.log(`Servers: ${allResult.meta.namespaces.join(", ")}`);

// Search specific tools by keyword
const githubResult = await search_tools("github");
for (const tool of githubResult.results) {
  console.log(`${tool.server}.${tool.name}: ${tool.description}`);
}

// Names only — fast scan
const namesResult = await search_tools("", "names");
namesResult.results.forEach((t) => console.log(`${t.server}.${t.name}`));

// Descriptions — medium detail
const descsResult = await search_tools("file", "descriptions");
descsResult.results.forEach((t) =>
  console.log(`${t.server}.${t.name}: ${t.description}`)
);

// Full schemas — for constructing tool calls
const fullResult = await search_tools("query", "full");
fullResult.results.forEach((t) =>
  console.log(`${t.server}.${t.name}`, JSON.stringify(t.input_schema))
);
```

---

## MCPClient Code Mode Methods

### MCPClient Methods

```typescript
class MCPClient {
  // Execute code with MCP tool access
  // Optional timeout overrides the executor-level default for this single call
  async executeCode(code: string, timeout?: number): Promise<ExecutionResult>;

  // Search available tools (also available as search_tools() inside code mode)
  async searchTools(
    query?: string,
    detailLevel?: "names" | "descriptions" | "full"
  ): Promise<ToolSearchResponse>;

  // Clean up resources (E2B sandboxes, MCP sessions)
  async close(): Promise<void>;
}
```

#### executeCode()

Execute a code string directly. The optional `timeout` overrides the executor-level default for that single execution:

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient(config, { codeMode: true });
await client.createAllSessions();

const result = await client.executeCode(`
  const files = await filesystem.list_directory({ path: "/data" });
  const count = files.content[0].text.split("\\n").length;
  return { fileCount: count };
`);

console.log(result.result);          // { fileCount: 42 }
console.log(result.logs);            // []
console.log(result.error);           // null
console.log(result.execution_time);  // 0.123

// Per-execution timeout override (30 seconds for this call only)
const timedResult = await client.executeCode(code, 30000);

await client.close();
```

#### searchTools()

Search tools from outside code mode:

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient(config, { codeMode: true });
await client.createAllSessions();

const response = await client.searchTools("file", "descriptions");
console.log(`Found ${response.meta.result_count} tools`);
for (const tool of response.results) {
  console.log(`${tool.server}.${tool.name}: ${tool.description}`);
}

await client.close();
```

---

## Agent Integration with PROMPTS.CODE_MODE

Use the built-in code mode system prompt with an agent:

```typescript
import { MCPClient } from "mcp-use";
import { MCPAgent } from "mcp-use/agent";
import { PROMPTS } from "mcp-use/client/prompts";

const client = new MCPClient(
  {
    mcpServers: {
      filesystem: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-filesystem", "./data"],
      },
      github: {
        url: "https://api.github.com/mcp",
        headers: { Authorization: `Bearer ${process.env.GITHUB_TOKEN}` },
      },
    },
  },
  { codeMode: true }
);

const agent = new MCPAgent({
  llm,
  client,
  systemPrompt: PROMPTS.CODE_MODE,
});

// The agent writes code that calls tools via namespaces
const result = await agent.run(
  "List all files in /data, then check recent PRs on my GitHub repo"
);

console.log(result);
await client.close();
```

The `PROMPTS.CODE_MODE` system prompt instructs the agent to:
1. Use `search_tools()` to discover available tools
2. Write code using `serverName.toolName(args)` syntax
3. Handle errors within the code block
4. Return structured results

---

## Error Handling

Check `result.error` after every `executeCode()` call. Errors inside the code block are caught and returned in the `error` field; they do not throw:

```typescript
const result = await client.executeCode(`
  try {
    const data = await github.get_pull_request({ number: 12345 });
    return data;
  } catch (e) {
    console.error(e);
    return { error: e.message };
  }
`);

if (result.error) {
  console.error("Execution failed:", result.error);
  console.log("Logs:", result.logs);
} else {
  console.log("Result:", result.result);
}
```

---

## Security Considerations

| Executor | Isolation Level | Untrusted Code? | Notes |
|---|---|---|---|
| **VM** | Basic (same process) | ❌ No | Can access process memory, env vars |
| **E2B** | Full (cloud sandbox) | ✅ Yes | Isolated Linux container, destroyed after use |
| **Custom (function)** | Depends on implementation | Depends | You control the isolation boundary |
| **Custom (class)** | Depends on implementation | Depends | Full control over execution environment |

Additional security rules:

- Always call `await client.close()` to terminate sandboxes and release resources.
- Set strict `timeoutMs` values to bound execution time and prevent runaway code.
- Prefer E2B in production or multi-tenant environments.

❌ **BAD** — Using VM executor with untrusted user code:

```typescript
const client = new MCPClient(config, { codeMode: true });

// This code runs in the same process — can access process.env, fs, etc.
await client.executeCode(userProvidedCode);
```

✅ **GOOD** — Using E2B executor for untrusted code:

```typescript
const client = new MCPClient(config, {
  codeMode: {
    enabled: true,
    executor: "e2b",
    executorOptions: {
      apiKey: process.env.E2B_API_KEY!,
      timeoutMs: 30000,
    },
  },
});

// Safe: runs in an isolated cloud sandbox
await client.executeCode(userProvidedCode);
```

---

## Decision Matrix — VM vs E2B vs Custom

| Factor | VM | E2B | Custom |
|---|---|---|---|
| **Isolation** | Basic (process-level) | Strong (cloud sandbox) | Depends on implementation |
| **Latency** | Near-zero | Network latency + sandbox startup | Variable |
| **Cost** | Free | Paid (E2B usage) | Implementation-dependent |
| **Access to OS / network** | Limited to Node built-ins | Full Linux env, network & filesystem | Customizable |
| **Untrusted code** | ❌ Unsafe | ✅ Safe | ✅ if you implement isolation |
| **Configuration complexity** | Low | Medium (API key, env) | High (you write the executor) |
| **Debugging** | Simple stack traces | Remote logs, may be harder | As you design it |

---

## Complete Example — VM Code Mode with Agent

```typescript
import { MCPClient } from "mcp-use";
import { MCPAgent } from "mcp-use/agent";
import { PROMPTS } from "mcp-use/client/prompts";

const client = new MCPClient(
  {
    mcpServers: {
      filesystem: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-filesystem", "./project"],
      },
    },
  },
  {
    codeMode: {
      enabled: true,
      executor: "vm",
      executorOptions: {
        timeoutMs: 60000,
        memoryLimitMb: 256,
      },
    },
  }
);

await client.createAllSessions();

// Direct code execution
const directResult = await client.executeCode(`
  // Discover available tools
  const tools = await search_tools("", "names");
  console.log("Available tools:", tools.meta.total_tools);

  // Use filesystem tools
  const files = await filesystem.list_directory({ path: "." });
  const fileList = files.content[0].text;
  const count = fileList.split("\\n").filter(Boolean).length;

  return { toolCount: tools.meta.total_tools, fileCount: count };
`);

console.log("Direct result:", directResult.result);
console.log("Logs:", directResult.logs);
console.log("Time:", directResult.execution_time, "seconds");

// Agent-driven code execution
const agent = new MCPAgent({
  llm,
  client,
  systemPrompt: PROMPTS.CODE_MODE,
});

const agentResult = await agent.run("Count all TypeScript files in the project");
console.log("Agent result:", agentResult);

await client.close();
```

---

## Available Imports

```typescript
// Core client and executor base
import { MCPClient, BaseCodeExecutor } from "mcp-use";

// CodeExecutor is an alias for BaseCodeExecutor (backward compatibility)
import { CodeExecutor } from "mcp-use";

// Concrete executor implementations
import { VMCodeExecutor, isVMAvailable, E2BCodeExecutor } from "mcp-use";

// Agent integration
import { MCPAgent } from "mcp-use/agent";

// Code mode system prompt
import { PROMPTS } from "mcp-use/client/prompts";

// Types (for custom executors)
import type {
  ExecutionResult,
  CodeModeConfig,
  VMExecutorOptions,
  E2BExecutorOptions,
  ToolSearchResponse,
  ToolSearchResult,
  ToolSearchMeta,
} from "mcp-use";
```
