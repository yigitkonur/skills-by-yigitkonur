# Complete Swift Models and ViewModels

## Use This When
- Building the Swift client layer for a Convex + SwiftUI app.
- Need copy-pasteable models and ViewModels that match a Convex backend.
- Reviewing how subscriptions, mutations, and error handling wire together.

---

## Convex Client (Module-Level)

```swift
import ClerkConvex
import ClerkKit
import ConvexMobile

// One client for the app -- bind() auto-syncs Clerk sessions
@MainActor
let client = ConvexClientWithAuth(
    deploymentUrl: "https://YOUR_SLUG.convex.cloud",
    authProvider: ClerkConvexAuthProvider()
)
```

No manual `login()` or `loginFromCache()` calls needed. With `ClerkConvexAuthProvider`, the `bind()` mechanism listens to `Clerk.shared.auth.events` and calls them automatically on session changes.

---

## Models

Every `Decodable` model **must** include `CodingKeys` with `case id = "_id"`.

```swift
struct Message: Decodable, Identifiable, Equatable {
    let id: String
    let body: String
    let userId: String
    let channelId: String

    enum CodingKeys: String, CodingKey {
        case id = "_id"
        case body
        case userId
        case channelId
    }
}

struct Channel: Decodable, Identifiable, Hashable {
    let id: String
    let name: String
    let createdBy: String

    enum CodingKeys: String, CodingKey {
        case id = "_id"
        case name
        case createdBy
    }
}
```

For fields using `v.int64()` on the server, use `@ConvexInt`:

```swift
struct Workout: Identifiable, Equatable, Decodable {
    let id: String
    let activity: String
    let date: String
    @OptionalConvexInt var duration: Int?

    enum CodingKeys: String, CodingKey {
        case id = "_id"
        case activity, date, duration
    }
}
```

---

## ChannelListViewModel

```swift
import Combine
import ConvexMobile

class ChannelListViewModel: ObservableObject {
    @Published var channels: [Channel] = []
    private var cancellables = Set<AnyCancellable>()

    init() {
        client.subscribe(to: "channels:list", yielding: [Channel].self)
            .replaceError(with: []) // ⚠️ PROTOTYPE ONLY — kills pipeline after first error. See pitfalls/01.
            .receive(on: DispatchQueue.main)
            .assign(to: &$channels)
    }
}
```

## ChannelViewModel

```swift
class ChannelViewModel: ObservableObject {
    @Published var messages: [Message] = []
    @Published var isSending = false
    @Published var error: String?
    private var cancellables = Set<AnyCancellable>()
    let channelId: String

    init(channelId: String) {
        self.channelId = channelId
        client.subscribe(
            to: "messages:list",
            with: ["channelId": channelId],
            yielding: [Message].self
        )
        .replaceError(with: []) // ⚠️ PROTOTYPE ONLY — kills pipeline after first error. See pitfalls/01.
        .receive(on: DispatchQueue.main)
        .assign(to: &$messages)
    }

    func send(body: String) {
        guard !body.trimmingCharacters(in: .whitespaces).isEmpty else { return }
        isSending = true
        error = nil
        Task { @MainActor in
            do {
                try await client.mutation("messages:send", with: [
                    "channelId": channelId,
                    "body": body
                ]) as Void
            } catch ClientError.ConvexError(let data) {
                error = try? JSONDecoder().decode(String.self, from: Data(data.utf8))
            } catch {
                self.error = error.localizedDescription
            }
            isSending = false
        }
    }
}
```

## ConnectionViewModel

```swift
class ConnectionViewModel: ObservableObject {
    @Published var isConnected = false

    init() {
        client.watchWebSocketState()
            .map { $0 == .connected }
            .receive(on: DispatchQueue.main)
            .assign(to: &$isConnected)
    }
}
```

---

## Pipeline Termination Warning

`.replaceError(with: [])` in the ViewModels above hides errors and terminates the stream. For production, use `Result`-wrapping or explicit `sink(receiveCompletion:receiveValue:)`. See [../client-sdk/03-subscriptions-errors-logging-and-connection-state.md](../client-sdk/03-subscriptions-errors-logging-and-connection-state.md).

## Note on Variable Naming

The official example uses `client` (not `convex`) as the module-level variable name. Both work, but `client` matches the official `clerk-convex-swift` WorkoutTracker example.

## Avoid
- Naming the module-level variable `convex` -- use `client` to match official examples.
- Calling `loginFromCache()` manually -- `ClerkConvexAuthProvider` handles session sync via `bind()`.
- Forgetting `CodingKeys` with `case id = "_id"` -- Convex documents use `_id`, not `id`.
- Using `@ObservedObject` where `@StateObject` is needed -- the VM will be recreated on every re-render.
- Omitting `.receive(on: DispatchQueue.main)` -- Combine publishers from the Convex SDK deliver on background threads.

## Read Next
- [02-complete-schema-and-backend-code.md](02-complete-schema-and-backend-code.md)
- [04-complete-swiftui-views.md](04-complete-swiftui-views.md)
- [../client-sdk/01-client-surface-runtime-and-auth-bridge.md](../client-sdk/01-client-surface-runtime-and-auth-bridge.md)
- [../client-sdk/02-type-system-wire-format-and-modeling.md](../client-sdk/02-type-system-wire-format-and-modeling.md)
