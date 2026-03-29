# @Observable Macro Re-Init Trap

## Use This When
- Choosing between `ObservableObject`/`@StateObject` and `@Observable`/`@State` for a model that owns Convex subscriptions.
- Debugging duplicate or leaked subscriptions tied to view lifecycle.
- Reviewing code that creates Combine pipelines inside an `@Observable` class `init()`.

## The Problem

When using `@Observable` with `@State`, SwiftUI may call `init()` on the observable object multiple times during view rebuilds. Unlike `@StateObject` (which guarantees single initialization), `@State` with `@Observable` creates a new instance on every parent rebuild, then discards the extras. The problem: **init() side effects run every time**, even on discarded instances.

After 10 parent rebuilds with subscription setup in `init()`: 10 subscriptions active, 9 leaked.

## Fix 1: ObservableObject + @StateObject (Recommended)

`@StateObject` guarantees `init()` runs exactly once per view lifetime. This is the safest pattern for models that own Convex subscriptions:

```swift
class TaskListViewModel: ObservableObject {
    @Published var tasks: [Task] = []
    private var cancellables = Set<AnyCancellable>()

    func startSubscription(client: ConvexClient) {
        client.subscribe(to: "tasks:list", with: [:], yielding: [Task].self)
            .receive(on: DispatchQueue.main)
            .removeDuplicates()
            .asResult()
            .sink { [weak self] result in
                switch result {
                case .success(let tasks): self?.tasks = tasks
                case .failure(let error): print(error)
                }
            }
            .store(in: &cancellables)
    }
}

struct TaskListView: View {
    @StateObject private var viewModel = TaskListViewModel()
    // Uses module-level `client` (see walkthrough/03)

    var body: some View {
        List(viewModel.tasks) { task in Text(task.title) }
            .task { viewModel.startSubscription(client: client) }
    }
}
```

## Fix 2: @Observable With Lazy .task Initialization

If using `@Observable`, keep `init()` side-effect-free and start subscriptions from `.task` with a guard:

```swift
@Observable
class TaskListModel {
    var tasks: [Task] = []
    private var isSubscribed = false
    private var cancellable: AnyCancellable?

    init() {} // NO side effects

    func startIfNeeded(client: ConvexClient) {
        guard !isSubscribed else { return }
        isSubscribed = true
        cancellable = client.subscribe(to: "tasks:list", with: [:], yielding: [Task].self)
            .receive(on: DispatchQueue.main)
            .removeDuplicates()
            .sink(receiveCompletion: { _ in }, receiveValue: { [weak self] tasks in
                self?.tasks = tasks
            })
    }
}
```

## Fix 3: App-Level @Observable

Create the observable at the `App` level where it will not be re-created by parent view rebuilds.

## Comparison

| Approach | Re-init on parent rebuild? | Side effect safety |
|---|---|---|
| `ObservableObject` + `@StateObject` | No | Safe by design |
| `@Observable` + `init()` side effects | Yes (dangerous) | Unsafe |
| `@Observable` + lazy `.task` init | Yes but guarded | Safe with guard |
| `@Observable` at App level | No | Safe |

## Avoid
- Putting subscription setup, network calls, or any side effects in an `@Observable` class `init()`.
- Using `@State` with `@Observable` for models that own Combine pipelines.
- Assuming SwiftUI creates `@Observable` instances only once — parent rebuilds trigger re-creation.

## Read Next
- [../swiftui/02-observation-and-ownership.md](../swiftui/02-observation-and-ownership.md)
- [09-task-modifier-cancels-on-navigation.md](09-task-modifier-cancels-on-navigation.md)
- [../swiftui/04-environment-injection-and-root-architecture.md](../swiftui/04-environment-injection-and-root-architecture.md)
