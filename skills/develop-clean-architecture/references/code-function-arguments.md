---
title: Minimize Function Arguments Using Parameter Objects
impact: MEDIUM
impactDescription: reduces call-site errors, improves IDE support and refactoring safety
tags: code, functions, arguments, parameters
---

## Minimize Function Arguments Using Parameter Objects

Functions with many parameters are hard to call correctly — argument order matters, optional values create ambiguity, and adding a new parameter forces changes at every call site. Parameter objects solve this while providing named, self-documenting arguments.

**Incorrect (too many positional arguments, boolean flags):**

```typescript
async function createInvoice(
  customerId: string,
  items: LineItem[],
  currency: string,
  taxRate: number,
  dueInDays: number,
  sendEmail: boolean, // Flag argument — what does true mean at call site?
  applyDiscount: boolean, // Another boolean toggle
  memo?: string,
  poNumber?: string,
): Promise<Invoice> {
  const subtotal = items.reduce((sum, item) => sum + item.amount, 0);
  const tax = subtotal * taxRate;
  const discount = applyDiscount ? subtotal * 0.1 : 0;
  const total = subtotal + tax - discount;

  const invoice = await invoiceRepository.create({
    customerId,
    items,
    currency,
    subtotal,
    tax,
    discount,
    total,
    dueDate: addDays(new Date(), dueInDays),
    memo,
    poNumber,
  });

  if (sendEmail) { // What did true mean again?
    await emailService.sendInvoice(invoice);
  }

  return invoice;
}

// Call site — impossible to understand without reading the signature
await createInvoice(custId, items, 'USD', 0.08, 30, true, false, undefined, 'PO-442');
```

**Correct (parameter object with TypeScript interface):**

```typescript
interface CreateInvoiceCommand {
  readonly customerId: string;
  readonly items: readonly LineItem[];
  readonly currency: CurrencyCode;
  readonly taxRate: number;
  readonly paymentTermDays: number;
  readonly memo?: string;
  readonly purchaseOrderNumber?: string;
  readonly discountPolicy?: DiscountPolicy;
  readonly delivery?: InvoiceDelivery;
}

type InvoiceDelivery =
  | { readonly method: 'email'; readonly recipientOverride?: string }
  | { readonly method: 'none' };

async function createInvoice(command: CreateInvoiceCommand): Promise<Invoice> {
  const { customerId, items, currency, taxRate, paymentTermDays } = command;

  const subtotal = calculateSubtotal(items);
  const tax = subtotal * taxRate;
  const discount = command.discountPolicy
    ? applyDiscount(subtotal, command.discountPolicy)
    : 0;

  const invoice = await invoiceRepository.create({
    customerId,
    items,
    currency,
    subtotal,
    tax,
    discount,
    total: subtotal + tax - discount,
    dueDate: addDays(new Date(), paymentTermDays),
    memo: command.memo,
    purchaseOrderNumber: command.purchaseOrderNumber,
  });

  if (command.delivery?.method === 'email') {
    await emailService.sendInvoice(invoice, command.delivery.recipientOverride);
  }

  return invoice;
}

// Call site — self-documenting, order-independent
await createInvoice({
  customerId: custId,
  items,
  currency: 'USD',
  taxRate: 0.08,
  paymentTermDays: 30,
  purchaseOrderNumber: 'PO-442',
  delivery: { method: 'email' },
});
```

**When NOT to use this pattern:**
- Functions with 1-2 naturally ordered parameters (`getElementById(id)`, `add(a, b)`)
- Standard library conventions where positional args are universally understood
- Simple predicate functions used in `.filter()` and `.map()` chains

**Benefits:**
- Call sites are self-documenting — no need to count argument positions
- Adding optional parameters requires zero changes to existing call sites
- Boolean flags are replaced by discriminated unions with explicit intent

Reference: [Clean Code Chapter 3 — Function Arguments](https://www.oreilly.com/library/view/clean-code-a/9780136083238/)
