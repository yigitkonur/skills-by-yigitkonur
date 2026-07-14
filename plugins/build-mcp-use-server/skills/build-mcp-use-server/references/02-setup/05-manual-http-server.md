# Manual HTTP Server

The minimal Streamable HTTP server you can write by hand. Use this when you don't want the scaffolder.

## Files

```
my-mcp-server/
├── package.json
├── tsconfig.json
└── src/
    └── server.ts
```

## `package.json`

```json
{
  "name": "my-mcp-server",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "mcp-use dev src/server.ts",
    "build": "mcp-use build",
    "start": "mcp-use start",
    "deploy": "mcp-use deploy"
  },
  "dependencies": {
    "mcp-use": "latest",
    "zod": "^4.0.0"
  },
  "devDependencies": {
    "@mcp-use/cli": "latest",
    "typescript": "^5.5.0",
    "@types/node": "^22.0.0",
    "tsx": "^4.0.0"
  }
}
```

`"type": "module"` is required. See `07-package-scripts.md` for what each script does.

## `tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "Node16",
    "moduleResolution": "Node16",
    "strict": true,
    "outDir": "./dist",
    "rootDir": "./src",
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": ["src/**/*", ".mcp-use/**/*"]
}
```

See `08-tsconfig-and-types.md` for why each option matters and how to add `resources/` for widgets.

## `src/server.ts`

```ts
import { MCPServer, text } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  description: "Minimal HTTP MCP server",
});

server.tool(
  {
    name: "get_weather",
    description: "Get weather for a city",
    schema: z.object({
      city: z.string().describe("City name"),
    }),
  },
  async ({ city }) => text(`Temperature: 72°F, Condition: sunny, City: ${city}`),
);

await server.listen(parseInt(process.env.PORT ?? "3000", 10));
```

`server.listen(port)` mounts MCP on `/mcp` and the Inspector on `/inspector` (dev mode only).

## Run

```bash
npm install
npm run dev
```

The dev server boots at `http://localhost:3000`:

| Path | Purpose |
|---|---|
| `/mcp` | JSON-RPC endpoint (POST). Primary client target. |
| `/mcp` | GET / DELETE / HEAD for SSE stream open, session terminate, health check. |
| `/inspector` | Web Inspector (dev only). |
| `/sse` | Legacy alias for older clients. |

## Verify with curl

```bash
# List tools
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'

# Call the tool
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_weather","arguments":{"city":"London"}}}'
```

## Configure clients

Always use the URL form:

```json
{
  "mcpServers": {
    "my-server": { "url": "http://localhost:3000/mcp" }
  }
}
```

The `command`/`args` form is for stdio servers — see `04-manual-stdio-server.md`.

## Where to look next

| Goal | Read |
|---|---|
| Add a real tool with a richer schema | `04-tools/01-overview.md` |
| Add a resource or prompt | `06-resources/`, `07-prompts/` |
| Run side-by-side with an existing app | `06-add-to-existing-app.md` |
| Deploy | `25-deploy/` |
