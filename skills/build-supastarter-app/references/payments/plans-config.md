# Plans Configuration

> Documents the billing plan map in `packages/payments/config.ts`. Consult this when changing prices, switching between user- and organization-level billing, or adding a new free / recurring / lifetime / enterprise plan.

## Key files

- `packages/payments/config.ts`

## Representative code

```ts
export const config = {
  billingAttachedTo: "user" as "user" | "organization",
  plans: {
    free: { isFree: true },
    pro: {
      recommended: true,
      prices: [
        { type: "recurring", productId: process.env.NEXT_PUBLIC_PRICE_ID_PRO_MONTHLY, interval: "month", amount: 29, currency: "USD", seatBased: true, trialPeriodDays: 7 },
        { type: "recurring", productId: process.env.NEXT_PUBLIC_PRICE_ID_PRO_YEARLY, interval: "year", amount: 290, currency: "USD", seatBased: true, trialPeriodDays: 7 },
      ],
    },
    lifetime: {
      prices: [{ type: "one-time", productId: process.env.NEXT_PUBLIC_PRICE_ID_LIFETIME, amount: 799, currency: "USD" }],
    },
    enterprise: { isEnterprise: true },
  },
} as const;
```

## Implementation notes

- `billingAttachedTo` decides whether purchases belong to users or organizations.
- `seatBased: true` matters for org billing and seat synchronization.
- Free and enterprise plans are config flags, not special hard-coded branches in the UI.

---

**Related references:**
- `references/payments/checkout-and-portal-flow.md` — How active plans are resolved from purchases
- `references/routing/access-guards.md` — `/choose-plan` gating based on plan setup
- `references/setup/config-feature-flags.md` — Cross-package billing configuration context
