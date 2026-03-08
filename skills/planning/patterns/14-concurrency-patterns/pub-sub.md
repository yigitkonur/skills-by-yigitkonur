# Publish/Subscribe (Pub/Sub)

**Decouple publishers from subscribers through topic-based message routing. Publishers do not know who listens; subscribers do not know who publishes.**

---

## Origin / History

The publish/subscribe pattern emerged from early event-driven systems in the 1980s. The TIBCO Rendezvous messaging system (1985) was one of the first commercial implementations. The Observer pattern (GoF, 1994) codified the in-process version. Java Message Service (JMS, 1998) standardized enterprise messaging including pub/sub topics.

Modern distributed pub/sub systems include Apache Kafka (LinkedIn, 2011), Google Cloud Pub/Sub (2015), AWS SNS (2010), and Redis Pub/Sub (2010). In-process implementations are ubiquitous: Node.js EventEmitter, browser DOM events, React's state management (Redux dispatch), and RxJS Subjects. The pattern's popularity stems from its ability to decouple systems while enabling real-time data flow.

---

## The Problem It Solves

Direct coupling between components creates a dependency web. If Service A needs to notify Services B, C, and D when an event occurs, Service A must know about all three — their APIs, availability, and error handling. Adding Service E requires modifying Service A. If Service C is slow, it slows Service A.

Pub/sub eliminates this coupling. Service A publishes an event to a topic. Services B, C, D, and E subscribe independently. Service A does not know or care how many subscribers exist. Each subscriber processes events at its own pace. New subscribers are added without modifying the publisher. Slow subscribers do not affect the publisher or each other.

The result is a system where components evolve independently, new features are added by adding subscribers, and the blast radius of failures is contained — a crashed subscriber does not affect the publisher or other subscribers.

---

## The Principle Explained

Pub/sub has three concepts: publishers produce messages on named topics (or channels), the message broker routes messages to all subscribers of that topic, and subscribers consume messages from their subscribed topics. The broker is the intermediary that decouples publishers from subscribers.

Fan-out is the defining characteristic: one published message is delivered to all subscribers. This distinguishes pub/sub from producer-consumer (where each message goes to exactly one consumer). Fan-out enables use cases like audit logging, analytics, cache invalidation, and notification — where multiple systems need to react to the same event.

Delivery guarantees vary by implementation. In-process EventEmitter provides synchronous delivery within the process. Redis Pub/Sub provides at-most-once delivery (messages are lost if no subscriber is connected). Kafka provides at-least-once delivery with consumer offsets and replay capability. Google Cloud Pub/Sub provides at-least-once with acknowledgment and dead-letter queues. The choice of delivery guarantee determines the reliability characteristics of the system.

---

## Code Examples

### BAD: Direct coupling — publisher must know all consumers

```typescript
// Order service knows about every downstream system
class OrderService {
  constructor(
    private inventoryService: InventoryService,
    private emailService: EmailService,
    private analyticsService: AnalyticsService,
    private loyaltyService: LoyaltyService,
    // Adding a new service means modifying this constructor
  ) {}

  async placeOrder(order: Order): Promise<void> {
    await this.saveOrder(order);

    // Tight coupling: knows about every consumer, handles their errors
    try { await this.inventoryService.reserve(order.items); } catch (e) { /* ... */ }
    try { await this.emailService.sendConfirmation(order); } catch (e) { /* ... */ }
    try { await this.analyticsService.trackPurchase(order); } catch (e) { /* ... */ }
    try { await this.loyaltyService.addPoints(order); } catch (e) { /* ... */ }
    // Each new consumer adds another try/catch block here
  }
}
```

### GOOD: Pub/sub — publisher is decoupled from all consumers

```typescript
// Type-safe event definitions
interface EventMap {
  "order.placed": { orderId: string; customerId: string; items: OrderItem[]; total: number };
  "order.shipped": { orderId: string; trackingNumber: string };
  "order.cancelled": { orderId: string; reason: string };
  "user.registered": { userId: string; email: string };
}

// In-process type-safe event bus
class EventBus {
  private subscribers = new Map<string, Array<(data: unknown) => Promise<void>>>();

  subscribe<K extends keyof EventMap>(
    event: K,
    handler: (data: EventMap[K]) => Promise<void>,
  ): () => void {
    const handlers = this.subscribers.get(event) ?? [];
    handlers.push(handler as (data: unknown) => Promise<void>);
    this.subscribers.set(event, handlers);

    // Return unsubscribe function
    return () => {
      const current = this.subscribers.get(event) ?? [];
      this.subscribers.set(
        event,
        current.filter((h) => h !== handler),
      );
    };
  }

  async publish<K extends keyof EventMap>(
    event: K,
    data: EventMap[K],
  ): Promise<void> {
    const handlers = this.subscribers.get(event) ?? [];
    // Fan-out: deliver to all subscribers
    const results = await Promise.allSettled(
      handlers.map((handler) => handler(data)),
    );
    // Log failures but do not let one subscriber affect others
    for (const result of results) {
      if (result.status === "rejected") {
        console.error(`Subscriber failed for ${String(event)}:`, result.reason);
      }
    }
  }
}

// Usage: publisher knows nothing about subscribers
const bus = new EventBus();

class OrderService {
  constructor(private eventBus: EventBus) {}

  async placeOrder(order: Order): Promise<void> {
    await this.saveOrder(order);
    // Publish once — all subscribers receive it
    await this.eventBus.publish("order.placed", {
      orderId: order.id,
      customerId: order.customerId,
      items: order.items,
      total: order.total,
    });
  }
}

// Subscribers register independently — no changes to OrderService
bus.subscribe("order.placed", async (data) => {
  await reserveInventory(data.items);
});

bus.subscribe("order.placed", async (data) => {
  await sendConfirmationEmail(data.customerId, data.orderId);
});

bus.subscribe("order.placed", async (data) => {
  await trackPurchaseAnalytics(data);
});

// Adding a new subscriber: zero changes to the publisher
bus.subscribe("order.placed", async (data) => {
  await addLoyaltyPoints(data.customerId, data.total);
});
```

### Distributed pub/sub with Redis

```typescript
import Redis from "ioredis";

const publisher = new Redis();
const subscriber = new Redis();

// Publisher: any service can publish
async function publishOrderEvent(event: EventMap["order.placed"]): Promise<void> {
  await publisher.publish("order.placed", JSON.stringify(event));
}

// Subscriber: independent service subscribes
subscriber.subscribe("order.placed", "order.shipped");

subscriber.on("message", async (channel: string, message: string) => {
  const data = JSON.parse(message);
  switch (channel) {
    case "order.placed":
      await handleOrderPlaced(data);
      break;
    case "order.shipped":
      await handleOrderShipped(data);
      break;
  }
});

// Warning: Redis Pub/Sub is fire-and-forget
// If no subscriber is connected, the message is lost
// For durability, use Redis Streams or Kafka instead
```

### Kafka-style pub/sub with consumer groups

```typescript
import { Kafka, EachMessagePayload } from "kafkajs";

const kafka = new Kafka({ clientId: "order-service", brokers: ["localhost:9092"] });

// Producer
const producer = kafka.producer();
await producer.connect();

async function publishEvent(topic: string, event: unknown): Promise<void> {
  await producer.send({
    topic,
    messages: [{ value: JSON.stringify(event) }],
  });
}

// Consumer — part of a consumer group for load balancing
const consumer = kafka.consumer({ groupId: "notification-service" });
await consumer.connect();
await consumer.subscribe({ topic: "order.placed", fromBeginning: false });

await consumer.run({
  eachMessage: async ({ topic, partition, message }: EachMessagePayload) => {
    const event = JSON.parse(message.value!.toString());
    await processEvent(event);
    // Kafka auto-commits offset — at-least-once delivery
  },
});

// Multiple consumer groups receive the same message (fan-out)
// Multiple consumers in the same group share the load (work distribution)
```

---

## Alternatives & Related Approaches

| Approach | Trade-off |
|---|---|
| **Direct coupling (function calls, HTTP)** | Simple, synchronous, easy to debug. But creates dependency chains and cascade failures. |
| **Request/Response (REST, gRPC)** | Bidirectional communication with immediate response. But couples caller to callee's availability and latency. |
| **Observer pattern (in-process)** | Lightweight pub/sub within a process. No serialization, no network. But does not cross process boundaries. |
| **Webhooks** | HTTP-based pub/sub. Publisher calls subscriber's URL. Simple but requires subscriber to expose an endpoint and handle retries. |
| **Polling** | Subscriber periodically checks for new data. Simple but wasteful and introduces latency equal to the polling interval. |
| **Server-Sent Events / WebSockets** | Real-time push from server to client. Good for browser-to-server pub/sub. Not designed for service-to-service communication. |

---

## When NOT to Apply

- **When you need a response**: Pub/sub is fire-and-forget. If the publisher needs a result from the subscriber, use request/response (HTTP, gRPC).
- **When ordering matters globally**: Pub/sub systems generally guarantee ordering per partition/topic, not globally. If you need strict global ordering, a single-partition topic or a different approach is needed.
- **Simple two-component systems**: If Service A only talks to Service B, pub/sub adds a broker dependency for no benefit. Direct calls are simpler.
- **When exactly-once processing is required**: Most pub/sub systems provide at-least-once delivery. Exactly-once requires idempotent subscribers or transactional outbox patterns.

---

## Tensions & Trade-offs

- **Decoupling vs. Observability**: Pub/sub makes the system flexible but harder to trace. "What happens when an order is placed?" requires searching all subscribers of the topic, which might span multiple codebases.
- **Fan-out vs. Resource usage**: Each subscriber processes every message. 10 subscribers means 10x the processing. Fan-out amplifies both value and cost.
- **At-most-once vs. At-least-once**: Redis Pub/Sub is at-most-once (fast but lossy). Kafka is at-least-once (durable but requires idempotent consumers). Neither is "free."
- **Schema evolution**: When the event schema changes, all subscribers must be updated. Without a schema registry, this coordination is error-prone.

---

## Real-World Consequences

**Microservices event-driven architecture**: Netflix, Uber, and LinkedIn use Kafka-based pub/sub as the backbone of their microservices communication. New features are built by subscribing to existing event topics without modifying the publishing services. This enabled Netflix to add personalization, A/B testing, and analytics features independently.

**Cache invalidation via pub/sub**: A CDN company uses Redis Pub/Sub to broadcast cache invalidation events across hundreds of edge servers. When content is updated, a single publish invalidates the cache globally within milliseconds — no polling, no TTL-based staleness.

**Debugging nightmare**: A large e-commerce platform experienced a bug where customer emails were sent twice. The cause: two different services subscribed to the same "order.placed" topic, and both sent emails (one was a legacy subscriber nobody knew about). The lesson: maintain a registry of subscribers and audit it regularly.

---

## Further Reading

- [Gregor Hohpe — Enterprise Integration Patterns: Publish-Subscribe Channel](https://www.enterpriseintegrationpatterns.com/patterns/messaging/PublishSubscribeChannel.html)
- [Apache Kafka Documentation — Topics and Partitions](https://kafka.apache.org/documentation/)
- [Redis Pub/Sub Documentation](https://redis.io/docs/manual/pubsub/)
- [Google Cloud Pub/Sub Documentation](https://cloud.google.com/pubsub/docs/overview)
- [Martin Kleppmann — Designing Data-Intensive Applications, Chapter 11](https://dataintensive.net/)
