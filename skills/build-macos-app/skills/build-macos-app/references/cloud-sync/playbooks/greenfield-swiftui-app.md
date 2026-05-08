# Greenfield SwiftUI App Playbook

## Use This When
- Starting a new SwiftUI app on Convex from scratch.
- Needing a default implementation order for product teams.
- Translating the corpus into execution steps.

## Reference Implementation
The official `clerk-convex-swift` example app (`Example/WorkoutTracker` in `github.com/clerk/clerk-convex-swift`) demonstrates the canonical small-app Clerk + Convex SwiftUI **iOS** baseline. Use it as a template for bootstrap, auth-gate, backend-wrapper, and feature-model patterns, not as a complete macOS or shared-app architecture.

## Default Sequence
1. Decide fit with [../onboarding/04-adoption-checklist-and-hard-stops.md](../onboarding/04-adoption-checklist-and-hard-stops.md).
2. Settle the mental model with [../onboarding/03-mental-model-live-data-functions-and-state.md](../onboarding/03-mental-model-live-data-functions-and-state.md).
3. Stand up Clerk auth and root client ownership:
   - Add `clerk-convex-swift` (product `ClerkConvex`) and `clerk-ios` (product `ClerkKit`, `ClerkKitUI`) as SPM dependencies.
   - Create `convex/auth.config.ts` with Clerk issuer URL and `applicationID: "convex"`.
   - Call `Clerk.configure(publishableKey:)` in the app `init()`.
   - Create one `@MainActor let client = ConvexClientWithAuth(deploymentUrl:authProvider: ClerkConvexAuthProvider())` at the top level.
   - Build a root auth gate observing `client.authState.values`, presenting `AuthView()` from `ClerkKitUI`.
   - Add `.prefetchClerkImages()` and `.environment(Clerk.shared)` on the root view.
4. Create `convex/functions.ts` with `userQuery`/`userMutation` wrappers using `convex-helpers` `customQuery`/`customMutation`/`customCtx`.
5. Design schema, indexes, and ownership rules before UI wiring. Use `tokenIdentifier` as the ownership key.
6. Build feature models around small bounded live queries using `client.subscribe(to:with:)` with Combine.
7. Add platform-specific reconnect and stale-data UX.

## Default Architecture
- One app-scoped authenticated client created with `ClerkConvexAuthProvider()`, bound via the convenience initializer.
- One root auth gate observing `authState` and presenting `AuthView()` for sign-in.
- Signed-in screens use `UserButton()` for user management where appropriate.
- `.environment(Clerk.shared)` injected on the root view for ClerkKitUI components.
- Feature-specific `@MainActor class: ObservableObject` models owned by `@StateObject`.
- Backend queries for live reads via `userQuery`, mutations for writes via `userMutation`, scheduled action flows for external side effects.
- `convex-helpers` user-guarded function wrappers centralizing auth checks.

## Copy These Patterns Directly From WorkoutTracker
- Keep the app bootstrap thin: configure Clerk, create the top-level client, and hand off to a landing/auth gate.
- Let the landing screen own only `authState` and sign-in sheet presentation.
- Put `UserButton()` inside authenticated feature toolbars rather than the app bootstrap.
- Split feature ownership by role: `WorkoutsModel` owns durable live-query state, `PendingWorkoutModel` owns transient editor/form state plus mutation argument assembly, and `NavigationModel` owns routing state.
- Use `tokenIdentifier` directly on domain documents when the product only needs per-user scoping.
- Use Combine `.switchToLatest()` when subscription parameters change over time.

## Extend Beyond WorkoutTracker Before Calling The App Production-Ready
- Add explicit error surfaces instead of relying on `replaceError(with:)` or `try?` everywhere.
- Add reconnect and stale-data UX for iOS background/foreground cycles.
- Add a richer `users` table only if the product truly needs profile or multi-feature user data.
- Add pagination, uploads, background workflows, or multi-window structure only when the product actually needs them.
- Add app-specific authorization beyond "user owns their own rows" if the product has roles, teams, or shared resources.

## Review Gates
- Verify there are no hard-stop product mismatches.
- Verify ownership uses `tokenIdentifier` server-side via `userQuery`/`userMutation` wrappers.
- Verify live queries are bounded.
- Verify iOS reconnect and macOS support assumptions are explicit.
- Verify `ClerkKitUI` components (`AuthView`, `UserButton`) are used instead of custom auth UI.
- Verify teams are not copying the example's simplifications blindly where their product needs richer user modeling or error handling.

## Read Next
- [02-shared-ios-macos-app-playbook.md](02-shared-ios-macos-app-playbook.md)
- [../authentication/01-clerk-first-setup.md](../authentication/01-clerk-first-setup.md)
- [../backend/01-schema-document-model-and-relationships.md](../backend/01-schema-document-model-and-relationships.md)
