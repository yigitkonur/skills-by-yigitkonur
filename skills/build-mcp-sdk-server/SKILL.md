---
name: build-mcp-sdk-server
description: Use skill if you are building an MCP server with the official TypeScript SDK, including tools, resources, prompts, transports, or v1-to-v2 migration.
---

# Build MCP SDK Server

Build MCP servers with the official TypeScript SDK v2 on the current `main` branch. This skill targets `@modelcontextprotocol/server`; if your code still imports `@modelcontextprotocol/sdk`, read `references/migration-v1-to-v2.md` first.

Treat the v2 guidance here as current-sdk guidance, not a production-stability claim. The upstream TypeScript SDK README currently marks v2 as pre-alpha on `main`, with v1.x still recommended for production until the stable v2 release ships.

## Decision tree

```
What do you need?
│
├── New server from scratch
│   ├── Scaffold project ───────────► references/project-setup.md
│   └── Pick a transport ───────────► references/transports.md
│
├── Register primitives
│   ├── Tools ──────────────────────► references/tools.md
│   ├── Resources ──────────────────► references/resources.md
│   └── Prompts ────────────────────► references/prompts.md
│
├── Advanced features
│   ├── Collect user input ─────────► references/elicitation.md
│   ├── Call the LLM from a tool ───► references/sampling.md
│   └── Long-running ops (exp.) ────► references/tasks.md
│
├── Migrate v1 to v2
│   └── ────────────────────────────► references/migration-v1-to-v2.md
│
└── Deploy
    ├── Claude Desktop (stdio) ──────► references/transports.md
    └── Production HTTP ─────────────► references/transports.md
```

## Quick start

Install:

```bash
npm init -y
npm install @modelcontextprotocol/server zod
npm install -D typescript tsx @types/node
```

Set `"type": "module"` in `package.json`.

If you need Streamable HTTP on Node.js, add only the adapters you actually use:

```bash
npm install @modelcontextprotocol/node
npm install @modelcontextprotocol/express express
```

Minimal stdio server:

```typescript
import { McpServer } from '@modelcontextprotocol/server';
import { StdioServerTransport } from '@modelcontextprotocol/server/stdio';
import { z } from 'zod/v4';

const server = new McpServer({ name: 'my-server', version: '1.0.0' });

server.registerTool(
  'greet',
  {
    title: 'Greet',
    description: 'Greet a user by name',
    inputSchema: z.object({
      name: z.string().describe('Name to greet'),
    }),
  },
  async ({ name }) => ({
    content: [{ type: 'text', text: `Hello, ${name}!` }],
  })
);

const transport = new StdioServerTransport();
await server.connect(transport);
```

Test it immediately:

```bash
npx @modelcontextprotocol/inspector tsx src/index.ts
```

## Key patterns

### Tool with structured output

When declaring `outputSchema`, return both `content` and `structuredContent`:

```typescript
server.registerTool(
  'search',
  {
    description: 'Search the document store',
    inputSchema: z.object({
      query: z.string().describe('Search terms'),
      limit: z.number().min(1).max(50).default(10).describe('Max results'),
    }),
    outputSchema: z.object({ results: z.array(z.string()) }),
    annotations: { readOnlyHint: true, openWorldHint: true },
  },
  async ({ query, limit }) => {
    const results = await search(query, limit);
    return {
      content: [{ type: 'text', text: JSON.stringify({ results }) }],
      structuredContent: { results },
    };
  }
);
```

### Error handling

Return errors as content. Never throw unhandled exceptions out of a tool callback:

```typescript
async ({ id }) => {
  try {
    const data = await fetchData(id);
    return { content: [{ type: 'text', text: JSON.stringify(data) }] };
  } catch (error) {
    return {
      content: [{ type: 'text', text: `Error: ${error instanceof Error ? error.message : String(error)}` }],
      isError: true,
    };
  }
}
```

### Dynamic resource

Use `ResourceTemplate` and always provide a `list` callback so clients can discover resources:

```typescript
import { ResourceTemplate } from '@modelcontextprotocol/server';

server.registerResource(
  'user-profile',
  new ResourceTemplate('user://{userId}/profile', {
    list: async () => ({
      resources: (await getUsers()).map(u => ({ uri: `user://${u.id}/profile`, name: u.name })),
    }),
  }),
  { title: 'User Profile', mimeType: 'application/json' },
  async (uri, { userId }) => ({
    contents: [{ uri: uri.href, text: JSON.stringify(await getUser(userId)) }],
  })
);
```

## Transport decision

| Transport | Use case | Key constraint |
|-----------|----------|----------------|
| stdio | Claude Desktop, CLI tools | Single client, process-spawned |
| Streamable HTTP (stateless) | Production APIs, serverless | Multi-client, scalable |
| Streamable HTTP (stateful) | Sessions, resumability | Multi-client, session persistence |
| SSE transport | Deprecated since March 2025 | Migrate to Streamable HTTP |

For localhost HTTP on Node.js, use `createMcpExpressApp()` from `@modelcontextprotocol/express` or `createMcpHonoApp()` from `@modelcontextprotocol/hono`. Pair Express with `NodeStreamableHTTPServerTransport` from `@modelcontextprotocol/node`.

## Common mistakes

1. Using the v1 API — `server.tool()` does not exist in v2; use `server.registerTool()`
2. Passing a raw shape `{ name: z.string() }` instead of `z.object({ name: z.string() })`
3. Using SSE transport — it was deprecated in March 2025
4. Throwing exceptions from tool callbacks — return `{ isError: true }` instead
5. Missing `"type": "module"` in `package.json`
6. Hardcoding secrets in `args` — pass them via `env` in the Claude Desktop config
7. Omitting `.describe()` on Zod fields — LLMs use these descriptions for context
8. Returning unbounded response sizes — Claude has a context window limit

## Reference files

| File | When to read |
|------|-------------|
| `references/project-setup.md` | Scaffolding a new server project from scratch |
| `references/tools.md` | Registering tools, schemas, annotations, ResourceLinks |
| `references/resources.md` | Static and dynamic resources, URI templates, completions |
| `references/prompts.md` | Prompt templates with argument schemas and completions |
| `references/transports.md` | Transport selection, stdio vs Streamable HTTP, configuration |
| `references/elicitation.md` | Requesting user input via form or URL mode |
| `references/sampling.md` | Server-side LLM sampling with tool calling |
| `references/tasks.md` | Experimental task-based execution for long-running ops |
| `references/migration-v1-to-v2.md` | Migrating from SDK v1 to v2 |
