# No Offline, No Optimistic Updates — Hard Limitations

## Use This When
- Deciding whether Convex fits an app that may need offline access.
- Explaining perceived latency on mutations to stakeholders.
- Evaluating the Swift SDK's feature parity with the React/JS SDK.

## What The Swift SDK Cannot Do

These are fundamental limitations of the ConvexMobile Swift SDK as of early 2026. They are tracked as GitHub issues with no announced timeline.

### No Offline Sync

The Swift SDK has **zero** offline support. No local cache persists across app launches, no offline reads, no offline write queue, no conflict resolution. When the WebSocket disconnects, subscriptions stop emitting values. When the app launches without network, no data is available.

If the app requires offline functionality, Convex alone is not sufficient. A supplementary local storage layer (CoreData, SwiftData, or similar) that you manage yourself is required.

### No Optimistic Updates

The React SDK supports optimistic updates — immediately updating the UI before server confirmation. The Swift SDK does not. Perceived latency on every mutation is: round-trip (~50-200ms) + subscription update push (~50-100ms) = **100-300ms** before the UI reflects the change.

A manual optimistic pattern is possible but error-prone:

```swift
func toggleComplete(task: Task) async {
    // Optimistically update local state
    await MainActor.run {
        if let index = tasks.firstIndex(where: { $0.id == task.id }) {
            tasks[index] = Task(id: task.id, title: task.title, isComplete: !task.isComplete)
        }
    }
    do {
        try await client.mutation("tasks:toggleComplete", with: ["taskId": task.id])
        // Subscription overwrites with server truth
    } catch {
        await MainActor.run {
            if let index = tasks.firstIndex(where: { $0.id == task.id }) {
                tasks[index] = task  // Revert to original
            }
        }
    }
}
```

This does not compose well with concurrent mutations.

### No SQL

Convex is a document database. No JOIN, GROUP BY, HAVING, UNION, or subqueries. Related data requires multiple queries in server functions.

### No Native File Upload API

File uploads require a manual three-step `URLSession` flow.

### Intel Mac Broken

The XCFramework ships ARM64 only. No Intel, Mac Catalyst, watchOS, tvOS, or visionOS support.

## Complete Limitations Table

| Feature | Status | Workaround |
|---|---|---|
| Offline sync | Not available | Add CoreData/SwiftData layer |
| Optimistic updates | Not available | Manual state management |
| SQL queries (JOIN, GROUP BY) | Not applicable | Multiple queries in server functions |
| Native file upload | Not available | URLSession three-step flow |
| Intel Mac (x86_64) | Broken | ARM64-only distribution |
| `usePaginatedQuery` equivalent | Not available | Manual cursor management |
| Streaming HTTP (SSE) | Not available | Use subscriptions instead |

## When To Evaluate Alternatives

Consider alternatives if the product **requires**:
- **Offline-first**: CRDTs (Automerge, Yjs), PowerSync, ElectricSQL, or Realm.
- **Complex queries**: PostgreSQL + Supabase, or Firebase with Cloud Functions.
- **Intel Mac support**: Any SDK with universal binary support.
- **Native optimistic updates**: React/web client (which has them), or a local-first database.

## Avoid
- Promising offline support or optimistic updates to stakeholders — neither exists in the Swift SDK.
- Hiding these limitations during architecture review.
- Building a production feature that depends on offline access without an explicit local persistence layer.
- Assuming feature parity between the React and Swift SDKs.

## Read Next
- [../operations/02-known-gaps-limitations-and-non-goals.md](../operations/02-known-gaps-limitations-and-non-goals.md)
- [../onboarding/04-adoption-checklist-and-hard-stops.md](../onboarding/04-adoption-checklist-and-hard-stops.md)
- [../platforms/02-offline-behavior-network-transitions-and-recovery.md](../platforms/02-offline-behavior-network-transitions-and-recovery.md)
