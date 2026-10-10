# Imports, Server Configuration, and Tool Registration

*Read this when migrating root imports, constructor options, Standard Schema validation, and tool registration syntax from v1 to v2.*

In `mcp-use v1`, the framework exposed multiple subpaths (`mcp-use/server`), supported CommonJS and older Node runtimes, permitted method chaining on tool registration, and relied on Zod v3 schemas. 

`mcp-use v2` standardizes around a root import (`mcp-use`), enforces Node.js `>= 22.22.2` with pure ESM, adopts the cross-ecosystem **Standard Schema specification** (implemented natively by Zod v4), requires static `ToolRef` exports for View typechecking, and separates tool definitions from callback handlers.

---

## At a Glance: Imports, Server & Tools Diff

| Feature / Surface | Legacy v1 (`mcp-use <= 1.34.5`) | Canonical v2 (`mcp-use >= 2.8.2`) | Impact / Action |
|---|---|---|---|
| **Package Import** | `import { MCPServer } from "mcp-use/server"` | `import { MCPServer } from "mcp-use"` | Root import; subpath `./server` deleted from package exports |
| **Node.js Engine** | Node ^20.19.0 or >=22.12.0; CJS or ESM | Node >= 22.22.2; strictly ESM (`"type": "module"`) | Set `"type": "module"` in `package.json`; upgrade runtime |
| **Schema Validation** | Zod v3 (`zod@^3.22.0`) | Standard Schema v1 (`zod@^4.0.0-alpha` or `~standard`) | Automatic schema validation against `~standard` interface |
| **Tool Registration** | `server.tool({ name, schema, cb })` | `export const tool = server.tool({ name, inputSchema, outputSchema }, cb)` | Definition is 1st argument, callback is 2nd argument |
| **Wire Schema Key** | `schema` | `inputSchema` (matches MCP wire protocol; `schema` is deprecated) | Rename `schema` to `inputSchema` |
| **Output Validation** | Optional `outputSchema` | Mandatory `outputSchema` for tools bound to Views | Enables client-side View validation and typed `structuredContent` |
| **Tool Static Export** | Not required | **Mandatory** (`export const myTool = ...`) | Required by `mcp-use typecheck` to emit `mcp-env.d.ts` |
| **Method Chaining** | `server.tool(...).tool(...)` (returned `this`) | `server.tool(...)` returns `ToolRef` (chaining fails) | One standalone statement per tool registration |
| **Public Origin** | Constructor `baseUrl: "https://..."` | Environment variable `MCP_URL` + constructor `basePath: "/mcp"` | Remove `baseUrl` constructor option; configure via env |
| **CORS Keys** | `cors.allowMethods`, `cors.allowHeaders` | `cors.methods`, `cors.allowedHeaders` | Rename CORS configuration options |
| **Root Logger** | `Logger.get()`, `Logger.configure()` | **Removed**; use own logger (`pino`, `console`) or `ctx.sendLog()` | Replace framework Logger with standard logger |

---

## Step 1: Update Imports

### Before (v1):
```typescript
import { MCPServer, text, object, error } from "mcp-use/server";
```

### After (v2):
```typescript
import { MCPServer } from "mcp-use";
import { z } from "zod";
```

> **Warning**: Attempting to import from `mcp-use/server` in v2 triggers `Error: Cannot find module 'mcp-use/server'`. Import `MCPServer` directly from `"mcp-use"`.

---

## Step 1b: The `Logger` Root API is Removed

v1's application logger is not exported from v2. `Logger`, `Logger.get(name)`, `Logger.configure(...)`, `Logger.setDebug(level)`, and the default `logger` instance **do not exist** in v2.

| v1 Pattern | Canonical v2 Destination |
|---|---|
| Server-side startup & diagnostic logs | Your own application logger (`pino`, Winston, `console`). mcp-use does not bundle one. |
| HTTP request logging | Constructor `logging: { enabled?: boolean, level?: "info" \| "debug" \| "trace" }`, or env `MCP_USE_LOG_LEVEL`. |
| Client-visible notifications | `await ctx.sendLog(level, data, loggerName?)` inside tool callbacks (fires MCP `notifications/message`). |
| Custom Fetch request logging | `requestLogger({...})` composed around `server.fetch` via `composeFetch`. |

```typescript
import { MCPServer } from "mcp-use";
import pino from "pino";

// Application-owned logger replaces Logger.get
const log = pino({ name: "server" });

const server = new MCPServer({
  name: "my-server",
  version: "2.0.0",
  logging: { level: "debug" }, // Framework HTTP logging
});

export const processTask = server.tool(
  { name: "process-task", inputSchema: z.object({ id: z.string() }), outputSchema: z.object({}) },
  async ({ id }, ctx) => {
    log.info({ id }, "Processing task server-side");     // Server log sink
    await ctx.sendLog("info", { stage: "started", id }); // MCP notification sent to client
    return { content: [{ type: "text", text: "Done" }], structuredContent: {} };
  }
);
```

---

## Step 1c: Mechanical Constructor & Config Renames

These v1 `ServerConfig` fields fail as TypeScript compilation errors in v2:

| v1 Field | v2 Status | Action |
|---|---|---|
| `baseUrl` | **Removed** | Delete. Public origin is runtime config (`MCP_URL` env variable), not a constructor field. Mount path is configured via `basePath`. |
| `cors.allowMethods` | → `cors.methods` | Rename property. |
| `cors.allowHeaders` | → `cors.allowedHeaders` | Rename property. |
| `cors.exposeHeaders` | **Removed** | Delete. v2 `CorsOptions` has no header exposure field. |
| `sessionStore`, `streamManager`, `stateless: false` | **Removed** | Delete. See `07-v1-to-v2-sessions-transports-stdio-sse.md`. |

```typescript
// v1 (Legacy)
const server = new MCPServer({
  name: "api",
  version: "1.0.0",
  baseUrl: "https://api.example.com",
  cors: { allowMethods: ["POST"], allowHeaders: ["authorization"] },
});

// v2 (Canonical)
const server = new MCPServer({
  name: "api",
  version: "2.0.0",
  basePath: "/mcp",
  cors: { methods: ["POST"], allowedHeaders: ["authorization"], credentials: true },
});
// Set origin via environment: MCP_URL=https://api.example.com npm start
```

---

## Step 2: Standard Schema (Zod v4) Adoption

In `mcp-use v2`, input and output validation conforms to the cross-ecosystem **Standard Schema specification** (`~standard` interface). This allows `mcp-use` to validate schemas from Zod, Valibot, ArkType, or any Standard Schema compliant library with zero overhead.

### Upgrading to Zod v4

Install Zod v4 (or alpha):

```bash
npm install zod@^4.0.0-alpha
```

Key Standard Schema advantages:
- Schemas export a standard `~standard: { version: 1, vendor: "zod", validate: ... }` contract.
- In v2, passing Zod v3 schemas (`zod@^3.22.x`) that do not implement `~standard` triggers validation warnings or type mismatches.
- Descriptions attached via `.describe("...")` are automatically extracted and advertised as JSON Schema property descriptions in `tools/list`.

```typescript
import { z } from "zod";

export const QueryInputSchema = z.object({
  query: z.string().min(1).describe("Search keywords to query the catalog"),
  limit: z.number().int().min(1).max(50).default(10).describe("Maximum results to return"),
  filter: z.enum(["active", "archived"]).optional().describe("Filter status"),
});
```

---

## Step 3: Tool Registration — Definition-First Callback

### Before (v1): Inline Schema & Callback in Object
```typescript
server.tool({
  name: "weather",
  description: "Get weather",
  schema: z.object({ city: z.string() }),
  cb: async ({ city }) => text(await fetchWeather(city)),
});
```

### After (v2): Definition (Arg 1) + Callback (Arg 2)
```typescript
export const weather = server.tool(
  {
    name: "weather",
    title: "Weather Forecast",
    description: "Get current weather conditions by city",
    inputSchema: z.object({
      city: z.string().describe("City name"),
    }),
    outputSchema: z.object({
      forecast: z.string(),
      temperature: z.number(),
    }),
  },
  async ({ city }) => {
    const data = await fetchWeather(city);
    return {
      content: [{ type: "text", text: `Weather in ${city}: ${data.forecast}` }],
      structuredContent: data,
    };
  }
);
```

**Key Architectural Changes**:
1. `schema` is renamed to **`inputSchema`** (matching the MCP wire field).
2. **`outputSchema` is mandatory** when the tool binds to a View, and strongly recommended for all tools to enforce type-safe `structuredContent`.
3. The callback function is passed as the **second parameter**, not as an inline `cb` property.
4. Returns a raw **`CallToolResult` envelope** instead of deprecated `text()` or `object()` helpers.
5. **No Method Chaining**: In v1, `server.tool()` returned `this` for chaining. In v2, it returns a typed `ToolRef`. Calling `server.tool(...).tool(...)` throws `TypeError: server.tool(...).tool is not a function`.

---

## Step 4: Export Every Static Tool (`ToolRef`)

All tools declared at module level **must be exported**:

```typescript
// ✓ Correct: ToolRef is exported
export const search = server.tool({ name: "search", ... }, async (...) => {...});
export const getDetails = server.tool({ name: "get-details", ... }, async (...) => {...});

// ✗ Incorrect: Not exported — View typecheck cannot infer RegisteredTools
const localTool = server.tool({ name: "local", ... }, async (...) => {...});

// ✓ Correct: Re-exporting from child modules
export { analyzeReport } from "./tools/reporting.js";
```

### Why Static Exports Are Mandatory
When you run `npx mcp-use typecheck`, the CLI scans your server module for exported `ToolRef` instances and generates `mcp-env.d.ts`. This file maps tool names to their TypeScript input and output types, providing compile-time type safety for `useToolContext<"search">()` and `useCallTool("search")` inside React Views.

---

## Step 5: Resource & Template Signatures

Static resources and templates have updated callback signatures in v2:

### Static Resources: `(uri: URL, ctx: RequestContext)`
```typescript
// v2 Static Resource: First argument is parsed URL; second is context
export const configResource = server.resource(
  {
    name: "App Config",
    uri: "app://config",
    mimeType: "application/json",
  },
  async (uri, ctx) => ({
    contents: [
      {
        uri: uri.href,
        mimeType: "application/json",
        text: JSON.stringify({ environment: "production" }),
      },
    ],
  })
);
```

### Resource Templates: `(uri: URL, params: Record<string, string | string[]>, ctx: RequestContext)`
Resource templates use flattened top-level `uriTemplate` and `complete` dictionaries:

```typescript
// v2 Resource Template: Flattened fields, autocomplete support
export const userResource = server.resourceTemplate(
  {
    name: "User Record",
    uriTemplate: "users://{id}",
    mimeType: "application/json",
    complete: {
      id: async (value) => ["usr_1", "usr_2"].filter((id) => id.startsWith(value)),
    },
  },
  async (uri, { id }, ctx) => ({
    contents: [
      {
        uri: uri.href,
        mimeType: "application/json",
        text: JSON.stringify({ id: String(id), status: "active" }),
      },
    ],
  })
);
```

---

## Step 6: Prompts: Single `schema` Field

The deprecated v1 `args: [{ name, type }]` array is completely removed. In v2, prompts use a single Standard Schema (Zod v4 object) and pass the callback as the second argument:

```typescript
export const codeReviewPrompt = server.prompt(
  {
    name: "code-review",
    title: "Code Review Assistant",
    description: "Generate thorough code review instructions",
    schema: z.object({
      code: z.string().describe("Source code to review"),
      language: z.string().default("typescript").describe("Programming language"),
    }),
  },
  async ({ code, language }) => ({
    messages: [
      {
        role: "user",
        content: {
          type: "text",
          text: `Review the following ${language} code for safety and correctness:\n\n${code}`,
        },
      },
    ],
  })
);
```

---

## Step 7: Tool Annotations and Visibility

### Tool Annotations
Declare model execution hints via `annotations`:
```typescript
export const deleteRecord = server.tool(
  {
    name: "delete-record",
    inputSchema: z.object({ id: z.string() }),
    outputSchema: z.object({ success: z.boolean() }),
    annotations: {
      destructiveHint: true, // Warns host model before execution
      readOnlyHint: false,
      idempotentHint: true,
      openWorldHint: false,
    },
  },
  async ({ id }) => ({ content: [...], structuredContent: { success: true } })
);
```

### Tool Visibility (MCP Apps)
Declare tool audience using `visibility`:
- `"model"`: Model-callable and app-visible (standard default).
- `"app"`: Hidden from the model's `tools/list`; callable exclusively from Views via `useCallTool()`.

```typescript
export const viewHelper = server.tool(
  {
    name: "view-internal-helper",
    visibility: "app", // Hidden from LLM; accessible only by React Views
    inputSchema: z.object({ itemId: z.string() }),
    outputSchema: z.object({ details: z.string() }),
  },
  async ({ itemId }) => ({ content: [...], structuredContent: { details: "..." } })
);
```

---

## Anti-Patterns and Common Traps

| Anti-Pattern | Root Mechanism & Failure Mode | Canonical v2 Fix |
|---|---|---|
| `import { MCPServer } from "mcp-use/server"` | `./server` subpath export removed from `package.json`. Triggers `Cannot find module 'mcp-use/server'`. | Change to `import { MCPServer } from "mcp-use"`. |
| `server.tool(...).tool(...)` | `server.tool` returns `ToolRef`, not `this`. Method chaining throws `TypeError: server.tool(...).tool is not a function`. | Declare each tool as a separate statement: `export const a = server.tool(...)`. |
| Unexported Tool References | Tools declared with `const tool = server.tool(...)` without `export` are not discovered by `mcp-use typecheck`. | Prepend `export const <toolName> = server.tool(...)`. |
| Using Zod v3 Schemas | Zod v3 schemas lack the `~standard` interface required by v2 Standard Schema validation. | Upgrade to `zod@^4.0.0-alpha` or a Standard Schema compliant validator. |
| Constructor `baseUrl` | `baseUrl` was removed from `ServerConfig`. Fails TypeScript compilation. | Mount path is set by `basePath`; origin is configured via `MCP_URL` environment variable. |
| Passing Callback in `cb` Field | Passing callback inside the first argument object is ignored or fails schema validation. | Pass callback as the second argument: `server.tool(definition, callback)`. |

---

## Next Steps & Cross-References

- **Response Envelopes**: See `04-v1-to-v2-responses-and-helpers.md` for constructing `CallToolResult` envelopes.
- **Authentication Setup**: See `05-v1-to-v2-auth.md` for `mixedAuth: true` and provider adapters.
- **Views Integration**: See `06-v1-to-v2-widgets-to-views.md` for binding tools to interactive views.
