# Registering a Tool

Use `server.tool(definition, handler)`. The definition object is the local tool contract; `mcp-use@1.26.0` forwards `name`, `title`, `description`, `inputSchema`, `annotations`, and `_meta` to the SDK for `tools/list`. The handler is what runs on `tools/call`.

## Minimum viable tool

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

`name` and a handler are the only hard requirements. `description` and `schema` are optional at the type level but mandatory in practice — without them the model cannot pick or call the tool reliably.

## Full signature

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
      tickets: z.array(z.object({ id: z.string(), title: z.string(), status: z.string() })),
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

## ToolDefinition fields

| Field | Type | Required | Purpose |
|---|---|---|---|
| `name` | `string` | yes | Unique kebab-case identifier. |
| `title` | `string` | no | Human-readable label for UIs. Falls back to `name`. |
| `description` | `string` | no | LLM-facing description. Always provide. |
| `schema` | `z.ZodTypeAny` | no | Input validation. Almost always provide. |
| `outputSchema` | `z.ZodTypeAny` | no | Typed structured output hint for TypeScript/codegen. Not forwarded to the SDK by `mcp-use@1.26.0`. See `07-input-schema-vs-output-schema.md`. |
| `annotations` | `ToolAnnotations` | no | Behavioral hints. See `04-describe-and-annotations.md`. |
| `cb` | `ToolCallback` | no | Inline handler instead of separate argument. |
| `_meta` | `Record<string, unknown>` | no | Opaque metadata (OpenAI Apps wiring, widget hydration). See `05-responses/09-meta-private-data.md`. |
| `widget` | `ToolWidgetConfig` | no | Widget config when returning `widget()`. See `18-mcp-apps/server-surface/01-widget-helper.md`. |
| `inputs` | `InputDefinition[]` | no | Deprecated. Use `schema`. |

## Naming

Use **action-verb + noun** in kebab-case. The name is the LLM's primary signal for which tool to pick.

```
get-user        create-ticket    search-orders
delete-comment  update-status    list-projects
```

Reject: `user`, `ticket`, `process`, `handle`, `doStuff`, `data`, `myTool`.

## Description

Write for the LLM. State **what**, **when**, and **what it returns**.

```typescript
description:
  "Look up a user by their ID or email. Returns profile including name, role, " +
  "and creation date. Use when the user asks about a specific person or account."
```

## Chaining

`server.tool()` returns the server, so multiple registrations chain.

```typescript
server
  .tool({ name: 'greet', ... }, ...)
  .tool({ name: 'search', ... }, ...)
  .tool({ name: 'update', ... }, ...);
```

## Dynamic tools

Add or remove tools after server start. Notify connected clients to refresh:

```typescript
server.tool({ name: "new-tool", schema: z.object({ input: z.string() }) }, async ({ input }) => text(input));
await server.sendToolsListChanged();
```
