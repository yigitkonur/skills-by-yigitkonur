# Event-Driven Architecture (EDA)

**Build systems where events are first-class citizens — components communicate by producing and reacting to events.**

---

## Origin

Event-driven architecture has deep roots in computer science, tracing back to the observer pattern and event-loop systems of the 1970s and 1980s. In enterprise software, it was formalized through the work of Gregor Hohpe and Bobby Woolf in *"Enterprise Integration Patterns"* (2003). Martin Fowler's articles on Event Sourcing and CQRS (2005-2011) further refined the patterns. The modern resurgence was driven by the rise of Apache Kafka (open-sourced by LinkedIn in 2011), which made durable, high-throughput event streaming practical. Today, EDA is foundational to microservices architectures and is championed by practitioners like Ben Stopford (*Designing Event-Driven Systems*, 2018).

---

## The Problem It Solves

In request/response architectures, the caller must know about the callee. When the Order Service needs to trigger inventory deduction, email notification, analytics tracking, and loyalty point accrual, it must call each service directly. Adding a new reaction (fraud detection) requires modifying the Order Service. The result is a system where every new feature tightens the coupling web, deployments become coordinated affairs, and a single slow downstream service blocks the entire chain.

---

## The Principle Explained

Event-Driven Architecture decouples producers from consumers. When something significant happens in the system (an order is placed, a payment is processed, a user signs up), the component that detected the event publishes it to a channel. Other components subscribe to channels they care about and react independently.

There are three main patterns within EDA. **Event Notification** is the simplest: a service publishes a lightweight event ("OrderPlaced, orderId: 123") and consumers fetch any additional data they need. **Event-Carried State Transfer** includes the full payload in the event ("OrderPlaced, with full order details"), reducing the need for consumers to call back. **Event Sourcing** stores the sequence of events as the source of truth, deriving current state by replaying them.

The key benefit is **extensibility without modification**. Adding a new reaction to "OrderPlaced" means deploying a new consumer — the Order Service is not changed or even aware of the new consumer. This enables independent team velocity, selective scaling (scale only the consumers that are slow), and temporal decoupling (consumers can process events at their own pace, including during downtime with replay).

---

## Code Examples

### BAD: Direct coupling — every new reaction requires changing the producer

```typescript
class OrderService {
  constructor(
    private readonly inventoryService: InventoryService,
    private readonly emailService: EmailService,
    private readonly analyticsService: AnalyticsService,
    private readonly loyaltyService: LoyaltyService,
    // Every new downstream service = new constructor parameter
    // and new deployment coupling
  ) {}

  async placeOrder(order: Order): Promise<void> {
    await this.orderRepo.save(order);

    // Synchronous chain — if any service is slow or down, order placement fails
    await this.inventoryService.decrementStock(order.items);
    await this.emailService.sendConfirmation(order.customerEmail, order);
    await this.analyticsService.trackPurchase(order);
    await this.loyaltyService.awardPoints(order.customerId, order.total);

    // Adding fraud detection? Modify this class again.
    // Adding warehouse routing? Modify this class again.
    // Adding partner notification? Modify this class again.
  }
}
```

### GOOD: Event-driven — producer publishes, consumers react independently

```typescript
// ============================================
// EVENTS — shared contract (often in a separate package)
// ============================================
interface DomainEvent {
  readonly eventId: string;
  readonly eventType: string;
  readonly occurredAt: string;
  readonly aggregateId: string;
}

interface OrderPlacedEvent extends DomainEvent {
  eventType: "order.placed";
  payload: {
    orderId: string;
    customerId: string;
    items: Array<{ productId: string; quantity: number; unitPrice: number }>;
    total: number;
    currency: string;
    shippingAddress: Address;
  };
}

interface OrderCancelledEvent extends DomainEvent {
  eventType: "order.cancelled";
  payload: {
    orderId: string;
    reason: string;
    refundAmount: number;
  };
}

// ============================================
// PRODUCER — publishes events, knows nothing about consumers
// ============================================
class OrderService {
  constructor(
    private readonly orderRepo: OrderRepository,
    private readonly eventPublisher: EventPublisher
  ) {}

  async placeOrder(command: PlaceOrderCommand): Promise<string> {
    const order = Order.create(command.customerId, command.items);
    await this.orderRepo.save(order);

    // Publish and forget — the order service's job is done
    await this.eventPublisher.publish<OrderPlacedEvent>({
      eventId: generateId(),
      eventType: "order.placed",
      occurredAt: new Date().toISOString(),
      aggregateId: order.id,
      payload: {
        orderId: order.id,
        customerId: order.customerId,
        items: order.items,
        total: order.total,
        currency: order.currency,
        shippingAddress: order.shippingAddress,
      },
    });

    return order.id;
  }
}

// ============================================
// CONSUMERS — deployed independently, react to events
// ============================================

// Inventory consumer — decrements stock
class InventoryEventHandler {
  constructor(private readonly inventory: InventoryRepository) {}

  async handleOrderPlaced(event: OrderPlacedEvent): Promise<void> {
    for (const item of event.payload.items) {
      await this.inventory.reserveStock(item.productId, item.quantity);
    }
  }

  async handleOrderCancelled(event: OrderCancelledEvent): Promise<void> {
    const order = await this.getOrderDetails(event.payload.orderId);
    for (const item of order.items) {
      await this.inventory.releaseStock(item.productId, item.quantity);
    }
  }
}

// Notification consumer — sends emails
class NotificationEventHandler {
  constructor(private readonly emailService: EmailService) {}

  async handleOrderPlaced(event: OrderPlacedEvent): Promise<void> {
    await this.emailService.sendOrderConfirmation({
      customerId: event.payload.customerId,
      orderId: event.payload.orderId,
      total: event.payload.total,
    });
  }
}

// Analytics consumer — tracks metrics (can be added without touching OrderService)
class AnalyticsEventHandler {
  constructor(private readonly analytics: AnalyticsClient) {}

  async handleOrderPlaced(event: OrderPlacedEvent): Promise<void> {
    await this.analytics.track("purchase", {
      orderId: event.payload.orderId,
      total: event.payload.total,
      itemCount: event.payload.items.length,
    });
  }
}

// ============================================
// INFRASTRUCTURE — event bus / message broker adapter
// ============================================
interface EventPublisher {
  publish<T extends DomainEvent>(event: T): Promise<void>;
}

interface EventSubscriber {
  subscribe<T extends DomainEvent>(
    eventType: string,
    handler: (event: T) => Promise<void>
  ): void;
}

// Kafka adapter
class KafkaEventPublisher implements EventPublisher {
  constructor(private readonly producer: KafkaProducer) {}

  async publish<T extends DomainEvent>(event: T): Promise<void> {
    await this.producer.send({
      topic: event.eventType,
      messages: [{
        key: event.aggregateId,
        value: JSON.stringify(event),
        headers: { eventId: event.eventId },
      }],
    });
  }
}

// Consumer wiring — typically in a separate deployment
function startInventoryConsumer(): void {
  const subscriber = new KafkaEventSubscriber(/* config */);
  const handler = new InventoryEventHandler(inventoryRepo);

  subscriber.subscribe("order.placed", (e) => handler.handleOrderPlaced(e));
  subscriber.subscribe("order.cancelled", (e) => handler.handleOrderCancelled(e));
}
```

---

## Alternatives & Related Principles

| Approach | Relationship |
|---|---|
| **Request/Response (REST, gRPC)** | Synchronous, point-to-point communication. Simpler to reason about but creates temporal coupling. Use for queries; use events for commands that trigger reactions. |
| **Message Queues (point-to-point)** | Messages are consumed by exactly one consumer. Events are consumed by all interested subscribers. Queues are for work distribution; events are for notification. |
| **Polling** | Consumers periodically check for changes. Simpler infrastructure but introduces latency, wastes resources, and does not scale. |
| **Webhooks** | Push-based notifications over HTTP. Simpler than a full event bus but lacks durability, replay, and ordering guarantees. |
| **Change Data Capture (CDC)** | Captures database changes as events (Debezium, DynamoDB Streams). Produces events without modifying application code. Useful for legacy integration. |

---

## When NOT to Apply

- **Simple request/response flows**: If User A creates a record and expects an immediate response with the created record, a synchronous API call is simpler and more appropriate.
- **When ordering is critical and complex**: Events may arrive out of order. If strict ordering across multiple event types is required, the infrastructure and logic complexity may not be worth it.
- **Small systems with few integrations**: The overhead of a message broker (Kafka, RabbitMQ), consumer groups, dead-letter queues, and retry logic is significant for a system with three services.
- **When debugging simplicity matters more than decoupling**: Tracing an event through five consumers across three services requires distributed tracing infrastructure. A synchronous call stack is debuggable with a single breakpoint.

---

## Tensions & Trade-offs

- **Eventual consistency**: Events are processed asynchronously. The inventory count may not reflect the latest order for seconds (or minutes). This requires UI patterns (optimistic updates, polling) and business process accommodation.
- **Exactly-once delivery**: Most message brokers guarantee at-least-once delivery. Consumers must be idempotent — processing the same event twice must produce the same result.
- **Event schema evolution**: Once published, event schemas are contracts. Adding a required field is a breaking change. Use versioning, optional fields, and schema registries.
- **Debugging complexity**: "What happens when an order is placed?" requires reading the event schema, finding all subscribers, and understanding each consumer's logic. No single call stack shows the full picture.
- **Operational overhead**: Kafka clusters, consumer lag monitoring, dead-letter queues, retry policies, schema registries — the infrastructure investment is substantial.

---

## Real-World Consequences

**Adherence example**: LinkedIn built its entire data infrastructure around Kafka and event-driven patterns. Every significant action (profile view, connection request, message sent) is an event. This enabled them to add new features (recommendations, notifications, analytics) by deploying new consumers without modifying existing services. Their system processes trillions of events per day.

**Over-application example**: A team made every internal method call within a single service go through an event bus. A "create user" operation published 8 events handled by 12 listeners within the same process. A simple null pointer exception in one listener caused a cascade of retry events that overwhelmed the bus. They reverted to direct method calls within services and reserved events for cross-service communication.

---

## Key Quotes

> "Events are both a pattern for integration and a mechanism for building systems that are resilient to change." — Gregor Hohpe

> "An event is a significant change in state." — K. Mani Chandy

> "The log is the natural data structure for handling data flow between services." — Jay Kreps, LinkedIn/Confluent

---

## Further Reading

- Hohpe, G., Woolf, B. — *Enterprise Integration Patterns* (2003)
- Stopford, B. — *Designing Event-Driven Systems* (2018, free from Confluent)
- Kleppmann, M. — *Designing Data-Intensive Applications* (2017), Chapter 11: "Stream Processing"
- Fowler, M. — [What do you mean by "Event-Driven"?](https://martinfowler.com/articles/201701-event-driven.html) (2017)
- Kreps, J. — [The Log: What every software engineer should know](https://engineering.linkedin.com/distributed-systems/log-what-every-software-engineer-should-know-about-real-time-datas-unifying) (2013)
- Richardson, C. — [Saga pattern](https://microservices.io/patterns/data/saga.html) for managing distributed transactions with events
