# Hollywood Principle

**"Don't call us, we'll call you." — Inversion of Control for decoupled systems.**

---

## Origin

The Hollywood Principle was named by Richard Sweet in his 1983 paper at a Mesa language workshop, drawing an analogy to Hollywood casting calls where actors audition and then wait — they do not call the studio. In software, it was formalized through the concept of **Inversion of Control (IoC)** by Ralph Johnson and Brian Foote in their 1988 paper *"Designing Reusable Classes."* Martin Fowler later clarified the distinction between IoC and Dependency Injection in his influential 2004 article *"Inversion of Control Containers and the Dependency Injection Pattern."*

---

## The Problem It Solves

In traditional procedural code, the application code calls library code. This creates a tight coupling: the caller must know the exact sequence of operations, the exact types to instantiate, and the exact control flow. When requirements change, the caller must change too. Without IoC, you end up with God classes that orchestrate everything, modules that cannot be tested in isolation, and plugin architectures that require recompilation to extend.

---

## The Principle Explained

The Hollywood Principle inverts the traditional flow of control. Instead of your code calling the framework, the framework calls your code. You provide hooks, callbacks, event handlers, or implementations of interfaces — and the framework decides when and how to invoke them.

This is the foundation of every modern framework. Express.js does not call your code procedurally; you register route handlers and Express calls them when requests arrive. React does not ask you to manage the render loop; you write components and React decides when to render them. Spring does not ask you to wire up dependencies; you declare them and Spring injects them.

The pattern works at multiple scales. At the small scale, it manifests as callbacks and event listeners. At the medium scale, it appears as Dependency Injection and the Strategy pattern. At the large scale, it becomes event-driven architecture and message bus systems where services publish events and the infrastructure routes them to subscribers.

---

## Code Examples

### BAD: Violating the Hollywood Principle — caller controls everything

```typescript
// The application manually orchestrates all steps
class OrderProcessor {
  process(order: Order): void {
    // Tight coupling: caller must know the exact sequence
    const validator = new OrderValidator();
    const isValid = validator.validate(order);

    if (!isValid) {
      const logger = new FileLogger("/var/log/orders.log");
      logger.error(`Invalid order: ${order.id}`);
      return;
    }

    const paymentGateway = new StripePaymentGateway("sk_live_xxx");
    const paymentResult = paymentGateway.charge(order.total);

    if (paymentResult.success) {
      const emailService = new SmtpEmailService("smtp.example.com");
      emailService.send(order.customerEmail, "Order confirmed!");

      const inventoryService = new InventoryService();
      inventoryService.decrementStock(order.items);

      const analyticsService = new GoogleAnalytics("UA-XXX");
      analyticsService.trackPurchase(order);
    }
  }
}

// Cannot test without real Stripe, SMTP, file system, analytics
// Cannot add new steps without modifying this class
// Cannot reorder steps without rewriting the method
```

### GOOD: Applying the Hollywood Principle — framework calls your code

```typescript
// Define contracts (ports) — your code provides implementations
interface OrderValidator {
  validate(order: Order): ValidationResult;
}

interface PaymentGateway {
  charge(amount: number, currency: string): Promise<PaymentResult>;
}

interface OrderEventHandler {
  handle(event: OrderEvent): Promise<void>;
}

// The framework orchestrates; your code plugs in
class OrderProcessor {
  constructor(
    private readonly validator: OrderValidator,
    private readonly paymentGateway: PaymentGateway,
    private readonly eventBus: EventBus
  ) {}

  async process(order: Order): Promise<OrderResult> {
    const validation = this.validator.validate(order);
    if (!validation.isValid) {
      await this.eventBus.publish({
        type: "order.validation.failed",
        payload: { orderId: order.id, errors: validation.errors },
      });
      return { success: false, errors: validation.errors };
    }

    const payment = await this.paymentGateway.charge(
      order.total,
      order.currency
    );

    if (payment.success) {
      // Publish event — framework calls handlers
      await this.eventBus.publish({
        type: "order.completed",
        payload: { order, paymentId: payment.id },
      });
    }

    return { success: payment.success };
  }
}

// Handlers are registered independently — Hollywood style
class EmailNotificationHandler implements OrderEventHandler {
  constructor(private readonly emailService: EmailService) {}

  async handle(event: OrderEvent): Promise<void> {
    if (event.type === "order.completed") {
      await this.emailService.sendOrderConfirmation(event.payload.order);
    }
  }
}

class InventoryHandler implements OrderEventHandler {
  constructor(private readonly inventory: InventoryService) {}

  async handle(event: OrderEvent): Promise<void> {
    if (event.type === "order.completed") {
      await this.inventory.decrementStock(event.payload.order.items);
    }
  }
}

// Wiring happens at composition root — add new handlers without changing processor
const eventBus = new EventBus();
eventBus.subscribe("order.completed", new EmailNotificationHandler(emailSvc));
eventBus.subscribe("order.completed", new InventoryHandler(inventorySvc));
eventBus.subscribe("order.completed", new AnalyticsHandler(analyticsSvc));
```

---

## Alternatives & Related Principles

| Approach | Relationship |
|---|---|
| **Dependency Injection** | The most common implementation of IoC. Instead of creating dependencies, you receive them. DI is a specific technique; the Hollywood Principle is the broader concept. |
| **Service Locator** | An alternative to DI where components ask a registry for their dependencies. Still inverts creation, but the component actively pulls rather than passively receives. Considered an anti-pattern by many because it hides dependencies. |
| **Event-Driven Architecture** | The Hollywood Principle at the system level. Services publish events and subscribers react — no service calls another directly. |
| **Template Method Pattern** | A class-level Hollywood Principle: the base class defines the algorithm skeleton and calls abstract methods that subclasses implement. |
| **Strategy Pattern** | Behavior is injected as an interchangeable algorithm, letting the framework call the right strategy at runtime. |
| **Plugin Architecture** | The host application defines extension points; plugins register themselves and the host calls them at appropriate moments. |

---

## When NOT to Apply

- **Simple scripts**: A 50-line utility script does not benefit from IoC containers. Direct instantiation is clearer.
- **Performance-critical inner loops**: Indirection through interfaces and event buses adds overhead. In hot paths, direct calls may be necessary.
- **When it obscures flow**: Over-applying IoC can make it impossible to follow the execution path. If understanding "what happens when an order is placed" requires reading 15 files and tracing through 3 event buses, you have gone too far.
- **Small teams, small codebases**: The organizational benefits of IoC (independent deployment, independent testing) have diminishing returns when one person can hold the entire system in their head.

---

## Tensions & Trade-offs

- **Flexibility vs. Readability**: IoC makes code flexible and extensible but harder to trace. `grep` for method calls fails when the call goes through an event bus.
- **Testability vs. Debuggability**: DI makes unit testing trivial but stack traces become walls of proxy/container calls.
- **Decoupling vs. Implicit coupling**: Events decouple sender and receiver but create invisible dependencies. Removing a handler has no compiler error — the feature silently stops working.
- **Configuration complexity**: IoC containers require configuration (XML, annotations, or code). This configuration is itself a source of bugs.

---

## Real-World Consequences

**Adherence example**: The Spring Framework's entire value proposition is the Hollywood Principle. Developers define beans and configuration; Spring wires them together and calls lifecycle methods. This has enabled a massive ecosystem of interchangeable components (swap Hibernate for jOOQ, swap MySQL for PostgreSQL) with minimal application code changes.

**Over-application example**: A team used an event bus for all internal communication within a single microservice. A simple "create user" operation published 7 events across 12 handlers. Debugging a registration bug required tracing through all 12 handlers to find which one failed. They simplified by keeping events for cross-service communication and using direct method calls within a service.

---

## Key Quotes

> "Don't call us, we'll call you." — the eponymous Hollywood casting analogy

> "One important characteristic of a framework is that the methods defined by the user to tailor the framework will often be called from within the framework itself, rather than from the user's application code." — Ralph Johnson & Brian Foote, 1988

> "The question is: what aspect of control are they inverting? [...] the inversion is about how they look up a plugin implementation." — Martin Fowler, 2004

---

## Further Reading

- Fowler, M. — [Inversion of Control Containers and the Dependency Injection Pattern](https://martinfowler.com/articles/injection.html) (2004)
- Johnson, R., Foote, B. — *Designing Reusable Classes* (1988)
- Gamma, E., Helm, R., Johnson, R., Vlissides, J. — *Design Patterns: Elements of Reusable Object-Oriented Software* (1994), Template Method and Strategy patterns
- Seemann, M. — *Dependency Injection: Principles, Practices, and Patterns* (2019)
- Sweet, R. — *The Mesa Programming Environment* (1985)
