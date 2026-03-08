# Dependency Inversion Principle (DIP)

**High-level modules should not depend on low-level modules. Both should depend on abstractions. Abstractions should not depend on details. Details should depend on abstractions.**

---

## Origin

Formulated by **Robert C. Martin** in his 1996 C++ Report article "The Dependency Inversion Principle" and later included in *Agile Software Development: Principles, Patterns, and Practices* (2003). The principle was a reaction to traditional procedural architectures where high-level business logic directly called low-level utilities (file I/O, database access, network calls), making the business logic untestable and tightly coupled to infrastructure details.

---

## The Problem It Solves

In a naive architecture, high-level policy modules (business rules, use cases) directly import and call low-level implementation modules (database drivers, HTTP clients, file system APIs). This means: business logic can't be tested without a real database. Switching from PostgreSQL to MongoDB requires rewriting business logic. The business rules -- the most valuable part of the system -- are held hostage by infrastructure decisions. The dependency arrow points the wrong way: policy depends on detail, when detail should depend on policy.

---

## The Principle Explained

DIP flips the dependency direction. Instead of `OrderService -> PostgresDatabase`, you have `OrderService -> OrderRepository (interface) <- PostgresOrderRepository`. The business logic depends on an abstraction it defines (the interface). The infrastructure implements that abstraction. The dependency arrows point *inward* toward the business logic, which sits at the center of the architecture, protected from external change.

This is the "inversion": traditionally, high-level modules depend on low-level modules. DIP inverts this so that low-level modules depend on (implement) interfaces defined by high-level modules. The high-level module *owns* the interface. It declares what it needs, and the low-level module provides it.

The practical consequence is transformative. Business logic becomes testable in isolation -- inject a fake repository in tests, a real one in production. Infrastructure becomes swappable -- change from REST to GraphQL, from PostgreSQL to DynamoDB, from SendGrid to Mailgun -- without touching business logic. Each layer can evolve independently, deployed by different teams on different schedules. The architecture becomes a set of plugins around a stable core.

---

## Code Examples

### BAD: High-level module depends on low-level details

```typescript
import { Pool } from "pg";  // Direct dependency on PostgreSQL driver
import Stripe from "stripe"; // Direct dependency on Stripe SDK
import sgMail from "@sendgrid/mail"; // Direct dependency on SendGrid

class OrderService {
  private db = new Pool({ connectionString: process.env.DATABASE_URL });
  private stripe = new Stripe(process.env.STRIPE_KEY!);

  async placeOrder(order: OrderInput): Promise<Order> {
    // Business logic is entangled with infrastructure
    const result = await this.db.query(
      "INSERT INTO orders (customer_id, total) VALUES ($1, $2) RETURNING *",
      [order.customerId, order.total]
    );

    await this.stripe.charges.create({
      amount: order.total * 100,
      currency: "usd",
      source: order.paymentToken,
    });

    await sgMail.send({
      to: order.customerEmail,
      from: "orders@example.com",
      subject: "Order Confirmation",
      text: `Your order #${result.rows[0].id} has been placed.`,
    });

    return result.rows[0];
  }
}

// Problems:
// 1. Can't test without PostgreSQL, Stripe, and SendGrid running
// 2. Can't switch to MySQL without rewriting OrderService
// 3. Can't switch to a different payment processor without rewriting
// 4. Can't switch to a different email provider without rewriting
// 5. Business logic (placing an order) is invisible under infrastructure noise
```

### GOOD: Dependency inversion with abstractions

```typescript
// --- Interfaces defined by the high-level module (business logic owns these) ---

interface OrderRepository {
  create(order: CreateOrderInput): Promise<Order>;
  findById(id: string): Promise<Order | null>;
}

interface PaymentGateway {
  charge(amount: number, currency: string, token: string): Promise<PaymentResult>;
}

interface NotificationService {
  sendOrderConfirmation(email: string, orderId: string): Promise<void>;
}

// --- High-level module: pure business logic ---

class OrderService {
  constructor(
    private readonly orders: OrderRepository,
    private readonly payments: PaymentGateway,
    private readonly notifications: NotificationService,
  ) {}

  async placeOrder(input: OrderInput): Promise<Order> {
    // Pure business logic -- no infrastructure details
    const paymentResult = await this.payments.charge(
      input.total,
      "usd",
      input.paymentToken,
    );

    if (!paymentResult.success) {
      throw new PaymentFailedError(paymentResult.error);
    }

    const order = await this.orders.create({
      customerId: input.customerId,
      total: input.total,
      paymentId: paymentResult.transactionId,
    });

    // Fire-and-forget notification (don't fail the order if email fails)
    this.notifications
      .sendOrderConfirmation(input.customerEmail, order.id)
      .catch((err) => console.error("Notification failed:", err));

    return order;
  }
}

// --- Low-level modules: implement abstractions ---

class PostgresOrderRepository implements OrderRepository {
  constructor(private readonly pool: Pool) {}

  async create(input: CreateOrderInput): Promise<Order> {
    const result = await this.pool.query(
      "INSERT INTO orders (customer_id, total, payment_id) VALUES ($1, $2, $3) RETURNING *",
      [input.customerId, input.total, input.paymentId],
    );
    return this.mapRow(result.rows[0]);
  }

  async findById(id: string): Promise<Order | null> {
    const result = await this.pool.query("SELECT * FROM orders WHERE id = $1", [id]);
    return result.rows[0] ? this.mapRow(result.rows[0]) : null;
  }

  private mapRow(row: Record<string, unknown>): Order {
    return { id: row.id as string, customerId: row.customer_id as string, total: row.total as number, paymentId: row.payment_id as string };
  }
}

class StripePaymentGateway implements PaymentGateway {
  constructor(private readonly stripe: Stripe) {}

  async charge(amount: number, currency: string, token: string): Promise<PaymentResult> {
    try {
      const charge = await this.stripe.charges.create({
        amount: amount * 100,
        currency,
        source: token,
      });
      return { success: true, transactionId: charge.id };
    } catch (error) {
      return { success: false, error: (error as Error).message };
    }
  }
}

class SendGridNotificationService implements NotificationService {
  async sendOrderConfirmation(email: string, orderId: string): Promise<void> {
    await sgMail.send({
      to: email,
      from: "orders@example.com",
      subject: "Order Confirmation",
      text: `Your order #${orderId} has been placed.`,
    });
  }
}

// --- Composition root: wire everything together ---
function createOrderService(): OrderService {
  const pool = new Pool({ connectionString: process.env.DATABASE_URL });
  const stripe = new Stripe(process.env.STRIPE_KEY!);

  return new OrderService(
    new PostgresOrderRepository(pool),
    new StripePaymentGateway(stripe),
    new SendGridNotificationService(),
  );
}
```

### Testing with DIP: trivially simple

```typescript
// Test business logic without ANY infrastructure
describe("OrderService", () => {
  it("should create an order after successful payment", async () => {
    const mockOrders: OrderRepository = {
      create: async (input) => ({ id: "order-1", ...input }),
      findById: async () => null,
    };

    const mockPayments: PaymentGateway = {
      charge: async () => ({ success: true, transactionId: "tx-123" }),
    };

    const mockNotifications: NotificationService = {
      sendOrderConfirmation: async () => {},
    };

    const service = new OrderService(mockOrders, mockPayments, mockNotifications);

    const order = await service.placeOrder({
      customerId: "cust-1",
      total: 99.99,
      paymentToken: "tok_123",
      customerEmail: "test@example.com",
    });

    expect(order.id).toBe("order-1");
    expect(order.paymentId).toBe("tx-123");
  });

  it("should throw when payment fails", async () => {
    const mockPayments: PaymentGateway = {
      charge: async () => ({ success: false, error: "Card declined" }),
    };

    const service = new OrderService(
      { create: async () => ({} as Order), findById: async () => null },
      mockPayments,
      { sendOrderConfirmation: async () => {} },
    );

    await expect(
      service.placeOrder({
        customerId: "cust-1",
        total: 99.99,
        paymentToken: "tok_bad",
        customerEmail: "test@example.com",
      }),
    ).rejects.toThrow(PaymentFailedError);
  });
});
// No database. No Stripe. No SendGrid. Tests run in milliseconds.
```

---

## Alternatives & Related Principles

| Principle | Relationship |
|-----------|-------------|
| **Service Locator** | An alternative to constructor injection. Objects request dependencies from a central registry at runtime. Easier to set up but hides dependencies (they're not visible in the constructor), making testing and reasoning harder. Generally considered an anti-pattern in modern development. |
| **Plugin Architecture** | The architectural manifestation of DIP. The core system defines interfaces (ports), and external modules provide implementations (plugins/adapters). Examples: VS Code extensions, webpack plugins, ESLint rules. |
| **Dependency Injection (DI) Frameworks** | Tools like InversifyJS, tsyringe, or NestJS's DI container automate the wiring of dependencies. They reduce the boilerplate of manual construction but add framework coupling. |
| **Hexagonal Architecture (Ports & Adapters)** | An architectural pattern built entirely on DIP. The core domain defines "ports" (interfaces). External systems connect through "adapters" (implementations). All dependencies point inward toward the domain. |
| **Clean Architecture** | Robert C. Martin's formalization of DIP at the architectural level. Concentric circles with business entities at the center, use cases around them, and infrastructure at the outer ring. All dependencies point inward. |

---

## When NOT to Apply

- **Simple scripts and utilities.** A 100-line CLI tool doesn't need interfaces and dependency injection. Direct dependencies are fine when the code is simple and unlikely to change.
- **When there's genuinely only one implementation.** If you will never swap PostgreSQL for another database (and you know this), an interface adds ceremony without benefit. That said, the testability argument still applies.
- **Stable, well-tested libraries.** Wrapping `Math.random()` or `Date.now()` in an interface "for testability" is usually overkill. Inject them only when they genuinely complicate testing.
- **Performance-critical code.** Virtual dispatch through interfaces has a small runtime cost. In hot loops processing millions of iterations, direct calls may be necessary.

---

## Tensions & Trade-offs

- **DIP vs. KISS**: DIP adds interfaces, implementations, and a composition root. For simple applications, this is over-engineering. Apply DIP at the boundaries where the real cost of coupling lives (database, external APIs, file system), not on every internal dependency.
- **DIP vs. YAGNI**: Creating an interface before you need a second implementation is speculative. Counter-argument: even with one implementation, the interface enables testing. The testability benefit often justifies the interface even without a second implementation.
- **DIP vs. Readability**: "Go to definition" on an interface shows the interface, not the implementation. Developers must navigate to find the actual behavior. Modern IDEs mitigate this with "go to implementations."
- **DIP vs. Framework Conventions**: Some frameworks (Express, Next.js) have their own patterns for dependency management. Fighting the framework to enforce DIP can be more costly than accepting its conventions.

---

## Real-World Consequences

A healthcare startup built their entire system with direct dependencies: business logic imported PostgreSQL drivers, Twilio SDK, and AWS S3 SDK directly. When they needed to run the system in an air-gapped government environment (no internet, different database, different file storage), they faced a 6-month rewrite. Every business logic file had `import pg from 'pg'` and `import AWS from 'aws-sdk'` sprinkled throughout. Had they used DIP -- defining `PatientRepository`, `NotificationService`, and `FileStorage` interfaces -- the government deployment would have required only new implementations of those interfaces, wired in a different composition root. Weeks, not months.

---

## Key Quotes

> "High-level modules should not depend on low-level modules. Both should depend on abstractions."
> -- Robert C. Martin

> "The dependency inversion principle is the fundamental low-level mechanism behind many of the benefits claimed for object-oriented technology."
> -- Robert C. Martin

> "Depend on abstractions, not on concretions."
> -- Robert C. Martin

> "The art of architecture is the art of drawing lines that I call boundaries. Those boundaries separate software elements from one another and restrict those on one side from knowing about those on the other."
> -- Robert C. Martin, *Clean Architecture*

---

## Further Reading

- *Agile Software Development: Principles, Patterns, and Practices* -- Robert C. Martin (2003)
- *Clean Architecture* -- Robert C. Martin (2017)
- ["The Dependency Inversion Principle"](https://web.archive.org/web/20110714224327/http://www.objectmentor.com/resources/articles/dip.pdf) -- Robert C. Martin (1996)
- *Dependency Injection: Principles, Practices, and Patterns* -- Steven van Deursen & Mark Seemann (2019)
- *Growing Object-Oriented Software, Guided by Tests* -- Steve Freeman & Nat Pryce (2009)
- *Hexagonal Architecture* -- Alistair Cockburn (2005)
