# Manual stdio Server

`mcp-use` is HTTP-first. `MCPServer` is built on Hono and starts an HTTP server via `server.listen()`. There is no `server.listenStdio()` and no first-class stdio transport in the public API.

If a host requires stdio, you have two options. Pick by audience.

## Option A — run the same `mcp-use` server over Streamable HTTP

This is the recommended path for any client written after the Streamable HTTP migration (Claude Desktop ≥ 0.10, ChatGPT, Cursor with HTTP support, MCP Inspector, programmatic clients).

The server file looks identical to `05-manual-http-server.md`. Configure the client with a URL, not a `command` / `args` pair:

```json
{
  "mcpServers": {
    "my-server": { "url": "http://localhost:3000/mcp" }
  }
}
```

Do **not** use Claude Desktop's `command` / `args` form for an `mcp-use` server — that form spawns a stdio child process, which `mcp-use` does not implement.

## Option B — drop to the raw SDK for true stdio

When the host only supports the legacy stdio shape (older Claude Desktop versions or strict CLI-installed servers), use `@modelcontextprotocol/sdk` directly. You lose Zod, HMR, the Inspector, and widgets — but you get a real stdio transport.

```ts
// src/server.ts
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";

const server = new Server(
  { name: "my-stdio-server", version: "1.0.0" },
  { capabilities: { tools: {} } },
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [{ name: "ping", description: "Reply pong", inputSchema: { type: "object" } }],
}));

server.setRequestHandler(CallToolRequestSchema, async (req) => {
  if (req.params.name === "ping") {
    return { content: [{ type: "text", text: "pong" }] };
  }
  throw new Error(`Unknown tool: ${req.params.name}`);
});

await server.connect(new StdioServerTransport());
```

`package.json`:

```json
{
  "name": "my-stdio-server",
  "type": "module",
  "bin": { "my-stdio-server": "dist/server.js" },
  "scripts": {
    "build": "tsc",
    "start": "node dist/server.js"
  },
  "dependencies": { "@modelcontextprotocol/sdk": "latest", "zod": "^4.0.0" },
  "devDependencies": { "typescript": "^5.5.0", "@types/node": "^22.0.0" }
}
```

Client config (Claude Desktop legacy form):

```json
{
  "mcpServers": {
    "my-stdio-server": {
      "command": "node",
      "args": ["/abs/path/to/dist/server.js"]
    }
  }
}
```

This file deliberately does not pretend `mcp-use` exposes a stdio transport. If you only need Claude Desktop / ChatGPT / Cursor, use Option A.

## Why this is not `server.listen()` over stdio

`server.listen()` binds an HTTP socket. Calling it without a port still produces an HTTP server, not a stdio transport. Earlier versions of this skill conflated the two — that was wrong. See `26-anti-patterns/` for related landmines.

## See also

- `05-manual-http-server.md` — the recommended path
- `09-transports/` — full transport guide once it lands
- `26-anti-patterns/` — common transport mistakes
