# Microservice
Build an Effect v3 microservice with `HttpApi`, SQL, cache, tracing, RPC boundaries, and test layer overrides.

Use this when the service owns data and participates in a larger distributed system. Keep the public HTTP contract thin, the domain service explicit, and infrastructure behind layers.

## Primitive index

| Primitive | Read first |
|---|---|
| HTTP contract and serving | [http-server](../http-server/02-defining-endpoints.md), [http-server](../http-server/07-handlers.md), [http-server](../http-server/15-serving.md) |
| SQL client, transactions, migrations | [sql](../sql/02-sql-client.md), [sql](../sql/04-transactions.md), [sql](../sql/08-sql-migrations.md), [sql](../sql/09-driver-postgres.md) |
| cache and request resolver | [caching](../caching/02-cache-make.md), [caching](../caching/03-cache-operations.md), [caching](../caching/07-request-resolver.md) |
| tracing, metrics, RPC | [observability](../observability/06-tracing-basics.md), [observability](../observability/08-metrics-counter-gauge.md), [rpc](../rpc/01-overview.md) |
| layers, config, tests | [services-layers](../services-layers/11-layer-providemerge.md), [config](../config/03-config-redacted.md), [testing](../testing/08-test-layers.md) |

## 1. Package setup

```typescript
{
  "type": "module",
  "scripts": {
    "dev": "tsx src/main.ts",
    "build": "tsc -p tsconfig.json",
    "test": "vitest"
  },
  "dependencies": {
    "@effect/platform": "^0.95.0",
    "@effect/platform-node": "^0.90.0",
    "@effect/sql": "^0.44.0",
    "@effect/sql-pg": "^0.45.0",
    "effect": "^3.21.2"
  },
  "devDependencies": {
    "@effect/vitest": "^0.28.0",
    "tsx": "^4.20.0",
    "typescript": "^5.9.0",
    "vitest": "^4.0.0"
  }
}
```

## 2. Entry point

`src/main.ts` launches the server layer. Do not run the domain program directly.

```typescript
import { NodeRuntime } from "@effect/platform-node"
import { Layer } from "effect"
import { HttpLive } from "./http.js"

HttpLive.pipe(
  Layer.launch,
  NodeRuntime.runMain
)
```

This shape gives the server, database pool, cache, and telemetry a single lifetime. Each request still gets its own fiber and interruption boundary.

## 3. Main Effect orchestration

`src/orders.ts` coordinates validation, SQL, cache invalidation, and tracing.

```typescript
import { SqlClient } from "@effect/sql"
import { Cache, Duration, Effect, Metric, Schema } from "effect"

export class Order extends Schema.Class<Order>("Order")({
  id: Schema.String,
  customerId: Schema.String,
  totalCents: Schema.Number
}) {}

export class CreateOrder extends Schema.Class<CreateOrder>("CreateOrder")({
  customerId: Schema.String,
  totalCents: Schema.Number
}) {}

export class OrderNotFound extends Schema.TaggedError<OrderNotFound>()("OrderNotFound", {
  id: Schema.String
}) {}

const createdCounter = Metric.counter("orders_created")

export class Orders extends Effect.Service<Orders>()("app/Orders", {
  effect: Effect.gen(function*() {
    const sql = yield* SqlClient.SqlClient
    const byIdCache = yield* Cache.make({
      capacity: 10_000,
      timeToLive: Duration.minutes(5),
      lookup: (id: string) =>
        sql<Order>`select id, customer_id as "customerId", total_cents as "totalCents" from orders where id = ${id}`.pipe(
          Effect.flatMap((rows) =>
            rows[0] ? Effect.succeed(new Order(rows[0])) : Effect.fail(new OrderNotFound({ id }))
          )
        )
    })

    const create = (input: CreateOrder) =>
      Effect.gen(function*() {
        const id = `order-${Date.now()}`
        const order = new Order({ id, ...input })
        yield* sql`insert into orders (id, customer_id, total_cents) values (${id}, ${input.customerId}, ${input.totalCents})`
        yield* Metric.increment(createdCounter)
        return order
      }).pipe(sql.withTransaction, Effect.withSpan("Orders.create"))

    const get = (id: string) =>
      byIdCache.get(id).pipe(Effect.withSpan("Orders.get", { attributes: { id } }))

    return { create, get } as const
  })
}) {}
```

The cache wraps reads only. Mutations should update or invalidate cache entries deliberately, not rely on accidental short TTLs.

## 4. Per-feature API definitions

`src/api.ts` exposes the service through a small HTTP surface.

```typescript
import { HttpApi, HttpApiEndpoint, HttpApiGroup } from "@effect/platform"
import { CreateOrder, Order, OrderNotFound } from "./orders.js"

export class OrdersGroup extends HttpApiGroup.make("orders")
  .add(HttpApiEndpoint.post("create", "/orders").setPayload(CreateOrder).addSuccess(Order))
  .add(HttpApiEndpoint.get("get", "/orders/:id").addSuccess(Order).addError(OrderNotFound))
{}

export class Api extends HttpApi.make("orders-api").add(OrdersGroup) {}
```

If another service needs the same capability internally, expose it through an RPC group or client service rather than reusing HTTP handler code. See [RPC group](../rpc/02-rpc-group.md) and [RPC client](../rpc/04-rpc-client.md).

## 5. Layer wiring

`src/http.ts` composes HTTP, SQL, and platform layers.

```typescript
import { HttpApiBuilder, HttpMiddleware, HttpServer } from "@effect/platform"
import { NodeHttpServer } from "@effect/platform-node"
import { PgClient } from "@effect/sql-pg"
import { Config, Effect, Layer } from "effect"
import { createServer } from "node:http"
import { Api } from "./api.js"
import { Orders } from "./orders.js"

const OrdersHandlers = HttpApiBuilder.group(Api, "orders", (handlers) =>
  Effect.gen(function*() {
    const orders = yield* Orders
    return handlers
      .handle("create", ({ payload }) => orders.create(payload))
      .handle("get", ({ path }) => orders.get(path.id))
  })
)

const SqlLive = PgClient.layerConfig({
  url: Config.redacted("DATABASE_URL")
})

const ApiLive = HttpApiBuilder.api(Api).pipe(
  Layer.provide(OrdersHandlers),
  Layer.provide(Orders.Default),
  Layer.provide(SqlLive)
)

export const HttpLive = HttpApiBuilder.serve(HttpMiddleware.logger).pipe(
  Layer.provide(ApiLive),
  HttpServer.withLogAddress,
  Layer.provide(NodeHttpServer.layer(createServer, { port: 3000 }))
)
```

Add OpenTelemetry as a layer at the same edge. Do not thread tracing clients through constructors manually.

## 6. Test layer override

Tests override `Orders` for API behavior, or SQL for repository behavior.

```typescript
import { Effect, Layer } from "effect"
import { CreateOrder, Order, Orders } from "../src/orders.js"

export const OrdersTest = Layer.succeed(Orders, {
  create: (input: CreateOrder) =>
    Effect.succeed(new Order({ id: "o1", ...input })),
  get: (id: string) =>
    Effect.succeed(new Order({ id, customerId: "c1", totalCents: 1000 }))
})
```

For transaction tests, provide a test SQL layer and run migrations before the test suite. Keep cache tests explicit by asserting repeated reads do not repeat the lookup.

## Workflow checklist

1. Start with the HTTP contract.
2. Add SQL behind the domain service.
3. Add cache only around read paths.
4. Add tracing around public service methods.
5. Keep the database URL in `Config.redacted`.
6. Keep transaction boundaries inside the domain service.
7. Keep RPC boundaries separate from HTTP handlers.
8. Verify cache, SQL, and handler layers independently.

## 7. Deployment

Deploy as a long-running Node service when the database pool and cache should stay warm. Containers should run the compiled `main.js`, expose one port, and provide `DATABASE_URL` through the platform secret store. For serverless environments, reduce pool size and review cold-start cost because the layer graph initializes per warm instance.

## Cross-references

See also: [HTTP API](02-greenfield-http-api.md), [background worker](07-background-worker.md), [MCP server](08-mcp-server.md), [SQL overview](../sql/01-overview.md).
