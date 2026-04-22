# Sessions and Lifecycle

Session management is relevant only for Streamable HTTP transport. Stdio transport uses a single connection that lives as long as the process.

## Session model

Each MCP session represents one client connection. The flow:

1. Client sends `initialize` request → server creates transport + session ID
2. Server returns session ID in `Mcp-Session-Id` response header
3. Client includes `mcp-session-id` in all subsequent requests
4. Client opens SSE stream via `GET /mcp` for server-initiated messages
5. Client ends session via `DELETE /mcp`

## Managing transport instances

The server must track active transports by session ID:

```typescript
const transports: Record<string, StreamableHTTPServerTransport> = {};

// In POST handler — new session:
const transport = new StreamableHTTPServerTransport({
  sessionIdGenerator: () => randomUUID(),
  onsessioninitialized: (sid) => {
    transports[sid] = transport;
  },
  onsessionclosed: (sid) => {
    delete transports[sid];
  },
});

transport.onclose = () => {
  const sid = transport.sessionId;
  if (sid) delete transports[sid];
};
```

## Accessing session in handlers

The `extra` argument passed to every handler includes `sessionId`:

```typescript
server.registerTool("user-data", {
  description: "Get user data for the current session",
  inputSchema: { key: z.string() },
}, async ({ key }, extra) => {
  const sessionId = extra.sessionId;
  // Use sessionId to look up per-session state
  const data = sessionStore.get(sessionId, key);
  return {
    content: [{ type: "text", text: JSON.stringify(data) }],
  };
});
```

## Per-session server instances

For servers that need isolated state per client, create a new `McpServer` per session:

```typescript
app.post("/mcp", async (req, res) => {
  const sessionId = req.headers["mcp-session-id"] as string | undefined;

  if (sessionId && transports[sessionId]) {
    await transports[sessionId].handleRequest(req, res, req.body);
    return;
  }

  if (!sessionId && isInitializeRequest(req.body)) {
    const transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: () => randomUUID(),
      onsessioninitialized: (sid) => { transports[sid] = transport; },
    });

    // Each session gets its own server with isolated state
    const server = createServer();
    await server.connect(transport);
    await transport.handleRequest(req, res, req.body);
    return;
  }
});
```

## Shared server instance

For stateless tools or shared resources, reuse one server across sessions:

```typescript
const server = new McpServer({ name: "shared", version: "1.0.0" });
// register tools once...

// But still need per-session transports for the HTTP layer
app.post("/mcp", async (req, res) => {
  // ... transport management stays per-session
});
```

## Sending notifications to clients

Use the server's notification methods or `extra.sendNotification` within handlers:

```typescript
// From within a handler — notify only the requesting client:
server.registerTool("long-task", config, async (args, extra) => {
  await extra.sendNotification({
    method: "notifications/progress",
    params: { progress: 50, total: 100 },
  });
  // ... continue processing ...
});

// From outside a handler — broadcast to all connected clients:
server.sendLoggingMessage({
  level: "info",
  data: "Server configuration updated",
});
```

## Graceful shutdown

Always clean up transports and connections on shutdown:

```typescript
async function shutdown() {
  console.error("Shutting down...");

  // Close all transports (sends session-end to connected clients)
  const closePromises = Object.values(transports).map((t) =>
    t.close().catch(() => {})
  );
  await Promise.all(closePromises);

  // Close the HTTP server
  httpServer.close();
  process.exit(0);
}

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
```

## Elicitation (requesting user input)

Elicitation lets the server ask the client's user for input. Access via `server.server`:

```typescript
const result = await server.server.elicitInput({
  message: "Please provide your API key",
  requestedSchema: {
    type: "object",
    properties: {
      apiKey: { type: "string", title: "API Key" },
    },
    required: ["apiKey"],
  },
});

if (result.action === "accept") {
  const apiKey = result.content.apiKey;
}
```

## Sampling (requesting LLM completions)

Sampling lets the server ask the client to generate an LLM completion:

```typescript
const result = await server.server.createMessage({
  messages: [
    { role: "user", content: { type: "text", text: "Summarize this data..." } },
  ],
  maxTokens: 500,
});
```

Both elicitation and sampling require the client to declare support for these capabilities.
