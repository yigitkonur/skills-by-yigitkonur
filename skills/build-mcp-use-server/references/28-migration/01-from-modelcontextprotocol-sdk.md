# Adopting mcp-use v2 from Raw @modelcontextprotocol/sdk

*Read this when migrating an existing server built on the low-level `@modelcontextprotocol/sdk` or split `@modelcontextprotocol/server` package to mcp-use v2.*

The official Anthropic Model Context Protocol SDK (`@modelcontextprotocol/sdk`) provides low-level primitives: an imperative `Server` class, manual request schemas (`ListToolsRequestSchema`, `CallToolRequestSchema`), manual JSON-RPC switch/case dispatch, and raw stdio or custom SSE transports.

Migrating to `mcp-use v2` replaces manual JSON-RPC boilerplate with a **definition-first declarative framework**: tools, resources, and prompts declare their schemas and callbacks in a single unified registration call; transports are replaced by stateless **Streamable HTTP**; input validation and tool listing are handled automatically; built-in OAuth providers eliminate manual token verification; and Views (interactive MCP Apps) are integrated with zero raw HTML wiring.

---

## At a Glance: Raw SDK vs. mcp-use v2

| Capability | Raw `@modelcontextprotocol/sdk` | Canonical mcp-use v2 | Impact / Action |
|---|---|---|---|
| **Server Instance** | `new Server({ name, version }, { capabilities })` | `new MCPServer({ name, version, basePath: "/mcp", ... })` | Single constructor configuring HTTP routing, auth, logging, and state |
| **Tool Registration** | `server.setRequestHandler(ListToolsRequestSchema, ...)` + `setRequestHandler(CallToolRequestSchema, ...)` | `export const tool = server.tool({ name, inputSchema, outputSchema }, handler)` | Single declarative call; tools/list and schema parsing handled automatically |
| **Input Validation** | Manual `schema.safeParse(request.params.arguments)` inside handler | Automatic framework validation against `inputSchema` via Standard Schema | Handler receives pre-validated, fully typed input arguments |
| **Tool Return Value** | Manual JSON-RPC result object or throwing `new McpError(...)` | Raw `CallToolResult` envelope (`{ content, structuredContent, isError }`) | Type-safe envelope; structuredContent checked against outputSchema |
| **Resource Templates** | `setRequestHandler(ListResourceTemplatesRequestSchema)` + `ReadResourceRequestSchema` | `server.resourceTemplate({ name, uriTemplate, complete }, handler)` | Flattened RFC 6570 template registration with autocomplete support |
| **Prompts** | `setRequestHandler(ListPromptsRequestSchema)` + `GetPromptRequestSchema` | `server.prompt({ name, schema }, handler)` | Declarative prompt registration with typed arguments schema |
| **Transport** | `StdioServerTransport` connected via `await server.connect(transport)` | Stateless Streamable HTTP via `server.listen(port)` or `server.fetch` | Stdio removed; serves modern Streamable HTTP endpoint at `/mcp` |
| **Interactive UI** | Manual `resources/read` returning HTML strings + custom iframe messaging | Built-in MCP Apps Views (`views/<name>/view.tsx`) + `@openai/apps-sdk-ui` | Automatic Vite bundling, asset hosting, and host-agnostic postMessage bridge |
| **Authentication** | Application-owned manual bearer token verification | Built-in OAuth providers (`mcp-use/oauth/*`) with `mixedAuth: true` | Automatic DCR metadata, token verification, and per-tool security schemes |
| **TypeScript Typing** | Manual type sharing across client and server | Exported `ToolRef` generates `mcp-env.d.ts` for View typing | Zero manual interface syncing between server tools and React views |

---

## Why Migrate from Raw SDK to mcp-use v2?

Migrating to `mcp-use v2` is strongly recommended when:
1. **You want to eliminate JSON-RPC boilerplate**: You have hundreds of lines of imperative `setRequestHandler` switch/case blocks and manual error code mapping.
2. **You need web serving and cloud deployment**: You want to deploy as a standard HTTP microservice, Docker container, Next.js route, or Cloudflare Worker without wrestling with custom SSE streaming bugs.
3. **You want interactive UI (MCP Apps)**: You want to render rich, interactive React components (views) in ChatGPT, Claude, or MCP hosts without writing raw iframe message buses.
4. **You need production authentication**: You need OAuth 2.0 with Dynamic Client Registration (Clerk, Auth0, Supabase, WorkOS, Keycloak) or fine-grained per-tool authorization (`mixedAuth`).

*When raw SDK remains the better fit*:
- Standalone CLI utilities that strictly communicate over standard input/output (`stdio`) without a web server.
- Custom transport protocols (WebSockets, IPC pipes) unsupported by mcp-use.
- Low-level MCP protocol extensions that alter base JSON-RPC framing.

---

## Architectural Mapping: Raw SDK Primitives to mcp-use v2

### 1. Tool Dispatch: Imperative `setRequestHandler` → Declarative `server.tool`

In raw SDK, adding a tool requires maintaining two separate handlers: one that advertises the tool in `ListToolsRequestSchema`, and another that handles execution in `CallToolRequestSchema`:

```typescript
// Raw SDK: Two handlers, manual schema conversion, manual error throwing
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [{ name: "calculate", inputSchema: zodToJsonSchema(CalculateArgs) }],
}));

server.setRequestHandler(CallToolRequestSchema, async (req) => {
  if (req.params.name === "calculate") {
    const parsed = CalculateArgs.safeParse(req.params.arguments);
    if (!parsed.success) throw new McpError(ErrorCode.InvalidParams, parsed.error.message);
    return { content: [{ type: "text", text: String(parsed.data.a + parsed.data.b) }] };
  }
  throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${req.params.name}`);
});
```

In `mcp-use v2`, tool registration is unified into a single declarative call:

```typescript
// mcp-use v2: Single declarative registration; automatic validation and listing
export const calculate = server.tool(
  {
    name: "calculate",
    inputSchema: z.object({ a: z.number(), b: z.number() }),
    outputSchema: z.object({ sum: z.number() }),
  },
  async ({ a, b }) => ({
    content: [{ type: "text", text: `Sum: ${a + b}` }],
    structuredContent: { sum: a + b },
  })
);
```

### 2. Transports: `StdioServerTransport` → Streamable HTTP

In raw SDK, servers typically attach to process stdio:

```typescript
// Raw SDK: stdio transport
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
const transport = new StdioServerTransport();
await server.connect(transport);
```

In `mcp-use v2`, stdio is removed in favor of **stateless Streamable HTTP**. The server listens on an HTTP port or exports a standard Web Fetch handler:

```typescript
// mcp-use v2: Streamable HTTP
// Node.js standalone:
await server.listen(3000); // Serves Streamable HTTP on http://localhost:3000/mcp

// Edge / Cloudflare Workers / Next.js:
export default { fetch: server.fetch };
```

### 3. Resource Templates: `ListResourceTemplates` → `server.resourceTemplate`

In raw SDK:

```typescript
// Raw SDK
server.setRequestHandler(ListResourceTemplatesRequestSchema, async () => ({
  resourceTemplates: [{ uriTemplate: "docs://{topic}", name: "Documentation", mimeType: "text/markdown" }],
}));

server.setRequestHandler(ReadResourceRequestSchema, async (req) => {
  const match = req.params.uri.match(/^docs:\/\/(.+)$/);
  if (!match) throw new McpError(ErrorCode.InvalidParams, "Invalid URI");
  return { contents: [{ uri: req.params.uri, text: `Documentation for ${match[1]}` }] };
});
```

In `mcp-use v2`:

```typescript
// mcp-use v2: Flattened template with extracted parameters and autocomplete
export const docTemplate = server.resourceTemplate(
  {
    name: "Documentation",
    uriTemplate: "docs://{topic}",
    mimeType: "text/markdown",
    complete: {
      topic: async (val) => ["getting-started", "auth", "tools"].filter((t) => t.startsWith(val)),
    },
  },
  async (uri, { topic }) => ({
    contents: [{ uri: uri.href, text: `Documentation for ${topic}` }],
  })
);
```

### 4. Prompts: `ListPrompts` / `GetPrompt` → `server.prompt`

In raw SDK:

```typescript
// Raw SDK
server.setRequestHandler(ListPromptsRequestSchema, async () => ({
  prompts: [{ name: "code-review", arguments: [{ name: "code", required: true }] }],
}));

server.setRequestHandler(GetPromptRequestSchema, async (req) => {
  if (req.params.name === "code-review") {
    return {
      messages: [{ role: "user", content: { type: "text", text: `Review:\n${req.params.arguments?.code}` } }],
    };
  }
  throw new McpError(ErrorCode.InvalidParams, "Unknown prompt");
});
```

In `mcp-use v2`:

```typescript
// mcp-use v2
export const codeReviewPrompt = server.prompt(
  {
    name: "code-review",
    title: "Code Review",
    schema: z.object({ code: z.string().describe("Source code to evaluate") }),
  },
  async ({ code }) => ({
    messages: [{ role: "user", content: { type: "text", text: `Review:\n${code}` } }],
  })
);
```

---

## Runnable Before & After Code Transformation

### Before: Classic Raw `@modelcontextprotocol/sdk` Server

```typescript
// Legacy Raw SDK: Manual JSON-RPC switch/case dispatch, stdio transport, McpError
// legacy-sdk-server.ts
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourceTemplatesRequestSchema,
  ReadResourceRequestSchema,
  ListPromptsRequestSchema,
  GetPromptRequestSchema,
  McpError,
  ErrorCode,
} from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";

const server = new Server(
  { name: "legacy-raw-sdk", version: "1.0.0" },
  {
    capabilities: {
      tools: {},
      resources: { subscribe: false },
      prompts: {},
    },
  }
);

const CalculateArgs = z.object({
  a: z.number().describe("First number"),
  b: z.number().describe("Second number"),
  operation: z.enum(["add", "multiply"]).describe("Arithmetic operation"),
});

// 1. Manual Tools Listing
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "calculate",
      description: "Perform arithmetic calculations",
      inputSchema: {
        type: "object",
        properties: {
          a: { type: "number", description: "First number" },
          b: { type: "number", description: "Second number" },
          operation: { type: "string", enum: ["add", "multiply"], description: "Arithmetic operation" },
        },
        required: ["a", "b", "operation"],
      },
    },
  ],
}));

// 2. Manual Tool Dispatch Switch/Case
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "calculate") {
    const parseResult = CalculateArgs.safeParse(request.params.arguments);
    if (!parseResult.success) {
      throw new McpError(
        ErrorCode.InvalidParams,
        `Invalid tool arguments: ${parseResult.error.message}`
      );
    }

    const { a, b, operation } = parseResult.data;
    const result = operation === "add" ? a + b : a * b;

    return {
      content: [{ type: "text", text: `Result of ${operation}: ${result}` }],
    };
  }

  throw new McpError(ErrorCode.MethodNotFound, `Tool not found: ${request.params.name}`);
});

// 3. Manual Resource Templates
server.setRequestHandler(ListResourceTemplatesRequestSchema, async () => ({
  resourceTemplates: [
    {
      uriTemplate: "notes://{id}",
      name: "Project Notes",
      mimeType: "text/plain",
    },
  ],
}));

server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const uri = request.params.uri;
  return {
    contents: [{ uri, mimeType: "text/plain", text: `Contents for note ${uri}` }],
  };
});

// 4. Manual Prompts
server.setRequestHandler(ListPromptsRequestSchema, async () => ({
  prompts: [
    {
      name: "summarize",
      description: "Summarize a text block",
      arguments: [{ name: "text", description: "Text to summarize", required: true }],
    },
  ],
}));

server.setRequestHandler(GetPromptRequestSchema, async (request) => {
  if (request.params.name === "summarize") {
    const text = request.params.arguments?.text || "";
    return {
      messages: [{ role: "user", content: { type: "text", text: `Summarize this:\n\n${text}` } }],
    };
  }
  throw new McpError(ErrorCode.InvalidParams, "Unknown prompt name");
});

// 5. Connect via stdio
const transport = new StdioServerTransport();
await server.connect(transport);
```

---

### After: Canonical mcp-use v2 Server

```typescript
// Canonical mcp-use v2: Definition-first tools, templates, prompts, Streamable HTTP
// server.ts
import { MCPServer } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({
  name: "canonical-v2-server",
  version: "2.0.0",
  basePath: "/mcp",
  port: 3000,
});

// 1. Definition-First Tool (automatic validation & tools/list generation)
export const calculate = server.tool(
  {
    name: "calculate",
    title: "Arithmetic Calculator",
    description: "Perform arithmetic calculations",
    inputSchema: z.object({
      a: z.number().describe("First number"),
      b: z.number().describe("Second number"),
      operation: z.enum(["add", "multiply"]).describe("Arithmetic operation"),
    }),
    outputSchema: z.object({
      result: z.number(),
      operation: z.string(),
    }),
  },
  async ({ a, b, operation }) => {
    const result = operation === "add" ? a + b : a * b;
    return {
      content: [{ type: "text", text: `Result of ${operation}: ${result}` }],
      structuredContent: { result, operation },
    };
  }
);

// 2. Definition-First Resource Template with URI interpolation
export const projectNotes = server.resourceTemplate(
  {
    name: "Project Notes",
    uriTemplate: "notes://{id}",
    mimeType: "text/plain",
    description: "Retrieve project notes by ID",
    complete: {
      id: async (val) => ["arch-overview", "api-contract", "changelog"].filter((id) => id.startsWith(val)),
    },
  },
  async (uri, { id }) => ({
    contents: [
      {
        uri: uri.href,
        mimeType: "text/plain",
        text: `Contents for note ${id}`,
      },
    ],
  })
);

// 3. Definition-First Prompt with Typed Arguments
export const summarizePrompt = server.prompt(
  {
    name: "summarize",
    title: "Summarize Document",
    description: "Summarize a text block",
    schema: z.object({
      text: z.string().describe("Text to summarize"),
    }),
  },
  async ({ text }) => ({
    messages: [
      {
        role: "user",
        content: { type: "text", text: `Summarize this:\n\n${text}` },
      },
    ],
  })
);

// Default export enables CLI runner (mcp-use dev / mcp-use start)
export default server;
```

---

## Anti-Patterns and Common Raw SDK Migration Traps

| Anti-Pattern | Root Mechanism & Failure Mode | Canonical v2 Fix |
|---|---|---|
| **Calling `server.setRequestHandler` on `MCPServer`** | `MCPServer` does not inherit or expose raw SDK's `setRequestHandler`. Triggers compile or runtime `TypeError: server.setRequestHandler is not a function`. | Use `server.tool()`, `server.resourceTemplate()`, and `server.prompt()`. |
| **Attempting to Attach `StdioServerTransport`** | `mcp-use v2` serves exclusively over stateless Streamable HTTP. Passing a stdio transport throws or fails silently. | Call `await server.listen(port)` for standalone HTTP serving, or export `{ fetch: server.fetch }`. |
| **Method Chaining: `server.tool(...).tool(...)`** | In v1 or some builder patterns, registration methods returned `this`. In v2, `server.tool()` returns a `ToolRef` (for View typing), which has no `.tool()` method. Fails with `TypeError: server.tool(...).tool is not a function`. | Register each tool in an independent statement: `export const a = server.tool(...)`. |
| **Throwing Raw `McpError` for Operational Errors** | Throwing `new McpError(ErrorCode.InternalError)` converts to a raw JSON-RPC protocol error, terminating client interaction. | Return a structured error envelope: `{ isError: true, content: [{ type: "text", text: "User-facing error message" }] }`. |
| **Omitting `export` on Static Tool Definitions** | Forgetting `export const tool = server.tool(...)` prevents the `mcp-use typecheck` compiler from detecting the tool in `mcp-env.d.ts`, breaking TypeScript autocomplete in React Views. | Always export static tool references from your server module. |
| **Manual Schema Stringification in `tools/list`** | Hand-writing JSON Schema objects or calling `zodToJsonSchema` manually causes schema drift and syntax mismatches. | Pass Zod schemas directly to `inputSchema` and `outputSchema`; mcp-use handles wire serialization automatically. |

---

## Next Steps & Cross-References

- **Response Envelope Patterns**: See `04-v1-to-v2-responses-and-helpers.md` for `CallToolResult` multi-block and media envelopes.
- **Adding Authentication**: See `05-v1-to-v2-auth.md` for configuring Clerk, Auth0, or custom OAuth providers.
- **Adding Views (MCP Apps)**: See `08-appssdk-to-mcp-apps.md` for converting raw HTML resources into `@openai/apps-sdk-ui` React components.
- **CLI Development & Typechecking**: See `references/03-cli/03-mcp-use-dev.md` and `04-mcp-use-build-and-typecheck.md`.
