# Swift Testing Reference

Opinionated guide to testing Swift apps. Prefer Swift Testing framework over XCTest for new code.

---

## 1. XCTest Fundamentals

Use XCTest for legacy codebases and when targeting pre-Swift-5.9 toolchains. For new code, prefer Swift Testing (§2).

```swift
final class UserServiceTests: XCTestCase {
    var sut: UserService!         // system under test
    var mockAPI: MockAPIClient!

    override func setUp() async throws {
        try await super.setUp()
        mockAPI = MockAPIClient()
        sut = UserService(api: mockAPI)
    }

    override func tearDown() async throws { sut = nil; mockAPI = nil; try await super.tearDown() }

    // Naming: test_methodName_condition_expectedResult
    func test_fetchUser_whenAPIFails_throwsNetworkError() async throws {
        mockAPI.stubbedError = NetworkError.noConnection
        await XCTAssertThrowsError(try await sut.fetchUser(id: "1"))
    }

    func test_fetchUser_whenAPISucceeds_returnsUser() async throws {
        mockAPI.stubbedUser = User(id: "1", name: "Alice")
        let user = try await sut.fetchUser(id: "1")
        XCTAssertEqual(user.name, "Alice")
    }
}
```

---

## 2. Swift Testing Framework (Preferred)

New in Swift 5.9 / Xcode 15. Richer diagnostics, parameterized tests, no subclassing.

```swift
import Testing

@Suite("UserService")
struct UserServiceTests {
    let sut: UserService
    let mockAPI: MockAPIClient

    init() {
        mockAPI = MockAPIClient()
        sut = UserService(api: mockAPI)
    }

    @Test("throws when API fails")
    func fetchUser_whenAPIFails_throwsError() async throws {
        mockAPI.stubbedError = NetworkError.noConnection
        await #expect(throws: NetworkError.self) {
            try await sut.fetchUser(id: "1")
        }
    }

    // #require stops the test on nil — use instead of XCTUnwrap
    @Test func fetchUser_returnsPopulatedUser() async throws {
        mockAPI.stubbedUser = User(id: "1", name: "Alice")
        let user = try await sut.fetchUser(id: "1")
        let name = try #require(user.name)
        #expect(name == "Alice")
    }

    // Parameterized — replaces copy-pasted test methods
    @Test("validates email", arguments: [
        ("alice@example.com", true),
        ("not-an-email",      false),
        ("",                  false),
    ])
    func validateEmail(input: String, expected: Bool) {
        #expect(sut.isValidEmail(input) == expected)
    }
}

// Tags for filtering runs
extension Tag { static let networking: Self = "networking" }

@Test(.tags(.networking))
func fetchUser_setsAuthorizationHeader() async throws { ... }
```

**XCTest vs Swift Testing:**

| | XCTest | Swift Testing |
|---|---|---|
| Assertion | `XCTAssertEqual` | `#expect(a == b)` |
| Fatal assertion | `XCTUnwrap` | `#require` |
| Parameterized | Manual | `@Test(arguments:)` |
| Parallel | Manual `async let` | Automatic per-test |
| Diagnostics | Single failure | Full expression tree |

---

## 3. Snapshot Testing

Use `pointfreeco/swift-snapshot-testing` for UI regression and data serialization tests.

```swift
// Package.swift dependency
.package(url: "https://github.com/pointfreeco/swift-snapshot-testing", from: "1.15.0")

import SnapshotTesting

final class ProfileViewTests: XCTestCase {
    func test_profileView_rendersCorrectly() {
        let view = ProfileView(user: .mock)
        // First run creates __Snapshots__/ reference image
        // Subsequent runs compare pixel-for-pixel
        assertSnapshot(of: view, as: .image(layout: .device(config: .iPhone13)))
    }

    // Text snapshot for data structures — fast, no image diffing
    func test_userDecoding_producesExpectedShape() {
        let user = try! JSONDecoder().decode(User.self, from: fixtureData)
        assertSnapshot(of: user, as: .dump)
    }

    // Custom strategy for any type
    func test_viewModel_state() {
        let vm = ProfileViewModel(user: .mock)
        assertSnapshot(of: vm, as: .json)   // .json, .plist, .lines available
    }
}
```

**CI configuration:** Set `SNAPSHOT_TESTING_RECORD=never` in CI env to prevent accidental baseline writes. Run `SNAPSHOT_TESTING_RECORD=all` locally to update baselines. Commit `__Snapshots__/` to version control.

---

## 4. Better Assertions with swift-custom-dump

Use `pointfreeco/swift-custom-dump` for structured diffs when values don't match.

```swift
import CustomDump

// XCTest drop-in with readable diffs
XCTAssertNoDifference(actual, expected)
// On failure prints:
//   UserProfile(
//  −   name: "Alice",
//  +   name: "Bob",
//     age: 30
//   )

// Swift Testing equivalent
expectNoDifference(actual, expected)

// For debugging in non-test code
customDump(complexValue)  // prints to stdout with indentation
```

Prefer `XCTAssertNoDifference` / `expectNoDifference` over `XCTAssertEqual` / `#expect(a == b)` whenever comparing structs or enums — the diff output makes failures immediately actionable.

---

## 5. Mock Generation

**Recommendation by project size:**

| Approach | Best For | Trade-off |
|---|---|---|
| `uber/mockolo` (CLI) | Large codebases, 50+ protocols | Fast generation, requires build step |
| `@Spyable` macro | Small-medium, compile-time | Simple API, call tracking only |
| `@Mockable` macro | Medium, full DSL | `given`/`verify` API, more setup |
| Manual mocks | Complex behavior, few mocks | Full control, maintenance burden |

### a. mockolo (CLI — preferred for large projects)

```bash
# Generate mocks for entire Sources directory
rtk mockolo --sourcedirs ./Sources --destination ./Tests/Mocks/GeneratedMocks.swift --testable-imports MyApp

# As SPM build tool plugin — add to test target in Package.swift
.testTarget(name: "AppTests", plugins: [.plugin(name: "MockoloPlugin")])
```

### b. @Spyable macro (compile-time, simple)

```swift
import Spyable

@Spyable
protocol APIClient {
    func fetchUser(id: String) async throws -> User
}

// Generated: APIClientSpy with call tracking
func test_loadsUser_onAppear() async throws {
    let spy = APIClientSpy()
    spy.fetchUserIdReturnValue = .mock
    let vm = ViewModel(api: spy)
    await vm.onAppear()
    #expect(spy.fetchUserIdCallsCount == 1)
    #expect(spy.fetchUserIdReceivedId == "42")
}
```

### c. @Mockable macro (compile-time, full DSL)

```swift
import Mockable

@Mockable
protocol UserRepository {
    func save(_ user: User) async throws
    func fetchAll() async throws -> [User]
}

func test_fetchAll_returnsUsers() async throws {
    let mock = MockUserRepository()
    given(mock).fetchAll().willReturn([.mock])
    let repo: UserRepository = mock
    let users = try await repo.fetchAll()
    verify(mock).fetchAll().called(.once)
}
```

### d. Manual mocks — when to prefer them

Use hand-written mocks when the protocol has stateful behavior (streams, event sequences), needs precise error injection order, or the generated mock would require heavy customization. For example, an `InMemoryUserRepository: UserRepository` that fully implements persistence using a dictionary is a fake and is usually clearer than any generated mock.

---

## 6. Dependency Injection for Testing

Use `pointfreeco/swift-dependencies` (`@Dependency`) for all injectable values.

```swift
import Dependencies

// Define dependency key
private enum APIClientKey: DependencyKey {
    static let liveValue: APIClient = LiveAPIClient()
    static let testValue: APIClient = MockAPIClient()    // auto-used in tests
    static let previewValue: APIClient = PreviewAPIClient()
}
extension DependencyValues {
    var apiClient: APIClient {
        get { self[APIClientKey.self] }; set { self[APIClientKey.self] = newValue }
    }
}

// Consume in production code
struct UserViewModel {
    @Dependency(\.apiClient) var apiClient
    @Dependency(\.continuousClock) var clock  // built-in: controllable time

    func load() async throws { ... }
}

// Override in tests — scoped, no global state mutation
func test_loadUsers_displaysNames() async throws {
    let vm = withDependencies {
        $0.apiClient = .mock(users: [.alice, .bob])
    } operation: {
        UserViewModel()
    }
    try await vm.load()
    #expect(vm.names == ["Alice", "Bob"])
}
```

`testValue` is picked up automatically in tests. Only override explicitly when a specific test needs different behavior.

---

## 7. Testing Architecture Patterns

### ViewModel (MVVM) — use `withDependencies` to inject mocks, check state before and after async call:

```swift
@Test func viewModel_onLoad_setsLoadedState() async throws {
    let vm = withDependencies { $0.apiClient = .mock(items: [.fixture]) } operation: { FeedViewModel() }
    await vm.load()
    guard case .loaded(let items) = vm.state else { Issue.record("Expected loaded"); return }
    #expect(!items.isEmpty)
}
```

### TCA Reducer

```swift
import ComposableArchitecture

@MainActor
func test_reducer_fetchUser_updatesState() async {
    let store = TestStore(initialState: ProfileFeature.State()) {
        ProfileFeature()
    } withDependencies: {
        $0.apiClient = .mock(user: .alice)
    }

    await store.send(.onAppear) { $0.isLoading = true }
    await store.receive(\.userResponse.success) {
        $0.isLoading = false
        $0.user = .alice
    }
}
```

### Testing Combine Publishers

Prefer `publisher.values` (AsyncSequence bridge) with `async/await` over `sink` + `XCTestExpectation`:

```swift
func test_publisher_emitsExpectedValues() async throws {
    let subject = PassthroughSubject<Int, Never>()
    let task = Task { subject.values.reduce(into: []) { $0.append($1) } }
    subject.send(1); subject.send(2); subject.send(completion: .finished)
    #expect(try await task.value == [1, 2])
}
```

---

## 8. UI Testing

Use XCUITest only for critical user flows (purchase funnels, auth, onboarding). It is slow, flaky, and expensive. Do not use for form validation, error states, or navigation logic — cover those with unit + snapshot tests.

Use the **Page Object pattern** to encapsulate element queries, and always set accessibility identifiers in code:

```swift
// In the view
Button("Checkout") { ... }.accessibilityIdentifier("checkout-button")

// In the test — Page Object wraps XCUIElement queries
struct CartPage {
    let app: XCUIApplication
    func tapCheckout() { app.buttons["checkout-button"].tap() }
}

final class CheckoutUITests: XCTestCase {
    func test_checkout_completesSuccessfully() {
        let app = XCUIApplication()
        app.launchArguments = ["--uitesting", "--reset-state"]
        app.launch()
        CartPage(app).tapCheckout()
        XCTAssert(app.staticTexts["order-confirmed"].waitForExistence(timeout: 5))
    }
}
```

---

## 9. Test Organization

```
Tests/
  AppTests/
    Features/
      Profile/
        ProfileViewModelTests.swift
        ProfileReducerTests.swift
      Feed/
        FeedViewModelTests.swift
    Helpers/
      User+Mock.swift        // test fixtures on production types
      XCTestCase+Helpers.swift
    __Snapshots__/           // committed to version control
```

**Test doubles terminology** (use consistently in PR reviews):

| Term | Behavior |
|---|---|
| **Stub** | Returns hard-coded values, no behavior verification |
| **Spy** | Records calls, optionally stubs return values |
| **Mock** | Pre-configured expectations, verifies interactions |
| **Fake** | Working implementation (e.g. in-memory store) |

**Arrange-Act-Assert:**

```swift
@Test func calculate_withDiscount_reducesTotal() {
    // Arrange
    let cart = Cart(items: [.init(price: 100)], discountCode: "SAVE10")
    // Act
    let total = cart.calculateTotal()
    // Assert
    #expect(total == 90)
}
```

---

## 10. Testing Best Practices

**What to test:**
- Business logic (calculators, validators, state machines)
- Error handling paths
- Boundary conditions (empty, nil, max values)
- Async race conditions via controlled clocks

**What NOT to test:**
- Framework behavior (SwiftUI view body rendering)
- Trivial getters/setters
- Private implementation details
- Third-party library behavior

**Test pyramid:** 70% unit, 20% integration, 10% UI. Invert this = slow, brittle suite.

**Avoiding flaky tests:**
- Replace `Task.sleep` with `@Dependency(\.continuousClock)` and advance it manually
- Never use `XCTestExpectation` with arbitrary timeouts — use `async/await`
- Isolate all mutable state in `setUp`/`tearDown` or `init`

**Code coverage:** Target 80% line coverage. 100% is counterproductive — it forces testing of trivial code while providing false confidence. Focus on critical paths, not line counts.

**Test performance:** Use `measure { }` in XCTest or `ContinuousClock().measure { }` with `#expect` in Swift Testing. Baselines stored in `.xctestplan`.

---

## 11. Macro Testing

Use `pointfreeco/swift-macro-testing` for testing custom Swift macros. Snapshots the expanded source.

```swift
import MacroTesting
import XCTest

final class StringifyMacroTests: XCTestCase {
    override func invokeTest() {
        withMacroTesting(macros: ["stringify": StringifyMacro.self]) {
            super.invokeTest()
        }
    }

    func test_stringify_expandsToTupleWithSource() {
        assertMacro {
            """
            #stringify(a + b)
            """
        } expansion: {
            """
            (a + b, "a + b")
            """
        }
    }

    func test_stringify_diagnosticOnInvalidInput() {
        assertMacro {
            "#stringify()"
        } diagnostics: {
            """
            #stringify()
                        ^ error: requires an expression argument
            """
        }
    }
}
```

First run records the expansion snapshot. Subsequent runs diff against it — any macro output change fails the test, making macro refactors safe.

---

## 12. Network Testing

**Preferred: inject a protocol, use a fake.**

```swift
protocol HTTPClient {
    func data(for request: URLRequest) async throws -> (Data, URLResponse)
}

// Fake for tests — no URLProtocol swizzling needed
final class FakeHTTPClient: HTTPClient {
    var stubbedResponses: [URL: Result<Data, Error>] = [:]
    func data(for request: URLRequest) async throws -> (Data, URLResponse) {
        let result = try stubbedResponses[request.url!] ?? { throw URLError(.badURL) }()
        let response = HTTPURLResponse(url: request.url!, statusCode: 200, httpVersion: nil, headerFields: nil)!
        return (try result.get(), response)
    }
}

// Load JSON fixtures from bundle
extension Data {
    static func fixture(_ name: String) -> Data {
        try! Data(contentsOf: Bundle.module.url(forResource: name, withExtension: "json")!)
    }
}
```

**URLProtocol fallback** — only when you cannot inject at the `URLSession` level (e.g. third-party SDKs):

```swift
final class MockURLProtocol: URLProtocol {
    static var handler: ((URLRequest) throws -> (HTTPURLResponse, Data))?
    override class func canInit(with request: URLRequest) -> Bool { true }
    override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }
    override func startLoading() {
        do {
            let (resp, data) = try Self.handler!(request)
            client?.urlProtocol(self, didReceive: resp, cacheStoragePolicy: .notAllowed)
            client?.urlProtocol(self, didLoad: data)
            client?.urlProtocolDidFinishLoading(self)
        } catch { client?.urlProtocol(self, didFailWithError: error) }
    }
    override func stopLoading() {}
}
// Setup: URLSessionConfiguration.ephemeral with protocolClasses = [MockURLProtocol.self]
```
