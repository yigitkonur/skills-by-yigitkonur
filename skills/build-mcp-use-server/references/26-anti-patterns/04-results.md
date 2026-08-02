# Results

*Read this when a tool still returns v1 helper values or its readable and structured result surfaces disagree.*

## Treating response helpers as the v2 default

The compatibility helpers remain exported but are deprecated. Do not teach new code to build results with `text()`, `object()`, `mix()`, `error()`, or `widget()`:

```typescript
import { object, text } from "mcp-use";
return object({ id, name });
```

Return the raw MCP envelope:

```typescript
return {
  content: [{ type: "text", text: `Found ${name}.` }],
  structuredContent: { id, name },
};
```

Use `references/05-responses/07-deprecated-v1-helpers.md` only when migrating helper-based code.

## Returning only stringified JSON

Do not force clients or models to parse JSON from a text block when the tool has structured output:

```typescript
return {
  content: [{ type: "text", text: JSON.stringify(result) }],
};
```

Declare `outputSchema`, return matching `structuredContent`, and keep a concise text fallback.

## Letting the two result surfaces disagree

Different hosts may consume different surfaces. These two values contradict each other:

```typescript
return {
  content: [{ type: "text", text: "Payment succeeded." }],
  structuredContent: { status: "failed" },
};
```

Both surfaces must communicate the same essential outcome. See `references/05-responses/03-structured-content-and-output-schema.md`.

## Omitting `structuredContent` with `outputSchema`

A successful result for a schema-backed tool must include `structuredContent` matching that schema. This is especially important for a tool bound to a View, because the View reads its props from `structuredContent`.

Do not add a View to a text-only tool. Define the output schema first, then return the matching value. See `references/18-mcp-apps/server-surface/01-tool-view-field.md`.

## Reporting an expected failure as normal text

This looks like a successful tool result to the client:

```typescript
return {
  content: [{ type: "text", text: "Error: user not found" }],
};
```

Set `isError: true`:

```typescript
return {
  isError: true,
  content: [{ type: "text", text: "User was not found." }],
};
```

Do not put stack traces, secrets, raw tokens, or internal paths in model-visible error text. See `references/05-responses/05-error-handling.md`.

## Putting private data in `structuredContent`

`structuredContent` is part of the tool result. Do not place access tokens, credentials, internal headers, or unnecessary upstream payloads there. Result `_meta` is for host-side auxiliary data, but it is not a substitute for secret storage. Keep secrets on the server.

## Returning unbounded payloads

Do not return an entire database table or upstream API response. Select fields covered by `outputSchema`, paginate results, or expose a resource for data that is naturally retrievable by URI.

## Correct v2 pattern

```typescript
const outputSchema = z.object({
  id: z.string(),
  displayName: z.string(),
});

export const getUser = server.tool(
  {
    name: "get-user",
    description: "Retrieve one user profile.",
    inputSchema: z.object({
      id: z.string().describe("Stable user ID"),
    }),
    outputSchema,
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