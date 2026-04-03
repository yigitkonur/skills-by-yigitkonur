# SwiftUI Observation And Ownership

## Use This When
- Choosing between `ObservableObject`, `@StateObject`, `@ObservedObject`, `@EnvironmentObject`, and `@Observable`.
- Debugging duplicate subscriptions or view-model reinitialization.
- Placing auth or live data owners in the SwiftUI tree.

## Default Ownership Model
- Use `ObservableObject` for models that own subscriptions, auth state, or connection monitoring.
- Use `@StateObject` at the first stable owner of that model.
- Pass the same instance downward through `@ObservedObject` or `@EnvironmentObject`.
- Keep app-wide owners at the app or root feature boundary.

## Why This Default Exists
- `@StateObject` preserves the owned instance across view re-renders via `@autoclosure` deferred initialization.
- `@State` evaluates eagerly — each view rebuild calls `init()`, and side effects (like starting subscriptions) fire every time.
- Convex subscriptions are side-effectful; repeated model initialization is not harmless.
- Shared live state should have one clear owner, not many coincidental creators.

## Recommendation Table

| Target | Use |
|---|---|
| iOS 13–16 | `ObservableObject` + `@StateObject` (only option) |
| iOS 17+ (safe default) | `ObservableObject` + `@StateObject` (recommended by Convex) |
| iOS 17+ (modern) | `@Observable` with mitigations below — understand the quirks |

## The `@Observable` Re-Init Problem

When `@Observable` is used with `@State`, SwiftUI's view reconstruction calls `init()` on **every view rebuild**. Each rebuild creates a new instance (which SwiftUI discards), but `init()` side effects — like starting subscriptions — still fire.

### Mitigation A: Place at App Level

```swift
@Observable final class AppStore {
    var messages: [Message] = []
    private var cancellables = Set<AnyCancellable>()
    init() {
        client.subscribe(to: "messages:list", yielding: [Message].self)
            .replaceError(with: []) // ⚠️ PROTOTYPE ONLY — kills pipeline after first error. See pitfalls/01.
            .receive(on: DispatchQueue.main)
            .sink { [weak self] in self?.messages = $0 }
            .store(in: &cancellables)
    }
}

@main struct MyApp: App {
    @State private var store = AppStore()
    var body: some Scene {
        WindowGroup { ContentView().environment(store) }
    }
}
```

### Mitigation B: Lazy Init via `.task`

```swift
struct ChatView: View {
    @State private var vm: ChatViewModel?
    var body: some View {
        Group {
            if let vm { ChatContent(vm: vm) }
            else { ProgressView() }
        }
        .task { vm = ChatViewModel() }
    }
}
```

### Mitigation C: Side-Effect-Free State Only

```swift
@Observable class FilterState {
    var searchText = ""        // no subscriptions in init — safe
    var showCompleted = true
}
```

> **Pipeline termination warning:** `.replaceError(with:)` in examples above terminates the stream after the first error. For production, use Result-wrapping. See `client-sdk/04-pipeline-termination-and-recovery.md`.

## Ownership Smells
- Child views creating their own `@StateObject` for shared feature state.
- View models recreating clients or auth providers inside their own lifecycle.
- Repeated `init()`-driven side effects when using `@Observable` without clear activation boundaries.

## Avoid
- `@ObservedObject` as the creator of state — it does not own the lifecycle.
- `@EnvironmentObject` when the state is not actually shared broadly enough to justify global reach.
- Putting subscription setup directly in an `@Observable` `init()` that can be triggered repeatedly.
- Treating ownership questions as SwiftUI ceremony instead of correctness.

## Read Next
- [01-consumption-patterns.md](01-consumption-patterns.md)
- [03-lifecycle-navigation-tabs-and-sheets.md](03-lifecycle-navigation-tabs-and-sheets.md)
- [../pitfalls/08-observable-macro-re-init-trap.md](../pitfalls/08-observable-macro-re-init-trap.md)
