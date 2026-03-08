# Error Handling Philosophy

**One-line summary:** Error handling strategy shapes your entire architecture -- choose between exceptions, error codes, and Result types deliberately, then apply the choice consistently to keep the happy path readable and failure paths explicit.

---

## Origin

Error handling philosophy has evolved through several paradigms. C used return codes (1970s). C++ and Java introduced exceptions (1980s-90s). Tony Hoare called null references his "billion-dollar mistake" (2009 QCon talk). Scott Wlaschin formalized "Railway-Oriented Programming" for functional error handling (2014, F# for Fun and Profit). Rust's `Result<T, E>` type (2015) brought algebraic error handling to systems programming. Each approach reflects a different philosophy about who is responsible for handling failure and how failures should propagate.

---

## The Problem It Solves

Poor error handling produces three failure modes: (1) **Silent failures** where errors are swallowed and the system continues in a corrupt state. (2) **Panic-driven code** where every function is wrapped in try/catch blocks that obscure the happy path. (3) **Null propagation** where `null` leaks through layers until it causes a `TypeError` far from its origin, making debugging a forensic exercise. The root problem is not choosing an error strategy; it is not choosing one at all, letting each developer handle errors differently until the codebase is an inconsistent patchwork.

---

## The Principle Explained

**Exceptions** model errors as exceptional control flow. When something goes wrong, you throw, and the runtime unwinds the stack until it finds a handler. The strength is that the happy path is uncluttered -- you write the logic as if nothing can go wrong, and handle errors separately. The weakness is that exceptions are invisible in the type system (in most languages). A function signature does not tell you what it throws, so callers may not know they need to handle failures.

**Result types** make errors explicit in the return type. A function returns either a success value or an error value, and the caller must inspect the result before using it. This eliminates invisible failure paths: the type system forces you to acknowledge errors. Railway-Oriented Programming extends this with chaining -- you compose operations that might fail into a pipeline where the first failure short-circuits the rest, like a train switching to an error track.

**The "Don't Return Null" principle** (Martin, Hoare) argues that null is a non-value masquerading as a value. Returning null forces every caller to check for it, and forgetting a single check causes a crash. Better alternatives: return an empty collection, throw an exception, use an Option/Maybe type, or use the Null Object pattern. The goal is to make absence explicit rather than implicit.

---

## Code Examples

### BAD: Try/Catch Anti-patterns

```typescript
// Anti-pattern 1: swallowing errors silently
async function getUser(id: string): Promise<User | null> {
  try {
    return await db.query(`SELECT * FROM users WHERE id = $1`, [id]);
  } catch (e) {
    // Error swallowed. Was it a connection failure? Permission error?
    // Corrupt data? We will never know.
    return null;
  }
}

// Anti-pattern 2: catch-and-rethrow adding nothing
async function processOrder(order: Order): Promise<void> {
  try {
    await validateOrder(order);
    await chargePayment(order);
    await fulfillOrder(order);
  } catch (e) {
    throw e; // Pointless: just let it propagate naturally
  }
}

// Anti-pattern 3: returning null, forcing null checks everywhere
function findDiscount(code: string): Discount | null {
  const discount = discounts.get(code);
  return discount ?? null;
}

// Caller must remember to check -- and every caller of THAT caller, forever
const discount = findDiscount(code);
const amount = discount.percentage * total; // TypeError if null!
```

### GOOD: Result Type Pattern (Railway-Oriented Programming)

```typescript
// Define a discriminated union Result type
type Result<T, E = Error> =
  | { readonly ok: true; readonly value: T }
  | { readonly ok: false; readonly error: E };

// Constructors
function Ok<T>(value: T): Result<T, never> {
  return { ok: true, value };
}

function Err<E>(error: E): Result<never, E> {
  return { ok: false, error };
}

// Chainable operations (Railway-Oriented Programming)
function map<T, U, E>(result: Result<T, E>, fn: (value: T) => U): Result<U, E> {
  return result.ok ? Ok(fn(result.value)) : result;
}

function flatMap<T, U, E>(
  result: Result<T, E>,
  fn: (value: T) => Result<U, E>
): Result<U, E> {
  return result.ok ? fn(result.value) : result;
}

// Domain-specific error types -- not just strings
type OrderError =
  | { readonly kind: "VALIDATION_FAILED"; readonly field: string; readonly reason: string }
  | { readonly kind: "PAYMENT_DECLINED"; readonly code: string }
  | { readonly kind: "INSUFFICIENT_STOCK"; readonly productId: string; readonly available: number }
  | { readonly kind: "RATE_LIMITED"; readonly retryAfterMs: number };

// Each step returns a Result -- errors are explicit in the type
function validateOrder(order: Order): Result<ValidatedOrder, OrderError> {
  if (!order.items.length) {
    return Err({ kind: "VALIDATION_FAILED", field: "items", reason: "Order must have items" });
  }
  if (!order.shippingAddress) {
    return Err({ kind: "VALIDATION_FAILED", field: "shippingAddress", reason: "Address required" });
  }
  return Ok({ ...order, validated: true } as ValidatedOrder);
}

async function chargePayment(order: ValidatedOrder): Promise<Result<PaidOrder, OrderError>> {
  const result = await paymentGateway.charge(order.total, order.paymentMethod);
  if (!result.success) {
    return Err({ kind: "PAYMENT_DECLINED", code: result.declineCode });
  }
  return Ok({ ...order, paymentId: result.transactionId } as PaidOrder);
}

async function reserveStock(order: PaidOrder): Promise<Result<FulfilledOrder, OrderError>> {
  for (const item of order.items) {
    const available = await inventory.checkStock(item.productId);
    if (available < item.quantity) {
      return Err({
        kind: "INSUFFICIENT_STOCK",
        productId: item.productId,
        available,
      });
    }
  }
  await inventory.reserve(order.items);
  return Ok({ ...order, fulfilled: true } as FulfilledOrder);
}

// Pipeline: chain operations, first failure short-circuits
async function processOrder(order: Order): Promise<Result<FulfilledOrder, OrderError>> {
  const validated = validateOrder(order);
  if (!validated.ok) return validated;

  const paid = await chargePayment(validated.value);
  if (!paid.ok) return paid;

  return reserveStock(paid.value);
}

// Caller gets exhaustive error handling via the type system
const result = await processOrder(order);
if (result.ok) {
  console.log(`Order fulfilled: ${result.value.paymentId}`);
} else {
  switch (result.error.kind) {
    case "VALIDATION_FAILED":
      respondWithBadRequest(result.error.field, result.error.reason);
      break;
    case "PAYMENT_DECLINED":
      respondWithPaymentError(result.error.code);
      break;
    case "INSUFFICIENT_STOCK":
      respondWithStockError(result.error.productId, result.error.available);
      break;
    case "RATE_LIMITED":
      respondWithRetryAfter(result.error.retryAfterMs);
      break;
  }
}
```

### GOOD: Error Boundaries (isolating exception zones)

```typescript
// Error boundary: catch at the boundary, convert to Result for internal use
class OrderController {
  async handleCreateOrder(req: Request, res: Response): Promise<void> {
    // Boundary: external I/O wrapped in error boundary
    const result = await this.orderService.processOrder(req.body);

    if (result.ok) {
      res.status(201).json(result.value);
    } else {
      // Translate domain errors to HTTP responses at the boundary
      const statusCode = this.mapErrorToStatus(result.error);
      res.status(statusCode).json({ error: result.error });
    }
  }

  private mapErrorToStatus(error: OrderError): number {
    switch (error.kind) {
      case "VALIDATION_FAILED": return 400;
      case "PAYMENT_DECLINED": return 402;
      case "INSUFFICIENT_STOCK": return 409;
      case "RATE_LIMITED": return 429;
    }
  }
}
```

---

## Alternatives & Related Approaches

| Approach | Philosophy | Best For |
|---|---|---|
| **Go-style error returns** | `value, err := fn()` -- explicit, no exceptions | When you want maximum explicitness and simplicity |
| **Rust Result/Option** | Compiler-enforced error handling via algebraic types | Systems code where unhandled errors are unacceptable |
| **Erlang "let it crash"** | Supervisors restart failed processes | Distributed systems with process isolation |
| **Monadic error handling** | Haskell `Either`, `ExceptT` monads | Highly compositional functional pipelines |
| **Exceptions (Java/C#/Python)** | Throw and catch, invisible in types | When most errors are truly exceptional |
| **Null Object pattern** | Return a do-nothing object instead of null | When absence should silently do nothing |

---

## When NOT to Apply

- **Do not use Result types for truly exceptional situations** like out-of-memory errors or stack overflows. These should remain exceptions because no caller can meaningfully handle them.
- **Do not force Result types in prototyping code.** The ceremony slows exploration. Switch to Result types when the code stabilizes.
- **Do not mix styles arbitrarily.** If your codebase uses exceptions, introducing Result types in one module creates cognitive dissonance. Adopt gradually at architectural boundaries.
- **Do not over-specify error types.** A function called by one caller does not need a 10-variant error enum. Keep error specificity proportional to the number of callers.

---

## Tensions & Trade-offs

- **Explicitness vs. readability:** Result types make errors visible but add boilerplate. Exceptions hide error paths but keep the happy path clean.
- **Granular errors vs. simplicity:** Fine-grained error types enable precise handling but increase surface area. Coarse error types are simpler but may lose information.
- **"Let it crash" vs. graceful degradation:** Restarting a process is simple but loses in-flight work. Graceful degradation preserves more state but is harder to implement correctly.
- **Performance:** Exceptions have near-zero cost on the happy path but high cost when thrown (stack unwinding). Result types have small constant overhead on every call.

---

## Real-World Consequences

- **The Ariane 5 explosion (1996)** was caused by an unhandled integer overflow exception in the inertial reference system. The software converted a 64-bit float to a 16-bit integer without checking for overflow, and the exception handler shut down the system.
- **npm's left-pad incident (2016)** cascaded because error handling in dependency resolution did not account for removed packages, causing thousands of builds to fail.
- **Stripe's API** uses explicit error codes with structured error objects, enabling clients to programmatically handle every failure mode -- a Result-type philosophy at the API boundary.

---

## Key Quotes

> "I call it my billion-dollar mistake. It was the invention of the null reference in 1965." -- Tony Hoare

> "Don't return null. Don't pass null." -- Robert C. Martin

> "Error handling is important, but if it obscures logic, it's wrong." -- Robert C. Martin

> "Make illegal states unrepresentable." -- Yaron Minsky

---

## Further Reading

- *Clean Code* by Robert C. Martin (2008) -- Chapter 7: Error Handling
- "Railway Oriented Programming" by Scott Wlaschin (fsharpforfunandprofit.com, 2014)
- *Effective Java* by Joshua Bloch (2018) -- Items 69-77 on exceptions
- *Programming Rust* by Blandy, Orendorff, and Tindall (2021) -- Chapter 7: Error Handling
- "The Error Model" by Joe Duffy (2016 blog post on Midori's error philosophy)
