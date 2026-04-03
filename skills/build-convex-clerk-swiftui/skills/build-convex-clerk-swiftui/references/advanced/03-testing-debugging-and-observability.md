# Testing, Debugging, And Observability

## Use This When
- Writing unit tests around Swift-side Convex integrations.
- Building SwiftUI previews without live backend dependencies.
- Investigating realtime failures or auth-refresh bugs.

## Default Testing Seams
- Use `MobileConvexClientProtocol` as the core test seam for Swift-side client behavior.
- Use the internal `ConvexClient(ffiClient:)` path with `@testable import` when unit tests need a mocked FFI client.
- Keep preview-only protocols or facades separate from live clients so previews stay deterministic.

## Async Test Rules
- Use XCTest expectations and async fulfillment patterns for publisher-driven behavior.
- Be explicit about `dropFirst()`, main-actor expectations, and subscription lifetime in tests.
- Treat timing-sensitive tests as lifecycle tests, not loose sleeps.

## Debugging Rules
- Enable `initConvexLogging()` in debug builds only.
- Inspect websocket lifecycle, auth refresh, subscription churn, and action or mutation outcomes through OSLog.
- Use `watchWebSocketState()` as a live diagnostic input, not as a replaying truth source.

## Preview Rule
- SwiftUI previews should not depend on a live Convex deployment.
- Keep preview data and preview clients explicit.
- Do not let preview scaffolding mutate production architecture boundaries.

## Avoid
- Sleep-driven flaky tests for realtime behavior.
- Letting preview support depend on the actual networked client.
- Shipping debug-only logging or test seams into production behavior by accident.

## Read Next
- [../client-sdk/03-subscriptions-errors-logging-and-connection-state.md](../client-sdk/03-subscriptions-errors-logging-and-connection-state.md)
- [../platforms/03-performance-battery-and-threading.md](../platforms/03-performance-battery-and-threading.md)
