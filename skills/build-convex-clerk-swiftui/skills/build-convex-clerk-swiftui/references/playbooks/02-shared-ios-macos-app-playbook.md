# Shared iOS And macOS App Playbook

## Use This When
- One product targets both iPhone and Mac.
- The team needs shared backend rules but different platform assumptions.
- Planning where to unify versus split behavior.

## Shared Defaults
- One backend schema and ownership model with `userQuery`/`userMutation` wrappers.
- One auth gate built around Clerk, `authState`, and `AuthView()`.
- Signed-in surfaces use `UserButton()` where account controls belong.
- One process-scoped client per app runtime (`@MainActor let client`).
- Shared feature models where lifecycle assumptions truly match.
- `.prefetchClerkImages()` and `.environment(Clerk.shared)` on the root view for both platforms.

## What Transfers Cleanly From The Official Example
- The single top-level authenticated client pattern.
- The landing-gate pattern that presents `AuthView()` and observes `client.authState.values`.
- The backend `userQuery`/`userMutation` wrapper approach.
- Feature models owned by `@StateObject` and split by responsibility.

## What Does Not Transfer Blindly
- `WorkoutTracker` is a simple single-scene iOS example, not a full shared iPhone + Mac architecture.
- A direct `tokenIdentifier` field may be enough for small apps, but shared products often outgrow that and need a richer `users` table or membership model.
- Toolbar placement, window ownership, and menu bar surfaces need explicit macOS decisions.
- iOS reconnect UX and macOS multi-window behavior still need product-specific design.

## Split The Platform Assumptions
- iOS needs reconnect and stale-data UX after background.
- macOS needs per-window state decisions, menu bar style decisions, and support-matrix messaging.
- Do not write one lifecycle story that pretends both platforms behave the same.
- `AuthView()` and `UserButton()` are part of a package that targets both iOS 17+ and macOS 14+, but `WorkoutTracker` itself is not a full macOS UX proof point.

## Architecture Notes
- Keep the backend shared unless product behavior truly diverges.
- Keep the client shared at the app boundary.
- Keep window- or scene-specific models separate on macOS.
- Keep iOS view ownership conservative because `.task` cancellation happens often.
- Feature models should use `@StateObject` ownership and Combine-based subscriptions with `.switchToLatest()` for reactive parameter changes.

## Review Gates
- Confirm Apple Silicon-only macOS support is acceptable.
- Confirm menu bar or multi-window surfaces are planned explicitly if relevant.
- Confirm iOS stale-state UX exists.

## Read Next
- [../platforms/01-ios-backgrounding-reconnection-and-staleness.md](../platforms/01-ios-backgrounding-reconnection-and-staleness.md)
- [../platforms/04-macos-multi-window-menu-bar-and-support-limits.md](../platforms/04-macos-multi-window-menu-bar-and-support-limits.md)
- [../swiftui/04-environment-injection-and-root-architecture.md](../swiftui/04-environment-injection-and-root-architecture.md)
