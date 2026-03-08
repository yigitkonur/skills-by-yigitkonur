# Provider Abstraction

> Explains how the payments package hides provider-specific logic behind a common interface. Consult this when switching from Stripe to another provider or when adding provider-specific logic without leaking it into API routes or UI code.

## Key files

- `packages/payments/types.ts`
- `packages/payments/provider/index.ts`
- `packages/payments/index.ts`

## Representative code

```ts
export type PaymentProvider = {
  createCheckoutLink: CreateCheckoutLink;
  createCustomerPortalLink: CreateCustomerPortalLink;
  webhookHandler: WebhookHandler;
};

// packages/payments/provider/index.ts
export * from "./stripe";
```

## Implementation notes

- API procedures call package-level exports such as `createCheckoutLink` rather than importing Stripe directly.
- Switching providers is mostly an export change in `packages/payments/provider/index.ts` plus env/config updates.
- Provider interfaces cover checkout, portal, webhooks, and subscription seat operations.

---

**Related references:**
- `references/payments/stripe-provider.md` — Concrete Stripe implementation
- `references/payments/stripe-provider.md` — How the API and UI use the abstraction
- `references/api/payments-organizations-modules.md` — Protected API procedures layered over the provider
