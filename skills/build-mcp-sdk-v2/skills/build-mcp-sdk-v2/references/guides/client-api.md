# Client API (v2)

Build MCP clients using `@modelcontextprotocol/client`.

## Setup

```bash
npm install @modelcontextprotocol/client
```

```typescript
import { Client, StdioClientTransport } from "@modelcontextprotocol/client";

const client = new Client(
  { name: "my-client", version: "1.0.0" },
  {
    capabilities: {
      sampling: { tools: {} },
      elicitation: { form: {}, url: {} },
      roots: { listChanged: true },
    },
    listChanged: {
      tools: { onChanged: (err, tools) => console.log("Tools updated") },
    },
  }
);
```

## Connecting

```typescript
// stdio (local server)
import { StdioClientTransport } from "@modelcontextprotocol/client";
const transport = new StdioClientTransport({
  command: "node", args: ["server.js"],
  env: { API_KEY: process.env.API_KEY },
});
await client.connect(transport);

// Streamable HTTP (remote server)
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/client";
const transport = new StreamableHTTPClientTransport(
  new URL("http://localhost:3000/mcp"),
  { authProvider: myOAuthProvider }
);
await client.connect(transport);
```

## Core methods

```typescript
const { tools } = await client.listTools();
const result = await client.callTool({ name: "search", arguments: { query: "MCP" } });
const { resources } = await client.listResources();
const { contents } = await client.readResource({ uri: "file:///README.md" });
const { prompts } = await client.listPrompts();
const { messages } = await client.getPrompt({ name: "review", arguments: { code: "..." } });
await client.ping();
await client.close();
```

## Authentication

### Simple auth provider (new in v2)

```typescript
const transport = new StreamableHTTPClientTransport(url, {
  authProvider: {
    async token() { return process.env.MCP_TOKEN; },
    async onUnauthorized(ctx) { /* handle 401 */ },
  },
});
```

### OAuth client provider

```typescript
import { OAuthClientProvider } from "@modelcontextprotocol/client";

class MyProvider implements OAuthClientProvider {
  get redirectUrl() { return "http://localhost:3000/callback"; }
  get clientMetadata() { return { client_name: "My App", ... }; }
  async tokens() { return storedTokens; }
  async saveTokens(tokens) { storedTokens = tokens; }
  // ... other required methods
}
```

### Built-in providers

```typescript
import { ClientCredentialsProvider, PrivateKeyJwtProvider } from "@modelcontextprotocol/client";

// Machine-to-machine
const provider = new ClientCredentialsProvider({ clientId: "...", clientSecret: "..." });

// JWT-based
const provider = new PrivateKeyJwtProvider({ clientId: "...", privateKey: pemString });
```

## Middleware (new in v2)

```typescript
import { applyMiddlewares, withOAuth, withLogging, createMiddleware } from "@modelcontextprotocol/client";

const middleware = applyMiddlewares(
  withOAuth(oauthProvider),
  withLogging({ logger: console.error }),
);
```

## Disconnect

```typescript
await transport.terminateSession(); // sends DELETE to server
await client.close();
```
