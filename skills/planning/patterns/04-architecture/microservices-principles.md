# Microservices Principles

**Decompose systems into independently deployable services, each owning a single business capability.**

---

## Origin

The term "microservices" was first used at a software architecture workshop near Venice in 2011, though the practices had been evolving at companies like Amazon, Netflix, and eBay for years before. James Lewis and Martin Fowler published the definitive description in their 2014 article *"Microservices: A Definition of This New Architectural Term."* Sam Newman's *"Building Microservices"* (2015, 2nd edition 2021) became the standard reference. The architecture emerged as a reaction to monolithic deployments that had become too large to change, test, or deploy safely.

---

## The Problem It Solves

Monolithic applications become victims of their own success. As the codebase grows, build times increase, deployments become risky (a bug in the checkout module takes down the entire application), and teams step on each other's code. Scaling is all-or-nothing — you cannot scale just the search functionality without scaling the entire monolith. Technology choices are locked in — the monolith is in Java, so everything must be in Java. Conway's Law takes hold: the organization's communication structure forces a coupled architecture.

---

## The Principle Explained

Microservices architecture decomposes a system into small, autonomous services that communicate over network protocols. Each service owns its data, deploys independently, and is built around a single business capability. The key principles are:

**Single Responsibility at the service level**: Each service does one thing well. An Order Service manages orders. A Payment Service handles payments. They do not share databases, and they do not share domain logic. This is DDD's bounded context applied at the deployment boundary.

**Independent deployability**: The defining characteristic. You must be able to deploy the Order Service without deploying the Payment Service. This requires well-defined contracts (APIs), backward-compatible changes, and independent data stores. If deploying Service A requires deploying Service B, you have a distributed monolith, not microservices.

**Decentralized governance**: Each team chooses its own technology stack, database, and deployment strategy. The Order Service might use PostgreSQL; the Search Service might use Elasticsearch. The teams agree on communication protocols (REST, gRPC, events) but not on internal implementation.

---

## Code Examples

### BAD: Distributed monolith — microservices without the principles

```typescript
// "Order Service" — but it directly calls other services synchronously
// and shares a database with them
class OrderController {
  async createOrder(req: Request, res: Response): Promise<void> {
    const order = req.body;

    // Synchronous call — Order Service is coupled to User Service
    const user = await fetch(`http://user-service/users/${order.userId}`);
    if (!user.ok) {
      res.status(400).json({ error: "Invalid user" });
      return;
    }

    // Synchronous call — coupled to Inventory Service
    for (const item of order.items) {
      const stock = await fetch(
        `http://inventory-service/stock/${item.productId}`
      );
      const stockData = await stock.json();
      if (stockData.quantity < item.quantity) {
        res.status(400).json({ error: `Insufficient stock for ${item.productId}` });
        return;
      }
    }

    // Shared database! — violates data ownership
    await sharedDb.query(
      "INSERT INTO orders (user_id, items, total) VALUES ($1, $2, $3)",
      [order.userId, JSON.stringify(order.items), order.total]
    );

    // Synchronous call — if payment service is down, order creation fails
    const payment = await fetch("http://payment-service/charge", {
      method: "POST",
      body: JSON.stringify({ amount: order.total, userId: order.userId }),
    });

    if (!payment.ok) {
      // No compensation — order is saved but payment failed
      res.status(500).json({ error: "Payment failed" });
      return;
    }

    res.status(201).json({ orderId: "xxx" });
  }
}
```

### GOOD: Properly bounded microservice with async communication

```typescript
// ============================================
// ORDER SERVICE — owns its domain and data
// ============================================

// Domain model — internal to this service
class Order {
  private status: OrderStatus = "pending";
  private readonly items: OrderItem[] = [];

  constructor(
    readonly id: string,
    readonly customerId: string
  ) {}

  addItem(productId: string, quantity: number, unitPrice: number): void {
    if (this.status !== "pending") {
      throw new Error("Cannot modify a non-pending order");
    }
    this.items.push(new OrderItem(productId, quantity, unitPrice));
  }

  get total(): number {
    return this.items.reduce((sum, item) => sum + item.lineTotal, 0);
  }

  confirm(): OrderConfirmedEvent {
    if (this.items.length === 0) throw new Error("Cannot confirm empty order");
    this.status = "confirmed";
    return new OrderConfirmedEvent(this.id, this.customerId, this.total, this.items);
  }

  markPaid(): void { this.status = "paid"; }
  markFailed(): void { this.status = "failed"; }
}

// API contract — what this service exposes
interface CreateOrderRequest {
  customerId: string;
  items: Array<{ productId: string; quantity: number; unitPrice: number }>;
}

interface OrderResponse {
  id: string;
  customerId: string;
  total: number;
  status: string;
}

// Controller — thin HTTP adapter
class OrderController {
  constructor(
    private readonly orderService: OrderApplicationService
  ) {}

  async createOrder(req: Request, res: Response): Promise<void> {
    try {
      const result = await this.orderService.createOrder(req.body);
      res.status(201).json(result);
    } catch (error) {
      if (error instanceof ValidationError) {
        res.status(400).json({ error: error.message });
      } else {
        res.status(500).json({ error: "Internal server error" });
      }
    }
  }
}

// Application service — orchestrates the use case
class OrderApplicationService {
  constructor(
    private readonly orderRepo: OrderRepository,
    private readonly eventPublisher: EventPublisher // Async communication
  ) {}

  async createOrder(input: CreateOrderRequest): Promise<OrderResponse> {
    const order = new Order(generateId(), input.customerId);

    for (const item of input.items) {
      order.addItem(item.productId, item.quantity, item.unitPrice);
    }

    const event = order.confirm();

    // Save to ORDER SERVICE's own database
    await this.orderRepo.save(order);

    // Publish event — other services react asynchronously
    // No synchronous coupling to payment, inventory, or notification services
    await this.eventPublisher.publish("order.confirmed", event);

    return this.toResponse(order);
  }

  // React to events from other services
  async handlePaymentCompleted(event: PaymentCompletedEvent): Promise<void> {
    const order = await this.orderRepo.findById(event.orderId);
    if (!order) return; // Idempotency: ignore unknown orders

    order.markPaid();
    await this.orderRepo.save(order);
    await this.eventPublisher.publish("order.paid", {
      orderId: order.id,
      customerId: order.customerId,
    });
  }

  async handlePaymentFailed(event: PaymentFailedEvent): Promise<void> {
    const order = await this.orderRepo.findById(event.orderId);
    if (!order) return;

    order.markFailed();
    await this.orderRepo.save(order);
    await this.eventPublisher.publish("order.failed", {
      orderId: order.id,
      reason: event.reason,
    });
  }

  private toResponse(order: Order): OrderResponse {
    return { id: order.id, customerId: order.customerId, total: order.total, status: "confirmed" };
  }
}

// Event publisher interface — this service does not know
// whether Kafka, RabbitMQ, or SQS is underneath
interface EventPublisher {
  publish(topic: string, event: unknown): Promise<void>;
}
```

---

## Alternatives & Related Principles

| Approach | Relationship |
|---|---|
| **Modular Monolith** | Same logical boundaries as microservices but deployed as a single unit. Provides many DDD benefits (bounded contexts, independent modules) without network overhead. Often the right starting point before extracting microservices. |
| **Service-Oriented Architecture (SOA)** | The predecessor. SOA used heavyweight protocols (SOAP, ESB) and shared data schemas. Microservices favor lightweight protocols and independent data stores. |
| **Serverless / FaaS** | Decomposes further — individual functions instead of services. Trades operational complexity (no servers) for cold start latency and vendor lock-in. |
| **Monolith** | The simplest deployment model. Right for most small-to-medium applications. Becomes painful at scale, both technical and organizational. |

---

## When NOT to Apply

- **Small teams (fewer than 8-10 developers)**: The operational overhead of microservices (service discovery, distributed tracing, API gateways, container orchestration) exceeds the benefits for small teams.
- **Unclear domain boundaries**: If you do not know where to draw service boundaries, you will draw them wrong. Start with a modular monolith, learn the domain, then extract services.
- **Startups finding product-market fit**: You need speed of iteration, not deployment independence. A monolith is faster to change.
- **When you cannot invest in infrastructure**: Microservices require CI/CD pipelines per service, container orchestration, observability tooling, and API management. Without this investment, microservices become an operational nightmare.

---

## Tensions & Trade-offs

- **Autonomy vs. Consistency**: Independent data stores mean eventual consistency. Distributed transactions (Sagas) are complex to implement correctly.
- **Deployment independence vs. Integration testing**: If services are truly independent, how do you test the end-to-end flow? Contract testing (Pact) and consumer-driven contracts help but do not fully replace integration tests.
- **Team autonomy vs. Standards**: If every team chooses a different language, framework, and database, cross-team mobility suffers and shared tooling becomes impossible.
- **Network overhead**: Every service call is a network call — serialization, latency, failure modes. What was a function call in the monolith is now an HTTP request.

---

## Real-World Consequences

**Adherence example**: Netflix decomposed its monolithic DVD service into hundreds of microservices. Each team owns a service end-to-end (you build it, you run it). This enabled them to scale to 200+ million subscribers, deploy thousands of times per day, and survive AWS region failures through service-level resilience.

**Premature adoption example**: A 5-person startup built 12 microservices for a todo application. They spent 80% of their time on infrastructure (Kubernetes, service mesh, distributed tracing) and 20% on features. Their competitor, with a single Rails monolith, shipped features 10x faster and won the market.

---

## Key Quotes

> "Microservices is a label, not a description." — Martin Fowler

> "If you can't build a well-structured monolith, what makes you think microservices is the answer?" — Simon Brown

> "The first rule of microservices: don't start with microservices." — Sam Newman paraphrasing common wisdom

> "You build it, you run it." — Werner Vogels, Amazon CTO

---

## Further Reading

- Newman, S. — *Building Microservices* (2nd edition, 2021)
- Lewis, J., Fowler, M. — [Microservices](https://martinfowler.com/articles/microservices.html) (2014)
- Richardson, C. — *Microservices Patterns* (2018)
- Fowler, M. — [MonolithFirst](https://martinfowler.com/bliki/MonolithFirst.html) (2015)
- Nygard, M. — *Release It!* (2018), on stability patterns for distributed systems
- Kleppmann, M. — *Designing Data-Intensive Applications* (2017), on distributed data consistency
