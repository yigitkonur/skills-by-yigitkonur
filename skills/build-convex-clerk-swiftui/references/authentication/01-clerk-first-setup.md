# Clerk-First Setup

## Use This When
- Setting up auth for a new SwiftUI app on Convex.
- Choosing the default auth path for iOS, macOS, or shared Apple-platform apps.
- Designing root session ownership.

## Default Position
- Treat Clerk + Convex as the default auth path for Swift.
- It is the current first-party path with an official bridge package maintained by Clerk.
- Build one long-lived `ConvexClientWithAuth<String>` and one root auth gate at the app boundary.
- Start with the official example's simple local-`@State` auth gate. Introduce a dedicated auth model only when app-wide coordination actually needs one.

## Package Identity
- Repository: `github.com/clerk/clerk-convex-swift`
- Product name: `ClerkConvex`
- Dependencies: `clerk-ios >= 1.0.0`, `convex-swift >= 0.8.0`
- Platforms: iOS 17+ / macOS 14+
- Swift tools version: 5.10
- Strict concurrency enabled in the package.

## Required Pieces
- `convex/auth.config.ts` on the backend with the Clerk issuer URL and `applicationID: "convex"`.
- Clerk SDK configuration in the app: `Clerk.configure(publishableKey:)` **before** the first access that initializes the authenticated client.
- `clerk-convex-swift` bridge package (product `ClerkConvex`).
- A root auth gate that mirrors `client.authState` and presents `AuthView()` from `ClerkKitUI` for sign-in.
- Signed-in screens that expose account controls with `UserButton()` where appropriate.

## Exact Wiring (Matches Official Example)

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
struct MyApp: App {
  init() {
    Clerk.configure(publishableKey: Env.clerkPublishableKey)
  }
  var body: some Scene {
    WindowGroup {
      LandingPage()
        .prefetchClerkImages()
        .environment(Clerk.shared)
    }
  }
}
```

Key details:
- The convenience initializer `ConvexClientWithAuth(deploymentUrl:authProvider:)` calls `authProvider.bind(client:)` internally, which starts automatic session sync immediately.
- `@MainActor` on the top-level `let client` is required because `ClerkConvexAuthProvider` is `@MainActor`.
- **Init ordering is safe:** Swift lazily initializes module-level `let` constants on first access. The `@MainActor` annotation serializes access to the main thread. Since `client` is first accessed when the SwiftUI view hierarchy builds (after `App.init()` runs), `Clerk.configure()` always completes before `client` is initialized. The official WorkoutTracker relies on this ordering.
- `.prefetchClerkImages()` is a `ClerkKitUI` view modifier that preloads Clerk user avatar assets.
- `.environment(Clerk.shared)` injects the Clerk instance for `AuthView()` and `UserButton()` to use.

## Auth Gate Pattern (Matches Official Example)

```swift
struct LandingPage: View {
  @State private var authState: AuthState<String> = .loading
  @State private var authViewIsPresented = false

  var body: some View {
    Group {
      switch authState {
      case .loading:
        ProgressView()
      case .unauthenticated:
        Button("Sign In") { authViewIsPresented = true }
      case .authenticated:
        MainView()
      }
    }
    .sheet(isPresented: $authViewIsPresented) {
      AuthView()   // from ClerkKitUI — owns the interactive sign-in flow
    }
    .task {
      for await state in client.authState.values {
        authState = state
      }
    }
  }
}
```

- `AuthView()` from `ClerkKitUI` handles all interactive sign-in methods Clerk supports, including Sign in with Apple.
- `UserButton()` from `ClerkKitUI` is a toolbar-ready avatar button for signed-in users (sign-out, profile management).
- Do **not** build sign-in around a manual `client.login()` call; Clerk UI owns sign-in, and the bound provider syncs Convex automatically.

## What The Official Example App Actually Owns
- `WorkoutTrackerApp` owns Clerk configuration and the single top-level authenticated client.
- `LandingPage` owns only the auth gate state (`authState`, `authViewIsPresented`) and the auth sheet presentation.
- Authenticated feature screens own their own domain state after sign-in.
- `UserButton()` lives on authenticated screens such as `WorkoutsPage` toolbars, not on the unauthenticated landing gate.
- The example does **not** create a separate `AuthModel` object for login/logout commands.

## How The Bridge Works Internally

The `ClerkConvexAuthProvider` has three internal mechanisms:

1. **Token fetch**: `session.getToken()` on the active `Clerk.shared.session`.
2. **Token refresh listener**: listens for `.tokenRefreshed(let token)` from `Clerk.shared.auth.events` and pushes fresh JWTs to the Convex client via the stored `onIdToken` callback.
3. **Session sync**: listens for `.sessionChanged(oldSession, newSession)` and triggers `client.loginFromCache()` when a session transitions to active, or `client.logout()` when a session is removed.

The session sync uses explicit transition guards:
- Login when `newSession.status == .active` AND (old was not active OR session ID changed).
- Logout when `oldSession` had an ID but `newSession` is nil.

Both `login(onIdToken:)` and `loginFromCache(onIdToken:)` call the same internal `authenticate(onIdToken:)`, which stores the callback, fetches the current token, and starts the refresh listener.

## Typed Errors

`ClerkConvexAuthError` covers three failure modes:
- `.clerkNotLoaded` — `Clerk.shared.isLoaded` is false. Wait for Clerk to load before authenticating.
- `.noActiveSession` — no `Clerk.shared.session` with `.active` status. The user must sign in first.
- `.tokenRetrievalFailed(String)` — `session.getToken()` returned nil.

## Server Identity Rule
- Use `ctx.auth.getUserIdentity()?.tokenIdentifier` as the canonical ownership key.
- For minimal per-user products, it is valid to store `tokenIdentifier` directly on domain documents and indexes. The official `WorkoutTracker` example does this with a `userId` string field.
- Add an app `users` record only when the product needs profile data, preferences, richer joins, or cross-feature user metadata.
- Do not use client-passed IDs as an authorization shortcut.
- Use `convex-helpers` `customQuery`/`customMutation` with `customCtx` for user-guarded wrappers (see backend/04).

## Client Ownership Rule
- Keep auth/session ownership at the app boundary.
- Do not recreate the authenticated client in feature views, windows, or menu bar surfaces.
- Let feature models assume an authenticated client already exists and focus on product state.
- Feature models use `client.subscribe(to:with:)` for live queries and `client.mutation(...)` for writes.
- When signed-in surfaces need user controls, place `UserButton()` inside those authenticated screens rather than inside the app bootstrap.

## Why Clerk Wins By Default
- It aligns with the current Convex auth model directly.
- The official provider resolves JWTs with `session.getToken()` and pushes `.tokenRefreshed` updates through the bridge.
- Session restore and session transitions are designed around `loginFromCache()`, `.sessionChanged`, and durable Clerk-managed credentials.
- It removes a large amount of custom auth-provider work from Swift teams.
- The `bind(client:)` initializer-time binding means session sync starts automatically — no manual wiring needed.

## Avoid
- Treating Firebase or direct SIWA as equal-default options.
- Putting auth bootstrap in feature screens.
- Ignoring the backend `auth.config.ts` requirement.
- Building custom sign-in UI when `AuthView()` from `ClerkKitUI` already handles it.
- Calling `client.login()` manually — interactive sign-in is Clerk UI's job.

## Read Next
- [02-custom-auth-provider-and-firebase-fallback.md](02-custom-auth-provider-and-firebase-fallback.md)
- [03-sign-in-with-apple-keychain-and-session-restoration.md](03-sign-in-with-apple-keychain-and-session-restoration.md)
- [../swiftui/04-environment-injection-and-root-architecture.md](../swiftui/04-environment-injection-and-root-architecture.md)
