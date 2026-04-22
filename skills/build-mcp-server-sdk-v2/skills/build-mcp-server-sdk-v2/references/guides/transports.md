# Transports (v2)

v2 transport architecture: web-standard core (`WebStandardStreamableHTTPServerTransport`) + Node.js shim (`NodeStreamableHTTPServerTransport`) + framework adapters. SSE server transport removed.

## Transport selection

| Transport | Package | Use when |
|---|---|---|
| `StdioServerTransport` | `@modelcontextprotocol/server` | Local CLI tools, editor integrations |
| `NodeStreamableHTTPServerTransport` | `@modelcontextprotocol/node` | Node.js HTTP servers |
| `WebStandardStreamableHTTPServerTransport` | `@modelcontextprotocol/server` | Deno, Bun, Cloudflare Workers |

## StdioServerTransport

```typescript
import { StdioServerTransport } from "@modelcontextprotocol/server";

const transport = new StdioServerTransport();
// Or with custom streams:
const transport = new StdioServerTransport(customStdin, customStdout);

await server.connect(transport);
```

All logging to stderr. stdout = JSON-RPC only.

## NodeStreamableHTTPServerTransport

```typescript
import { NodeStreamableHTTPServerTransport } from "@modelcontextprotocol/node";

const transport = new NodeStreamableHTTPServerTransport({
  sessionIdGenerator: () => randomUUID(),     // undefined = stateless
  onsessioninitialized: (sid) => { ... },
  onsessionclosed: (sid) => { ... },
  enableJsonResponse: false,                  // true = JSON-only (no SSE)
  eventStore: myEventStore,                   // for resumability
  retryInterval: 1000,                        // SSE retry (ms)
});

// Node.js IncomingMessage/ServerResponse API
await transport.handleRequest(req, res, req.body);

// SSE control
transport.closeSSEStream(requestId);
transport.closeStandaloneSSEStream();
```

Reads `req.auth` (set by auth middleware) and forwards as `authInfo`.

## WebStandardStreamableHTTPServerTransport

```typescript
import { WebStandardStreamableHTTPServerTransport } from "@modelcontextprotocol/server";

const transport = new WebStandardStreamableHTTPServerTransport({
  sessionIdGenerator: () => crypto.randomUUID(),
});

// Web Standard Request/Response API
const response: Response = await transport.handleRequest(request, {
  parsedBody: await request.json(),
  authInfo: verifiedAuth,
});
```

Same options as `NodeStreamableHTTPServerTransport`. Works on any Web Streams-capable runtime.

## EventStore for resumability

```typescript
interface EventStore {
  storeEvent(streamId: string, message: JSONRPCMessage): Promise<string>;
  getStreamIdForEventId?(eventId: string): Promise<string | undefined>;
  replayEventsAfter(
    lastEventId: string,
    { send }: { send: (eventId: string, message: JSONRPCMessage) => Promise<void> }
  ): Promise<string>;
}
```

Use `InMemoryEventStore` for development. Implement with Redis/DB for production.

## Removed in v2

- `SSEServerTransport` — use Streamable HTTP instead
- `allowedHosts`/`allowedOrigins`/`enableDnsRebindingProtection` on transport — use framework middleware
- `StreamableHTTPServerTransport` from SDK — renamed to `NodeStreamableHTTPServerTransport` in `@modelcontextprotocol/node`
