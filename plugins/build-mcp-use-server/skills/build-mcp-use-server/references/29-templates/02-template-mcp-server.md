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

This is the real generated file, verbatim (`{{PROJECT_NAME}}` is substituted with the project name at scaffold time):

```typescript
import { completable, MCPServer } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({
  name: "{{PROJECT_NAME}}",
  title: "{{PROJECT_NAME}}",
  version: "1.0.0",
  description: "An MCP server built with mcp-use",
});

// Tool: demo weather lookup
export const fetchWeather = server.tool(
  {
    name: "fetch-weather",
    description: "Return demo weather for a city",
    inputSchema: z.object({ city: z.string() }),
    outputSchema: z.object({
      city: z.string(),
      conditions: z.string(),
      temperature: z.string(),
    }),
    annotations: { readOnlyHint: true, openWorldHint: false },
  },
  async ({ city }) => {
    const weather = { city, conditions: "sunny", temperature: "22°C" };
    return {
      content: [{ type: "text", text: JSON.stringify(weather) }],
      structuredContent: weather,
    };
  }
);

// Prompt: code review assistant with a completable argument
server.prompt(
  {
    name: "review-code",
    description: "Review code for correctness and maintainability",
    schema: z.object({
      language: completable(z.string(), ["typescript", "javascript", "python", "go"]),
      code: z.string(),
    }),
  },
  async ({ language, code }) => ({
    messages: [
      {
        role: "user",
        content: { type: "text", text: `Review this ${language} code:\n\n${code}` },
      },
    ],
  })
);

export default server;
```

Note the CLI, not the entry file, starts the listener — there is no `server.listen()` call. `mcp-use dev`/`mcp-use start` import the default export and bind it.

## Key Points

1. **Tools are exported as const** — `export const fetchWeather = server.tool(...)` enables type inference in `mcp-env.d.ts` and view bindings.
2. **Raw MCP responses** — Return `{ content, structuredContent }` directly (no deprecated helpers).
3. **No views** — Tools don't have a `view` field; they render as text.
4. **Prompts use `schema`, not `arguments`** — `PromptDefinition` takes `{ name, title?, description?, schema? }` where `schema` is a Standard Schema (Zod object). There is no `arguments` array field in v2; wrap completable fields with `completable(schema, suggestions)` imported from `mcp-use`.
5. **No `server.listen()` in the scaffolded file** — `npm run dev`/`npm run build`/`npm run start` (all `mcp-use` CLI subcommands) own the HTTP socket. Call `.listen(port?, options?)` yourself only in hand-coded, non-scaffolded servers (see `references/29-templates/04-template-blank-and-manual.md`).
6. **`annotations`** — `{ readOnlyHint, openWorldHint, ... }` describe tool behavior to clients; see `references/04-tools/04-describe-and-annotations.md`.

## Development

```bash
npm run dev
# Starts http://127.0.0.1:3000/mcp + Inspector at /mcp/inspector
# Watches index.ts for changes; HMR restarts on save
```

## Deployment

```bash
npm run deploy
# Default source mode: GitHub-backed. Requires a configured `origin` remote,
# the Manufact GitHub App installed on that repo, and `mcp-use login` first.
# Prints server ID, deployment ID, status, and a dashboard URL — copy the
# generated MCP endpoint from the dashboard; do not infer it from the slug.
```

`mcp-use deploy --no-github` skips Git entirely and uploads the local project as a managed archive (80 MB limit) instead — use it when there is no GitHub repo yet. `mcp-use login` authenticates; `mcp-use whoami` only prints the already-authenticated identity, it does not log in. Full flag/behavior reference: `references/25-deploy/`.

## Next Steps

- Add more tools to `index.ts` — each as an exported const.
- Use resources for data access (read `references/06-resources/01-overview.md`).
- Add OAuth to protect endpoints (read `references/11-auth/01-overview.md`).
- Read `references/04-tools/canonical-anchor.md` for a fully annotated tool example.
