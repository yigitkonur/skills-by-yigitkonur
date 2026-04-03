---
title: Parse at the Boundary — Trust Inside
impact: HIGH
impactDescription: eliminates scattered validation, enforces trusted types throughout inner layers
tags: code, validation, parsing, boundaries
---

## Parse at the Boundary — Trust Inside

Parse data once at the system boundary using Zod/Valibot/Arktype. After parsing, types are trusted throughout inner layers — no re-validation near domain logic. This enforces the architectural principle that adapters handle untrusted input and inner layers receive trusted, typed data.

**Incorrect (validation scattered across layers):**

```typescript
// adapters/http/OrderController.ts
app.post('/orders', async (req, res) => {
  const result = await placeOrder(req.body);
  // ...
});

// application/usecases/PlaceOrder.ts — validates AGAIN inside use case
async function placeOrder(input: unknown): Promise<Result<OrderId, OrderError>> {
  if (!input || typeof input !== 'object') throw new Error('Invalid input');
  const data = input as any;
  if (!data.customerId) throw new Error('customerId required');  // WRONG LAYER
  if (!Array.isArray(data.lineItems)) throw new Error('lineItems required');
  // Business logic buried under validation noise
}
```

**Correct (parse once at adapter boundary, trust everywhere inside):**

```typescript
import { z } from 'zod';

// adapters/http/schemas/PlaceOrder.schema.ts
const PlaceOrderSchema = z.object({
  customerId: z.string().uuid(),
  lineItems: z.array(z.object({
    productId: z.string().uuid(),
    quantity: z.number().int().positive().max(100),
  })).min(1).max(10),
  couponCode: z.string().regex(/^[A-Z0-9]{6,12}$/).optional(),
});

type PlaceOrderRequest = z.infer<typeof PlaceOrderSchema>;

// adapters/http/OrderController.ts — parse at the boundary
app.post('/orders', async (req, res) => {
  const parsed = PlaceOrderSchema.safeParse(req.body);
  if (!parsed.success) {
    return res.status(400).json({ errors: parsed.error.issues });
  }
  // parsed.data is fully typed — trusted from here inward
  const result = await placeOrder(parsed.data as PlaceOrderCommand);
  // ...
});

// application/usecases/PlaceOrder.ts — receives trusted, typed data
async function placeOrder(
  cmd: PlaceOrderCommand,
  deps: PlaceOrderDeps,
): Promise<Result<OrderId, OrderError>> {
  // cmd is trusted — NO validation here
  const order = Order.create(cmd.customerId as CustomerId, cmd.lineItems);
  // ... pure business logic orchestration
}
```

**When NOT to use this pattern:**
- Domain invariants that MUST live on the entity (e.g., max 10 lines) — entities enforce their own rules
- Internal function calls where the caller is already trusted code

**Benefits:**
- Single source of truth for input shape — Zod schema generates types automatically
- Inner layers are clean — no defensive checks polluting business logic
- Schema reusable for documentation, OpenAPI generation, and client SDKs
- Parse errors return structured, user-friendly messages at the boundary

Reference: [Parse, Don't Validate — Alexis King](https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/)
