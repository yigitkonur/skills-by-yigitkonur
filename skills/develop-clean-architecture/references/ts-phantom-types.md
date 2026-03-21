---
title: Use Phantom Types to Enforce State Machine Transitions at Compile Time
impact: MEDIUM-HIGH
impactDescription: makes invalid state transitions unrepresentable — caught at compile time, not runtime
tags: ts, phantom-types, state-machine, type-safety
---

## Use Phantom Types to Enforce State Machine Transitions at Compile Time

Phantom type parameters encode entity state at the type level. Functions accept only entities in the correct state, making invalid transitions a compile error. This is an advanced pattern for domains with strict state machines.

**Incorrect (runtime state checks — invalid transitions discovered at runtime):**

```typescript
class Order {
  status: 'draft' | 'pending' | 'confirmed' | 'shipped';

  ship(trackingId: string): void {
    if (this.status !== 'confirmed') {
      throw new Error('Can only ship confirmed orders');  // Runtime discovery
    }
    this.status = 'shipped';
  }
}

// Bug discovered at runtime, not compile time
const draft = new Order();
draft.ship('TRACK123');  // Compiles fine, crashes at runtime
```

**Correct (phantom types enforce valid transitions at compile time):**

```typescript
declare const _state: unique symbol;
type Tagged<T, S> = T & { readonly [_state]: S };

type DraftOrder = Tagged<Order, 'Draft'>;
type PendingOrder = Tagged<Order, 'Pending'>;
type ConfirmedOrder = Tagged<Order, 'Confirmed'>;
type ShippedOrder = Tagged<Order, 'Shipped'>;

function submitOrder(order: DraftOrder): PendingOrder {
  // ... submit logic
  return order as unknown as PendingOrder;
}

function confirmOrder(order: PendingOrder): ConfirmedOrder {
  // ... confirmation logic
  return order as unknown as ConfirmedOrder;
}

function shipOrder(order: ConfirmedOrder): ShippedOrder {
  // ... shipping logic
  return order as unknown as ShippedOrder;
}

// Valid transition chain — LSP enforces order
const draft: DraftOrder = createDraftOrder(/*...*/);
const pending: PendingOrder = submitOrder(draft);
const confirmed: ConfirmedOrder = confirmOrder(pending);
const shipped: ShippedOrder = shipOrder(confirmed);

// Invalid transitions — compile error
// shipOrder(draft);    // Type 'DraftOrder' is not assignable to 'ConfirmedOrder'
// confirmOrder(draft); // Type 'DraftOrder' is not assignable to 'PendingOrder'
```

**When NOT to use this pattern:**
- Simple status fields with few transitions — runtime checks are sufficient
- When the team is not familiar with advanced TypeScript — adds cognitive overhead
- Prototyping where the state machine is still evolving rapidly

**Benefits:**
- Invalid state transitions are compile errors — not runtime exceptions
- Self-documenting: function signatures show exactly which state is required and produced
- Zero runtime cost — phantom types are erased in emitted JavaScript
- Composable with branded types for additional type safety

Reference: [TypeScript Handbook — Advanced Types](https://www.typescriptlang.org/docs/handbook/2/types-from-types.html)
