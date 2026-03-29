# Subscriptions, Errors, Logging, And Connection State

## Use This When
- Designing live data flows in Swift.
- Handling `ClientError`, reconnect UX, or logging.
- Explaining what transport recovery does and does not fix.

## Subscription Rules
- A subscription is the live read path; it is not a passive notification channel.
- `client.subscribe(to:with:yielding:)` returns `AnyPublisher<T, ClientError>` — Combine native.
- Subscription lifetime follows the owner of the Combine pipeline or async task.
- When the pipeline fails, the publisher is terminal and must be rebuilt intentionally.
- Rust-level reconnect only helps while the subscription owner is still alive and the pipeline has not already terminated.

### The Terminal Pipeline Trap

```swift
// This STOPS updating after the first error — permanently
client.subscribe(to: "messages:list", yielding: [Message].self)
    .replaceError(with: [])   // emits [] then COMPLETES — no more values ever
    .receive(on: DispatchQueue.main)
    .assign(to: &$messages)
```

When any `ClientError` occurs, `.replaceError(with:)` emits the fallback, then the publisher sends `.finished`. Your UI freezes with stale data and never updates again. This is Combine's design, not a Convex bug.

**For production, use Result-wrapping** — see `04-pipeline-termination-and-recovery.md` for the full pattern.

## Error Rules
- Distinguish product errors (`ConvexError`) from infrastructure or bridge failures (`InternalError`, `ServerError`).
- Prefer structured error payloads when the UI must branch on a known server-side condition.
- Use `replaceError` only in prototypes or when losing the stream is acceptable for the current screen.
- For production-critical subscriptions, preserve error information and decide explicitly how to recreate the subscription.

## Connection-State Rules

```swift
client.watchWebSocketState()
    .receive(on: DispatchQueue.main)
    .sink { state in
        switch state {
        case .connected: // hide banner
        case .connecting: // show "Reconnecting..."
        }
    }
    .store(in: &cancellables)
```

- `watchWebSocketState()` is useful for banners, degraded-state UX, and reconnect indicators.
- It behaves like an event stream, not a replaying current-value source.
- Subscribe early if you need to observe the initial connection transition.
- Pair connection-state UX with explicit stale-data messaging on iOS.
- See `05-websocket-state-and-connection-banner.md` for the complete banner pattern.

## Logging Rules

```swift
#if DEBUG
initConvexLogging()  // Call once at app launch — debug builds only
#endif
```

- Enable `initConvexLogging()` only in debug builds.
- Use logs to inspect websocket lifecycle, auth refresh, and subscription or mutation behavior.
- Filter in Console.app by subsystem or process name.
- Treat logs as developer tooling, not end-user telemetry.
- See `06-debug-logging.md` for full Console.app filtering guidance.

## Default Guidance
- Always `.receive(on: DispatchQueue.main)` before updating `@Published` properties — values arrive on the Rust bridge thread.
- Keep connection monitoring app-scoped when multiple screens depend on it.
- Use a Result-style wrapper when the UI must show both live data and terminal-failure state.
- For dynamic query parameters (date range, selected tab), use `.switchToLatest()` — see `../swiftui/01-consumption-patterns.md`.

## Avoid
- Assuming `.catch` or `replaceError` preserves realtime updates after a failure.
- Treating `watchWebSocketState()` as proof that the current data is fresh.
- Shipping debug logging in production builds.
- Forgetting `.receive(on: DispatchQueue.main)` — values arrive off-main, causing purple Xcode warnings and potential crashes.

## Read Next
- [04-pipeline-termination-and-recovery.md](04-pipeline-termination-and-recovery.md)
- [05-websocket-state-and-connection-banner.md](05-websocket-state-and-connection-banner.md)
- [../swiftui/01-consumption-patterns.md](../swiftui/01-consumption-patterns.md)
