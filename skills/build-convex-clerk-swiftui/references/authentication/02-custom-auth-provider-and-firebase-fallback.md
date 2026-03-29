# Custom AuthProvider And Firebase Fallback

## Use This When
- Clerk is not available or not acceptable.
- Implementing a custom `AuthProvider<T>`.
- Integrating Firebase Auth into Convex on Swift.

## Contract To Respect
- `login(onIdToken:)` must establish a fresh authenticated session.
- `loginFromCache(onIdToken:)` must restore or validate a cached session for reconnect and launch restore.
- `extractIdToken(from:)` must return the JWT Convex should use. Must be `nonisolated` if the provider is `@MainActor`.
- `logout()` must tear down session state, cancel listeners, and sign out cleanly.

## The `onIdToken` Rule
- Store the callback when login or restore succeeds.
- Push fresh JWTs when the provider refreshes them.
- Push `nil` when the session becomes invalid.
- Treat this callback as the live bridge into the Convex auth runtime, not optional bookkeeping.
- Do NOT call `onIdToken` synchronously from within `login`/`loginFromCache` — the return value seeds the initial token via `extractIdToken`.

## Reference: How The Official Clerk Provider Structures This

The official `ClerkConvexAuthProvider` is the canonical implementation to model custom providers after:

- **Shared authenticate path**: both `login(onIdToken:)` and `loginFromCache(onIdToken:)` delegate to a single `authenticate(onIdToken:)` method that stores the callback, fetches the current token, and starts a refresh listener. Custom providers can follow this same pattern when their login and cache-restore logic are equivalent.
- **Session transition guards**: the provider tracks session transitions with explicit guards:
  - **Login** when `newSession.status == .active` AND (old was not active OR session ID changed).
  - **Logout** when `oldSession` had an ID but `newSession` is nil.
  - Custom providers should implement similar transition logic rather than naively calling login/logout on every auth event.
- **Weak client reference**: the provider holds a `weak` reference to `ConvexClientWithAuth` via `bind(client:)` to avoid retain cycles. Custom providers that bind to the client should do the same.
- **Task-based listeners**: token refresh and session sync run as `Task` instances stored as properties. In the official Clerk provider, `logout()` explicitly cancels the token-refresh listener and clears `onIdToken`, while the session-sync task remains bound to auth events so future session transitions can still drive client login/logout. Custom providers should be equally explicit about which listeners stop on logout and which remain to observe future auth changes.

## Firebase Position
- Firebase is a viable OIDC fallback, not the default path.
- You own the provider implementation, listener lifecycle, and token-refresh behavior.
- Firebase credential persistence helps, but the Convex bridge logic is still your responsibility.
- Unlike the official Clerk bridge, there is no packaged session-sync helper that binds directly to `ConvexClientWithAuth`.
- Firebase's `addIDTokenDidChangeListener` is the closest analog to Clerk's `.tokenRefreshed` event for driving `onIdToken` updates.

## `loginFromCache()` Rule
- This is the reconnect path on network recovery or app resume.
- Cached credentials must be checked or renewed before being returned.
- A provider that skips real validation here will produce brittle reconnect behavior.
- In the official Clerk provider, `loginFromCache` calls the exact same `authenticate()` as `login` because Clerk manages credential caching and renewal internally. Custom providers whose auth backend does not cache credentials must add explicit cache-check logic here.

## Avoid
- Pull-only token strategies when the provider can emit refresh events.
- Returning stale cached sessions without renewal or verification.
- Treating a custom provider as if it were lower maintenance than Clerk.
- Copying Clerk-oriented SwiftUI guidance while still expecting a custom provider to behave like `ClerkConvexAuthProvider` without implementing the same semantics.
- Skipping session transition guards — logging in on every auth event instead of only on meaningful transitions wastes work and can cause flickering auth state.

## Read Next
- [01-clerk-first-setup.md](01-clerk-first-setup.md)
- [03-sign-in-with-apple-keychain-and-session-restoration.md](03-sign-in-with-apple-keychain-and-session-restoration.md)
- [../backend/04-auth-rules-and-server-ownership.md](../backend/04-auth-rules-and-server-ownership.md)
