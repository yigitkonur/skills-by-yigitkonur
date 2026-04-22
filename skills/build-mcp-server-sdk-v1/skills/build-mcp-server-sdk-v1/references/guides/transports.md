# Transports

MCP servers communicate with clients over a transport layer. Source-verified against `v1.x` branch of `modelcontextprotocol/typescript-sdk`.

## Transport selection

| Transport | Use when | Clients | Infrastructure |
|---|---|---|---|
| **stdio** | Local CLI tools, editor integrations | Single | None — child process |
| **Streamable HTTP (stateful)** | Remote servers, multi-client, needs sessions | Multiple | HTTP server |
| **Streamable HTTP (stateless)** | Simple remote API wrappers | Multiple | HTTP server |
| ~~SSE~~ | Legacy clients only | Multiple | HTTP server |

## Transport interface

All transports implement:

```typescript
interface Transport {
  start(): Promise<void>;
  close(): Promise<void>;
  send(message: JSONRPCMessage, options?: { relatedRequestId?: RequestId }): Promise<void>;
  onclose?: () => void;
  onerror?: (error: Error) => void;
  onmessage?: (message: JSONRPCMessage, extra?: MessageExtraInfo) => void;
  sessionId?: string;
}
```

## StdioServerTransport

Zero infrastructure. The client spawns the server as a child process.

```typescript
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

class StdioServerTransport implements Transport {
  constructor(
    stdin: Readable = process.stdin,
    stdout: Writable = process.stdout
  )
  async start(): Promise<void>
  async close(): Promise<void>
  async send(message: JSONRPCMessage): Promise<void>
}
```

Rules for stdio:
- **All logging must go to stderr** — stdout is reserved for JSON-RPC messages
- Messages are newline-delimited and MUST NOT contain embedded newlines
- Custom streams: `new StdioServerTransport(customStdin, customStdout)`

```typescript
const server = new McpServer({ name: "my-server", version: "1.0.0" });
const transport = new StdioServerTransport();
await server.connect(transport);

process.on("SIGINT", async () => {
  await server.close();
  process.exit(0);
});
```

## StreamableHTTPServerTransport (Node.js)

A thin Node.js wrapper over `WebStandardStreamableHTTPServerTransport` using `@hono/node-server`. Both expose identical public methods.

### Source-verified constructor and options

```typescript
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";

type StreamableHTTPServerTransportOptions = {
  sessionIdGenerator?: () => string;              // undefined = stateless
  onsessioninitialized?: (sessionId: string) => void | Promise<void>;
  onsessionclosed?: (sessionId: string) => void | Promise<void>;
  enableJsonResponse?: boolean;                   // Default: false (SSE)
  eventStore?: EventStore;                        // For resumability
  retryInterval?: number;                         // SSE retry suggestion (ms)
  supportedProtocolVersions?: string[];
  // @deprecated — use hostHeaderValidation middleware instead:
  allowedHosts?: string[];
  allowedOrigins?: string[];
  enableDnsRebindingProtection?: boolean;
};

class StreamableHTTPServerTransport implements Transport {
  constructor(options?: StreamableHTTPServerTransportOptions)
  get sessionId(): string | undefined
  async start(): Promise<void>
  async close(): Promise<void>
  async send(message: JSONRPCMessage, options?: { relatedRequestId?: RequestId }): Promise<void>
  async handleRequest(
    req: IncomingMessage & { auth?: AuthInfo },
    res: ServerResponse,
    parsedBody?: unknown
  ): Promise<void>
  closeSSEStream(requestId: RequestId): void
  closeStandaloneSSEStream(): void
}
```

### Stateful HTTP server pattern

```typescript
import express from "express";
import { randomUUID } from "node:crypto";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { createMcpExpressApp } from "@modelcontextprotocol/sdk/server/express.js";
import { isInitializeRequest } from "@modelcontextprotocol/sdk/types.js";

const app = createMcpExpressApp();
const transports: Record<string, StreamableHTTPServerTransport> = {};

function createServer(): McpServer {
  const server = new McpServer({ name: "my-server", version: "1.0.0" });
  // register tools, resources, prompts...
  return server;
}

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
    transport.onclose = () => {
      const sid = transport.sessionId;
      if (sid) delete transports[sid];
    };
    const server = createServer();
    await server.connect(transport);
    await transport.handleRequest(req, res, req.body);
    return;
  }
  res.status(400).json({ jsonrpc: "2.0", error: { code: -32000, message: "Bad Request" }, id: null });
});

app.get("/mcp", async (req, res) => {
  const sid = req.headers["mcp-session-id"] as string;
  if (!sid || !transports[sid]) { res.status(400).send("Invalid session"); return; }
  await transports[sid].handleRequest(req, res);
});

app.delete("/mcp", async (req, res) => {
  const sid = req.headers["mcp-session-id"] as string;
  if (sid && transports[sid]) await transports[sid].handleRequest(req, res);
  res.status(200).end();
});

app.listen(3000, () => console.error("MCP server on :3000"));
```

### Stateless HTTP server

```typescript
const transport = new StreamableHTTPServerTransport({
  sessionIdGenerator: undefined,
});
const server = new McpServer({ name: "stateless", version: "1.0.0" });
await server.connect(transport);

app.post("/mcp", async (req, res) => {
  await transport.handleRequest(req, res, req.body);
});
```

### EventStore interface (source-verified)

```typescript
type StreamId = string;
type EventId = string;

interface EventStore {
  storeEvent(streamId: StreamId, message: JSONRPCMessage): Promise<EventId>;
  getStreamIdForEventId?(eventId: EventId): Promise<StreamId | undefined>;
  replayEventsAfter(
    lastEventId: EventId,
    { send }: { send: (eventId: EventId, message: JSONRPCMessage) => Promise<void> }
  ): Promise<StreamId>;
}
```

`getStreamIdForEventId` is optional. Use `InMemoryEventStore` for development; implement with Redis/DB for production.

### SSE polling via server-side disconnect (SEP-1699)

Use `closeSSEStream(requestId)` to close a specific request's SSE stream, or `closeStandaloneSSEStream()` to close the GET notification stream. Clients reconnect with `Last-Event-ID`.

## DNS rebinding protection

### createMcpExpressApp (recommended)

```typescript
import { createMcpExpressApp } from "@modelcontextprotocol/sdk/server/express.js";

interface CreateMcpExpressAppOptions {
  host?: string;              // Defaults to '127.0.0.1'
  allowedHosts?: string[];
}

function createMcpExpressApp(options?: CreateMcpExpressAppOptions): Express;
```

Auto-applies `localhostHostValidation()` when host is `127.0.0.1`, `localhost`, or `::1`. Warns when binding to `0.0.0.0` without `allowedHosts`.

### hostHeaderValidation middleware

```typescript
import {
  hostHeaderValidation,
  localhostHostValidation,
} from "@modelcontextprotocol/sdk/server/middleware/hostHeaderValidation.js";

function hostHeaderValidation(allowedHostnames: string[]): RequestHandler;
function localhostHostValidation(): RequestHandler;
```

Returns 403 with JSON-RPC error body on failure.

## WebStandardStreamableHTTPServerTransport

For Deno, Bun, Cloudflare Workers:

```typescript
import { WebStandardStreamableHTTPServerTransport }
  from "@modelcontextprotocol/sdk/server/webStandardStreamableHttp.js";

class WebStandardStreamableHTTPServerTransport implements Transport {
  constructor(options?: WebStandardStreamableHTTPServerTransportOptions)
  async handleRequest(req: Request, options?: HandleRequestOptions): Promise<Response>
  closeSSEStream(requestId: RequestId): void
  closeStandaloneSSEStream(): void
}

interface HandleRequestOptions {
  parsedBody?: unknown;
  authInfo?: AuthInfo;
}
```

Returns a Web API `Response` object. Same options as `StreamableHTTPServerTransport`.

## SSEServerTransport (deprecated)

```typescript
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";

// @deprecated — use StreamableHTTPServerTransport
class SSEServerTransport implements Transport {
  constructor(endpoint: string, res: ServerResponse, options?: SSEServerTransportOptions)
  get sessionId(): string
  async handlePostMessage(req, res, parsedBody?): Promise<void>
  async handleMessage(message, extra?): Promise<void>
}
```

## Graceful shutdown for HTTP servers

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
