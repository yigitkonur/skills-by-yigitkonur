# REST Principles and the Richardson Maturity Model

## Origin

Roy Fielding defined REST (Representational State Transfer) in his 2000 doctoral dissertation. Leonard Richardson later proposed a maturity model that classifies APIs into four levels (0-3), providing a practical ladder for evaluating how "RESTful" an API truly is.

## Explanation

The Richardson Maturity Model breaks REST adoption into levels:

- **Level 0 — The Swamp of POX**: Single URI, single HTTP method (usually POST). Essentially RPC over HTTP. The transport is HTTP but none of its features are leveraged.
- **Level 1 — Resources**: Individual URIs for individual resources (`/orders/123`), but still using a single HTTP method. You have addressability but not proper use of verbs.
- **Level 2 — HTTP Verbs**: Proper use of GET, POST, PUT, DELETE, PATCH with correct status codes. This is where most production APIs live and is often "good enough."
- **Level 3 — Hypermedia Controls (HATEOAS)**: Responses include links that tell clients what actions are possible next. The API becomes self-describing and discoverable.

### Key Principles

- **Statelessness**: Each request contains all information needed to process it. No server-side sessions.
- **Resource-Oriented Design**: Model nouns (resources), not verbs (actions). `/orders` not `/createOrder`.
- **Uniform Interface**: Consistent use of HTTP methods, status codes, and content negotiation.
- **HATEOAS**: Hypermedia As The Engine Of Application State. Clients navigate via links in responses.

## TypeScript Code Examples

### Bad: Level 0 — RPC Style (Everything is POST to one endpoint)

```typescript
// BAD: Single endpoint, action buried in body
app.post("/api", async (req, res) => {
  const { action, payload } = req.body;

  switch (action) {
    case "getOrder":
      const order = await db.orders.findById(payload.id);
      res.json({ result: order });
      break;
    case "createOrder":
      const newOrder = await db.orders.create(payload);
      res.json({ result: newOrder });
      break;
    case "deleteOrder":
      await db.orders.delete(payload.id);
      res.json({ result: "ok" });
      break;
  }
});
```

### Good: Level 2 — Proper Resources and Verbs

```typescript
// GOOD: Resources with proper HTTP verbs and status codes
import { Router } from "express";

const router = Router();

router.get("/orders", async (req, res) => {
  const orders = await orderService.list(req.query);
  res.status(200).json({ data: orders });
});

router.get("/orders/:id", async (req, res) => {
  const order = await orderService.findById(req.params.id);
  if (!order) return res.status(404).json({ error: "Order not found" });
  res.status(200).json({ data: order });
});

router.post("/orders", async (req, res) => {
  const order = await orderService.create(req.body);
  res.status(201).json({ data: order });
});

router.patch("/orders/:id", async (req, res) => {
  const order = await orderService.update(req.params.id, req.body);
  res.status(200).json({ data: order });
});

router.delete("/orders/:id", async (req, res) => {
  await orderService.delete(req.params.id);
  res.status(204).send();
});
```

### Good: Level 3 — HATEOAS Links

```typescript
// GOOD: Response includes navigable links
interface HateoasLink {
  rel: string;
  href: string;
  method: string;
}

interface OrderResponse {
  data: Order;
  _links: HateoasLink[];
}

function buildOrderResponse(order: Order): OrderResponse {
  const links: HateoasLink[] = [
    { rel: "self", href: `/orders/${order.id}`, method: "GET" },
    { rel: "update", href: `/orders/${order.id}`, method: "PATCH" },
    { rel: "cancel", href: `/orders/${order.id}/cancel`, method: "POST" },
    { rel: "items", href: `/orders/${order.id}/items`, method: "GET" },
  ];

  if (order.status === "pending") {
    links.push({
      rel: "pay",
      href: `/orders/${order.id}/payments`,
      method: "POST",
    });
  }

  return { data: order, _links: links };
}
```

## Alternatives

| Approach | Best For | Trade-off |
|----------|----------|-----------|
| **GraphQL** | Complex frontends needing flexible queries | Higher complexity, caching is harder |
| **gRPC** | Service-to-service, high performance | Not browser-friendly without a proxy |
| **tRPC** | Full-stack TypeScript monorepos | Tight coupling between client and server |
| **JSON-RPC** | Simple internal services | No resource semantics |

## When NOT to Apply

- **Internal microservices with high throughput**: gRPC with Protocol Buffers is typically more efficient for service-to-service communication where browser support is unnecessary.
- **Real-time bidirectional communication**: WebSockets or Server-Sent Events are better suited for push-based patterns.
- **HATEOAS specifically**: Most teams stop at Level 2. Level 3 adds complexity that few clients actually leverage. Apply it when your API has genuinely discoverable workflows (e.g., payment state machines) rather than bolting it on everywhere.

## Trade-offs

- **Simplicity vs. Completeness**: Level 2 is pragmatic; Level 3 is purist. Choose based on your consumers.
- **Over-fetching**: REST endpoints return fixed shapes. Clients may need multiple calls to assemble a view (which GraphQL addresses).
- **Statelessness**: Eliminates server-side session management but increases payload size since every request must be self-contained.
- **Cacheability**: GET requests are trivially cacheable. This is one of REST's strongest practical advantages over RPC-style APIs.

## Further Reading

- [Fielding's Dissertation — Chapter 5](https://www.ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm)
- [Richardson Maturity Model — Martin Fowler](https://martinfowler.com/articles/richardsonMaturityModel.html)
- [Microsoft REST API Guidelines](https://github.com/microsoft/api-guidelines)
- [Zalando RESTful API Guidelines](https://opensource.zalando.com/restful-api-guidelines/)
