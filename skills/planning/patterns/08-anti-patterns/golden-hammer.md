# Golden Hammer

## Origin

Abraham Maslow, 1966: "If all you have is a hammer, everything looks like a nail." Adapted to software engineering in Brown et al., *AntiPatterns* (1998) as the "Golden Hammer" — a familiar technology or approach applied to every problem regardless of fit.

## Explanation

The Golden Hammer occurs when a team or developer becomes so comfortable with a particular technology, pattern, or approach that they use it for everything — even when it is a poor fit. It is driven by familiarity bias: the known tool feels safer and faster than learning a new one, even when the new tool would be significantly better.

This is not about having preferences. It is about applying those preferences without evaluating whether they fit the problem at hand.

## TypeScript Code Examples

### Bad: Using a Relational Database for Everything

```typescript
// "We use PostgreSQL for everything" — even when it is the wrong tool.

// Time-series metrics: 10,000 writes/second, mostly append, range queries
// PostgreSQL can do this, but a time-series DB (TimescaleDB, InfluxDB) is purpose-built.
await db.query(`
  INSERT INTO metrics (timestamp, service, cpu_usage, memory_usage)
  VALUES ($1, $2, $3, $4)
`, [new Date(), "api-server", 0.75, 0.62]);

// Full-text search: fuzzy matching, relevance scoring, faceted search
// PostgreSQL has tsvector, but Elasticsearch/Meilisearch does this natively.
const results = await db.query(`
  SELECT *, ts_rank(search_vector, plainto_tsquery($1)) AS rank
  FROM products
  WHERE search_vector @@ plainto_tsquery($1)
  ORDER BY rank DESC
  LIMIT 20
`, [userQuery]);
// Works, but lacks typo tolerance, synonyms, faceting, and is slow at scale.

// Caching: read-heavy, key-value lookups, sub-millisecond latency needed
// PostgreSQL roundtrip is 1-5ms. Redis roundtrip is 0.1-0.5ms.
const cached = await db.query(
  "SELECT value FROM cache WHERE key = $1 AND expires_at > NOW()",
  [cacheKey]
);
// Using a relational database as a cache because "we already have Postgres."
```

### Good: Right Tool for Each Job

```typescript
// Each data store chosen for its strengths

// Relational data: PostgreSQL — perfect fit
const user = await pgPool.query(
  "SELECT * FROM users WHERE id = $1",
  [userId]
);

// Time-series metrics: TimescaleDB (PostgreSQL extension) or InfluxDB
await tsdb.write({
  measurement: "api_metrics",
  tags: { service: "api-server" },
  fields: { cpu: 0.75, memory: 0.62 },
  timestamp: new Date(),
});

// Full-text search: Elasticsearch or Meilisearch
const searchResults = await meilisearch.index("products").search(userQuery, {
  attributesToHighlight: ["name", "description"],
  facets: ["category", "brand"],
  limit: 20,
});

// Caching: Redis — sub-millisecond key-value lookups
const cached = await redis.get(cacheKey);
if (cached) return JSON.parse(cached);
```

### Bad: Using React for Everything

```typescript
// "We're a React shop" — even for a static marketing page

// Marketing landing page: no interactivity, SEO-critical, fast load needed
// Built as a React SPA with client-side rendering anyway:
function LandingPage() {
  const [content, setContent] = useState<Content | null>(null);
  useEffect(() => {
    fetch("/api/landing-content").then((r) => r.json()).then(setContent);
  }, []);
  if (!content) return <Spinner />;  // SEO: Google sees a spinner
  return <div dangerouslySetInnerHTML={{ __html: content.html }} />;
}

// The page could be static HTML generated at build time.
// React adds 40KB+ of JavaScript for zero interactivity.
```

### Good: Match Rendering Strategy to Requirements

```typescript
// Static marketing page: use a static site generator or plain HTML
// Result: zero JavaScript, instant load, perfect SEO

// Interactive dashboard: React is a great fit
// Complex state management, real-time updates, component reuse
function Dashboard() {
  const metrics = useRealTimeMetrics();
  const filters = useFilterState();
  return (
    <DashboardLayout>
      <FilterPanel filters={filters} />
      <MetricsGrid data={metrics} />
      <AlertsTimeline />
    </DashboardLayout>
  );
}

// CLI tool: no framework needed, plain TypeScript/Node.js
// "Should we use React Ink for this?" — No. It's a 10-line script.
```

## Technology Monoculture Risks

| Monoculture Pattern | Risk |
|---|---|
| One language for everything | Cannot exploit language-specific strengths |
| One database for everything | Performance bottlenecks for wrong workloads |
| One framework for everything | Overengineered simple things, underserved complex things |
| One cloud provider for everything | Vendor lock-in, pricing leverage loss |
| One testing approach for everything | Missing entire categories of defects |

## Alternatives and Related Concepts

- **Polyglot persistence:** Use different databases for different data patterns.
- **Polyglot programming:** Use the language best suited to each problem domain.
- **Technology radar:** Regularly evaluate new tools against current stack.
- **Spike/prototype:** Before committing to a tool for a new problem, spend a day prototyping with the right tool.

## When NOT to Apply (When a Golden Hammer Is Justified)

- **Small teams with limited capacity:** Learning a new database, language, or framework has real costs. A team of three may be right to use PostgreSQL for everything rather than operating five data stores.
- **Operational overhead:** Each technology adds deployment, monitoring, alerting, and on-call burden. The "right tool" must justify its operational cost.
- **Short-lived projects:** A prototype that will be rewritten in six months does not need optimal technology choices.
- **Hiring constraints:** If your market has abundant Java developers but few Rust developers, using Java for a performance-sensitive service may be pragmatic.

## Trade-offs

| Approach | Benefit | Cost |
|---|---|---|
| Golden Hammer (one tool) | Low learning curve, simple operations | Suboptimal solutions, scaling limits |
| Right tool for every job | Optimal per-problem solutions | Operational complexity, fragmented expertise |
| Small polyglot (2-3 core tools) | Balance of optimization and simplicity | Some compromise on both sides |
| Periodic technology evaluation | Prevents stagnation | Evaluation takes time, may trigger churn |

## Real-World Consequences

- **MongoDB for everything (2012-2015):** The "MongoDB is web scale" era saw teams using a document database for relational data, losing joins, transactions, and consistency guarantees.
- **Microservices as Golden Hammer:** "Every new feature gets its own microservice" — even when a module in the monolith would suffice. Result: distributed monolith with network latency.
- **Kubernetes for everything:** Running a single-container application on Kubernetes because "we're a Kubernetes shop." The operational overhead dwarfs the application.
- **Excel as Golden Hammer:** Finance teams running critical business logic in spreadsheets because Excel is what they know. The UK's COVID test-and-trace program lost 16,000 records because Excel has a row limit.

## Further Reading

- Brown, W. et al. (1998). *AntiPatterns: Refactoring Software, Architectures, and Projects in Crisis*
- Sadalage, P. & Fowler, M. (2012). *NoSQL Distilled* — polyglot persistence
- ThoughtWorks Technology Radar — quarterly technology evaluation framework
- Kleppmann, M. (2017). *Designing Data-Intensive Applications* — choosing the right data store
