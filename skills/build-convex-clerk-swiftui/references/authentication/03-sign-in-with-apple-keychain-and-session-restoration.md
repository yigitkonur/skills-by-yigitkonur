# Sign In With Apple, Keychain, And Session Restoration

## Use This When
- A team wants Sign in with Apple in a Convex-backed Swift app.
- Designing credential persistence and secure session storage.
- Deciding whether direct Apple identity-token auth is acceptable.

## Default Position
- Prefer Clerk-managed SIWA for production. `AuthView()` from `ClerkKitUI` handles the interactive Sign in with Apple flow natively — no custom `ASAuthorizationController` code needed on the Swift side.
- Treat raw Apple identity tokens as short-lived bootstrap material, not durable renewable sessions.
- Store durable session material in Keychain, not `UserDefaults`.
- In Clerk-backed apps, let `AuthView()` own the interactive SIWA flow and let the bound Convex client follow Clerk session changes automatically via the `bind(client:)` session sync.

## Clerk + SIWA: The Official Path

When Clerk is the auth provider, Sign in with Apple is just one of the methods `AuthView()` supports:

```swift
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

struct LandingPage: View {
  @State private var authState: AuthState<String> = .loading
  @State private var authViewIsPresented = false

  var body: some View {
    Group {
      switch authState {
      case .loading: ProgressView()
      case .unauthenticated:
        Button("Sign In") { authViewIsPresented = true }
      case .authenticated: MainView()
      }
    }
    .sheet(isPresented: $authViewIsPresented) {
      AuthView()  // handles SIWA, email, social — whatever Clerk is configured for
    }
    .task {
      for await state in client.authState.values {
        authState = state
      }
    }
  }
}
```

- `AuthView()` renders Sign in with Apple as a first-class option when enabled in the Clerk dashboard.
- Clerk exchanges Apple's short-lived identity token for a renewable Clerk session internally.
- The `ClerkConvexAuthProvider`'s bound session sync keeps Convex aligned automatically.
- `UserButton()` from `ClerkKitUI` provides signed-in user management (profile, sign-out) as a toolbar item.

## Keychain Rules
- Use Keychain for refresh-capable or restorable session material.
- Choose accessibility based on product behavior, not convenience.
- Use biometric-protected items as a local security enhancement, not a replacement for renewable sessions.

## Session-Restore Rule
- `loginFromCache()` is the place where cached credentials are revalidated or renewed.
- A restored session must still be able to produce a current JWT for the Convex bridge.
- Session restoration is part of normal reconnect behavior, not a niche launch-time path.
- In the official Clerk bridge, `.sessionChanged` drives this sync automatically after the provider binds to the client. Both `login` and `loginFromCache` call the same internal `authenticate()` because Clerk manages credential caching and renewal.

## SIWA Guidance
- Direct SIWA token bridging is a niche choice and not the production default.
- If the app needs reliable renewable auth, route SIWA through Clerk or a backend exchange.
- Keep server ownership keyed by `tokenIdentifier`, not by raw Apple-specific fields.

## Avoid
- Storing sensitive session material in `UserDefaults`.
- Treating Apple identity tokens as if they were long-lived refreshable sessions.
- Conflating biometric unlock with auth refresh or backend session validity.
- Building a custom `ASAuthorizationController` flow when `AuthView()` from `ClerkKitUI` already handles SIWA natively.

## Read Next
- [01-clerk-first-setup.md](01-clerk-first-setup.md)
- [02-custom-auth-provider-and-firebase-fallback.md](02-custom-auth-provider-and-firebase-fallback.md)
- [../platforms/01-ios-backgrounding-reconnection-and-staleness.md](../platforms/01-ios-backgrounding-reconnection-and-staleness.md)
