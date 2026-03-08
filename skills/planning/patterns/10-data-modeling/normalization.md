# Database Normalization

## Origin

Database normalization was formalized by Edgar F. Codd in 1970 as part of his relational model of data. Codd introduced the first three normal forms; Boyce-Codd Normal Form (BCNF) was refined by Raymond Boyce and Codd in 1974. The theory addresses data redundancy and update anomalies — problems that arise when the same fact is stored in multiple places.

## Explanation

Normalization is the process of structuring a relational database to reduce redundancy and improve data integrity. Each normal form builds on the previous one.

### First Normal Form (1NF)

- Every column contains atomic (indivisible) values.
- No repeating groups or arrays in a single column.
- Each row is uniquely identifiable (has a primary key).

**Violation**: A `phone_numbers` column containing `"555-1234, 555-5678"`.

### Second Normal Form (2NF)

- Must be in 1NF.
- Every non-key column depends on the entire primary key, not just part of it.
- Only relevant for composite primary keys.

**Violation**: A table with composite key `(order_id, product_id)` and a column `customer_name` that depends only on `order_id`.

### Third Normal Form (3NF)

- Must be in 2NF.
- No transitive dependencies: non-key columns depend only on the primary key, not on other non-key columns.

**Violation**: A table with `employee_id`, `department_id`, and `department_name`. The department name depends on `department_id`, not on `employee_id`.

### Boyce-Codd Normal Form (BCNF)

- Must be in 3NF.
- Every determinant is a candidate key. Handles edge cases where 3NF allows anomalies with overlapping candidate keys.

### Update Anomalies

Without normalization, three types of anomalies can occur:

- **Insert anomaly**: Cannot record a fact without unrelated data (e.g., cannot add a department without also adding an employee).
- **Update anomaly**: Changing a fact requires updating multiple rows (e.g., renaming a department means updating every employee row in that department).
- **Delete anomaly**: Deleting data causes loss of unrelated facts (e.g., deleting the last employee in a department loses the department record).

## TypeScript Code Examples

### Bad: Denormalized Flat Table

```typescript
// BAD: All data in one table — redundancy everywhere
interface OrderFlat {
  orderId: string;
  orderDate: Date;
  customerName: string;       // Repeated for every order
  customerEmail: string;      // Repeated for every order
  customerAddress: string;    // Repeated for every order
  productName: string;        // Repeated across orders
  productPrice: number;       // Can become inconsistent
  quantity: number;
}

// Problem: Customer "Alice" has 50 orders. Changing her email
// means updating 50 rows. Miss one? Data is inconsistent.
await db.query(
  "UPDATE orders SET customer_email = $1 WHERE customer_name = $2",
  ["new@email.com", "Alice"]
  // What if customer_name is not unique? Which Alice?
);
```

### Good: Normalized to 3NF

```typescript
// GOOD: Each fact stored exactly once
// Schema (PostgreSQL):
const schema = `
  CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    address TEXT
  );

  CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    price_cents INTEGER NOT NULL
  );

  CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id),
    ordered_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    status TEXT NOT NULL DEFAULT 'pending'
  );

  CREATE TABLE order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id),
    product_id UUID NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price_cents INTEGER NOT NULL -- snapshot at time of order
  );

  CREATE INDEX idx_orders_customer_id ON orders(customer_id);
  CREATE INDEX idx_order_items_order_id ON order_items(order_id);
  CREATE INDEX idx_order_items_product_id ON order_items(product_id);
`;

// TypeScript interfaces mirroring normalized schema
interface Customer {
  id: string;
  name: string;
  email: string;
  address: string | null;
}

interface Product {
  id: string;
  name: string;
  priceCents: number;
}

interface Order {
  id: string;
  customerId: string;
  orderedAt: Date;
  status: "pending" | "confirmed" | "shipped" | "delivered";
}

interface OrderItem {
  id: string;
  orderId: string;
  productId: string;
  quantity: number;
  unitPriceCents: number; // Intentional denormalization: price at time of purchase
}
```

### Good: Querying Normalized Data with Joins

```typescript
// GOOD: Reconstruct the full picture via joins
async function getOrderWithDetails(orderId: string): Promise<OrderDetails> {
  const result = await db.query(
    `SELECT
      o.id AS order_id,
      o.ordered_at,
      o.status,
      c.name AS customer_name,
      c.email AS customer_email,
      oi.quantity,
      oi.unit_price_cents,
      p.name AS product_name
    FROM orders o
    JOIN customers c ON c.id = o.customer_id
    JOIN order_items oi ON oi.order_id = o.id
    JOIN products p ON p.id = oi.product_id
    WHERE o.id = $1`,
    [orderId]
  );

  return mapToOrderDetails(result.rows);
}
```

### Good: Handling the Price Snapshot Problem

```typescript
// GOOD: unit_price_cents on order_items is intentional denormalization.
// Product price may change; the order records what the customer actually paid.

async function createOrderItem(
  orderId: string,
  productId: string,
  quantity: number
): Promise<OrderItem> {
  // Capture current price at order time
  const product = await db.query(
    "SELECT price_cents FROM products WHERE id = $1",
    [productId]
  );

  return db.query(
    `INSERT INTO order_items (order_id, product_id, quantity, unit_price_cents)
     VALUES ($1, $2, $3, $4)
     RETURNING *`,
    [orderId, productId, quantity, product.rows[0].price_cents]
  );
}
// This is a deliberate denormalization — the order item captures a historical fact
// that must not change when the product price is updated.
```

## Alternatives

| Approach | Best For | Trade-off |
|----------|----------|-----------|
| **Document stores (MongoDB)** | Naturally nested data, flexible schemas | Embedding duplicates data; updates are harder |
| **Denormalization** | Read-heavy workloads where join cost matters | Write complexity, potential inconsistency |
| **Star/Snowflake schema** | Analytics and data warehousing | Optimized for reads, not transactional integrity |
| **Graph databases** | Highly connected data with traversal queries | Different query paradigm entirely |

## When NOT to Apply

- **Analytics and reporting databases**: Normalization optimizes for write correctness. Analytical workloads need denormalized star/snowflake schemas optimized for aggregation queries.
- **Document-oriented data**: If your data is naturally hierarchical (e.g., a blog post with embedded comments), forcing it into normalized tables adds join complexity with little benefit. Use a document store or PostgreSQL JSONB.
- **Extreme read performance requirements**: When you need sub-millisecond reads on complex views, pre-computed denormalized tables or materialized views may be necessary (see denormalization.md).
- **Prototyping**: Normalize later. Get the product right first.

## Trade-offs

- **Data integrity vs. read performance**: Normalization guarantees each fact is stored once (no inconsistency), but reconstructing complex views requires joins, which have a cost.
- **Write simplicity vs. read complexity**: Updates are simple in a normalized schema (change one row), but reads require joining multiple tables.
- **Storage vs. redundancy**: Normalized schemas use less storage, but modern storage is cheap. The real cost of redundancy is inconsistency, not disk space.
- **Price snapshots and historical data**: Some denormalization is mandatory. An order must record the price at the time of purchase, not the current product price. Recognize when a "copy" is actually a historical fact.

## Further Reading

- [Codd, E.F. — A Relational Model of Data for Large Shared Data Banks (1970)](https://www.seas.upenn.edu/~zives/03f/cis550/codd.pdf)
- [Use the Index, Luke — Normalization](https://use-the-index-luke.com/sql/normalize)
- [PostgreSQL Documentation — Database Design](https://www.postgresql.org/docs/current/ddl.html)
- [Database Normalization Explained — Lucidchart](https://www.lucidchart.com/pages/database-normalization)
