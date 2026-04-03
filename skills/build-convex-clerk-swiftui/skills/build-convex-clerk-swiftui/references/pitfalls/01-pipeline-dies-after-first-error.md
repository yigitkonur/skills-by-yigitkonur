# Pipeline Dies After First Error

## Use This When
- Debugging a subscription that silently stops updating after a transient error.
- Reviewing any Combine pipeline built on `client.subscribe(...)`.
- Choosing an error-handling strategy for production subscriptions.

## The Problem

Combine publishers from `client.subscribe(...)` have a failure type of `ClientError`. Per Combine's contract, once a publisher emits `.failure`, it is **permanently terminated**. No more values. Ever.

Transient network errors, server-side throws, validation failures, and auth token expiry all produce `ClientError`. After any of these, the subscription pipeline stops permanently.

## Why `.replaceError(with:)` Makes It Worse

`.replaceError(with:)` emits the replacement value then **completes** the publisher. The subscription stops receiving updates. The code looks correct at first glance, but the UI silently freezes on stale data.

```swift
// BROKEN: Looks safe, actually kills the subscription
client.subscribe(to: "tasks:list", with: [:], yielding: [Task].self)
    .receive(on: DispatchQueue.main)
    .replaceError(with: [])  // Emits [] then COMPLETES. Dead.
    .sink { tasks in
        self.tasks = tasks   // Receives [] once, then never fires again
    }
    .store(in: &cancellables)
```

## The Fix: Result-Wrapping + Resubscribe

Wrap the output in `Result` so errors become values instead of completions. The error is visible as UI state. However, `.catch` still terminates the upstream, so you must call `resubscribe()` to resume live updates.

```swift
extension Publisher {
    func asResult() -> AnyPublisher<Result<Output, Failure>, Never> {
        self
            .map { Result<Output, Failure>.success($0) }
            .catch { error in Just(Result<Output, Failure>.failure(error)) }
            .eraseToAnyPublisher()
    }
}
```

Usage on every subscription:

```swift
client.subscribe(to: "tasks:list", with: [:], yielding: [Task].self)
    .receive(on: DispatchQueue.main)
    .removeDuplicates()
    .asResult()
    .sink { [weak self] result in
        switch result {
        case .success(let tasks):
            self?.tasks = tasks
            self?.error = nil
        case .failure(let error):
            self?.error = error.localizedDescription
            // Tasks remain at last known good value
            // Pipeline completes after this — call resubscribe() to resume live updates
        }
    }
    .store(in: &cancellables)
```

## Pipeline Lifecycle

```
Without Result-wrapping:
  Value -> Value -> Error -> [DEAD — no more values ever]

With .replaceError(with:):
  Value -> Value -> Error -> Fallback -> [COMPLETE — no more values ever]

With Result-wrapping:
  Value -> Value -> Error(as value) -> [COMPLETE]
  [ERROR VISIBLE AS UI STATE — pipeline completes, call resubscribe() to resume live updates]
```

> **Note:** `.catch` (used inside `asResult()`) always terminates the upstream publisher after emitting the wrapped error. The pipeline does NOT stay alive. To resume live updates, you must call `resubscribe()` — cancel all existing cancellables and rebuild the subscription pipeline from scratch. Result-wrapping is better than `.replaceError` because the error is visible as UI state, but it does not magically keep the stream open.

## Avoid
- Using `.replaceError(with:)` on any subscription publisher — it completes the stream.
- Using bare `.catch` without re-wrapping — same terminal semantics.
- Assuming the Rust transport layer will prevent all errors from reaching the Combine pipeline.
- Skipping `.asResult()` on subscriptions that "probably won't error" — transient failures happen in production.

## Read Next
- [../client-sdk/03-subscriptions-errors-logging-and-connection-state.md](../client-sdk/03-subscriptions-errors-logging-and-connection-state.md)
- [../swiftui/01-consumption-patterns.md](../swiftui/01-consumption-patterns.md)
- [../platforms/01-ios-backgrounding-reconnection-and-staleness.md](../platforms/01-ios-backgrounding-reconnection-and-staleness.md)
