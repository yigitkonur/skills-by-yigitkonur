# Producer-Consumer Pattern

**Decouple work production from work consumption using queues, enabling independent scaling, backpressure, and reliable processing.**

---

## Origin / History

The producer-consumer problem is one of the oldest in computer science, first described by Edsger Dijkstra in 1965 as a synchronization problem involving bounded buffers. The original formulation focused on shared memory coordination using semaphores. Over decades, the pattern evolved from in-process thread coordination to distributed message queuing.

RabbitMQ (2007), Amazon SQS (2006), Apache Kafka (2011), and Redis Streams (2018) are all implementations of the producer-consumer pattern at the distributed systems level. In Node.js, the Streams API (readable/writable/transform streams) implements producer-consumer with built-in backpressure. The pattern is so fundamental that it appears in every system that processes work asynchronously — from operating system I/O schedulers to web server request queues to CI/CD pipelines.

---

## The Problem It Solves

When a producer generates work faster than a consumer can process it, one of three things happens: work is dropped (data loss), the producer blocks (reduced throughput), or memory fills up until the system crashes. Without explicit flow control, the default behavior in most systems is the third option.

Direct invocation — where the producer calls the consumer synchronously — creates tight coupling. The producer must wait for the consumer, the consumer cannot be scaled independently, and a slow consumer becomes a bottleneck for the entire system. If the consumer crashes, the work in progress is lost.

The producer-consumer pattern solves these problems by inserting a queue between producer and consumer. The queue absorbs bursts, enables independent scaling, provides backpressure when the consumer falls behind, and can persist work for durability. Producers and consumers can be added or removed without affecting each other.

---

## The Principle Explained

The pattern has three components: producers that create work items, a queue (buffer) that holds work items, and consumers that process work items. The queue decouples the lifecycle and rate of producers and consumers.

Backpressure is the mechanism by which a full queue signals producers to slow down. Without backpressure, a fast producer overwhelms a slow consumer. Backpressure can be implemented as blocking (producer waits for queue space), dropping (newest or oldest items are discarded), or signaling (producer receives a "slow down" notification). The choice depends on whether losing work is acceptable.

Bounded vs. unbounded buffers represent a critical design decision. An unbounded queue never rejects work but can consume unlimited memory. A bounded queue limits memory usage but must handle the "queue full" case. In production systems, bounded queues with explicit overflow policies are almost always correct — unbounded queues are a deferred out-of-memory crash.

---

## Code Examples

### BAD: Direct invocation with no buffering or flow control

```typescript
// Producer directly calls consumer — tight coupling, no buffering
async function handleWebhook(event: WebhookEvent): Promise<void> {
  // If processEvent is slow, the webhook response is slow
  // If processEvent crashes, the event is lost
  // If 1000 webhooks arrive simultaneously, 1000 processEvent calls run in parallel
  await processEvent(event);
}

async function processEvent(event: WebhookEvent): Promise<void> {
  await enrichWithUserData(event);      // 100ms
  await updateAnalytics(event);         // 200ms
  await notifyDownstreamServices(event); // 150ms
  // Total: 450ms blocking the webhook response
}
```

### GOOD: In-process producer-consumer with bounded queue and backpressure

```typescript
interface WorkItem<T> {
  readonly data: T;
  readonly resolve: (result: void) => void;
  readonly reject: (error: Error) => void;
}

class BoundedQueue<T> {
  private queue: Array<WorkItem<T>> = [];
  private processing = false;
  private activeWorkers = 0;

  constructor(
    private readonly processor: (item: T) => Promise<void>,
    private readonly maxQueueSize: number = 1000,
    private readonly concurrency: number = 5,
  ) {}

  async enqueue(item: T): Promise<void> {
    if (this.queue.length >= this.maxQueueSize) {
      throw new Error(
        `Queue full (${this.maxQueueSize} items). Apply backpressure.`,
      );
    }

    return new Promise<void>((resolve, reject) => {
      this.queue.push({ data: item, resolve, reject });
      this.drain();
    });
  }

  get stats(): { queued: number; active: number; capacity: number } {
    return {
      queued: this.queue.length,
      active: this.activeWorkers,
      capacity: this.maxQueueSize,
    };
  }

  private async drain(): Promise<void> {
    while (this.queue.length > 0 && this.activeWorkers < this.concurrency) {
      const workItem = this.queue.shift()!;
      this.activeWorkers++;

      this.processor(workItem.data)
        .then(() => workItem.resolve())
        .catch((error) => workItem.reject(error))
        .finally(() => {
          this.activeWorkers--;
          this.drain();
        });
    }
  }
}

// Usage: webhook handler with bounded processing
const eventQueue = new BoundedQueue<WebhookEvent>(processEvent, 1000, 5);

async function handleWebhook(event: WebhookEvent): Promise<void> {
  try {
    await eventQueue.enqueue(event);
  } catch (error) {
    // Backpressure: return 429 (Too Many Requests) to the webhook sender
    throw new HttpError(429, "Service overloaded, please retry later");
  }
}
```

### Node.js Streams — built-in producer-consumer with backpressure

```typescript
import { Transform, pipeline } from "node:stream";
import { promisify } from "node:util";

const pipelineAsync = promisify(pipeline);

// Transform stream — consumes input, produces output, with automatic backpressure
class EventEnricher extends Transform {
  constructor() {
    super({ objectMode: true, highWaterMark: 16 }); // Bounded buffer of 16 items
  }

  async _transform(
    event: WebhookEvent,
    _encoding: string,
    callback: (error?: Error | null, data?: unknown) => void,
  ): Promise<void> {
    try {
      const enriched = await enrichWithUserData(event);
      callback(null, enriched);
    } catch (error) {
      callback(error instanceof Error ? error : new Error(String(error)));
    }
  }
}

// Pipeline: producer -> transform -> consumer
// Backpressure flows automatically from consumer to producer
await pipelineAsync(
  createEventStream(),     // Producer: readable stream of events
  new EventEnricher(),     // Transform: enrich each event (bounded buffer)
  createDatabaseWriter(),  // Consumer: writable stream to database
);
```

### Distributed producer-consumer with message queue

```typescript
import { SQSClient, SendMessageCommand, ReceiveMessageCommand,
  DeleteMessageCommand } from "@aws-sdk/client-sqs";

const sqs = new SQSClient({ region: "us-east-1" });
const QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/123456789/events";

// Producer: send events to SQS — fire and continue
async function produceEvent(event: WebhookEvent): Promise<void> {
  await sqs.send(new SendMessageCommand({
    QueueUrl: QUEUE_URL,
    MessageBody: JSON.stringify(event),
    MessageGroupId: event.customerId, // FIFO ordering per customer
  }));
  // Returns immediately — SQS handles durability and delivery
}

// Consumer: poll SQS and process — independent process/service
async function startConsumer(): Promise<void> {
  while (true) {
    const response = await sqs.send(new ReceiveMessageCommand({
      QueueUrl: QUEUE_URL,
      MaxNumberOfMessages: 10,
      WaitTimeSeconds: 20, // Long polling — efficient
    }));

    if (!response.Messages) continue;

    await Promise.all(
      response.Messages.map(async (message) => {
        try {
          const event: WebhookEvent = JSON.parse(message.Body!);
          await processEvent(event);
          // Acknowledge successful processing — remove from queue
          await sqs.send(new DeleteMessageCommand({
            QueueUrl: QUEUE_URL,
            ReceiptHandle: message.ReceiptHandle!,
          }));
        } catch (error) {
          // Do NOT delete — SQS will retry after visibility timeout
          console.error("Failed to process message:", error);
        }
      }),
    );
  }
}
```

---

## Alternatives & Related Approaches

| Approach | Trade-off |
|---|---|
| **Direct invocation (synchronous call)** | Simplest. No queue, no decoupling. Works when producer and consumer run at the same rate and failure is not a concern. |
| **Polling** | Consumer periodically checks for new work. Simple but wasteful (empty polls) and introduces latency (poll interval). |
| **Pub/Sub** | Similar to producer-consumer but messages go to all subscribers, not just one. Use pub/sub for broadcast, producer-consumer for work distribution. |
| **Event sourcing** | Append-only log (like Kafka) that is both a pub/sub system and a producer-consumer queue. Consumers read at their own pace. |
| **Work stealing** | Multiple consumers share a set of queues. When a consumer's queue is empty, it "steals" from another. Balances load dynamically. Used in Go's goroutine scheduler. |

---

## When NOT to Apply

- **Request/response APIs**: If the caller needs an immediate result, a queue adds unnecessary latency. Use direct invocation.
- **Low-volume systems**: If you process 10 events per minute, the complexity of a queue is not justified. Direct processing with error handling suffices.
- **When ordering is critical and complex**: While queues can preserve order (FIFO), complex ordering requirements (e.g., per-entity ordering with global transactions) make queue-based systems very difficult.
- **Real-time requirements**: Queues add latency. If processing must happen within milliseconds of production, direct invocation or in-memory pub/sub is more appropriate.

---

## Tensions & Trade-offs

- **Decoupling vs. Complexity**: Queues decouple producers from consumers, but add operational complexity — monitoring queue depth, handling dead letters, managing consumer scaling.
- **Throughput vs. Latency**: Batching messages improves throughput but increases latency for individual messages. The optimal batch size depends on the use case.
- **At-least-once vs. Exactly-once**: Most queue systems guarantee at-least-once delivery. Exactly-once requires idempotent consumers or deduplication — significant additional complexity.
- **Bounded vs. Unbounded**: Bounded queues prevent memory exhaustion but require backpressure handling. Unbounded queues are simpler but risk resource exhaustion.

---

## Real-World Consequences

**Email delivery systems**: Every large email service (SendGrid, Postmark, Mailgun) uses producer-consumer queues. The API accepts emails (producer), a queue buffers them, and workers deliver them to SMTP servers (consumers). This decoupling enables handling burst loads (Black Friday email campaigns) without dropping messages or overwhelming mail servers.

**Video transcoding pipelines**: YouTube, Netflix, and similar platforms use producer-consumer queues for video processing. When a video is uploaded (produced), it enters a queue. Transcoding workers (consumers) process it into multiple formats and resolutions. Scaling consumers independently of the upload API is essential — transcoding takes minutes while upload acknowledgment must be instant.

**The dangers of unbounded queues**: A fintech company used an unbounded in-memory queue for transaction processing. During a traffic spike, the queue grew to 2 million items, consuming 8GB of RAM, triggering an OOM kill that lost all queued transactions. Switching to a bounded queue with SQS overflow prevented recurrence.

---

## Further Reading

- [Edsger Dijkstra — Cooperating Sequential Processes (1965)](https://www.cs.utexas.edu/users/EWD/ewd01xx/EWD123.PDF)
- [RabbitMQ Tutorials — Work Queues](https://www.rabbitmq.com/tutorials/tutorial-two-javascript.html)
- [AWS SQS Developer Guide](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/)
- [Node.js Streams Documentation](https://nodejs.org/api/stream.html)
- [Martin Kleppmann — Designing Data-Intensive Applications, Chapter 11: Stream Processing](https://dataintensive.net/)
