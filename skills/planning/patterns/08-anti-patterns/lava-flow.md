# Lava Flow

## Origin

Described in Brown et al., *AntiPatterns* (1998). Named for the geological analogy: molten lava hardens into rock that is difficult and dangerous to remove. Dead or questionable code solidifies in the codebase and becomes too risky to touch.

## Explanation

Lava Flow occurs when dead code, experimental fragments, or abandoned features remain in the codebase because:

1. **No one knows if it is still used** — "Maybe something calls this at runtime?"
2. **No one understands what it does** — the author left, documentation does not exist
3. **Removing it might break something** — no tests, no type safety, no confidence
4. **Feature flags that never get cleaned up** — the flag is removed from the UI but the code paths remain

Over time, lava flow code accumulates, increasing maintenance burden, confusing new developers, and hiding actual bugs behind layers of dead code.

## TypeScript Code Examples

### Bad: Lava Flow Accumulation

```typescript
// payment-processor.ts — archaeological layers of dead code

// v1: Original Stripe integration (2019) — "DO NOT DELETE, might still be used by X"
export async function processPaymentV1(amount: number): Promise<void> {
  // Old Stripe charges API — deprecated but nobody removed it
  // const charge = await stripe.charges.create({ amount, currency: 'usd' });
  // Commented out but left "just in case"
  throw new Error("Deprecated — use v2");
}

// v2: PaymentIntents migration (2021) — "Replaced by v3 but keep for rollback"
export async function processPaymentV2(amount: number): Promise<void> {
  // This function is called by nothing. But removing it feels risky.
  const intent = await stripe.paymentIntents.create({
    amount,
    currency: "usd",
    // Old configuration that no longer matches our Stripe account setup
    payment_method_types: ["card"],
  });
  return intent;
}

// v3: Current implementation (2023)
export async function processPayment(amount: number): Promise<PaymentResult> {
  const intent = await stripe.paymentIntents.create({
    amount,
    currency: "usd",
    automatic_payment_methods: { enabled: true },
  });
  return { intentId: intent.id, status: intent.status };
}

// Experimental multi-currency support (2022) — developer left the company
// Nobody knows if this was finished or if anything uses it
export async function processPaymentMultiCurrency(
  amount: number,
  currency: string,
  exchangeRate?: number,
): Promise<unknown> {
  // Half-implemented, no tests, no types, no documentation
  if (exchangeRate) {
    amount = amount * exchangeRate; // Is this right? Nobody knows.
  }
  // More code that references services that no longer exist...
}

// Feature flag code that was never cleaned up
const USE_NEW_CHECKOUT = process.env.USE_NEW_CHECKOUT === "true";
// This flag was set to true in all environments 18 months ago.
// Both code paths still exist. The "old" path has diverged and is untested.
```

### Good: Clean Codebase with Dead Code Removed

```typescript
// payment-processor.ts — only the current, tested implementation

import Stripe from "stripe";

interface PaymentResult {
  readonly intentId: string;
  readonly status: string;
}

const stripe = new Stripe(config.stripeSecretKey);

export async function processPayment(
  amount: number,
  currency: string = "usd"
): Promise<PaymentResult> {
  const intent = await stripe.paymentIntents.create({
    amount,
    currency,
    automatic_payment_methods: { enabled: true },
  });
  return { intentId: intent.id, status: intent.status };
}

// Old versions: deleted. They live in git history if ever needed.
// Feature flags: cleaned up within 2 weeks of full rollout.
// Experimental code: in a branch, not in main.
```

### Feature Flag Lifecycle (Preventing Lava Flow)

```typescript
// feature-flags.ts — with expiration tracking

interface FeatureFlag {
  readonly name: string;
  readonly enabled: boolean;
  readonly createdAt: Date;
  readonly expiresAt: Date;         // REQUIRED — forces cleanup
  readonly owner: string;            // Who is responsible for cleanup
  readonly cleanupTicket: string;    // Linked JIRA/Linear ticket
}

const flags: ReadonlyArray<FeatureFlag> = [
  {
    name: "new-checkout-flow",
    enabled: true,
    createdAt: new Date("2025-01-15"),
    expiresAt: new Date("2025-03-15"),  // 2 months to clean up
    owner: "checkout-team",
    cleanupTicket: "ENG-4521",
  },
];

// CI check: fail build if any flag is past its expiration date
export function checkExpiredFlags(): void {
  const now = new Date();
  const expired = flags.filter((f) => now > f.expiresAt);
  if (expired.length > 0) {
    const names = expired.map((f) => `${f.name} (owner: ${f.owner})`);
    throw new Error(
      `Expired feature flags must be cleaned up: ${names.join(", ")}`
    );
  }
}
```

## Detection and Prevention

| Signal | Indicates Lava Flow |
|---|---|
| `// TODO: remove after migration` from 2 years ago | Abandoned cleanup task |
| Functions with zero callers (dead code analysis) | Code that nothing uses |
| Commented-out code blocks | "Just in case" preservation |
| Multiple versions of the same function | Incomplete migration |
| Feature flags always set to the same value | Flag that was never cleaned up |
| `@deprecated` annotations with no removal date | Permanent "temporary" code |

## Alternatives and Countermeasures

- **Git as the safety net:** Delete dead code confidently. It lives in git history.
- **Dead code analysis tools:** TypeScript's `noUnusedLocals`, `ts-prune`, ESLint `no-unused-vars`.
- **Feature flag expiration:** Enforce cleanup deadlines for every flag.
- **Deprecation schedules:** Mark code deprecated with a removal date, not just a warning.
- **Regular codebase audits:** Quarterly review to identify and remove dead code.

## When NOT to Apply (When Keeping Old Code Is Justified)

- **Regulatory requirements:** Some industries require keeping historical code for audit purposes. Keep it in a separate archive, not in the active codebase.
- **Active rollback capability:** If a new system is in canary deployment, keeping the old code path for days or weeks is reasonable. Set a cleanup date.
- **Backward compatibility:** Public APIs must maintain old endpoints during deprecation periods. This is not lava flow — it is intentional support.

## Trade-offs

| Approach | Benefit | Cost |
|---|---|---|
| Delete aggressively | Clean codebase, clear ownership | Risk of removing something still used |
| Keep everything "just in case" | Zero risk of breaking deletions | Codebase grows, confusion increases |
| Feature flag expiration | Forces cleanup | Requires tooling and discipline |
| Quarterly dead code audits | Periodic cleanup | Time investment, may miss things |

## Real-World Consequences

- **Internet Explorer compatibility code:** For years, web codebases carried IE-specific hacks that no one dared remove. Even after IE was officially dead, the code lingered.
- **Android's `AsyncTask`:** Deprecated in API 30, but code using it persists in millions of apps and libraries. The lava hardened.
- **Enterprise Java codebases:** Layers of SOAP, REST v1, REST v2, and GraphQL endpoints, each "too risky to remove," each with different serialization formats.
- **Feature flag debt at Knight Capital (2012):** An old feature flag was accidentally reactivated, executing a dead trading algorithm that lost $440 million in 45 minutes.

## Further Reading

- Brown, W. et al. (1998). *AntiPatterns: Refactoring Software, Architectures, and Projects in Crisis*
- Fowler, M. (2018). *Refactoring* — "Dead Code" and "Speculative Generality" smells
- Hodgson, P. (2017). "Feature Toggles (aka Feature Flags)" — martinfowler.com
- Feathers, M. (2004). *Working Effectively with Legacy Code*
