# Algebraic Data Types

**Model your domain with sum types (this OR that) and product types (this AND that), achieving exhaustive pattern matching and compile-time safety.**

---

## Origin / History

Algebraic data types (ADTs) originate from type theory and were first implemented in ML (Robin Milner, 1973). The name "algebraic" comes from the mathematical relationship: product types correspond to multiplication (a tuple of A and B has |A| x |B| possible values) and sum types correspond to addition (a value of A or B has |A| + |B| possible values). Haskell (1990) refined ADTs with its `data` declarations and pattern matching. Rust, Swift, Kotlin, and Scala all adopted ADTs as core language features.

TypeScript supports ADTs through discriminated unions (sum types) and interfaces/tuples (product types). The `never` type enables exhaustiveness checking — the compiler can verify that you have handled every variant. This capability, added incrementally through TypeScript versions 2.0-4.0, brought ML-style type safety to the JavaScript ecosystem.

---

## The Problem It Solves

Without sum types, representing "one of several possibilities" requires error-prone patterns: nullable fields (`status: string | null`), magic string enums, boolean flags, or class hierarchies with `instanceof` checks. These approaches share a critical flaw: when you add a new variant, the compiler does not tell you about all the places that need updating.

Consider a payment that can be pending, completed, failed, or refunded. With a string status field, any code that switches on the status might silently ignore a new variant. With a discriminated union, adding a new variant causes a compile error everywhere the union is not exhaustively handled. The impossible state — a "completed" payment with an error message, or a "pending" payment with a transaction ID — becomes unrepresentable.

---

## The Principle Explained

A product type combines multiple values into one. A TypeScript `interface` with multiple fields is a product type: `{ name: string; age: number }` has string x number possible values. Tuples are also product types.

A sum type represents a choice between alternatives. In TypeScript, this is a discriminated union: a union of types that share a common "discriminant" field (tag). Each variant can carry different data. The type system ensures you can only access fields that exist on the variant you have narrowed to.

Pattern matching — implemented in TypeScript through `switch` statements on the discriminant — lets you handle each variant. The key technique for exhaustiveness is the `never` type: in the default branch, assign the value to a variable of type `never`. If you have not handled all variants, the compiler will error because the value is not `never`. This turns forgotten cases from runtime bugs into compile-time errors.

---

## Code Examples

### BAD: Stringly-typed state with impossible states and no exhaustiveness

```typescript
interface Payment {
  id: string;
  status: "pending" | "completed" | "failed" | "refunded";
  amount: number;
  // These fields are sometimes present, sometimes not
  transactionId?: string;    // Only for completed
  errorMessage?: string;     // Only for failed
  refundId?: string;         // Only for refunded
  refundedAt?: Date;         // Only for refunded
}

function getPaymentSummary(payment: Payment): string {
  // No compile-time guarantee we handle all statuses
  if (payment.status === "completed") {
    // payment.transactionId might be undefined even for "completed" — type allows it
    return `Paid: ${payment.transactionId}`;
  }
  if (payment.status === "failed") {
    return `Failed: ${payment.errorMessage}`;
  }
  // Forgot "refunded" — no compiler warning!
  return "Pending";
}

// Impossible states are representable:
const broken: Payment = {
  id: "1",
  status: "pending",
  amount: 100,
  transactionId: "tx_123",  // Pending payment with a transaction ID??
  errorMessage: "oops",     // Pending payment with an error??
};
```

### GOOD: Discriminated unions making impossible states unrepresentable

```typescript
interface PendingPayment {
  readonly kind: "pending";
  readonly id: string;
  readonly amount: number;
  readonly createdAt: Date;
}

interface CompletedPayment {
  readonly kind: "completed";
  readonly id: string;
  readonly amount: number;
  readonly transactionId: string;  // Required, not optional
  readonly completedAt: Date;
}

interface FailedPayment {
  readonly kind: "failed";
  readonly id: string;
  readonly amount: number;
  readonly errorMessage: string;   // Required, not optional
  readonly failedAt: Date;
}

interface RefundedPayment {
  readonly kind: "refunded";
  readonly id: string;
  readonly amount: number;
  readonly transactionId: string;
  readonly refundId: string;       // Required, not optional
  readonly refundedAt: Date;
}

type Payment =
  | PendingPayment
  | CompletedPayment
  | FailedPayment
  | RefundedPayment;

// Exhaustiveness helper — compile error if a case is missing
function assertNever(value: never): never {
  throw new Error(`Unhandled variant: ${JSON.stringify(value)}`);
}

function getPaymentSummary(payment: Payment): string {
  switch (payment.kind) {
    case "pending":
      return `Awaiting payment of $${payment.amount}`;
    case "completed":
      return `Paid $${payment.amount} (tx: ${payment.transactionId})`;
    case "failed":
      return `Failed: ${payment.errorMessage}`;
    case "refunded":
      return `Refunded $${payment.amount} (ref: ${payment.refundId})`;
    default:
      return assertNever(payment); // Compile error if a case is missing
  }
}

// Impossible states are unrepresentable:
// A PendingPayment cannot have a transactionId — the type does not allow it.
// A FailedPayment must have an errorMessage — it is required.
```

### Modeling complex domain logic with ADTs

```typescript
// A loading state machine — common in React applications
type AsyncState<T, E = Error> =
  | { readonly status: "idle" }
  | { readonly status: "loading" }
  | { readonly status: "success"; readonly data: T }
  | { readonly status: "error"; readonly error: E };

function renderUserProfile(state: AsyncState<User, string>): string {
  switch (state.status) {
    case "idle":
      return "Click to load profile";
    case "loading":
      return "Loading...";
    case "success":
      // TypeScript narrows: state.data is available here
      return `Hello, ${state.data.name}`;
    case "error":
      // TypeScript narrows: state.error is available here
      return `Error: ${state.error}`;
    default:
      return assertNever(state);
  }
}

// Tree structure as a recursive ADT
type Tree<T> =
  | { readonly kind: "leaf"; readonly value: T }
  | { readonly kind: "node"; readonly left: Tree<T>; readonly right: Tree<T> };

function sumTree(tree: Tree<number>): number {
  switch (tree.kind) {
    case "leaf":
      return tree.value;
    case "node":
      return sumTree(tree.left) + sumTree(tree.right);
    default:
      return assertNever(tree);
  }
}
```

### State transitions enforced by types

```typescript
// Only valid transitions are possible
function completePayment(
  payment: PendingPayment,
  transactionId: string,
): CompletedPayment {
  return {
    kind: "completed",
    id: payment.id,
    amount: payment.amount,
    transactionId,
    completedAt: new Date(),
  };
}

function refundPayment(
  payment: CompletedPayment,
  refundId: string,
): RefundedPayment {
  return {
    kind: "refunded",
    id: payment.id,
    amount: payment.amount,
    transactionId: payment.transactionId,
    refundId,
    refundedAt: new Date(),
  };
}

// Compile error: cannot refund a pending payment
// refundPayment(pendingPayment, "ref_1");  // Type error!
```

---

## Alternatives & Related Approaches

| Approach | Trade-off |
|---|---|
| **Class hierarchies + instanceof** | Familiar OOP pattern. But `instanceof` does not work across module boundaries, does not narrow types in `switch`, and class hierarchies are hard to extend without modifying the base class. |
| **Visitor pattern** | Achieves exhaustiveness through double-dispatch. More ceremony (one method per variant), but allows adding operations without modifying the data types. |
| **if/else chains with type guards** | Works without discriminant fields. But no exhaustiveness checking, and chains grow unwieldy with many variants. |
| **String enums + optional fields** | Simple and familiar. But allows impossible states and provides no narrowing of fields per variant. |
| **Branded types** | Use unique symbol brands for nominal typing. Useful for primitive wrappers (UserId vs OrderId) but not for variant modeling. |

---

## When NOT to Apply

- **Simple boolean states**: If something is just "on" or "off", a boolean is clearer than `{ kind: "on" } | { kind: "off" }`.
- **Highly dynamic data**: JSON from external APIs with unpredictable shapes is better modeled with runtime validation (Zod, io-ts) than compile-time ADTs.
- **When variants share almost all fields**: If 95% of the data is shared across all variants, the boilerplate of separate interfaces outweighs the benefit. Use a shared base with a status field.
- **Rapid prototyping**: ADTs require upfront domain modeling. In exploration phases, this precision can slow you down.

---

## Tensions & Trade-offs

- **Safety vs. Verbosity**: Each variant requires its own interface. For a type with many variants and many shared fields, the boilerplate is significant.
- **Closed vs. Open**: Discriminated unions are closed — adding a variant requires modifying the union definition. Class hierarchies are open — new subclasses can be added without modifying the base. This is the "expression problem."
- **Domain modeling vs. Serialization**: ADTs model domain logic beautifully, but serializing/deserializing them (JSON, database rows) requires mapping layers.
- **Exhaustiveness vs. Default behavior**: Sometimes you want a default case. Exhaustiveness checking penalizes this — you must explicitly handle every variant even if most share behavior.

---

## Real-World Consequences

**React useReducer patterns**: The React community widely adopted discriminated unions for reducer actions. `type Action = { type: "INCREMENT" } | { type: "SET"; value: number } | { type: "RESET" }` with an exhaustive switch in the reducer catches missing action handlers at compile time.

**Making illegal states unrepresentable**: A healthcare SaaS company modeled patient records as ADTs — `type PatientRecord = Active | Discharged | Deceased`. This prevented bugs where discharged patients could be scheduled for appointments or deceased patients could receive prescriptions. The type system caught what testing alone had missed for months.

**Elm's model**: The Elm programming language built its entire architecture around ADTs for messages and models. The result is that Elm applications famously have zero runtime exceptions in production — the type system, powered by ADTs and exhaustiveness, catches the errors at compile time.

---

## Further Reading

- [TypeScript Handbook — Discriminated Unions](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#discriminated-unions)
- [Scott Wlaschin — Designing with Types (F# for Fun and Profit)](https://fsharpforfunandprofit.com/series/designing-with-types/)
- [Richard Feldman — Making Impossible States Impossible (Elm Conf 2016)](https://www.youtube.com/watch?v=IcgmSRJHu_8)
- [Yaron Minsky — Effective ML (Jane Street Tech Talk)](https://blog.janestreet.com/effective-ml-video/)
- [Alexis King — Parse, Don't Validate](https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/)
