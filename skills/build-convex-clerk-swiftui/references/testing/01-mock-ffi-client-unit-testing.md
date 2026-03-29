# Mock FFI Client Unit Testing

## Use This When
- Writing unit tests for ViewModels or services that call `client.subscribe`, `client.mutation`, or `client.action`.
- Isolating Swift tests from the Rust FFI bridge and live Convex deployments.
- Verifying that mutation arguments are captured correctly in tests.

## The Testing Challenge

`ConvexClient` wraps a Rust FFI bridge. Its only public initializer requires a deployment URL and opens a real WebSocket. The SDK exposes `MobileConvexClientProtocol`, and `@testable import ConvexMobile` lets you inject a mock via `init(ffiClient:)`.

## Protocol Surface

```swift
public protocol MobileConvexClientProtocol {
  func subscribe<T: Decodable>(
    to name: String,
    with args: [String: ConvexEncodable?]?,
    yielding type: T.Type
  ) -> AnyPublisher<T, ClientError>

  func mutation<T: Decodable>(
    _ name: String,
    with args: [String: ConvexEncodable?]?
  ) async throws -> T

  func action<T: Decodable>(
    _ name: String,
    with args: [String: ConvexEncodable?]?
  ) async throws -> T
}
```

## MockConvexClient

```swift
import Combine
@testable import ConvexMobile

final class MockConvexClient: MobileConvexClientProtocol {

  // MARK: - Subscription stubbing
  var subscriptionSubject = PassthroughSubject<Any, ClientError>()

  func subscribe<T: Decodable>(
    to name: String,
    with args: [String: ConvexEncodable?]?,
    yielding type: T.Type
  ) -> AnyPublisher<T, ClientError> {
    subscriptionSubject
      .compactMap { $0 as? T }
      .eraseToAnyPublisher()
  }

  // MARK: - Mutation stubbing
  var lastMutationName: String?
  var lastMutationArgs: [String: ConvexEncodable?]?
  var mutationResult: Any = ()

  func mutation<T: Decodable>(
    _ name: String,
    with args: [String: ConvexEncodable?]?
  ) async throws -> T {
    lastMutationName = name
    lastMutationArgs = args
    guard let result = mutationResult as? T else {
      throw ClientError.InternalError(msg: "Mock type mismatch")
    }
    return result
  }

  // MARK: - Action stubbing
  var lastActionName: String?
  var actionResult: Any = ()

  func action<T: Decodable>(
    _ name: String,
    with args: [String: ConvexEncodable?]?
  ) async throws -> T {
    lastActionName = name
    guard let result = actionResult as? T else {
      throw ClientError.InternalError(msg: "Mock type mismatch")
    }
    return result
  }
}
```

## Test Subscription Delivery

```swift
import XCTest
import Combine
@testable import ConvexMobile

final class ChannelViewModelTests: XCTestCase {
  var mock: MockConvexClient!
  var cancellables = Set<AnyCancellable>()

  override func setUp() {
    mock = MockConvexClient()
  }

  func testSubscriptionDeliversMessages() {
    let expectation = expectation(description: "messages arrive")

    struct Message: Decodable, Equatable {
      let id: String
      let body: String
      enum CodingKeys: String, CodingKey {
        case id = "_id"
        case body
      }
    }

    mock.subscribe(
      to: "messages:list",
      with: ["channelId": "ch1"],
      yielding: [Message].self
    )
    .receive(on: DispatchQueue.main)
    .sink(
      receiveCompletion: { _ in },
      receiveValue: { messages in
        XCTAssertEqual(messages.count, 1)
        XCTAssertEqual(messages.first?.body, "hello")
        expectation.fulfill()
      }
    )
    .store(in: &cancellables)

    mock.subscriptionSubject.send(
      [Message(id: "msg1", body: "hello")] as Any
    )

    wait(for: [expectation], timeout: 2.0)
  }
}
```

## Test Mutation Args Capture

```swift
func testSendMessageCapturesArgs() async throws {
  mock.mutationResult = () as Any

  try await mock.mutation(
    "messages:send",
    with: [
      "channelId": "ch1",
      "body": "hello world"
    ]
  ) as Void

  XCTAssertEqual(mock.lastMutationName, "messages:send")
  // Verify the argument was captured (compare after casting)
  XCTAssertEqual(mock.lastMutationArgs?["body"] as? String, "hello world")
}
```

## Key Rules

| Concern | Approach |
|---|---|
| Isolate FFI | `@testable import` + `MockConvexClient` |
| Subscription tests | `PassthroughSubject` + `XCTestExpectation` |
| Mutation tests | Capture `lastMutationName` / `lastMutationArgs` |
| Thread safety | Always `.receive(on: DispatchQueue.main)` |
| CodingKeys | Every model must map `case id = "_id"` |

## Avoid
- Using `.replaceError(with:)` in test pipelines -- it terminates the stream after the first error and silently stops receiving updates. Use `sink(receiveCompletion:receiveValue:)` with error state + `resubscribe()`, or Result-wrapping + `resubscribe()`.
- Creating a real `ConvexClient` in unit tests -- it opens a live WebSocket.
- Skipping `CodingKeys` with `case id = "_id"` -- Convex documents use `_id`, not `id`.
- Testing on a background queue without dispatching to main -- Combine pipelines from ConvexMobile must use `.receive(on: DispatchQueue.main)`.

## Read Next
- [02-integration-testing-with-test-deployment.md](02-integration-testing-with-test-deployment.md)
- [03-swiftui-preview-with-mock-client.md](03-swiftui-preview-with-mock-client.md)
- [../client-sdk/03-subscriptions-errors-logging-and-connection-state.md](../client-sdk/03-subscriptions-errors-logging-and-connection-state.md)
