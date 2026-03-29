# NWPathMonitor Network Awareness

## Use This When
- Building network-aware UI that shows connection status alongside WebSocket state.
- Distinguishing between device-level network loss and Convex-specific connection issues.
- Designing degraded-state UX for offline or poor-connectivity conditions.

## Why Both NWPathMonitor And watchWebSocketState

`watchWebSocketState()` tells you about the Convex WebSocket connection specifically. `NWPathMonitor` tells you about the device's network in general. A device can have network connectivity while the WebSocket is still reconnecting (after sleep/wake, server maintenance, or token refresh). Showing both gives users accurate status.

## Network Monitor

```swift
import Network

@MainActor
final class NetworkPathMonitor: ObservableObject {
    @Published private(set) var isConnected = true
    @Published private(set) var connectionType: NWInterface.InterfaceType = .wifi
    private let monitor = NWPathMonitor()
    private let queue = DispatchQueue(label: "com.app.networkmonitor", qos: .utility)

    init() {
        monitor.pathUpdateHandler = { [weak self] path in
            DispatchQueue.main.async {
                self?.isConnected = path.status == .satisfied
                self?.connectionType = [.wifi, .cellular]
                    .first(where: { path.usesInterfaceType($0) }) ?? .other
            }
        }
        monitor.start(queue: queue)
    }

    deinit { monitor.cancel() }
    var isExpensive: Bool { monitor.currentPath.isExpensive }
}
```

## Combined Status View

```swift
struct ConnectionStatusView: View {
    @StateObject private var network = NetworkPathMonitor()
    @State private var wsState: WebSocketState?

    var status: String {
        if !network.isConnected { return "No network" }
        switch wsState {
        case .connected: return "Live"
        case .connecting: return "Reconnecting..."
        case nil: return "Checking..."
        }
    }

    var body: some View {
        HStack {
            Circle()
                .fill(wsState == .connected ? .green : .orange)
                .frame(width: 8, height: 8)
            Text(status)
                .font(.caption)
        }
        .task {
            for await state in client.watchWebSocketState().values {
                wsState = state
            }
        }
    }
}
```

## Degraded State Handling

Use network awareness to adjust product behavior proactively:

| Condition | Recommended Action |
|-----------|-------------------|
| `!network.isConnected` | Show offline banner, disable mutation buttons |
| `network.isExpensive` (cellular/hotspot) | Consider reducing subscription scope or pausing non-essential queries |
| `wsState == .connecting` | Show reconnecting indicator, keep UI interactive with stale data |
| `wsState == .connected && network.isConnected` | Full realtime — no degradation needed |

## Placement Rules
- Own `NetworkPathMonitor` as a `@StateObject` at the screen level or inject via `@EnvironmentObject` for app-wide access.
- Own WebSocket state in `.task` — it ties naturally to view lifetime and cancels cleanly.
- Combine both signals in the view layer, not in the monitor itself.

## Avoid
- Using `NWPathMonitor` alone to determine Convex connectivity — a satisfied network path does not guarantee the WebSocket is connected.
- Using `watchWebSocketState()` alone to detect device-level network loss — the WebSocket may report `.connecting` for reasons unrelated to network availability.
- Starting `NWPathMonitor` on the main queue — use a dedicated utility queue and dispatch updates to main.
- Blocking mutations when the WebSocket is reconnecting — mutations are queued and sent when the connection resumes.

## Read Next
- [02-offline-behavior-network-transitions-and-recovery.md](02-offline-behavior-network-transitions-and-recovery.md)
- [01-ios-backgrounding-reconnection-and-staleness.md](01-ios-backgrounding-reconnection-and-staleness.md)
- [03-performance-battery-and-threading.md](03-performance-battery-and-threading.md)
