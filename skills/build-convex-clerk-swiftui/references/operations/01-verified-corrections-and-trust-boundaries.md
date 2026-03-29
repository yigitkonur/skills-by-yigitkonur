# Verified Corrections And Trust Boundaries

## Use This When
- Translating the research corpus into hard claims.
- Deciding which claims are verified in source versus inferred from documentation or ecosystem discussion.
- Preventing overstatement about support, features, or patterns.

## Corrected Or Nuanced Claims
- `TabView` does cancel `.task` when switching tabs. Do not repeat the older inverted claim.
- `@Observable` may run `init()` multiple times during view rebuilds, but the main practical risk is repeated side effects such as duplicate subscription setup.
- The cited `convex-helpers` pagination/filter bug is historical context, but the referenced issue is closed.
- Binary-size impact should not be described with an overconfident tiny estimate.

## Verified Strong Claims
- The SDK architecture uses a Swift -> UniFFI -> Rust stack with lazy client initialization and Rust-managed reconnection.
- `watchWebSocketState()` behaves like an event stream with no replay.
- Subscription failure is terminal in the Combine pipeline.
- Clerk's official Swift bridge uses `.tokenRefreshed` for push token updates and `.sessionChanged` for automatic client session sync.
- macOS support is Apple Silicon only in the checked XCFramework slices.

### Verified From Official `clerk-convex-swift` Source (v0.1.0+)
- `ClerkConvexAuthProvider` is `@MainActor public final class` conforming to `AuthProvider` with `T = String`.
- The convenience initializer `ConvexClientWithAuth(deploymentUrl:authProvider:)` calls `authProvider.bind(client:)` which starts session sync immediately.
- `bind(client:)` stores a `weak` reference to the client and starts a `Task` that listens for `Clerk.shared.auth.events`.
- Both `login(onIdToken:)` and `loginFromCache(onIdToken:)` delegate to the same internal `authenticate(onIdToken:)`.
- `authenticate(onIdToken:)` calls `fetchToken()` (checks `Clerk.shared.isLoaded`, verifies `session.status == .active`, calls `session.getToken()`) then starts a token refresh listener.
- Session sync uses explicit transition guards: login when `newSession.status == .active` AND (old was not active OR session ID changed); logout when old had ID but new is nil.
- `ClerkConvexAuthError` is a `LocalizedError, Sendable, Equatable` enum with three cases: `.clerkNotLoaded`, `.noActiveSession`, `.tokenRetrievalFailed(String)`.
- `extractIdToken(from:)` is `nonisolated` and returns the input string unchanged (identity function for `T = String`).
- Package requires `clerk-ios >= 1.0.0` and `convex-swift >= 0.8.0`, targets iOS 17+ / macOS 14+, Swift tools 5.10, strict concurrency enabled.
- The official example app uses `convex-helpers` `customQuery`/`customMutation`/`customCtx` for `userQuery`/`userMutation` wrappers with centralized auth checks.
- The official example stores `tokenIdentifier` in a `userId` field with a compound index (`userId_date`).
- The official example uses `@OptionalConvexInt` property wrapper for optional Int64 fields in `Decodable` models.
- The official example uses Combine `.switchToLatest()` for reactive subscription parameter changes and `.removeDuplicates()` to avoid redundant view updates.
- The official example uses a thin landing auth gate with local `@State`; it does not prove every app needs a dedicated `AuthModel` object.
- The official example places `UserButton()` in authenticated feature toolbars rather than the unauthenticated landing screen.

### What The Official Example Does Not Prove
- It does not prove every production app should skip a `users` table; it only proves direct `tokenIdentifier` ownership is valid for a small app.
- It does not prove reconnect UX, stale-data indicators, or offline handling are solved; the sample app does not cover those flows deeply.
- It does not prove a shared iOS + macOS multi-window architecture; the sample is a narrow app template.
- It does not prove `replaceError(with:)` and `try?` are sufficient production error-handling strategy.

## Trust-Boundary Rule
- Prefer verified implementation facts over ecosystem speculation.
- Present community metrics and adoption claims as snapshots, not timeless truths.
- Mark roadmap-adjacent statements as possible future direction, not current capability.
- Where the corpus was partially corrected, preserve the nuance instead of flattening it.

## Safe Language Patterns
- Say "the research corpus indicates" for maturity, ecosystem, and usage observations.
- Say "verified in source" for API shape, auth behavior, connection behavior, and XCFramework support facts.
- Say "current limitation" for missing offline persistence, optimistic updates, or unsupported platform slices.

## Read Next
- [02-known-gaps-limitations-and-non-goals.md](02-known-gaps-limitations-and-non-goals.md)
- [../00-reference-map.md](../00-reference-map.md)
