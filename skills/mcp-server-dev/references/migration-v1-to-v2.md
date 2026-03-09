# Migration Guide: v1 to v2

## Status note

The official TypeScript SDK `main` branch is currently v2 pre-alpha. Upstream still recommends v1.x for production until the stable v2 release ships, so use this guide when you are actively migrating or building against v2 on purpose.

## Package Changes

```bash
# v1
npm install @modelcontextprotocol/sdk

# v2
npm install @modelcontextprotocol/server zod

# Optional Node.js HTTP transport / middleware
npm install @modelcontextprotocol/node
npm install @modelcontextprotocol/express express
```

## Import Changes

```typescript
// v1
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';

// v2
import { McpServer } from '@modelcontextprotocol/server';
import { StdioServerTransport } from '@modelcontextprotocol/server/stdio';
import { z } from 'zod/v4';
```

## Tool Registration

The variadic `.tool()` method is removed. Use `.registerTool()` with a config object:

```typescript
// v1: server.tool(name, schema, callback)
server.tool('greet', { name: z.string() }, async ({ name }) => {
  return { content: [{ type: 'text', text: `Hello, ${name}!` }] };
});

// v1: server.tool(name, description, schema, callback)
server.tool('greet', 'Greet a user', { name: z.string() }, async ({ name }) => {
  return { content: [{ type: 'text', text: `Hello, ${name}!` }] };
});

// v2: server.registerTool(name, config, callback)
server.registerTool(
  'greet',
  {
    description: 'Greet a user',
    inputSchema: z.object({ name: z.string() }),
  },
  async ({ name }) => {
    return { content: [{ type: 'text', text: `Hello, ${name}!` }] };
  }
);
```

Config object fields: `title?`, `description?`, `inputSchema?`, `outputSchema?`, `annotations?`, `_meta?`

## Prompt Registration

```typescript
// v1
server.prompt('summarize', { text: z.string() }, async ({ text }) => {
  return { messages: [{ role: 'user', content: { type: 'text', text } }] };
});

// v2
server.registerPrompt(
  'summarize',
  { argsSchema: z.object({ text: z.string() }) },
  async ({ text }) => {
    return { messages: [{ role: 'user', content: { type: 'text', text } }] };
  }
);
```

Config object fields: `title?`, `description?`, `argsSchema?`

## Resource Registration

```typescript
// v1
server.resource('config', 'config://app', async (uri) => {
  return { contents: [{ uri: uri.href, text: '{}' }] };
});

// v2 — note the required third argument (metadata)
server.registerResource('config', 'config://app', {}, async (uri) => {
  return { contents: [{ uri: uri.href, text: '{}' }] };
});
```

The third argument (metadata) is required — pass `{}` if no metadata.

## Zod Schemas

v2 requires full Zod schemas wrapped with `z.object()`. Raw shapes are no longer accepted:

```typescript
// v1: raw shape (worked)
server.tool('greet', { name: z.string() }, callback);

// v2: must be z.object()
server.registerTool('greet', {
  inputSchema: z.object({ name: z.string() }),
}, callback);

// For tools with no parameters
server.registerTool('ping', {
  inputSchema: z.object({}),
}, callback);
```

This applies to:
- `inputSchema` in `registerTool()`
- `outputSchema` in `registerTool()`
- `argsSchema` in `registerPrompt()`

## Zod Version

v2 uses `zod/v4`:

```typescript
// v1
import { z } from 'zod';

// v2
import { z } from 'zod/v4';
```

## Transport Changes

SSE transport is deprecated. Use Streamable HTTP:

```typescript
// v1 (deprecated)
import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';

// v2
import { NodeStreamableHTTPServerTransport } from '@modelcontextprotocol/node';
```

## Quick Reference

| v1 | v2 |
|----|-----|
| `server.tool(name, schema, cb)` | `server.registerTool(name, { inputSchema: z.object(schema) }, cb)` |
| `server.prompt(name, schema, cb)` | `server.registerPrompt(name, { argsSchema: z.object(schema) }, cb)` |
| `server.resource(name, uri, cb)` | `server.registerResource(name, uri, {}, cb)` |
| `{ name: z.string() }` | `z.object({ name: z.string() })` |
| `import { z } from 'zod'` | `import { z } from 'zod/v4'` |
| `SSEServerTransport` | `NodeStreamableHTTPServerTransport` |
| `@modelcontextprotocol/sdk` | `@modelcontextprotocol/server` + optional runtime adapters |
