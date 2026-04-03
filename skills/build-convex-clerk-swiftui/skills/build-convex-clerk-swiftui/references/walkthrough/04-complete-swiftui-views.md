# Complete SwiftUI Views

## Use This When
- Building the SwiftUI view layer for a Convex + Clerk app.
- Need a complete, copy-pasteable set of views from app entry point through auth gate to chat UI.
- Reviewing the correct way to wire `AuthView()`, `UserButton()`, and subscription-backed views.

---

## App Entry Point

```swift
import ClerkConvex
import ClerkKit
import ClerkKitUI
import ConvexMobile
import SwiftUI

@MainActor
let client = ConvexClientWithAuth(
    deploymentUrl: Env.convexDeploymentUrl,
    authProvider: ClerkConvexAuthProvider()
)

@main
struct ChatApp: App {
    init() {
        Clerk.configure(publishableKey: Env.clerkPublishableKey)
        #if DEBUG
        initConvexLogging()
        #endif
    }

    var body: some Scene {
        WindowGroup {
            LandingPage()
                .prefetchClerkImages()
                .environment(Clerk.shared)
        }
    }
}
```

---

## LandingPage (Auth Gate)

```swift
struct LandingPage: View {
    @State private var authState: AuthState<String> = .loading
    @State private var authViewIsPresented = false

    var body: some View {
        Group {
            switch authState {
            case .loading:
                ProgressView("Loading...")
            case .unauthenticated:
                VStack(spacing: 20) {
                    Image(systemName: "message.fill")
                        .font(.system(size: 60))
                    Text("My Chat App").font(.largeTitle)
                    Button("Sign In") { authViewIsPresented = true }
                        .buttonStyle(.borderedProminent)
                }
            case .authenticated:
                MainTabView()
            }
        }
        .sheet(isPresented: $authViewIsPresented) {
            AuthView()  // Clerk's prebuilt auth -- all flows handled
        }
        .task {
            for await state in client.authState.values {
                authState = state
            }
        }
    }
}
```

---

## MainTabView

```swift
struct MainTabView: View {
    @StateObject var channelListVM = ChannelListViewModel()
    @StateObject var connectionVM = ConnectionViewModel()

    var body: some View {
        ZStack(alignment: .top) {
            TabView {
                ChannelListView()
                    .environmentObject(channelListVM)
                    .tabItem { Label("Channels", systemImage: "message") }
                ProfileView()
                    .tabItem { Label("Profile", systemImage: "person") }
            }

            if !connectionVM.isConnected {
                ConnectionBanner()
            }
        }
    }
}
```

---

## ChannelListView

```swift
struct ChannelListView: View {
    @EnvironmentObject var vm: ChannelListViewModel

    var body: some View {
        NavigationStack {
            List(vm.channels) { channel in
                NavigationLink(value: channel) {
                    Text(channel.name)
                }
            }
            .navigationTitle("Channels")
            .navigationDestination(for: Channel.self) { channel in
                ChannelView(channelId: channel.id)
            }
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    UserButton()  // Clerk's prebuilt sign-out / profile UI
                }
            }
        }
    }
}
```

---

## ChannelView (Messages + Compose)

```swift
struct ChannelView: View {
    @StateObject private var vm: ChannelViewModel
    @State private var messageText = ""

    init(channelId: String) {
        _vm = StateObject(wrappedValue: ChannelViewModel(channelId: channelId))
    }

    var body: some View {
        VStack {
            // Message list
            ScrollViewReader { proxy in
                List(vm.messages) { msg in
                    MessageBubble(message: msg)
                        .id(msg.id)
                }
                .onChange(of: vm.messages.count) { _, _ in
                    if let last = vm.messages.last {
                        withAnimation { proxy.scrollTo(last.id, anchor: .bottom) }
                    }
                }
            }

            // Compose bar
            HStack {
                TextField("Message", text: $messageText)
                    .textFieldStyle(.roundedBorder)
                    .onSubmit { send() }

                Button(action: send) {
                    Image(systemName: "arrow.up.circle.fill")
                        .font(.title2)
                }
                .disabled(vm.isSending || messageText.isEmpty)
            }
            .padding()
        }
        .navigationTitle("Chat")
    }

    private func send() {
        let text = messageText
        messageText = ""
        vm.send(body: text)
    }
}
```

---

## MessageBubble

```swift
struct MessageBubble: View {
    let message: Message

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(message.body)
        }
    }
}
```

---

## ConnectionBanner

```swift
struct ConnectionBanner: View {
    @State private var isConnected = true

    var body: some View {
        Group {
            if !isConnected {
                HStack(spacing: 6) {
                    ProgressView().scaleEffect(0.7)
                    Text("Reconnecting...").font(.caption).fontWeight(.medium)
                }
                .padding(.horizontal, 12).padding(.vertical, 6)
                .background(.orange.opacity(0.9))
                .foregroundStyle(.white)
                .clipShape(Capsule())
                .transition(.move(edge: .top).combined(with: .opacity))
            }
        }
        .task {
            for await state in client.watchWebSocketState().values {
                isConnected = state == .connected
            }
        }
    }
}
```

---

## ProfileView

```swift
struct ProfileView: View {
    var body: some View {
        NavigationStack {
            Text("Profile")
                .navigationTitle("Profile")
                .toolbar {
                    ToolbarItem(placement: .topBarTrailing) {
                        UserButton()
                    }
                }
        }
    }
}
```

---

## Pipeline Termination Warning

ViewModels using `.replaceError(with:)` will stop receiving updates after the first error. For production, use `Result`-wrapping or explicit `sink`. See [../client-sdk/03-subscriptions-errors-logging-and-connection-state.md](../client-sdk/03-subscriptions-errors-logging-and-connection-state.md).

## Avoid
- Building custom sign-in/sign-out UI -- use `AuthView()` and `UserButton()` from `ClerkKitUI`.
- Forgetting `.prefetchClerkImages()` on the root view -- causes avatar loading delays.
- Forgetting `.environment(Clerk.shared)` on the root view -- Clerk views crash without it.
- Using `@ObservedObject` where `@StateObject` is needed for ViewModels.
- Omitting `#if DEBUG` guard around `initConvexLogging()` -- logs expose JWTs in production.

## Read Next
- [03-complete-swift-models-and-viewmodels.md](03-complete-swift-models-and-viewmodels.md)
- [05-deployment-checklist.md](05-deployment-checklist.md)
- [../swiftui/01-consumption-patterns.md](../swiftui/01-consumption-patterns.md)
- [../swiftui/02-observation-and-ownership.md](../swiftui/02-observation-and-ownership.md)
