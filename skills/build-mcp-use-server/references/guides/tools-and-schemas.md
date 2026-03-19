# Tools and Schemas

Definitive guide to registering tools, writing Zod schemas, and handling tool calls with mcp-use.

---

## Tool Registration API

Register tools using the chainable `.tool(definition, handler)` method on your `MCPServer` instance.

### Minimal Tool

```typescript
import { MCPServer, text } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({ name: "my-server", version: "1.0.0" });

server.tool(
  {
    name: "greet",
    description: "Return a greeting for the given name.",
    schema: z.object({
      name: z.string().describe("Person to greet"),
    }),
  },
  async ({ name }) => text(`Hello, ${name}!`)
);
```

### Chaining Multiple Tools

```typescript
server
  .tool({ name: 'greet', ... }, async (params) => { ... })
  .tool({ name: 'search', ... }, async (params) => { ... })
  .tool({ name: 'update', ... }, async (params) => { ... });
```

### Full Tool Signature

```typescript
server.tool(
  {
    name: "search-tickets",
    title: "Search Tickets",
    description:
      "Search support tickets by status and keyword. " +
      "Returns matching tickets sorted by creation date.",
    schema: z.object({
      query: z.string().min(1).max(200).describe("Search keyword"),
      status: z.enum(["open", "closed", "pending"]).describe("Ticket status filter"),
      limit: z.number().int().min(1).max(100).default(20).describe("Max results"),
    }).strict(),
    outputSchema: z.object({
      tickets: z.array(z.object({
        id: z.string(),
        title: z.string(),
        status: z.string(),
      })),
      total: z.number(),
    }),
    annotations: {
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: false,
    },
  },
  async (args, ctx) => {
    await ctx.log("info", `Searching: query="${args.query}" status=${args.status}`);
    const tickets = await db.searchTickets(args.query, args.status, args.limit);
    return object({ tickets, total: tickets.length });
  }
);
```

---

## ToolDefinition Properties

| Property | Type | Required | Purpose |
|---|---|---|---|
| `name` | `string` | Yes | Unique identifier (kebab-case) |
| `title` | `string` | No | Human-readable name for UI; falls back to `name` |
| `description` | `string` | No | LLM-facing description of what the tool does |
| `schema` | `z.ZodTypeAny` | No | Zod schema for input validation |
| `outputSchema` | `z.ZodTypeAny` | No | Zod schema for structured output; enables type inference in `useCallTool()` |
| `annotations` | `ToolAnnotations` | No | Behavioral hints for clients (read-only, destructive, etc.) |
| `cb` | `ToolCallback` | No | Inline handler (alternative to separate callback argument) |
| `_meta` | `Record<string, unknown>` | No | Opaque metadata passed through to MCP protocol (used for OpenAI Apps SDK integration) |
| `widget` | `ToolWidgetConfig` | No | Widget config for tools returning `widget()` responses |
| `inputs` | `InputDefinition[]` | No | **Deprecated.** Use `schema` (Zod) instead. |

**`ToolWidgetConfig` fields** (used with `widget` property):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | Yes | Widget name — must match a widget folder in `resources/` |
| `invoking` | `string` | No | Status text shown while the tool is running (auto-defaulted to `"Loading <name>..."`) |
| `invoked` | `string` | No | Status text shown after the tool completes (auto-defaulted to `"<name> ready"`) |
| `widgetAccessible` | `boolean` | No | Whether the widget can initiate tool calls (e.g., via `useCallTool`). Defaults to `true`. |
| `resultCanProduceWidget` | `boolean` | No | Whether this tool result can produce a widget. Defaults to `true`. |

---

## Complex Zod Patterns

The `mcp-use` server relies on Zod for runtime validation and JSON Schema generation.

### Discriminated Unions (Polymorphism)

Use `z.discriminatedUnion` when a tool accepts different shapes of data based on a type field.

```typescript
const notificationSchema = z.discriminatedUnion("channel", [
  z.object({
    channel: z.literal("email"),
    address: z.string().email(),
    subject: z.string(),
  }),
  z.object({
    channel: z.literal("slack"),
    channelId: z.string(),
    mrkdwn: z.boolean(),
  }),
]);

server.tool(
  {
    name: "send-notification",
    schema: z.object({
      notification: notificationSchema,
    }),
  },
  async ({ notification }) => {
    if (notification.channel === "email") {
      // notification.address is typed here
    } else {
      // notification.channelId is typed here
    }
    return text("Sent");
  }
);
```

### Recursive Schemas

Use `z.lazy()` for recursive data structures like file trees.

```typescript
const nodeSchema: z.ZodType<Node> = z.lazy(() =>
  z.object({
    name: z.string(),
    children: z.array(nodeSchema).optional(),
  })
);

server.tool(
  {
    name: "process-tree",
    schema: z.object({ root: nodeSchema }),
  },
  // ...
);
```

### Records (Dynamic Keys)

Use `z.record()` when keys are not known in advance.

```typescript
server.tool(
  {
    name: "update-env",
    schema: z.object({
      vars: z.record(z.string(), z.string()).describe("Environment variables to set"),
    }),
  },
  async ({ vars }) => {
    // vars is Record<string, string>
    return text(`Updated ${Object.keys(vars).length} variables`);
  }
);
```

### Intersections

Combine schemas with `.and()` or `z.intersection()`.

```typescript
const pagination = z.object({ page: z.number(), limit: z.number() });
const filters = z.object({ status: z.string() });

server.tool(
  {
    name: "list-items",
    schema: pagination.and(filters),
  },
  async ({ page, limit, status }) => {
    // All fields available
    return text("Listing...");
  }
);
```

---

## Context Object (`ctx`)

The second argument to every handler provides session state and advanced capabilities.

| Property | Type | Description |
|---|---|---|
| `ctx.session` | `Session` | Current session object (id, transport, etc.) |
| `ctx.client` | `ClientInfo` | Client identity and capabilities |
| `ctx.client.info()` | `Function` | Returns `{ name, version }` from the MCP `initialize` handshake |
| `ctx.client.can(capability)` | `Function` | Returns `true`/`false` for a given capability (e.g., `'sampling'`) |
| `ctx.client.supportsApps()` | `Function` | Returns `true` if client is MCP Apps / ChatGPT compatible |
| `ctx.client.extension(id)` | `Function` | Returns extension metadata by ID (e.g., `'io.modelcontextprotocol/ui'`) |
| `ctx.client.user()` | `Function` | Returns per-invocation `UserContext` from `params._meta`, or `undefined` |
| `ctx.log(level, msg)` | `Function` | Send logs to the client (`debug`, `info`, `notice`, `warning`, `error`, `critical`, `alert`, `emergency`) |
| `ctx.auth` | `AuthContext` | Authenticated user info (if OAuth enabled) |
| `ctx.reportProgress` | `Function` | Report progress `(loaded, total, message)` |
| `ctx.elicit` | `Function` | Request user input mid-execution |
| `ctx.sample` | `Function` | Request LLM sampling from client |
| `ctx.sendNotification` | `Function` | Send custom notification to client |

### Example Usage

```typescript
async (args, ctx) => {
  const { sessionId } = ctx.session;
  const { name, version } = ctx.client.info();
  
  // Log to client console
  await ctx.log("info", `Processing request in session ${sessionId}`);

  // Check capabilities
  if (ctx.client.can("sampling")) {
    const summary = await ctx.sample("Summarize this...");
  }

  // Report progress
  await ctx.reportProgress(50, 100, "Halfway there");
  
  return text("Done");
}
```

---

## Error Handling

Proper error handling ensures the LLM understands *why* a tool failed rather than just seeing a crash.

### Expected Errors

Use the `error()` helper for logic failures (e.g., "User not found").

```typescript
import { error } from "mcp-use/server";

if (!user) {
  return error(`User ${id} not found`);
}
```

This returns a result with `isError: true`, which the LLM interprets as a failure to correct.

### Unexpected Errors

Throwing an error will result in an Internal Server Error (500) unless caught.

```typescript
try {
  await db.query();
} catch (err) {
  await ctx.log("error", `DB failed: ${err.message}`);
  return error("Database unavailable");
}
```

---

## Tool Annotations

Annotations are behavioral hints that clients use to present confirmation dialogs, filter tools, or optimize execution. Set them in the `annotations` object on the tool definition.

| Annotation | Type | Default | Purpose |
|---|---|---|---|
| `readOnlyHint` | `boolean` | `false` | Tool does not modify any state |
| `destructiveHint` | `boolean` | `true` | Tool may delete or irreversibly alter data (only meaningful when `readOnlyHint` is `false`) |
| `idempotentHint` | `boolean` | `false` | Repeated calls with same args produce same result (only meaningful when `readOnlyHint` is `false`) |
| `openWorldHint` | `boolean` | `true` | Tool interacts with external/unbounded systems |

Additional custom annotations supported by mcp-use:

| Annotation | Type | Purpose |
|---|---|---|
| `requiresAuth` | `boolean` | Tool requires authenticated session |
| `rateLimit` | `string` | Rate limit description (e.g., `"10/minute"`) |
| `deprecated` | `boolean` | Tool is deprecated; clients may hide or warn |

```typescript
// Read-only search tool                      // Destructive delete tool
annotations: {                                annotations: {
  readOnlyHint: true,                           readOnlyHint: false,
  destructiveHint: false,                       destructiveHint: true,
  idempotentHint: true,                         idempotentHint: false,
  openWorldHint: false,                         openWorldHint: false,
}                                               requiresAuth: true,
                                              }
```

> **Guideline:** Set `readOnlyHint: true` on every read/search/get tool. Set `destructiveHint: true` on delete/remove tools. Clients may use these to prompt for confirmation.

---

## Returning Widgets from Tools

This is the recommended way to expose widgets to a model. Since `exposeAsTool` defaults to `false`, widgets are registered as MCP resources only. Defining a custom tool that calls `widget()` gives you full control over the tool's name, description, schema, and business logic.

You must include the `widget: { name, ... }` config in your tool definition when returning widgets. This sets up all the registration-time metadata needed for proper widget rendering. The widget file must exist in your `resources/` folder but does **not** need `exposeAsTool: true`.

```typescript
import { widget, text } from 'mcp-use/server';
import { z } from 'zod';

server.tool({
  name: 'get-weather',
  description: 'Get current weather for a city',
  schema: z.object({
    city: z.string().describe('City name')
  }),
  // Widget config sets all registration-time metadata
  widget: {
    name: 'weather-display',  // Must match a widget in resources/
    invoking: 'Fetching weather...',
    invoked: 'Weather loaded'
  }
}, async ({ city }) => {
  const weatherData = await fetchWeather(city);

  // Return widget with runtime data only
  return widget({
    props: weatherData,              // Widget-only data passed to useWidget().props (hidden from model)
    output: text(`Weather in ${city}: ${weatherData.temp}°C`),  // What the model sees
    message: `Current weather in ${city}`  // Optional text message override
  });
});
```

See the [UI Widgets guide](./ui-widgets) for complete widget creation and registration documentation.

---

## OpenAI Apps SDK Integration (`_meta`)

For ChatGPT and OpenAI-compatible clients, use `_meta` on the tool definition and in the handler return value to wire up widget rendering:

```typescript
server.tool({
  name: 'show_chart',
  description: 'Display a chart',
  schema: z.object({
    data: z.array(z.any()).describe('The chart data')
  }),
  _meta: {
    'openai/outputTemplate': 'ui://widgets/chart',
    'openai/toolInvocation/invoking': 'Generating chart...',
    'openai/toolInvocation/invoked': 'Chart generated',
    'openai/widgetAccessible': true
  }
}, async ({ data }) => {
  return {
    _meta: {
      'openai/outputTemplate': 'ui://widgets/chart'
    },
    content: [{
      type: 'text',
      text: 'Chart displayed'
    }],
    structuredContent: { data }
  };
});
```

> **Note:** The recommended approach is to use the `widget` helper in a custom tool (see above) or set `exposeAsTool: true` in a widget's metadata. The `_meta` pattern is the lower-level mechanism used internally.

---

## Zod Schema Patterns

Schemas define what arguments a tool accepts. The schema is converted to JSON Schema for the MCP protocol, so `.describe()` on every field is critical — it's how the LLM knows what to provide.

### Primitives

```typescript
z.string().describe("User's email address")
z.number().describe("Quantity to order")
z.boolean().describe("Whether to include archived items")
```

### Constrained Primitives

```typescript
z.string().min(1).max(100).describe("Between 1 and 100 chars")
z.string().email().describe("Valid email")    z.string().url().describe("Valid URL")
z.string().uuid().describe("UUID identifier") z.string().regex(/^[A-Z]{2}-\d+$/).describe("Ticket ID like AB-123")
z.number().int().positive().describe("Whole positive number")
z.number().min(0).max(100).describe("Percentage 0-100")
z.number().int().min(1).max(1000).default(50).describe("Page size")
```

### Enums

```typescript
z.enum(["asc", "desc"]).describe("Sort direction")
z.enum(["low", "medium", "high", "critical"]).describe("Priority level")
z.enum(["created", "updated", "priority"]).default("created").describe("Sort field")
```

### Optional and Default Fields

```typescript
z.object({
  query: z.string().min(1).describe("Search term — required"),
  page: z.number().int().positive().optional().describe("Page number, omit for first page"),
  limit: z.number().int().min(1).max(100).default(25).describe("Results per page"),
})
```

> `.optional()` means the field can be omitted (`undefined` in handler). `.default(value)` means it can be omitted but always has a value in the handler.

### Nested Objects

```typescript
z.object({
  user: z.object({
    name: z.string().min(1).describe("Full name"),
    email: z.string().email().describe("Email address"),
    role: z.enum(["admin", "member", "viewer"]).describe("User role"),
  }).describe("User to create"),
  sendWelcomeEmail: z.boolean().default(true).describe("Send welcome email on creation"),
})
```

### Arrays

```typescript
z.object({
  tags: z.array(z.string()).describe("Tags to apply"),
  userIds: z.array(z.string().uuid()).min(1).max(50).describe("User IDs to notify"),
  items: z.array(
    z.object({
      productId: z.string().describe("Product identifier"),
      quantity: z.number().int().positive().describe("Number of items"),
    })
  ).min(1).describe("Line items in the order"),
})
```

### Discriminated Unions

```typescript
z.object({
  action: z.discriminatedUnion("type", [
    z.object({
      type: z.literal("email"),
      to: z.string().email().describe("Recipient email"),
      subject: z.string().describe("Subject line"),
    }),
    z.object({
      type: z.literal("sms"),
      phone: z.string().describe("Phone number with country code"),
      message: z.string().max(160).describe("SMS text"),
    }),
  ]).describe("Notification channel and its parameters"),
})
```

### Using `.strict()`

Reject unknown fields to prevent LLM hallucination:

```typescript
z.object({
  id: z.string().describe("Record ID"),
  title: z.string().describe("New title"),
}).strict()  // Rejects { id: "1", title: "x", unknownField: true }
```

### Completable Schemas

`completable()` provides autocomplete hints for `server.prompt()` argument fields. It is **not supported** for `server.tool()` schemas. For resource template URI variable autocomplete, use `callbacks.complete` on the `resourceTemplate` definition instead.

```typescript
import { completable } from "mcp-use/server";

// ✅ Valid: completable() in a prompt schema
server.prompt(
  {
    name: "run-linter",
    schema: z.object({
      language: completable(z.string().describe("Programming language"), [
        "python", "typescript", "rust", "go", "java",
      ]),
      project: completable(
        z.string().describe("Project name"),
        async (value) => db.search(value).map((r) => r.name)
      ),
    }),
  },
  async ({ project, language }) =>
    `Lint ${project} as ${language}`
);

// ✅ Valid: autocomplete for resourceTemplate URI variables
server.resourceTemplate(
  {
    name: "project-file",
    uriTemplate: "project://{name}/files",
    callbacks: {
      complete: {
        name: async (value) => db.search(value).map((r) => r.name),
      },
    },
  },
  async (uri, { name }) => object(await db.getProject(name))
);
```

---

## Handler Callback

The handler is `async (args, ctx) => result`. `args` is typed from the Zod schema; `ctx` provides session state, logging, and advanced MCP features. See `response-helpers.md` for the complete guide to response helpers (`text`, `object`, `error`, `mix`, `markdown`, `image`, etc.).

---

## Client Identity & Caller Context

### Session-level client info

Values from the MCP `initialize` handshake, stable for the connection lifetime:

```typescript
server.tool({ name: "check-client", schema: z.object({}) }, async (_p, ctx) => {
  const { name, version } = ctx.client.info();      // "ChatGPT", "1.0.0"
  const hasSampling = ctx.client.can("sampling");    // true / false
  const isAppsClient = ctx.client.supportsApps();    // MCP Apps / ChatGPT
  const uiExt = ctx.client.extension('io.modelcontextprotocol/ui');
  return text(`${name} ${version}, apps: ${isAppsClient}`);
});
```

### Per-invocation caller context — `ctx.client.user()`

Returns normalized metadata from `params._meta` that some clients send with every `tools/call`. Returns `undefined` for clients that don't send this (Inspector, Claude Desktop, CLI, etc.).

> **Warning:** This data is client-reported and unverified. Do not use for access control. Use `ctx.auth` with OAuth for verified identity.

**`UserContext` fields:** `subject` (stable user ID), `conversationId` (chat thread), `locale` (BCP-47), `location` (`{ city, region, country, timezone, latitude, longitude }`), `userAgent`, `timezoneOffsetMinutes`

### ChatGPT Multi-Tenant Model

ChatGPT establishes a **single MCP session for all users** of a deployed app. The session ID alone cannot identify individual callers — use `ctx.client.user()`:

```
1 MCP session  ctx.session.sessionId              — shared across ALL users
  N subjects   ctx.client.user()?.subject         — one per ChatGPT user account
    M threads  ctx.client.user()?.conversationId  — one per chat conversation
```

---

## Tool Logging

Tools send log messages to clients during execution using `ctx.log()`. Useful for progress reporting, debugging, and real-time feedback during long operations.

```typescript
server.tool({
  name: "process-files",
  description: "Process multiple files",
  schema: z.object({ files: z.array(z.string()) }),
}, async ({ files }, ctx) => {
  await ctx.log("info", "Starting file processing");
  for (const file of files) {
    await ctx.log("debug", `Processing ${file}`);
    // ... process file ...
  }
  await ctx.log("info", "Processing completed");
  return text(`Processed ${files.length} files`);
});
```

**MCP Log Levels** (ascending severity): `debug`, `info`, `notice`, `warning`, `error`, `critical`, `alert`, `emergency`

> The third argument to `ctx.log()` is an optional logger name string. Example: `await ctx.log('info', 'Done', 'my-logger')`.

---

## Notifying Clients of Tool Changes

When dynamically adding or removing tools at runtime, notify connected clients to refresh their tool list:

```typescript
server.tool({
  name: "new-tool",
  description: "A dynamically added tool",
  schema: z.object({ input: z.string() }),
}, async ({ input }) => text(`Processed: ${input}`));

await server.sendToolsListChanged();
```

---

## Tool Naming Conventions

Use **action-verb + noun** in kebab-case:

```
✅ get-user, create-ticket, search-orders, delete-comment, update-status, list-projects
❌ user, ticket, process, handle, doStuff, data, myTool
```

The name is the tool's unique identifier across the server. The `title` field provides a human-readable label for UIs.

---

## Best Practices

### Descriptions for LLMs

Write descriptions for LLMs, not humans. Be specific about **what**, **when**, and **what it returns**:

```typescript
// ❌ Too vague
description: "Gets user data"

// ✅ Specific and actionable
description:
  "Look up a user by their ID or email. Returns profile including name, role, and creation date. " +
  "Use when the user asks about a specific person or account."
```

### Schema Design

- **`.describe()` on every field** — the LLM reads these to decide what values to provide
- **Use constraints** — `min`, `max`, `email`, `uuid` catch bad input before your handler
- **Use `.default()`** — reduce required fields with sensible defaults
- **Use `.strict()`** — prevent hallucinated extra fields
- **Keep schemas flat** — avoid deep nesting; LLMs handle flat objects better

### Error Handling

```typescript
server.tool({
  name: "get-order",
  description: "Retrieve an order by ID.",
  schema: z.object({
    orderId: z.string().regex(/^ORD-\d+$/).describe("Order ID like ORD-12345"),
  }),
}, async (args, ctx) => {
  try {
    const order = await db.getOrder(args.orderId);
    if (!order) return error(`Order ${args.orderId} not found.`);
    return object({
      id: order.id, status: order.status,
      items: order.items.map(i => ({ name: i.name, qty: i.quantity })),
      total: order.total,
    });
  } catch (err) {
    ctx.log("error", `Failed to fetch order: ${err.message}`);
    return error("Failed to retrieve order. Please try again.");
  }
});
```

- Use `error()` for expected failures — LLM sees `isError: true`
- Throw exceptions only for unexpected failures (bugs, infra)
- Curate responses — return only fields the LLM needs, not raw API dumps

---

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Generic names: `process`, `handle` | LLM can't choose the right tool | Specific verbs: `search-users`, `create-ticket` |
| Missing `.describe()` on fields | LLM guesses at field purposes | Add `.describe()` to every schema field |
| Returning raw API responses | Bloated context, confusing nesting | Curate with `object()` — only relevant fields |
| No error handling in handler | Unhandled throws crash the server | Wrap in `try/catch`, return `error()` |
| Too many parameters (>6) | LLM struggles with complex schemas | Split into multiple focused tools |
| Giant catch-all tools | One tool doing 5 things via "mode" param | One tool per action |
| Not using annotations | Clients can't warn before destructive actions | Set `readOnlyHint`, `destructiveHint` |
| Schema without `.strict()` | LLM may send hallucinated extra fields | Add `.strict()` to top-level schemas |
---

## Zod Schema Cookbook

A collection of common validation patterns for MCP tools.

### Date Strings

Validate ISO 8601 dates.

```typescript
const dateSchema = z.string().datetime({ offset: true });
// "2023-01-01T00:00:00Z"
```

### JSON Strings

Parse a string containing JSON.

```typescript
const jsonSchema = z.string().transform((str, ctx) => {
  try {
    return JSON.parse(str);
  } catch (e) {
    ctx.addIssue({ code: z.ZodIssueCode.custom, message: "Invalid JSON" });
    return z.NEVER;
  }
});
```

### File Paths (Safe)

Prevent directory traversal attacks.

```typescript
const pathSchema = z.string().regex(/^[\w\-. /]+$/).refine((val) => !val.includes(".."), {
  message: "Path cannot contain '..'",
});
```

### SemVer

Validate semantic versions.

```typescript
const semverSchema = z.string().regex(/^\d+\.\d+\.\d+(-[\w.]+)?$/);
// "1.0.0", "2.0.0-beta.1"
```

### URL with Protocol

Enforce HTTPS.

```typescript
const urlSchema = z.string().url().startsWith("https://");
```

---

## Testing Tools

Tools are just functions. You can unit test them directly by importing the handler or mocking the context.

### Unit Testing

```typescript
// tool.ts
export const addTool = {
  name: "add",
  schema: z.object({ a: z.number(), b: z.number() }),
  handler: async ({ a, b }) => text(`${a + b}`),
};

// tool.test.ts
import { addTool } from "./tool";
import { describe, it, expect } from "vitest";

describe("addTool", () => {
  it("adds two numbers", async () => {
    const result = await addTool.handler({ a: 1, b: 2 }, {} as any);
    expect(result).toEqual({ 
      content: [{ type: "text", text: "3" }],
      isError: false 
    });
  });
});
```

### Mocking Context

Create a minimal mock context for tests requiring logs or auth.

```typescript
const mockCtx = {
  session: { sessionId: "test-session" },
  log: vi.fn(),
  auth: { userId: "user-1" },
  reportProgress: vi.fn(),
};

await myTool.handler(args, mockCtx);
expect(mockCtx.log).toHaveBeenCalledWith("info", "Processing...");
```

---

## Validation Errors

When a tool call fails schema validation, `mcp-use` automatically returns a detailed error to the client (and thus the LLM).

### Error Format

The error message includes the path and issue for every failure:

```
Validation Error:
- name: Required
- age: Expected number, received string
- email: Invalid email address
```

This helps the LLM self-correct and try again with valid arguments.

### Custom Error Messages

Customize Zod error messages to guide the LLM.

```typescript
z.string().min(10, { message: "Description must be at least 10 characters long to be useful." })
```

---

## Performance Optimization

Tool handlers run in the main event loop. Keep them fast to avoid blocking other requests.

### Parallel Execution

Use `Promise.all` for independent operations.

```typescript
// ❌ Sequential (slow)
const user = await db.getUser(id);
const posts = await db.getPosts(id);

// ✅ Parallel (fast)
const [user, posts] = await Promise.all([
  db.getUser(id),
  db.getPosts(id),
]);
```

### Caching

Cache expensive computations or API calls.

```typescript
import { LRUCache } from "lru-cache";

const cache = new LRUCache({ max: 100, ttl: 60000 });

async (args) => {
  const key = JSON.stringify(args);
  if (cache.has(key)) return cache.get(key);

  const result = await computeExpensiveResult(args);
  cache.set(key, result);
  return result;
};
```

### Offloading

For CPU-intensive tasks (image processing, heavy parsing), use worker threads or offload to a separate service to keep the MCP server responsive.

## Tool Design Patterns

### Descriptions

```typescript
// ❌ BAD: Vague description
description: "Get data"

// ✅ GOOD: Specific for LLM
description: "Retrieve user profile by email or ID. Use when asked about specific user details."
```

### Schemas

```typescript
// ❌ BAD: Any types
z.any()

// ✅ GOOD: Specific types
z.object({ id: z.string().uuid() })
```

### Handlers

```typescript
// ❌ BAD: Throwing strings
throw "Failed";

// ✅ GOOD: Returning error objects
return error("Operation failed: resource locked");
```
