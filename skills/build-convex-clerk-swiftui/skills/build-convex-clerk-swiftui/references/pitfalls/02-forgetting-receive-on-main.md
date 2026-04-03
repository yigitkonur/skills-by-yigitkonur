# Forgetting .receive(on: DispatchQueue.main)

## Use This When
- Seeing purple runtime warnings about publishing changes from background threads.
- Debugging intermittent `EXC_BAD_ACCESS` crashes in release builds involving Convex data.
- Writing or reviewing any Combine pipeline that updates `@Published` properties from `client.subscribe(...)`.

## The Problem

Values from `client.subscribe(...)`, `client.mutation(...)`, and `client.action(...)` arrive on the Rust Tokio runtime thread. SwiftUI requires all UI updates on the main thread. Without `.receive(on: DispatchQueue.main)`, updating `@Published` properties causes purple runtime warnings in debug and crashes in release.

## The Fix

Add `.receive(on: DispatchQueue.main)` to every Combine pipeline that touches UI state. The recommended operator order is `.removeDuplicates()` THEN `.receive(on: DispatchQueue.main)` THEN `.sink`/`.assign`. This way deduplication runs on the background thread (more efficient for large arrays) and only the final UI update hops to main:

```swift
client.subscribe(to: "tasks:list", with: [:], yielding: [Task].self)
    .removeDuplicates()                  // runs on background thread — cheap for large arrays
    .receive(on: DispatchQueue.main)     // REQUIRED — switch to main before UI update
    .asResult()
    .sink { [weak self] result in
        switch result {
        case .success(let value):
            self?.data = value
        case .failure(let error):
            self?.error = error.localizedDescription
        }
    }
    .store(in: &cancellables)
```

## Exception: .task Modifier

SwiftUI's `.task { }` runs in a `@MainActor`-isolated context. One-shot `client.action(...)` or `client.mutation(...)` calls inside `.task` are already on the main actor. However, Combine subscriptions still need `.receive(on: DispatchQueue.main)` regardless of where the pipeline is created.

## Async Mutation/Action Calls in ViewModels

For async/await calls outside `.task`, use `MainActor.run` to update published properties:

```swift
func toggleComplete(taskId: String) async {
    do {
        try await client.mutation("tasks:toggleComplete", with: ["taskId": taskId])
    } catch {
        await MainActor.run {
            self.error = error.localizedDescription
        }
    }
}
```

## Avoid
- Omitting `.receive(on: DispatchQueue.main)` on any Combine pipeline that updates `@Published` state.
- Placing `.receive(on:)` after `.sink` — it must appear before the subscriber.
- Assuming `.task { }` isolation covers Combine subscription pipelines created inside it.
- Ignoring purple runtime warnings — they become crashes in release builds.

## Read Next
- [01-pipeline-dies-after-first-error.md](01-pipeline-dies-after-first-error.md)
- [../swiftui/01-consumption-patterns.md](../swiftui/01-consumption-patterns.md)
- [../platforms/03-performance-battery-and-threading.md](../platforms/03-performance-battery-and-threading.md)
