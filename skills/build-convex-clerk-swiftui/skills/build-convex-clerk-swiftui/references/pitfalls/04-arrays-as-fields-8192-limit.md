# Arrays As Fields — 8192 Element Limit

## Use This When
- Designing a Convex schema where a document field holds a list of items.
- Evaluating whether to embed child data in a parent document or use a separate table.
- Investigating growing document sizes or hitting the 1MB document limit.

## The Limits

| Limit | Value |
|---|---|
| Maximum array elements per field | **8,192** |
| Maximum document size | **1 MB** |

## The O(N^2) Bandwidth Problem

Every Convex document update re-sends the **entire document** to all subscribers. Appending to an array means the Nth append transmits N items. After 1,000 appends, total bandwidth is ~500,000 item-units. This is quadratic growth that becomes visible well before hitting the hard limits.

## Common Anti-Patterns

- **Chat messages as array on a channel document** — every new message re-sends the entire history.
- **Activity log as array on a user document** — grows forever, hits 8,192 limit.
- **Transcription segments as array** — unbounded, high-frequency appends.

## The Fix: Separate Table with Foreign Key

```typescript
// convex/schema.ts
export default defineSchema({
  channels: defineTable({ name: v.string() }),
  messages: defineTable({
    channelId: v.id("channels"),
    text: v.string(),
    createdAt: v.number(),
  }).index("by_channel", ["channelId", "createdAt"]),
});
```

Insert new documents instead of appending to arrays. Subscribers to a bounded query on the child table receive only the relevant page of results.

## When Arrays Are Appropriate

Small, bounded, rarely-changing arrays are fine:

| Use Case | Typical Size | Appropriate? |
|---|---|---|
| User roles | 1-5 | Yes |
| Tag labels | 1-10 | Yes |
| Participant IDs (bounded) | 1-20 | Yes |
| Chat messages | Unbounded | **No** |
| Activity log | Unbounded | **No** |
| Transcription segments | Unbounded | **No** |

Rule of thumb: if the array can grow beyond ~100 elements, use a separate table.

## Avoid
- Storing unbounded or frequently-appended lists as document array fields.
- Assuming array growth will stay small based on current usage.
- Using arrays for data that should be queried, filtered, or paginated independently.

## Read Next
- [../backend/01-schema-document-model-and-relationships.md](../backend/01-schema-document-model-and-relationships.md)
- [03-unbounded-collect-bandwidth-bomb.md](03-unbounded-collect-bandwidth-bomb.md)
- [../advanced/04-streaming-workloads-and-transcription.md](../advanced/04-streaming-workloads-and-transcription.md)
