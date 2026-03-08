# Spaghetti Code

## Origin

The term dates to the 1970s, popularized by Edsger Dijkstra's campaign against `goto` statements ("Go To Statement Considered Harmful," 1968). Spaghetti code originally referred to tangled control flow created by excessive `goto` jumps. Today it describes any code with complex, intertwined control flow that is difficult to follow.

## Explanation

Spaghetti code is code where the flow of execution is tangled and unpredictable. Functions call each other in unexpected ways, conditionals nest deeply, state is modified from multiple places, and tracing the execution path from input to output requires heroic effort.

Unlike a God Object (which is about responsibility concentration), spaghetti code is about control flow tangling. A small module can be spaghetti code. The defining characteristic is that you cannot read the code linearly and understand what it does.

## TypeScript Code Examples

### Bad: Tangled Control Flow

```typescript
export async function processOrder(req: Request): Promise<Response> {
  let user: User | null = null;
  let order: Order | null = null;
  let discount = 0;
  let shippingCost = 0;
  let taxAmount = 0;
  let retryCount = 0;
  let needsReview = false;
  let emailSent = false;

  try {
    user = await getUser(req.body.userId);
    if (!user) {
      if (req.body.guestCheckout) {
        user = await createGuestUser(req.body.email);
        if (!user) return errorResponse(400, "Cannot create guest");
        needsReview = true;
      } else {
        return errorResponse(401, "Not authenticated");
      }
    } else {
      if (user.suspended) {
        if (user.suspensionReason === "payment" && req.body.paymentUpdate) {
          await unsuspendUser(user.id);
          user.suspended = false; // Mutating the object in place
        } else {
          return errorResponse(403, "Account suspended");
        }
      }
    }

    for (const item of req.body.items) {
      const product = await getProduct(item.productId);
      if (!product) continue; // Silently drops invalid items
      if (product.stock < item.quantity) {
        if (product.allowBackorder) {
          needsReview = true;
        } else {
          if (req.body.partialOrder) {
            item.quantity = product.stock; // Mutates input
            if (item.quantity === 0) continue;
          } else {
            return errorResponse(400, `${product.name} out of stock`);
          }
        }
      }
    }

    retry: while (retryCount < 3) {
      try {
        order = await createOrder(user!.id, req.body.items);
        break;
      } catch (e) {
        retryCount++;
        if (retryCount >= 3) throw e;
        await sleep(retryCount * 1000);
        continue retry;
      }
    }

    // 80 more lines of nested conditionals for discounts, tax,
    // shipping, payment processing, email notifications...
    // Each section mutates shared variables and checks flags
    // set by previous sections.

    if (needsReview && !emailSent) {
      try {
        await sendReviewEmail(order!);
        emailSent = true;
      } catch {
        // Swallow error — email is "non-critical"
        // but now needsReview is true and emailSent is false
        // and later code checks both flags differently
      }
    }

    return successResponse(order);
  } catch (e) {
    // Catch-all that handles errors from any of the above sections
    // What state is the order in? Was payment charged? Who knows.
    return errorResponse(500, "Something went wrong");
  }
}
```

### Good: Structured, Linear Flow

```typescript
export async function processOrder(req: Request): Promise<Response> {
  // Step 1: Resolve user
  const userResult = await resolveUser(req.body);
  if (!userResult.success) return errorResponse(userResult.status, userResult.error);

  // Step 2: Validate and adjust items
  const itemsResult = await validateOrderItems(req.body.items, req.body.partialOrder);
  if (!itemsResult.success) return errorResponse(400, itemsResult.error);

  // Step 3: Create order with retry
  const order = await createOrderWithRetry(userResult.user.id, itemsResult.items);

  // Step 4: Calculate pricing
  const pricing = await calculatePricing(order, userResult.user);

  // Step 5: Process payment
  const paymentResult = await processPayment(order, pricing);
  if (!paymentResult.success) {
    await cancelOrder(order.id);
    return errorResponse(402, "Payment failed");
  }

  // Step 6: Post-order processing (non-critical, fire-and-forget)
  await postOrderProcessing(order, userResult.needsReview).catch(logError);

  return successResponse(order);
}

// Each step is a focused function with clear inputs and outputs.
// No shared mutable state. No nested conditionals. Linear flow.

async function resolveUser(body: OrderRequest): Promise<UserResolution> {
  if (body.userId) {
    const user = await getUser(body.userId);
    if (!user) return { success: false, status: 401, error: "User not found" };
    if (user.suspended) return { success: false, status: 403, error: "Suspended" };
    return { success: true, user, needsReview: false };
  }
  if (body.guestCheckout) {
    const guest = await createGuestUser(body.email);
    if (!guest) return { success: false, status: 400, error: "Guest creation failed" };
    return { success: true, user: guest, needsReview: true };
  }
  return { success: false, status: 401, error: "Authentication required" };
}
```

## Measuring Spaghetti: Cyclomatic Complexity

Cyclomatic complexity counts the number of independent paths through a function. High complexity = spaghetti.

```typescript
// Cyclomatic complexity: count decisions (if, else, for, while, case, &&, ||, ?:)

// Complexity 1: linear code, no branches
function add(a: number, b: number): number {
  return a + b;  // Complexity: 1
}

// Complexity 12+: spaghetti territory
function processInput(input: unknown): Result {
  if (input === null) { /* ... */ }                    // +1
  else if (typeof input === "string") {                // +1
    if (input.length === 0) { /* ... */ }              // +1
    else if (input.startsWith("http")) {               // +1
      if (input.includes("api")) { /* ... */ }         // +1
      else { /* ... */ }
    }
  } else if (Array.isArray(input)) {                   // +1
    for (const item of input) {                        // +1
      if (item && typeof item === "object") { /* */ }  // +1
    }
  }
  // ... continues nesting
}

// Rule of thumb:
// 1-5:   Simple, easy to test
// 6-10:  Moderate, consider refactoring
// 11-20: Complex, should refactor
// 21+:   Spaghetti — must refactor
```

## Alternatives and Countermeasures

- **Extract functions:** Move each logical step into a named function.
- **Early returns:** Replace nested `if/else` with guard clauses that return early.
- **Result types:** Use typed result objects instead of flags and mutable state.
- **Pipeline pattern:** Process data through a chain of transformations.
- **State machines:** For complex state transitions, use an explicit state machine instead of flags.

## When NOT to Apply (When Complex Flow Is Acceptable)

- **Parsers and lexers:** Parsing inherently involves complex branching. The complexity is essential, not accidental.
- **Protocol implementations:** Network protocols have complex state machines that resist simplification.
- **Performance-critical inner loops:** Sometimes an unrolled, branchy loop is necessary for performance.

## Trade-offs

| Approach | Benefit | Cost |
|---|---|---|
| Keep spaghetti code as-is | No refactoring risk | Growing maintenance burden, bugs hide |
| Extract into many small functions | Each function is simple | More indirection, harder to trace |
| Use a framework/pipeline | Structured flow, reusable stages | Learning curve, framework dependency |
| Rewrite from scratch | Clean slate | High risk, violates Gall's Law |

## Real-World Consequences

- **Healthcare.gov (2013):** The codebase had deeply nested, tangled logic across multiple vendor codebases. When it failed on launch, debugging was nearly impossible because no one could trace the execution flow.
- **The Ariane 5 explosion (1996):** A control flow path in the inertial reference system triggered a conversion overflow. The tangled error-handling code masked the real failure.
- **Legacy banking systems:** COBOL codebases with thousands of `GOTO` statements — literal spaghetti code — that banks cannot replace because no one fully understands the control flow.

## Further Reading

- Dijkstra, E. (1968). "Go To Statement Considered Harmful"
- Martin, R. (2008). *Clean Code* — chapters on functions and control flow
- McCabe, T. (1976). "A Complexity Measure" — cyclomatic complexity
- Fowler, M. (2018). *Refactoring* — "Long Method" and "Replace Nested Conditional with Guard Clauses"
