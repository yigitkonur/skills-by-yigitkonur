# Pagination Strategies

## Origin

Pagination is as old as databases themselves. The simplest approach — OFFSET/LIMIT — maps directly to SQL. As datasets grew into millions of rows, the performance cliff of deep offset pagination drove adoption of cursor-based and keyset pagination. Companies like Slack, Facebook, and Twitter popularized cursor-based pagination through their public APIs.

## Explanation

### Offset Pagination

The client specifies a page number or offset and a page size. The server skips rows up to the offset, then returns the next page.

- **SQL**: `SELECT * FROM orders ORDER BY created_at DESC LIMIT 20 OFFSET 100`
- **Problem**: The database must scan and discard all rows before the offset. Page 5000 of a million-row table means scanning 100,000 rows to discard 99,980.

### Cursor-Based Pagination

The server returns an opaque cursor (typically a base64-encoded identifier) with each page. The client passes this cursor to fetch the next page. The cursor encodes enough information to seek directly to the next page.

- **SQL**: `SELECT * FROM orders WHERE id < $cursor ORDER BY id DESC LIMIT 20`
- **Advantage**: Constant-time page retrieval regardless of depth.

### Keyset Pagination

A specific form of cursor pagination where the cursor is based on the sort columns. If sorting by `created_at DESC`, the cursor is the `created_at` value of the last item on the current page.

- **SQL**: `SELECT * FROM orders WHERE created_at < $last_created_at ORDER BY created_at DESC LIMIT 20`
- **Advantage**: Works efficiently with any indexed sort column.

### Comparison

| Feature | Offset | Cursor | Keyset |
|---------|--------|--------|--------|
| Jump to page N | Yes | No | No |
| Deep pagination perf | O(offset) | O(1) | O(1) |
| Stable under inserts | No (items shift) | Yes | Yes |
| Sort flexibility | Any | Encoded | Must match index |
| Implementation effort | Trivial | Moderate | Moderate |

## TypeScript Code Examples

### Bad: Naive Offset Pagination

```typescript
// BAD: Deep pagination causes full table scans
app.get("/orders", async (req, res) => {
  const page = parseInt(req.query.page as string) || 1;
  const limit = parseInt(req.query.limit as string) || 20;
  const offset = (page - 1) * limit;

  // At page 10000: OFFSET 200000 — database scans and discards 200K rows
  const orders = await db.query(
    "SELECT * FROM orders ORDER BY created_at DESC LIMIT $1 OFFSET $2",
    [limit, offset]
  );

  // Total count requires a separate full scan
  const [{ count }] = await db.query("SELECT COUNT(*) as count FROM orders");

  res.json({
    data: orders,
    page,
    totalPages: Math.ceil(count / limit),
    total: count,
  });
});
```

### Good: Cursor-Based Pagination

```typescript
// GOOD: Cursor-based pagination with opaque cursors
interface PaginatedResponse<T> {
  data: T[];
  pageInfo: {
    hasNextPage: boolean;
    hasPreviousPage: boolean;
    startCursor: string | null;
    endCursor: string | null;
  };
}

function encodeCursor(id: string, createdAt: Date): string {
  return Buffer.from(JSON.stringify({ id, createdAt })).toString("base64url");
}

function decodeCursor(cursor: string): { id: string; createdAt: Date } {
  const parsed = JSON.parse(Buffer.from(cursor, "base64url").toString());
  return { id: parsed.id, createdAt: new Date(parsed.createdAt) };
}

app.get("/orders", async (req, res) => {
  const limit = Math.min(parseInt(req.query.limit as string) || 20, 100);
  const after = req.query.after as string | undefined;

  let query = "SELECT * FROM orders";
  const params: unknown[] = [limit + 1]; // Fetch one extra to detect hasNextPage

  if (after) {
    const cursor = decodeCursor(after);
    query += " WHERE (created_at, id) < ($2, $3)";
    params.push(cursor.createdAt, cursor.id);
  }

  query += " ORDER BY created_at DESC, id DESC LIMIT $1";

  const rows = await db.query(query, params);
  const hasNextPage = rows.length > limit;
  const data = hasNextPage ? rows.slice(0, limit) : rows;

  const response: PaginatedResponse<Order> = {
    data,
    pageInfo: {
      hasNextPage,
      hasPreviousPage: !!after,
      startCursor: data.length > 0
        ? encodeCursor(data[0].id, data[0].created_at)
        : null,
      endCursor: data.length > 0
        ? encodeCursor(data[data.length - 1].id, data[data.length - 1].created_at)
        : null,
    },
  };

  res.json(response);
});
```

### Good: Keyset Pagination with Composite Sort

```typescript
// GOOD: Keyset pagination using indexed columns directly
interface KeysetParams {
  limit: number;
  afterCreatedAt?: Date;
  afterId?: string;
  sortDirection: "asc" | "desc";
}

async function paginateOrders(params: KeysetParams): Promise<{
  data: Order[];
  nextCursor: { createdAt: Date; id: string } | null;
}> {
  const { limit, afterCreatedAt, afterId, sortDirection } = params;
  const fetchLimit = limit + 1;

  let query: string;
  let queryParams: unknown[];

  if (afterCreatedAt && afterId) {
    const op = sortDirection === "desc" ? "<" : ">";
    query = `
      SELECT * FROM orders
      WHERE (created_at, id) ${op} ($2, $3)
      ORDER BY created_at ${sortDirection}, id ${sortDirection}
      LIMIT $1
    `;
    queryParams = [fetchLimit, afterCreatedAt, afterId];
  } else {
    query = `
      SELECT * FROM orders
      ORDER BY created_at ${sortDirection}, id ${sortDirection}
      LIMIT $1
    `;
    queryParams = [fetchLimit];
  }

  const rows: Order[] = await db.query(query, queryParams);
  const hasMore = rows.length > limit;
  const data = hasMore ? rows.slice(0, limit) : rows;
  const last = data[data.length - 1];

  return {
    data,
    nextCursor: hasMore ? { createdAt: last.created_at, id: last.id } : null,
  };
}
```

## Alternatives

| Approach | Best For | Trade-off |
|----------|----------|-----------|
| **Offset** | Admin UIs, simple lists, "jump to page" required | Breaks at scale, unstable under mutations |
| **Cursor** | Public APIs, infinite scroll, mobile apps | No random page access |
| **Keyset** | Large datasets with clear sort order | Sort must match available indexes |
| **Seek method (proprietary)** | Complex multi-column sorts | Vendor-specific implementations |
| **Search-after (Elasticsearch)** | Full-text search results | Tied to Elasticsearch's API |

## When NOT to Apply

- **Small datasets (< 1000 rows)**: If the total dataset fits comfortably in a single response, pagination adds unnecessary complexity. Return everything.
- **Export/bulk operations**: Pagination is for interactive use. For bulk data export, use streaming, database cursors, or file-based export.
- **When users genuinely need page N**: Cursor pagination cannot jump to an arbitrary page. If your UI requires "go to page 47," offset is the only option (accept the cost).

## Trade-offs

- **Offset is universally understood** but fundamentally broken for deep pages and unstable when data is inserted or deleted between page fetches.
- **Cursor pagination is the industry standard** for public APIs but eliminates the "total count" and "jump to page" features that some UIs require.
- **Total counts are expensive.** `SELECT COUNT(*)` on large tables is slow in PostgreSQL. Consider caching counts, returning estimates (`reltuples` from `pg_class`), or omitting totals entirely.
- **Composite cursors** are essential when sort columns have duplicate values. Sorting by `created_at` alone fails when multiple rows share the same timestamp. Always include a unique tiebreaker (typically the primary key).

## Further Reading

- [Slack API — Pagination](https://api.slack.com/docs/pagination)
- [Use the Index, Luke — Pagination Done the Right Way](https://use-the-index-luke.com/no-offset)
- [Relay Specification — Cursor Connections](https://relay.dev/graphql/connections.htm)
- [Markus Winand — We Need Tool Support for Keyset Pagination](https://use-the-index-luke.com/blog/2019-11/we-need-tool-support-for-keyset-pagination)
