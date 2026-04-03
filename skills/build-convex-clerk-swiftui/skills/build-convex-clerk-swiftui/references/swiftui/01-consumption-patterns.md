# SwiftUI Consumption Patterns

## Use This When
- Choosing how a view or view model should consume a Convex subscription.
- Comparing `.task`, `sink`, `assign`, `.onReceive`, or `switchToLatest`.
- Teaching a SwiftUI team which patterns are defaults versus convenience options.

## Recommended Default
- Use `ObservableObject` models owned by `@StateObject` for long-lived or important subscriptions.
- Use `sink` when you need explicit completion handling or multiple side effects.
- Use `assign(to: &$property)` when the subscription can write directly into `@Published` state and losing the cancellable handle is desirable.

## Concrete Example: Reactive Parameters (Adapted From Official WorkoutTracker)

The official WorkoutTracker example shows the canonical Combine subscription pattern for a parameterized live query. The snippet below is a teaching-friendly adaptation of that structure:

```swift
@MainActor
class WorkoutsModel: ObservableObject {
  @Published var workouts: [Workout] = []
  @Published var selectedStartOfWeek: Date

  init() {
    // Compute start of current week (actual example uses inline calendar math)
    let dayOfWeek = Calendar.current.component(.weekday, from: Date.now)
    selectedStartOfWeek = calendar.date(
      byAdding: .day, value: dayTranslation[dayOfWeek]!, to: Date.now)!

    // When selectedStartOfWeek changes, switch to a new subscription
    $selectedStartOfWeek
      .map { week in
        client.subscribe(
          to: "workouts:getInRange",
          with: [
            "startDate": week.localIso8601DateFormat(),
            "endDate": calendar.date(byAdding: .day, value: 6, to: week)!
              .localIso8601DateFormat(),
          ]
        )
        .removeDuplicates()           // skip if data unchanged
        .replaceError(with: [])       // ⚠️ PROTOTYPE ONLY — kills pipeline after first error. See pitfalls/01.
        .receive(on: DispatchQueue.main) // UI thread
        .eraseToAnyPublisher()
      }
      .switchToLatest()               // cancel old subscription, use new
      .assign(to: &$workouts)         // bind to @Published
  }
}
```

This single pipeline handles:
- **Parameter reactivity**: when `selectedStartOfWeek` changes, `.map` creates a new subscription.
- **Automatic cancellation**: `.switchToLatest()` cancels the previous subscription.
- **Deduplication**: `.removeDuplicates()` avoids redundant view updates.
- **Error fallback**: `.replaceError(with: [])` converts a failure in the current inner publisher into a fallback value. It does not keep that failing subscription alive; a new upstream parameter change is what creates a fresh subscription later.
- **Main thread delivery**: `.receive(on: DispatchQueue.main)` ensures UI safety.
- **Direct binding**: `.assign(to: &$workouts)` ties the subscription to `@Published` state.

## Simple View-Scoped Option

```swift
.task {
  for await state in client.authState.values {
    authState = state
  }
}
```

- Use `.task { for await publisher.values }` for smaller screens whose data should end when the view disappears.
- Use `.task(id:)` when query arguments change and the old task should cancel automatically.
- Keep this pattern for view-scoped state, not app-critical shared state.
- The official example uses this for `authState` observation at the root landing page.

## Other Useful Patterns
- `.onReceive` is acceptable for light iOS 13+ cases where a view needs a direct hook into a publisher.
- `switchToLatest` is the preferred pattern when the selected query inputs live in published state and can change over time.
- Result-wrapped streams are useful when the UI must keep failure state visible.

## Selection Rules
- If the screen must survive navigation churn, own the subscription in a model.
- If the query is parameterized by current state, reach for `switchToLatest` or `.task(id:)`.
- If the UI must display terminal failure, do not hide it behind `replaceError`.
- If multiple consumers need the same value, prefer app or feature state over ad hoc hot-stream fan-out.

## Avoid
- Treating `.task` as the default for data that must outlive the view.
- Assuming `assign(to:)` gives you a place to react to failures after the fact.
- Solving duplicate owner problems with more Combine operators instead of cleaner ownership.
- Forgetting `.removeDuplicates()` before `.replaceError()` — without it, every server push triggers a view update even if data is unchanged.

## Read Next
- [02-observation-and-ownership.md](02-observation-and-ownership.md)
- [03-lifecycle-navigation-tabs-and-sheets.md](03-lifecycle-navigation-tabs-and-sheets.md)
- [../advanced/01-pagination-live-tail-and-history.md](../advanced/01-pagination-live-tail-and-history.md)
