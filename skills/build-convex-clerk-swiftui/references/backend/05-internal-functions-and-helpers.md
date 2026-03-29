# Internal Functions And Helpers

## Use This When
- Creating server-side logic that should not be callable from Swift.
- Building shared auth-gated function wrappers with `convex-helpers`.
- Deciding between `internal` and public function visibility.
- Calling one Convex function from another on the server.

## Auth-Gated Functions (Primary Pattern)

See [04-auth-rules-and-server-ownership.md](04-auth-rules-and-server-ownership.md) for the complete `userQuery`/`userMutation` pattern from the official WorkoutTracker, including the `convex/functions.ts` wrappers and usage examples.

Install: `npm install convex-helpers@^0.1.0`

`customCtx` from `convex-helpers` merges the object returned by `userCheck()` into the handler's `ctx`. This is why handlers can reference `ctx.identity.tokenIdentifier` directly -- it is injected at the TypeScript level by the wrapper, not a built-in Convex property.

This pattern guarantees `ctx.identity` at the TypeScript level so handlers never need null checks.

## Internal Functions

Internal functions are only callable from other Convex functions, never from Swift:

```typescript
import { internalMutation, internalQuery } from "./_generated/server";
import { v } from "convex/values";

export const getByToken = internalQuery({
  args: { tokenIdentifier: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db.query("users")
      .withIndex("by_token", q => q.eq("tokenIdentifier", args.tokenIdentifier))
      .unique();
  },
});

export const createIfNotExists = internalMutation({
  args: { tokenIdentifier: v.string(), name: v.string() },
  handler: async (ctx, args) => {
    const existing = await ctx.db.query("users")
      .withIndex("by_token", q => q.eq("tokenIdentifier", args.tokenIdentifier))
      .unique();
    if (existing) return existing._id;
    return await ctx.db.insert("users", { ...args });
  },
});
```

## Calling Internal Functions From Other Functions

```typescript
import { internal } from "./_generated/api";

export const send = mutation({
  handler: async (ctx, args) => {
    const user = await ctx.runQuery(internal.users.getByToken, {
      tokenIdentifier: identity.tokenIdentifier,
    });
  },
});
```

## Alternative: Plain Helper Function

A simpler but less type-safe approach. Requires manual null checks in every handler:

```typescript
// convex/helpers.ts
import { QueryCtx, MutationCtx } from "./_generated/server";

export async function requireUser(ctx: QueryCtx | MutationCtx) {
  const identity = await ctx.auth.getUserIdentity();
  if (!identity) throw new Error("Must be authenticated");

  const user = await ctx.db.query("users")
    .withIndex("by_token", q => q.eq("tokenIdentifier", identity.tokenIdentifier))
    .unique();
  if (!user) throw new Error("User not found");
  return user;
}
```

Use this only when the app needs a richer `users` table lookup in every handler. For simple ownership scoping, the `userQuery`/`userMutation` pattern is preferred.

## Decision Guide

```
Is this called directly by your Swift app?
├── YES → public: query / mutation / action
│         └── Needs auth? Use userQuery / userMutation from convex-helpers
└── NO  → internal: internalQuery / internalMutation / internalAction
```

Default to `internal`. Only expose what the client actually needs to call.

## Avoid
- Exposing internal functions as public when only the server calls them.
- Writing auth checks inline in every handler instead of using `userQuery`/`userMutation`.
- Forgetting argument validators on internal functions; they still need them.
- Using `helpers.ts` with `requireUser` when the simpler `functions.ts` + `userQuery`/`userMutation` pattern covers the need.

## Read Next
- [06-intent-plus-schedule-pattern.md](06-intent-plus-schedule-pattern.md)
- [04-auth-rules-and-server-ownership.md](04-auth-rules-and-server-ownership.md)
- [08-file-organization-and-naming.md](08-file-organization-and-naming.md)
