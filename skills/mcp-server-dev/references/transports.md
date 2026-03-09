# Transports Reference

Transports define how MCP clients communicate with your server. Choose the right transport based on your deployment target.

## Transport Decision Matrix

| Transport | Use Case | Clients | Scalability | Complexity |
|-----------|----------|---------|-------------|------------|
| stdio | Claude Desktop, CLI tools | Single | Process-bound | Minimal |
| Streamable HTTP (stateless) | Production APIs, serverless | Multi | Horizontal | Moderate |
| Streamable HTTP (stateful) | Sessions, resumability | Multi | Per-session | Moderate |
| SSE | **Deprecated** | Multi | Limited | N/A — migrate |

## stdio Transport

For local, process-spawned integrations. The client starts your server as a subprocess.

```typescript
import { McpServer } from '@modelcontextprotocol/server';
import { StdioServerTransport } from '@modelcontextprotocol/server/stdio';

const server = new McpServer({ name: 'my-server', version: '1.0.0' });

// Register tools, resources, prompts...

const transport = new StdioServerTransport();
await server.connect(transport);
```

**Claude Desktop config:**

```json
{
  "mcpServers": {
    "my-server": {
      "command": "npx",
      "args": ["-y", "tsx", "/absolute/path/to/src/index.ts"],
      "env": {
        "API_KEY": "your-key"
      }
    }
  }
}
```

**Important:**
- Use absolute paths
- Pass secrets via `env`, never hardcode in `args`
- Use `npx -y` for zero-install execution of published packages
- Set `cwd` when the server needs access to project files
- Log to stderr only — stdout is reserved for MCP protocol messages

## Streamable HTTP Transport (Recommended for Production)

Streamable HTTP replaced the legacy SSE transport. It supports request/response, SSE notifications, JSON-only mode, and session management.

### Stateless (Simplest)

No session tracking. Ideal for simple API-style servers and serverless deployment:

```typescript
import { McpServer } from '@modelcontextprotocol/server';
import { createMcpExpressApp } from '@modelcontextprotocol/express';
import { NodeStreamableHTTPServerTransport } from '@modelcontextprotocol/node';

// Option A: Express with DNS rebinding protection (recommended for localhost)
const app = createMcpExpressApp();

app.post('/mcp', async (req, res) => {
  const server = new McpServer({ name: 'my-server', version: '1.0.0' });
  // Register tools...
  const transport = new NodeStreamableHTTPServerTransport({
    sessionIdGenerator: undefined, // stateless
  });
  await server.connect(transport);
  await transport.handleRequest(req, res, req.body);
});

app.listen(3000, '127.0.0.1');
```

### Stateful (Sessions)

Session persistence for multi-turn interactions:

```typescript
import { randomUUID } from 'node:crypto';
import { createMcpExpressApp } from '@modelcontextprotocol/express';
import { NodeStreamableHTTPServerTransport } from '@modelcontextprotocol/node';

const app = createMcpExpressApp();
const sessions = new Map<string, McpServer>();

app.post('/mcp', async (req, res) => {
  const sessionId = req.headers['mcp-session-id'] as string | undefined;

  if (sessionId && sessions.has(sessionId)) {
    // Resume existing session
    const server = sessions.get(sessionId)!;
    // ... handle request
  } else {
    // New session
    const server = new McpServer({ name: 'my-server', version: '1.0.0' });
    // Register tools...
    const transport = new NodeStreamableHTTPServerTransport({
      sessionIdGenerator: () => randomUUID(),
    });
    await server.connect(transport);
    await transport.handleRequest(req, res, req.body);
  }
});
```

### JSON Response Mode

No SSE streaming — plain JSON responses to every POST:

```typescript
const transport = new NodeStreamableHTTPServerTransport({
  sessionIdGenerator: () => randomUUID(),
  enableJsonResponse: true,
});
```

## DNS Rebinding Protection

If your server listens on localhost, use `createMcpExpressApp()` or `createMcpHonoApp()` — they validate the `Host` header by default:

```typescript
import { createMcpExpressApp } from '@modelcontextprotocol/express';

const app = createMcpExpressApp(); // Host header validation included
```

Do NOT use `NodeStreamableHTTPServerTransport` directly on localhost without this protection.

## Migrating SSE to Streamable HTTP

SSE was deprecated in March 2025. Migration steps:

1. Replace `SSEServerTransport` with `NodeStreamableHTTPServerTransport`
2. Change client endpoint from `/sse` + `/messages` to single `/mcp` path
3. Update Claude Desktop config if using URL-based connection

```typescript
// Before (deprecated)
import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';

// After
import { NodeStreamableHTTPServerTransport } from '@modelcontextprotocol/node';

const transport = new NodeStreamableHTTPServerTransport({
  sessionIdGenerator: undefined, // or () => randomUUID()
});
```

## Client Configuration for Remote Servers

```json
{
  "mcpServers": {
    "remote-server": {
      "url": "https://api.example.com/mcp",
      "headers": {
        "Authorization": "Bearer your-token"
      }
    }
  }
}
```
