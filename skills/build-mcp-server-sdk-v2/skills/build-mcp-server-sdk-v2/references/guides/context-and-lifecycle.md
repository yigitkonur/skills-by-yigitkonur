# ServerContext and Lifecycle (v2)

v2 replaces v1's flat `RequestHandlerExtra` with a structured `ServerContext`.

## ServerContext — full definition

```typescript
type ServerContext = BaseContext & {
  mcpReq: {
    log: (level: LoggingLevel, data: unknown, logger?: string) => Promise<void>;
    elicitInput: (params: ElicitRequestFormParams | ElicitRequestURLParams) => Promise<ElicitResult>;
    requestSampling: (params: CreateMessageRequest['params']) => Promise<CreateMessageResult>;
  };
  http?: {
    req?: RequestInfo;
    closeSSE?: () => void;
    closeStandaloneSSE?: () => void;
  };
};

type BaseContext = {
  sessionId?: string;
  mcpReq: {
    id: RequestId;
    method: string;
    _meta?: RequestMeta;
    signal: AbortSignal;
    send: (request, schema, options?) => Promise<Result>;
    notify: (notification) => Promise<void>;
  };
  http?: {
    authInfo?: AuthInfo;
  };
  task?: TaskContext;
};
```

## Using context in handlers

### Logging

```typescript
server.registerTool("process", config, async (args, ctx) => {
  await ctx.mcpReq.log("info", "Starting processing");
  // ... work ...
  await ctx.mcpReq.log("info", { processed: 42, total: 100 });
  return { content: [{ type: "text" as const, text: "Done" }] };
});
```

Levels: `debug`, `info`, `notice`, `warning`, `error`, `critical`, `alert`, `emergency`.

### Elicitation (requesting user input)

```typescript
server.registerTool("configure", config, async (args, ctx) => {
  // Form mode — structured data
  const result = await ctx.mcpReq.elicitInput({
    mode: "form",
    message: "Configure settings:",
    requestedSchema: {
      type: "object",
      properties: {
        region: { type: "string", enum: ["us-east", "eu-west"] },
        debug: { type: "boolean", default: false },
      },
      required: ["region"],
    },
  });

  if (result.action === "accept") {
    return { content: [{ type: "text" as const, text: `Region: ${result.content.region}` }] };
  }
  return { content: [{ type: "text" as const, text: "Configuration cancelled" }], isError: true };
});
```

### Sampling (requesting LLM completion)

```typescript
server.registerTool("summarize", config, async (args, ctx) => {
  const result = await ctx.mcpReq.requestSampling({
    messages: [{
      role: "user",
      content: { type: "text", text: `Summarize: ${args.text}` },
    }],
    maxTokens: 200,
  });

  return { content: [{ type: "text" as const, text: result.content.text }] };
});
```

### Cancellation

```typescript
server.registerTool("long-task", config, async (args, ctx) => {
  for (const chunk of chunks) {
    if (ctx.mcpReq.signal.aborted) {
      return { content: [{ type: "text" as const, text: "Cancelled" }], isError: true };
    }
    await processChunk(chunk);
  }
  return { content: [{ type: "text" as const, text: "Done" }] };
});
```

### Progress notifications

```typescript
server.registerTool("import", config, async (args, ctx) => {
  const progressToken = ctx.mcpReq._meta?.progressToken;

  for (let i = 0; i < total; i++) {
    if (progressToken !== undefined) {
      await ctx.mcpReq.notify({
        method: "notifications/progress",
        params: { progressToken, progress: i, total, message: `${i}/${total}` },
      });
    }
    await processItem(i);
  }
  return { content: [{ type: "text" as const, text: `Imported ${total} items` }] };
});
```

### SSE stream control (polling pattern)

```typescript
server.registerTool("async-op", config, async (args, ctx) => {
  // Disconnect client's SSE stream — they'll reconnect with Last-Event-ID
  ctx.http?.closeSSE?.();

  // Continue processing — events queued in EventStore
  const result = await longRunningWork(args);
  return { content: [{ type: "text" as const, text: result }] };
});
```

## Session management

```typescript
const transports: Record<string, NodeStreamableHTTPServerTransport> = {};

// Per-session server isolation
app.post("/mcp", async (req, res) => {
  const sessionId = req.headers["mcp-session-id"] as string | undefined;

  if (sessionId && transports[sessionId]) {
    await transports[sessionId].handleRequest(req, res, req.body);
    return;
  }

  if (!sessionId && isInitializeRequest(req.body)) {
    const transport = new NodeStreamableHTTPServerTransport({
      sessionIdGenerator: () => randomUUID(),
      onsessioninitialized: (sid) => { transports[sid] = transport; },
    });
    transport.onclose = () => {
      const sid = transport.sessionId;
      if (sid) delete transports[sid];
    };
    const server = createServer(); // Fresh McpServer per session
    await server.connect(transport);
    await transport.handleRequest(req, res, req.body);
    return;
  }
});
```

## Graceful shutdown

```typescript
const httpServer = app.listen(3000);

async function shutdown() {
  for (const transport of Object.values(transports)) {
    try { await transport.close(); } catch { /* ignore */ }
  }
  httpServer.close();
  process.exit(0);
}

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
```
