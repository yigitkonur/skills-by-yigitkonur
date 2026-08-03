# Permission Guards

*Read this when you need to restrict tool/resource access by scope, role, or organization.*

## Scope Guard Pattern

Check if the token includes required scopes:

```typescript
server.tool(
  {
    name: "send-email",
    description: "Send email on behalf of user",
    inputSchema: z.object({ to: z.string(), subject: z.string() }),
  },
  async (params, ctx) => {
    if (!ctx.auth.scopes.includes("mail.send")) {
      return {
        isError: true,
        content: [
          {
            type: "text",
            text: "This tool requires mail.send scope. Request access from your admin.",
          },
        ],
      };
    }

    return { content: [{ type: "text", text: "Email sent" }] };
  },
);
```

## Permission Guard Pattern

`ctx.auth.permissions` is provider-mapped application authorization, distinct from OAuth `scopes`:

```typescript
server.tool(
  {
    name: "delete_document",
    description: "Delete a document when the caller has permission.",
    inputSchema: z.object({ documentId: z.string() }),
  },
  async ({ documentId }, ctx) => {
    if (!ctx.auth.permissions.includes("documents:delete")) {
      return {
        isError: true,
        content: [{ type: "text", text: "Forbidden: documents:delete permission required" }],
      };
    }

    return { content: [{ type: "text", text: "Document deleted" }] };
  },
);
```

Provider mappings differ: Auth0 and WorkOS map their permission claim, Clerk maps organization permissions, Keycloak flattens resource roles as `client:role`, and Supabase maps AAL to `aal:<level>`. Check the specific provider's `providers/<name>.md` file for exactly what lands in `permissions`.

## Role Guard Pattern

```typescript
server.tool(
  {
    name: "delete-user",
    description: "Delete a user (admin only)",
    inputSchema: z.object({ userId: z.string() }),
  },
  async (params, ctx) => {
    if (ctx.auth.user.organizationRole !== "admin") {
      return {
        isError: true,
        content: [{ type: "text", text: "admin role required" }],
      };
    }

    return { content: [{ type: "text", text: "User deleted" }] };
  },
);
```

## Custom Permission Logic

```typescript
async (params, ctx) => {
  const isAdmin = ctx.auth.user.roles?.includes("admin") ?? false;
  const hasScope = ctx.auth.scopes.includes("write");

  if (!isAdmin || !hasScope) {
    return { isError: true, content: [{ type: "text", text: "Access denied" }] };
  }

  // Proceed
}
```

## Organization Guard (Clerk)

```typescript
if (!ctx.auth.user.organizationId) {
  return {
    isError: true,
    content: [{ type: "text", text: "You are not a member of an organization" }],
  };
}
```

Tool, resource, and prompt handlers reached through the protected MCP `basePath` receive only authenticated requests when OAuth is configured. OAuth discovery endpoints, assets, and custom routes remain public unless you add separate middleware for them.
