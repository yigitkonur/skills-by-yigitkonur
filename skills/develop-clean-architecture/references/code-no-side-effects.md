---
title: Separate Pure Computation from Side Effects
impact: MEDIUM
impactDescription: enables deterministic testing, prevents hidden state corruption
tags: code, purity, side-effects, cqs
---

## Separate Pure Computation from Side Effects

Functions should either compute and return a value OR perform a side effect — not both. Mixing computation with mutation creates hidden coupling. Keep domain logic pure; push side effects to injected ports dispatched from use cases.

**Tension with domain events:** Domain events ARE side effects — but intentional, explicit ones. The reconciliation: domain entities collect events internally (pure), and use cases dispatch them through an injected port AFTER persistence succeeds. This keeps the core pure while making side effects explicit and testable.

**Incorrect (computation mixed with side effects):**

```typescript
class ShoppingCart {
  private items: CartItem[] = [];
  private appliedPromo: string | null = null;

  // Looks like a query, but mutates state (violates CQS)
  getTotal(promoCode?: string): number {
    let total = 0;
    for (let i = 0; i < this.items.length; i++) {
      // Mutation hidden inside a "getter"
      this.items[i].computedPrice = this.items[i].unitPrice * this.items[i].quantity;
      total += this.items[i].computedPrice;
    }

    if (promoCode) {
      this.appliedPromo = promoCode; // Side effect! Modifies cart state
      total *= 0.9;
    }

    // Another hidden side effect — logging that looks harmless
    // but writes to external system
    analytics.track('cart_total_viewed', { total, items: this.items.length });

    return total;
  }

  // Mutates the input array — caller doesn't expect this
  sortItemsByPrice(items: CartItem[]): CartItem[] {
    items.sort((a, b) => a.unitPrice - b.unitPrice); // Mutates original!
    return items;
  }
}
```

**Correct (pure computation separated from effects):**

```typescript
// Pure computation — no side effects, deterministic, easily testable
function calculateCartTotal(
  items: readonly CartItem[],
  promoCode?: string,
): CartSummary {
  const lineItems = items.map((item) => ({
    ...item,
    lineTotal: item.unitPrice * item.quantity,
  }));

  const subtotal = lineItems.reduce((sum, item) => sum + item.lineTotal, 0);
  const discount = promoCode ? resolveDiscount(subtotal, promoCode) : 0;

  return {
    lineItems,
    subtotal,
    discount,
    total: subtotal - discount,
    appliedPromoCode: promoCode,
  };
}

function sortItemsByPrice(items: readonly CartItem[]): ReadonlyArray<CartItem> {
  return [...items].sort((a, b) => a.unitPrice - b.unitPrice); // New array, no mutation
}

// Side effects isolated in orchestration layer
class CartCheckoutService {
  async viewCartSummary(cartId: string, promoCode?: string): Promise<CartSummary> {
    const cart = await this.cartRepository.findById(cartId);

    // Query: pure computation, no side effects
    const summary = calculateCartTotal(cart.items, promoCode);

    // Command: explicit side effect, clearly separated
    if (promoCode) {
      await this.cartRepository.applyPromo(cartId, promoCode);
    }

    // Side effect: explicitly performed, not hidden in computation
    await this.analytics.track('cart_total_viewed', {
      total: summary.total,
      itemCount: cart.items.length,
    });

    return summary;
  }
}

// Immutable data structures enforce purity
interface CartItem {
  readonly productId: string;
  readonly unitPrice: number;
  readonly quantity: number;
}

interface CartSummary {
  readonly lineItems: ReadonlyArray<CartItem & { readonly lineTotal: number }>;
  readonly subtotal: number;
  readonly discount: number;
  readonly total: number;
  readonly appliedPromoCode?: string;
}
```

**When NOT to use this pattern:**
- Performance-critical code where in-place mutation avoids allocation pressure (e.g., game loops, buffer processing)
- Builder/fluent APIs where chaining mutations is the established interface contract
- Framework lifecycle hooks (React `useEffect`, Express middleware) where side effects are the expected behavior

**Benefits:**
- Pure functions need no mocks — pass data in, assert data out
- Side effects are visible in the orchestration layer, not hidden in helpers
- `readonly` types catch accidental mutation at compile time, not at runtime

Reference: [Clean Code Chapter 3 + 14 — Side Effects and Successive Refinement](https://www.oreilly.com/library/view/clean-code-a/9780136083238/)
