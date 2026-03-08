# Server Creation Patterns

## Overview

This reference covers how MCP servers are created across three approaches: the official TypeScript SDK, mcp-use TypeScript, and mcp-use Python.

## Official TypeScript SDK (`@modelcontextprotocol/sdk`)

### Two-Level Architecture

The official SDK has two server classes:

1. **`McpServer`** (high-level) — ergonomic API with `registerTool()`, `registerResource()`, `registerPrompt()`
2. **`Server`** (low-level) — raw JSON-RPC protocol handler with `setRequestHandler()`

```typescript
import { McpServer } from '@modelcontextprotocol/server';

// High-level
const server = new McpServer(
    { name: 'my-server', version: '1.0.0' },    // Implementation info
    {                                              // ServerOptions
        capabilities: {
            tools: {},
            resources: { listChanged: true },
            prompts: { listChanged: true },
            logging: {}
        },
        instructions: 'Instructions for the LLM client'
    }
);
```

```typescript
import { Server } from '@modelcontextprotocol/server';

// Low-level
const server = new Server(
    { name: 'my-server', version: '1.0.0' },
    { capabilities: { tools: {} } }
);
server.setRequestHandler('tools/list', async () => ({
    tools: [{ name: 'add', inputSchema: { type: 'object', properties: { a: { type: 'number' } } } }]
}));
server.setRequestHandler('tools/call', async (request) => {
    // Handle tool calls manually
});
```

### Transport Setup (Manual)

```typescript
import { StdioServerTransport } from '@modelcontextprotocol/server';

const transport = new StdioServerTransport();
await server.connect(transport);  // Blocks until stdin closes
```

For HTTP, you must wire up Express/Hono + StreamableHTTPServerTransport manually (see migrating-from-ts-sdk.md).

## mcp-use TypeScript (`mcp-use/server`)

### Single MCPServer Class

mcp-use provides a production-focused `MCPServer` with MCP primitives (`tool`, `resource`, `resourceTemplate`, `prompt`, `uiResource`) and a built-in Hono app for custom routes/middleware.

```typescript
import {
    MCPServer,
    RedisSessionStore,
    RedisStreamManager,
    oauthAuth0Provider,
} from 'mcp-use/server'

const server = new MCPServer({
    // Required
    name: 'my-server',
    version: '1.0.0',

    // Identity / metadata
    title: 'My Server',
    description: 'What this server does',
    websiteUrl: 'https://myserver.com',
    favicon: 'favicon.ico',

    // Network
    host: 'localhost',
    baseUrl: 'https://myserver.com',

    // CORS policy (replaces defaults when set)
    cors: {
        origin: ['https://app.example.com'],
        allowMethods: ['GET', 'POST', 'OPTIONS'],
        exposeHeaders: ['mcp-session-id'],
    },

    // DNS rebinding protection (Host validation)
    allowedOrigins: ['https://app.example.com'],

    // Sessions / streams
    sessionIdleTimeoutMs: 86400000,
    sessionStore: new RedisSessionStore({ client: redis }),
    streamManager: new RedisStreamManager({ client: redis, pubSubClient: pubSubRedis }),

    // Authentication
    oauth: oauthAuth0Provider({ domain: 'your-tenant.auth0.com', audience: 'https://your-api.example.com' }),
})
```

### Starting the Server

```typescript
// Programmatic HTTP start
await server.listen(3000)
// → http://localhost:3000/mcp
// → http://localhost:3000/inspector

// Custom middleware/routes via Hono app
server.app.use('/api/admin/*', async (c, next) => {
    // auth check ...
    await next()
})

server.app.get('/health', (c) => c.json({ status: 'ok' }))
```

```bash
# CLI workflow (official)
mcp-use dev
mcp-use build
mcp-use start
mcp-use deploy
```

### ServerConfig (high-signal fields)

```typescript
interface ServerConfig {
    // Required
    name: string
    version: string

    // Identity
    title?: string
    description?: string
    websiteUrl?: string
    favicon?: string
    icons?: Array<{ src: string; mimeType?: string; sizes?: string[] }>

    // Network
    host?: string
    baseUrl?: string
    cors?: {
        origin?: string | string[]
        allowMethods?: string[]
        allowHeaders?: string[]
        exposeHeaders?: string[]
    }
    allowedOrigins?: string[] // Host header validation (DNS rebinding protection)

    // Transport/session mode
    stateless?: boolean
    sessionIdleTimeoutMs?: number
    sessionStore?: SessionStore
    streamManager?: StreamManager

    // Auth
    oauth?: OAuthProvider
}
```

### How It Works Internally (Practical View)

1. `new MCPServer(config)` initializes MCP capabilities + HTTP app plumbing.
2. MCP routes (`/mcp`, widgets assets path, `/inspector`) are registered internally.
3. Session mode is auto-detected unless `stateless` is explicitly forced.
4. `listen(port)` starts the server; clients connect using standard MCP transport headers.

## mcp-use Python (`mcp_use.server`)

### MCPServer Class (extends FastMCP)

```python
from mcp_use import MCPServer

server = MCPServer(
    name="my-server",
    # Extends FastMCP from official Python SDK
)

@server.tool(name="greet", description="Greet someone")
async def greet(name: str) -> str:
    return f"Hello, {name}!"

@server.resource(uri="info://version", name="version")
async def version() -> str:
    return "1.0.0"

@server.prompt(name="review", title="Code Review")
def review_prompt(code: str) -> str:
    return f"Please review:\n{code}"

# Run the server
server.run()  # or use with uvicorn for HTTP
```

### Python MCPRouter (Modular Organization)

```python
from mcp_use.server import MCPRouter

# math_routes.py
router = MCPRouter()

@router.tool()
def add(a: int, b: int) -> int:
    return a + b

@router.tool()
def multiply(a: int, b: int) -> int:
    return a * b

# main.py
from mcp_use.server import MCPServer
from math_routes import router as math_router

server = MCPServer(name="calculator")
server.include_router(math_router, prefix="math")
# Tools become: math_add, math_multiply
```

### Python Authentication

```python
from mcp_use.server.auth import BearerAuthProvider

server = MCPServer(
    name="protected-server",
    auth=BearerAuthProvider(token="secret-token"),
)
```

## Comparison Table

| Aspect | Official TS SDK | mcp-use TS | mcp-use Python |
|---|---|---|---|
| Class | `McpServer` + `Server` | `MCPServer` (single) | `MCPServer` (extends FastMCP) |
| Transport | Manual setup | Built-in via `listen()` + CLI (`dev/build/start`) | Built-in via `run()` |
| HTTP Framework | BYO (Express/Hono) | Built-in Hono integration (`server.app`) | Built-in (Starlette) |
| Session Storage | Manual Map tracking | Pluggable: InMemory / FileSystem / Redis + optional RedisStreamManager | Via FastMCP |
| OAuth | Manual implementation | Built-in providers (`oauth*Provider`) | BearerAuthProvider |
| Schema | Zod v4 | Zod | Pydantic + Field |
| CLI | None | `mcp-use dev/build/start/deploy/login/...` | None |
| HMR | None | `mcp-use dev` | None |
| Inspector | Separate package | Built-in at `/inspector` | Built-in debug mode |
| Response helpers | None | `text()`, `object()`, etc. | Return strings/dicts |
| Routing | None | Hono routes via `server.app` | MCPRouter |
| Middleware | None | Hono middleware via `server.app.use` | Custom Middleware class |
