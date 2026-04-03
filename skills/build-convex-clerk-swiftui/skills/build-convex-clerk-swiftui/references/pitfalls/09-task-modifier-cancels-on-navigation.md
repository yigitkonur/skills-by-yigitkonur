# .task Modifier Cancels On Navigation

## Use This When
- Deciding where to start a long-lived Convex subscription in SwiftUI.
- Debugging subscriptions that tear down and recreate on every navigation push, tab switch, or sheet dismissal.
- Choosing between `.task { }` and `@StateObject` for subscription ownership.

## The Problem

SwiftUI's `.task { }` modifier cancels its work on every `onDisappear`. This includes navigation push (detail view appears, list disappears), tab switch, sheet dismissal of the presenting view, and any view removal from the hierarchy.

For subscriptions started in `.task`, every navigation event tears down the subscription and re-creates it on return:

```
1. User sees list -> .task starts subscription
2. User taps item -> NavigationLink pushes detail
3. List.onDisappear -> .task CANCELLED, subscription torn down
4. User taps Back -> List.onAppear -> .task restarts, new subscription
5. Brief flash of empty/stale data while reconnecting
```

## The Fix: @StateObject for Persistent Subscriptions

`@StateObject` persists across `onDisappear`/`onAppear` cycles. The subscription stays alive during navigation:

```swift
class TaskListViewModel: ObservableObject {
    @Published var tasks: [Task] = []
    private var cancellables = Set<AnyCancellable>()
    private var isSubscribed = false

    func startSubscription(client: ConvexClient) {
        guard !isSubscribed else { return }
        isSubscribed = true

        client.subscribe(to: "tasks:list", with: [:], yielding: [Task].self)
            .receive(on: DispatchQueue.main)
            .removeDuplicates()
            .asResult()
            .sink { [weak self] result in
                switch result {
                case .success(let tasks): self?.tasks = tasks
                case .failure(let error): self?.isSubscribed = false
                }
            }
            .store(in: &cancellables)
    }
}

struct TaskListView: View {
    @StateObject private var viewModel = TaskListViewModel()
    // Uses module-level `client` (see walkthrough/03)

    var body: some View {
        List(viewModel.tasks) { task in
            NavigationLink(task.title) { TaskDetailView(taskId: task.id) }
        }
        .task { viewModel.startSubscription(client: client) }
    }
}
```

## When .task IS Appropriate

`.task` is correct for throwaway screens where the subscription lifecycle should match the view lifecycle:

| Scenario | Use .task? | Use @StateObject? |
|---|---|---|
| List view in NavigationStack | No | Yes |
| Tab root view | No | Yes |
| Detail view (pushed) | Yes | No |
| Modal/sheet content | Yes | No |
| One-shot data fetch | Yes | No |
| App-critical real-time data | No | Yes |

## .task(id:) Variant

`.task(id:)` restarts when the `id` value changes. Useful for detail views that resubscribe with different parameters:

```swift
Text(task?.title ?? "Loading...")
    .task(id: taskId) {
        // Cancels old subscription, starts new one when taskId changes
    }
```

## Avoid
- Starting long-lived subscriptions in `.task { }` on list views or tab root views.
- Assuming `.task` work survives `onDisappear` — it does not.
- Ignoring the brief stale/empty flash between teardown and re-creation.
- Using `.task { }` for subscriptions that must stay alive across navigation.

## Read Next
- [08-observable-macro-re-init-trap.md](08-observable-macro-re-init-trap.md)
- [../swiftui/03-lifecycle-navigation-tabs-and-sheets.md](../swiftui/03-lifecycle-navigation-tabs-and-sheets.md)
- [../swiftui/01-consumption-patterns.md](../swiftui/01-consumption-patterns.md)
