# Convex Backend Quick Reference Card

## Use This When
- Need a fast lookup for Convex schema, query, mutation, action, or index syntax.
- Writing backend functions and need to check the API surface quickly.
- Reviewing code for common mistakes (missing indexes, unbounded queries, non-determinism).

## Schema Rules

```
defineSchema({                     Always wrap in defineSchema()
  tableName: defineTable({         One defineTable per table
    field: v.string(),             v.string() v.number() v.boolean()
    opt: v.optional(v.string()),   v.optional() for nullable
    ref: v.id("otherTable"),       v.id() for foreign keys
    union: v.union(                v.union() for enums
      v.literal("a"),
      v.literal("b")
    ),
    nested: v.object({...}),       v.object() for embedded docs
    list: v.array(v.string()),     v.array() for arrays
  })
  .index("by_X", ["fieldA"])            Single-field index
  .index("by_X_Y", ["fieldA","fieldB"]) Compound index
  .searchIndex("search_X", {            Full-text search
    searchField: "body",
    filterFields: ["channelId"]
  })
})
```

## Function Decision

```
Read data for UI?         -> query     (reactive, cached, no side-effects)
Write to database?        -> mutation  (transactional, deterministic)
Call external API?         -> action   (non-deterministic, use scheduler)
Only called by server?     -> internal (internalQuery/Mutation/Action)
Called by client?          -> public   (query/mutation/action)
```

## Auth-Gated Functions (Primary Pattern)

Use `userQuery`/`userMutation` from `convex-helpers` as the default for all authenticated functions:

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

Then use them:

```typescript
// convex/items.ts
import { v } from "convex/values";
import { userQuery, userMutation } from "./functions";

export const list = userQuery({
  args: {},
  handler: async (ctx) => {
    return await ctx.db.query("items")
      .withIndex("by_owner", q => q.eq("ownerId", ctx.identity.tokenIdentifier))
      .collect();
  },
});
```

**Alternative:** For one-off cases where the wrapper is not used, you can check auth inline:

```typescript
const identity = await ctx.auth.getUserIdentity();
if (!identity) throw new Error("Not authenticated");
```

But prefer `userQuery`/`userMutation` as the default -- it centralizes the check and provides `ctx.identity` directly.

## Query Rules

```typescript
export const myQuery = query({
  args: { fieldA: v.string() },           // Always validate args
  handler: async (ctx, args) => {
    // USE indexes -- never scan full table
    return await ctx.db
      .query("tableName")
      .withIndex("by_X", q => q.eq("fieldA", args.fieldA))
      .order("desc")                       // "asc" (default) or "desc"
      .take(50);                           // Limit results

    // NEVER do:
    // .filter(q => q.eq(...))  -- scans entire table
    // fetch()                  -- unbounded, use .collect() or .take()
    // Math.random()            -- non-deterministic, breaks caching
    // Date.now()               -- non-deterministic
  },
});
```

## Mutation Rules

```typescript
export const myMutation = mutation({
  args: { ... },
  handler: async (ctx, args) => {
    // Insert
    const id = await ctx.db.insert("table", { ...fields });

    // Update (patch = merge, replace = overwrite)
    await ctx.db.patch(docId, { field: "newValue" });
    await ctx.db.replace(docId, { ...allFields });

    // Delete
    await ctx.db.delete(docId);

    // Read within mutation -- same API as query
    const doc = await ctx.db.get(docId);

    // NEVER do:
    // fetch() to external APIs
    // Non-deterministic operations
    // Side effects beyond ctx.db writes
    // Sleep or setTimeout

    return id;  // Return value goes to client
  },
});
```

## Action Rules

```typescript
export const myAction = action({
  args: { ... },
  handler: async (ctx, args) => {
    // CAN call external APIs
    const resp = await fetch("https://api.example.com/...");

    // CAN call mutations/queries
    await ctx.runMutation(internal.module.myMutation, { ... });
    const data = await ctx.runQuery(internal.module.myQuery, { ... });

    // CANNOT access ctx.db directly
    // CANNOT be reactive (no subscriptions to actions)

    // Prefer: schedule from mutation instead of calling action directly
    // await ctx.scheduler.runAfter(0, internal.module.myAction, {...})
  },
});
```

## Index Patterns

```
Single field:     .index("by_status", ["status"])
Compound:         .index("by_channel_time", ["channelId", "createdAt"])
Equality + range: .withIndex("by_X", q => q.eq("a", v).gt("b", min))

Rules:
  - Equality fields FIRST, range field LAST
  - At most ONE range constraint per query
  - Index must be prefix-complete (no skipping fields)
```

## Common Patterns

```typescript
// Upsert
const existing = await ctx.db.query("t").withIndex(...).unique();
if (existing) { await ctx.db.patch(existing._id, {...}); }
else { await ctx.db.insert("t", {...}); }

// Paginated query (manual cursor)
.withIndex("by_time").order("desc").take(limit + 1)
// If result.length > limit -> more pages exist

// Resolve foreign key (no JOINs in Convex)
const author = await ctx.db.get(message.authorId);

// Schedule background work from mutation
await ctx.scheduler.runAfter(0, internal.jobs.processUpload, { fileId });
```

## Limits

```
Query/mutation execution:    max runtime varies by plan
Document size:               1 MB
Arguments size:              8 MB
Transactions:                8,192 documents read/written
Scheduled functions:         1,000 pending per deployment
```

## Avoid
- Using raw `query`/`mutation` for authenticated endpoints -- use `userQuery`/`userMutation` wrappers.
- Using `.filter()` for queries that should use `.withIndex()` -- `.filter()` scans the entire table.
- Calling external APIs from mutations -- use actions or schedule them.
- Using `Date.now()` or `Math.random()` in queries or mutations -- non-deterministic operations break caching and transactions.
- Unbounded `.collect()` without an index range -- always constrain the result set.

## Read Next
- [02-swift-sdk-api-cheat-sheet.md](02-swift-sdk-api-cheat-sheet.md)
- [03-sql-to-convex-mapping-table.md](03-sql-to-convex-mapping-table.md)
- [04-function-decision-tree.md](04-function-decision-tree.md)
- [../backend/03-queries-mutations-actions-scheduling.md](../backend/03-queries-mutations-actions-scheduling.md)
