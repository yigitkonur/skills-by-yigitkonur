# Xcode SPM Setup: ConvexMobile

## Use This When
- Adding the Convex Swift SDK to an Xcode project for the first time.
- Verifying platform requirements before committing to ConvexMobile.
- Setting up an authenticated or unauthenticated Convex client in Swift.

## Add the Package

1. In Xcode: **File -> Add Package Dependencies**.
2. Repository URL: `https://github.com/get-convex/convex-swift`
3. Version rule: **Up to Next Major** from `0.8.1`.
4. Select `ConvexMobile` target and add it to your app target.

## Create the Client

One client per app. Never create multiple instances -- each owns a single WebSocket connection.

### Without Auth

```swift
import ConvexMobile

let client = ConvexClient(deploymentUrl: "https://happy-animal-123.convex.cloud")
```

### With Clerk Auth

```swift
import ConvexMobile
import ClerkKit
import ClerkConvex

Clerk.configure(publishableKey: "pk_test_your_key")

@MainActor
let client = ConvexClientWithAuth(
  deploymentUrl: "https://happy-animal-123.convex.cloud",
  authProvider: ClerkConvexAuthProvider()
)
// Session sync is automatic via bind(client:) -- no manual loginFromCache() calls needed
```

## Platform Requirements

| Platform | Minimum Version | Architecture | Notes |
|---|---|---|---|
| iOS + macOS (with Clerk auth) | **iOS 17+ / macOS 14+** | arm64 | Required when using Clerk auth — the default path |
| iOS (SDK only) | 13.0 | arm64 | Without Clerk |
| iOS Simulator | 13.0 | arm64 | Without Clerk |
| macOS (SDK only) | 10.15 (Catalina) | arm64 only | Without Clerk |

> **Footnote:** ConvexMobile SDK alone supports iOS 13+ / macOS 10.15+, but Clerk integration raises the floor.

**Intel Mac builds will fail.** The XCFramework contains arm64 slices only (issue #10 open). Mac Catalyst is not supported.

## Debug Logging

```swift
@main
struct MyApp: App {
  init() {
    #if DEBUG
    initConvexLogging()   // routes Rust logs to Xcode console
    #endif
  }

  var body: some Scene {
    WindowGroup { ContentView() }
  }
}
```

Filter in Console.app: `subsystem:dev.convex.ConvexMobile`. **Never enable in production** -- logs expose JWTs and user data.

## Verify the Setup

```swift
struct ContentView: View {
  @State private var connected = false

  var body: some View {
    Text(connected ? "Connected!" : "Connecting...")
      .task {
        for await state in client.watchWebSocketState().values {
          connected = state == .connected
        }
      }
  }
}
```

If "Connected!" appears, the SDK is working.

## Binary Size

The Rust XCFramework adds approximately 5-15 MB after stripping and App Store thinning (Tokio runtime, TLS, WebSocket, Convex protocol).

## Avoid
- Creating multiple `ConvexClient` instances -- one per process is the rule.
- Enabling `initConvexLogging()` in release builds -- it leaks JWTs and user data.
- Targeting Intel Macs or Mac Catalyst -- no XCFramework slices exist.
- Using `import Clerk` or `import ClerkSDK` -- the correct imports are `import ClerkKit`, `import ClerkConvex`, `import ClerkKitUI`.

## Read Next
- [03-clerk-account-and-jwt-template-setup.md](03-clerk-account-and-jwt-template-setup.md)
- [../client-sdk/01-client-surface-runtime-and-auth-bridge.md](../client-sdk/01-client-surface-runtime-and-auth-bridge.md)
- [../authentication/01-clerk-first-setup.md](../authentication/01-clerk-first-setup.md)
