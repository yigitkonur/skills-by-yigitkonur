# os_log and Console.app Filtering

## Use This When
- Debugging WebSocket connectivity, subscription updates, or auth token flow in the Convex SDK.
- Filtering Convex-specific logs in Console.app or Xcode.
- Adding structured logging to your own Convex integration code.

## Enable Convex Logging

Call `initConvexLogging()` once at app launch to route Rust-level logs through Apple's unified logging:

```swift
import ConvexMobile

@main
struct MyApp: App {
  init() {
    #if DEBUG
    initConvexLogging()
    #endif
  }

  var body: some Scene {
    WindowGroup { ContentView() }
  }
}
```

**Always wrap in `#if DEBUG`.** The logs expose JWTs, user IDs, function names, and argument values. Shipping in production is a security risk.

## What Gets Logged

| Event Category | Example |
|---|---|
| WebSocket lifecycle | `Opening WebSocket to wss://...convex.cloud` |
| Connection state | `WebSocket connected`, `WebSocket disconnected` |
| Subscription events | `Subscribing to messages:list`, `Received update for query #42` |
| Mutation/action calls | `Calling mutation messages:send with args {...}` |
| Auth token refresh | `Setting auth token: eyJhbG...` (full JWT) |
| Reconnection | `Reconnecting after 2s backoff` |
| Errors | `Server error: Function not found: messages:typo` |

## Filtering in Console.app

1. Open `/Applications/Utilities/Console.app`.
2. Select your device or simulator.
3. Click "Start Streaming".

### By Subsystem

```
subsystem:dev.convex.ConvexMobile
```

### Narrow by Category

```
subsystem:dev.convex.ConvexMobile category:websocket
subsystem:dev.convex.ConvexMobile category:subscription
subsystem:dev.convex.ConvexMobile category:auth
```

> **Note:** Category granularity depends on the Rust tracing subscriber inside the SDK. Subsystem-based filtering (`subsystem:dev.convex.ConvexMobile`) is reliable. Category-level filtering should be verified against your specific SDK version -- the categories shown here are illustrative, not guaranteed.

### Show Debug-Level Logs

Action menu -> Include Info Messages -> Include Debug Messages.

## Add Your Own Structured Logs

```swift
import os.log

extension Logger {
  static let convexApp = Logger(
    subsystem: Bundle.main.bundleIdentifier ?? "com.myapp",
    category: "ConvexIntegration"
  )
}

// Usage
func startSubscription() {
  Logger.convexApp.debug("Starting subscription to messages:list")

  client.subscribe(
    to: "messages:list",
    with: ["channelId": channelId],
    yielding: [Message].self
  )
  .receive(on: DispatchQueue.main)
  .sink(
    receiveCompletion: { completion in
      if case .failure(let error) = completion {
        Logger.convexApp.error("Subscription failed: \(error)")
      }
    },
    receiveValue: { [weak self] messages in
      Logger.convexApp.info("Received \(messages.count) messages")
      self?.messages = messages
    }
  )
  .store(in: &cancellables)
}
```

## Common Debugging Scenarios

**Auth not working**: Filter for `auth` category. Look for `Setting auth token:` (token sent), `Auth error:` (token rejected), or no auth logs at all (session sync never started -- verify `ClerkConvexAuthProvider` is bound via `bind(client:)`).

**Subscription not updating**: Filter for `subscription` category. Look for `Subscribing to X` (subscribe called), `Received update for query #N` (server pushed data), or no update logs (function name mismatch).

**WebSocket disconnecting**: Filter for `websocket` category. Look for disconnect reasons and reconnection backoff patterns.

## Quick Reference

| Task | Filter |
|---|---|
| All SDK logs | `subsystem:dev.convex.ConvexMobile` |
| WebSocket only | `+ category:websocket` |
| Auth only | `+ category:auth` |
| Your app logs | `subsystem:com.yourapp category:ConvexIntegration` |

## Avoid
- Enabling `initConvexLogging()` in release builds -- it leaks JWTs and user data to anyone with Console.app access.
- Logging user tokens or secrets in your own `Logger` calls -- use `%{private}@` for sensitive string interpolation.
- Using `.replaceError(with:)` in subscription pipelines -- it silently terminates the stream, making it look like subscriptions stopped updating when the real issue is pipeline termination.
- Calling `loginFromCache()` manually to "fix" missing auth logs -- `bind(client:)` handles session restore automatically.

## Read Next
- [01-mock-ffi-client-unit-testing.md](01-mock-ffi-client-unit-testing.md)
- [../client-sdk/03-subscriptions-errors-logging-and-connection-state.md](../client-sdk/03-subscriptions-errors-logging-and-connection-state.md)
- [../platforms/01-ios-backgrounding-reconnection-and-staleness.md](../platforms/01-ios-backgrounding-reconnection-and-staleness.md)
