# Polyglot Persistence

## Origin

The term "polyglot persistence" was coined by Scott Leberknight in 2008 and popularized by Martin Fowler and Pramod Sadalage. It emerged as a counter to the "one database for everything" mindset that dominated the RDBMS era. The explosion of NoSQL databases in the late 2000s (MongoDB, Cassandra, Redis, Neo4j) made it clear that different data access patterns benefit from different storage engines. The principle: use the right database for the job, not one database for all jobs.

## Explanation

### The Core Idea

Instead of forcing all data into a single database technology, match each data access pattern to the storage engine optimized for it:

| Data Pattern | Optimal Storage | Why |
|-------------|----------------|-----|
| Transactional CRUD | PostgreSQL, MySQL | ACID guarantees, mature tooling |
| Full-text search | Elasticsearch, Meilisearch | Inverted indexes, relevance scoring |
| Caching / sessions | Redis, Memcached | Sub-millisecond reads, TTL support |
| Time-series metrics | TimescaleDB, InfluxDB | Time-based partitioning, rollups |
| Graph traversals | Neo4j, Amazon Neptune | Relationship-first queries |
| Document storage | MongoDB, DynamoDB | Flexible schema, horizontal scaling |
| Wide-column analytics | Cassandra, ScyllaDB | Write-heavy, partition-key access |
| Message queuing | Kafka, RabbitMQ | Ordered streams, consumer groups |
| Blob storage | S3, MinIO | Large binary objects, cheap at scale |

### Decision Framework

1. **What are the read patterns?** Key-value lookup? Full-text search? Graph traversal? Aggregation?
2. **What are the write patterns?** Transactional? Append-only? High throughput?
3. **What consistency is required?** Strong (ACID)? Eventual? Causal?
4. **What is the data lifecycle?** Short-lived (cache)? Permanent (ledger)? Time-boxed (metrics)?
5. **What is the team's operational capacity?** Each database is an additional system to monitor, backup, upgrade, and debug.

## TypeScript Code Examples

### Bad: One Database for Everything

```typescript
// BAD: Using PostgreSQL for everything, even where it's a poor fit
class UniversalRepository {
  // Relational data — fine
  async getOrder(id: string): Promise<Order> {
    return db.query("SELECT * FROM orders WHERE id = $1", [id]);
  }

  // Full-text search — PostgreSQL can do this, but it's mediocre at scale
  async searchProducts(query: string): Promise<Product[]> {
    return db.query(
      "SELECT * FROM products WHERE to_tsvector(name || ' ' || description) @@ plainto_tsquery($1)",
      [query]
    );
    // No relevance tuning, no fuzzy matching, no synonyms, no facets
  }

  // Session storage — using PostgreSQL for ephemeral 15-minute sessions
  async getSession(sessionId: string): Promise<Session | null> {
    return db.query("SELECT * FROM sessions WHERE id = $1 AND expires_at > NOW()", [sessionId]);
    // Full ACID overhead for throwaway data. Disk I/O for every page load.
  }

  // Caching — storing computed results in PostgreSQL
  async getCachedDashboard(userId: string): Promise<DashboardData | null> {
    return db.query(
      "SELECT data FROM cache WHERE key = $1 AND expires_at > NOW()",
      [`dashboard:${userId}`]
    );
    // Why is your cache backed by the same disk as your transactions?
  }
}
```

### Good: Purpose-Matched Storage

```typescript
// GOOD: Each storage engine matched to its access pattern
import { Pool } from "pg";
import Redis from "ioredis";
import { Client as ElasticClient } from "@elastic/elasticsearch";

// PostgreSQL for transactional data
const pg = new Pool({ connectionString: process.env.DATABASE_URL });

// Redis for caching, sessions, and rate limiting
const redis = new Redis(process.env.REDIS_URL);

// Elasticsearch for search
const elastic = new ElasticClient({ node: process.env.ELASTICSEARCH_URL });

class OrderRepository {
  // Transactional operations belong in PostgreSQL
  async create(order: CreateOrderInput): Promise<Order> {
    return pg.query(
      `INSERT INTO orders (customer_id, status, total_cents)
       VALUES ($1, 'pending', $2) RETURNING *`,
      [order.customerId, order.totalCents]
    );
  }

  async findById(id: string): Promise<Order | null> {
    // Check cache first
    const cached = await redis.get(`order:${id}`);
    if (cached) return JSON.parse(cached);

    // Cache miss — query PostgreSQL
    const result = await pg.query("SELECT * FROM orders WHERE id = $1", [id]);
    const order = result.rows[0] ?? null;

    if (order) {
      await redis.setex(`order:${id}`, 300, JSON.stringify(order)); // 5 min cache
    }

    return order;
  }
}

class ProductSearchService {
  // Full-text search belongs in Elasticsearch
  async search(query: string, filters: SearchFilters): Promise<SearchResult> {
    const result = await elastic.search({
      index: "products",
      body: {
        query: {
          bool: {
            must: [
              {
                multi_match: {
                  query,
                  fields: ["name^3", "description", "category"],
                  fuzziness: "AUTO",
                },
              },
            ],
            filter: [
              ...(filters.category ? [{ term: { category: filters.category } }] : []),
              ...(filters.minPrice ? [{ range: { price: { gte: filters.minPrice } } }] : []),
            ],
          },
        },
        aggs: {
          categories: { terms: { field: "category.keyword" } },
          price_ranges: {
            range: { field: "price", ranges: [{ to: 50 }, { from: 50, to: 200 }, { from: 200 }] },
          },
        },
      },
    });

    return mapSearchResult(result);
  }
}

class SessionStore {
  // Sessions belong in Redis — ephemeral, fast, TTL built-in
  async create(userId: string): Promise<string> {
    const sessionId = generateSecureId();
    const session = { userId, createdAt: Date.now() };
    await redis.setex(`session:${sessionId}`, 900, JSON.stringify(session)); // 15 min
    return sessionId;
  }

  async get(sessionId: string): Promise<Session | null> {
    const data = await redis.get(`session:${sessionId}`);
    return data ? JSON.parse(data) : null;
  }

  async destroy(sessionId: string): Promise<void> {
    await redis.del(`session:${sessionId}`);
  }
}
```

### Good: Keeping Stores in Sync

```typescript
// GOOD: Event-driven synchronization between stores
// PostgreSQL is the source of truth; other stores are derived

async function onProductUpdated(event: ProductUpdatedEvent): Promise<void> {
  const product = await pg.query("SELECT * FROM products WHERE id = $1", [event.productId]);

  // Sync to Elasticsearch for search
  await elastic.index({
    index: "products",
    id: event.productId,
    body: {
      name: product.name,
      description: product.description,
      category: product.category,
      price: product.priceCents / 100,
      updatedAt: new Date(),
    },
  });

  // Invalidate cache
  await redis.del(`product:${event.productId}`);

  console.log(`Synced product ${event.productId} to Elasticsearch and invalidated cache`);
}
```

## Alternatives

| Approach | Best For | Trade-off |
|----------|----------|-----------|
| **PostgreSQL for (almost) everything** | Small-to-medium apps, limited ops capacity | Acceptable until you hit specific bottlenecks |
| **Managed multi-model databases** (Cosmos DB, FaunaDB) | Reducing operational overhead | Vendor lock-in, less optimal per-use-case |
| **Data mesh** | Large organizations with domain teams | Organizational pattern, not just technical |
| **Data lake + serving layer** | Analytics-heavy workloads | Complex pipeline, latency to insights |

## When NOT to Apply

- **Small teams or early-stage products**: Every additional database is a system to operate — backups, monitoring, upgrades, failover. If PostgreSQL handles your workload, do not add complexity.
- **When PostgreSQL extensions suffice**: pg_trgm for fuzzy text search, JSONB for document patterns, and TimescaleDB for time-series can defer the need for separate databases.
- **When you lack operational maturity**: Running Elasticsearch, Redis, and PostgreSQL reliably requires expertise in each. If your team cannot operate a database well, adding more databases makes everything worse.
- **Prototype and MVP phase**: Use one database. Prove the product first. Add specialized storage when you have proven bottlenecks.

## Trade-offs

- **Optimal reads vs. operational complexity**: Each database engine is another system to monitor, patch, scale, and debug. The performance gain must justify the operational cost.
- **Data consistency**: Data spread across multiple stores will diverge. You need synchronization mechanisms (events, CDC, dual-writes) and must accept eventual consistency between stores.
- **Query joins across stores**: You cannot SQL JOIN data from PostgreSQL and Elasticsearch. Application-level joins or data duplication are required.
- **Team knowledge**: Each database has its own query language, indexing strategy, failure modes, and operational runbook. Ensure your team has (or can acquire) expertise in each system you adopt.
- **Backup and disaster recovery**: Each additional database needs its own backup strategy, retention policy, and restore procedure. Test recovery for every store.

## Further Reading

- [Martin Fowler — Polyglot Persistence](https://martinfowler.com/bliki/PolyglotPersistence.html)
- [Pramod Sadalage & Martin Fowler — NoSQL Distilled](https://www.nosqldistilled.com/)
- [Designing Data-Intensive Applications — Martin Kleppmann](https://dataintensive.net/)
- [AWS — Choosing the Right Database](https://aws.amazon.com/products/databases/)
