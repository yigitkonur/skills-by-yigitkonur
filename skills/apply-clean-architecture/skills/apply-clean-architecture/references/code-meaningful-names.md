---
title: Use Meaningful Names from the Domain's Ubiquitous Language
impact: HIGH
impactDescription: eliminates decoding time, enforces DDD ubiquitous language across codebase
tags: code, naming, readability, intent, ubiquitous-language
---

## Use Meaningful Names from the Domain's Ubiquitous Language

Clean Code says: use intention-revealing names. DDD says: names must come from the domain's ubiquitous language — names in code must match names used by domain experts. Combine both: every name should be pronounceable, searchable, and drawn from the domain vocabulary.

**Naming conventions by construct type:**

| Construct | Convention | Example | Why |
|---|---|---|---|
| Domain Entity | `PascalCase` noun | `Order`, `Customer` | Mirrors DDD entity |
| Value Object | `PascalCase` noun | `Money`, `EmailAddress` | Self-documenting domain concept |
| Use Case fn | verb + noun phrase | `placeOrder`, `cancelOrder` | Screaming architecture |
| Port (interface) | `I` prefix OR noun role | `IOrderRepository` or `OrderRepository` | Choose one per project |
| Adapter impl | prefix concrete tech | `PrismaOrderRepository` | Layer explicit |
| Domain Event | past tense noun | `OrderPlaced`, `PaymentFailed` | "Something happened" |
| Command | imperative noun | `PlaceOrderCommand` | CQRS command |
| Query | `Get/Find` + noun | `GetOrderByIdQuery` | CQRS query |
| Error class | noun + `Error` | `InsufficientFundsError` | Findable by type |

**Incorrect (abbreviated, misleading, encoded names):**

```typescript
// Cryptic abbreviations force readers to decode
const d = new Date(); // What does d represent?
const ymdStr = formatDate(d); // Unpronounceable

interface IUserData { // Hungarian-style I prefix adds noise
  fn: string; // First name? Function? Filename?
  ln: string;
  dob: number; // Timestamp? Age? Year?
  addr: string;
}

function calcPrc(amt: number, tx: number, dsc: number): number {
  return amt + (amt * tx) - dsc; // What is prc? price? percent? process?
}

enum Status { // Generic — status of what?
  a, // What does 'a' mean?
  i,
  d,
}

class Mgr<T, U> { // T and U reveal nothing about constraints
  proc(val: T): U { /* ... */ }
}

type Cb = (e: Error | null, r: unknown) => void; // Callback? What kind?
```

**Correct (intention-revealing, pronounceable, searchable names):**

```typescript
const currentDate = new Date();
const formattedIsoDate = formatDate(currentDate);

interface UserProfile { // No I prefix — TypeScript convention
  firstName: string;
  lastName: string;
  dateOfBirth: Date; // Type reveals format
  shippingAddress: string;
}

function calculateTotalPrice(
  subtotalCents: number,
  taxRate: number,
  discountCents: number,
): number {
  return subtotalCents + (subtotalCents * taxRate) - discountCents;
}

enum SubscriptionStatus { // Scoped, clear domain context
  Active = 'ACTIVE',
  Inactive = 'INACTIVE',
  Delinquent = 'DELINQUENT',
}

class EntityRepository<TEntity, TIdentifier> {
  findById(id: TIdentifier): Promise<TEntity | undefined> { /* ... */ }
}

type OrderEventHandler = (error: Error | null, result: OrderConfirmation) => void;
```

**When NOT to use this pattern:**
- Loop indices (`i`, `j`, `k`) in small, tight loops are idiomatic and clear
- Lambda parameters in short callbacks (`items.map(x => x.id)`) when context is obvious
- Well-known mathematical formulas where single-letter variables match the domain notation

**Benefits:**
- New team members understand code without a glossary or tribal knowledge
- Find-and-replace refactoring works reliably with unique, descriptive names
- Code reviews focus on logic instead of deciphering abbreviations

Reference: [Clean Code Chapter 2 — Meaningful Names](https://www.oreilly.com/library/view/clean-code-a/9780136083238/)
