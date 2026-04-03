# Task: Integrate Payments

> Checklist for adding or extending billing behavior. Consult this when changing plans, checkout, customer IDs, or billing UI.

> ⚠️ **Steering:** Billing can attach to either the `user` or the `organization` entity. Check `packages/payments/config.ts` to see which mode is active before making changes — the wrong assumption will cause checkout flows to create customer IDs on the wrong entity.

## Core files

- `packages/payments/config.ts` — plan definitions and billing attachment mode
- `packages/payments/types.ts` — provider contract
- `packages/payments/provider/index.ts` — active provider selection
- `packages/payments/provider/stripe/index.ts` — default provider implementation

## Practical checklist

1. Update plan metadata in `config.ts`
2. Make sure the provider implements the required contract in `types.ts`
3. Keep customer IDs attached to the correct entity (`user` or `organization`) — check `config.ts`
4. Expose checkout/portal flows through the API layer rather than direct client calls
5. Reflect billing state in settings or organization UI using existing components
6. Test the full flow: plan selection → checkout → active subscription → portal access

## Billing guard interaction

Plan gating affects `/app` redirects through the guard chain in `apps/web/app/(saas)/app/layout.tsx`. When billing is enabled and there is no free plan:

1. Layout checks for active purchases via `orpcClient.payments.listPurchases(...)`
2. If no active plan exists, user is redirected to `/choose-plan`
3. After checkout completion, user is redirected back to `/app`

This means checkout work is never just a button change — it affects the redirect chain.

---

**Related references:**
- `references/payments/plans-config.md` — Plan definitions and billing attachment rules
- `references/payments/customer-ids.md` — How customer IDs are stored
- `references/payments/checkout-and-portal-flow.md` — Checkout and portal flow details
- `references/payments/webhook-flow.md` — Webhook handling for payment events
- `references/payments/stripe-provider.md` — Stripe provider implementation
- `references/settings/billing-security-and-avatar.md` — Billing-related user settings entry points
- `references/routing/access-guards.md` — How billing guards affect page access
