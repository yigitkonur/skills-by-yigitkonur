# Tool Design

*Read this when a tool is hard for a model to select, call correctly, or recover from after an expected failure.*

## Combining unrelated operations

Do not hide several capabilities behind an `action` argument:

```typescript
server.tool(
  {
    name: "manage-users",
    inputSchema: z.object({
      action: z.enum(["create", "get", "delete"]),
      payload: z.any(),
    }),
  },
  handler,
);
```

Register focused tools such as `create-user`, `get-user`, and `delete-user`. Each operation then has an accurate schema, description, and annotations.

## Using vague or inconsistent names

Prefer a specific action and object in kebab-case.

| Avoid | Use instead |
|---|---|
| `manage-users` | `create-user`, `get-user`, `delete-user` |
| `process` | `process-payment` |
| `data` | `get-billing-history` |
| `sendEmail` | `send-email` |

Names are client-visible identifiers. Keep them stable once published.

## Omitting the tool description

A name alone is not enough to distinguish similar tools:

```typescript
server.tool({ name: "search", inputSchema }, callback);
```

State the capability, scope, and important result limit:

```typescript
server.tool(
  {
    name: "search-docs",
    description: "Search internal product documentation and return at most 20 matching pages.",
    inputSchema,
  },
  callback,
);
```

Descriptions guide tool selection; field descriptions guide argument construction. See `references/04-tools/04-describe-and-annotations.md`.

## Hiding a static tool inside a loop

A static tool should be assigned to an exported module-level constant:

```typescript
for (const definition of definitions) {
  server.tool(definition, handler);
}
```

That dynamic shape prevents generated view typings from discovering a static `ToolRef`. Export each known tool directly. Reserve dynamic registration for genuinely runtime-derived tools such as OpenAPI operations. See `references/04-tools/02-registering-a-tool.md`.

## Misstating annotations

Do not mark a mutating tool as read-only or omit a destructive hint to avoid confirmation:

```typescript
annotations: {
  readOnlyHint: true,
  destructiveHint: false,
}
```

Set hints according to actual behavior. They influence host decisions but do not enforce authorization.

## Throwing expected operational failures

Do not throw for an expected not-found, rejected input, or upstream business failure:

```typescript
if (!user) throw new Error(`User ${id} not found`);
```

Return a tool error envelope so the client receives an MCP result:

```typescript
if (!user) {
  return {
    isError: true,
    content: [{ type: "text", text: `User ${id} was not found.` }],
  };
}
```

Keep the message safe and actionable. Unexpected programmer errors may still throw and be handled by the server boundary. See `references/05-responses/05-error-handling.md`.

## Passing through entire upstream responses

Do not return a large vendor payload unchanged. Select only fields required by the declared output contract. This keeps `structuredContent` stable and reduces model context cost.

## Correct v2 pattern

```typescript
export const getUser = server.tool(
  {
    name: "get-user",
    description: "Retrieve one user profile by its stable ID.",
    inputSchema: z.object({
      id: z.string().describe("Stable user ID"),
    }),
    outputSchema: z.object({
      id: z.string(),
      displayName: z.string(),
    }),
    annotations: {
      readOnlyHint: true,
      destructiveHint: false,
      openWorldHint: false,
    },
  },
  async ({ id }) => {
    const user = await users.find(id);
    if (!user) {
      return {
        isError: true,
        content: [{ type: "text", text: `User ${id} was not found.` }],
      };
    }

    const output = { id: user.id, displayName: user.displayName };
    return {
      content: [{ type: "text", text: `Found ${output.displayName}.` }],
      structuredContent: output,
    };
  },
);
```