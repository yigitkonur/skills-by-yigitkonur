# Client API

The `Client` class connects to MCP servers and invokes their tools, resources, and prompts. Use it for building MCP client applications, testing servers, or creating multi-server orchestration.

## Client class

```typescript
import { Client } from "@modelcontextprotocol/sdk/client/index.js";

const client = new Client(
  { name: "my-client", version: "1.0.0" },
  {
    capabilities: {
      sampling: {},                          // Enable server-requested LLM completions
      roots: { listChanged: true },          // Enable filesystem root queries
      elicitation: { form: {}, url: {} },    // Enable server-requested user input
    },
  }
);
```

## Connecting to servers

### stdio (local process)

```typescript
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const transport = new StdioClientTransport({
  command: "node",
  args: ["server.js"],
  env: { API_KEY: process.env.API_KEY },
  cwd: "/path/to/server",
  stderr: "inherit",    // 'inherit' | 'pipe' | 'ignore'
});

await client.connect(transport);
```

### Streamable HTTP (remote)

```typescript
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";

const transport = new StreamableHTTPClientTransport(
  new URL("http://localhost:3000/mcp"),
  {
    requestInit: { headers: { "X-Custom": "value" } },
    authProvider: myOAuthProvider,    // OAuthClientProvider for OAuth
    reconnectionOptions: {
      initialReconnectionDelay: 1000,
      maxReconnectionDelay: 30000,
      reconnectionDelayGrowFactor: 1.5,
      maxRetries: 2,
    },
    eventStore: myEventStore,        // For resumability
  }
);

await client.connect(transport);
```

## Core methods

### Tools

```typescript
// List available tools
const { tools } = await client.listTools();

// Call a tool
const result = await client.callTool({
  name: "search",
  arguments: { query: "MCP", limit: 10 },
});
// result: CallToolResult { content, structuredContent?, isError? }
```

### Resources

```typescript
// List resources
const { resources } = await client.listResources();

// List resource templates
const { resourceTemplates } = await client.listResourceTemplates();

// Read a resource
const { contents } = await client.readResource({ uri: "file:///project/README.md" });

// Subscribe to changes
await client.subscribeResource({ uri: "file:///project/config.json" });
await client.unsubscribeResource({ uri: "file:///project/config.json" });
```

### Prompts

```typescript
// List prompts
const { prompts } = await client.listPrompts();

// Get a prompt with arguments
const { messages, description } = await client.getPrompt({
  name: "code_review",
  arguments: { code: "function hello() {}" },
});
```

### Completions

```typescript
// Autocomplete prompt arguments
const { completion } = await client.complete({
  ref: { type: "ref/prompt", name: "code_review" },
  argument: { name: "language", value: "py" },
});
// completion: { values: ["python", "pytorch"], total: 10, hasMore: true }
```

### Logging

```typescript
await client.setLoggingLevel("info");
```

### Utility

```typescript
await client.ping();
await client.close();

const caps = client.getServerCapabilities();
const version = client.getServerVersion();
const instructions = client.getInstructions();
```

## List change notifications

React to server-side changes:

```typescript
const client = new Client(clientInfo, {
  capabilities: { /* ... */ },
  listChanged: {
    tools: {
      onChanged: (err, tools) => {
        if (err) console.error("Tool list error:", err);
        else console.log("Tools updated:", tools);
      },
    },
    resources: {
      onChanged: (err, resources) => { /* ... */ },
    },
    prompts: {
      onChanged: (err, prompts) => { /* ... */ },
    },
  },
});
```

## Roots (filesystem boundaries)

When a server calls `roots/list`, the client responds with the configured roots:

```typescript
client.setRequestHandler(ListRootsRequestSchema, async () => ({
  roots: [
    { uri: "file:///home/user/project", name: "My Project" },
  ],
}));

// Notify server when roots change
await client.sendRootsListChanged();
```

## Sampling handler

When a server requests LLM completions via `sampling/createMessage`:

```typescript
client.setRequestHandler(CreateMessageRequestSchema, async (request) => {
  const { messages, modelPreferences, maxTokens } = request.params;

  // Call your LLM
  const completion = await callLLM(messages, maxTokens);

  return {
    role: "assistant",
    content: { type: "text", text: completion.text },
    model: "claude-3-sonnet",
    stopReason: "endTurn",
  };
});
```

## Client authentication

### Simple bearer token

```typescript
const transport = new StreamableHTTPClientTransport(url, {
  requestInit: {
    headers: { Authorization: `Bearer ${process.env.MCP_TOKEN}` },
  },
});
```

### OAuthClientProvider (full OAuth)

```typescript
import { OAuthClientProvider } from "@modelcontextprotocol/sdk/client/auth.js";

class MyOAuthProvider implements OAuthClientProvider {
  get redirectUrl() { return "http://localhost:3000/callback"; }
  get clientMetadata() {
    return {
      client_name: "My Client",
      redirect_uris: ["http://localhost:3000/callback"],
      grant_types: ["authorization_code"],
      response_types: ["code"],
      token_endpoint_auth_method: "none",
    };
  }

  async clientInformation() { /* return stored client info */ }
  async saveClientInformation(info) { /* persist client info */ }
  async tokens() { /* return stored tokens */ }
  async saveTokens(tokens) { /* persist tokens */ }
  async redirectToAuthorization(url) { /* open browser to url */ }
  async saveCodeVerifier(verifier) { /* persist for PKCE */ }
  async codeVerifier() { /* return stored verifier */ }
}

const transport = new StreamableHTTPClientTransport(url, {
  authProvider: new MyOAuthProvider(),
});
```

### Auth extensions (built-in providers)

```typescript
import {
  ClientCredentialsProvider,
  PrivateKeyJwtProvider,
} from "@modelcontextprotocol/sdk/client/auth-extensions.js";

// Machine-to-machine (no user interaction)
const provider = new ClientCredentialsProvider({
  clientId: "my-service",
  clientSecret: process.env.CLIENT_SECRET,
});

// JWT-based client auth
const provider = new PrivateKeyJwtProvider({
  clientId: "my-service",
  privateKey: process.env.PRIVATE_KEY,
});
```

## Experimental: task-based tool calls

```typescript
// Stream a task-based tool call
const stream = client.experimental.tasks.callToolStream({
  name: "long-analysis",
  arguments: { datasetId: "123" },
});

for await (const msg of stream) {
  if ("task" in msg.result) {
    console.log("Task:", msg.result.task.status);
  } else {
    console.log("Result:", msg.result);
  }
}

// Or poll manually
const task = await client.experimental.tasks.getTask(taskId);
const result = await client.experimental.tasks.getTaskResult(taskId);
const tasks = await client.experimental.tasks.listTasks();
await client.experimental.tasks.cancelTask(taskId);
```
