---
title: Model Domain States as Discriminated Unions for Exhaustive Checking
impact: HIGH
impactDescription: makes illegal states unrepresentable, compiler verifies all state transitions
tags: ts, discriminated-unions, state, exhaustive
---

## Model Domain States as Discriminated Unions for Exhaustive Checking

Discriminated unions with a literal discriminant property model domain state machines so each state carries only its relevant data. Combined with exhaustive `never` checks, the compiler guarantees every state is handled — adding a new state produces compile errors at every unhandled switch.

**Incorrect (string status with optional fields — unsafe access):**

```typescript
// domain/entities/Order.ts
interface Order {
  id: string
  status: 'draft' | 'confirmed' | 'shipped' | 'delivered' | 'cancelled'
  items: OrderItem[]
  confirmedAt?: Date          // Only exists when confirmed+
  trackingNumber?: string     // Only exists when shipped+
  deliveredAt?: Date          // Only exists when delivered
  cancellationReason?: string // Only exists when cancelled
}

function getShippingInfo(order: Order): string {
  if (order.status === 'shipped') {
    // trackingNumber MIGHT be undefined — TS cannot guarantee it
    return `Tracking: ${order.trackingNumber!.toUpperCase()}`  // Runtime crash if missing
  }
  return 'Not shipped'
}

function handleOrder(order: Order): void {
  switch (order.status) {
    case 'draft': /* ... */ break
    case 'confirmed': /* ... */ break
    case 'shipped': /* ... */ break
    // 'delivered' and 'cancelled' silently unhandled — no compiler warning
  }
}
```

**Correct (discriminated union with guaranteed data per state):**

```typescript
// domain/entities/Order.ts
interface OrderBase {
  id: string
  items: OrderItem[]
}

interface DraftOrder extends OrderBase {
  readonly kind: 'draft'
}

interface ConfirmedOrder extends OrderBase {
  readonly kind: 'confirmed'
  confirmedAt: Date
}

interface ShippedOrder extends OrderBase {
  readonly kind: 'shipped'
  confirmedAt: Date
  trackingNumber: string  // Guaranteed present for shipped orders
}

interface DeliveredOrder extends OrderBase {
  readonly kind: 'delivered'
  confirmedAt: Date
  trackingNumber: string
  deliveredAt: Date
}

interface CancelledOrder extends OrderBase {
  readonly kind: 'cancelled'
  cancelledAt: Date
  cancellationReason: string
}

type Order = DraftOrder | ConfirmedOrder | ShippedOrder | DeliveredOrder | CancelledOrder

function assertNever(x: never): never {
  throw new Error(`Unexpected state: ${JSON.stringify(x)}`)
}

function getShippingInfo(order: Order): string {
  switch (order.kind) {
    case 'shipped':
      return `Tracking: ${order.trackingNumber.toUpperCase()}`  // ✅ Guaranteed string
    case 'delivered':
      return `Delivered on ${order.deliveredAt.toISOString()}`  // ✅ Guaranteed Date
    case 'draft':
    case 'confirmed':
    case 'cancelled':
      return 'Not shipped'
    default:
      return assertNever(order)  // ❌ Compile error if a new state is added but unhandled
  }
}

// Type-safe state transitions
function confirmOrder(order: DraftOrder, now: Date): ConfirmedOrder {
  return { ...order, kind: 'confirmed', confirmedAt: now }
}

function shipOrder(order: ConfirmedOrder, trackingNumber: string): ShippedOrder {
  return { ...order, kind: 'shipped', trackingNumber }
}
```

**When NOT to use this pattern:**
- Simple boolean flags (active/inactive) where a union adds unnecessary ceremony
- Data models with many shared fields and few state-specific ones
- External API response types where you don't control the shape

**Benefits:**
- Illegal states are unrepresentable — no optional field guessing
- Adding a new state produces compile errors at every unhandled location
- State transitions are explicit functions with typed inputs and outputs
- IDE autocompletion shows only fields available for the current state
- Self-documenting code — the type definition IS the state machine spec

Reference: [TypeScript Handbook — Narrowing](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#discriminated-unions)
