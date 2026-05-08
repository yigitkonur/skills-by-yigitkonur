# Swift SDK API Cheat Sheet

## Use This When
- Need a fast lookup for `ConvexClient` or `ConvexClientWithAuth` API signatures.
- Writing subscription, mutation, or action calls in Swift.
- Checking argument encoding, model decoding, or logging rules.

---

## ConvexClient (No Auth)

```swift
import ConvexMobile

let client = ConvexClient(deploymentUrl: "https://slug.convex.cloud")
```

### subscribe(to:with:yielding:)

```swift
func subscribe<T: Decodable>(
    to name: String,
    with args: [String: ConvexEncodable?]? = nil,
    yielding output: T.Type? = nil
) -> AnyPublisher<T, ClientError>
```

Returns a Combine publisher that emits every time the server-side query result changes. The subscription stays alive as long as the `AnyCancellable` is retained.

```swift
client.subscribe(
    to: "messages:list",
    with: ["channelId": channelId],
    yielding: [Message].self
)
.receive(on: DispatchQueue.main)    // REQUIRED -- always main queue
.sink(
    receiveCompletion: { completion in
        if case .failure(let error) = completion {
            print("Subscription error: \(error)")
        }
    },
    receiveValue: { messages in
        self.messages = messages
    }
)
.store(in: &cancellables)
```

### mutation(_:with:)

```swift
func mutation<T: Decodable>(
    _ name: String,
    with args: [String: ConvexEncodable?]
) async throws -> T
```

Calls a Convex mutation. Returns the mutation's return value. Throws on error.

```swift
let messageId: String = try await client.mutation(
    "messages:send",
    with: [
        "channelId": channelId,
        "body": "Hello!"
    ]
)

// For mutations that return void:
try await client.mutation("messages:markRead", with: [...]) as Void
```

### action(_:with:)

```swift
func action<T: Decodable>(
    _ name: String,
    with args: [String: ConvexEncodable?]
) async throws -> T
```

Calls a Convex action. Same signature as mutation. Use for functions that call external APIs or perform non-deterministic work.

```swift
let result: UploadResult = try await client.action(
    "files:generateUploadUrl",
    with: [:]
)
```

### watchWebSocketState()

```swift
func watchWebSocketState() -> AnyPublisher<WebSocketState, Never>
```

Emits the current WebSocket connection state. Never fails (publishes `Never`). Only two states: `.connected` and `.connecting`.

```swift
client.watchWebSocketState()
    .receive(on: DispatchQueue.main)
    .sink { state in
        // state: .connected | .connecting  (only two states exist)
        self.isConnected = state == .connected
    }
    .store(in: &cancellables)
```

---

## ConvexClientWithAuth (with Clerk)

```swift
import ClerkConvex
import ClerkKit
import ConvexMobile

Clerk.configure(publishableKey: "pk_test_xxx")

@MainActor
let client = ConvexClientWithAuth(
    deploymentUrl: "https://slug.convex.cloud",
    authProvider: ClerkConvexAuthProvider()
)
// bind() starts automatic session sync -- no manual login() calls needed
```

Inherits all methods from `ConvexClient` plus:

### authState

```swift
var authState: AnyPublisher<AuthState<String>, Never>
```

Backed by `CurrentValueSubject` -- new subscribers get last-known state immediately.

```swift
// Observe in a view:
.task {
    for await state in client.authState.values {
        authState = state  // .loading, .unauthenticated, or .authenticated
    }
}
```

### login() / loginFromCache() / logout()

```swift
func login() async -> Result<T, Error>
func loginFromCache() async -> Result<T, Error>
func logout() async
```

**With `ClerkConvexAuthProvider`:** You do NOT call these manually. The `bind()` mechanism listens to `Clerk.shared.auth.events` and calls them automatically on session changes. There is no need to call `loginFromCache()` at app launch or `login()` on sign-in -- the auth provider handles the full lifecycle.

**With a custom auth provider:** Call `loginFromCache()` at app launch; `login()` when user initiates sign-in.

---

## Argument Types -- `ConvexEncodable`

Arguments to `mutation()`, `action()`, and `subscribe()` are `[String: ConvexEncodable?]`:

```swift
// String, Int, Bool, nil all conform to ConvexEncodable
try await client.mutation("messages:send", with: [
    "body": "Hello",        // String
    "count": 5,             // Int (auto-encoded as tagged integer)
    "active": true,         // Bool
    "bio": nil,             // null
])

// Arrays and nested dicts
try await client.mutation("posts:tag", with: [
    "tags": ["swift", "ios"] as [ConvexEncodable?],
    "address": ["city": "Istanbul"] as [String: ConvexEncodable?],
])
```

For decoding `v.int64()` fields, use `@ConvexInt var x: Int` (or `@OptionalConvexInt var x: Int?`).

---

## initConvexLogging()

```swift
func initConvexLogging()
```

Routes Rust-level SDK logs to `os_log`. Filter in Console.app by `subsystem:dev.convex.ConvexMobile`.

```swift
#if DEBUG
initConvexLogging()   // NEVER in production -- exposes JWTs
#endif
```

---

## Decodable Model Rules

Every model **must** include `CodingKeys` with `case id = "_id"`:

```swift
struct Message: Decodable, Identifiable {
    let id: String
    let body: String
    let creationTime: Double

    enum CodingKeys: String, CodingKey {
        case id = "_id"              // MANDATORY
        case body
        case creationTime = "_creationTime"
    }
}
```

---

## Pipeline Termination Warning

> **WARNING:** `.replaceError(with:)` terminates the publisher permanently after the first error. The subscription will never emit again. **All `.catch` variants also terminate the upstream -- none of them keep the pipeline alive.** To handle errors in production, use one of:
>
> 1. `sink(receiveCompletion:receiveValue:)` — set an error state in `receiveCompletion`, then call `resubscribe()` (cancel all cancellables and rebuild the pipeline) to resume live updates.
> 2. Result-wrapping (`.asResult()`) — the error is visible as UI state, but the pipeline still completes. Call `resubscribe()` to resume live updates.
>
> See [../pitfalls/01-pipeline-dies-after-first-error.md](../pitfalls/01-pipeline-dies-after-first-error.md).

---

## Quick Patterns

```swift
// Subscribe + update @Published
client.subscribe(to: "fn:name", with: [:], yielding: [T].self)
    .receive(on: DispatchQueue.main)
    .sink(receiveCompletion: { _ in }, receiveValue: { self.items = $0 })
    .store(in: &cancellables)

// Fire-and-forget mutation
Task { try? await client.mutation("fn:name", with: [...]) as Void }

// Await mutation result
let id: String = try await client.mutation("fn:name", with: [...])

// Check connection
client.watchWebSocketState()
    .receive(on: DispatchQueue.main)
    .map { $0 == .connected }
    .sink { self.isOnline = $0 }
    .store(in: &cancellables)
```

## Avoid
- Naming the client variable `convex` -- use `client` to match official examples.
- Calling `loginFromCache()` or `login()` manually when using `ClerkConvexAuthProvider`.
- Omitting `.receive(on: DispatchQueue.main)` on subscription pipelines -- causes purple runtime warnings.
- Using `.replaceError(with:)` in production -- it silently kills the subscription on first error.
- Forgetting `CodingKeys` with `case id = "_id"` on Decodable models.
- Using `initConvexLogging()` without `#if DEBUG` -- exposes JWTs and user data.

## Read Next
- [01-convex-backend-quick-reference-card.md](01-convex-backend-quick-reference-card.md)
- [03-sql-to-convex-mapping-table.md](03-sql-to-convex-mapping-table.md)
- [../client-sdk/01-client-surface-runtime-and-auth-bridge.md](../client-sdk/01-client-surface-runtime-and-auth-bridge.md)
- [../client-sdk/02-type-system-wire-format-and-modeling.md](../client-sdk/02-type-system-wire-format-and-modeling.md)
