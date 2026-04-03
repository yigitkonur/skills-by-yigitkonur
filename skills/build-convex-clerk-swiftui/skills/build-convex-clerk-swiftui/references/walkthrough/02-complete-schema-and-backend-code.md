# Complete Schema and Backend Code

## Use This When
- Building out the full TypeScript backend for a Convex + SwiftUI app.
- Need a complete, copy-pasteable backend with schema, auth wrappers, and CRUD functions.
- Reviewing how `userQuery`/`userMutation` wrappers work with ownership checks.

---

## Schema

```typescript
// convex/schema.ts
import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  channels: defineTable({
    name: v.string(),
    description: v.optional(v.string()),
    createdBy: v.string(),  // tokenIdentifier -- no separate users table needed
  }),

  channelMembers: defineTable({
    channelId: v.id("channels"),
    userId: v.string(),     // tokenIdentifier
  })
    .index("by_channel", ["channelId"])
    .index("by_user", ["userId"])
    .index("by_channel_user", ["channelId", "userId"]),

  messages: defineTable({
    channelId: v.id("channels"),
    userId: v.string(),     // tokenIdentifier
    body: v.string(),
    isEdited: v.optional(v.boolean()),
  })
    .index("by_channel", ["channelId"]),
});
```

**Note:** The official WorkoutTracker stores `tokenIdentifier` directly as `userId: v.string()` in domain tables. A separate `users` table is optional -- only needed if you store profile data beyond what Clerk provides.

---

## Auth-Gated Function Wrappers (convex-helpers)

```typescript
// convex/functions.ts
import { mutation, query, QueryCtx } from "./_generated/server";
import { customQuery, customCtx, customMutation } from "convex-helpers/server/customFunctions";

async function userCheck(ctx: QueryCtx) {
  const identity = await ctx.auth.getUserIdentity();
  if (identity === null) throw new Error("Unauthenticated");
  return { identity };
}

export const userQuery = customQuery(query, customCtx(async (ctx) => await userCheck(ctx)));
export const userMutation = customMutation(mutation, customCtx(async (ctx) => await userCheck(ctx)));
```

Install: `npm install convex-helpers@^0.1.0`

This is the primary auth pattern. Every authenticated function uses `userQuery` or `userMutation` instead of raw `query`/`mutation`. The wrapper:
- Centralizes the auth check so individual functions never forget it.
- Provides `ctx.identity` directly in the handler, avoiding repeated `getUserIdentity()` calls.
- Is the pattern used in the official `clerk-convex-swift` example app.

---

## Auth Config

```typescript
// convex/auth.config.ts
export default {
  providers: [{
    domain: "YOUR_CLERK_FRONTEND_API_URL",
    applicationID: "convex",
  }],
};
```

---

## Messages

```typescript
// convex/messages.ts
import { v } from "convex/values";
import { userMutation, userQuery } from "./functions";

export const list = userQuery({
  args: { channelId: v.id("channels") },
  handler: async (ctx, args) => {
    return await ctx.db.query("messages")
      .withIndex("by_channel", q => q.eq("channelId", args.channelId))
      .order("desc").take(50);
  },
});

export const send = userMutation({
  args: { channelId: v.id("channels"), body: v.string() },
  handler: async (ctx, args) => {
    if (args.body.trim().length === 0) throw new Error("Cannot be empty");
    if (args.body.length > 4000) throw new Error("Too long");

    // Verify membership
    const member = await ctx.db.query("channelMembers")
      .withIndex("by_channel_user", q =>
        q.eq("channelId", args.channelId)
         .eq("userId", ctx.identity.tokenIdentifier))
      .unique();
    if (!member) throw new Error("Not a member");

    return await ctx.db.insert("messages", {
      channelId: args.channelId,
      userId: ctx.identity.tokenIdentifier,
      body: args.body.trim(),
    });
  },
});

export const remove = userMutation({
  args: { messageId: v.id("messages") },
  handler: async (ctx, args) => {
    const message = await ctx.db.get(args.messageId);
    if (!message || message.userId !== ctx.identity.tokenIdentifier) {
      throw new Error("Not found or not authorized");
    }
    await ctx.db.delete(args.messageId);
  },
});
```

---

## Channels

```typescript
// convex/channels.ts
import { v } from "convex/values";
import { userMutation, userQuery } from "./functions";

export const list = userQuery({
  args: {},
  handler: async (ctx) => {
    const memberships = await ctx.db.query("channelMembers")
      .withIndex("by_user", q => q.eq("userId", ctx.identity.tokenIdentifier))
      .collect();
    return Promise.all(memberships.map(m => ctx.db.get(m.channelId)));
  },
});

export const create = userMutation({
  args: { name: v.string(), description: v.optional(v.string()) },
  handler: async (ctx, args) => {
    if (args.name.trim().length === 0) throw new Error("Name required");
    const channelId = await ctx.db.insert("channels", {
      name: args.name.trim(),
      description: args.description,
      createdBy: ctx.identity.tokenIdentifier,
    });
    // Creator auto-joins
    await ctx.db.insert("channelMembers", {
      channelId,
      userId: ctx.identity.tokenIdentifier,
    });
    return channelId;
  },
});
```

---

## Optional: Users Table

Only add a `users` table if you need to store profile data beyond what `ctx.auth.getUserIdentity()` provides:

```typescript
// Only if needed -- add to schema.ts:
users: defineTable({
    tokenIdentifier: v.string(),
    name: v.string(),
    email: v.optional(v.string()),
}).index("by_token", ["tokenIdentifier"])
```

```typescript
// convex/users.ts -- only if you have a users table
import { userMutation, userQuery } from "./functions";

export const createOrUpdate = userMutation({
  args: {},
  handler: async (ctx) => {
    const existing = await ctx.db.query("users")
      .withIndex("by_token", q => q.eq("tokenIdentifier", ctx.identity.tokenIdentifier))
      .unique();
    if (existing) {
      await ctx.db.patch(existing._id, {
        name: ctx.identity.name ?? existing.name,
      });
      return existing._id;
    }
    return await ctx.db.insert("users", {
      tokenIdentifier: ctx.identity.tokenIdentifier,
      name: ctx.identity.name ?? "Anonymous",
      email: ctx.identity.email,
    });
  },
});
```

## Avoid
- Using raw `query`/`mutation` for authenticated endpoints -- always use `userQuery`/`userMutation`.
- Creating a `helpers.ts` file with a standalone `requireUser()` function as the primary pattern -- use `convex/functions.ts` with `userQuery`/`userMutation` wrappers instead.
- Accepting `userId` from the client in mutation args -- always derive from `ctx.identity.tokenIdentifier`.
- Using `.filter()` instead of `.withIndex()` for ownership checks -- it scans the entire table.
- Storing user identity data that changes frequently (avatar URL, display name) in every domain document.

## Read Next
- [01-from-zero-to-realtime-chat-app.md](01-from-zero-to-realtime-chat-app.md)
- [03-complete-swift-models-and-viewmodels.md](03-complete-swift-models-and-viewmodels.md)
- [../backend/04-auth-rules-and-server-ownership.md](../backend/04-auth-rules-and-server-ownership.md)
