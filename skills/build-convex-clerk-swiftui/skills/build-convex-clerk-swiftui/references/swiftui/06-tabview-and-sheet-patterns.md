# TabView And Sheet Patterns

## Use This When
- Building a tabbed interface where subscriptions must persist across tab switches.
- Presenting sheets or modals that need their own subscription lifecycle.
- Debugging blank screens or re-subscription churn on tab switch or sheet dismiss.

## TabView Cancellation Behavior

TabView **eagerly initializes** all tab views on first render, so `.task` fires on all tabs immediately. However, switching tabs **cancels** `.task` on deselected tabs. This means subscriptions in `.task` are torn down every time the user switches away and rebuilt when they switch back.

### What `.task` Does Wrong In Tabs

```swift
// DON'T — subscription dies on every tab switch
struct MessagesTab: View {
    @State var messages: [Message] = []
    var body: some View {
        List(messages) { Text($0.body) }
            .task {
                for await msgs in client.subscribe(
                    to: "messages:list",
                    with: [:],
                    yielding: [Message].self
                ).values {
                    messages = msgs
                }
            }
    }
}
```

Every tab switch cancels and re-creates the subscription. This causes wasted bandwidth, momentary blank screens, and unnecessary server load.

### Safe Pattern: @StateObject Above The TabView

```swift
struct MainTabView: View {
    @StateObject private var messagesVM = MessagesViewModel()
    @StateObject private var workoutsVM = WorkoutsViewModel()

    var body: some View {
        TabView {
            MessagesTab()
                .environmentObject(messagesVM)
                .tabItem { Label("Messages", systemImage: "message") }
            WorkoutsTab()
                .environmentObject(workoutsVM)
                .tabItem { Label("Workouts", systemImage: "figure.run") }
        }
    }
}
```

`@StateObject` ViewModels with subscriptions in `init()` persist across tab switches because the object is owned by the parent view, not the tab content. The ViewModels subscribe once and stay alive for the lifetime of the tab container.

## Sheet And Modal Lifecycle

Sheets follow standard view lifecycle rules:
- `.task` starts on presentation and cancels on dismissal.
- `@StateObject` inside a sheet is **created fresh** each time the sheet is presented.
- When the sheet is dismissed, both `.task` and the `@StateObject` are torn down.

### Sheet With Editor Pattern

```swift
struct ParentView: View {
    @State private var showEditor = false

    var body: some View {
        Button("Add Item") { showEditor = true }
            .sheet(isPresented: $showEditor) {
                EditorSheet()
            }
    }
}

struct EditorSheet: View {
    @StateObject var vm = EditorViewModel()  // fresh per presentation
    @Environment(\.dismiss) var dismiss

    var body: some View {
        NavigationStack {
            Form { /* editing fields bound to vm */ }
                .toolbar {
                    ToolbarItem(placement: .confirmationAction) {
                        Button("Save") {
                            vm.save()
                            dismiss()
                        }
                    }
                }
        }
    }
}
```

### Sheet Data Rules

| Need | Pattern |
|------|---------|
| Sheet needs its own subscription | `.task` inside the sheet — cancelled on dismiss, which is correct |
| Sheet needs parent data | Pass via `@EnvironmentObject` or initializer — do not duplicate the subscription |
| Sheet fires a mutation | Fire-and-forget from the sheet ViewModel — subscribe to the result elsewhere |
| Sheet needs fresh state each presentation | `@StateObject` inside the sheet view — re-created each time |

## Combining Tabs With Sheets

When a tab presents a sheet, the tab's `@StateObject` subscription stays alive while the sheet is open. The sheet's own `.task` or `@StateObject` handles sheet-scoped work independently.

```swift
struct WorkoutsTab: View {
    @EnvironmentObject var workoutsVM: WorkoutsViewModel
    @State private var showEditor = false

    var body: some View {
        List(workoutsVM.workouts) { workout in
            WorkoutRow(workout: workout)
        }
        .toolbar {
            Button("Add") { showEditor = true }
        }
        .sheet(isPresented: $showEditor) {
            WorkoutEditorSheet()  // gets its own fresh @StateObject
        }
    }
}
```

## Avoid
- Placing persistent subscriptions in `.task` inside tab content views — they will be cancelled on every tab switch.
- Assuming tab views stay "alive" when deselected — SwiftUI cancels their `.task` modifiers.
- Duplicating parent subscriptions inside sheets instead of passing data via environment or initializer.
- Expecting `@StateObject` inside a sheet to survive across present/dismiss cycles — it is re-created each time.

## Read Next
- [05-navigation-stack-subscription-lifecycle.md](05-navigation-stack-subscription-lifecycle.md)
- [03-lifecycle-navigation-tabs-and-sheets.md](03-lifecycle-navigation-tabs-and-sheets.md)
- [02-observation-and-ownership.md](02-observation-and-ownership.md)
