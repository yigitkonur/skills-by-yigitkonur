# Task: Integrate Payments

> Checklist for adding or extending billing behavior. Consult this when changing plans, checkout, customer IDs, or billing UI.

## Core files

- `packages/payments/config.ts` — plan definitions
- `packages/payments/types.ts` — provider contract
- `packages/payments/provider/index.ts` — active provider selection
- `packages/payments/provider/stripe/index.ts` — default provider implementation

## Practical checklist

1. Update plan metadata in `config.ts`
2. Make sure the provider implements the required contract in `types.ts`
3. Keep customer IDs attached to the correct entity (`user` or `organization`)
4. Expose checkout/portal flows through the API layer rather than direct client calls
5. Reflect billing state in settings or organization UI using existing components

---

**Related references:**
- `references/payments/plans-config.md` — Plan definitions and billing attachment rules
- `references/payments/customer-ids.md` — How customer IDs are stored
- `references/settings/billing-security-and-avatar.md` — Billing-related user settings entry points
