---
title: Use Branded Types to Prevent Primitive Obsession at Compile Time
impact: HIGH
impactDescription: eliminates entire class of argument-swap bugs at zero runtime cost
tags: ts, branded-types, domain, type-safety
---

## Use Branded Types to Prevent Primitive Obsession at Compile Time

Branded types create nominal typing from structural primitives using intersection types with unique symbols. They catch wrong-argument bugs at compile time with zero runtime overhead, complementing value objects for cases where full class wrappers are overkill.

**Incorrect (raw primitives allow silent mix-ups):**

```typescript
// domain/services/OrderService.ts
function assignOrderToUser(orderId: string, userId: string): void {
  // Both are just strings — nothing prevents swapping them
  console.log(`Assigning order ${orderId} to user ${userId}`)
}

function processRefund(userId: string, orderId: string, amount: number): void {
  // Parameter order differs from assignOrderToUser — easy to confuse
  console.log(`Refunding ${amount} for order ${orderId} to user ${userId}`)
}

// BUG: arguments are swapped, but TypeScript sees string === string ✅
const userId = 'usr_abc123'
const orderId = 'ord_xyz789'

assignOrderToUser(userId, orderId)  // Compiles fine — assigns user to order!
processRefund(orderId, userId, 100) // Compiles fine — refunds to an order ID!
```

**Correct (branded types catch swaps at compile time):**

```typescript
// domain/types/branded.ts
declare const __brand: unique symbol
type Brand<T, B> = T & { readonly [__brand]: B }

export type UserId = Brand<string, 'UserId'>
export type OrderId = Brand<string, 'OrderId'>
export type Email = Brand<string, 'Email'>

export function createUserId(value: string): UserId {
  if (!value.startsWith('usr_')) {
    throw new Error(`Invalid UserId format: ${value}`)
  }
  return value as UserId
}

export function createOrderId(value: string): OrderId {
  if (!value.startsWith('ord_')) {
    throw new Error(`Invalid OrderId format: ${value}`)
  }
  return value as OrderId
}

export function createEmail(value: string): Email {
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
    throw new Error(`Invalid email: ${value}`)
  }
  return value.toLowerCase() as Email
}

// domain/services/OrderService.ts
function assignOrderToUser(orderId: OrderId, userId: UserId): void {
  console.log(`Assigning order ${orderId} to user ${userId}`)
}

function processRefund(userId: UserId, orderId: OrderId, amount: number): void {
  console.log(`Refunding ${amount} for order ${orderId} to user ${userId}`)
}

const userId = createUserId('usr_abc123')
const orderId = createOrderId('ord_xyz789')

assignOrderToUser(orderId, userId)  // ✅ Correct order
assignOrderToUser(userId, orderId)  // ❌ Compile error: UserId not assignable to OrderId
processRefund(orderId, userId, 100) // ❌ Compile error: OrderId not assignable to UserId
```

**Alternative (unique symbol approach for value objects — zero runtime overhead):**

```typescript
const _emailBrand: unique symbol = Symbol('Email');
type Email = {
  readonly [_emailBrand]: typeof _emailBrand;
  readonly value: string;
};

type ValidEmail = { readonly type: 'ValidEmail'; readonly email: Email };
type InvalidEmail = { readonly type: 'InvalidEmail'; readonly reason: string };

function parseEmail(raw: string): ValidEmail | InvalidEmail {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(raw)) return { type: 'InvalidEmail', reason: `Invalid format: ${raw}` };
  const email: Email = { [_emailBrand]: _emailBrand, value: raw.toLowerCase() };
  return { type: 'ValidEmail', email };
}

// LSP narrows to exact type on each branch
const result = parseEmail('user@example.com');
if (result.type === 'ValidEmail') {
  result.email.value; // LSP: string
} else {
  result.reason;      // LSP: string — no .email available
}
```

Use the `unique symbol` approach when value objects need richer type narrowing with discriminated unions.

**When NOT to use this pattern:**
- Internal helper functions where parameters are unambiguous
- Temporary local variables within a single function scope
- When a full value object class is warranted (complex validation, methods, equality)
- Prototyping or throwaway scripts where type rigor slows iteration

**Benefits:**
- Entire class of argument-swap bugs eliminated at compile time
- Zero runtime overhead — brands are erased in emitted JavaScript
- Factory functions centralize validation at creation boundaries
- Composes naturally with existing string operations (branded strings are still strings)
- Gradual adoption — introduce one branded type at a time

Reference: [TypeScript Handbook — Type Branding](https://www.typescriptlang.org/docs/handbook/2/types-from-types.html) | [Khalil Stemmler — Functional Domain Modeling](https://khalilstemmler.com/articles/typescript-domain-driven-design/functional-error-handling/)
