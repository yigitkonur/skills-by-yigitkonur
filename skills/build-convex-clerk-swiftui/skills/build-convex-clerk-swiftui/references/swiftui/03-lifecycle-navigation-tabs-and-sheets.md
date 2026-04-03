# SwiftUI Lifecycle, Navigation, Tabs, And Sheets

## Use This When
- Deciding where a subscription should live.
- Debugging data loss or duplicate work during navigation changes.
- Explaining why a screen-level `.task` stopped updating.

## Authoritative Lifecycle Rules
- SwiftUI cancels `.task` when a view disappears or changes identity.
- `NavigationStack` pushes can cancel the source view's task.
- `TabView` does cancel `.task` on tab switch even though tabs may still be eagerly initialized.
- Sheets and modals also cancel view-scoped work when dismissed.

## Navigation Pattern (Official Example)

The official WorkoutTracker example uses `NavigationStack(path:)` with a separate `NavigationModel`:

```swift
class NavigationModel: ObservableObject {
  @Published var path: [WorkoutsPage.SubPages] = []
  func openEditor() { path.append(.workoutEditor) }
  func closeEditor() { path.removeAll() }
}

struct WorkoutsPage: View {
  enum SubPages { case workoutEditor }

  @StateObject var workoutsModel = WorkoutsModel()
  @StateObject var navigationModel = NavigationModel()

  var body: some View {
    NavigationStack(path: $navigationModel.path) {
      VStack {
        WorkoutList()
        Button("Add Workout", action: navigationModel.openEditor)
      }
      .navigationDestination(for: SubPages.self) { _ in
        WorkoutEditorPage()
      }
      .toolbar {
        ToolbarItem(placement: .topBarTrailing) {
          UserButton()  // ClerkKitUI: signed-in user management
        }
      }
    }
    .environmentObject(workoutsModel)
    .environmentObject(navigationModel)
  }
}
```

Key patterns:
- **Separate `NavigationModel`**: navigation state is an `ObservableObject`, not inline `@State`. This lets child views trigger navigation programmatically.
- **`@EnvironmentObject`**: both `WorkoutsModel` and `NavigationModel` are injected as environment objects so child views can access them without prop drilling.
- **`navigationDestination(for:)`**: type-safe routing for pushed destinations.
- **Feature models own subscriptions**: `WorkoutsModel` subscribes in `init()` and survives navigation changes because it's owned by `@StateObject`.
- **`UserButton()`** from `ClerkKitUI` in the toolbar provides signed-in user management.

## Placement Rules
- Put view-scoped reads in `.task` only when cancellation on disappearance is acceptable.
- Put durable live data in a `@StateObject` model when the data must survive navigation, tabs, or sheet churn.
- Put auth and app-wide session state above feature navigation boundaries.

## Parameter Changes
- Use `.task(id:)` or `switchToLatest` when the active query inputs change.
- Let identity changes cancel old work intentionally instead of layering manual cleanup over unstable ownership.
- The official example uses `.switchToLatest()` for reactive subscription parameters (see swiftui/01-consumption-patterns.md).

## Cleanup Guidance
- Manual `onDisappear` cleanup is an edge tool, not a first resort.
- First fix ownership. Only then add explicit cleanup for rare cases that truly need it.

## Avoid
- Assuming macOS hide/show behavior matches iOS navigation behavior.
- Assuming a tab switch leaves a view-task alive because the tab view itself still exists.
- Recreating important subscriptions on every push/pop cycle.
- Mixing navigation state into feature data models — keep them separate as the official example does.

## Read Next
- [01-consumption-patterns.md](01-consumption-patterns.md)
- [02-observation-and-ownership.md](02-observation-and-ownership.md)
- [../platforms/04-macos-multi-window-menu-bar-and-support-limits.md](../platforms/04-macos-multi-window-menu-bar-and-support-limits.md)
