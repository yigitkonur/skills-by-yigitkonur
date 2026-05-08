# Type System, Wire Format, And Modeling

## Use This When
- Decoding Convex values into Swift models.
- Explaining numeric wrappers, `CodingKeys`, or mutation argument encoding.
- Preventing subtle runtime decode failures.

## Core Rule
- Convex numeric wire formats do not map cleanly onto naive `JSONDecoder` assumptions for all cases.
- Use the provided wrappers for tagged numeric types instead of assuming plain `Int` or `Double` will decode safely.
- Treat model decoding as part of the contract between backend schema and Swift types.

## Required Modeling Patterns

### Document ID Mapping
Map `_id` to `id` through `CodingKeys` when using `Identifiable` in SwiftUI.

### Numeric Wrappers
- Use `@ConvexInt` for required integer fields that arrive through Convex's tagged Int64 format.
- Use `@OptionalConvexInt` for optional integer fields (the wrapper handles `nil` → `Optional<Int>.none`).
- Use the float wrappers when the wire shape requires them.

```swift
@ConvexInt var viewCount: Int      // required v.int64()
@OptionalConvexInt var score: Int? // optional v.int64()
```

### Concrete Example (From Official WorkoutTracker)

```swift
import ConvexMobile

struct Workout: Identifiable, Equatable, Decodable {
  let id: String
  let _date: String
  let activity: Activity
  @OptionalConvexInt
  var duration: Int?

  enum CodingKeys: String, CodingKey {
    case id = "_id"       // Convex document ID → Identifiable.id
    case _date = "date"   // rename to avoid clash with computed property
    case activity
    case duration
  }
}

private var dateFormatter: ISO8601DateFormatter {
  let dateFormatter = ISO8601DateFormatter()
  dateFormatter.formatOptions = [.withFullDate]
  dateFormatter.timeZone = TimeZone(abbreviation: "UTC")
  return dateFormatter
}

extension Workout {
  var date: Date {
    dateFormatter.date(from: self._date)!
  }
}

enum Activity: String, Identifiable, CaseIterable, Codable {
  var id: Self { self }
  case running = "Running"
  case lifting = "Lifting"
  case walking = "Walking"
  case swimming = "Swimming"
}
```

Key points:
- `Identifiable` + `Equatable` + `Decodable` is the minimum for SwiftUI lists with Combine `.removeDuplicates()`.
- `@OptionalConvexInt` handles Convex's Int64 wire format for optional integers.
- Use `CodingKeys` to rename `_id` -> `id` and any fields that clash with Swift computed properties.
- For date-only strings like `"YYYY-MM-DD"`, use `.withFullDate` and an explicit timezone just like the sample; a bare `ISO8601DateFormatter().date(from:)` is not a safe substitute here.
- Match `Activity` raw values to the backend mutation validator's allowed string literals, not just the table schema field type.

## Encoding Rules

### Mutation Arguments

Mutation and action args are built as `[String: ConvexEncodable]` dictionaries:

```swift
// Required fields
var args: [String: ConvexEncodable] = [
  "date": date.localIso8601DateFormat(),
  "activity": activity.rawValue,
]

// Optional fields — add conditionally
if let duration {
  args["duration"] = duration
}

try await client.mutation("workouts:store", with: args)
```

- Arrays and nested dictionaries can be encoded recursively when their contents conform.
- `nil` values should be omitted from the dictionary rather than encoded as explicit null for optional fields.
- For document ID arguments, use `v.id("tableName")` on the backend and pass the raw string from the Swift model.

## Practical Safety Rules
- Keep backend field naming stable and explicit.
- Prefer small backend response shapes that Swift can decode predictably.
- When a decode error matters to UX, surface it instead of swallowing it into an empty fallback.
- Treat type modeling as a first-class part of review for both Swift and TypeScript changes.

## Avoid
- Raw `Int`/`Double` decoding for values that the corpus says need wrappers.
- Letting `_id` leak through your UI model layer unchanged when `id` is the ergonomic shape.
- Assuming optionality or missing fields will behave the same on both sides without explicit modeling.
- Including optional fields with `nil` values in mutation argument dictionaries — omit them instead.

## Read Next
- [01-client-surface-runtime-and-auth-bridge.md](01-client-surface-runtime-and-auth-bridge.md)
- [03-subscriptions-errors-logging-and-connection-state.md](03-subscriptions-errors-logging-and-connection-state.md)
