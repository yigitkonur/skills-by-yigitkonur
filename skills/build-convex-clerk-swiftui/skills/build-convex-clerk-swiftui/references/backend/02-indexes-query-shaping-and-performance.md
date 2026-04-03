# Indexes, Query Shaping, And Performance

## Use This When
- Designing or reviewing Convex queries.
- Explaining why `.filter()` or `.collect()` can be a production bug, not a style preference.
- Planning search, pagination, or time-window queries.

## Default Query Rule
- Query through indexes first.
- Use `.withIndex(...)` with left-to-right equality constraints and at most one terminal range.
- Assume `_creationTime` is implicitly appended to normal indexes.
- Bound result sets with `.take(...)` or `.paginate(...)` unless the table is truly tiny and permanently bounded.

## What To Avoid Immediately
- `.filter()` as the normal way to express database reads.
- `.collect()` over a table that can grow.
- Counting by `collect().length`.
- `Date.now()` or similar time-dependent logic inside queries.

## Index Design Rules
- Name indexes after the fields they actually serve.
- Add the fields in the order you plan to constrain them.
- Consider implicit `_creationTime` before adding redundant secondary indexes.
- Use separate search indexes for full-text search; do not assume normal indexes and search indexes behave the same.

## Performance Reality
- Convex re-sends the full query result on invalidation, not deltas.
- A wide live query becomes a bandwidth problem even if the individual documents are small.
- Favor latest-N live views plus paginated history for feeds, sessions, or transcripts.
- Treat query width as an explicit performance budget.

## Determinism And Reactivity
- Queries rerun when accessed data changes, not when time passes.
- For time-driven releases or expirations, schedule writes that flip flags or pass a rounded time value from the client.
- Query logic must stay pure and reactive-safe.

## Search Notes
- Search is useful, but it has its own limits: relevance-first ordering, limited equality filtering, and no broad SQL-style search composition.
- If the product needs sophisticated search sorting or analytics, document that as a capability gap early.

## Pagination Default
- Keep the live tail small.
- Use cursor pagination for history.
- Explain to UI owners that additional pages are not the same thing as a single giant live subscription.

## Read Next
- [../advanced/01-pagination-live-tail-and-history.md](../advanced/01-pagination-live-tail-and-history.md)
- [03-queries-mutations-actions-scheduling.md](03-queries-mutations-actions-scheduling.md)
- [../operations/02-known-gaps-limitations-and-non-goals.md](../operations/02-known-gaps-limitations-and-non-goals.md)
