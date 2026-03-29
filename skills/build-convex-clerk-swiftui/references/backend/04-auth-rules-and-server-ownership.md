# Auth Rules And Server Ownership

## Use This When
- Designing authenticated Convex functions.
- Reviewing authorization boundaries between Swift and TypeScript.
- Choosing ownership keys and user-record patterns.

## Backend Auth Configuration

```typescript
// convex/auth.config.ts
export default {
  providers: [{
    domain: process.env.CLERK_JWT_ISSUER_DOMAIN!,   // Set in Convex Dashboard → Settings → Environment Variables
    applicationID: "convex",
  }],
};
```

Run `npx convex dev` after creating or updating this file.

## Default Ownership Model
- Configure external OIDC in `convex/auth.config.ts`.
- Derive user identity on the server with `ctx.auth.getUserIdentity()`.
- Use `tokenIdentifier` as the canonical ownership key.
- Choose the ownership shape deliberately:
  - Minimal per-user apps may store `tokenIdentifier` directly on domain documents and indexes.
  - Richer apps may create an app-level `users` record keyed by `tokenIdentifier` and reference that record from domain data.

## Official Example: Minimal Ownership Shape
- The official `WorkoutTracker` example does **not** create a `users` table.
- It stores `ctx.identity.tokenIdentifier` directly into a `userId` string field on `workouts`.
- It indexes `userId` together with `date` using `userId_date`.
- This is the correct default when the product only needs per-user scoping, not richer user-domain modeling.

## When To Add A `users` Table
- Add one when the app needs editable profile data, preferences, avatars, roles, team membership, or joins across multiple feature areas.
- Keep `tokenIdentifier` as the lookup key even when you add a richer user record.
- Do not force a `users` table into small apps just because authentication exists.

## User-Guarded Functions (Official Pattern)

The official Clerk + Convex example uses `convex-helpers` to create `userQuery` and `userMutation` wrappers that enforce authentication at the function boundary:

```typescript
// convex/functions.ts
import { mutation, query, QueryCtx } from "./_generated/server";
import {
  customQuery, customCtx, customMutation,
} from "convex-helpers/server/customFunctions";

async function userCheck(ctx: QueryCtx) {
  const identity = await ctx.auth.getUserIdentity();
  if (identity === null) {
    throw new Error("Unauthenticated call to create");
  }
  return { identity };
}

export const userQuery = customQuery(
  query,
  customCtx(async (ctx) => await userCheck(ctx))
);

export const userMutation = customMutation(
  mutation,
  customCtx(async (ctx) => await userCheck(ctx))
);
```

Then use `userQuery`/`userMutation` instead of raw `query`/`mutation` for all authenticated functions:

```typescript
// convex/workouts.ts
import { v } from "convex/values";
import { userMutation, userQuery } from "./functions";

export const store = userMutation({
  args: {
    date: v.string(),
    duration: v.optional(v.int64()),
    activity: v.union(
      v.literal("Running"),
      v.literal("Lifting"),
      v.literal("Walking"),
      v.literal("Swimming")
    ),
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("workouts", {
      userId: ctx.identity.tokenIdentifier,
      date: args.date,
      duration: args.duration,
      activity: args.activity,
    });
  },
});

export const getInRange = userQuery({
  args: { startDate: v.string(), endDate: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db.query("workouts")
      .withIndex("userId_date", (q) =>
        q.eq("userId", ctx.identity.tokenIdentifier)
          .gte("date", args.startDate)
          .lte("date", args.endDate)
      ).collect();
  },
});
```

This pattern:
- Centralizes the auth check so individual functions never forget it.
- Provides `ctx.identity` directly in the handler, avoiding repeated `getUserIdentity()` calls.
- Is used in the official `clerk-convex-swift` example app (`convex-helpers` v0.1.x+).
- Pairs naturally with both ownership models: direct `tokenIdentifier` storage or a richer app-level `users` table.
- Shows that the closed set of `Activity` values is enforced in the mutation args validator even though the table schema itself stores `activity` as a string field.

## Ownership-Checked Mutations

When a mutation modifies a user-owned document, verify ownership before writing:

```typescript
export const remove = userMutation({
  args: { workoutId: v.id("workouts") },
  handler: async (ctx, args) => {
    const workout = await ctx.db.get(args.workoutId);
    if (workout === null || workout.userId !== ctx.identity.tokenIdentifier) {
      throw new Error("Workout not found");
    }
    await ctx.db.delete(args.workoutId);
    return args.workoutId;
  },
});
```

## Authorization Rule
- Never accept a client-passed `userId` for authorization.
- Derive the caller on the server, then resolve product ownership or membership there.
- Write authorization in TypeScript guard logic, not in Swift and not in a separate rules DSL.

## Swift Boundary Rule
- Swift may pass resource IDs or requested actions.
- Swift must not decide access scope, membership, or ownership.
- Authenticated views still need backend checks because a valid session does not imply authorization for every document.

## Provider Reality For Swift Teams
- There is no built-in Convex native-mobile auth stack in the Swift SDK.
- Clerk is the current first-party path, with the official `ClerkConvex` package binding Clerk session sync into `ConvexClientWithAuth` via `bind(client:)`.
- Firebase is possible through a custom `AuthProvider`, but you own the integration details.
- Sign in with Apple is viable through `AuthView()` from `ClerkKitUI`, which handles SIWA natively when enabled in the Clerk dashboard.

## Schema With Ownership Index

```typescript
// convex/schema.ts
import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  workouts: defineTable({
    activity: v.string(),
    date: v.string(),
    duration: v.optional(v.int64()),
    userId: v.string(),
  }).index("userId_date", ["userId", "date"]),
});
```

The `userId` field stores `ctx.identity.tokenIdentifier` and is indexed for efficient per-user queries.
This schema mirrors the official example's minimal ownership model; it is not proof that every app should skip a `users` table.

## Background And Scheduled Work
- Scheduled functions do not inherit auth context.
- If user-specific background work is needed, persist the necessary identity or ownership references explicitly.
- Background tasks must still validate ownership when they write or reveal user data.

## Avoid
- `subject` as the only identity key across providers.
- Client-side filtering as a substitute for server-side authorization.
- Public scheduled or internal helper functions.
- Treating auth success as product-level authorization success.
- Raw `query`/`mutation` for authenticated endpoints — use `userQuery`/`userMutation` wrappers.
- Assuming the official example's missing `users` table means richer products should never create one.

## Read Next
- [../authentication/01-clerk-first-setup.md](../authentication/01-clerk-first-setup.md)
- [../authentication/02-custom-auth-provider-and-firebase-fallback.md](../authentication/02-custom-auth-provider-and-firebase-fallback.md)
- [../swiftui/04-environment-injection-and-root-architecture.md](../swiftui/04-environment-injection-and-root-architecture.md)
