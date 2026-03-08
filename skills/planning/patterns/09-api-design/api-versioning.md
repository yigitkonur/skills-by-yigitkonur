# API Versioning Strategies

## Origin

API versioning became a critical concern as web services matured beyond internal use. When external consumers depend on your API, any breaking change can cascade into production failures. The debate between URI-based, header-based, and query-param-based versioning has been ongoing since the early days of public APIs, with companies like Stripe pioneering date-based approaches.

## Explanation

Versioning strategies fall into several categories:

- **URI Path Versioning** (`/v1/orders`): Most visible, easiest to understand. The version is part of the route itself.
- **Header Versioning** (`Accept: application/vnd.myapi.v2+json`): Keeps URIs clean. The version is negotiated via content type headers.
- **Query Parameter Versioning** (`/orders?version=2`): Easy to add retroactively. Less "pure" but pragmatic.
- **Date-Based Versioning** (Stripe model): Clients pin to a date. The server transforms requests/responses to match the pinned API shape.
- **No Versioning / Evolution** (GraphQL model): Add fields freely, deprecate old ones. Avoid breaking changes by design.

### What Counts as a Breaking Change

- Removing or renaming a field
- Changing a field's type
- Adding a required input parameter
- Changing error formats or status codes
- Altering authentication schemes

### What Is NOT a Breaking Change

- Adding optional fields to responses
- Adding optional query parameters
- Adding new endpoints
- Adding new enum values (if clients handle unknown values)

## TypeScript Code Examples

### Bad: No Versioning Strategy

```typescript
// BAD: Breaking changes pushed to all consumers simultaneously
app.get("/orders/:id", async (req, res) => {
  const order = await getOrder(req.params.id);
  // Renamed 'total' to 'totalAmount' — every client breaks
  res.json({
    id: order.id,
    totalAmount: order.total, // was: total
    currency: order.currency,
  });
});
```

### Good: URI Path Versioning with Router Isolation

```typescript
// GOOD: Version-specific routers with clear separation
import { Router } from "express";

const v1Router = Router();
const v2Router = Router();

v1Router.get("/orders/:id", async (req, res) => {
  const order = await getOrder(req.params.id);
  res.json({
    id: order.id,
    total: order.totalCents / 100, // v1: dollars as float
    currency: order.currency,
  });
});

v2Router.get("/orders/:id", async (req, res) => {
  const order = await getOrder(req.params.id);
  res.json({
    id: order.id,
    amount: { cents: order.totalCents, currency: order.currency }, // v2: structured money
  });
});

app.use("/v1", v1Router);
app.use("/v2", v2Router);
```

### Good: Stripe-Style Date-Based Versioning

```typescript
// GOOD: Date-based versioning with transformation layers
type ApiVersion = "2024-01-15" | "2024-06-01" | "2025-01-10";

interface VersionTransformer {
  transformResponse(data: InternalOrder): unknown;
}

const transformers: Record<ApiVersion, VersionTransformer> = {
  "2024-01-15": {
    transformResponse(order) {
      return { id: order.id, total: order.totalCents / 100 };
    },
  },
  "2024-06-01": {
    transformResponse(order) {
      return {
        id: order.id,
        amount: { cents: order.totalCents, currency: order.currency },
      };
    },
  },
  "2025-01-10": {
    transformResponse(order) {
      return {
        id: order.id,
        amount: { cents: order.totalCents, currency: order.currency },
        metadata: order.metadata ?? {},
      };
    },
  },
};

function versionMiddleware(req: Request, res: Response, next: NextFunction) {
  const version = (req.headers["stripe-version"] as ApiVersion) ?? "2025-01-10";
  if (!transformers[version]) {
    return res.status(400).json({ error: `Unknown API version: ${version}` });
  }
  req.apiVersion = version;
  next();
}

app.get("/orders/:id", versionMiddleware, async (req, res) => {
  const order = await getOrder(req.params.id);
  const transformer = transformers[req.apiVersion];
  res.json({ data: transformer.transformResponse(order) });
});
```

### Good: Header-Based Content Negotiation

```typescript
// GOOD: Version via Accept header
app.get("/orders/:id", async (req, res) => {
  const accept = req.headers.accept ?? "";
  const order = await getOrder(req.params.id);

  if (accept.includes("application/vnd.myapi.v2+json")) {
    res.type("application/vnd.myapi.v2+json").json(formatV2(order));
  } else {
    res.type("application/vnd.myapi.v1+json").json(formatV1(order));
  }
});
```

## Alternatives

| Strategy | Pros | Cons |
|----------|------|------|
| **URI path** (`/v1/`) | Obvious, cacheable, easy routing | URI pollution, hard to sunset |
| **Header-based** | Clean URIs, proper HTTP semantics | Less discoverable, harder to test in browser |
| **Query param** | Easy to add, flexible | Caching complexity, feels hacky |
| **Date-based** (Stripe) | Granular, per-consumer pinning | Complex server-side transformation |
| **GraphQL evolution** | No versions needed | Requires discipline around deprecation |

## When NOT to Apply

- **Internal-only APIs with a single consumer**: If you own both sides and deploy them together, versioning adds unnecessary overhead. Just coordinate deployments.
- **Prototyping and early-stage products**: Versioning too early adds complexity. Wait until you have external consumers or cannot coordinate deployments.
- **GraphQL APIs**: The type system and field deprecation built into GraphQL make explicit versioning largely unnecessary.

## Trade-offs

- **URI versioning** is the most common and most pragmatic but semantically impure since the version is not part of the resource identity.
- **Date-based versioning** gives the best consumer experience but requires maintaining transformation layers indefinitely (or until sunset).
- **Every version you keep alive is code you must test and maintain.** Set clear deprecation policies (e.g., "N-2 versions supported, 12-month sunset window").
- **Additive-only changes** are the cheapest approach. Design your initial API to be extensible: use objects instead of flat fields, include envelope wrappers, and make all new fields optional.

## Further Reading

- [Stripe's API Versioning Approach](https://stripe.com/blog/api-versioning)
- [API Versioning Has No Right Answer — Phil Sturgeon](https://apisyouwonthate.com/blog/api-versioning-has-no-right-answer)
- [Semantic Versioning for APIs](https://semver.org/)
- [Google API Design Guide — Versioning](https://cloud.google.com/apis/design/versioning)
