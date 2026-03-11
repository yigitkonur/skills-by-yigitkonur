# Performance Review Checklist

Patterns and anti-patterns to check during PR review when evaluating performance impact. Focus on issues that degrade at scale — not micro-optimizations.

---

## When to Apply Performance Review

Not every PR needs a performance deep-dive. Trigger detailed performance review when:

- PR adds or modifies database queries
- PR introduces loops that process collections of unknown size
- PR adds new API endpoints that aggregate data
- PR modifies hot paths (auth middleware, request handlers, event loops)
- PR adds file I/O, network calls, or external service integrations
- PR changes caching, indexing, or pagination logic

Skip detailed performance review for:
- Documentation-only changes
- Test-only changes (unless testing performance)
- Config changes that don't affect runtime behavior
- UI-only changes that don't affect data fetching

---

## Database Query Patterns

### N+1 Query Detection

The single most common performance bug in PRs. Occurs when code fetches a list, then queries for related data per item.

**Pattern to watch for:**
```javascript
// N+1 PROBLEM — 1 query + N queries
const users = await db.query('SELECT * FROM users');
for (const user of users) {
  const orders = await db.query('SELECT * FROM orders WHERE user_id = ?', [user.id]);
  user.orders = orders;
}

// FIX — single query with JOIN or batch
const users = await db.query(`
  SELECT u.*, o.* FROM users u
  LEFT JOIN orders o ON o.user_id = u.id
`);

// FIX — batch query
const users = await db.query('SELECT * FROM users');
const userIds = users.map(u => u.id);
const orders = await db.query('SELECT * FROM orders WHERE user_id IN (?)', [userIds]);
```

**ORM variants (equally dangerous):**
```python
# N+1 in Django
for post in Post.objects.all():
    print(post.author.name)  # Lazy load triggers N queries

# FIX
for post in Post.objects.select_related('author').all():
    print(post.author.name)  # Single JOIN query
```

```javascript
// N+1 in Prisma
const posts = await prisma.post.findMany();
for (const post of posts) {
  const author = await prisma.user.findUnique({ where: { id: post.authorId } });
}

// FIX
const posts = await prisma.post.findMany({ include: { author: true } });
```

### Unbounded Queries

Queries that return unlimited results are time bombs — they work fine with 100 rows and crash the server with 100,000.

```javascript
// DANGEROUS — no limit
const users = await db.query('SELECT * FROM users');

// SAFE — paginated
const users = await db.query('SELECT * FROM users LIMIT ? OFFSET ?', [pageSize, offset]);

// DANGEROUS — ORM without limit
const posts = await Post.findAll();

// SAFE — ORM with limit
const posts = await Post.findAll({ limit: 50, offset: page * 50 });
```

**Red flags:**
- `SELECT *` without `LIMIT`
- `.findAll()` / `.find({})` without pagination
- API endpoints that return entire collections
- Export/report endpoints that load all data into memory

### Missing Indexes

When a PR adds new query patterns, verify indexes exist for the WHERE clause columns.

```sql
-- New query pattern introduced in PR
SELECT * FROM orders WHERE status = 'pending' AND created_at > '2024-01-01';

-- Check: does an index exist on (status, created_at)?
-- If not, flag as 🟡 Important for tables >10k rows
```

**When to flag missing indexes:**
- New WHERE clause on columns without indexes
- New JOIN conditions on unindexed foreign keys
- New ORDER BY on unindexed columns for large tables
- Composite queries that would benefit from compound indexes

### Query Inside Transaction Scope

```javascript
// DANGEROUS — long transaction holds locks
await db.transaction(async (tx) => {
  const users = await tx.query('SELECT * FROM users');
  for (const user of users) {
    await sendEmail(user.email);  // Network call inside transaction!
    await tx.query('UPDATE users SET notified = true WHERE id = ?', [user.id]);
  }
});

// SAFE — minimize transaction scope
const users = await db.query('SELECT * FROM users WHERE notified = false');
for (const user of users) {
  await sendEmail(user.email);
}
await db.query('UPDATE users SET notified = true WHERE id IN (?)', [users.map(u => u.id)]);
```

---

## Memory Patterns

### Unbounded Collections

```javascript
// DANGEROUS — accumulates indefinitely
const allResults = [];
while (hasMore) {
  const page = await fetchPage(cursor);
  allResults.push(...page.items);  // Memory grows without bound
  cursor = page.nextCursor;
  hasMore = !!cursor;
}

// SAFE — stream/process per page
while (hasMore) {
  const page = await fetchPage(cursor);
  await processItems(page.items);  // Process and discard
  cursor = page.nextCursor;
  hasMore = !!cursor;
}
```

### Large File Loading

```javascript
// DANGEROUS — loads entire file into memory
const content = fs.readFileSync('large-export.csv', 'utf-8');
const lines = content.split('\n');

// SAFE — stream line by line
const rl = readline.createInterface({ input: fs.createReadStream('large-export.csv') });
for await (const line of rl) {
  processLine(line);
}
```

### Object Cloning in Hot Paths

```javascript
// DANGEROUS — deep clone on every request
app.get('/api/config', (req, res) => {
  const config = JSON.parse(JSON.stringify(globalConfig));  // O(n) clone
  config.user = req.user;
  res.json(config);
});

// SAFE — shallow spread or targeted copy
app.get('/api/config', (req, res) => {
  res.json({ ...globalConfig, user: req.user });
});
```

---

## Network and I/O Patterns

### Missing Timeouts

```javascript
// DANGEROUS — no timeout, one slow service blocks everything
const response = await fetch('https://external-api.com/data');

// SAFE — explicit timeout
const controller = new AbortController();
const timeout = setTimeout(() => controller.abort(), 5000);
const response = await fetch('https://external-api.com/data', {
  signal: controller.signal,
});
clearTimeout(timeout);
```

**Every outbound HTTP request should have an explicit timeout.** Missing timeouts on external calls are a silent killer — one slow downstream service can exhaust the connection pool and bring down the entire application.

### Missing Retry with Backoff

```javascript
// DANGEROUS — single attempt, transient errors cause failures
const response = await fetch(url);

// SAFE — retry with exponential backoff
async function fetchWithRetry(url, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fetch(url, { signal: AbortSignal.timeout(5000) });
    } catch (err) {
      if (i === maxRetries - 1) throw err;
      await new Promise(r => setTimeout(r, Math.pow(2, i) * 1000));
    }
  }
}
```

### Sequential vs Parallel Requests

```javascript
// SLOW — sequential (total = sum of all response times)
const users = await fetchUsers();
const orders = await fetchOrders();
const products = await fetchProducts();

// FAST — parallel (total = max response time)
const [users, orders, products] = await Promise.all([
  fetchUsers(),
  fetchOrders(),
  fetchProducts(),
]);
```

---

## Algorithmic Complexity Red Flags

| Pattern | Complexity | Fix |
|---------|-----------|-----|
| Nested loops over same collection | O(n²) | Use Set/Map for lookups |
| Array `.find()` inside loop | O(n²) | Pre-index with Map |
| Array `.includes()` on large arrays | O(n) per check | Convert to Set for O(1) |
| Sorting inside a loop | O(n² log n) | Sort once before loop |
| String concatenation in loop | O(n²) for many languages | Use StringBuilder/join |
| Recursive function without memoization | Potentially O(2ⁿ) | Add memoization cache |
| Linear scan for lookup | O(n) | Use hash map for O(1) |

### Example: O(n²) hidden in innocent code

```javascript
// O(n²) — .includes() is O(n) called n times
const unique = [];
for (const item of items) {
  if (!unique.includes(item)) {
    unique.push(item);
  }
}

// O(n) — Set handles deduplication
const unique = [...new Set(items)];
```

---

## Caching Concerns

When reviewing caching changes:

| Check | Question | Red Flag |
|-------|----------|----------|
| Cache invalidation | Is the cache cleared when source data changes? | Data mutated but cache not invalidated |
| Cache key design | Are cache keys specific enough to avoid collisions? | Same key for different users/contexts |
| Cache TTL | Is the TTL appropriate for the data's staleness tolerance? | No TTL (stale forever) or TTL too long |
| Cache size | Is the cache bounded? | Unbounded cache that grows with data |
| Thundering herd | Is there protection against simultaneous cache misses? | All requests rebuild cache at once |

---

## Performance Severity Guide

| Finding | Severity | Condition |
|---------|----------|-----------|
| N+1 query in frequently called path | 🟡 Important | Endpoint called >100x/day |
| N+1 query in admin/rare path | 🟢 Suggestion | Endpoint called rarely |
| Unbounded query (no LIMIT) | 🟡 Important | Table will grow over time |
| Missing timeout on external call | 🟡 Important | Always — cascading failure risk |
| O(n²) algorithm on small data | 🟢 Suggestion | n < 100 in practice |
| O(n²) algorithm on unbounded data | 🟡 Important | n grows with usage |
| Memory leak (event listener, cache) | 🟡 Important | In long-running process |
| Missing index on new query | 🟡 Important | Table > 10k rows |
| Unnecessary deep clone | 🟢 Suggestion | Unless in hot path |
| Sequential requests (parallelizable) | 🟢 Suggestion | Unless latency-critical |

**Calibration rule:** Only flag performance issues that are measurably impactful at current or near-future scale. "This could theoretically be slow" is not actionable. "This query scans 100k rows without an index" is actionable.
