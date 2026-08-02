# Permission Guards

*Read this when you need to restrict tool/resource access by scope, role, or organization.*

## Scope Guard Pattern

Check if the token includes required scopes:

```typescript
server.tool({
  name: "send-email",
  description: "Send email on behalf of user",
  inputSchema: z.object({ to: z.string(), subject: z.string() }),
  async (input, ctx) => {
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
});
```

## Role Guard Pattern

```typescript
server.tool({
  name: "delete-user",
  description: "Delete a user (admin only)",
  inputSchema: z.object({ userId: z.string() }),
  async (input, ctx) => {
    if (ctx.auth.user.organizationRole !== "admin") {
      return {
        isError: true,
        content: [{ type: "text", text: "admin role required" }],
      };
    }
    
    return { content: [{ type: "text", text: "User deleted" }] };
  },
});
```

## Custom Permission Logic

```typescript
async (input, ctx) => {
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

All endpoints require authentication when OAuth is configured; you never receive unauthenticated requests at handler code.
