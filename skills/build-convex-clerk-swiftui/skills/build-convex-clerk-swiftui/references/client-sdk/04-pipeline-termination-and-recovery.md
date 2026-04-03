# Pipeline Termination And Recovery

## Use This When
- A subscription stops updating and the UI shows stale or empty data.
- Designing production-grade Combine pipelines for Convex subscriptions.
- Understanding why `.replaceError(with:)` kills live updates permanently.
- Building retry or resubscribe logic after a subscription error.

## The Problem

This is the single most important implementation detail for production apps: a Combine publisher from `subscribe()` permanently stops after the first error.

```swift
// This STOPS updating after the first error — permanently
client.subscribe(to: "messages:list", yielding: [Message].self)
    .replaceError(with: [])
    .receive(on: DispatchQueue.main)
    .assign(to: &$messages)
```

When any `ClientError` occurs:
1. `.replaceError(with: [])` emits `[]` as a fallback value.
2. The publisher completes (sends `.finished`).
3. No more values will ever arrive.
4. Your UI shows empty data and never updates again.

This is Combine's design: once a publisher sends `.failure` or `.finished`, it is done forever.

## The Fix: Result-Wrapping

```swift
client.subscribe(to: "messages:list", yielding: [Message].self)
    .map { Result<[Message], ClientError>.success($0) }
    .catch { error in Just(Result.failure(error)) }
    .receive(on: DispatchQueue.main)
    .assign(to: &$messageResult)
```

This catches the error, wraps it as a `Result.failure`, and surfaces the error in your UI state. The pipeline still completes after the error value, but you see what happened:

```swift
switch vm.messageResult {
case .success(let messages):
    List(messages) { Text($0.body) }
case .failure(let error):
    Text("Error: \(error.localizedDescription)")
    Button("Retry") { vm.resubscribe() }
}
```

**Important:** Even with Result-wrapping, the Combine pipeline completes after the error value. The transport may reconnect automatically, but the Combine chain is done. To resume live updates, recreate the subscription from the owning model.

## Production ViewModel Pattern

```swift
class ContentViewModel: ObservableObject {
    @Published var messages: [Message] = []
    @Published var isConnected = false
    @Published var lastUpdatedAt: Date?
    @Published var subscriptionError: ClientError?
    private var cancellables = Set<AnyCancellable>()

    init() {
        setupSubscriptions()
    }

    private func setupSubscriptions() {
        // Data subscription with Result-wrapping
        client.subscribe(to: "messages:list", yielding: [Message].self)
            .map { Result<[Message], ClientError>.success($0) }
            .catch { Just(Result.failure($0)) }
            .receive(on: DispatchQueue.main)
            .sink { [weak self] result in
                switch result {
                case .success(let msgs):
                    self?.messages = msgs
                    self?.lastUpdatedAt = Date()
                    self?.subscriptionError = nil
                case .failure(let error):
                    self?.subscriptionError = error
                }
            }
            .store(in: &cancellables)

        // Connection status
        client.watchWebSocketState()
            .map { $0 == .connected }
            .receive(on: DispatchQueue.main)
            .assign(to: &$isConnected)
    }

    func resubscribe() {
        cancellables.removeAll()
        subscriptionError = nil
        setupSubscriptions()
    }
}
```

## Tri-State Pattern

```swift
enum ViewState<T> {
    case loading
    case loaded(T)
    case failed(ClientError)
}

class TodoViewModel: ObservableObject {
    @Published var state: ViewState<[Todo]> = .loading
    private var cancellables = Set<AnyCancellable>()

    init() {
        client.subscribe(to: "tasks:get", yielding: [Todo].self)
            .map { ViewState.loaded($0) }
            .catch { error in Just(ViewState<[Todo]>.failed(error)) }
            .receive(on: DispatchQueue.main)
            .sink { [weak self] in self?.state = $0 }
            .store(in: &cancellables)
    }
}
```

## View Using The ViewModel

```swift
struct ContentView: View {
    @StateObject private var vm = ContentViewModel()

    var body: some View {
        VStack {
            if !vm.isConnected {
                ConnectionBanner()
            }

            if let error = vm.subscriptionError {
                ErrorBanner(error: error)
            }

            List(vm.messages) { msg in
                Text(msg.body)
            }

            if let lastUpdated = vm.lastUpdatedAt {
                Text("Updated \(lastUpdated, style: .relative) ago")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }
        }
    }
}
```

## When `.replaceError(with:)` Is Acceptable
- Prototyping and demos.
- Simple screens where the view rebuilds on navigation (`.task` pattern).
- Non-critical subscriptions where stale data is acceptable.

Never use it in production for critical data paths.

## Avoid
- Assuming `.catch` or `.replaceError` preserves realtime updates after a failure.
- Using `.assign(to: &$property)` directly on a failable publisher without Result-wrapping.
- Forgetting that the Combine pipeline is terminal even when the WebSocket transport reconnects.
- Skipping the `resubscribe()` method; without it there is no way to restore live updates after an error.

## Read Next
- [05-websocket-state-and-connection-banner.md](05-websocket-state-and-connection-banner.md)
- [06-debug-logging.md](06-debug-logging.md)
- [03-subscriptions-errors-logging-and-connection-state.md](03-subscriptions-errors-logging-and-connection-state.md)
- [../backend/07-structured-errors-convexerror.md](../backend/07-structured-errors-convexerror.md)
