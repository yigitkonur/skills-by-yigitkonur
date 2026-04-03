# Environment Injection And Root Architecture

## Use This When
- Placing the authenticated client and root auth state in a SwiftUI app.
- Choosing between custom environment keys, environment objects, and newer observation-based environment injection.
- Defining boundaries between infrastructure state and feature state.

## Default Root Shape (Official Example Pattern)

```swift
import ClerkKit
import ClerkConvex
import ClerkKitUI
import ConvexMobile
import SwiftUI

// Top-level client — one per process, lives for the app's lifetime
@MainActor
let client = ConvexClientWithAuth(
  deploymentUrl: Env.convexDeploymentUrl,
  authProvider: ClerkConvexAuthProvider()
)

@main
struct MyApp: App {
  init() {
    Clerk.configure(publishableKey: Env.clerkPublishableKey)
  }
  var body: some Scene {
    WindowGroup {
      LandingPage()
        .prefetchClerkImages()        // ClerkKitUI: preload user avatars
        .environment(Clerk.shared)     // inject Clerk for AuthView/UserButton
    }
  }
}

// Keep secrets/config in one place
struct Env {
  static let clerkPublishableKey = "YOUR_CLERK_PUBLISHABLE_KEY"
  static let convexDeploymentUrl = "YOUR_CONVEX_DEPLOYMENT_URL"
}
```

Key points:
- `@MainActor let client` at the top level — required because `ClerkConvexAuthProvider` is `@MainActor`.
- `Clerk.configure(publishableKey:)` must run in the app `init()` **before** the client is first accessed.
- The convenience initializer calls `authProvider.bind(client:)` internally, starting automatic session sync.
- `.prefetchClerkImages()` is a `ClerkKitUI` view modifier for preloading user avatars.
- `.environment(Clerk.shared)` is required for `AuthView()` and `UserButton()` to function.
- Feature models access the top-level `client` directly (it's a module-level constant).

## Auth Gate At The Root

```swift
struct LandingPage: View {
  @State private var authState: AuthState<String> = .loading
  @State private var authViewIsPresented = false

  var body: some View {
    Group {
      switch authState {
      case .loading: ProgressView()
      case .unauthenticated:
        VStack {
          Button("Login") { authViewIsPresented = true }
        }
      case .authenticated:
        MainView()  // WorkoutsPage() in the official example
      }
    }
    .sheet(isPresented: $authViewIsPresented) {
      AuthView()
    }
    .task {
      for await state in client.authState.values {
        authState = state
      }
    }
  }
}
```

- `client.authState.values` is an `AsyncSequence` from the `CurrentValueSubject`-backed publisher.
- The `.task` modifier ties the subscription to the view's lifetime.
- `AuthView()` from `ClerkKitUI` owns interactive sign-in (SIWA, email, social).
- `UserButton()` from `ClerkKitUI` goes in toolbars for signed-in screens (profile, sign-out).
- The official example uses local `@State` here instead of a dedicated `AuthModel`; that is a good default until auth coordination grows beyond one landing gate.

## What The Official Example Splits Apart
- `WorkoutTrackerApp` owns only Clerk configuration and the long-lived client.
- `LandingPage` owns only auth gate state and sign-in sheet presentation.
- `WorkoutsPage` owns domain state objects such as `WorkoutsModel` and `NavigationModel` with `@StateObject`.
- `WorkoutEditorPage` owns a separate `PendingWorkoutModel` for transient form state and mutation argument assembly.
- Authenticated feature chrome, including `UserButton()`, belongs inside signed-in screens.
- The example keeps app auth state, durable live-query state, transient editor state, and navigation state in separate objects instead of one large root store.

## Injection Options
- Custom environment key: a good default for read-only infrastructure access.
- `@EnvironmentObject`: useful when a richer shared store owns more than just the client.
- iOS 17 observation-based environment injection: viable, but still apply the same ownership rules.
- Module-level `let client` (official pattern): simplest for single-client apps. Feature models reference it directly.
- Move beyond the module-level pattern only when testability, previews, or multiple runtime clients create a real need.

## Boundary Rules
- Auth ownership belongs above navigation boundaries.
- Connection monitoring belongs where multiple screens can share the same truth.
- Per-screen live data belongs in feature models, not in the app object.
- Per-window macOS state belongs in per-window models even when the client is shared process-wide.

## Feature Model Ownership

```swift
struct WorkoutsPage: View {
  @StateObject var workoutsModel = WorkoutsModel()
  @StateObject var navigationModel = NavigationModel()

  var body: some View {
    NavigationStack(path: $navigationModel.path) {
      // ... feature content
    }
    .environmentObject(workoutsModel)
    .environmentObject(navigationModel)
  }
}
```

- Feature models are `@MainActor class: ObservableObject`, owned by `@StateObject`.
- They reference the top-level `client` for subscriptions and mutations.
- They do not construct auth state or manage sessions.
- Splitting domain state and navigation state into separate models, like `WorkoutsModel` and `NavigationModel`, keeps feature boundaries clean.
- Use a separate editor model like `PendingWorkoutModel` when a sheet or editor owns transient form fields, validation, and mutation argument assembly.

## Testing Benefit
- Passing the client into models keeps those models easier to preview and unit test.
- Infrastructure injection is an architectural tool, not just a convenience wrapper.

## Avoid
- Leaf views instantiating `ClerkConvexAuthProvider()` or authenticated clients.
- Treating the app object as the owner of every feature-specific subscription.
- Mixing app-wide auth state and feature-domain state into one oversized root object.
- Modeling Clerk sign-in as a manual `client.login()` action instead of presenting `AuthView()`.
- Forgetting `.environment(Clerk.shared)` — `AuthView()` and `UserButton()` will not work without it.
- Treating `UserButton()` as part of unauthenticated bootstrap UI instead of authenticated feature chrome.

## Read Next
- [02-observation-and-ownership.md](02-observation-and-ownership.md)
- [../authentication/01-clerk-first-setup.md](../authentication/01-clerk-first-setup.md)
- [../platforms/04-macos-multi-window-menu-bar-and-support-limits.md](../platforms/04-macos-multi-window-menu-bar-and-support-limits.md)
