# Stripe Provider

> Documents the default Stripe implementation used by the starter. Consult this when changing webhook handling, checkout metadata, portal behavior, or seat updates.

> ⚠️ **Provider abstraction.** The payment provider interface is generic. Stripe-specific code lives under `packages/payments/provider/stripe/`. Other providers implement the same interface behind the same contract.

## Key files

- `packages/payments/provider/stripe/index.ts`

## Representative code

```ts
export const createCheckoutLink: CreateCheckoutLink = async (options) => {
  const stripeClient = getStripeClient();
  const metadata = {
    organization_id: options.organizationId || null,
    user_id: options.userId || null,
  };

  const response = await stripeClient.checkout.sessions.create({
    mode: options.type === "subscription" ? "subscription" : "payment",
    line_items: [{ quantity: options.seats ?? 1, price: options.productId }],
    metadata,
  });

  return response.url;
};
```

## Webhook events handled

- `checkout.session.completed`
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`

## Implementation notes

- Metadata carries `organization_id` and `user_id` so webhooks can attach purchases to the correct entity.
- One-time and subscription checkouts are handled differently, but both go through the same provider module.
- Seat updates and cancellation are provider-level operations invoked from auth or billing flows.

---

**Related references:**
- `references/payments/provider-abstraction.md` — Common interface Stripe implements
- `references/payments/customer-ids.md` — Persisting Stripe customer IDs on users/orgs
- `references/api/payments-organizations-modules.md` — Procedures that invoke the provider
