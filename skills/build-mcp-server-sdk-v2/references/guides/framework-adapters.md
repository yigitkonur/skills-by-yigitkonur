# Framework Adapters (v2)

v2 provides dedicated adapter packages for Express and Hono. These replace v1's built-in `createMcpExpressApp()`. `@modelcontextprotocol/hono` is the official SDK adapter package; `@hono/mcp` is a community Hono middleware package with a different API and must not be substituted silently.

## Express adapter

```bash
npm install --save-exact @modelcontextprotocol/express@2.0.0-alpha.2
npm install express
```

```typescript
import { createMcpExpressApp } from "@modelcontextprotocol/express";

interface CreateMcpExpressAppOptions {
  host?: string;           // Default: '127.0.0.1'
  allowedHosts?: string[]; // Explicit allowlist
}

const app = createMcpExpressApp({ host: "127.0.0.1" });
```

What it wires up:
- `express.json()` body parser
- Localhost DNS rebinding protection (auto-enabled for `127.0.0.1`, `localhost`, `::1`)
- Custom host validation when `allowedHosts` is provided
- Warning when binding to `0.0.0.0` without `allowedHosts`

### Express middleware exports

```typescript
import {
  hostHeaderValidation,
  localhostHostValidation,
} from "@modelcontextprotocol/express";

// Custom host allowlist
app.use(hostHeaderValidation(["api.example.com", "mcp.example.com"]));

// Localhost-only (127.0.0.1, localhost, [::1])
app.use(localhostHostValidation());
```

## Hono adapter

```bash
npm install --save-exact @modelcontextprotocol/hono@2.0.0-alpha.2
npm install hono
```

```typescript
import { createMcpHonoApp } from "@modelcontextprotocol/hono";

const app = createMcpHonoApp({ host: "127.0.0.1" });
```

Same DNS rebinding logic as Express. Additionally installs JSON body-parsing middleware that stashes parsed body in `c.set('parsedBody', ...)` for MCP transport consumption.

If a repo imports `@hono/mcp`, pause before applying these examples. Decide whether to keep the community middleware API or migrate to the official `@modelcontextprotocol/hono` adapter.

### Hono middleware exports

```typescript
import {
  hostHeaderValidation,
  localhostHostValidation,
} from "@modelcontextprotocol/hono";
```

## Node.js transport (required for HTTP)

```bash
npm install --save-exact @modelcontextprotocol/node@2.0.0-alpha.2
```

```typescript
import { NodeStreamableHTTPServerTransport } from "@modelcontextprotocol/node";

// Same options as v1's StreamableHTTPServerTransport
const transport = new NodeStreamableHTTPServerTransport({
  sessionIdGenerator: () => randomUUID(),
  onsessioninitialized: (sid) => { transports[sid] = transport; },
  eventStore: myEventStore,    // For resumability
  retryInterval: 1000,         // SSE retry hint (ms)
});
```

`NodeStreamableHTTPServerTransport` is a thin Node.js shim over `WebStandardStreamableHTTPServerTransport`. It bridges `IncomingMessage`/`ServerResponse` to Web Standard `Request`/`Response` using `@hono/node-server`.

It reads `req.auth` (set by auth middleware) and forwards it as `authInfo` to the inner transport.

## Web-standard transport (Deno, Bun, Workers)

For non-Node.js runtimes, use the web-standard transport directly:

```typescript
import { WebStandardStreamableHTTPServerTransport } from "@modelcontextprotocol/server";

const transport = new WebStandardStreamableHTTPServerTransport({
  sessionIdGenerator: () => crypto.randomUUID(),
});

// Returns a Web API Response
const response = await transport.handleRequest(request, {
  parsedBody: await request.json(),
  authInfo: verifiedAuth,
});
```

## v1 → v2 transport migration

| v1 | v2 |
|---|---|
| `import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js"` | `import { NodeStreamableHTTPServerTransport } from "@modelcontextprotocol/node"` |
| `import { createMcpExpressApp } from "@modelcontextprotocol/sdk/server/express.js"` | `import { createMcpExpressApp } from "@modelcontextprotocol/express"` |
| `SSEServerTransport` | Removed — use Streamable HTTP |
| DNS rebinding on transport (`allowedHosts`) | DNS rebinding on middleware (`hostHeaderValidation`) |
