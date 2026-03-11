# Checkout and Portal Flow

> Documents the end-to-end billing flow from pricing-table selection to provider checkout, then back into the customer portal and purchase-derived UI state. Consult this when changing checkout redirects, billing CTA behavior, or how active purchases affect the product experience.

> ⚠️ **`billingAttachedTo` setting.** This config value determines whether checkout is tied to the User or Organization model. It affects which ID is passed as the customer reference.

## Key files

- `apps/web/modules/saas/payments/components/PricingTable.tsx`
- `apps/web/modules/saas/settings/components/CustomerPortalButton.tsx`
- `packages/api/modules/payments/procedures/create-checkout-link.ts`
- `packages/api/modules/payments/procedures/create-customer-portal-link.ts`
- `packages/payments/lib/helper.ts`

## Checkout flow

`PricingTable` is the main client entry point for plan selection. Authenticated users trigger `orpc.payments.createCheckoutLink`, while anonymous visitors are sent to signup first.

```tsx
const { checkoutLink } = await createCheckoutLinkMutation.mutateAsync({
  type: price.type === "one-time" ? "one-time" : "subscription",
  productId: price.productId,
  organizationId,
  redirectUrl: window.location.href,
});

window.location.href = checkoutLink;
```

Important details:

- checkout is always created through the API layer, not by calling the provider package from the client
- `redirectUrl` usually comes from `window.location.href`, so the user returns to the surface they started from
- organization billing passes `organizationId`, which lets the API compute seat counts and the right customer record

## Customer portal flow

`CustomerPortalButton` is the main settings-side entry point for existing subscriptions. It calls `payments.createCustomerPortalLink` and redirects the browser to the provider-hosted portal.

```tsx
const { customerPortalLink } =
  await createCustomerPortalMutation.mutateAsync({
    purchaseId,
    redirectUrl: window.location.href,
  });

window.location.href = customerPortalLink;
```

That keeps billing management outside the app while preserving a clean return path to the current settings or billing page.

## API responsibilities

The payments API layer owns the security and provider orchestration work:

- `create-checkout-link` validates the requested product, resolves the customer ID, optionally loads the organization, and computes seats for seat-based pricing
- `create-customer-portal-link` verifies the purchase belongs to the current user or accessible organization before delegating to `@repo/payments`
- `list-purchases` returns the purchase list used by guarded routes and billing UI

This keeps pricing components thin and prevents client code from guessing at provider-specific rules.

## Purchase-derived state after checkout

`createPurchasesHelper()` in `packages/payments/lib/helper.ts` turns raw purchase rows into app-level answers such as `activePlan`, `hasSubscription`, and `hasPurchase`. That helper is what route guards and billing UI rely on after checkout completes.

In practice the sequence is:

1. user selects a plan in `PricingTable`
2. the API creates a provider checkout URL
3. the provider completes the payment or subscription change
4. webhook processing persists updated purchase rows
5. UI and guard logic re-read purchases through `createPurchasesHelper()`

## Practical notes

- one-time and recurring products share the same client entry pattern; the procedure distinguishes them with the `type` field
- enterprise plans are handled outside this flow and usually route users to sales/contact instead of checkout
- customer portal access is purchase-specific, so settings UI needs a concrete purchase ID
- when billing is attached to organizations, checkout and portal flows must respect organization ownership and membership checks

---

**Related references:**
- `references/payments/plans-config.md` — plan metadata that drives price selection
- `references/payments/customer-ids.md` — how user/org billing identities are stored
- `references/payments/stripe-provider.md` — provider-side checkout and portal implementation
- `references/payments/webhook-flow.md` — how completed billing events update purchases
- `references/routing/access-guards.md` — how active purchases gate `/app` access
