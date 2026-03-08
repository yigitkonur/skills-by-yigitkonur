# GraphQL vs REST — Honest Trade-offs

## Origin

REST has dominated web API design since the mid-2000s. GraphQL was developed internally at Facebook in 2012 and open-sourced in 2015 to solve specific problems they faced: mobile clients with limited bandwidth needing flexible data fetching, and a rapidly evolving product with hundreds of frontend teams. It is not a replacement for REST — it is an alternative with a different set of trade-offs.

## Explanation

### Core Differences

**REST**: Multiple endpoints, each returning a fixed resource shape. The server decides what data comes back. Caching is straightforward (HTTP caching by URL). Tooling is universal.

**GraphQL**: Single endpoint, client specifies exactly which fields it needs. The server exposes a schema; the client queries it. Caching requires custom strategies. Tooling is specialized.

### The Problems GraphQL Solves

**Over-fetching**: REST endpoint `/users/123` returns 30 fields when the mobile app only needs `name` and `avatar`. GraphQL lets the client request only those two fields.

**Under-fetching (N+1 at the API level)**: Displaying a page requires `/users/123`, then `/users/123/orders`, then `/orders/456/items` — three round trips. GraphQL resolves this in a single query.

**Rapid frontend iteration**: Frontend teams can add fields to their queries without waiting for backend changes, as long as the schema supports it.

### The Problems GraphQL Creates

**N+1 at the resolver level**: A naive GraphQL server fetching `users { orders { items } }` will execute one query per user for orders, then one query per order for items. DataLoader is required to batch these.

**Caching difficulty**: REST responses are cacheable by URL. GraphQL POST requests to a single endpoint are not cacheable by HTTP infrastructure. You need application-level caching (persisted queries, response caching).

**Complexity cost**: Schema design, resolver implementation, DataLoader patterns, query depth limiting, query cost analysis, and persisted queries all add operational overhead.

## TypeScript Code Examples

### REST: Over-fetching Problem

```typescript
// REST: Client gets everything whether it wants it or not
app.get("/users/:id", async (req, res) => {
  const user = await db.users.findById(req.params.id);
  // Returns 30 fields; mobile client only needs name + avatar
  res.json({
    id: user.id,
    name: user.name,
    avatar: user.avatarUrl,
    email: user.email,
    phone: user.phone,
    address: user.address,
    preferences: user.preferences,
    // ... 23 more fields
  });
});

// Client needs 3 requests to build one page:
// GET /users/123
// GET /users/123/orders?limit=5
// GET /orders/456/items
```

### GraphQL: Flexible Querying

```typescript
// GraphQL: Client asks for exactly what it needs in one request
import { makeExecutableSchema } from "@graphql-tools/schema";

const typeDefs = `
  type User {
    id: ID!
    name: String!
    avatar: String
    email: String!
    orders(limit: Int = 10): [Order!]!
  }

  type Order {
    id: ID!
    total: Money!
    status: OrderStatus!
    items: [OrderItem!]!
  }

  type Money {
    cents: Int!
    currency: String!
  }

  type OrderItem {
    id: ID!
    product: Product!
    quantity: Int!
  }

  type Product {
    id: ID!
    name: String!
    imageUrl: String
  }

  enum OrderStatus { PENDING CONFIRMED SHIPPED DELIVERED }

  type Query {
    user(id: ID!): User
  }
`;

// Client query — one request, exact data needed:
// query {
//   user(id: "123") {
//     name
//     avatar
//     orders(limit: 5) {
//       id
//       total { cents currency }
//       items { product { name imageUrl } quantity }
//     }
//   }
// }
```

### Bad: Naive Resolvers with N+1

```typescript
// BAD: Each user triggers a separate orders query,
// each order triggers a separate items query
const resolvers = {
  Query: {
    user: (_: unknown, { id }: { id: string }) => db.users.findById(id),
  },
  User: {
    // Called once per user — fine for single user, disastrous for lists
    orders: (user: User) => db.orders.findByUserId(user.id),
  },
  Order: {
    // Called once PER ORDER — N orders = N queries
    items: (order: Order) => db.orderItems.findByOrderId(order.id),
  },
  OrderItem: {
    // Called once PER ITEM — M items = M queries
    product: (item: OrderItem) => db.products.findById(item.productId),
  },
};
// A list of 10 users with 5 orders each with 3 items:
// 1 (users) + 10 (orders) + 50 (items) + 150 (products) = 211 queries
```

### Good: DataLoader to Batch and Deduplicate

```typescript
// GOOD: DataLoader batches and deduplicates database calls
import DataLoader from "dataloader";

function createLoaders() {
  return {
    orders: new DataLoader<string, Order[]>(async (userIds) => {
      const orders = await db.orders.findByUserIds([...userIds]);
      const grouped = groupBy(orders, "userId");
      return userIds.map((id) => grouped[id] ?? []);
    }),

    orderItems: new DataLoader<string, OrderItem[]>(async (orderIds) => {
      const items = await db.orderItems.findByOrderIds([...orderIds]);
      const grouped = groupBy(items, "orderId");
      return orderIds.map((id) => grouped[id] ?? []);
    }),

    products: new DataLoader<string, Product>(async (productIds) => {
      const products = await db.products.findByIds([...productIds]);
      const byId = keyBy(products, "id");
      return productIds.map((id) => byId[id]);
    }),
  };
}

// Create loaders per request (important — loaders cache within a request)
app.use("/graphql", (req, _res, next) => {
  req.loaders = createLoaders();
  next();
});

const resolvers = {
  User: {
    orders: (user: User, _args: unknown, ctx: Context) =>
      ctx.loaders.orders.load(user.id),
  },
  Order: {
    items: (order: Order, _args: unknown, ctx: Context) =>
      ctx.loaders.orderItems.load(order.id),
  },
  OrderItem: {
    product: (item: OrderItem, _args: unknown, ctx: Context) =>
      ctx.loaders.products.load(item.productId),
  },
};
// Same query now: 1 (users) + 1 (orders batch) + 1 (items batch) + 1 (products batch) = 4 queries
```

### Good: Query Depth and Cost Limiting

```typescript
// GOOD: Prevent abusive deep or expensive queries
import depthLimit from "graphql-depth-limit";
import { createComplexityLimitRule } from "graphql-validation-complexity";

const server = new ApolloServer({
  schema,
  validationRules: [
    depthLimit(7), // Max nesting depth
    createComplexityLimitRule(1000, {
      // Cost analysis
      scalarCost: 1,
      objectCost: 2,
      listFactor: 10,
    }),
  ],
});
```

## When to Choose REST

- Your API is CRUD-focused with predictable access patterns
- You need HTTP caching (CDN, browser cache) out of the box
- Your consumers are diverse (third-party developers, non-JavaScript clients)
- Your team is not prepared to invest in GraphQL tooling and patterns
- You are building a public API with rate limiting per endpoint

## When to Choose GraphQL

- Multiple frontend clients (web, mobile, TV) with different data needs
- Rapid frontend iteration where backends are a bottleneck
- Complex, deeply nested data relationships
- You have the engineering capacity to handle DataLoader, caching, and query cost management
- Internal APIs where you control all consumers

## Trade-offs Table

| Concern | REST | GraphQL |
|---------|------|---------|
| Caching | HTTP native | Requires custom approach |
| Error handling | Status codes + body | Always 200, errors in body |
| File upload | Multipart form-data | Requires spec extension |
| Real-time | SSE, WebSocket separate | Subscriptions built in |
| Monitoring | Standard HTTP metrics | Needs per-field instrumentation |
| Learning curve | Low | Moderate to high |
| Tooling maturity | Universal | Ecosystem-specific |
| Over/under-fetching | Common problem | Solved by design |
| N+1 queries | At API level | At resolver level |

## Further Reading

- [GraphQL Specification](https://spec.graphql.org/)
- [DataLoader — Utility for batching and caching](https://github.com/graphql/dataloader)
- [Apollo Federation — Distributed GraphQL](https://www.apollographql.com/docs/federation/)
- [Why Not Use GraphQL? — Wundergraph](https://wundergraph.com/blog/why_not_use_graphql)
- [Shopify — Lessons from Maintaining a Large GraphQL API](https://shopify.engineering/lessons-learned-graphql)
