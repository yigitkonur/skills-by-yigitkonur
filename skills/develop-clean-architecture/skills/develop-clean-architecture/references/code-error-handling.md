---
title: Use Result Types and Custom Error Hierarchies Not Null Returns
impact: HIGH
impactDescription: eliminates null-check bugs, enables exhaustive error handling at compile time
tags: code, errors, result-type, null-safety, two-error-types
---

## Use Result Types and Custom Error Hierarchies Not Null Returns

Returning `null` or `-1` to signal errors is invisible to the type system. Use the two-error-type model: EXPECTED errors (domain errors) are typed and returned in Result; UNEXPECTED errors (defects) are thrown and caught by catch-all middleware. In this repo the Result branch uses `ok: true | false`, while rich error variants use `_tag` for pattern matching and `never` exhaustion.

**Incorrect (null returns hide error paths):**

```typescript
async function findUserByEmail(email: string): Promise<User | null> {
  const row = await db.query('SELECT * FROM users WHERE email = $1', [email]);
  if (!row) return null;
  return mapRowToUser(row);
}

async function resetPassword(email: string): Promise<string | null> {
  const user = await findUserByEmail(email);
  if (!user) return null;  // Null propagation — what went wrong?
  const token = await tokenService.generate(user.id);
  if (!token) return null;  // Different failure, same null signal
  return token;
}

const token = await resetPassword(email);
await redirectToReset(token.slice(0, 8));  // Bug: crashes if null
```

**Correct (two-error-type model with _tag pattern matching):**

```typescript
// Expected error classes with _tag for pattern matching
class InsufficientFundsError {
  readonly _tag = 'InsufficientFundsError' as const;
  constructor(readonly shortfall: Money) {}
}

class ProductNotFoundError {
  readonly _tag = 'ProductNotFoundError' as const;
  constructor(readonly productId: ProductId) {}
}

class CouponExpiredError {
  readonly _tag = 'CouponExpiredError' as const;
  constructor(readonly expiredAt: Date) {}
}

type PlaceOrderError = InsufficientFundsError | ProductNotFoundError | CouponExpiredError;

// Result type
type Result<T, E = Error> =
  | { readonly ok: true; readonly value: T }
  | { readonly ok: false; readonly error: E };

// Use case returns Result with typed error union
async function placeOrder(cmd: PlaceOrderCommand): Promise<Result<OrderId, PlaceOrderError>> {
  // ... business logic
}

// Controller: exhaustive handling with never check
const result = await placeOrder(cmd);
if (result.ok) {
  res.status(201).json({ orderId: result.value });
  return;
}

// Every possible error is visible — no hidden throws
switch (result.error._tag) {
  case 'InsufficientFundsError':
    res.status(402).json({ error: 'Payment failed', shortfall: result.error.shortfall });
    break;
  case 'ProductNotFoundError':
    res.status(404).json({ error: 'Product not found', id: result.error.productId });
    break;
  case 'CouponExpiredError':
    res.status(422).json({ error: 'Coupon expired', since: result.error.expiredAt });
    break;
  default:
    // LSP redlines this if a new error type is added and not handled
    const _exhaustive: never = result.error;
}
```

**The two-error-type summary:**

| Error Type | Mechanism | Caught Where | Example |
|---|---|---|---|
| Expected (domain) | `Result<T, E>` return | Caller handles via switch | `InsufficientFundsError` |
| Unexpected (defect) | `throw` | Catch-all middleware | Out of memory, assertion failure |

**When NOT to use this pattern:**
- Simple lookups where `undefined` is idiomatic (`Map.get()`, `Array.find()`)
- Infrastructure adapters wrapping SDKs that throw — catch at boundary, return Result
- When the team has adopted `neverthrow` or `effect-ts` — use their API

**Benefits:**
- The `never` exhaustion check is an architecture enforcer — new error variants immediately flag all unhandled switch statements at compile time
- No try/catch pyramids — Results compose with map/flatMap
- Expected vs. unexpected errors have different handling strategies by design
- Stack traces preserved through the error hierarchy

Reference: [Clean Code Chapter 7 — Error Handling](https://www.oreilly.com/library/view/clean-code-a/9780136083238/) | [Effect TS — Two Error Types](https://effect.website/)
