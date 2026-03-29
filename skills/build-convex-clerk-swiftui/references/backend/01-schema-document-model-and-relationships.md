# Schema, Document Model, And Relationships

## Use This When
- Designing tables for a new Convex backend.
- Migrating a Swift team away from Core Data, Firestore collections, or SQL-table instincts.
- Modeling a feature before writing queries or mutations.

## Default Data Model
- Convex stores tables of JSON-like documents with automatic `_id` and `_creationTime` fields.
- Prefer flat tables linked by IDs over deep nesting or document trees.
- Treat a document as a bounded unit of state, not a bag that grows forever.
- Add schema validation once the model is understood, then let deploy-time validation catch drift.

## Concrete Example (Official WorkoutTracker)

```typescript
// convex/schema.ts
import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  workouts: defineTable({
    activity: v.string(),
    date: v.string(),                  // ISO 8601 "YYYY-MM-DD"
    duration: v.optional(v.int64()),   // optional → @OptionalConvexInt on Swift side
    userId: v.string(),                // stores ctx.identity.tokenIdentifier
  }).index("userId_date", ["userId", "date"]),
});
```

Key patterns:
- **`userId: v.string()`**: stores `ctx.identity.tokenIdentifier` from the server auth context. Never accept this from the client.
- **Compound index `["userId", "date"]`**: enables efficient range queries filtered by user (`q.eq("userId", ...).gte("date", ...).lte("date", ...)`).
- **`v.optional(v.int64())`**: maps to `@OptionalConvexInt var duration: Int?` on the Swift side.
- **`v.string()` for dates**: Convex has no native date type; ISO 8601 strings enable range indexing.
- **Flat table**: workouts are a single table, not nested under users. Ownership is via the `userId` field + index.

## Relationship Rules
- Model ownership and relations with `v.id("tableName")` fields.
- Do joins in backend query code, not in Swift, when the UI needs combined shapes.
- Use explicit tables for membership, many-to-many relationships, and high-churn companion data.
- Do not try to recreate SQL join semantics or Firestore subcollection habits directly.

## High-Churn Separation Rule
- Separate frequently changing data from stable profile or metadata fields.
- Presence, typing indicators, ephemeral counters, or streaming segments should live apart from slow-changing user/session docs.
- This reduces reactive invalidation cost and OCC conflict pressure.

## Unbounded Array Rule
- Never store growing lists as array fields inside one document.
- Arrays hit element and document-size limits and cause whole-document rewrites.
- Use separate child tables for segments, feed items, comments, files, or timeline events.

## Counter And Summary Rule
- Do not count by reading and measuring a whole collection.
- Maintain explicit counters or summary docs inside mutations.
- Treat denormalized summary fields as first-class schema, not a hack.

## Modeling Checklist
- Can each document stay well-bounded over time?
- Is high-churn data isolated from stable data?
- Can every important query be expressed through indexes instead of `.filter()`?
- Is ownership represented by server-derived identities instead of client-provided IDs?

## Avoid
- Document designs that require appending forever to one field.
- Deeply nested object graphs that Swift has to decode and partially update.
- Relying on implicit client-side joining or client ownership checks.
- Treating Convex like SQL with richer query power than it actually has.

## Read Next
- [02-indexes-query-shaping-and-performance.md](02-indexes-query-shaping-and-performance.md)
- [03-queries-mutations-actions-scheduling.md](03-queries-mutations-actions-scheduling.md)
- [04-auth-rules-and-server-ownership.md](04-auth-rules-and-server-ownership.md)
