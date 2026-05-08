# Debug Logging

## Use This When
- Diagnosing WebSocket connection issues, subscription behavior, or auth token refreshes.
- Setting up a new Convex project and verifying the SDK is communicating correctly.
- Filtering Convex-specific logs in Console.app during development.

## Setup

```swift
@main
struct MyApp: App {
    init() {
        #if DEBUG
        initConvexLogging()   // call before any Convex usage
        #endif
    }
    var body: some Scene { WindowGroup { ContentView() } }
}
```

## What You See

```
[ConvexMobile] WebSocket connecting to wss://your-project.convex.cloud
[ConvexMobile] WebSocket connected
[ConvexMobile] Subscribing to query: messages:list
[ConvexMobile] Query result received: 3 documents
[ConvexMobile] Auth token refresh requested
[ConvexMobile] WebSocket reconnecting (attempt 1, backoff 100ms)
```

## Console.app Filtering

Open Console.app and filter by subsystem: `dev.convex.ConvexMobile`

This isolates Convex SDK logs from all other system output, making it easy to trace subscription lifecycle, auth events, and reconnect behavior.

## Technical Details
- Calls through to Rust's `init_convex_logging()` which sets up a `tracing` subscriber routing to `os_log`.
- Idempotent: uses `std::sync::Once` internally so subsequent calls are no-ops.
- Added in SDK version 0.6.0.
- OSLog subsystem: `dev.convex.ConvexMobile`.

## Avoid
- Shipping `initConvexLogging()` in production builds; logs can expose JWT tokens and user data. The `#if DEBUG` guard is mandatory.
- Calling `initConvexLogging()` after the first Convex operation; call it at app launch before any client usage.
- Relying on Xcode console alone; Console.app with subsystem filtering provides better structured output.

## Read Next
- [04-pipeline-termination-and-recovery.md](04-pipeline-termination-and-recovery.md)
- [05-websocket-state-and-connection-banner.md](05-websocket-state-and-connection-banner.md)
- [../advanced/03-testing-debugging-and-observability.md](../advanced/03-testing-debugging-and-observability.md)
