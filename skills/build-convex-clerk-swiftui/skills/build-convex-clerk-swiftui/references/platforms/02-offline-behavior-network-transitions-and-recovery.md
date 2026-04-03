# Offline Behavior, Network Transitions, And Recovery

## Use This When
- Designing degraded-state UX for iOS or shared Apple-platform apps.
- Explaining what Convex does without offline persistence.
- Pairing network reachability with websocket state.

## Hard Truth
- The Swift SDK does not provide offline persistence.
- Last values may remain in memory, but they are not a durable offline database.
- Reconnect is automatic when the process is active again, but missed time still exists.
- There is no optimistic update mechanism in the current Swift SDK.

## Recommended UX Pattern: Four-State Model

Combine `NWPathMonitor` with `watchWebSocketState()` to distinguish four states:

| State | NWPathMonitor | WebSocket | UX |
|---|---|---|---|
| Fully live | `.satisfied` | `.connected` | Normal — no indicator needed |
| Reconnecting | `.satisfied` | `.connecting` | "Reconnecting..." banner |
| No network | `.unsatisfied` | `.connecting` | "No network" overlay |
| Stale after resume | `.satisfied` | `.connected` | "Data may be outdated" (timestamp-based) |

## Staleness Detection

```swift
class ConnectionMonitor: ObservableObject {
    @Published var isStale = false
    private var lastFreshDataAt: Date = .now
    private var backgroundedAt: Date?

    func handleBackground() {
        backgroundedAt = .now
    }

    func handleForeground() {
        if let bg = backgroundedAt {
            let gap = Date.now.timeIntervalSince(bg)
            isStale = gap > 10  // stale if backgrounded > 10s
        }
    }

    func markFresh() {
        lastFreshDataAt = .now
        isStale = false
    }
}
```

## Recovery Rule
- Reconnect behavior belongs to the transport layer — Convex handles this.
- Subscription recovery still depends on owner lifetime and non-terminal pipeline state.
- If a Combine pipeline terminated with an error before the network drop, reconnect will NOT revive it.
- App logic should assume some user-visible stale window after disruption.

## Avoid
- Describing Convex as offline-first.
- Hiding network loss by freezing the UI without explanation.
- Treating reachability alone as proof that data is current.
- Promising optimistic updates — the Swift SDK does not support them.

## Read Next
- [01-ios-backgrounding-reconnection-and-staleness.md](01-ios-backgrounding-reconnection-and-staleness.md)
- [05-nwpathmonitor-network-awareness.md](05-nwpathmonitor-network-awareness.md)
- [../client-sdk/03-subscriptions-errors-logging-and-connection-state.md](../client-sdk/03-subscriptions-errors-logging-and-connection-state.md)
