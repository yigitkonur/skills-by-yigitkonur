# Template: Minimal stdio Server

Smallest viable mcp-use server. Runs under stdio (Claude Desktop) and Streamable HTTP (Inspector / ChatGPT) from the same `index.ts`. Use `mcp-use dev` for hot-reload, `mcp-use build` then `mcp-use start` for production.

## Layout

```
my-mcp-server/
├── package.json
├── tsconfig.json
└── index.ts
```

## `package.json`

```json
{
  "name": "my-mcp-server",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "mcp-use dev",
    "build": "mcp-use build",
    "start": "mcp-use start",
    "deploy": "mcp-use deploy"
  },
  "dependencies": {
    "mcp-use": "^1.21.5",
    "zod": "^4.0.0"
  },
  "devDependencies": {
    "@mcp-use/cli": "latest",
    "typescript": "^5.5.0"
  }
}
```

> **v1.21.5+:** `zod` is a `peerDependency` of `mcp-use` and must be in your own `dependencies`. It is not auto-installed.

## `tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true
  },
  "include": ["index.ts", "resources/**/*", ".mcp-use/**/*"]
}
```

The `resources/**/*` and `.mcp-use/**/*` globs are pre-wired so this same scaffold accepts widget files later without a config change.

## `index.ts`

```typescript
import { MCPServer, text, markdown } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({
  name: "my-mcp-server",
  version: "1.0.0",
  description: "A minimal MCP server",
});

server.tool(
  {
    name: "greet",
    description: "Generate a greeting",
    schema: z.object({
      name: z.string().describe("Name to greet"),
    }),
  },
  async ({ name }) => text(`Hello, ${name}! Welcome to MCP.`)
);

server.resource(
  {
    name: "greeting",
    uri: "app://greeting",
    title: "Greeting Message",
  },
  async () => markdown("# Hello from mcp-use!")
);

// MCP endpoints are auto-mounted at /mcp under HTTP, or wired to stdin/stdout under stdio.
await server.listen();
```

## Run

```bash
npm install
npm run dev
```

`mcp-use dev` starts an HTTP transport on http://localhost:3000/mcp and serves the Inspector at /inspector. For production, run `npm run build && npm run start`.

## Wire to Claude Desktop (stdio)

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "node",
      "args": ["/absolute/path/to/my-mcp-server/dist/index.js"]
    }
  }
}
```

`server.listen()` auto-detects stdio when stdin is not a TTY.

## When to graduate

- Need env-driven config or modular tool files → `03-production-http.md`.
- Need React widgets → `04-mcp-apps-widget.md`.
- Need Edge deployment → `05-serverless-deno.md`.
