# Client Surface, Runtime, And Auth Bridge

## Use This When
- Explaining what the Swift SDK actually exposes.
- Placing `ConvexClient` or `ConvexClientWithAuth` in app architecture.
- Clarifying how the auth bridge interacts with the Rust runtime.

## Public Surface To Remember
- `subscribe(to:with:yielding:)` for live query results (returns a Combine `Publisher`).
- `mutation(...)` and `action(...)` as `async throws` calls.
- `watchWebSocketState()` for connection-state events.
- `initConvexLogging()` for debug logging.
- `ConvexClientWithAuth<T>` for authenticated flows backed by an `AuthProvider`.
- `authState` — a `CurrentValueSubject`-backed publisher that emits `.loading`, `.authenticated(T)`, or `.unauthenticated`.

## Runtime Shape
- The public Swift layer is a thin shell over UniFFI bindings into a Rust client.
- Connection setup is lazy; the websocket is not fully established until needed.
- JSON-string FFI payloads are a core part of the bridge, so encoding and decoding shape matter.
- There is no public one-shot `query()` API in the current Swift surface.

**Workaround for one-shot reads:** Use `subscribe()` with Combine's `.first()` operator, which takes the first emitted value then automatically cancels the subscription:

```swift
let result: [Message] = try await client.subscribe(to: "messages:latest", yielding: [Message].self)
    .first()
    .values
    .first(where: { _ in true })!
```

## Auth Bridge Shape
- `ConvexClientWithAuth` delegates login, cached session restore, logout, and token extraction to an `AuthProvider`.
- The provider stores the `onIdToken` callback and uses it to push fresh or invalidated tokens to the underlying client.
- `loginFromCache()` is the session-restore and reconnect path, not optional convenience glue.
- A healthy auth architecture keeps one authenticated client alive at the app boundary.
- In the official Clerk path, the `ClerkConvex` convenience initializer calls `authProvider.bind(client: self)`, which stores a `weak` reference to the client and starts automatic session sync via `Clerk.shared.auth.events`.
- The Clerk bridge resolves tokens with `session.getToken()`, pushes `.tokenRefreshed` updates, and reacts to `.sessionChanged`.
- Both `login(onIdToken:)` and `loginFromCache(onIdToken:)` delegate to a shared `authenticate(onIdToken:)` internally.

## Type Helpers For Decodable Models

### `@OptionalConvexInt` Property Wrapper

Convex represents integers as `Int64` on the wire. The `@OptionalConvexInt` property wrapper handles optional Int64 → optional Int decoding:

```swift
struct Workout: Identifiable, Equatable, Decodable {
  let id: String
  let _date: String
  let activity: Activity
  @OptionalConvexInt
  var duration: Int?

  enum CodingKeys: String, CodingKey {
    case id = "_id"
    case _date = "date"
    case activity
    case duration
  }
}
```

- Use `_id` as the `CodingKeys` mapping for Convex document IDs.
- Use `@OptionalConvexInt` for optional integer fields that come across as Int64.
- Model types should be `Decodable`, `Identifiable`, and `Equatable` for use with SwiftUI lists and Combine deduplication.

## Feature Model Patterns (Adapted From Official Example)

### Reactive Subscriptions With Combine

Feature models use `client.subscribe(to:with:)` with Combine operators for live data. The snippet below is adapted from the official `WorkoutsModel` shape:

```swift
@MainActor
class WorkoutsModel: ObservableObject {
  @Published var workouts: [Workout] = []
  @Published var selectedStartOfWeek: Date

  init() {
    // Compute start of current week (uses UTC-configured calendar)
    let dayOfWeek = Calendar.current.component(.weekday, from: Date.now)
    selectedStartOfWeek = calendar.date(
      byAdding: .day, value: dayTranslation[dayOfWeek]!, to: Date.now)!

    $selectedStartOfWeek
      .map { week in
        client.subscribe(
          to: "workouts:getInRange",
          with: [
            "startDate": week.localIso8601DateFormat(),
            "endDate": calendar.date(byAdding: .day, value: 6, to: week)!
              .localIso8601DateFormat(),
          ]
        )
        .removeDuplicates()
        .replaceError(with: [])
        .receive(on: DispatchQueue.main)
        .eraseToAnyPublisher()
      }
      .switchToLatest()
      .assign(to: &$workouts)
  }
}
```

Key patterns:
- **`.switchToLatest()`**: when subscription parameters change (e.g. selected week), the previous subscription is automatically cancelled and replaced by the new one.
- **`.removeDuplicates()`**: avoids unnecessary view updates when data hasn't changed.
- **`.replaceError(with:)`**: subscription failures are terminal in Combine; replace with a safe default.
- **`.receive(on: DispatchQueue.main)`**: ensure UI updates happen on the main thread.
- **`.assign(to: &$published)`**: bind directly to a `@Published` property for automatic SwiftUI updates.

### Mutations From Feature Models

```swift
func delete(workout: Workout) {
  let args: [String: ConvexEncodable] = ["workoutId": workout.id]
  Task { @MainActor in
    try? await client.mutation("workouts:remove", with: args)
  }
}
```

- Mutation arguments use `[String: ConvexEncodable]` dictionaries.
- Wrap in `Task { @MainActor in }` when calling from a synchronous context.

## Official Example Boundary
- The official example uses a module-level `@MainActor let client` rather than dependency injection into each feature model.
- `LandingPage` observes `client.authState.values` directly with local `@State` and presents `AuthView()`.
- Authenticated feature models such as `WorkoutsModel` and `PendingWorkoutModel` call the shared `client` directly.
- This is the simplest correct shape for a small single-client app; explicit injection is still useful when previews and tests need isolated clients.

## Default Usage Rules
- Create one long-lived client per process.
- Keep the authenticated client separate from feature view models.
- Prefer one root auth gate or owner that mirrors `authState` into app-level state.
- Do not hide the absence of a public one-shot query helper; design around subscriptions and explicit workarounds instead.
- Feature models should be `@MainActor class` with `ObservableObject` conformance, owned by `@StateObject` in views.
- Use the official example's module-level client pattern unless the app has a clear testing or modularity reason to inject the client differently.

## Avoid
- Recreating the client inside views or per-window popovers.
- Treating `action()` as a generic read substitute when a query or mutation should own the flow.
- Confusing transport reconnect with automatic resurrection of a failed Combine pipeline.
- Expecting interactive Clerk sign-in to come from a manual `client.login()` button instead of `AuthView()` from `ClerkKitUI`.
- Assuming a separate `AuthModel` object is mandatory when a local root auth gate already solves the app's needs.

## Read Next
- [02-type-system-wire-format-and-modeling.md](02-type-system-wire-format-and-modeling.md)
- [03-subscriptions-errors-logging-and-connection-state.md](03-subscriptions-errors-logging-and-connection-state.md)
- [../swiftui/04-environment-injection-and-root-architecture.md](../swiftui/04-environment-injection-and-root-architecture.md)
