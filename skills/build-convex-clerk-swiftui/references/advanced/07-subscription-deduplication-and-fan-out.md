# Subscription Deduplication And Fan-Out

## Use This When
- Preventing unnecessary re-renders when the WebSocket reconnects with unchanged data.
- Sharing one subscription across multiple views without duplicating server resources.
- Understanding the difference between Rust-level and Combine-level deduplication.

## .removeDuplicates() Prevents Re-Renders On Reconnect

When the WebSocket reconnects (after sleep, background, network change), the server re-sends the current value for all active subscriptions. Without deduplication, every reconnect triggers a UI update even when the data has not changed.

```swift
// Without deduplication: re-renders on every reconnect
client.subscribe(to: "tasks:list", with: [:], yielding: [Task].self)
    .receive(on: DispatchQueue.main)
    .sink { ... }

// With deduplication: only re-renders when data actually changes
client.subscribe(to: "tasks:list", with: [:], yielding: [Task].self)
    .receive(on: DispatchQueue.main)
    .removeDuplicates()  // Requires Equatable conformance
    .sink { ... }
```

## Model Must Be Equatable

`.removeDuplicates()` requires the output type to conform to `Equatable`. For arrays, this means the element type must be `Equatable`.

```swift
struct TaskItem: Decodable, Identifiable, Equatable {
    let id: String
    let title: String
    let isComplete: Bool
    let assigneeId: String?

    enum CodingKeys: String, CodingKey {
        case id = "_id"
        case title
        case isComplete
        case assigneeId
    }
    // Equatable is auto-synthesized since all properties are Equatable
}
```

## Custom Equality For Performance

For large result sets, comparing entire arrays can be expensive. Use a custom comparator that checks a cheaper proxy:

```swift
client.subscribe(to: "tasks:list", with: [:], yielding: [TaskItem].self)
    .receive(on: DispatchQueue.main)
    .removeDuplicates { previous, current in
        previous.count == current.count
            && previous.first?.id == current.first?.id
            && previous.last?.id == current.last?.id
    }
    .sink { ... }
```

## .share() For Multiple Views Consuming One Subscription

When multiple views need the same subscription data, use `.share()` to avoid creating duplicate Combine pipelines:

```swift
class SharedDataManager: ObservableObject {
    let tasksPublisher: AnyPublisher<[TaskItem], ClientError>
    private var cancellables = Set<AnyCancellable>()

    init() {
        tasksPublisher = client.subscribe(
            to: "tasks:list",
            with: [:],
            yielding: [TaskItem].self
        )
        .receive(on: DispatchQueue.main)
        .removeDuplicates()
        .share()
        .eraseToAnyPublisher()
    }
}
```

Multiple views can subscribe to `tasksPublisher`:

```swift
// View A: Task list
class TaskListViewModel: ObservableObject {
    @Published var tasks: [TaskItem] = []
    private var cancellables = Set<AnyCancellable>()

    func start(manager: SharedDataManager) {
        manager.tasksPublisher
            .sink(
                receiveCompletion: { _ in },
                receiveValue: { [weak self] in self?.tasks = $0 }
            )
            .store(in: &cancellables)
    }
}

// View B: Task count badge
class TaskBadgeViewModel: ObservableObject {
    @Published var incompleteCount = 0
    private var cancellables = Set<AnyCancellable>()

    func start(manager: SharedDataManager) {
        manager.tasksPublisher
            .map { tasks in tasks.filter { !$0.isComplete }.count }
            .removeDuplicates()
            .sink(
                receiveCompletion: { _ in },
                receiveValue: { [weak self] in self?.incompleteCount = $0 }
            )
            .store(in: &cancellables)
    }
}
```

## .share() Is Hot — Late Subscribers Miss The Initial Value

`.share()` converts the publisher to a "hot" publisher. It only multicasts values emitted **after** subscription. If View B subscribes after the first value was emitted, it will not receive that initial value until the next update from the server.

### Fix: shareReplay (Custom Operator)

Combine does not include `shareReplay`. Implement it when late subscribers need the last emitted value:

```swift
extension Publisher {
    func shareReplay(_ count: Int = 1) -> AnyPublisher<Output, Failure> {
        let subject = CurrentValueSubject<Output?, Failure>(nil)
        var cancellable: AnyCancellable?

        return Deferred {
            if cancellable == nil {
                cancellable = self.sink(
                    receiveCompletion: { subject.send(completion: $0) },
                    receiveValue: { subject.send($0) }
                )
            }
            return subject
                .compactMap { $0 }
                .eraseToAnyPublisher()
        }
        .eraseToAnyPublisher()
    }
}
```

> **Warning:** This implementation has known issues: the captured `var cancellable` is not thread-safe, the `count` parameter is ignored (only replays latest value), and the upstream subscription may leak if all downstream subscribers cancel. For production use, consider the `share(replay:)` operator from [CombineExt](https://github.com/CombineCommunity/CombineExt).

## Two Levels Of Deduplication

| Level | What It Does | When It Helps |
|-------|-------------|---------------|
| Rust client | Deduplicates identical WebSocket subscriptions (same function + same args) | Two ViewModels subscribing to `tasks:list` with `[:]` share one WebSocket subscription |
| `.removeDuplicates()` | Suppresses Combine emissions when data has not changed | Prevents UI re-renders on reconnect or redundant server pushes |
| `.share()` | Multiple Combine subscribers share one processing pipeline | Avoids duplicate `.map`, `.removeDuplicates()`, etc. per view |

## When To Use What

| Scenario | Operator |
|----------|----------|
| Single subscriber | `.removeDuplicates()` only |
| Prevent reconnect re-renders | `.removeDuplicates()` |
| Multiple views, same data | `.share()` + per-view `.map()` |
| Multiple views, need replay | `.shareReplay(1)` (custom) |

## Avoid
- Omitting `.removeDuplicates()` — every WebSocket reconnect will trigger unnecessary re-renders.
- Using `.replaceError(with:)` on shared subscription publishers — it emits the fallback then **completes** permanently, killing the shared stream for ALL subscribers.
- Forgetting `Equatable` conformance on model types — `.removeDuplicates()` will not compile without it.
- Over-sharing with `.share()` when independent ViewModels with Rust-level deduplication are simpler and sufficient.

## Read Next
- [06-full-text-search-reactive.md](06-full-text-search-reactive.md)
- [01-pagination-live-tail-and-history.md](01-pagination-live-tail-and-history.md)
- [../swiftui/01-consumption-patterns.md](../swiftui/01-consumption-patterns.md)
