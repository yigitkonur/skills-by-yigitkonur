# Permission Guards

Enforce access control inside tool handlers. Never trust the client to filter calls.

## Where to guard

| Layer | When to use |
|---|---|
| Tool handler (top) | Default — fast to write, easy to audit per-tool |
| Wrapper helper | When 5+ tools share the same guard |
| Server-level middleware | Bearer-token presence is enforced by mcp-use; do not duplicate. Use middleware only for cross-cutting policy (rate limit, audit log). |

The bearer token itself is verified by mcp-use before your handler runs. By the time `ctx.auth` is populated, the token is valid. Your job is to check **what the user is allowed to do**.

## Permission check (Auth0 / RFC 9068)

```ts
import { error, text } from 'mcp-use/server'

server.tool(
  {
    name: 'delete-document',
    schema: z.object({ documentId: z.string() }),
  },
  async ({ documentId }, ctx) => {
    if (!ctx.auth.permissions.includes('delete:documents')) {
      return { content: [{ type: 'text', text: 'Forbidden: delete:documents required' }], isError: true }
    }
    await db.documents.delete({ id: documentId })
    return text('Deleted')
  }
)
```

## Role check (Keycloak realm role)

```ts
if (!ctx.auth.user.roles?.includes('admin')) {
  return { content: [{ type: 'text', text: 'Forbidden: admin role required' }], isError: true }
}
```

For Keycloak resource roles, check `ctx.auth.permissions` formatted as `client:role`:

```ts
if (!ctx.auth.permissions.includes('billing-api:write')) { /* deny */ }
```

## Scope check

```ts
if (!ctx.auth.scopes.includes('write:repos')) {
  return { content: [{ type: 'text', text: 'Forbidden: write:repos scope required' }], isError: true }
}
```

## Organization-scoped data (WorkOS multi-tenant)

```ts
const orgId = ctx.auth.user.organization_id as string | undefined
if (!orgId) {
  return { content: [{ type: 'text', text: 'No organization context' }], isError: true }
}
return await db.data.findMany({ where: { organizationId: orgId } })
```

## Reusable guard helper

When the same guard repeats:

```ts
function requirePermission(ctx: ToolContext, perm: string) {
  if (!ctx.auth.permissions.includes(perm)) {
    return error(`Forbidden: ${perm} required`)
  }
}

server.tool({ name: 'archive-document', schema: z.object({ id: z.string() }) },
  async ({ id }, ctx) => {
    const denied = requirePermission(ctx, 'archive:documents')
    if (denied) return denied
    await db.documents.archive({ id })
    return text('Archived')
  }
)
```

For broader error handling patterns, see `../24-production/04-error-strategy.md`.

## Returning 403-style errors

MCP does not have HTTP status codes for tool responses. Return:

```ts
return { content: [{ type: 'text', text: 'Forbidden: <reason>' }], isError: true }
```

Use `error()` from `mcp-use/server` for the same shape:

```ts
import { error } from 'mcp-use/server'
return error('Forbidden: delete:documents required')
```

## Anti-patterns

- **Don't** rely on `ctx.auth.user.email` matching a list — emails can change.
- **Don't** check permissions by scanning `ctx.auth.payload` directly when `ctx.auth.permissions` already exposes the normalized form.
- **Don't** silently `return text('')` on denial — always set `isError: true` so the client can surface the failure.
- **Don't** put guards in middleware that hides the policy from the tool definition. Co-locate guards with handlers for auditability.

## Cross-references

- `ctx.auth` shape: `03-ctx-auth-object.md`
- Auth0 permissions setup: `providers/01-auth0.md`
- Keycloak roles: `providers/04-keycloak.md`
- Error strategy: `../24-production/04-error-strategy.md`
