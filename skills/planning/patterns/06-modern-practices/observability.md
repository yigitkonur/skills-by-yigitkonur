# Observability

**One-line summary:** Observability is the ability to understand a system's internal state from its external outputs -- through the three pillars of logs, metrics, and traces -- enabling you to answer questions you did not anticipate when you wrote the code.

---

## Origin

The term "observability" comes from control theory (Rudolf Kalman, 1960), where a system is observable if its internal state can be inferred from its outputs. Cindy Sridharan's *Distributed Systems Observability* (O'Reilly, 2018) brought the concept to software engineering. Google's SRE book (2016) formalized the "four golden signals" (latency, traffic, errors, saturation). OpenTelemetry (2019, merger of OpenTracing and OpenCensus) standardized instrumentation across languages. The key distinction from traditional monitoring: monitoring tells you *when* something is wrong; observability helps you understand *why*.

---

## The Problem It Solves

In distributed systems, failures are emergent. A slow response might be caused by a database lock, a downstream service timeout, a garbage collection pause, or a misconfigured load balancer. Traditional monitoring dashboards show predefined metrics -- CPU usage, error rates, response times -- but these tell you the symptom, not the cause. Without observability, debugging requires reproducing the issue locally (often impossible), adding ad-hoc logging and redeploying (too slow), or guessing and hoping (error-prone). Observability gives you the data to trace a single request through 15 services and pinpoint exactly where and why it failed.

---

## The Principle Explained

**Structured logging** replaces free-text log lines with machine-parseable events. Instead of `console.log("User login failed")`, you emit a structured event with fields: `{ event: "auth.login_failed", userId: "abc", reason: "invalid_password", ip: "1.2.3.4", timestamp: "..." }`. Structured logs can be queried, aggregated, and correlated. They are the foundation of observability because they capture the context that metrics and traces cannot.

**Metrics** are numerical measurements aggregated over time: request count, error rate, latency percentiles, queue depth, memory usage. Google's four golden signals -- latency, traffic, errors, saturation -- cover the essential health indicators for any service. Metrics are cheap to collect and store, fast to query, and ideal for dashboards and alerts. But they lack context: a spike in error rate tells you something is wrong, not which users are affected or why.

**Distributed traces** follow a single request as it flows through multiple services. Each service adds a "span" to the trace, recording what it did, how long it took, and whether it succeeded. A trace ID (correlation ID) threads through all spans, enabling you to reconstruct the full journey of a request. Traces answer the question metrics cannot: "Why did THIS specific request take 12 seconds when the p50 is 200ms?"

---

## Code Examples

### BAD: Unstructured Logging, No Correlation

```typescript
// Unstructured, unsearchable, no context
app.post("/api/orders", async (req, res) => {
  console.log("Received order request");

  try {
    console.log("Validating order...");
    const order = validateOrder(req.body);

    console.log("Processing payment...");
    await processPayment(order);

    console.log("Order created successfully"); // Which order? For whom?
    res.json({ success: true });
  } catch (err) {
    console.log("Error: " + err); // No stack trace, no context
    res.status(500).json({ error: "Internal error" });
  }
});

// In another service, no way to correlate with the above
async function processPayment(order: any): Promise<void> {
  console.log("Payment processing started");
  // If this fails, how do we connect it to the originating request?
  console.log("Payment done");
}
```

### GOOD: Structured Logging with Correlation IDs

```typescript
import { Logger } from "./observability/logger";
import { trace, SpanStatusCode, context } from "@opentelemetry/api";

interface LogContext {
  readonly traceId: string;
  readonly spanId: string;
  readonly userId?: string;
  readonly orderId?: string;
  readonly [key: string]: unknown;
}

// Structured logger that always includes trace context
class StructuredLogger {
  info(event: string, data: Record<string, unknown> = {}): void {
    const span = trace.getActiveSpan();
    const entry = {
      level: "info",
      event,
      timestamp: new Date().toISOString(),
      traceId: span?.spanContext().traceId,
      spanId: span?.spanContext().spanId,
      ...data,
    };
    process.stdout.write(JSON.stringify(entry) + "\n");
  }

  error(event: string, error: Error, data: Record<string, unknown> = {}): void {
    const span = trace.getActiveSpan();
    const entry = {
      level: "error",
      event,
      timestamp: new Date().toISOString(),
      traceId: span?.spanContext().traceId,
      spanId: span?.spanContext().spanId,
      error: { message: error.message, stack: error.stack, name: error.name },
      ...data,
    };
    process.stdout.write(JSON.stringify(entry) + "\n");
  }
}

const logger = new StructuredLogger();
const tracer = trace.getTracer("order-service");

// Request handler with full observability
app.post("/api/orders", async (req, res) => {
  const span = tracer.startSpan("http.post.create_order");

  try {
    const userId = req.authenticatedUser.id;
    span.setAttribute("user.id", userId);
    logger.info("order.create.started", { userId });

    // Validation span
    const validationSpan = tracer.startSpan("order.validate", {}, context.active());
    const order = validateOrder(req.body);
    validationSpan.end();

    span.setAttribute("order.id", order.id);
    span.setAttribute("order.item_count", order.items.length);
    span.setAttribute("order.total_cents", order.totalCents);

    // Payment span -- trace propagates to payment service automatically
    const paymentSpan = tracer.startSpan("order.process_payment", {}, context.active());
    const paymentResult = await processPayment(order);
    paymentSpan.setAttribute("payment.provider", paymentResult.provider);
    paymentSpan.setAttribute("payment.transaction_id", paymentResult.transactionId);
    paymentSpan.end();

    logger.info("order.create.succeeded", {
      userId,
      orderId: order.id,
      totalCents: order.totalCents,
      itemCount: order.items.length,
    });

    span.setStatus({ code: SpanStatusCode.OK });
    res.status(201).json({ orderId: order.id });
  } catch (error) {
    span.setStatus({ code: SpanStatusCode.ERROR, message: error.message });
    span.recordException(error);

    logger.error("order.create.failed", error, {
      userId: req.authenticatedUser?.id,
      requestBody: sanitize(req.body), // Remove sensitive fields before logging
    });

    res.status(500).json({ error: "Order creation failed" });
  } finally {
    span.end();
  }
});
```

### GOOD: Metrics with the Four Golden Signals

```typescript
import { metrics } from "@opentelemetry/api";

const meter = metrics.getMeter("order-service");

// Four Golden Signals as metrics

// 1. Latency: how long requests take
const requestDuration = meter.createHistogram("http.request.duration", {
  description: "HTTP request duration in milliseconds",
  unit: "ms",
});

// 2. Traffic: how many requests per second
const requestCount = meter.createCounter("http.request.count", {
  description: "Total HTTP requests",
});

// 3. Errors: how many requests fail
const errorCount = meter.createCounter("http.request.errors", {
  description: "Total HTTP request errors",
});

// 4. Saturation: how full is the system
const activeConnections = meter.createUpDownCounter("http.connections.active", {
  description: "Current active HTTP connections",
});

// Middleware to record all four signals automatically
function observabilityMiddleware(req: Request, res: Response, next: NextFunction): void {
  const startTime = Date.now();
  activeConnections.add(1);

  res.on("finish", () => {
    const duration = Date.now() - startTime;
    const labels = {
      method: req.method,
      path: req.route?.path ?? req.path,
      status_code: String(res.statusCode),
    };

    requestDuration.record(duration, labels);
    requestCount.add(1, labels);
    activeConnections.add(-1);

    if (res.statusCode >= 500) {
      errorCount.add(1, labels);
    }
  });

  next();
}
```

---

## SLOs, SLIs, and SLAs

| Concept | Definition | Example |
|---|---|---|
| **SLI (Service Level Indicator)** | A quantitative measure of service behavior | 99.2% of requests complete in under 500ms |
| **SLO (Service Level Objective)** | A target value for an SLI | "99.9% of requests should succeed" |
| **SLA (Service Level Agreement)** | A contract with consequences for missing SLOs | "If uptime drops below 99.9%, customer gets credits" |
| **Error budget** | The allowed amount of unreliability (100% - SLO) | 0.1% error budget = 43.8 minutes of downtime/month |

---

## Alternatives & Related Approaches

| Approach | Philosophy | Limitation |
|---|---|---|
| **printf debugging** | Add print statements, observe output | Does not scale; requires redeployment |
| **Log file grepping** | Search unstructured logs with grep/awk | Slow, fragile, loses context across services |
| **APM-only (Application Performance Monitoring)** | Rely on vendor agent for everything | Vendor lock-in, limited custom instrumentation |
| **Dashboard-only monitoring** | Watch dashboards, react to anomalies | Reactive, not investigative; alert fatigue |
| **Synthetic monitoring** | Probe from outside to detect failures | Catches user-facing failures, misses internal issues |

---

## When NOT to Apply

- **Simple single-process applications.** A CLI tool or a batch job does not need distributed tracing. Structured logging is sufficient.
- **When the cost exceeds the value.** Observability infrastructure (log aggregation, trace storage, metric backends) costs money. A small team with a small system may not need Jaeger, Prometheus, and Elasticsearch.
- **As a substitute for good design.** Observability helps you find problems, but it does not fix them. If your architecture is fundamentally flawed, more dashboards will not help.

---

## Tensions & Trade-offs

- **Verbosity vs. cost:** More logging and tracing means more storage and processing cost. Sample traces (e.g., 10% of requests) and set log level thresholds.
- **Alert sensitivity vs. alert fatigue:** Too many alerts and the team ignores them all. Too few and real incidents go unnoticed. Use SLO-based alerting (alert on error budget burn rate, not individual errors).
- **Cardinality vs. queryability:** High-cardinality labels (like user ID on every metric) make metrics expensive to store. Use logs for high-cardinality data, metrics for low-cardinality aggregates.
- **Instrumentation overhead vs. performance:** Every span and log line has a cost. Use sampling for high-throughput systems.

---

## Real-World Consequences

- **Amazon's 2017 S3 outage** took 4+ hours to diagnose partly because the blast radius was larger than expected and the tooling could not quickly identify the root cause across dependent services.
- **Uber's Jaeger** (open-source distributed tracing) was built because their engineers could not debug latency issues across hundreds of microservices with logs alone.
- **Netflix's observability platform** processes trillions of metrics daily, enabling them to detect and resolve issues within minutes across a global infrastructure.

---

## Key Quotes

> "Observability is not about logs, metrics, and traces. It's about being able to ask arbitrary questions about your system without having to deploy new code." -- Charity Majors

> "Monitoring tells you whether the system works. Observability lets you ask why it's not working." -- Cindy Sridharan

> "Without observability, you're flying blind in production." -- Liz Fong-Jones

> "The four golden signals: latency, traffic, errors, and saturation. If you can only measure four metrics, focus on these." -- Google SRE Book

---

## Further Reading

- *Distributed Systems Observability* by Cindy Sridharan (O'Reilly, 2018)
- *Site Reliability Engineering* by Google (O'Reilly, 2016) -- Chapters on monitoring
- *Observability Engineering* by Charity Majors, Liz Fong-Jones, George Miranda (O'Reilly, 2022)
- OpenTelemetry documentation (opentelemetry.io)
- "Monitoring and Observability" by Cindy Sridharan (blog series at copyconstruct.medium.com)
