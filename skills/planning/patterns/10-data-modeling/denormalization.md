# Strategic Denormalization

## Origin

Denormalization is the deliberate introduction of redundancy into a normalized database schema to improve read performance. While normalization theory dates to the 1970s, denormalization became a systematic practice with the rise of high-traffic web applications in the 2000s. Companies like Facebook, Twitter, and Amazon recognized that join-heavy normalized queries could not meet their latency requirements at scale, and began treating denormalization as an engineering tool rather than a design failure.

## Explanation

Denormalization is not the absence of normalization — it is the intentional reversal of normalization after understanding the trade-offs. You start normalized, identify read performance bottlenecks, and selectively denormalize to address them.

### Strategies

**Precomputed Columns**: Store derived values directly on the row. Example: `order_total_cents` on the `orders` table instead of summing `order_items` every time.

**Materialized Views**: Database-maintained snapshots of complex queries, refreshed on a schedule or on demand. The database handles the redundancy for you.

**Duplicated Fields**: Copy frequently accessed fields from related tables into the queried table. Example: `customer_name` on the `orders` table to avoid joining `customers` for display.

**Summary Tables**: Pre-aggregated tables for analytics. Example: `daily_sales_summary` with `date`, `product_id`, `total_units`, `total_revenue`.

**Embedding (Document Style)**: Store related data as JSON within a relational column (PostgreSQL JSONB). Useful for data that is always read together and rarely queried independently.

### When to Denormalize

1. A specific query is too slow and cannot be improved by indexing or query optimization.
2. The read-to-write ratio is heavily skewed toward reads.
3. The denormalized data can be kept consistent (via triggers, application logic, or eventual consistency).
4. You accept the maintenance cost of dual-write logic.

## TypeScript Code Examples

### Bad: Premature Denormalization

```typescript
// BAD: Denormalized from the start with no strategy for keeping data consistent
interface OrderTable {
  id: string;
  customerName: string;        // Duplicated from customers table
  customerEmail: string;       // Duplicated from customers table
  customerPhone: string;       // Duplicated from customers table
  productNames: string;        // Comma-separated list — not even 1NF
  totalAmount: number;         // Computed but no mechanism to keep it in sync
  shippingAddressCity: string; // Duplicated from addresses table
}

// Customer changes email — now you must update orders too
// No trigger, no event, no application logic handles this
// Data silently becomes inconsistent
```

### Good: Precomputed Column with Trigger

```typescript
// GOOD: Denormalized total maintained by a database trigger
const migration = `
  -- Add precomputed total to orders
  ALTER TABLE orders ADD COLUMN total_cents INTEGER;

  -- Trigger function to recalculate total
  CREATE OR REPLACE FUNCTION update_order_total()
  RETURNS TRIGGER AS $$
  BEGIN
    UPDATE orders
    SET total_cents = (
      SELECT COALESCE(SUM(unit_price_cents * quantity), 0)
      FROM order_items
      WHERE order_id = COALESCE(NEW.order_id, OLD.order_id)
    )
    WHERE id = COALESCE(NEW.order_id, OLD.order_id);
    RETURN NEW;
  END;
  $$ LANGUAGE plpgsql;

  CREATE TRIGGER trg_order_items_total
  AFTER INSERT OR UPDATE OR DELETE ON order_items
  FOR EACH ROW EXECUTE FUNCTION update_order_total();
`;

// Application code can now read the total without a join or aggregation
async function getOrderTotal(orderId: string): Promise<number> {
  const result = await db.query(
    "SELECT total_cents FROM orders WHERE id = $1",
    [orderId]
  );
  return result.rows[0].total_cents;
}
```

### Good: Materialized View for Dashboard

```typescript
// GOOD: Materialized view for an analytics dashboard
const materializedView = `
  CREATE MATERIALIZED VIEW daily_sales_summary AS
  SELECT
    DATE_TRUNC('day', o.ordered_at) AS sale_date,
    p.id AS product_id,
    p.name AS product_name,
    COUNT(DISTINCT o.id) AS order_count,
    SUM(oi.quantity) AS units_sold,
    SUM(oi.unit_price_cents * oi.quantity) AS revenue_cents
  FROM orders o
  JOIN order_items oi ON oi.order_id = o.id
  JOIN products p ON p.id = oi.product_id
  WHERE o.status != 'cancelled'
  GROUP BY DATE_TRUNC('day', o.ordered_at), p.id, p.name;

  CREATE UNIQUE INDEX idx_daily_sales_date_product
    ON daily_sales_summary(sale_date, product_id);
`;

// Refresh on a schedule (e.g., every 5 minutes or via cron)
async function refreshDashboard(): Promise<void> {
  await db.query("REFRESH MATERIALIZED VIEW CONCURRENTLY daily_sales_summary");
}

// Dashboard queries hit the materialized view — fast, no joins
async function getDailySales(date: Date): Promise<DailySale[]> {
  const result = await db.query(
    "SELECT * FROM daily_sales_summary WHERE sale_date = $1 ORDER BY revenue_cents DESC",
    [date]
  );
  return result.rows;
}
```

### Good: Application-Level Denormalization with Events

```typescript
// GOOD: Denormalized read model updated via domain events
interface OrderReadModel {
  orderId: string;
  customerName: string;
  customerEmail: string;
  itemCount: number;
  totalCents: number;
  status: string;
  lastUpdated: Date;
}

// Write path: normalized tables
async function createOrder(input: CreateOrderInput): Promise<Order> {
  const order = await db.transaction(async (tx) => {
    const order = await tx.orders.insert({
      customerId: input.customerId,
      status: "pending",
    });

    for (const item of input.items) {
      await tx.orderItems.insert({
        orderId: order.id,
        productId: item.productId,
        quantity: item.quantity,
        unitPriceCents: item.priceCents,
      });
    }

    return order;
  });

  // Emit event to update read model
  await eventBus.publish("order.created", { orderId: order.id });
  return order;
}

// Event handler: build/update the denormalized read model
async function handleOrderCreated(event: { orderId: string }): Promise<void> {
  const order = await getOrderWithDetails(event.orderId);

  await db.query(
    `INSERT INTO order_read_models (order_id, customer_name, customer_email, item_count, total_cents, status, last_updated)
     VALUES ($1, $2, $3, $4, $5, $6, NOW())
     ON CONFLICT (order_id) DO UPDATE SET
       customer_name = EXCLUDED.customer_name,
       item_count = EXCLUDED.item_count,
       total_cents = EXCLUDED.total_cents,
       status = EXCLUDED.status,
       last_updated = NOW()`,
    [order.id, order.customerName, order.customerEmail, order.itemCount, order.totalCents, order.status]
  );
}
```

## Alternatives

| Approach | Best For | Trade-off |
|----------|----------|-----------|
| **Database indexes** | Speeding up queries without schema changes | Does not eliminate join cost |
| **Caching (Redis)** | Hot data that changes infrequently | Cache invalidation complexity |
| **CQRS** | Separate read and write models at the application level | Architectural complexity, eventual consistency |
| **Read replicas** | Scaling read throughput | Replication lag, still same schema |
| **Column-store databases** | Analytical aggregation queries | Different storage engine |

## When NOT to Apply

- **Before you have a performance problem**: Denormalization is a response to measured bottlenecks, not a preventive measure. Start normalized and prove the need.
- **When data consistency is critical and you cannot afford eventual consistency**: Financial ledgers, inventory counts, and compliance data should remain normalized unless you have bulletproof synchronization.
- **When write throughput is the bottleneck**: Denormalization adds write overhead (triggers, dual-writes, event handlers). If writes are the problem, denormalization makes it worse.
- **Small tables**: Joining three tables of 10,000 rows each with proper indexes takes microseconds. Denormalization adds complexity with negligible performance gain.

## Trade-offs

- **Read speed vs. write complexity**: Every denormalized field must be kept in sync. Triggers are reliable but add write latency. Application events are flexible but introduce eventual consistency.
- **Consistency guarantees**: Denormalized data can become stale. Materialized views have a refresh lag. Event-driven read models have processing lag. Decide how much staleness is acceptable.
- **Maintenance burden**: Denormalized columns must be updated when the source data changes. If you forget to update a code path, data silently becomes incorrect.
- **Migration difficulty**: Adding denormalization to an existing schema requires backfilling. Removing it requires ensuring no code path still depends on the denormalized fields.

## Further Reading

- [Martin Kleppmann — Designing Data-Intensive Applications, Chapter 3](https://dataintensive.net/)
- [PostgreSQL — Materialized Views](https://www.postgresql.org/docs/current/rules-materializedviews.html)
- [Uber — Schemaless: How We Denormalize Data at Uber](https://www.uber.com/en-GB/blog/schemaless-part-one/)
- [CQRS Pattern — Microsoft](https://learn.microsoft.com/en-us/azure/architecture/patterns/cqrs)
