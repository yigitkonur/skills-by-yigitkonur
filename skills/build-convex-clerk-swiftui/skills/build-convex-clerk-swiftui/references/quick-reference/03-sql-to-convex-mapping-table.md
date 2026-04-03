# SQL to Convex Mapping Table

## Use This When
- Translating SQL instincts into Convex patterns.
- Helping a team member who knows SQL but not Convex.
- Quick lookup for how a specific SQL operation maps to Convex API calls.

## Core Operations

```
+----------------------+----------------------------------------------+
| SQL                  | Convex                                       |
+----------------------+----------------------------------------------+
| CREATE TABLE         | defineTable({...}) in schema.ts              |
| ALTER TABLE          | Edit defineTable + push (auto-migrates)      |
| DROP TABLE           | Remove from schema (data preserved)          |
| INSERT INTO          | ctx.db.insert("table", {...})                |
| UPDATE ... SET       | ctx.db.patch(id, {...})  (merge)             |
| UPDATE (full)        | ctx.db.replace(id, {...})  (overwrite)       |
| DELETE FROM          | ctx.db.delete(id)                            |
| SELECT * FROM        | ctx.db.query("table").collect()              |
| SELECT ... BY ID     | ctx.db.get(id)                               |
| TRANSACTION          | Mutations are always transactional            |
+----------------------+----------------------------------------------+
```

## Filtering (WHERE)

```
+----------------------------+----------------------------------------+
| SQL                        | Convex                                 |
+----------------------------+----------------------------------------+
| WHERE col = 'val'          | .withIndex("by_col",                  |
|                            |   q => q.eq("col", "val"))            |
+----------------------------+----------------------------------------+
| WHERE col > 10             | .withIndex("by_col",                  |
|                            |   q => q.gt("col", 10))               |
+----------------------------+----------------------------------------+
| WHERE a = 1 AND b > 5     | .withIndex("by_a_b",                  |
|                            |   q => q.eq("a", 1).gt("b", 5))      |
+----------------------------+----------------------------------------+
| WHERE col IN (1,2,3)      | No direct equivalent.                  |
|                            | Options:                               |
|                            |   1. Multiple queries + merge          |
|                            |   2. .filter() (full table scan!)      |
+----------------------------+----------------------------------------+
| WHERE a = 1 OR b = 2      | No direct equivalent.                  |
|                            | Options:                               |
|                            |   1. Two queries + merge + dedupe      |
|                            |   2. .filter() (full table scan!)      |
+----------------------------+----------------------------------------+
| WHERE col LIKE '%text%'   | .withSearchIndex("search_col", q =>   |
|                            |   q.search("col", "text"))            |
|                            | (full-text search, not substring)      |
+----------------------------+----------------------------------------+
| WHERE col IS NULL          | Store as undefined (omit field) or    |
|                            | use v.optional() + .filter()           |
+----------------------------+----------------------------------------+
```

## Ordering and Limiting

```
+----------------------+----------------------------------------------+
| SQL                  | Convex                                       |
+----------------------+----------------------------------------------+
| ORDER BY col ASC     | .order("asc")  (default)                    |
|                      | Ordering is by _creationTime within index    |
| ORDER BY col DESC    | .order("desc")                               |
|                      | For custom sort: use index field order       |
+----------------------+----------------------------------------------+
| LIMIT 10             | .take(10)                                    |
| LIMIT 10 OFFSET 20  | No built-in offset. Use cursor-based:       |
|                      |   .take(limit+1), check if extra exists     |
+----------------------+----------------------------------------------+
| SELECT TOP 1         | .first()                                     |
| ... LIMIT 1          | .unique() (throws if >1 result)             |
+----------------------+----------------------------------------------+
```

## Joins and Relations

```
+----------------------------+----------------------------------------+
| SQL                        | Convex                                 |
+----------------------------+----------------------------------------+
| JOIN                       | No JOINs. Instead:                    |
|                            |   const msg = await ctx.db.get(id);   |
|                            |   const author = await               |
|                            |     ctx.db.get(msg.authorId);         |
+----------------------------+----------------------------------------+
| LEFT JOIN                  | Same as above; check for null:        |
|                            |   const author = await               |
|                            |     ctx.db.get(msg.authorId);         |
|                            |   // author may be null               |
+----------------------------+----------------------------------------+
| Subquery                   | Nest queries in handler:              |
|                            |   const msgs = await ctx.db           |
|                            |     .query("messages")...collect();   |
|                            |   return Promise.all(                 |
|                            |     msgs.map(m => ctx.db.get(...))    |
|                            |   );                                  |
+----------------------------+----------------------------------------+
```

## Aggregations

```
+----------------------+----------------------------------------------+
| SQL                  | Convex                                       |
+----------------------+----------------------------------------------+
| COUNT(*)             | No built-in count.                           |
|                      | Options:                                     |
|                      |   1. Maintain a counter field in mutations   |
|                      |   2. .collect().length (small tables only)   |
|                      |   3. @convex-dev/aggregate library           |
+----------------------+----------------------------------------------+
| SUM(col)             | .collect() then reduce in JS                |
| AVG(col)             | Or maintain running totals in mutations      |
| MAX(col) / MIN(col)  | Or use @convex-dev/aggregate                |
+----------------------+----------------------------------------------+
| GROUP BY             | No built-in grouping.                        |
|                      | Options:                                     |
|                      |   1. Multiple indexed queries per group      |
|                      |   2. @convex-dev/aggregate                   |
|                      |   3. Denormalize into summary table          |
+----------------------+----------------------------------------------+
| HAVING               | Filter after manual grouping in JS           |
+----------------------+----------------------------------------------+
```

## Indexing

```
+-----------------------------+---------------------------------------+
| SQL                         | Convex                                |
+-----------------------------+---------------------------------------+
| CREATE INDEX idx            | .index("by_col", ["col"])             |
|   ON table(col)             |   in defineTable()                    |
+-----------------------------+---------------------------------------+
| CREATE INDEX idx            | .index("by_a_b", ["a", "b"])         |
|   ON table(a, b)            |                                       |
+-----------------------------+---------------------------------------+
| CREATE UNIQUE INDEX         | No unique indexes.                    |
|                             | Enforce in mutation: query + check    |
+-----------------------------+---------------------------------------+
| FULLTEXT INDEX              | .searchIndex("search_X", {           |
|                             |   searchField: "body",               |
|                             |   filterFields: ["channelId"]        |
|                             | })                                    |
+-----------------------------+---------------------------------------+
```

## Key Differences from SQL

1. **No ad-hoc queries** -- every filter needs a pre-defined index
2. **No JOINs** -- resolve references with `ctx.db.get()` in code
3. **No OR / IN** -- requires multiple queries or full-table `.filter()`
4. **No aggregations** -- maintain counters or use `@convex-dev/aggregate`
5. **Ordering** -- by `_creationTime` within index range, or define sort field
6. **Pagination** -- cursor-based only, no OFFSET
7. **Transactions** -- every mutation is automatically a transaction
8. **Reactivity** -- queries are subscriptions; SQL requires polling

## Avoid
- Using `.filter()` as a general-purpose WHERE clause -- it scans the entire table.
- Expecting JOIN syntax -- resolve references with sequential `ctx.db.get()` calls.
- Using `.collect().length` for counting on large tables -- maintain counter docs instead.
- Assuming OFFSET-based pagination exists -- use cursor-based patterns with `.take(limit + 1)`.
- Treating Convex indexes like SQL indexes -- Convex indexes must be prefix-complete and support at most one range constraint.

## Read Next
- [01-convex-backend-quick-reference-card.md](01-convex-backend-quick-reference-card.md)
- [04-function-decision-tree.md](04-function-decision-tree.md)
- [../backend/01-schema-document-model-and-relationships.md](../backend/01-schema-document-model-and-relationships.md)
- [../backend/02-indexes-query-shaping-and-performance.md](../backend/02-indexes-query-shaping-and-performance.md)
