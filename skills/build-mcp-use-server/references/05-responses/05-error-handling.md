# Error handling

*Read this when a tool call fails validation, runtime, or auth.*

## Error envelope (isError: true)

Return error **without throwing**:

```typescript
return {
  isError: true,
  content: [{ type: "text", text: "User not found: user_123" }],
};
```

Prefer returning error envelopes over throwing — you control the message and avoid the generic conversion below. That said, an uncaught throw is not fatal: the SDK's `tools/call` handler wraps every tool execution in try/catch and converts any thrown error into `{ content: [{ type: "text", text: errorMessage }], isError: true }` automatically, with no logging and no crash. `errorMessage` is `error.message` for `Error` instances, or `String(error)` otherwise — so a thrown `Error("Not found")` becomes indistinguishable on the wire from `return { isError: true, content: [{ type: "text", text: "Not found" }] }`. The difference is control: a thrown error loses the chance to add context, pick a friendlier message, or attach recovery hints before the client sees it.

## When to error vs throw

| Scenario | Action | Example |
|----------|--------|---------|
| Input schema rejects arguments (before callback runs) | SDK converts the thrown validation error into `{ isError: true, content: [...] }` — same try/catch as an in-callback throw | Missing required field |
| Auth denied (token expired) | Return error | `{ isError: true, content: [...] }` |
| Dependency unavailable (API down) | Return error | `isError: true` + helpful message |
| Unhandled exception in callback | SDK catches it and converts to `{ isError: true, content: [{ type: "text", text: error.message }] }` — no logging, no crash, no propagation to the process | A `db.query()` call throws |
| Tool name not found / tool disabled | Raw JSON-RPC error response (`InvalidParams`), not a tool-domain `isError` result — this check runs *before* the try/catch | Client calls an unregistered or disabled tool name |

## Example: graceful degradation

```typescript
server.tool(
  {
    name: "get-user",
    inputSchema: z.object({ id: z.string() }),
    outputSchema: z.object({ id: z.string(), name: z.string() }),
  },
  async ({ id }, ctx) => {
    try {
      const user = await db.users.get(id);
      if (!user) {
        return {
          isError: true,
          content: [{ type: "text", text: `User not found: ${id}` }],
        };
      }
      return {
        content: [{ type: "text", text: `Found user: ${user.name}` }],
        structuredContent: { id: user.id, name: user.name },
      };
    } catch (err) {
      return {
        isError: true,
        content: [{
          type: "text",
          text: `Database error: ${err instanceof Error ? err.message : "unknown"}`,
        }],
      };
    }
  }
);
```

**Pattern:** Catch, log (if needed), return error envelope.

## Error in structured context

Keep error results plain text and omit `structuredContent`. The SDK's output-schema check (`validateToolOutput`) skips validation entirely when `isError: true`, so a stray `structuredContent` on an error result is not checked against `outputSchema` — but it is **not stripped** either; it still goes out on the wire and may confuse a client expecting the schema shape. Leave it off:

```typescript
// Avoid — structuredContent survives on the wire, unvalidated, and may not match outputSchema
return {
  isError: true,
  content: [{ type: "text", text: "..." }],
  structuredContent: { code: 404 },
};

// Prefer
return {
  isError: true,
  content: [{ type: "text", text: "Not found (error code 404)" }],
};
```

## Auth errors

With OAuth configured, unauthenticated HTTP requests are rejected before a tool callback runs, so `ctx.auth` is required inside the callback. Check the authenticated caller's scopes, permissions, or typed user fields:

```typescript
import { MCPServer } from "mcp-use";
import {
  oauthClerkProvider,
  type ClerkOAuthUser,
} from "mcp-use/oauth/clerk";
import { z } from "zod";

const authServer = new MCPServer<ClerkOAuthUser>({
  name: "admin-tools",
  version: "1.0.0",
  oauth: oauthClerkProvider({
    frontendApiUrl: "https://example.clerk.accounts.dev",
  }),
});

authServer.tool(
  { name: "admin-action", inputSchema: z.object({ id: z.string() }) },
  async ({ id }, ctx) => {
    if (!ctx.auth.permissions.includes("admin")) {
      return {
        isError: true,
        content: [{ type: "text", text: "Insufficient permissions (requires admin)" }],
      };
    }

    return {
      content: [{ type: "text", text: `Authorized admin action for ${id}` }],
    };
  }
);
```

Return a tool-domain error for insufficient authorization. Do not add an impossible `if (!ctx.auth)` branch to an OAuth-authenticated callback.
