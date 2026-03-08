# Law of Demeter (LoD)

**Don't talk to strangers — only interact with your immediate collaborators.**

---

## Origin

The Law of Demeter was formulated in 1987 by Ian Holland at Northeastern University, working on the Demeter Project (named after the Greek goddess of agriculture). It was published in the paper *"Object-Oriented Programming: An Objective Sense of Style"* by Karl Lieberherr, Ian Holland, and Arthur Riel. The principle is sometimes called the **Principle of Least Knowledge**.

---

## The Problem It Solves

Without the Law of Demeter, objects reach deep into the internal structure of other objects, creating **tight coupling** across multiple layers. When `order.getCustomer().getAddress().getCity()` appears in your code, a change to the `Address` structure forces changes everywhere this chain exists. The resulting code is brittle, hard to test (you must mock entire object graphs), and violates encapsulation at every dot in the chain.

---

## The Principle Explained

The Law of Demeter states that a method `M` of object `O` should only call methods on:

1. `O` itself
2. Objects passed as arguments to `M`
3. Objects created within `M`
4. `O`'s direct component objects (fields/properties)

In practical terms, **count the dots**. If you see more than one dot in a chain (excluding fluent builder patterns), you are likely violating LoD. The fix is to push the behavior closer to the data it operates on — ask the object that owns the data to perform the action for you.

This does not mean you wrap every property in a delegation method. That leads to bloated interfaces and "middle-man" classes. The real insight is about **responsibility**: if you find yourself reaching through an object to get data, the operation probably belongs in that object (or an intermediate collaborator) rather than in the caller.

The law is a heuristic, not an absolute rule. Data structures (DTOs, records) that exist purely to carry data are exempt — they have no behavior to push into. The key is recognizing whether you are dealing with an **object** (behavior + data) or a **data structure** (data only).

---

## Code Examples

### BAD: Violating LoD — reaching through object chains

```typescript
interface Address {
  city: string;
  state: string;
  zipCode: string;
}

interface Customer {
  name: string;
  address: Address;
}

interface Order {
  customer: Customer;
  total: number;
}

// Caller reaches deep into the structure
function calculateShippingCost(order: Order): number {
  // Violation: order -> customer -> address -> state
  const state = order.customer.address.state;

  if (state === "CA") {
    return order.total * 0.1;
  }
  return order.total * 0.05;
}

// Testing requires building the entire object graph
function calculateTax(order: Order): number {
  // Violation: reaching through multiple layers
  if (order.customer.address.zipCode.startsWith("9")) {
    return order.total * 0.0875;
  }
  return order.total * 0.06;
}
```

### GOOD: Applying LoD — asking objects to do the work

```typescript
class ShippingAddress {
  constructor(
    private readonly city: string,
    private readonly state: string,
    private readonly zipCode: string
  ) {}

  isInState(stateCode: string): boolean {
    return this.state === stateCode;
  }

  isInZipRange(prefix: string): boolean {
    return this.zipCode.startsWith(prefix);
  }

  getShippingZone(): "west" | "east" | "central" {
    if (["CA", "OR", "WA"].includes(this.state)) return "west";
    if (["NY", "NJ", "CT"].includes(this.state)) return "east";
    return "central";
  }
}

class Customer {
  constructor(
    private readonly name: string,
    private readonly shippingAddress: ShippingAddress
  ) {}

  getShippingZone(): "west" | "east" | "central" {
    return this.shippingAddress.getShippingZone();
  }

  isInTaxZipRange(prefix: string): boolean {
    return this.shippingAddress.isInZipRange(prefix);
  }
}

class Order {
  constructor(
    private readonly customer: Customer,
    private readonly total: number
  ) {}

  calculateShippingCost(): number {
    const zone = this.customer.getShippingZone();
    const rates = { west: 0.1, east: 0.07, central: 0.05 };
    return this.total * rates[zone];
  }

  calculateTax(): number {
    if (this.customer.isInTaxZipRange("9")) {
      return this.total * 0.0875;
    }
    return this.total * 0.06;
  }
}

// Caller only talks to its immediate collaborator
function processOrder(order: Order): { shipping: number; tax: number } {
  return {
    shipping: order.calculateShippingCost(),
    tax: order.calculateTax(),
  };
}
```

---

## Alternatives & Related Principles

| Principle | Relationship |
|---|---|
| **Tell, Don't Ask** | Closely aligned — push behavior to the object that owns the data. LoD is the structural rule; Tell Don't Ask is the behavioral motivation. |
| **Fluent Interfaces** | Intentionally violate LoD's "count the dots" heuristic. `builder.setName("x").setAge(5).build()` chains dots but each call returns the same or next builder — this is not reaching into internal structure. |
| **Facade Pattern** | Provides a simplified interface over a complex subsystem, enforcing LoD at the architectural level. |
| **Mediator Pattern** | Centralizes communication between objects so they don't need to know about each other's internals. |

---

## When NOT to Apply

- **Data Transfer Objects / Records**: DTOs are pure data structures. Applying LoD to them creates pointless delegation methods. `dto.address.city` is fine for a data carrier.
- **Fluent APIs / Builders**: Method chaining that returns `this` or a new builder is not an LoD violation — you are always talking to the same abstraction.
- **Internal module code**: Within a tightly-coupled module that is deployed together, excessive LoD adherence creates "middle man" classes that do nothing but forward calls.
- **Functional pipelines**: `array.filter(...).map(...).reduce(...)` chains are transformations on values, not reaching into object internals.

---

## Tensions & Trade-offs

- **LoD vs. Simplicity**: Strict adherence can create dozens of small forwarding methods (`customer.getAddressCity()`, `customer.getAddressState()`), making the codebase harder to navigate.
- **LoD vs. Performance**: Delegation layers add method call overhead. In hot paths, this can matter.
- **LoD vs. Discoverability**: When everything is encapsulated behind delegation, IDE autocompletion becomes less helpful — you cannot explore the structure.
- **Encapsulation vs. Flexibility**: The more you hide, the more wrapper methods you need when new use cases arise.

---

## Real-World Consequences

**Violation example**: A large e-commerce platform had shipping logic that reached through `order.cart.items[0].product.vendor.warehouse.location.country`. When the warehouse model was restructured, over 200 files required changes. The migration took three sprints instead of the estimated one.

**Adherence example**: A payments service exposed only `payment.isEligibleForRefund()` rather than letting callers inspect internal state. When refund eligibility rules changed from "within 30 days" to a complex multi-factor check, only the `Payment` class changed. Zero callers were modified.

---

## Key Quotes

> "Only talk to your immediate friends." — Ian Holland, 1987

> "The Law of Demeter for functions states that any method of an object should call only methods belonging to itself, any parameters passed in, any objects it creates, and any directly held component objects." — *The Pragmatic Programmer*, Hunt & Thomas

> "More than one dot is a smell." — common paraphrase (though not always accurate)

---

## Further Reading

- Lieberherr, K., Holland, I., Riel, A. — *Object-Oriented Programming: An Objective Sense of Style* (1988)
- Hunt, A., Thomas, D. — *The Pragmatic Programmer* (1999), Chapter on "The Law of Demeter"
- Martin, R.C. — *Clean Code* (2008), Chapter 6: "Objects and Data Structures"
- Demeter Project homepage: [ccs.neu.edu/research/demeter](http://www.ccs.neu.edu/research/demeter/)
- Fowler, M. — [TellDontAsk](https://martinfowler.com/bliki/TellDontAsk.html) (related principle)
