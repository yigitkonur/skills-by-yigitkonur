# Intent Plus Schedule Pattern

## Use This When
- A mutation needs to trigger an external API call (Stripe, email, push notification).
- You need a reliable audit trail for multi-step operations.
- Building any flow where a database write and a side effect must stay coordinated.

## The Problem

If you call an action directly and it fails midway (e.g., Stripe charges but saving to DB fails), you have no record of what happened.

## The Solution

```
1. Swift calls: mutation (records intent + schedules action)
   → If mutation fails, schedule is cancelled. Nothing happened.

2. Action runs after mutation commits
   → Calls external API
   → Writes result via runMutation
   → If action fails, DB still shows "pending" — you can retry
```

## Complete Example: Payment Flow

### Server (TypeScript)

```typescript
// convex/payments.ts
import { mutation, internalAction, internalMutation } from "./_generated/server";
import { internal } from "./_generated/api";
import { v } from "convex/values";

// Step 1: Mutation records intent + schedules action
export const initiate = mutation({
  args: { itemId: v.id("items"), amount: v.number() },
  handler: async (ctx, args) => {
    const identity = await ctx.auth.getUserIdentity();
    if (!identity) throw new Error("Unauthenticated");

    const paymentId = await ctx.db.insert("payments", {
      itemId: args.itemId,
      amount: args.amount,
      userId: identity.tokenIdentifier,
      status: "pending",
    });

    // Atomic with mutation — if mutation rolls back, schedule cancelled
    await ctx.scheduler.runAfter(0, internal.payments.charge, {
      paymentId,
      amount: args.amount,
    });

    return paymentId;
  },
});

// Step 2: Action calls external API after mutation commits
export const charge = internalAction({
  args: { paymentId: v.id("payments"), amount: v.number() },
  handler: async (ctx, args) => {
    try {
      const response = await fetch("https://api.stripe.com/v1/charges", {
        method: "POST",
        headers: { "Authorization": `Bearer ${process.env.STRIPE_SECRET_KEY}` },
        body: new URLSearchParams({
          amount: String(args.amount),
          currency: "usd",
        }),
      });
      const result = await response.json();

      await ctx.runMutation(internal.payments.markPaid, {
        paymentId: args.paymentId,
        stripeChargeId: result.id,
      });
    } catch (error) {
      await ctx.runMutation(internal.payments.markFailed, {
        paymentId: args.paymentId,
        error: String(error),
      });
    }
  },
});

export const markPaid = internalMutation({
  args: { paymentId: v.id("payments"), stripeChargeId: v.string() },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.paymentId, {
      status: "paid",
      stripeChargeId: args.stripeChargeId,
    });
  },
});

export const markFailed = internalMutation({
  args: { paymentId: v.id("payments"), error: v.string() },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.paymentId, { status: "failed", error: args.error });
  },
});
```

### Client (Swift)

```swift
// Initiate payment
let paymentId: String = try await client.mutation("payments:initiate", with: [
    "itemId": itemId,
    "amount": 2999
])

// Subscribe to watch status (reactive — updates automatically)
client.subscribe(to: "payments:getStatus", with: ["paymentId": paymentId], yielding: Payment?.self)
    .receive(on: DispatchQueue.main)
    .assign(to: &$payment)
```

## Why This Pattern Matters

| What if... | Intent + Schedule | Direct Action Call |
|---|---|---|
| Action fails midway | DB shows "pending" — you can retry | No record of what happened |
| Mutation rolls back | Schedule cancelled — nothing happened | N/A |
| Need to audit | Full history in DB | Possible data loss |

## Scheduling Atomicity Rule

| Scheduled from | Atomic with caller? |
|---|---|
| **Mutation** | Yes — rolls back together |
| **Action** | No — fires even if action fails |

Always schedule from mutations, not actions.

## Avoid
- Calling external APIs directly from mutations (mutations cannot use `fetch`).
- Scheduling from actions and expecting rollback atomicity.
- Skipping the intent record and calling the action directly from Swift.
- Using `.assign(to:)` in production subscription pipelines without Result-wrapping (the pipeline dies on first error).

## Read Next
- [05-internal-functions-and-helpers.md](05-internal-functions-and-helpers.md)
- [07-structured-errors-convexerror.md](07-structured-errors-convexerror.md)
- [03-queries-mutations-actions-scheduling.md](03-queries-mutations-actions-scheduling.md)
- [../../client-sdk/04-pipeline-termination-and-recovery.md](../client-sdk/04-pipeline-termination-and-recovery.md)
