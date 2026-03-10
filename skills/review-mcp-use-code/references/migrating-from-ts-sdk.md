# Migrating from Official MCP TypeScript SDK to mcp-use

## Overview

The official `@modelcontextprotocol/sdk` provides low-level building blocks. mcp-use wraps it and adds production concerns. This guide maps common official SDK patterns to their mcp-use equivalents.

## Package Changes

```
# Official SDK
npm install @modelcontextprotocol/server @modelcontextprotocol/client zod

# mcp-use server framework
npm install mcp-use zod
```

mcp-use provides server APIs under `mcp-use/server` and its own CLI workflow (`dev`, `build`, `start`, `deploy`).

## Import Mapping

| Official SDK | mcp-use |
|---|---|
| `import { McpServer } from '@modelcontextprotocol/server'` | `import { MCPServer } from 'mcp-use/server'` |
| `import { StdioServerTransport } from '@modelcontextprotocol/server'` | Not needed for standard mcp-use HTTP server flow |
| `import { StreamableHTTPServerTransport } from '@modelcontextprotocol/server'` | Not needed — `server.listen()` handles HTTP transport |
| `import { ResourceTemplate } from '@modelcontextprotocol/server'` | `server.resourceTemplate()` |

## Server Creation

### Official SDK

```typescript
import { McpServer } from '@modelcontextprotocol/server';
import { StdioServerTransport } from '@modelcontextprotocol/server';

const server = new McpServer(
    { name: 'my-server', version: '1.0.0' },
    {
        capabilities: {
            tools: {},
            resources: { listChanged: true },
            prompts: { listChanged: true },
            logging: {}
        },
        instructions: 'Server instructions for the client'
    }
);

// Manual transport setup
const transport = new StdioServerTransport();
await server.connect(transport);
```

### mcp-use

```typescript
import { MCPServer } from 'mcp-use/server'

const server = new MCPServer({
    name: 'my-server',
    version: '1.0.0',
    description: 'Server instructions for the client',
    host: 'localhost',
    allowedOrigins: ['https://myapp.com'], // Host header validation (DNS rebinding protection)
    sessionIdleTimeoutMs: 86400000,
})

// One-liner start — handles transport, sessions, CORS, /mcp endpoint
await server.listen(3000)
```

### What changes:
1. **Constructor**: Two-arg `(info, options)` → single config object
2. **Capabilities**: Auto-detected from registrations (no manual declaration)
3. **Transport**: `listen()` handles Streamable HTTP + session lifecycle
4. **Instructions**: `options.instructions` → `config.description`

## Tool Registration

### Official SDK

```typescript
server.registerTool('search', {
    title: 'Search',
    description: 'Search the database',
    inputSchema: z.object({
        query: z.string().describe('Search query'),
        limit: z.number().default(10).describe('Max results')
    }),
    outputSchema: z.object({
        results: z.array(z.object({
            id: z.string(),
            title: z.string(),
            score: z.number()
        }))
    }),
    annotations: {
        readOnlyHint: true,
        openWorldHint: false
    }
}, async ({ query, limit }, ctx) => {
    const results = await db.search(query, limit);
    await ctx.mcpReq.log('info', `Found ${results.length} results`);
    return {
        content: [{ type: 'text', text: JSON.stringify(results) }],
        structuredContent: { results }
    };
});
```

### mcp-use

```typescript
import { text, object } from 'mcp-use/server'

server.tool({
    name: 'search',
    description: 'Search the database',
    schema: z.object({
        query: z.string().describe('Search query'),
        limit: z.number().default(10).describe('Max results')
    }),
    annotations: { readOnlyHint: true },
}, async ({ query, limit }, ctx) => {
    const results = await db.search(query, limit);
    await ctx.log('info', `Found ${results.length} results`);
    return object({ results });
})
```

### What changes:
1. **Method**: `registerTool(name, config, cb)` → `tool(config, cb)` (name moves into config)
2. **Schema key**: `inputSchema` → `schema`
3. **Response**: Manual `{ content: [{ type: 'text', text }] }` → `text()`, `object()`, etc.
4. **Logging**: `ctx.mcpReq.log('info', msg)` → `ctx.log('info', msg)`
5. **Output schema**: Use response helpers and typed structured content

## Resource Registration

### Official SDK — Static Resource

```typescript
server.registerResource('readme', 'docs://readme', {
    title: 'README',
    mimeType: 'text/markdown'
}, async (uri) => ({
    contents: [{ uri: uri.href, text: '# My App\nDocumentation here.' }]
}));
```

### mcp-use — Static Resource

```typescript
import { markdown } from 'mcp-use/server'

server.resource({
    uri: 'docs://readme',
    name: 'README',
    title: 'README',
    mimeType: 'text/markdown',
}, async () => markdown('# My App\nDocumentation here.'))
```

### Official SDK — Dynamic Resource (Template)

```typescript
import { ResourceTemplate } from '@modelcontextprotocol/server';

server.registerResource(
    'user-profile',
    new ResourceTemplate('users://{userId}/profile', {
        list: async () => ({
            resources: users.map(u => ({
                uri: `users://${u.id}/profile`,
                name: u.name
            }))
        })
    }),
    { title: 'User Profile', mimeType: 'application/json' },
    async (uri, { userId }) => ({
        contents: [{ uri: uri.href, text: JSON.stringify(getUser(userId)) }]
    })
);
```

### mcp-use — Dynamic Resource (Template)

```typescript
import { object } from 'mcp-use/server'

server.resourceTemplate({
    uriTemplate: 'users://{userId}/profile',
    name: 'User Profile',
    mimeType: 'application/json',
}, async (uri, { userId }) => object(getUser(userId)))
```

### What changes:
1. **Static**: `registerResource(name, uri, meta, cb)` → `resource(config, cb)`
2. **Template**: `new ResourceTemplate(...)` + `registerResource(...)` → `resourceTemplate(config, cb)`
3. **Response**: Manual `contents: [{ uri, text }]` → response helpers (`text()`, `object()`, etc.)
4. **Listing**: Separate `list` callback in ResourceTemplate → handled automatically or via list callback in config

## Prompt Registration

### Official SDK

```typescript
server.registerPrompt('summarize', {
    title: 'Summarize Text',
    description: 'Create a summary of provided text',
    argsSchema: z.object({
        text: z.string(),
        style: z.enum(['brief', 'detailed']).default('brief')
    })
}, ({ text, style }) => ({
    messages: [{
        role: 'user',
        content: { type: 'text', text: `Summarize (${style}):\n\n${text}` }
    }]
}));
```

### mcp-use

```typescript
import { text } from 'mcp-use/server'

server.prompt({
    name: 'summarize',
    description: 'Create a summary of provided text',
    schema: z.object({
        text: z.string(),
        style: z.enum(['brief', 'detailed']).default('brief')
    }),
}, async ({ text: input, style }) => text(`Summarize (${style}):\n\n${input}`))
```

### What changes:
1. **Method**: `registerPrompt(name, config, cb)` → `prompt(config, cb)`
2. **Schema key**: `argsSchema` → `schema`
3. **Response**: Manual `{ messages: [{ role, content }] }` → response helpers auto-convert

## Transport Layer

### Official SDK — stdio

```typescript
import { StdioServerTransport } from '@modelcontextprotocol/server';
const transport = new StdioServerTransport();
await server.connect(transport);
```

### mcp-use — HTTP server workflow

```bash
mcp-use dev
mcp-use build
mcp-use start
```

mcp-use focuses on a production-oriented HTTP server workflow; HTTP transport/session handling is built in once you call `listen()` (or use CLI commands).

### Official SDK — HTTP (Streamable HTTP)

```typescript
import express from 'express';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/server';
import { randomUUID } from 'crypto';

const app = express();
const transports = new Map<string, StreamableHTTPServerTransport>();

app.post('/mcp', async (req, res) => {
    const sessionId = req.headers['mcp-session-id'] as string;
    let transport = transports.get(sessionId);
    
    if (!transport) {
        transport = new StreamableHTTPServerTransport({
            sessionIdGenerator: () => randomUUID(),
        });
        transport.onsessioninitialized = (id) => transports.set(id, transport);
        await server.connect(transport);
    }
    
    await transport.handleRequest(req, res, req.body);
});

app.get('/mcp', async (req, res) => {
    const sessionId = req.headers['mcp-session-id'] as string;
    const transport = transports.get(sessionId);
    if (!transport) { res.status(400).end(); return; }
    await transport.handleRequest(req, res);
});

app.delete('/mcp', async (req, res) => {
    const sessionId = req.headers['mcp-session-id'] as string;
    const transport = transports.get(sessionId);
    if (transport) { await transport.close(); transports.delete(sessionId); }
    res.status(200).end();
});

app.listen(3000);
```

### mcp-use — HTTP

```typescript
await server.listen(3000)
```

That's it. All of the above (POST/GET/DELETE handlers, session routing, transport management) is handled internally by mcp-use.

## Session Management

### Official SDK

Manual — track in a Map:
```typescript
const sessions = new Map<string, Transport>();
// Route requests by mcp-session-id header
// Clean up on disconnect
// No persistence across restarts
```

### mcp-use

Pluggable storage backends:
```typescript
import {
    MCPServer,
    InMemorySessionStore,
    FileSystemSessionStore,
    RedisSessionStore,
    RedisStreamManager,
} from 'mcp-use/server'

// Development default (when NODE_ENV !== 'production')
const devServer = new MCPServer({
    name: 'dev',
    version: '1.0.0',
    sessionStore: new FileSystemSessionStore({ path: '.mcp-use/sessions.json' }),
})

// Single-instance production default (if no store override)
const prodServer = new MCPServer({
    name: 'prod',
    version: '1.0.0',
    sessionStore: new InMemorySessionStore(),
})

// Distributed production
const distributedServer = new MCPServer({
    name: 'prod',
    version: '1.0.0',
    sessionStore: new RedisSessionStore({ client: redis }),
    streamManager: new RedisStreamManager({
        client: redis,
        pubSubClient: pubSubRedis,
    }),
})
```

## Authentication

### Official SDK

Manual middleware — implement interfaces yourself:
```typescript
// You must implement:
interface OAuthServerProvider {
    authorize(client, params): Promise<...>;
    challengeForAuthorizationCode(client, authCode): Promise<...>;
    exchangeAuthorizationCode(client, authCode, ...): Promise<...>;
    exchangeRefreshToken(client, refreshToken, ...): Promise<...>;
    verifyAccessToken(token): Promise<...>;
}
// Then wire up /oauth/* endpoints manually
```

### mcp-use

Built-in providers:
```typescript
import { MCPServer, oauthAuth0Provider, oauthSupabaseProvider } from 'mcp-use/server'

const server = new MCPServer({
    name: 'protected-server',
    version: '1.0.0',
    oauth: oauthAuth0Provider({
        domain: 'your-tenant.auth0.com',
        audience: 'https://your-api.example.com',
    }),
})

const supabaseServer = new MCPServer({
    name: 'supabase-server',
    version: '1.0.0',
    oauth: oauthSupabaseProvider({
        projectId: process.env.MCP_USE_OAUTH_SUPABASE_PROJECT_ID!,
    }),
})

// Access auth in tools:
server.tool({ name: 'profile' }, async (_, context) => {
    const user = context.auth
    return text(`Hello, ${user.userId}`)
})
```

Available providers: `oauthAuth0Provider`, `oauthSupabaseProvider`, `oauthWorkOSProvider`, `oauthKeycloakProvider`, `oauthCustomProvider`.

## Advanced Features (mcp-use only)

These features have no equivalent in the official SDK:

| Feature | mcp-use API | Description |
|---|---|---|
| Response helpers | `text()`, `object()`, `markdown()`, `html()`, `image()`, `audio()`, `binary()`, `error()`, `mix()`, `resource()`, `widget()` | Type-safe response builders |
| UI Widgets | `server.uiResource()` + `widget()` helper | Interactive MCP Apps widgets |
| Inspector | Built-in at `/inspector` | Visual debug for tools/resources/prompts |
| HMR | `mcp-use dev` | Hot reload during development |
| CLI | `mcp-use dev/build/start/deploy/login/whoami/logout` | End-to-end server workflow |
| Middleware | Hono middleware via `server.app.use(...)` | Route-scoped middleware support |
| Custom HTTP routes | `server.app.get()/post()/use()` | REST endpoints alongside MCP |
| Elicitation | `ctx.elicit(message, zodSchema)` or `ctx.elicit(message, url)` | Request user input from tools |
| Sampling | `ctx.sample(promptOrParams, options?)` | Request LLM completion from tools |
| Notifications | `server.sendToolsListChanged()`, `server.sendNotification()` | Push updates to clients |

## Complete Migration Example

### Before (Official SDK, ~80 lines)

```typescript
import { McpServer, ResourceTemplate } from '@modelcontextprotocol/server';
import { StdioServerTransport } from '@modelcontextprotocol/server';
import * as z from 'zod/v4';

const server = new McpServer(
    { name: 'weather-server', version: '1.0.0' },
    { capabilities: { tools: {}, resources: { listChanged: true } } }
);

server.registerTool('get-weather', {
    description: 'Get weather for a city',
    inputSchema: z.object({ city: z.string() })
}, async ({ city }) => ({
    content: [{ type: 'text', text: `Weather in ${city}: Sunny, 72°F` }]
}));

server.registerResource('cities', 'weather://cities', {
    title: 'Available Cities'
}, async (uri) => ({
    contents: [{ uri: uri.href, text: JSON.stringify(['NYC', 'LA', 'London']) }]
}));

server.registerPrompt('forecast', {
    argsSchema: z.object({ city: z.string(), days: z.number() })
}, ({ city, days }) => ({
    messages: [{
        role: 'user',
        content: { type: 'text', text: `Give me a ${days}-day forecast for ${city}` }
    }]
}));

const transport = new StdioServerTransport();
await server.connect(transport);
```

### After (mcp-use, ~40 lines)

```typescript
import { MCPServer, text, object } from 'mcp-use/server'
import { z } from 'zod'

const server = new MCPServer({
    name: 'weather-server',
    version: '1.0.0',
})

server.tool({
    name: 'get-weather',
    description: 'Get weather for a city',
    schema: z.object({ city: z.string() }),
}, async ({ city }) => text(`Weather in ${city}: Sunny, 72°F`))

server.resource({
    uri: 'weather://cities',
    name: 'Available Cities',
}, async () => object(['NYC', 'LA', 'London']))

server.prompt({
    name: 'forecast',
    schema: z.object({ city: z.string(), days: z.number() }),
}, async ({ city, days }) => text(`Give me a ${days}-day forecast for ${city}`))

await server.listen(3000)
```
