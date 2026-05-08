# Encoding Arguments: ConvexEncodable

## Use This When
- Passing arguments to `client.mutation(...)` or `client.action(...)` from Swift.
- Working with optional, nested, or array arguments in Convex calls.
- Understanding how Swift types map to Convex wire format.

## Built-in Conformances

| Swift Type | Sends As | Example |
|---|---|---|
| `String` | JSON string | `"name": "Alice"` |
| `Int`, `Int32`, `Int64` | Tagged integer `{"$integer": "..."}` | `"count": 5` |
| `Double`, `Float` | JSON number (or tagged for NaN/Inf) | `"score": 3.14` |
| `Bool` | JSON boolean | `"active": true` |
| `nil` (optional) | JSON null | `"bio": nil` |
| `[ConvexEncodable?]` | JSON array | `"tags": ["a", "b"] as [ConvexEncodable?]` |
| `[String: ConvexEncodable?]` | JSON object | `"address": ["city": "Istanbul"] as [String: ConvexEncodable?]` |

## Examples

```swift
// Simple arguments
try await client.mutation("messages:send", with: [
    "body": "Hello world",
    "channelId": selectedChannelId,
])

// No arguments
try await client.mutation("queue:clear")

// Nil argument (sends null)
try await client.mutation("profile:update", with: ["bio": nil])

// Nested dictionary
try await client.mutation("profile:update", with: [
    "address": [
        "street": "123 Main St",
        "city": "Springfield",
    ] as [String: ConvexEncodable?],
])

// Array
try await client.mutation("posts:tag", with: [
    "tags": ["swift", "ios"] as [ConvexEncodable?],
])

// Integer (auto-encoded as tagged)
try await client.mutation("counter:increment", with: ["amount": 5])
```

## Key Rules
1. All mutation and action arguments are `[String: ConvexEncodable?]` dictionaries.
2. Dictionary keys are sorted alphabetically during encoding; deterministic but irrelevant for correctness.
3. Custom structs do not conform to `ConvexEncodable`; build the dictionary manually at the call site.
4. Swift `Int` is encoded as the Convex tagged integer format automatically.
5. Nested `nil` encodes as JSON `null`.

## Avoid
- Trying to pass a custom `Encodable` struct directly as an argument; there is no automatic bridge from `Encodable` to `ConvexEncodable`.
- Forgetting the `as [String: ConvexEncodable?]` cast on nested dictionaries; Swift cannot infer the type without it.
- Forgetting the `as [ConvexEncodable?]` cast on array arguments.
- Using a variable named `convex` instead of `client` for the Convex client instance.

## Read Next
- [02-type-system-wire-format-and-modeling.md](02-type-system-wire-format-and-modeling.md)
- [01-client-surface-runtime-and-auth-bridge.md](01-client-surface-runtime-and-auth-bridge.md)
- [04-pipeline-termination-and-recovery.md](04-pipeline-termination-and-recovery.md)
