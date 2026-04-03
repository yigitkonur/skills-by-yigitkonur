# Trusting The Client For Authorization

## Use This When
- Designing authenticated Convex functions that access user-scoped data.
- Reviewing backend code that accepts a `userId` argument.
- Setting up row-level security or team membership checks.

## The Rule

**Never accept `userId` as a function argument for authorization.** The client can send any value. Always derive the user identity server-side from `ctx.auth.getUserIdentity()`.

## The Vulnerability

```typescript
// BAD: Trusts client-provided userId
export const getMyTasks = query({
  args: { userId: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("tasks")
      .withIndex("by_user", (q) => q.eq("userId", args.userId))
      .collect();
    // Any client can pass any userId and read anyone's tasks
  },
});
```

## The Fix: Use userQuery/userMutation (Primary) or ctx.auth (Alternative)

**Primary — `userQuery`/`userMutation` from `convex-helpers`:**

```typescript
import { userQuery, userMutation } from "./functions";

export const getMyTasks = userQuery({
  args: {},
  handler: async (ctx) => {
    return await ctx.db
      .query("tasks")
      .withIndex("by_user", (q) =>
        q.eq("userId", ctx.identity.tokenIdentifier)
      )
      .take(100);
  },
});
```

**Alternative — manual `ctx.auth.getUserIdentity()` check:**

```typescript
export const getMyTasks = query({
  args: {},
  handler: async (ctx) => {
    const identity = await ctx.auth.getUserIdentity();
    if (!identity) throw new Error("Unauthenticated");

    return await ctx.db
      .query("tasks")
      .withIndex("by_user", (q) =>
        q.eq("userId", identity.tokenIdentifier)
      )
      .take(100);
  },
});
```

Use `tokenIdentifier` (includes issuer prefix) for database lookups, not `subject`.

## Ownership-Checked Mutations

Always verify ownership before modifying user-scoped documents:

```typescript
export const deleteTask = userMutation({
  args: { taskId: v.id("tasks") },
  handler: async (ctx, args) => {
    const task = await ctx.db.get(args.taskId);
    if (!task || task.userId !== ctx.identity.tokenIdentifier) {
      throw new Error("Not authorized");
    }
    await ctx.db.delete(args.taskId);
  },
});
```

## Swift-Side: No userId In Arguments

```swift
// GOOD: No userId needed — server derives it from auth token
try await client.mutation("tasks:deleteTask", with: ["taskId": taskId])

// GOOD: Query does not need userId either
client.subscribe(to: "tasks:getMyTasks", with: [:], yielding: [Task].self)
    .receive(on: DispatchQueue.main)
    .removeDuplicates()
    .asResult()
    .sink { [weak self] result in ... }
    .store(in: &cancellables)
```

## Exception: Public Data

Passing a `userId` argument is correct when viewing another user's **public** profile, but the server must enforce that only public fields are returned.

## Avoid
- Accepting `userId` or `ownerId` as function arguments for access control.
- Using `subject` instead of `tokenIdentifier` as the ownership key.
- Client-side filtering as a substitute for server-side authorization.
- Using raw `query`/`mutation` for authenticated endpoints — prefer `userQuery`/`userMutation` wrappers.

## Read Next
- [../backend/04-auth-rules-and-server-ownership.md](../backend/04-auth-rules-and-server-ownership.md)
- [../authentication/01-clerk-first-setup.md](../authentication/01-clerk-first-setup.md)
- [06-calling-actions-directly-for-side-effects.md](06-calling-actions-directly-for-side-effects.md)
