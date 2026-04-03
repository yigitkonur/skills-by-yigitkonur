# Subscription Placement Decision Matrix

## Use This When
- Deciding where to start a Convex subscription in SwiftUI (`.task`, `@StateObject`, or `@EnvironmentObject`).
- Debugging subscriptions that cancel prematurely or leak as zombies.
- Reviewing lifecycle behavior differences between the three patterns.

## The Three Patterns

SwiftUI offers three places to start a Convex subscription. Each has different lifecycle behavior. Choosing wrong causes either premature cancellation or zombie subscriptions.

## Decision Matrix

```
+---------------------+-----------+----------+----------+----------------------+
| Pattern             | Cancels   | Cancels  | Survives | Best For             |
|                     | on nav    | on tab   | app      |                      |
|                     | pop?      | switch?  | restart? |                      |
+---------------------+-----------+----------+----------+----------------------+
| .task { }           | YES       | YES      | NO       | Simple screens,      |
|                     |           |          |          | detail views         |
+---------------------+-----------+----------+----------+----------------------+
| @StateObject VM     | NO*       | NO*      | NO       | List screens,        |
|                     |           |          |          | production VMs       |
+---------------------+-----------+----------+----------+----------------------+
| @EnvironmentObject  | NO        | NO       | NO       | Auth state,          |
|                     |           |          |          | connection status    |
+---------------------+-----------+----------+----------+----------------------+

* @StateObject survives as long as the SwiftUI view identity persists.
  NavigationStack keeps parent views alive, so the VM survives child pushes.
  TabView keeps all tabs alive, so VMs survive tab switches.
```

## Pattern 1: .task { } (View-Scoped)

The subscription lives exactly as long as the view is on screen.

```swift
struct ChannelDetailView: View {
    let channelId: String
    @State private var messages: [Message] = []
    @State private var cancellables = Set<AnyCancellable>()

    var body: some View {
        List(messages) { msg in
            Text(msg.body)
        }
        .task {
            client.subscribe(
                to: "messages:list",
                with: ["channelId": channelId],
                yielding: [Message].self
            )
            .receive(on: DispatchQueue.main)
            .sink(
                receiveCompletion: { _ in },
                receiveValue: { self.messages = $0 }
            )
            .store(in: &cancellables)
        }
    }
}
```

**When it cancels:**
- User taps Back (NavigationStack pops) -> cancels
- Parent view disappears -> cancels
- Tab switches away (if not in NavigationStack) -> cancels

**Use when:**
- The data is only relevant while viewing this specific screen
- You want automatic cleanup with no manual lifecycle management
- Prototype or simple app with few screens

**Do not use when:**
- You need the subscription to survive navigation to a child view
- You need shared state across multiple views

## Pattern 2: @StateObject ViewModel (VM-Scoped)

The subscription lives as long as the ViewModel, which lives as long as the view identity exists in the SwiftUI hierarchy.

```swift
@MainActor
final class ChannelViewModel: ObservableObject {
    @Published var messages: [Message] = []
    private var cancellables = Set<AnyCancellable>()

    let channelId: String

    init(channelId: String) {
        self.channelId = channelId
    }

    func subscribe() {
        client.subscribe(
            to: "messages:list",
            with: ["channelId": channelId],
            yielding: [Message].self
        )
        .receive(on: DispatchQueue.main)
        .sink(
            receiveCompletion: { _ in },
            receiveValue: { [weak self] in self?.messages = $0 }
        )
        .store(in: &cancellables)
    }
}

struct ChannelView: View {
    @StateObject private var viewModel: ChannelViewModel

    init(channelId: String) {
        _viewModel = StateObject(
            wrappedValue: ChannelViewModel(channelId: channelId)
        )
    }

    var body: some View {
        List(viewModel.messages) { msg in
            Text(msg.body)
        }
        .task { viewModel.subscribe() }
    }
}
```

**When it cancels:**
- View identity is destroyed (removed from NavigationStack entirely)
- ViewModel is deallocated

**Does NOT cancel when:**
- Child view is pushed onto NavigationStack (parent stays alive)
- Tab switches (TabView keeps all root views alive)

**Use when:**
- Production apps where you need reliable subscription lifecycle
- Screens with complex state (loading, error, data)
- Views that push child views but should keep receiving updates

## Pattern 3: @EnvironmentObject (App-Scoped)

The subscription lives for the entire app session. Inject at the root.

```swift
@MainActor
final class AuthModel: ObservableObject {
    @Published var isSignedIn = false
    private var cancellables = Set<AnyCancellable>()

    func observe() {
        client.authState
            .receive(on: DispatchQueue.main)
            .sink { [weak self] state in
                self?.isSignedIn = state == .authenticated
            }
            .store(in: &cancellables)
    }
}

// Root of the app
@main
struct MyApp: App {
    @StateObject private var authModel = AuthModel()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(authModel)
                .task { authModel.observe() }
        }
    }
}
```

**When it cancels:**
- App is terminated
- Never cancels during normal navigation

**Use when:**
- Auth state (every screen needs to know if user is signed in)
- WebSocket connection status (show banner anywhere)
- Current user profile (available everywhere)

**Do not use when:**
- Data is screen-specific (wastes resources to keep alive globally)

## When to Use Each Pattern

```
+--------------------------------+--------------------------+
| Scenario                       | Pattern                  |
+--------------------------------+--------------------------+
| Auth state                     | @EnvironmentObject       |
| Connection banner              | @EnvironmentObject       |
| Current user profile           | @EnvironmentObject       |
| Channel list                   | @StateObject             |
| Message list in a channel      | @StateObject             |
| Member list                    | @StateObject             |
| Quick detail popup             | .task { }                |
| Search results                 | .task { }                |
| One-shot data fetch            | .task { } + .first()     |
+--------------------------------+--------------------------+
```

## Common Mistakes

| Mistake | Symptom | Fix |
|---------|---------|-----|
| `.task` for list screen | Data disappears on child push | Use `@StateObject` |
| `@ObservedObject` instead of `@StateObject` | VM recreated on re-render | Use `@StateObject` |
| EnvironmentObject for per-screen data | Zombie subscriptions | Use `@StateObject` |
| Missing `.receive(on: DispatchQueue.main)` | Purple runtime warning | Add it to every subscription |
| Using `.replaceError(with:)` | Subscription silently dies | Use `sink` with error handling |

## Pipeline Termination Warning

> **WARNING:** `.replaceError(with:)` terminates the publisher permanently after the first error. Regardless of which pattern you choose, the subscription will never emit again after an error if you use this operator. Always use explicit error handling in `sink(receiveCompletion:receiveValue:)`.

## API Reminder

```swift
subscribe(to:with:yielding:) -> AnyPublisher<T, ClientError>
mutation(_:with:) async throws -> T
action(_:with:) async throws -> T
```

Every `Decodable` model must have `CodingKeys` with `case id = "_id"`.

## Avoid
- Using `.task { }` for list screens where the subscription must survive child navigation pushes.
- Using `@ObservedObject` where `@StateObject` is needed -- the VM will be recreated on every re-render.
- Injecting screen-specific data via `@EnvironmentObject` -- creates zombie subscriptions that waste resources.
- Omitting `.receive(on: DispatchQueue.main)` -- Combine publishers from the Convex SDK deliver on background threads.
- Using `.replaceError(with:)` in production -- silently kills the subscription pipeline on first error.

## Read Next
- [04-function-decision-tree.md](04-function-decision-tree.md)
- [../swiftui/01-consumption-patterns.md](../swiftui/01-consumption-patterns.md)
- [../swiftui/02-observation-and-ownership.md](../swiftui/02-observation-and-ownership.md)
- [../swiftui/03-lifecycle-navigation-tabs-and-sheets.md](../swiftui/03-lifecycle-navigation-tabs-and-sheets.md)
