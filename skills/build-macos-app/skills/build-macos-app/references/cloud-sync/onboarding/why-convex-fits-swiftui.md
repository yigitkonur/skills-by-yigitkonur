# Why Convex Fits SwiftUI

## Use This When
- Explaining Convex to SwiftUI-native developers who have not built a backend before.
- Framing why Convex feels different from Firebase or Supabase on Apple platforms.
- Deciding whether the app's UI model benefits from live subscriptions instead of manual fetch-and-cache work.

## Core Alignment
- SwiftUI is reactive: the UI describes what it should look like for current state.
- Convex applies the same idea to backend data: describe a query once, then keep the result current.
- The Swift SDK exposes `subscribe(...) -> AnyPublisher<T, ClientError>` and `.values` for `AsyncSequence`, which map directly onto SwiftUI consumption patterns.
- This removes the common split found in other stacks between "initial fetch" and "separate realtime listener".

## Why This Feels Native In SwiftUI
- `@Published` and `ObservableObject` already speak Combine; Convex subscriptions drop straight into that pipeline.
- `.task { for await ... }` matches view-scoped subscriptions for simple screens.
- `assign(to: &$property)` and `sink` let long-lived view models own subscriptions without manual listener cleanup.
- SwiftUI cancellation semantics can own the subscription lifecycle when the subscription is placed correctly.

## Where Convex Reduces Friction
- No manual merge between REST-loaded data and websocket-delivered changes.
- No explicit listener-registration object comparable to Firebase's cleanup model.
- Query/mutation/action categories give Swift teams a cleaner mental model than assembling ad hoc endpoints.
- Server-side joins and reactive re-execution reduce client cache invalidation code.

## What Makes The Fit Real Instead Of Marketing
- The SDK is thin but architecturally sound: Swift -> UniFFI -> Rust -> Convex sync engine.
- Reconnection and resubscription behavior are handled inside the Rust layer, not rebuilt in Swift.
- Auth refresh can be pushed through `onIdToken` rather than polled manually.
- The main remaining work in Swift is choosing safe ownership and lifecycle patterns.

## Best Fit Profile
- Realtime-heavy UIs such as chat, collaboration, activity feeds, dashboards, queues, or operator consoles.
- Teams fluent in SwiftUI that are willing to put backend logic in TypeScript.
- Apps where "latest truth" matters more than offline-first local persistence.
- Teams willing to accept an early-stage Swift ecosystem in exchange for a more coherent live-data model.

## Do Not Oversell It
- Convex is not the right fit purely because it feels reactive.
- If the app needs offline-first storage, SQL-heavy reporting, Intel Mac distribution, or unsupported Apple platforms, the SwiftUI alignment is not enough to override those gaps.
- The ecosystem remains small; Discord and source reading are part of the operational reality.

## Read Next
- [02-convex-vs-firebase-vs-supabase.md](02-convex-vs-firebase-vs-supabase.md)
- [03-mental-model-live-data-functions-and-state.md](03-mental-model-live-data-functions-and-state.md)
- [04-adoption-checklist-and-hard-stops.md](04-adoption-checklist-and-hard-stops.md)
