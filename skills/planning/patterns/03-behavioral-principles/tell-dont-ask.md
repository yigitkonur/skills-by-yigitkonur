# Tell, Don't Ask

**Push behavior to the object that owns the data, instead of pulling data out and operating on it externally.**

---

## Origin

The Tell, Don't Ask principle was articulated by Andy Hunt and Dave Thomas in *The Pragmatic Programmer* (1999) and further popularized by Alec Sharp in *Smalltalk by Example* (1997). Martin Fowler wrote an influential bliki post on the topic in 2013, connecting it to the broader discussion of domain modeling. The concept is rooted in object-oriented design thinking that traces back to Alan Kay's original vision of objects as communicating entities that send messages to each other, rather than passive data containers.

---

## The Problem It Solves

When code asks an object for its data, makes a decision based on that data, and then tells the object what to do, the decision logic is in the wrong place. This leads to the **Anemic Domain Model** anti-pattern, where objects are reduced to data bags and business logic is scattered across services, controllers, and utility functions. The result is duplicated decision-making, shotgun surgery when rules change, and an inability to ensure invariants because anyone can read the data and act on it however they choose.

---

## The Principle Explained

Tell, Don't Ask reverses the relationship between caller and object. Instead of asking `if (account.getBalance() > amount)` and then calling `account.debit(amount)`, you tell the object what you want: `account.withdraw(amount)` — and the object decides internally whether the operation is valid.

The key insight is that the object that owns the data is in the best position to make decisions about that data. It has access to all internal state, it can enforce invariants, and it can evolve its decision logic without requiring changes to callers. When callers make decisions based on extracted data, any change to the business rule requires finding and updating every caller.

This does not mean objects should never expose data. Read-only properties for display, serialization, and reporting are fine. The principle targets **behavioral decisions** — when code extracts data to determine what action to take. If you find yourself writing `if (object.getX() === something) { object.doY() }`, that is a strong signal that `doY` should incorporate the condition internally, or a new method should encapsulate the entire decision.

---

## Code Examples

### BAD: Asking for data and making external decisions

```typescript
class BankAccount {
  private balance: number;
  private status: "active" | "frozen" | "closed";
  private overdraftLimit: number;

  getBalance(): number { return this.balance; }
  getStatus(): string { return this.status; }
  getOverdraftLimit(): number { return this.overdraftLimit; }
  setBalance(amount: number): void { this.balance = amount; }
}

// Business logic is scattered across the service
class PaymentService {
  processPayment(account: BankAccount, amount: number): PaymentResult {
    // ASK: pull out all the data
    if (account.getStatus() !== "active") {
      return { success: false, reason: "Account not active" };
    }

    if (account.getBalance() + account.getOverdraftLimit() < amount) {
      return { success: false, reason: "Insufficient funds" };
    }

    // Dangerous: caller manipulates internal state directly
    account.setBalance(account.getBalance() - amount);

    return { success: true };
  }
}

// Same logic duplicated in another service
class TransferService {
  transfer(from: BankAccount, to: BankAccount, amount: number): void {
    // Duplicate decision logic — if overdraft rules change, both must update
    if (from.getStatus() !== "active") throw new Error("Source account not active");
    if (from.getBalance() + from.getOverdraftLimit() < amount) {
      throw new Error("Insufficient funds");
    }
    from.setBalance(from.getBalance() - amount);
    to.setBalance(to.getBalance() + amount);
  }
}
```

### GOOD: Telling objects what to do — behavior lives with data

```typescript
class InsufficientFundsError extends Error {
  constructor(
    public readonly requested: number,
    public readonly available: number
  ) {
    super(`Insufficient funds: requested ${requested}, available ${available}`);
  }
}

class AccountNotActiveError extends Error {
  constructor(public readonly accountId: string) {
    super(`Account ${accountId} is not active`);
  }
}

class BankAccount {
  constructor(
    private readonly id: string,
    private balance: number,
    private status: "active" | "frozen" | "closed",
    private readonly overdraftLimit: number
  ) {}

  // TELL: the account decides if withdrawal is allowed
  withdraw(amount: number): void {
    this.ensureActive();
    this.ensureSufficientFunds(amount);
    this.balance -= amount;
  }

  // TELL: the account decides if deposit is allowed
  deposit(amount: number): void {
    this.ensureActive();
    if (amount <= 0) {
      throw new Error("Deposit amount must be positive");
    }
    this.balance += amount;
  }

  // TELL: transfer logic encapsulated — invariants enforced
  transferTo(target: BankAccount, amount: number): void {
    this.withdraw(amount);
    target.deposit(amount);
  }

  canAfford(amount: number): boolean {
    return this.status === "active" && this.availableFunds() >= amount;
  }

  // Read-only access for display/reporting is fine
  getBalanceSnapshot(): { balance: number; available: number } {
    return {
      balance: this.balance,
      available: this.availableFunds(),
    };
  }

  private ensureActive(): void {
    if (this.status !== "active") {
      throw new AccountNotActiveError(this.id);
    }
  }

  private ensureSufficientFunds(amount: number): void {
    const available = this.availableFunds();
    if (available < amount) {
      throw new InsufficientFundsError(amount, available);
    }
  }

  private availableFunds(): number {
    return this.balance + this.overdraftLimit;
  }
}

// Services are thin — they orchestrate, not decide
class PaymentService {
  processPayment(account: BankAccount, amount: number): PaymentResult {
    try {
      account.withdraw(amount); // TELL the account to withdraw
      return { success: true };
    } catch (error) {
      if (error instanceof InsufficientFundsError) {
        return { success: false, reason: "Insufficient funds" };
      }
      if (error instanceof AccountNotActiveError) {
        return { success: false, reason: "Account not active" };
      }
      throw error;
    }
  }
}

class TransferService {
  transfer(from: BankAccount, to: BankAccount, amount: number): void {
    from.transferTo(to, amount); // One line — all logic in the domain
  }
}
```

---

## Alternatives & Related Principles

| Approach | Relationship |
|---|---|
| **Anemic Domain Model** | The anti-pattern that results from ignoring Tell, Don't Ask. Objects hold data; services hold logic. Martin Fowler calls this "one of those anti-patterns that are so common that many people think it is normal." |
| **Procedural Style** | In procedural programming, separating data and functions is the norm. Tell, Don't Ask is an OO principle — it does not apply to pure procedural code. |
| **Functional Pipelines** | In FP, data flows through transformations: `data |> validate |> transform |> persist`. There is no "object" to tell. Tell, Don't Ask and FP solve the same problem (co-locating logic with data) through different mechanisms. |
| **Law of Demeter** | Closely related — LoD says "don't reach through objects," Tell Don't Ask says "don't pull data out of objects." Together they push you toward rich domain models. |
| **Command-Query Separation** | Commands change state (tell), queries return data (ask). CQS is about keeping these separate; Tell Don't Ask is about preferring commands over data-extraction-then-decision. |
| **Information Expert (GRASP)** | Assign responsibility to the class that has the information needed to fulfill it. Tell, Don't Ask is a behavioral restatement of Information Expert. |

---

## When NOT to Apply

- **Presentation / UI layers**: Views need to ask objects for data to display. A React component rendering `{account.balance}` is asking, and that is correct — the UI's job is to display, not to embed domain logic.
- **Reporting and analytics**: Aggregating data across objects for reports requires extracting data. This is a read-only concern.
- **Serialization / API responses**: Transforming objects to JSON requires reading properties.
- **Data structures vs. objects**: If something is a plain data carrier (a DTO, a value object), asking it for its fields is fine. Tell, Don't Ask applies to **behavioral objects**.
- **Functional codebases**: In a functional architecture with immutable data and pure functions, the principle does not directly apply. The equivalent is keeping transformation logic co-located with the types it operates on.

---

## Tensions & Trade-offs

- **Tell Don't Ask vs. Single Responsibility**: If you push too much logic into domain objects, they become bloated God objects. The balance is pushing **domain decisions** into objects while keeping orchestration in services.
- **Testability**: Rich domain objects with embedded logic are easy to unit test. But they can be harder to test in integration if they depend on infrastructure.
- **Tell Don't Ask vs. CQRS**: CQRS separates reads from writes. The "ask" side (queries) is explicitly designed to extract data, which seems to contradict Tell Don't Ask. The resolution: Tell Don't Ask applies to behavioral decisions, not to data retrieval for display.
- **Pragmatism**: A one-line check `if (user.isAdmin())` followed by an action is a minor "ask." Wrapping this in `user.performAdminAction(callback)` adds complexity for no real benefit.

---

## Real-World Consequences

**Violation example**: A healthcare system had patient eligibility checks duplicated across 14 different services. Each service asked the `Patient` object for insurance data, dates, and status flags, then applied its own eligibility logic. When eligibility rules changed for a regulatory update, 14 services needed modification. Three were missed, causing compliance violations.

**Adherence example**: The Shopify codebase uses rich domain objects for order processing. An `Order` object knows its own fulfillment rules, discount eligibility, and tax obligations. When Canada changed tax rules, only the `Order` and `TaxCalculator` classes needed changes — the dozens of services that orchestrate orders were untouched.

---

## Key Quotes

> "Procedural code gets information then makes decisions. Object-oriented code tells objects to do things." — Alec Sharp, *Smalltalk by Example*

> "Tell-Don't-Ask is a stepping stone towards a more encapsulated design." — Martin Fowler

> "The fundamental tenet of object orientation is the unification of methods and data." — Grady Booch

---

## Further Reading

- Fowler, M. — [TellDontAsk](https://martinfowler.com/bliki/TellDontAsk.html) (2013)
- Hunt, A., Thomas, D. — *The Pragmatic Programmer* (1999)
- Sharp, A. — *Smalltalk by Example* (1997)
- Fowler, M. — [AnemicDomainModel](https://martinfowler.com/bliki/AnemicDomainModel.html) (2003)
- Evans, E. — *Domain-Driven Design* (2003), on rich domain models
- Larman, C. — *Applying UML and Patterns* (2004), GRASP Information Expert
