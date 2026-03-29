# Per-Window ViewModels And The @StateObject Gotcha

## Use This When
- Building a macOS app with multiple windows that need independent state.
- Debugging why all windows show identical selection, scroll position, or expanded/collapsed state.
- Deciding what to share process-wide versus what to isolate per window.

## The Problem

If you declare a `@StateObject` ViewModel in your `App` struct, it is created **once** for the entire process. Every window shares that single instance. On macOS, this means all windows display identical state and mutating the ViewModel in one window mutates it in all windows.

```swift
// BAD: Shared across ALL windows
@main
struct MyApp: App {
    @StateObject private var viewModel = TaskListViewModel()  // ONE instance

    var body: some Scene {
        WindowGroup {
            ContentView(viewModel: viewModel)  // Every window gets same VM
        }
    }
}
```

Open two windows — they both show the same selection, same scroll position, same expanded/collapsed state.

## The Fix: Declare ViewModels Inside The View Hierarchy

Move `@StateObject` declarations into the view that each window instantiates. SwiftUI creates a new `@StateObject` for each window's view instance.

```swift
import ClerkKit
import ClerkConvex
import ConvexMobile
import SwiftUI

@MainActor
let client = ConvexClientWithAuth(
    deploymentUrl: Env.convexDeploymentUrl,
    authProvider: ClerkConvexAuthProvider()
)

@main
struct MyMacApp: App {
    init() {
        Clerk.configure(publishableKey: Env.clerkPublishableKey)
    }

    var body: some Scene {
        WindowGroup {
            ContentView()  // No ViewModel passed from App
                .prefetchClerkImages()
                .environment(Clerk.shared)
        }
    }
}

struct ContentView: View {
    // Each window gets its OWN instance
    @StateObject private var viewModel = TaskListViewModel()

    var body: some View {
        List(viewModel.tasks, selection: $viewModel.selectedTaskId) { task in
            TaskRow(task: task)
        }
        .task {
            viewModel.startSubscription()
        }
    }
}
```

Now each window has independent selection, independent scroll state, and independent ViewModel lifecycle.

## What Gets Shared Versus Per-Window

| Layer | Sharing | Where To Declare |
|-------|---------|-----------------|
| `ConvexClientWithAuth` | Shared (one WebSocket) | Module-level `let client` |
| Auth state | Shared (one session) | Module-level client, auth gate above windows |
| Subscription data | Shared at WebSocket level | ViewModel (but data from server is identical) |
| Selection state | Per-window | `@StateObject` in View |
| Navigation state | Per-window | `@StateObject` in View |
| UI-specific state | Per-window | `@State` / `@StateObject` in View |

## Per-Window ViewModel Pattern

Even though data is shared at the WebSocket level, each window's ViewModel holds its own Combine subscription. This is efficient — the Rust client deduplicates identical subscriptions internally and only maintains one WebSocket subscription per unique function+arguments pair.

```swift
import Combine
import ConvexMobile

class TaskListViewModel: ObservableObject {
    @Published var tasks: [TaskItem] = []
    @Published var selectedTaskId: String?
    @Published var error: String?

    private var cancellables = Set<AnyCancellable>()

    func startSubscription() {
        client.subscribe(to: "tasks:list", with: [:], yielding: [TaskItem].self)
            .receive(on: DispatchQueue.main)
            .removeDuplicates()
            .sink(
                receiveCompletion: { [weak self] completion in
                    if case .failure(let error) = completion {
                        self?.error = error.localizedDescription
                    }
                },
                receiveValue: { [weak self] tasks in
                    self?.tasks = tasks
                }
            )
            .store(in: &cancellables)
    }
}
```

## @Observable Macro — Same Problem

The `@Observable` macro (macOS 14+) has the same issue. If you create it in the App struct with `@State`, it is shared across all windows.

```swift
// BAD with @Observable too
@main
struct MyApp: App {
    @State private var viewModel = TaskListViewModel()  // Shared!
    // ...
}
```

Fix is the same: create `@Observable` objects inside the view hierarchy, not at the App level.

## When Shared State Is Correct

Some state should intentionally be shared across all windows:
- Auth status (logged in / out)
- User profile
- App-wide settings
- Unread notification count

For these, declare at the App level with full intention:

```swift
@main
struct MyMacApp: App {
    @StateObject private var appSettings = AppSettingsManager()  // Intentionally shared

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(appSettings)
                .environment(Clerk.shared)
        }
    }
}
```

## Avoid
- Declaring feature-specific `@StateObject` ViewModels in the `App` struct — they will be shared across all windows unintentionally.
- Assuming `@Observable` solves this — the same placement rules apply.
- Forgetting that `MenuBarExtra` content shares the App-level scope — per-menu-bar state needs the same view-level ownership pattern.
- Passing the module-level `client` via environment when direct access is simpler — the module-level `let client` pattern means ViewModels can reference it directly.

## Read Next
- [04-macos-multi-window-menu-bar-and-support-limits.md](04-macos-multi-window-menu-bar-and-support-limits.md)
- [../swiftui/04-environment-injection-and-root-architecture.md](../swiftui/04-environment-injection-and-root-architecture.md)
- [../swiftui/02-observation-and-ownership.md](../swiftui/02-observation-and-ownership.md)
