# WebSocket State And Connection Banner

## Use This When
- Building a reconnecting indicator or offline banner in your app.
- Monitoring Convex connection health from SwiftUI views or view models.
- Combining network reachability with WebSocket state for a full connectivity picture.

## The API

```swift
client.watchWebSocketState() -> AnyPublisher<WebSocketState, Never>
```

Two states: `.connected` and `.connecting`. Never fails (`Never` error type).

Backed by `PassthroughSubject` — only emits future state changes, not the current state. Subscribe early to catch the initial `.connecting` to `.connected` transition.

## Connection Banner Component

```swift
struct ConnectionBanner: View {
    @State private var isConnected = true

    var body: some View {
        Group {
            if !isConnected {
                HStack(spacing: 6) {
                    ProgressView().scaleEffect(0.7)
                    Text("Reconnecting...")
                        .font(.caption)
                        .fontWeight(.medium)
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(.orange.opacity(0.9))
                .foregroundStyle(.white)
                .clipShape(Capsule())
                .transition(.move(edge: .top).combined(with: .opacity))
            }
        }
        .animation(.spring(response: 0.3), value: isConnected)
        .task {
            for await state in client.watchWebSocketState().values {
                isConnected = state == .connected
            }
        }
    }
}
```

## In A ViewModel

```swift
class AppViewModel: ObservableObject {
    @Published var isConnected = false
    private var cancellables = Set<AnyCancellable>()

    init() {
        client.watchWebSocketState()
            .map { $0 == .connected }
            .receive(on: DispatchQueue.main)
            .assign(to: &$isConnected)
    }
}
```

## Combined With NWPathMonitor

```swift
struct StatusView: View {
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
            Circle().fill(wsState == .connected ? .green : .orange)
                .frame(width: 8, height: 8)
            Text(status).font(.caption)
        }
        .task {
            for await state in client.watchWebSocketState().values {
                wsState = state
            }
        }
    }
}
```

## Avoid
- Treating `watchWebSocketState()` as proof that the current data is fresh; it only reports transport state.
- Subscribing late and missing the initial `.connecting` to `.connected` transition.
- Showing a connection banner as the sole error indicator; combine it with subscription-level error state.
- Using a dedicated `convex` variable name for the client; the correct variable name is `client`.

## Read Next
- [04-pipeline-termination-and-recovery.md](04-pipeline-termination-and-recovery.md)
- [06-debug-logging.md](06-debug-logging.md)
- [../platforms/01-ios-backgrounding-reconnection-and-staleness.md](../platforms/01-ios-backgrounding-reconnection-and-staleness.md)
