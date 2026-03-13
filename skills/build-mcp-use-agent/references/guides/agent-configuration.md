# Agent Configuration

## MCPAgentOptions (full interface)

### Common options (both modes)

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `maxSteps` | `number` | `5` | Maximum tool-calling cycles per request |
| `autoInitialize` | `boolean` | `false` | Auto-call `initialize()` on construction |
| `memoryEnabled` | `boolean` | `true` | Enable conversation memory |
| `systemPrompt` | `string \| null` | `null` | Custom system prompt (overrides template) |
| `systemPromptTemplate` | `string \| null` | `null` | Template with `{tool_descriptions}` placeholder |
| `additionalInstructions` | `string \| null` | `null` | Extra guidance appended to system prompt |
| `disallowedTools` | `string[]` | `[]` | Tool names the agent must not use |
| `additionalTools` | `StructuredToolInterface[]` | `[]` | Extra tools beyond MCP-discovered ones |
| `toolsUsedNames` | `string[]` | `undefined` | Restrict to specific tool names |
| `exposeResourcesAsTools` | `boolean` | `true` | Make MCP resources callable as tools |
| `exposePromptsAsTools` | `boolean` | `true` | Make MCP prompts callable as tools |
| `useServerManager` | `boolean` | `false` | Enable dynamic multi-server routing |
| `verbose` | `boolean` | `false` | Detailed logging of internal steps |
| `observe` | `boolean` | `true` | Enable observability integration |
| `callbacks` | `BaseCallbackHandler[]` | `[]` | LangChain callback handlers |
| `adapter` | `LangChainAdapter` | `undefined` | Custom LangChain adapter |
| `serverManagerFactory` | `(client: MCPClient) => ServerManager` | `undefined` | Custom server manager factory |

### Explicit mode options

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `llm` | `LanguageModel` | Yes | LangChain chat model instance |
| `client` | `MCPClient` | No | Pre-configured client (optional if `connectors` provided) |
| `connectors` | `BaseConnector[]` | No | Connector definitions |

### Simplified mode options

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `llm` | `string` | Yes | `"provider/model"` format |
| `llmConfig` | `LLMConfig` | No | Temperature, maxTokens, apiKey overrides |
| `mcpServers` | `Record<string, MCPServerConfig>` | Yes | Inline server definitions |

## System prompt customization

```typescript
// Option 1: Full custom prompt (replaces default entirely)
const agent = new MCPAgent({
  llm, client,
  systemPrompt: "You are a data analyst. Only use tools for data operations.",
});

// Option 2: Template with tool descriptions injected
const agent = new MCPAgent({
  llm, client,
  systemPromptTemplate: `You are a security auditor.
Available tools:
{tool_descriptions}
Only use tools marked as safe.`,
});

// Option 3: Append extra instructions to default prompt
const agent = new MCPAgent({
  llm, client,
  additionalInstructions: "Always verify results before reporting. Follow corporate compliance.",
});
```

## Tool access control

```typescript
// Block specific tools at construction
const agent = new MCPAgent({
  llm, client,
  disallowedTools: ["file_system", "network", "shell", "database"],
});

// Update blocklist at runtime
agent.setDisallowedTools(["file_system"]);
await agent.initialize(); // re-apply after changes

// Check current blocklist
const blocked = agent.getDisallowedTools(); // → ["file_system"]
```

## Auto-initialization

```typescript
// Without autoInitialize — must call initialize() or it auto-inits on first run()
const agent = new MCPAgent({ llm, client });
await agent.initialize(); // explicit
await agent.run("query");

// With autoInitialize — ready immediately
const agent = new MCPAgent({ llm, client, autoInitialize: true });
await agent.run("query"); // no need to call initialize()
```

## Remote agent options

```typescript
// Additional options for RemoteAgent
const agent = new MCPAgent({
  llm, client,
  agentId: "remote-agent-id",    // for remote execution
  apiKey: "mcp-use-api-key",     // MCP Use Cloud API key
  baseUrl: "https://cloud.mcp-use.com",
});
```

## Best practices

1. **Set `maxSteps` proportional to task complexity** — simple queries: 5–10, complex multi-step: 20–50.
2. **Use `systemPrompt` for persona** — define the agent's role and constraints.
3. **Use `additionalInstructions` for per-task guidance** — changes frequently, keeps base prompt stable.
4. **Use `disallowedTools` for security** — block dangerous tools in production.
5. **Prefer `autoInitialize: true`** unless you need to customize between construction and first run.
