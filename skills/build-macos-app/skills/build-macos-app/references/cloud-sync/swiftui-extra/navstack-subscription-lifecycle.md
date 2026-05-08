# NavigationStack Subscription Lifecycle

## Use This When
- Deciding whether to place a subscription in `.task` or `@StateObject` within a navigation stack.
- Debugging data loss when a user pushes or pops views in a `NavigationStack`.
- Understanding why a list subscription stopped updating after a detail view was pushed.

## The Lifecycle

```
User on ListScreen
  → ListScreen.onAppear → .task starts → subscription active

User taps item → pushes DetailScreen
  → ListScreen.onDisappear → .task CANCELLED
  → DetailScreen.onAppear → DetailScreen.task starts

User taps Back
  → DetailScreen.onDisappear → DetailScreen.task cancelled
  → ListScreen.onAppear → .task starts AGAIN (re-subscribes)
```

Every push cancels the parent view's `.task`. Every pop cancels the child's `.task` and restarts the parent's. This means subscriptions placed in `.task` on a list screen will be torn down and rebuilt on every navigation round-trip.

## @StateObject Survives Push/Pop

A `@StateObject` declared in the parent view is NOT destroyed when a child is pushed onto the stack. Its internal subscriptions remain active.

```swift
struct ListScreen: View {
    @StateObject var vm = ListViewModel()  // survives push/pop

    var body: some View {
        NavigationStack {
            List(vm.items) { item in
                NavigationLink(value: item) { Text(item.title) }
            }
            .navigationDestination(for: Item.self) { item in
                DetailView(item: item)
                // vm.subscription is STILL ACTIVE here
            }
        }
    }
}
```

The `ListViewModel` owns the Combine subscription via `cancellables`. Because `@StateObject` is not re-created on push/pop, the subscription stays alive and the list data is current when the user pops back.

## Subscription Placement Rules

| Placement | Survives Push/Pop | Best For |
|-----------|------------------|----------|
| `.task` on list view | No — cancelled on push | One-shot fetches, detail-only data |
| `@StateObject` model | Yes — survives | Durable list subscriptions, shared state |
| `.task(id:)` on detail | No — cancelled on pop | Parameter-driven detail queries |

### Recommended Pattern

```swift
// List ViewModel — subscribes in init, survives navigation
class ListViewModel: ObservableObject {
    @Published var items: [Item] = []
    private var cancellables = Set<AnyCancellable>()

    init() {
        client.subscribe(to: "items:list", with: [:], yielding: [Item].self)
            .receive(on: DispatchQueue.main)
            .removeDuplicates()
            .sink(
                receiveCompletion: { _ in },
                receiveValue: { [weak self] in self?.items = $0 }
            )
            .store(in: &cancellables)
    }
}

// Detail view — uses .task for screen-scoped data
struct DetailView: View {
    let itemId: String
    @State private var detail: ItemDetail?

    var body: some View {
        Group {
            if let detail { ItemDetailContent(detail: detail) }
            else { ProgressView() }
        }
        .task {
            for await d in client.subscribe(
                to: "items:getDetail",
                with: ["id": itemId],
                yielding: ItemDetail.self
            ).values {
                detail = d
            }
        }
    }
}
```

## Avoid
- Placing durable list subscriptions in `.task` on screens users navigate away from — they will be cancelled on every push.
- Assuming `.task` on a parent screen stays active while a child is visible in the stack.
- Using `.onDisappear` for manual subscription cleanup instead of fixing ownership with `@StateObject`.
- Recreating expensive subscriptions on every push/pop cycle when a `@StateObject` model would eliminate the churn.

## Read Next
- [03-lifecycle-navigation-tabs-and-sheets.md](03-lifecycle-navigation-tabs-and-sheets.md)
- [02-observation-and-ownership.md](02-observation-and-ownership.md)
- [06-tabview-and-sheet-patterns.md](06-tabview-and-sheet-patterns.md)
