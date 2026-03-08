# 10 — Data Modeling

Patterns for structuring, evolving, and managing data in relational databases and beyond. Focused on the decisions that determine whether your data layer is an asset or a liability.

## Contents

| # | Pattern | Summary | Key Decision |
|---|---------|---------|--------------|
| 1 | [Normalization](./normalization.md) | 1NF through BCNF, update anomalies, when normalization is the right default | How should I structure my tables? |
| 2 | [Denormalization](./denormalization.md) | Strategic denormalization, materialized views, precomputed aggregates | How do I speed up reads without sacrificing integrity? |
| 3 | [Schema Evolution](./schema-evolution.md) | Backward/forward compatibility, expand-contract pattern, zero-downtime migrations | How do I change my schema without breaking consumers? |
| 4 | [Event Sourcing Data](./event-sourcing-data.md) | Events as source of truth, projections, snapshots | Should I store state or history? |
| 5 | [Polyglot Persistence](./polyglot-persistence.md) | Right database for the job, decision framework | Should I use more than one database? |
| 6 | [Domain Modeling](./domain-modeling.md) | Aggregates, entities vs value objects, consistency boundaries | Where are my transactional boundaries? |
| 7 | [Soft Delete vs Hard Delete](./soft-delete-vs-hard-delete.md) | Soft deletes, hard deletes, GDPR, archival tables | How should I handle data deletion? |

## Decision Flowchart

### "How should I structure my data?"

```
Start with normalized tables (3NF).
  |
  v
Are read queries too slow after proper indexing?
  NO  --> Stay normalized. You are done.
  YES --> Is the bottleneck join cost or aggregation cost?
            |
            +-- Join cost --> Denormalize with duplicated fields or materialized views
            |                 (see denormalization.md)
            |
            +-- Aggregation --> Precomputed summary tables or materialized views
                                (see denormalization.md)
```

### "Do I need event sourcing?"

```
Does the business need a complete history of every state change?
  NO  --> Use CRUD. Add an audit log if you need some history.
  YES --> Is the domain complex with clear state machine transitions?
            NO  --> An audit log table is likely sufficient.
            YES --> Does the team have DDD experience?
                      NO  --> Start with CRUD + audit log. Learn DDD first.
                      YES --> Event sourcing is appropriate.
                              (see event-sourcing-data.md)
```

### "Should I use multiple databases?"

```
Can PostgreSQL handle all your access patterns with extensions?
  YES --> Use PostgreSQL. One database to operate is a gift.
  NO  --> Which pattern is bottlenecked?
            |
            +-- Full-text search    --> Add Elasticsearch
            +-- Caching / sessions  --> Add Redis
            +-- Time-series metrics --> Add TimescaleDB (PG extension) or InfluxDB
            +-- Graph traversals    --> Add Neo4j
            +-- High-write append   --> Add Kafka / Cassandra
            |
            (see polyglot-persistence.md)
```

### "How should I handle deletion?"

```
Is this personal data subject to GDPR / privacy regulation?
  YES --> Hard delete or anonymize. Soft delete does NOT satisfy erasure requirements.
          (see soft-delete-vs-hard-delete.md)
  NO  --> Do users need an "undo" or "restore" feature?
            YES --> Soft delete with enforced query filtering
                    OR archive table pattern
            NO  --> Hard delete. Simple is better.
                    Add an audit log if you need deletion records.
```

### "How do I evolve my schema safely?"

```
Is this a breaking change? (rename, remove, type change)
  NO  --> Add the column/field with a default. Deploy. Done.
  YES --> Are there multiple consumers or rolling deployments?
            NO  --> Direct migration in a maintenance window is acceptable.
            YES --> Use the expand-contract pattern:
                    1. Expand: add new alongside old
                    2. Migrate: switch reads, backfill
                    3. Contract: remove old
                    (see schema-evolution.md)
```

## Cross-References

- **API Design (Section 09)**: Data models directly influence API design. Normalized data often maps to REST resources. Denormalized read models often power GraphQL resolvers.
- **Event Sourcing Data + Domain Modeling**: These two patterns are deeply connected. Event sourcing is the persistence mechanism; domain modeling (aggregates) defines the consistency boundaries that events operate within.
- **Normalization + Denormalization**: Read them as a pair. Normalization is the default; denormalization is the measured response to proven read bottlenecks.
- **Schema Evolution + API Versioning**: Database schema evolution and API versioning are the same problem at different layers. The expand-contract pattern applies to both.

## Recommended Reading Order

1. **Normalization** — the foundation; everything else builds on understanding why normalization matters
2. **Domain Modeling** — how to think about consistency boundaries before writing SQL
3. **Denormalization** — when and how to intentionally break normalization rules
4. **Soft Delete vs Hard Delete** — a concrete, everyday decision every project faces
5. **Schema Evolution** — essential before your first production migration
6. **Polyglot Persistence** — when PostgreSQL is not enough
7. **Event Sourcing Data** — read last, only when you have a genuine use case
