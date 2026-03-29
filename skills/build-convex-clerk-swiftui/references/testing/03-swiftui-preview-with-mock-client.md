# SwiftUI Preview with Mock Client

## Use This When
- Building SwiftUI previews for views that depend on Convex data.
- Preventing preview crashes caused by real WebSocket connections.
- Providing fixture data to ViewModels in `#Preview` blocks.

## The Problem

SwiftUI previews crash if a ViewModel opens a real WebSocket. A protocol abstraction lets previews inject a mock that returns fixture data instantly via `Just()`.

## Define ConvexClientProtocol

Mirror the three methods your app uses from `ConvexClient`:

```swift
import Combine
import ConvexMobile

protocol ConvexClientProtocol {
  func subscribe<T: Decodable>(
    to name: String,
    with args: [String: ConvexEncodable?]? = nil,
    yielding type: T.Type? = nil
  ) -> AnyPublisher<T, ClientError>

  func mutation<T: Decodable>(
    _ name: String,
    with args: [String: ConvexEncodable?]? = nil
  ) async throws -> T

  func action<T: Decodable>(
    _ name: String,
    with args: [String: ConvexEncodable?]
  ) async throws -> T
}

// ConvexClient already satisfies this
extension ConvexClient: ConvexClientProtocol {}
```

## PreviewConvexClient

Returns static fixture data, never touches the network:

```swift
import Combine
import ConvexMobile

final class PreviewConvexClient: ConvexClientProtocol {
  private var fixtures: [String: Any] = [:]

  func setFixture<T: Decodable>(_ name: String, value: T) {
    fixtures[name] = value
  }

  func subscribe<T: Decodable>(
    to name: String,
    with args: [String: ConvexEncodable?],
    yielding type: T.Type
  ) -> AnyPublisher<T, ClientError> {
    guard let value = fixtures[name] as? T else {
      return Fail(error: ClientError.InternalError(msg:"No fixture for \(name)"))
        .eraseToAnyPublisher()
    }
    return Just(value)
      .setFailureType(to: ClientError.self)
      .eraseToAnyPublisher()
  }

  func mutation<T: Decodable>(
    _ name: String,
    with args: [String: ConvexEncodable?]
  ) async throws -> T {
    guard let value = fixtures[name] as? T else {
      throw ClientError.InternalError(msg:"No fixture for \(name)")
    }
    return value
  }

  func action<T: Decodable>(
    _ name: String,
    with args: [String: ConvexEncodable?]
  ) async throws -> T {
    guard let value = fixtures[name] as? T else {
      throw ClientError.InternalError(msg:"No fixture for \(name)")
    }
    return value
  }
}
```

## Fixture Models

Every `Decodable` struct must include `CodingKeys` with `_id` mapping:

```swift
struct Message: Decodable, Identifiable {
  let id: String
  let body: String
  let authorName: String
  let creationTime: Double

  enum CodingKeys: String, CodingKey {
    case id = "_id"
    case body
    case authorName
    case creationTime = "_creationTime"
  }
}
```

## ViewModel Using the Protocol

```swift
import Combine

final class ChannelViewModel: ObservableObject {
  @Published var messages: [Message] = []

  private let client: ConvexClientProtocol
  private let channelId: String
  private var cancellables = Set<AnyCancellable>()

  init(client: ConvexClientProtocol, channelId: String) {
    self.client = client
    self.channelId = channelId
  }

  func startSubscription() {
    client.subscribe(
      to: "messages:list",
      with: ["channelId": channelId],
      yielding: [Message].self
    )
    .receive(on: DispatchQueue.main)
    .sink(
      receiveCompletion: { _ in },
      receiveValue: { [weak self] in self?.messages = $0 }
    )
    .store(in: &cancellables)
  }
}
```

## Use in #Preview

```swift
#Preview("Channel with messages") {
  let mock = PreviewConvexClient()
  mock.setFixture("messages:list", value: Fixtures.messages)

  let vm = ChannelViewModel(client: mock, channelId: "ch1")
  vm.startSubscription()

  return ChannelView(viewModel: vm)
}

#Preview("Empty channel") {
  let mock = PreviewConvexClient()
  mock.setFixture("messages:list", value: [Message]())

  let vm = ChannelViewModel(client: mock, channelId: "ch1")
  vm.startSubscription()

  return ChannelView(viewModel: vm)
}
```

## Avoid
- Making real network calls in previews -- always use `PreviewConvexClient`.
- Using `.replaceError(with:)` in Combine pipelines -- it terminates the stream permanently after the first error. Use `sink` with explicit `receiveCompletion` handling.
- Skipping `CodingKeys` with `case id = "_id"` -- Convex documents use `_id`.
- Omitting `.receive(on: DispatchQueue.main)` on subscriptions -- UI updates must be on the main queue.
- Passing a real `ConvexClient` or `ConvexClientWithAuth` to preview blocks.

## Read Next
- [01-mock-ffi-client-unit-testing.md](01-mock-ffi-client-unit-testing.md)
- [../swiftui/02-observation-and-ownership.md](../swiftui/02-observation-and-ownership.md)
- [../swiftui/04-environment-injection-and-root-architecture.md](../swiftui/04-environment-injection-and-root-architecture.md)
