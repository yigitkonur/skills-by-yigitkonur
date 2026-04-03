# Function Decision Tree

## Use This When
- Deciding whether a backend function should be a query, mutation, or action.
- Choosing between public and internal visibility.
- Need a quick reference for function type capabilities and limits.

## Text-Based Decision Tree

```
START: What does this function need to do?
|
|-- Read data that the UI displays?
|  |
|  |-- YES -> Use QUERY
|  |  |
|  |  |-- Called by client (Swift app)?
|  |  |  +-- YES -> export const myFn = query({...})
|  |  |
|  |  +-- Called only by other server functions?
|  |     +-- YES -> export const myFn = internalQuery({...})
|  |
|  +-- NO (continue)
|
|-- Write to the database?
|  |
|  |-- YES -> Use MUTATION
|  |  |
|  |  |-- Does it also need to call an external API?
|  |  |  +-- YES -> Mutation writes to DB, then schedules an action:
|  |  |          await ctx.scheduler.runAfter(0, internal.x.y, {})
|  |  |
|  |  |-- Called by client?
|  |  |  +-- YES -> export const myFn = mutation({...})
|  |  |
|  |  +-- Called only by server?
|  |     +-- YES -> export const myFn = internalMutation({...})
|  |
|  +-- NO (continue)
|
|-- Call an external API / do non-deterministic work?
|  |
|  |-- YES -> Use ACTION
|  |  |
|  |  |-- Also need to write to DB?
|  |  |  +-- YES -> Call ctx.runMutation() from within the action
|  |  |
|  |  |-- Called by client?
|  |  |  +-- YES -> export const myFn = action({...})
|  |  |
|  |  +-- Called only by server?
|  |     +-- YES -> export const myFn = internalAction({...})
|  |
|  +-- NO (continue)
|
+-- None of the above?
   +-- Re-evaluate. Every backend function is a query, mutation, or action.
```

## Quick Summary Table

```
+----------+-----------+----------+-----------+----------------------+
| Type     | Read DB   | Write DB | External  | Reactive             |
|          |           |          | APIs      | (subscribable)       |
+----------+-----------+----------+-----------+----------------------+
| query    | YES       | NO       | NO        | YES                  |
| mutation | YES       | YES      | NO        | NO (fire & forget)   |
| action   | via run*  | via run* | YES       | NO                   |
+----------+-----------+----------+-----------+----------------------+

* Actions access DB only through ctx.runQuery() / ctx.runMutation()
```

## Public vs Internal

```
+----------------------+---------------------------------------------+
| Visibility           | When to use                                 |
+----------------------+---------------------------------------------+
| Public               | Client (Swift app) calls it directly        |
| (query, mutation,    | Appears in generated API types              |
|  action)             | Validate all args -- user input is untrusted |
+----------------------+---------------------------------------------+
| Internal             | Only other server functions call it          |
| (internalQuery,      | Background jobs, scheduled functions        |
|  internalMutation,   | Helper functions called by actions          |
|  internalAction)     | Cannot be called from the client            |
+----------------------+---------------------------------------------+
```

## Common Patterns

### Pattern: Mutation + Scheduled Action

When you need to write to DB AND call an external API:

```typescript
// Step 1: Mutation writes to DB and schedules work
export const createPost = mutation({
  args: { title: v.string(), body: v.string() },
  handler: async (ctx, args) => {
    const postId = await ctx.db.insert("posts", {
      title: args.title,
      body: args.body,
      status: "processing",
    });
    // Step 2: Schedule the action (runs after mutation commits)
    await ctx.scheduler.runAfter(
      0,
      internal.posts.generateSummary,
      { postId }
    );
    return postId;
  },
});

// Step 3: Action calls external API and writes result via mutation
export const generateSummary = internalAction({
  args: { postId: v.id("posts") },
  handler: async (ctx, args) => {
    const post = await ctx.runQuery(internal.posts.getById, {
      id: args.postId,
    });
    const summary = await fetch("https://api.openai.com/...", {...});
    await ctx.runMutation(internal.posts.setSummary, {
      postId: args.postId,
      summary: await summary.text(),
    });
  },
});
```

### Pattern: Auth-Gated Query with userQuery

```typescript
// convex/functions.ts -- define once, use everywhere
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

```typescript
// convex/items.ts -- ctx.identity is directly available
import { userQuery } from "./functions";

export const myProtectedQuery = userQuery({
  args: {},
  handler: async (ctx) => {
    return await ctx.db
      .query("items")
      .withIndex("by_owner", q => q.eq("ownerId", ctx.identity.tokenIdentifier))
      .collect();
  },
});
```

## Limits Reference

```
+------------------------+-------------------------------------------+
| Limit                  | Value                                     |
+------------------------+-------------------------------------------+
| Query/mutation runtime | Varies by plan (see Convex docs)          |
| Action runtime         | Up to 10 minutes                          |
| Document size          | 1 MB                                      |
| Arguments size         | 8 MB                                      |
| Documents read/written | 8,192 per transaction                     |
| Scheduled functions    | 1,000 pending per deployment              |
| File storage           | Individual files up to 5 GB               |
| Concurrent connections | Varies by plan                            |
+------------------------+-------------------------------------------+
```

## Swift Client Mapping

```swift
// query  -> subscribe(to:with:yielding:) returns AnyPublisher (reactive)
// mutation -> mutation(_:with:) async throws -> T
// action  -> action(_:with:) async throws -> T
```

Every subscription must include `.receive(on: DispatchQueue.main)`.
Every `Decodable` model must include `CodingKeys` with `case id = "_id"`.

## Avoid
- Calling external APIs from mutations -- use actions or schedule them from a mutation.
- Using `Date.now()` or `Math.random()` in queries or mutations -- non-deterministic operations break caching.
- Making actions directly client-callable when they only serve as background work -- use `internalAction` and schedule from a mutation.
- Using a standalone `requireUser()` helper as the primary auth pattern -- use `userQuery`/`userMutation` wrappers from `convex-helpers` instead.
- Accessing `ctx.db` directly from actions -- use `ctx.runQuery()` / `ctx.runMutation()`.

## Read Next
- [01-convex-backend-quick-reference-card.md](01-convex-backend-quick-reference-card.md)
- [05-subscription-placement-decision-matrix.md](05-subscription-placement-decision-matrix.md)
- [../backend/03-queries-mutations-actions-scheduling.md](../backend/03-queries-mutations-actions-scheduling.md)
- [../backend/04-auth-rules-and-server-ownership.md](../backend/04-auth-rules-and-server-ownership.md)
