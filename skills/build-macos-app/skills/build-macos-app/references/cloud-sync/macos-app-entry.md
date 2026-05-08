# macOS Multi-Window, Menu Bar, And Support Limits

## Use This When
- Building a macOS app or shared iOS + macOS app with Convex.
- Planning multi-window state, menu bar behavior, or support-matrix communication.
- Preventing iOS lifecycle assumptions from leaking into macOS architecture.

## Trust Boundary
- The official `clerk-convex-swift` package supports macOS 14+.
- The official `WorkoutTracker` sample is still a narrow app template, not a full macOS multi-window or menu-bar reference architecture.
- Use this file for macOS-specific architectural guidance; do not pretend the sample app directly proves every macOS rule here.

## Official Package Support
- `clerk-convex-swift` targets **macOS 14+** in its `Package.swift`.
- `ClerkKitUI` components (`AuthView()`, `UserButton()`, `.prefetchClerkImages()`) work on macOS.
- However, the official example app (`WorkoutTracker`) only demonstrates **iOS patterns**. There is no official macOS example.
- macOS multi-window, menu bar, and per-window state patterns are your responsibility to architect.

## Core macOS Shape
- Share one client process-wide (`@MainActor let client`).
- Keep per-window feature state per window.
- Instantiate per-window `@StateObject` models inside the window view hierarchy, not in the `App` struct.
- Treat hide/show and close as different events with different consequences for state lifetime.

## macOS App Entry (Adapted From Official iOS Pattern)

```swift
import ClerkKit
import ClerkConvex
import ClerkKitUI
import ConvexMobile
import SwiftUI

@MainActor
let client = ConvexClientWithAuth(
  deploymentUrl: Env.convexDeploymentUrl,
  authProvider: ClerkConvexAuthProvider()
)

@main
struct MyMacApp: App {
  init() {
    Clerk.configure(publishableKey: Env.clerkPublishableKey)
  }

  var body: some Scene {
    // Main window — shared client, per-window feature models
    WindowGroup {
      LandingPage()
        .prefetchClerkImages()
        .environment(Clerk.shared)
    }

    // Menu bar extra (optional)
    MenuBarExtra("Status", systemImage: "circle.fill") {
      MenuBarView()
        .environment(Clerk.shared)
    }
    .menuBarExtraStyle(.window)  // required for live-updating content
  }
}
```

Key macOS differences from the iOS pattern:
- The `@MainActor let client` is process-wide — shared across all windows.
- Each `WindowGroup` window gets its own view hierarchy and its own `@StateObject` models.
- Do NOT put `@StateObject` feature models in the `App` struct — they would be shared across all windows unintentionally.
- `MenuBarExtra` requires `.menuBarExtraStyle(.window)` for live-updating SwiftUI content.
- Auth gate pattern (`LandingPage` observing `client.authState`) works identically on macOS.

## Per-Window Feature Models

```swift
struct MainContentView: View {
  // Each window owns its own feature models
  @StateObject var workoutsModel = WorkoutsModel()
  @StateObject var navigationModel = NavigationModel()

  var body: some View {
    NavigationSplitView {
      Sidebar()
    } detail: {
      WorkoutsPage()
    }
    .environmentObject(workoutsModel)
    .environmentObject(navigationModel)
    .toolbar {
      ToolbarItem(placement: .automatic) {
        UserButton()  // ClerkKitUI: works on macOS
      }
    }
  }
}
```

## Menu Bar Rule
- Use `.menuBarExtraStyle(.window)` for live-updating menu bar UX.
- Do not assume the default `.menu` style will behave like a normal realtime SwiftUI surface.
- Keep auth and client ownership above the menu bar shell.

## Sleep, Wake, And App Nap
- Sleep can drop the connection.
- Wake triggers reconnect behavior and may involve cached-session restore via `loginFromCache()`.
- Menu-bar-heavy apps may need explicit App Nap prevention for truly persistent background-style behavior.
- Unlike iOS, macOS does not suspend apps — the WebSocket stays alive when windows are hidden.

## Support Matrix
- The checked XCFramework supports macOS arm64, not Intel macOS.
- Mac Catalyst is not supported.
- Treat these as early architecture constraints, not footnotes for release week.

## Sandbox Rule
- Sandboxed apps need outgoing-network entitlement (`com.apple.security.network.client`).
- Platform distribution planning must include entitlements and slice support up front.

## Avoid
- Sharing one `@StateObject` instance across windows by accident in the app root.
- Designing macOS lifecycle rules as if they matched iOS background suspension.
- Promising Intel or Catalyst support.
- Assuming the official WorkoutTracker iOS example translates directly to macOS without adapting window management, split view navigation, and toolbar placement.

## Read Next
- [../swiftui/04-environment-injection-and-root-architecture.md](../swiftui/04-environment-injection-and-root-architecture.md)
- [../operations/02-known-gaps-limitations-and-non-goals.md](../operations/02-known-gaps-limitations-and-non-goals.md)
- [../playbooks/02-shared-ios-macos-app-playbook.md](../playbooks/02-shared-ios-macos-app-playbook.md)
