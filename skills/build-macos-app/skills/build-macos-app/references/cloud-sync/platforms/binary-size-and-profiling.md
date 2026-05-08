# Binary Size And Instruments Profiling

## Use This When
- Evaluating the size impact of adding ConvexMobile to an app.
- Profiling network behavior, energy usage, or connection lifecycle with Instruments.
- Debugging WebSocket issues using OSLog and Console.app.

## Binary Size Impact

The `libconvexmobile-rs.xcframework` static archive is approximately 48.8 MB pre-stripping. After link-time optimization and App Store thinning, the on-device impact is **approximately 5-15 MB**.

This includes the Tokio runtime, TLS stack, WebSocket protocol, and Convex sync engine compiled from Rust. It cannot be reduced, replaced, or tree-shaken — it is a single static archive.

| Measurement Point | Size |
|-------------------|------|
| Raw `.xcframework` | ~48.8 MB |
| After LTO + strip | ~15-20 MB |
| On-device (App Store thinning) | ~5-15 MB |

## Instruments: Network Template

1. Run the app with Instruments using the Network template.
2. Filter by app process and look for `wss://` connections to the deployment URL.
3. Observe reconnection events as TCP connections drop and re-establish.
4. Measure time-to-reconnect after simulating network transitions (airplane mode toggle, Wi-Fi switch).

This confirms subscription lifecycle, reconnection behavior, and bandwidth usage per subscription.

## Instruments: Energy Template

1. Use the Energy Log template.
2. Measure background versus foreground network energy.
3. The Network Transfers view shows WebSocket frame frequency and size.
4. Look for subscription churn — repeated subscribe/unsubscribe cycles from navigation or tab switches waste energy.

## OSLog Debugging

```swift
#if DEBUG
initConvexLogging()  // Routes Rust client logs to OSLog
#endif
```

Filter in Console.app by subsystem `dev.convex.ConvexMobile`. This surfaces:
- WebSocket lifecycle events (connect, disconnect, reconnect)
- Subscription registration and teardown
- Auth token refresh timing
- Mutation and action results

Keep `initConvexLogging()` behind `#if DEBUG` — it should never ship in production builds.

## Threading Safety Note

Convex Combine publishers deliver values on the Rust Tokio runtime thread. Always use `.receive(on: DispatchQueue.main)` before assigning to `@Published` properties. In `.task {}` modifiers, the closure inherits `@MainActor` from the view, so assigning to `@State` directly is safe.

## Avoid
- Making specific binary-size claims without freshly verified measurements — sizes shift across SDK releases.
- Shipping `initConvexLogging()` in production builds.
- Profiling in the Simulator — Instruments data is only meaningful on a real device for energy and network measurements.
- Assigning subscription values to `@Published` properties without `.receive(on: DispatchQueue.main)` — this causes main-thread assertion failures.

## Read Next
- [03-performance-battery-and-threading.md](03-performance-battery-and-threading.md)
- [05-nwpathmonitor-network-awareness.md](05-nwpathmonitor-network-awareness.md)
- [../advanced/03-testing-debugging-and-observability.md](../advanced/03-testing-debugging-and-observability.md)
