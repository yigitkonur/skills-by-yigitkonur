# Schemas

*Read this when tool arguments are ambiguous, validation fails unexpectedly, or a project still uses Zod v3 patterns.*

## Keeping Zod v3

v2 expects Zod v4 or another Standard Schema implementation. Do not retain a Zod v3 dependency after migrating:

```json
{
  "dependencies": {
    "zod": "^3.0.0"
  }
}
```

Install Zod v4 and verify that the dependency tree does not contain an accidental v3 copy. See `references/02-setup/01-prerequisites.md`.

## Using the deprecated `schema` alias

This v1-style key remains an alias but should not be used in new v2 code:

```typescript
schema: z.object({ query: z.string() })
```

Use the MCP wire-aligned key:

```typescript
inputSchema: z.object({ query: z.string() })
```

See `references/04-tools/03-schemas-standard-schema-and-zod-v4.md`.

## Using `z.any()` or `z.unknown()` for normal inputs

These schemas remove useful validation and provide no argument guidance:

```typescript
inputSchema: z.object({ payload: z.any() })
```

Describe the real shape:

```typescript
inputSchema: z.object({
  payload: z.object({
    title: z.string().describe("Record title"),
    priority: z.enum(["low", "normal", "high"]).describe("Processing priority"),
  }),
})
```

If several unrelated payload shapes are possible, split the capability into separate tools.

## Omitting field descriptions

Do not rely on short names such as `id`, `value`, or `type` to explain the argument:

```typescript
inputSchema: z.object({
  id: z.string(),
  amount: z.number(),
})
```

Add `.describe()` to every input field:

```typescript
inputSchema: z.object({
  id: z.string().describe("Order ID"),
  amount: z.number().int().positive().describe("Refund amount in cents"),
})
```

Descriptions are emitted with the schema and help the model construct valid calls.

## Encoding a closed set as a free string

Do not describe allowed values only in prose:

```typescript
status: z.string().describe("One of open, closed, or pending")
```

Use an enum so the allowed values are machine-readable:

```typescript
status: z.enum(["open", "closed", "pending"]).describe("Issue status")
```

## Making every argument optional

An all-optional schema hides the actual contract and pushes validation into the handler. Keep required inputs required. Use `.default()` only where the server has a real default, and `.optional()` only where absence is meaningful.

## Declaring output without returning it

When `outputSchema` is set, successful results must include matching `structuredContent`. A text-only success violates the declared contract:

```typescript
outputSchema: z.object({ count: z.number() })
// Incorrect success:
return { content: [{ type: "text", text: "Found 3" }] };
```

Return `{ count: 3 }` in `structuredContent`, or return an `isError: true` envelope. See `references/04-tools/06-validation-pipeline.md`.

## Correct v2 pattern

```typescript
import { z } from "zod";

const inputSchema = z.object({
  query: z.string().min(1).describe("Search phrase"),
  status: z.enum(["open", "closed"]).describe("Issue status to include"),
  limit: z.number().int().min(1).max(50).default(10).describe("Maximum results"),
});

const outputSchema = z.object({
  count: z.number().int(),
  ids: z.array(z.string()),
});

export const searchIssues = server.tool(
  {
    name: "search-issues",
    description: "Search issues by phrase and status.",
    inputSchema,
    outputSchema,
  },
  async ({ query, status, limit }) => {
    const ids = await issues.search({ query, status, limit });
    return {
      content: [{ type: "text", text: `Found ${ids.length} issues.` }],
      structuredContent: { count: ids.length, ids },
    };
  },
);
```