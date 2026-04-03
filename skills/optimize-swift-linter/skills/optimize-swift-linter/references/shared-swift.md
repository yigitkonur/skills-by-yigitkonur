# Shared Swift Best Practices

Opinionated guide for Swift 6 targeting both macOS and iOS. One right way per pattern.

---

## 1. Naming Conventions

Follow Apple's API Design Guidelines without compromise.

- **Types/protocols:** `UpperCamelCase` — `UserProfile`, `DataFetching`
- **Variables/functions:** `lowerCamelCase` — `fetchUser()`, `isLoading`
- **Booleans:** prefix with `is`, `has`, `should`, `can` — `isAuthenticated`
- **Protocol capability suffix:** `-able`/`-ible` only for capabilities — `Codable`, `Sendable`; use noun-based names for semantic roles — `DataSource`, `Delegate`
- **Abbreviations:** only universally accepted ones — `URL`, `ID`, `HTTP`; spell out everything else — `userId` not `uid`

```swift
// Correct
protocol ImageCaching { func store(_ image: Image, forKey key: String) }
struct UserProfileViewModel { var isLoading: Bool }
func fetchUsers(matching query: String) async throws -> [User]

// Wrong: abbreviations, vague names, wrong case
protocol imgCache { func storeImg(_ img: Image, key: String) }
struct VM { var loading: Bool }
func get(_ q: String) async throws -> [User]
```

---

## 2. Value Types vs Reference Types

Default to `struct`. Use `class` only when you need identity, inheritance, or ObjC interop.

```swift
// Struct: pure data, no shared state
struct Point { var x: Double; var y: Double }

// Class: identity matters, shared mutable state managed explicitly
final class ImageCache {
    private var storage: [String: Image] = [:]
    func store(_ image: Image, forKey key: String) { storage[key] = image }
}
```

Copy-on-write for large custom structs — only implement when profiling proves it necessary:

```swift
final class Storage<T> { var value: T; init(_ value: T) { self.value = value } }
struct LargeBuffer {
    private var _storage: Storage<[UInt8]>
    mutating func append(_ byte: UInt8) {
        if !isKnownUniquelyReferenced(&_storage) { _storage = Storage(_storage.value) }
        _storage.value.append(byte)
    }
}
```

---

## 3. Swift Concurrency

Use `async`/`await` throughout. Never use completion handlers in new code.

```swift
// Structured concurrency with TaskGroup
func fetchAll(ids: [String]) async throws -> [User] {
    try await withThrowingTaskGroup(of: User.self) { group in
        for id in ids { group.addTask { try await fetchUser(id: id) }  }
        return try await group.reduce(into: []) { $0.append($1) }
    }
}

// Bridge from completion handler once at the boundary
func legacyFetch(id: String) async throws -> User {
    try await withCheckedThrowingContinuation { continuation in
        oldAPI.fetch(id: id) { result in continuation.resume(with: result) }
    }
}

// Actor for shared mutable state — eliminates data races
actor RequestQueue {
    private var pending: [URLRequest] = []
    func enqueue(_ request: URLRequest) { pending.append(request) }
    func next() -> URLRequest? { pending.isEmpty ? nil : pending.removeFirst() }
}

// MainActor for UI updates
@MainActor
final class ViewModel: ObservableObject {
    var items: [Item] = []
    func load() async throws {
        let fetched = try await service.fetch()   // suspends off main thread
        items = fetched                           // resumes on MainActor
    }
}
```

**Pitfalls:** After every `await` inside an actor, recheck state — another task may have mutated it. Mark closures `@Sendable` when crossing actor boundaries.

---

## 4. Error Handling

Use typed throws (Swift 6) for domain errors. Reserve `Result` for storing/passing errors as values.

```swift
enum NetworkError: Error {
    case noConnection
    case httpError(statusCode: Int)
    case decodingFailed(underlying: Error)
}

// Typed throws: compiler guarantees exhaustive catch
func fetchData(from url: URL) throws(NetworkError) -> Data {
    guard isConnected else { throw .noConnection }
    // ...
}

// Call site: no need to cast `error`
do {
    let data = try fetchData(from: url)
} catch .noConnection {
    showOfflineBanner()
} catch .httpError(let code) where code == 401 {
    promptLogin()
} catch let error {
    log(error)
}

// Result only for async pipelines or deferred error delivery
func cachedFetch(url: URL) -> Result<Data, NetworkError> { .success(data) }
```

---

## 5. Protocol-Oriented Design

Use protocols for abstraction at boundaries (testability, DI). Do not protocol-wrap every type.

```swift
protocol Persistence {
    func save<T: Codable>(_ value: T, forKey key: String) throws
    func load<T: Codable>(forKey key: String) throws -> T
}

// Default implementation via extension — no inheritance needed
extension Persistence {
    func saveIfPresent<T: Codable>(_ value: T?, forKey key: String) throws {
        guard let value else { return }
        try save(value, forKey: key)
    }
}

// Composition over inheritance
typealias Repository = Persistence & Queryable
```

When the type is always concrete and not tested in isolation, skip the protocol.

---

## 6. Optionals

Use `guard let` for early-exit unwrapping. Use `if let` only inside blocks where you need the unwrapped value.

```swift
func process(input: String?) -> String {
    guard let input else { return "" }          // early exit
    guard !input.isEmpty else { return "" }
    return input.trimmingCharacters(in: .whitespaces)
}

// Nil-coalescing for defaults
let name = user.displayName ?? user.email ?? "Anonymous"

// Optional chaining for reads
let count = cart?.items.count

// Force-unwrap: only for IBOutlets and test assertions
@IBOutlet private var titleLabel: UILabel!
XCTAssertEqual(result!, expected)
```

Never chain more than two `??` operators or three `?.` accesses in one expression — extract to a variable.

---

## 7. Enums with Associated Values

Encode state as enums to make illegal states unrepresentable.

```swift
enum LoadState<T> {
    case idle
    case loading
    case loaded(T)
    case failed(Error)
}

// State machine: transitions are exhaustive
extension LoadState {
    var value: T? { if case .loaded(let v) = self { return v } else { return nil } }
    var isLoading: Bool { if case .loading = self { return true } else { return false } }
}

// Codable enum with associated values (Swift 5.5+)
enum Shape: Codable {
    case circle(radius: Double)
    case rectangle(width: Double, height: Double)
}

// CaseIterable for simple enums without associated values
enum Tab: String, CaseIterable { case home, search, profile }
```

---

## 8. Generics & Type Erasure

Use generics for compile-time polymorphism. Use `any` only when storing heterogeneous values.

```swift
// Generic function — single concrete type per call, zero boxing
func first<C: Collection>(_ collection: C) -> C.Element? { collection.first }

// Opaque return type — caller gets concrete type, implementation stays flexible
func makeParser() -> some Parser { JSONParser() }

// any — existential, needed for heterogeneous collections
var shapes: [any Drawable] = [Circle(), Rectangle()]

// Type erasure pattern for pre-iOS17 / when `any` performance matters
struct AnyRepository<T>: Repository {
    private let _save: (T) throws -> Void
    init<R: Repository>(_ base: R) where R.Item == T { _save = base.save }
}
```

Default to `some`. Switch to `any` only when you need a heterogeneous collection or dynamic dispatch.

---

## 9. Property Wrappers

Use framework wrappers for their intended scope. Create custom wrappers only when the same projection logic recurs 3+ times.

```swift
@Observable   // iOS 17+/macOS 14+ — replaces ObservableObject
final class AppState {
    var currentUser: User?
    var theme: Theme = .system
}

// In SwiftUI views — no @ObservedObject, just hold reference
struct ProfileView: View {
    var state: AppState          // passed in, tracked automatically
    @Bindable var state: AppState // when you need $state.theme binding
}

// Custom thread-safe property wrapper
@propertyWrapper
struct Locked<T> {
    private var _value: T
    private let lock = NSLock()
    init(wrappedValue: T) { _value = wrappedValue }
    var wrappedValue: T {
        get { lock.withLock { _value } }
        set { lock.withLock { _value = newValue } }
    }
}
```

---

## 10. Access Control

Default to `private`. Widen only when proven necessary. Use the strictest level possible.

```swift
// internal  — default, same module (omit the keyword — never write it explicitly)
// private   — declaration scope only
// fileprivate — file only (rare: use when an extension in the same file needs access)
// package   — Swift 5.9+, same SwiftPM package
// public    — external module, cannot subclass/override
// open      — external module, can subclass/override (explicit opt-in to subclassing)

final class UserStore {
    private var cache: [String: User] = [:]   // never leaks
    package func prefetch(ids: [String]) { }  // visible in same package
    public var count: Int { cache.count }
}
```

Mark everything `final` by default. Remove `final` only when inheritance is intentional.

```swift
// WRONG — class without final
public class SpacecraftEngine { }

// RIGHT — final by default
public final class SpacecraftEngine { }

// ALSO RIGHT — open explicitly signals subclassing intent
open class SpacecraftEngine { }
```

**Omit `internal`** — it is the default and repeating it is noise.

```swift
// WRONG
internal class Spaceship {
    internal func travel(to planet: Planet) { }
}

// RIGHT
class Spaceship {
    func travel(to planet: Planet) { }
}
```

**Specify access per-declaration in extensions**, not on the extension itself. This makes the access level immediately visible even when the extension declaration is off-screen.

```swift
// WRONG
public extension Universe {
    func generateGalaxy() { }   // accidentally public, not obvious at call site
}

private extension Spaceship {
    func enableHyperdrive() { }
}

// RIGHT
extension Universe {
    public func generateGalaxy() { }
}

extension Spaceship {
    fileprivate func enableHyperdrive() { }  // private extension = fileprivate semantics
}
```

---

## 11. Memory Management

Capture `[weak self]` in escaping closures. **Avoid `unowned`** — it crashes if the referenced object has been deallocated. Prefer `[weak self]` with an explicit nil-check, or capture the specific value directly instead of capturing `self`.

```swift
// WRONG — unowned crashes on deallocation
service.fetch { [unowned self] result in
    handleResult(result)
}

// RIGHT — weak capture with guard
networkService.fetch(url: url) { [weak self] result in
    guard let self else { return }
    handleResult(result)
}

// ALSO RIGHT — direct capture avoids self entirely
let url = self.url
networkService.fetch(url: url) { [url] result in
    log(url, result)
}
```

When upgrading from a weak reference, bind back to `self` — not to a renamed variable like `strongSelf`.

```swift
// WRONG
API.request { [weak self] response in
    guard let strongSelf = self else { return }
    strongSelf.handleResponse(response)
}

// RIGHT
API.request { [weak self] response in
    guard let self else { return }
    handleResponse(response)
}
```

// Combine / async — Task holds strong ref, so cancel in deinit
final class ViewModel {
    private var tasks: [Task<Void, Never>] = []

    func load() {
        tasks.append(Task { [weak self] in
            guard let self else { return }
            await self.fetchData()
        })
    }

    deinit { tasks.forEach { $0.cancel() } }
}

// Retain cycle detection: make cycle-prone types final class + check in Instruments
```

---

## 12. Codable & Serialization

Use `CodingKeys` enum whenever JSON keys differ from Swift names. Avoid custom `encode`/`decode` unless truly necessary.

```swift
struct Article: Codable {
    var id: Int
    var publishedAt: Date
    var authorName: String

    enum CodingKeys: String, CodingKey {
        case id
        case publishedAt = "published_at"
        case authorName  = "author_name"
    }
}

let decoder = JSONDecoder()
decoder.dateDecodingStrategy = .iso8601
decoder.keyDecodingStrategy = .convertFromSnakeCase  // replaces manual CodingKeys for snake_case

// Nested container for unwrapping envelope { "data": { ... } }
init(from decoder: Decoder) throws {
    let root = try decoder.container(keyedBy: RootKeys.self)
    let nested = try root.nestedContainer(keyedBy: CodingKeys.self, forKey: .data)
    id = try nested.decode(Int.self, forKey: .id)
}
```

---

## 13. Collections & Algorithms

Prefer `map`/`compactMap`/`filter`/`reduce` over mutable accumulation loops. Mutable variables increase complexity — keep them in the narrowest scope possible, or eliminate them entirely.

```swift
// WRONG — mutable accumulator with a loop
var results = [SomeType]()
for element in input {
    let result = transform(element)
    results.append(result)
}

// RIGHT — functional transform, immutable result
let results = input.map { transform($0) }

// WRONG — mutable accumulator with optional handling
var filtered = [SomeType]()
for element in input {
    if let result = transformThatReturnsOptional(element) {
        filtered.append(result)
    }
}

// RIGHT
let filtered = input.compactMap { transformThatReturnsOptional($0) }
```

```swift
// lazy — only compute elements actually consumed
let firstFive = (1...).lazy.filter { $0.isMultiple(of: 3) }.prefix(5)

// Swift Algorithms package
import Algorithms
let batches = users.chunks(ofCount: 20)        // paginate
let unique  = users.uniqued(on: \.email)       // deduplicate stably
let pairs   = zip(keys, values).map(KeyValue.init)
```

**Prefer immutable static properties.** `static var` is global mutable state; use `static let` or a computed `static var` instead.

```swift
// WRONG — global mutable state
enum Fonts {
    static var title = UIFont(name: "Helvetica", size: 17)!
}

// RIGHT — immutable
enum Fonts {
    static let title = UIFont(name: "Helvetica", size: 17)!
}

// RIGHT — computed (for types where a fresh value is needed each time)
struct FeatureState {
    var count: Int
    static var initial: FeatureState { FeatureState(count: 0) }
}
```

---

## 14. String Handling

Use `String(localized:)` for all user-visible strings. Use regex builders for pattern matching.

```swift
// Localization — compile-time key checking in Xcode 15+
let message = String(localized: "welcome.title", defaultValue: "Welcome back!")

// AttributedString for styled text (no NSAttributedString in new code)
var title = AttributedString("Hello, \(name)")
title[title.startIndex...].font = .headline

// Regex builder — type-safe, readable
import RegexBuilder
let version = Regex {
    Capture(OneOrMore(.digit))
    "."
    Capture(OneOrMore(.digit))
}
if let match = versionString.firstMatch(of: version) {
    let (_, major, minor) = match.output
}
```

---

## 15. SwiftUI Shared Patterns

Use `@Observable` + `@Bindable`. Pass environment values through `Environment`, not singletons.

```swift
@Observable
final class Router {
    var path = NavigationPath()
    func push(_ destination: AppDestination) { path.append(destination) }
}

struct RootView: View {
    @State private var router = Router()   // owns the instance

    var body: some View {
        NavigationStack(path: $router.path) {
            HomeView()
                .environment(router)       // inject, not singleton
        }
    }
}

struct HomeView: View {
    @Environment(Router.self) private var router
    @Bindable var router: Router           // when you need two-way binding

    var body: some View {
        Button("Go") { router.push(.detail(id: "1")) }
    }
}

// ViewModifier for reusable presentation logic
struct CardStyle: ViewModifier {
    func body(content: Content) -> some View {
        content.padding().background(.regularMaterial).clipShape(RoundedRectangle(cornerRadius: 12))
    }
}
extension View {
    func cardStyle() -> some View { modifier(CardStyle()) }
}

---

## 16. Type Inference

Don't include types where they can be easily inferred from the right-hand side. Let the compiler do the work.

```swift
// WRONG — type repeated on both sides
let sun: Star = Star(mass: 1.989e30)
let earth: Planet = Planet.earth
let enableGravity: Bool = true
let numberOfPlanets: Int = 8

// RIGHT
let sun = Star(mass: 1.989e30)
let earth = Planet.earth
let enableGravity = true
let numberOfPlanets = 8
```

When the RHS is a static member with a leading dot (an `init`, `static` property, or enum case), prefer the inferred form — move the type to the right.

```swift
// WRONG
struct SolarSystemBuilder {
    let sun: Star = .init(mass: 1.989e30)
    let earth: Planet = .earth
}

// RIGHT
struct SolarSystemBuilder {
    let sun = Star(mass: 1.989e30)
    let earth = Planet.earth
}
```

Explicit types are still required when there is no RHS, when you need to widen the type, or when the inferred form would change semantics (e.g. `String?` vs. `String`).

```swift
// RIGHT — no RHS
let sun: Star

// RIGHT — narrowing/widening required
let moonsMass: Float = 1.989e30
let planets: [Planet] = []
let optional: String? = nil
```

---

## 17. Self Usage

Don't use `self` unless it's required for disambiguation (e.g., shadowing in an initializer) or mandated by the language (e.g., closures, `mutating` context). Redundant `self.` prefixes add noise without adding clarity.

```swift
final class Listing {

    init(capacity: Int, allowsPets: Bool) {
        self.capacity = capacity          // required: shadows parameter name
        isFamilyFriendly = !allowsPets    // NOT required — omit self
    }

    private let isFamilyFriendly: Bool
    private var capacity: Int

    private func increaseCapacity(by amount: Int) {
        capacity += amount  // NOT self.capacity
        save()              // NOT self.save()
    }
}
```

---

## 18. Trailing Commas

Add a trailing comma after the last element of multi-line, multi-element comma-separated lists (arrays, dictionaries, function declarations, function calls). Omit the trailing comma for single-element lists.

```swift
// WRONG — multi-element list, missing trailing comma
let terrestrialPlanets = [
    mercury,
    venus,
    earth,
    mars
]

func buildSolarSystem(
    innerPlanets: [Planet],
    outerPlanets: [Planet]
) { }

// RIGHT
let terrestrialPlanets = [
    mercury,
    venus,
    earth,
    mars,
]

func buildSolarSystem(
    innerPlanets: [Planet],
    outerPlanets: [Planet],
) { }
```

```swift
// WRONG — single-element list must NOT have trailing comma
let planetsWithLife = [
    earth,
]

// RIGHT
let planetsWithLife = [
    earth
]
```

---

## 19. Pattern Matching

Place `let` inline, adjacent to each bound variable when destructuring enum cases or tuples. Do not hoist a single `let` before the entire pattern.

```swift
// WRONG — hoisted let obscures which identifiers are new bindings
switch result {
case let .success(value):
    use(value)
case let .error(code, reason):
    log(code, reason)
}

// RIGHT — inline let, immediately adjacent to each binding
switch result {
case .success(let value):
    use(value)
case .error(let code, let reason):
    log(code, reason)
}

// RIGHT — same rule applies in guard
guard case .success(let value) = result else { return }
```

---

## 20. Attributes Placement

**Functions, types, and computed properties:** place attributes on the line above the declaration.

```swift
// WRONG
@objc class Spaceship {
    @ViewBuilder var controlPanel: some View { ... }
    @discardableResult func fly() -> Bool { ... }
}

// RIGHT
@objc
class Spaceship {
    @ViewBuilder
    var controlPanel: some View { ... }

    @discardableResult
    func fly() -> Bool { ... }
}
```

**Simple stored property attributes:** place on the same line as the declaration. This keeps related properties visually grouped.

```swift
// WRONG — wastes vertical space, makes grouping harder
@State
private var warpDriveEnabled: Bool
@State
private var lifeSupportEnabled: Bool

// RIGHT
@State private var warpDriveEnabled: Bool
@State private var lifeSupportEnabled: Bool
@Environment(\.controlPanelStyle) private var controlPanelStyle
```

**Complex attributes** (named arguments, or more than one unnamed argument) go on the previous line even for stored properties.

```swift
// WRONG
@available(*, deprecated, message: "To be retired by 2030") var legacyEngine: Engine

// RIGHT
@available(*, deprecated, message: "To be retired by 2030")
var legacyEngine: Engine

@Query(sort: \.distance)
var allPlanets: [Planet]
```

---

## 21. Conditional Assignment

Use `if`/`switch` expressions to initialize a new property rather than declaring an uninitialized `var` and assigning on every branch. This eliminates unnecessary type annotations, prevents accidental `var` when `let` suffices, and removes repetitive property-name noise.

```swift
// WRONG — uninitialized var, explicit type required, name repeated on every branch
var planetLocation: String
if let star = planet.star {
    planetLocation = "The \(star.name) system"
} else {
    planetLocation = "Rogue planet"
}

// RIGHT — single expression, type inferred, let possible
let planetLocation =
    if let star = planet.star {
        "The \(star.name) system"
    } else {
        "Rogue planet"
    }

// RIGHT — switch expression
let planetType: PlanetType =
    switch planet {
    case .mercury, .venus, .earth, .mars:
        .terrestrial
    case .jupiter, .saturn, .uranus, .neptune:
        .gasGiant
    }
```

For multi-line `if`/`switch` expressions, break after the `=` and indent the expression body. A line break is not required when the whole declaration fits on one line.

```swift
// ALSO RIGHT — fits on one line
let moonName = if let moon = planet.moon { moon.name } else { "none" }
```

---

## 22. Closures

**`Void` in type signatures:** use `Void` not `()` when declaring a closure's return type or a function parameter that takes a void-returning closure.

```swift
// WRONG
func register(completion: () -> ()) { }

// RIGHT
func register(completion: () -> Void) { }
```

**Omit `Void` from inline closure expressions** — the compiler infers it.

```swift
// WRONG
someAsyncThing() { argument -> Void in
    use(argument)
}

// RIGHT
someAsyncThing() { argument in
    use(argument)
}
```

**Name unused closure parameters as `_`** to signal clearly that they are intentionally ignored.

```swift
// WRONG — reader must figure out which params are unused
completion { value1, value2, value3 in
    process(value3)
}

// RIGHT
completion { _, _, value3 in
    process(value3)
}
```

**Avoid `unowned` captures** — see section 11.

---

## 23. Namespaces

Use caseless `enum`s to organize related public or internal constants and functions into namespaces. Caseless enums cannot be instantiated, which matches their intent perfectly.

```swift
// WRONG — struct can be instantiated accidentally
struct Environment {
    static let earthGravity = 9.8
    static let moonGravity = 1.6
}

// RIGHT — caseless enum cannot be instantiated
enum Environment {
    enum Earth {
        static let gravity = 9.8
    }
    enum Moon {
        static let gravity = 1.6
    }
}

// Usage
let g = Environment.Earth.gravity
```

`private` globals are permitted without a namespace wrapper since they are scoped to a single file and do not pollute the global namespace. Still consider wrapping them for consistency.

---

## 24. @unchecked Sendable

Avoid `@unchecked Sendable`. It suppresses the compiler's concurrency checks without providing any thread-safety guarantee. Prefer one of these safer alternatives:

**1. Use `Sendable` directly**, with `@MainActor` if the type needs to be mutable.

```swift
// WRONG — mutable class unsafely bypasses checks
final class Planet: @unchecked Sendable {
    var mass: Double   // not thread-safe, but compiler won't tell you
}

// RIGHT — immutable class is genuinely Sendable
final class Planet: Sendable {
    let mass: Double
}

// RIGHT — mutable class isolated to MainActor is thread-safe
@MainActor
final class Planet: Sendable {
    var mass: Double
}
```

**2. Use `@preconcurrency import`** when working with a type from a module that hasn't yet adopted Swift Concurrency.

```swift
// WRONG — unsafely marks a non-thread-safe external type as Sendable
import ThirdPartyKit
extension ThirdPartyModel: @unchecked Sendable { }

// RIGHT
@preconcurrency import ThirdPartyKit
```

**3. Restructure code** so the compiler can verify thread safety directly (e.g., replace subclassing with a protocol + `final` concrete type).

When `@unchecked Sendable` is truly unavoidable (e.g., a class whose mutable state is protected by a lock), add a comment explaining precisely why it is safe.
