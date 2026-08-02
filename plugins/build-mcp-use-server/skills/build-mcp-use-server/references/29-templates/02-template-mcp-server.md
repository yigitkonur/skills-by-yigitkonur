# Template: mcp-server

*Read this for a complete tree of the `mcp-server` template and what it demonstrates.*

## Generated File Tree

```
my-project/
├── index.ts                     # MCPServer entry; exports default
├── mcp-env.d.ts                 # Auto-generated type bridge
├── package.json                 # Includes dev/build/typecheck/start/deploy scripts
├── tsconfig.json                # ESM + MCP types
├── gitignore                    # Node + .mcp-use/
├── README.md                    # Quick start reference
└── public/
    └── icon.svg                 # Server icon (shown in Inspector, Claude Desktop)
```

## What `index.ts` Demonstrates

```typescript
import { MCPServer } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
});

// Tool: weather forecast
export const getWeather = server.tool(
  {
    name: "get-weather",
    description: "Get 5-day weather forecast for a city",
    inputSchema: z.object({
      city: z.string().describe("City name"),
      unit: z.enum(["celsius", "fahrenheit"]).optional().describe("Temperature unit"),
    }),
    outputSchema: z.object({
      city: z.string(),
      forecast: z.array(z.object({ day: z.string(), high: z.number(), low: z.number() })),
    }),
  },
  async ({ city, unit = "celsius" }) => {
    // Mock response for demo
    return {
      content: [{ type: "text", text: `5-day forecast for ${city}` }],
      structuredContent: {
        city,
        forecast: [{ day: "Monday", high: 22, low: 18 }],
      },
    };
  }
);

// Prompt: code review assistant
server.prompt(
  {
    name: "code-review",
    description: "Review code for style and bugs",
    arguments: [{ name: "language", description: "Programming language" }],
  },
  async ({ language }) => [
    {
      type: "text",
      text: `You are a code reviewer for ${language}. Be constructive.`,
    },
  ]
);

export default server;

server.listen();  // Starts HTTP on PORT (default 3000)
```

## Key Points

1. **Tools are exported as const** — `export const getWeather = server.tool(...)` enables type inference in `mcp-env.d.ts` and view bindings.
2. **Raw MCP responses** — Return `{ content, structuredContent }` directly (no deprecated helpers).
3. **No views** — Tools don't have a `view` field; they render as text.
4. **Prompts are optional** — Demonstrations only; omit if not needed.
5. **server.listen()** defaults to `process.env.PORT` or 3000; HTTP endpoint at `/mcp`.

## Development

```bash
npm run dev
# Starts http://127.0.0.1:3000/mcp + Inspector at /mcp/inspector
# Watches index.ts for changes; HMR restarts on save
```

## Deployment

```bash
npm run deploy
# Requires GitHub repo + login (mcp-use whoami)
# Deploys to Manufact Cloud → https://{slug}.run.mcp-use.com/mcp
```

## Next Steps

- Add more tools to `index.ts` — each as an exported const.
- Use resources for data access (read `../06-resources/01-overview.md`).
- Add OAuth to protect endpoints (read `../11-auth/01-overview.md`).
- Read `04-tools/canonical-anchor.md` for a fully annotated tool example.
