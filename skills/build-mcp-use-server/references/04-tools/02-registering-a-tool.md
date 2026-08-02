# Registering a Tool

*Read this when adding a tool to your server.*

Use `server.tool(definition, callback)` to register a tool. The definition is the contract (name, descriptions, schemas); the callback is what runs. Both are required at startup (definition-time work must be cheap — put databases and caches at module scope).

## Minimum Viable Tool

```typescript
import { MCPServer } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({ name: "my-server", version: "1.0.0" });

export const greet = server.tool(
  {
    name: "greet",
    description: "Return a greeting for the given name.",
    inputSchema: z.object({
      name: z.string().describe("Person to greet"),
    }),
  },
  async ({ name }, ctx) => ({
    content: [{ type: "text", text: `Hello, ${name}!` }],
  })
);
```

**Export every static tool as `const`** — the auto-generated `mcp-env.d.ts` derives view types from exported `ToolRef` names.

## Full Signature (with Optional Fields)

```typescript
export const searchTickets = server.tool(
  {
    name: "search-tickets",
    title: "Search Tickets",
    description: "Search support tickets by status and keyword. Returns matching tickets sorted by creation date.",
    inputSchema: z.object({
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
    view: {
      name: "ticket-results",
      description: "Interactive ticket search results",
      prefersBorder: true,
    },
  },
  async (args, ctx) => {
    await ctx.sendLog("info", `Searching: query="${args.query}" status=${args.status}`);
    const tickets = await db.searchTickets(args.query, args.status, args.limit);
    return {
      content: [{ type: "text", text: `Found ${tickets.length} tickets` }],
      structuredContent: { tickets, total: tickets.length },
    };
  }
);
```

## ToolDefinition Fields

| Field | Type | Default | Purpose |
|---|---|---|---|
| `name` | `string` | (required) | Unique kebab-case identifier, e.g., `"get-user"` |
| `title` | `string` | Inferred from `name` | Human-readable label for UIs |
| `description` | `string` | undefined | LLM-facing description of behavior |
| `inputSchema` | `StandardSchemaWithJSON` | undefined | Input validation (Zod v4, ArkType, Valibot, etc.); every field must have `.describe()` |
| `outputSchema` | `StandardSchemaWithJSON` | undefined | Output schema (required if tool has a `view`); SDK validates `structuredContent` at runtime |
| `annotations` | `ToolAnnotations` | undefined | Hints: `readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint` |
| `_meta` | `MetaObject` | undefined | Opaque extension metadata on `tools/list` descriptor |
| `view` | `ToolViewConfig` | undefined | Bind tool to MCP App view; requires `outputSchema`. Shape: `{ name, description?, csp?, permissions?, domain?, prefersBorder? }` |

## Return Type

Handlers return `ToolResult<TOutput>`:

```typescript
type ToolResult<TOutput> = 
  | InputRequiredResult                         // elicitation re-run
  | (TOutput extends never 
      ? CallToolResult                          // no outputSchema: any CallToolResult
      : (CallToolResult & { structuredContent: TOutput })  // with outputSchema: must include structuredContent
        | (CallToolResult & { isError: true }))  // or error response
```

## Naming Convention

Use **action-verb + noun** in kebab-case:

```
get-user         create-ticket      search-orders
delete-comment   update-status      list-projects
```

Avoid: bare nouns (`user`), generic verbs (`handle`, `process`), camelCase.

## Description Discipline

Write for the LLM. Include **what**, **when to use**, and **what is returned**:

```typescript
description: 
  "Search support tickets by status and keyword. " +
  "Returns matching tickets sorted by creation date. " +
  "Use when the user needs to find specific tickets."
```

## ToolRef Export

Every static tool returns a `ToolRef<Name, Input, Output>` with phantom type info. Export it so `mcp-env.d.ts` can expose the type to Views:

```typescript
export const getTool = server.tool(...);
// mcp-env.d.ts now knows getTool's input and output types
```

## Chaining

`server.tool()` returns the server for chaining:

```typescript
server
  .tool({ name: "greet", ... }, ...)
  .tool({ name: "search", ... }, ...)
  .tool({ name: "update", ... }, ...);
```
