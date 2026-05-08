# Loading, Error, Data Tri-State Pattern

## Use This When
- Representing subscription state cleanly across loading, success, and failure.
- Building skeleton loading screens that transition to live data.
- Handling subscription errors with user-visible recovery options.

## The Enum

```swift
enum ViewState<T> {
    case loading
    case loaded(T)
    case failed(ClientError)
}
```

This replaces scattered optionals and boolean flags with a single exhaustive state. The compiler enforces that every case is handled.

## ViewModel

```swift
import Combine
import ConvexMobile

class TodoViewModel: ObservableObject {
    @Published var state: ViewState<[Todo]> = .loading
    private var cancellables = Set<AnyCancellable>()

    init() {
        subscribe()
    }

    private func subscribe() {
        client.subscribe(to: "tasks:get", with: [:], yielding: [Todo].self)
            .receive(on: DispatchQueue.main)
            .removeDuplicates()
            .map { ViewState.loaded($0) }
            .catch { error in Just(ViewState<[Todo]>.failed(error)) }
            .sink { [weak self] in self?.state = $0 }
            .store(in: &cancellables)
    }

    func resubscribe() {
        state = .loading
        cancellables.removeAll()
        subscribe()
    }
}
```

### Pipeline Termination Warning

`catch { Just(.failed(error)) }` surfaces the error as UI state, but the Combine pipeline **completes** after that single value. The subscription stops receiving updates. The `resubscribe()` method handles this by clearing cancellables and re-creating the subscription from scratch.

## View

```swift
struct TodoListView: View {
    @StateObject private var vm = TodoViewModel()

    var body: some View {
        switch vm.state {
        case .loading:
            ProgressView()
        case .loaded(let todos):
            List(todos) { todo in
                Text(todo.text)
            }
        case .failed(let error):
            VStack(spacing: 12) {
                Image(systemName: "exclamationmark.triangle")
                    .font(.largeTitle)
                    .foregroundStyle(.secondary)
                Text(error.localizedDescription)
                    .foregroundStyle(.red)
                    .multilineTextAlignment(.center)
                Button("Retry") { vm.resubscribe() }
                    .buttonStyle(.borderedProminent)
            }
            .padding()
        }
    }
}
```

## Skeleton Loading Variant

For richer loading states, extend the pattern with placeholder data:

```swift
case .loading:
    List(0..<5, id: \.self) { _ in
        HStack {
            RoundedRectangle(cornerRadius: 4)
                .fill(.quaternary)
                .frame(height: 16)
        }
        .redacted(reason: .placeholder)
    }
```

## When To Use This Pattern

| Scenario | Recommendation |
|----------|----------------|
| Single subscription driving one screen | Use `ViewState<T>` directly |
| Multiple independent subscriptions on one screen | One `ViewState<T>` per subscription, or a composite state |
| Subscription that must never show loading after first data | Add a `.loaded` → `.loaded` transition that skips `.loading` on resubscribe |
| Auth-gated content | Combine with `AuthState` — auth gate first, then tri-state for data |

## Avoid
- Representing loading/error/data with separate `@Published` booleans (`isLoading`, `hasError`, `data: T?`) — these allow impossible states like `isLoading == true && hasError == true`.
- Using `.replaceError(with:)` on subscription publishers — it emits the fallback then **completes** the pipeline permanently, killing live updates.
- Forgetting the retry path — once `catch` completes the pipeline, the user is stuck without `resubscribe()`.
- Showing a loading spinner on every resubscribe when stale data would be a better UX.

## Read Next
- [01-consumption-patterns.md](01-consumption-patterns.md)
- [02-observation-and-ownership.md](02-observation-and-ownership.md)
- [05-navigation-stack-subscription-lifecycle.md](05-navigation-stack-subscription-lifecycle.md)
