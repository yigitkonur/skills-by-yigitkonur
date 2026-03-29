# Calling Actions Directly For Side Effects

## Use This When
- Designing a feature that calls an external API (email, payment, push notification) from Convex.
- Reviewing code that performs non-idempotent side effects inside an action.
- Debugging duplicate charges, duplicate emails, or missing database records after a failure.

## The Problem

Actions are **not transactional** and **not automatically retried**. If an action calls an external API and then writes to the database, a failure between those two steps leaves the side effect completed but unrecorded. A user retry sends the email or charges the card again.

| Failure Point | External API | DB Record | Outcome |
|---|---|---|---|
| Before API call | Not sent | Not recorded | Safe — retry works |
| After API call, before DB write | **Sent** | **Not recorded** | Dangerous — retry duplicates |
| After DB write | Sent | Recorded | Success |

## The Fix: Intent + Schedule Pattern

Record the **intent** in a transactional mutation, then schedule the action. The database record exists before any side effect runs.

```typescript
// Step 1: Mutation records intent + schedules action (ATOMIC)
export const sendEmail = mutation({
  args: { to: v.string(), subject: v.string(), body: v.string() },
  handler: async (ctx, args) => {
    const identity = await ctx.auth.getUserIdentity();
    if (!identity) throw new Error("Unauthenticated");

    const emailId = await ctx.db.insert("emails", {
      to: args.to, subject: args.subject, body: args.body,
      status: "pending",
      requestedBy: identity.tokenIdentifier,
      requestedAt: Date.now(),
    });

    // Atomic with the insert — if mutation fails, schedule is rolled back
    await ctx.scheduler.runAfter(0, internal.emails.actuallySend, { emailId });
    return emailId;
  },
});

// Step 2: Scheduled action performs the side effect
export const actuallySend = internalAction({
  args: { emailId: v.id("emails") },
  handler: async (ctx, args) => {
    const email = await ctx.runQuery(internal.emails.getEmail, { emailId: args.emailId });
    if (!email || email.status !== "pending") return;

    try {
      await sendgrid.send({ to: email.to, subject: email.subject, body: email.body });
      await ctx.runMutation(internal.emails.markSent, { emailId: args.emailId });
    } catch (error) {
      await ctx.runMutation(internal.emails.markFailed, {
        emailId: args.emailId, error: String(error),
      });
    }
  },
});
```

## Swift-Side: Call The Mutation, Not The Action

```swift
// Swift calls the mutation (which records intent + schedules action)
let emailId: String = try await client.mutation(
    "emails:sendEmail",
    with: ["to": to, "subject": subject, "body": body]
)
// Email status updates reactively via subscription
```

## When Direct Actions Are Acceptable

Direct action calls are fine when the operation is idempotent, has no external side effects, or is fire-and-forget:

```swift
// OK: Reading external data — no side effects, safe to retry
let weather: WeatherData = try await client.action(
    "weather:getCurrent", with: ["city": "San Francisco"]
)
```

## Avoid
- Calling non-idempotent external APIs directly inside actions without a preceding intent record.
- Assuming Convex retries actions on failure — it does not.
- Having Swift call `client.action(...)` directly for operations that modify external state.
- Skipping the `status` field on intent records — it is needed for idempotency checks.

## Read Next
- [../backend/03-queries-mutations-actions-scheduling.md](../backend/03-queries-mutations-actions-scheduling.md)
- [07-trusting-client-for-authorization.md](07-trusting-client-for-authorization.md)
- [../operations/01-verified-corrections-and-trust-boundaries.md](../operations/01-verified-corrections-and-trust-boundaries.md)
