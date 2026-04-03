# Webhook Flow

> Documents the provider webhook pipeline that creates, updates, and deletes purchase rows. Consult this when debugging payment state drift between Stripe and the application database.

> ⚠️ **Webhook secret.** The `STRIPE_WEBHOOK_SECRET` must match the webhook endpoint registered in Stripe Dashboard. Mismatches cause silent signature verification failures.

## Key file

- `packages/payments/provider/stripe/index.ts`

## Representative code

```ts
switch (event.type) {
  case "checkout.session.completed":
    await createPurchase({ type: "ONE_TIME", productId, customerId: customer as string });
    await setCustomerIdToEntity(customer as string, {
      organizationId: metadata?.organization_id,
      userId: metadata?.user_id,
    });
    break;
  case "customer.subscription.created":
    await createPurchase({
      subscriptionId: id,
      type: "SUBSCRIPTION",
      productId,
      status: event.data.object.status,
    });
    break;
  case "customer.subscription.updated":
    await updatePurchase({ id: existingPurchase.id, status: event.data.object.status });
    break;
  case "customer.subscription.deleted":
    await deletePurchaseBySubscriptionId(event.data.object.id);
    break;
}
```

## Flow summary

- verify Stripe signature
- branch by event type
- mutate `Purchase` rows
- persist provider customer IDs back onto users or organizations

This is the source of truth for subscription lifecycle updates after checkout completes.

---

**Related references:**
- `references/payments/stripe-provider.md` — Provider implementation that owns the webhook
- `references/payments/customer-ids.md` — Customer ID persistence used in webhook handlers
- `references/database/query-patterns.md` — Query helpers used by webhook mutations
