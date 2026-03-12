# Tools & Schemas Reference

Definitive guide to registering tools, writing Zod schemas, and returning responses with mcp-use.

---

## Tool Registration API

Register tools with `server.tool()`. Every tool needs a name, description, input schema, and async handler.

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
  async (args) => text(`Hello, ${args.name}!`)
);
```

### Full Tool Signature

```typescript
server.tool(
  {
    name: "search-tickets",              // kebab-case, unique across server
    description:
      "Search support tickets by status and keyword. " +
      "Returns matching tickets sorted by creation date.",
    schema: z.object({
      query: z.string().min(1).max(200).describe("Search keyword"),
      status: z.enum(["open", "closed", "pending"]).describe("Ticket status filter"),
      limit: z.number().int().min(1).max(100).default(20).describe("Max results"),
    }).strict(),
    annotations: {
      title: "Search Tickets",
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: false,
    },
  },
  async (args, ctx) => {
    ctx.log("info", `Searching: query="${args.query}" status=${args.status}`);
    const tickets = await db.searchTickets(args.query, args.status, args.limit);
    return object({ tickets, total: tickets.length });
  }
);
```

### Annotation Reference

| Annotation | Type | Default | Purpose |
|---|---|---|---|
| `title` | `string` | — | Human-readable tool name for UI display |
| `readOnlyHint` | `boolean` | `false` | Tool does not modify any state |
| `destructiveHint` | `boolean` | `false` | Tool may delete or irreversibly alter data |
| `idempotentHint` | `boolean` | `false` | Repeated calls with same args produce same result |
| `openWorldHint` | `boolean` | `false` | Tool interacts with external/unbounded systems |

> **Guideline:** Set `readOnlyHint: true` on every read/search/get tool. Set `destructiveHint: true` on delete/remove tools. Clients may use these to prompt for confirmation.

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
// Strings
z.string().min(1).describe("Must not be empty")
z.string().min(1).max(100).describe("Between 1 and 100 chars")
z.string().email().describe("Valid email address")
z.string().url().describe("Valid URL")
z.string().uuid().describe("UUID identifier")
z.string().regex(/^[A-Z]{2}-\d+$/).describe("Ticket ID like AB-123")

// Numbers
z.number().int().positive().describe("Whole positive number")
z.number().min(0).max(100).describe("Percentage between 0 and 100")
z.number().int().min(1).max(1000).default(50).describe("Page size")
```

### Enums

```typescript
// Fixed string set
z.enum(["asc", "desc"]).describe("Sort direction")
z.enum(["low", "medium", "high", "critical"]).describe("Priority level")

// With default
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

> `.optional()` means the field can be omitted (`undefined` in handler). `.default(value)` means it can be omitted but always has a value.

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

Use when a field's type determines the shape of the rest of the object:

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

---

## Response Helpers

Import from `mcp-use/server`:

```typescript
import { text, object, markdown, image, mix, error, audio, binary, html, xml, array, resource } from "mcp-use/server";
```

### `text(content)`

Plain text response for simple messages.

```typescript
return text("User created successfully.");
return text(`Found ${count} results for "${query}".`);
```

### `object(data)`

Structured JSON. Preferred when the LLM will process the data further.

```typescript
return object({
  user: { id: "u_123", name: "Alice", role: "admin" },
  createdAt: "2025-01-15T10:30:00Z",
});
```

### `markdown(content)`

Markdown-formatted text for reports and formatted output.

```typescript
return markdown(`# Results\n\nFound **${results.length}** tickets matching "${query}".`);
```

### `image(base64, mimeType)`

```typescript
return image(chartBuffer.toString("base64"), "image/png");
```

### `mix(...responses)`

Combine multiple content types in one response.

```typescript
return mix(
  text("Here is the analysis:"),
  object({ metrics: { p50: 120, p99: 450 } }),
  image(chartBase64, "image/png"),
);
```

### `error(message)`

Error response with `isError: true`. The LLM treats this as a failure.

```typescript
return error("Ticket not found: " + ticketId);
return error(`Rate limit exceeded. Retry after ${retryAfter}s.`);
```

### Other Helpers

```typescript
return audio(base64Data, "audio/mp3");
return binary(base64Data, "application/octet-stream");
return html("<h1>Report</h1><p>Generated at ...</p>");
return xml("<response><status>ok</status></response>");
return array([item1, item2, item3]);
return resource("file:///path/to/data.csv", "text/csv", content);
```

---

## Context Object

The second argument to every handler is `ctx`, providing session state, logging, and advanced MCP features.

```typescript
server.tool(
  { name: "example", description: "...", schema: z.object({}) },
  async (args, ctx) => {
    ctx.session.id;                           // Unique session identifier
    const info = ctx.client.info();           // { name: "Claude", version: "3.5" }
    const caps = ctx.client.capabilities();   // Supported MCP features

    ctx.log("info", `Processing item ${args.id}`);
    ctx.log("warning", "Approaching rate limit");

    ctx.auth.user.userId;      // Authenticated user ID (requires OAuth)
    ctx.auth.permissions;      // Granted permissions/scopes

    // Elicitation — ask user for structured input
    const result = await ctx.elicit("Provide deployment target:", z.object({
      environment: z.enum(["staging", "production"]).describe("Target env"),
    }));
    if (result.action === "accept") { /* use result.data */ }

    // Sampling — LLM completions via the connected client
    const completion = await ctx.sample({
      messages: [{ role: "user", content: { type: "text", text: "Summarize: " + data } }],
      maxTokens: 500,
    });

    // Notifications
    await ctx.sendNotification("custom/progress", { step: 3, total: 10 });

    return text("Done");
  }
);
```

### Context Availability

| Feature | Requires | Notes |
|---|---|---|
| `ctx.session` | Any transport | Always available |
| `ctx.client.info()` | Client `initialize` | Most clients provide this |
| `ctx.log()` | Logging capability | Gracefully ignored if unsupported |
| `ctx.auth` | OAuth configured | `undefined` without auth |
| `ctx.elicit()` | Elicitation capability | Check capabilities first |
| `ctx.sample()` | Sampling capability | Check capabilities first |
| `ctx.sendNotification()` | SSE/StreamableHTTP | Not available over stdio |

---

## Tool Design Best Practices

### Naming

Use action verbs in kebab-case:

```
✅ get-user, create-ticket, search-orders, delete-comment, update-status
❌ user, ticket, process, handle, doStuff, data
```

### Descriptions

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

### Response Design

- **Prefer `object()`** for data the LLM will process or reference
- **Use `text()`** for simple confirmations
- **Use `error()`** for expected failures — LLM sees `isError: true`
- **Throw exceptions** only for unexpected failures (bugs, infra)
- **Curate responses** — return only fields the LLM needs, not raw API dumps

### Handler Pattern

```typescript
server.tool(
  {
    name: "get-order",
    description: "Retrieve an order by ID. Returns order details including items and status.",
    schema: z.object({
      orderId: z.string().regex(/^ORD-\d+$/).describe("Order ID like ORD-12345"),
    }),
  },
  async (args, ctx) => {
    try {
      const order = await db.getOrder(args.orderId);
      if (!order) return error(`Order ${args.orderId} not found.`);
      return object({
        id: order.id,
        status: order.status,
        items: order.items.map(i => ({ name: i.name, qty: i.quantity })),
        total: order.total,
      });
    } catch (err) {
      ctx.log("error", `Failed to fetch order: ${err.message}`);
      return error("Failed to retrieve order. Please try again.");
    }
  }
);
```

---

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Generic names: `process`, `handle`, `run` | LLM can't choose the right tool | Specific verbs: `search-users`, `create-ticket`, `delete-comment` |
| Missing `.describe()` on fields | LLM guesses at field purposes, often wrong | Add `.describe()` to every schema field |
| Returning raw API responses | Bloated context, confusing nested structures | Curate: return only relevant fields via `object()` |
| No error handling in handler | Unhandled throws crash the server process | Wrap in `try/catch`, return `error()` for expected failures |
| Too many parameters (>6) | LLM struggles to fill complex schemas correctly | Split into multiple focused tools with fewer params each |
| Mutable state without async safety | Race conditions under concurrent tool calls | Use locks, queues, or database transactions |
| Using `text()` for structured data | LLM can't reliably parse free-text data | Use `object()` for anything the LLM will reference |
| Giant catch-all tools | One tool doing 5 different things based on a "mode" param | One tool per action; use clear names |
| Not using annotations | Clients can't warn users before destructive actions | Set `readOnlyHint`, `destructiveHint` on every tool |
| Schema without `.strict()` | LLM may send extra hallucinated fields silently | Add `.strict()` to top-level schemas |
