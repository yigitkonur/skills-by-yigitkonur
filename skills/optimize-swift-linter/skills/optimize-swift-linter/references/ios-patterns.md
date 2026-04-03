# iOS Patterns — Swift Best Practices Reference

Opinionated patterns for iOS development. Prefer SwiftUI + SwiftData + async/await. UIKit only when necessary.

---

## 1. App Architecture

Use `@main` with `App` protocol. Bridge `UIApplicationDelegate` via `@UIApplicationDelegateAdaptor` for callbacks that SwiftUI can't handle (push token registration, BGTaskScheduler).

```swift
@main
struct MyApp: App {
    @UIApplicationDelegateAdaptor(AppDelegate.self) var delegate
    @Environment(\.scenePhase) private var phase

    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        .onChange(of: phase) { _, new in
            if new == .background { scheduleBackgroundRefresh() }
        }
    }
}

class AppDelegate: NSObject, UIApplicationDelegate {
    func application(_ app: UIApplication,
                     didFinishLaunchingWithOptions opts: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        BGTaskScheduler.shared.register(forTaskWithIdentifier: "com.app.refresh", using: nil) { task in
            handleRefresh(task as! BGAppRefreshTask)
        }
        return true
    }
    func application(_ app: UIApplication, didRegisterForRemoteNotificationsWithDeviceToken token: Data) {
        // send token to server
    }
}
```

---

## 2. Navigation

Prefer `NavigationStack` with a `NavigationPath` for programmatic control. Use `NavigationSplitView` on iPad.

```swift
// Path-based navigation — supports deep linking
@State private var path = NavigationPath()

NavigationStack(path: $path) {
    RootView()
        .navigationDestination(for: Item.self) { ItemDetailView(item: $0) }
        .navigationDestination(for: Route.self) { RouteView(route: $0) }
}

// Deep link handling
.onOpenURL { url in
    if let item = Item(url: url) { path.append(item) }
}

// iPad split view
NavigationSplitView {
    SidebarView(selection: $selection)
} detail: {
    DetailView(item: selection)
}
.navigationSplitViewStyle(.balanced)
```

---

## 3. SwiftUI for iOS

```swift
// List with swipe actions, search, pull-to-refresh
@State private var query = ""
@State private var items: [Item] = []

NavigationStack {
    List(filteredItems) { item in
        ItemRow(item: item)
            .swipeActions(edge: .trailing) {
                Button(role: .destructive) { delete(item) } label: { Label("Delete", systemImage: "trash") }
            }
            .swipeActions(edge: .leading) {
                Button { pin(item) } label: { Label("Pin", systemImage: "pin") }
                    .tint(.orange)
            }
    }
    .searchable(text: $query, prompt: "Search items")
    .refreshable { await loadItems() }  // pull-to-refresh — must be async
    .navigationTitle("Items")
}

// Sheets & covers
.sheet(isPresented: $showSheet) { SheetView() }
.fullScreenCover(isPresented: $showCover) { CoverView() }
.popover(isPresented: $showPop) { PopoverView() }  // iPad: real popover; iPhone: sheet

// Safe area & geometry — avoid GeometryReader unless truly needed
.ignoresSafeArea(.keyboard)          // extend behind keyboard
.safeAreaInset(edge: .bottom) { BottomBar() }  // prefer this over GeometryReader

// Lazy scroll — use LazyVStack inside ScrollView for variable-height items;
// use List when you need swipe actions or selection.
ScrollView {
    LazyVStack(spacing: 12) {
        ForEach(items) { ItemCard(item: $0) }
    }
    .padding()
}
```

---

## 4. UIKit Integration

```swift
// UIViewRepresentable — wrap a UIKit view
struct VideoPlayer: UIViewRepresentable {
    let player: AVPlayer
    func makeUIView(context: Context) -> AVPlayerLayer { AVPlayerLayer(player: player) }
    func updateUIView(_ view: AVPlayerLayer, context: Context) {}
}

// UIViewControllerRepresentable — with Coordinator for delegation
struct CameraView: UIViewControllerRepresentable {
    @Binding var image: UIImage?

    func makeCoordinator() -> Coordinator { Coordinator(self) }
    func makeUIViewController(context: Context) -> UIImagePickerController {
        let picker = UIImagePickerController()
        picker.sourceType = .camera
        picker.delegate = context.coordinator
        return picker
    }
    func updateUIViewController(_ vc: UIImagePickerController, context: Context) {}

    class Coordinator: NSObject, UIImagePickerControllerDelegate, UINavigationControllerDelegate {
        var parent: CameraView
        init(_ parent: CameraView) { self.parent = parent }
        func imagePickerController(_ picker: UIImagePickerController,
                                   didFinishPickingMediaWithInfo info: [UIImagePickerController.InfoKey: Any]) {
            parent.image = info[.originalImage] as? UIImage
            picker.dismiss(animated: true)
        }
    }
}
// Use UIKit for: custom gesture recognizers, complex scroll interactions, MapKit annotation clustering, camera, rich text editing.
```

---

## 5. Data Persistence

```swift
// SwiftData — preferred for new projects (iOS 17+)
@Model class Task {
    var title: String
    var isDone: Bool
    var createdAt: Date
    init(title: String) { self.title = title; isDone = false; createdAt = .now }
}

// Setup in App
.modelContainer(for: Task.self)

// In views
@Query(sort: \Task.createdAt) var tasks: [Task]
@Environment(\.modelContext) private var context

func add() { context.insert(Task(title: "New")) }
func delete(_ t: Task) { context.delete(t) }

// UserDefaults — settings only, never secrets
@AppStorage("hapticEnabled") var hapticEnabled = true

// Keychain — secrets, tokens
import Security
func saveToken(_ token: String) {
    let data = Data(token.utf8)
    let query: [String: Any] = [kSecClass as String: kSecClassGenericPassword,
                                 kSecAttrAccount as String: "authToken",
                                 kSecValueData as String: data]
    SecItemDelete(query as CFDictionary)
    SecItemAdd(query as CFDictionary, nil)
}
```

---

## 6. Networking

```swift
// Async/await with structured concurrency
actor NetworkClient {
    private let session = URLSession.shared
    private let decoder = JSONDecoder()

    func fetch<T: Decodable>(_ type: T.Type, from url: URL) async throws -> T {
        let (data, response) = try await session.data(from: url)
        guard (response as? HTTPURLResponse)?.statusCode == 200 else { throw APIError.badStatus }
        return try decoder.decode(T.self, from: data)
    }

    // Parallel requests
    func loadDashboard() async throws -> (User, [Post]) {
        async let user = fetch(User.self, from: .user)
        async let posts = fetch([Post].self, from: .posts)
        return try await (user, posts)
    }

    // Retry with exponential backoff
    func fetchWithRetry<T: Decodable>(_ type: T.Type, from url: URL, attempts: Int = 3) async throws -> T {
        for attempt in 1...attempts {
            do { return try await fetch(type, from: url) }
            catch { if attempt == attempts { throw error }
                    try await Task.sleep(for: .seconds(Double(attempt) * 2)) }
        }
        fatalError()
    }
}

// Certificate pinning — implement URLSessionDelegate.urlSession(_:didReceive:completionHandler:)
// Validate SecTrust against bundled certificate; call .cancelAuthenticationChallenge on mismatch.
```

---

## 7. Push Notifications

```swift
// Request permission + register
func registerForPush() async {
    let center = UNUserNotificationCenter.current()
    let granted = try? await center.requestAuthorization(options: [.alert, .badge, .sound])
    if granted == true { await UIApplication.shared.registerForRemoteNotifications() }
}

// Rich notification — UNNotificationServiceExtension: mutate content, download image, attach.
// Background push (content-available: 1) — handle in AppDelegate:
// application(_:didReceiveRemoteNotification:fetchCompletionHandler:) → call completion(.newData)
```

---

## 8. Background Processing

```swift
// BGAppRefreshTask — registered in AppDelegate (see §1)
func scheduleBackgroundRefresh() {
    let request = BGAppRefreshTaskRequest(identifier: "com.app.refresh")
    request.earliestBeginDate = Date(timeIntervalSinceNow: 15 * 60)
    try? BGTaskScheduler.shared.submit(request)
}

func handleRefresh(_ task: BGAppRefreshTask) {
    task.expirationHandler = { task.setTaskCompleted(success: false) }
    Task {
        await syncData()
        task.setTaskCompleted(success: true)
        scheduleBackgroundRefresh()  // reschedule
    }
}

// Background URLSession — survives app termination
let config = URLSessionConfiguration.background(withIdentifier: "com.app.bg-upload")
config.isDiscretionary = true
let bgSession = URLSession(configuration: config, delegate: self, delegateQueue: nil)
```

---

## 9. Widgets & Extensions

```swift
// WidgetKit timeline provider
struct Provider: TimelineProvider {
    func placeholder(in context: Context) -> SimpleEntry { SimpleEntry(date: .now, value: 0) }
    func getSnapshot(in context: Context, completion: @escaping (SimpleEntry) -> Void) {
        completion(SimpleEntry(date: .now, value: 42))
    }
    func getTimeline(in context: Context, completion: @escaping (Timeline<SimpleEntry>) -> Void) {
        let entries = (0..<5).map { i in
            SimpleEntry(date: Calendar.current.date(byAdding: .minute, value: i * 15, to: .now)!, value: i)
        }
        completion(Timeline(entries: entries, policy: .atEnd))
    }
}

// Live Activities (ActivityKit) — separate from WidgetKit
import ActivityKit
struct DeliveryAttributes: ActivityAttributes {
    struct ContentState: Codable, Hashable { var eta: Date }
    var orderId: String
}

let activity = try Activity<DeliveryAttributes>.request(
    attributes: DeliveryAttributes(orderId: "123"),
    content: .init(state: .init(eta: .now.addingTimeInterval(1800)), staleDate: nil)
)
```

---

## 10. Accessibility

```swift
// VoiceOver labels — always provide meaningful labels for images and icons
Image(systemName: "heart.fill")
    .accessibilityLabel("Favorite")
    .accessibilityValue(isFavorited ? "selected" : "not selected")
    .accessibilityAddTraits(.isButton)

// Dynamic Type — use .font(.body) system fonts; never hardcode sizes
Text(title).font(.headline)  // scales automatically
    .dynamicTypeSize(.small ... .accessibility2)  // optional cap

// Reduce Motion
@Environment(\.accessibilityReduceMotion) var reduceMotion
withAnimation(reduceMotion ? nil : .spring()) { show.toggle() }

// AccessibilityRotor — custom navigation for VoiceOver
.accessibilityRotor("Unread") {
    ForEach(messages.filter(\.isUnread)) { msg in
        AccessibilityRotorEntry(msg.preview, id: msg.id)
    }
}

// Group related elements
HStack { Icon(); Text("Label") }
    .accessibilityElement(children: .combine)
```

---

## 11. Performance

```swift
// AsyncImage with caching via URLCache
AsyncImage(url: url) { phase in
    switch phase {
    case .success(let img): img.resizable().scaledToFill()
    case .failure: Image(systemName: "photo")
    case .empty: ProgressView()
    @unknown default: EmptyView()
    }
}

// Avoid redraws — use Equatable, avoid passing whole model to child
struct Row: View, Equatable {
    let title: String; let subtitle: String  // primitives, not whole object
    static func == (l: Row, r: Row) -> Bool { l.title == r.title && l.subtitle == r.subtitle }
    var body: some View { /* ... */ }
}

// List vs LazyVStack
// List: built-in swipe actions, selection, separators — prefer for interactive lists
// LazyVStack: custom layouts, cards, variable spacing — prefer for feed-style UIs

// Memory: release caches in .background scene phase. Instruments: Time Profiler, Allocations, SwiftUI profiler.
```

---

## 12. App Store

```swift
// StoreKit 2 — never use SKPaymentQueue
import StoreKit

func loadProducts() async throws -> [Product] {
    try await Product.products(for: ["com.app.premium", "com.app.yearly"])
}

func purchase(_ product: Product) async throws {
    let result = try await product.purchase()
    switch result {
    case .success(let verification):
        let transaction = try verification.payloadValue
        await transaction.finish()
    case .userCancelled, .pending: break
    @unknown default: break
    }
}

// Check entitlements on launch
for await result in Transaction.currentEntitlements {
    if let transaction = try? result.payloadValue { unlock(transaction.productID) }
}

// App review prompt — call after meaningful user action, max 3x/year enforced by OS
import StoreKit
func requestReviewIfAppropriate() {
    if completedActions >= 5 { AppStore.requestReview() }
}

// App Tracking Transparency — request before any ad SDK init
import AppTrackingTransparency
let status = await ATTrackingManager.requestTrackingAuthorization()
```

---

## 13. Security

```swift
// Biometric auth
import LocalAuthentication

func authenticate() async throws -> Bool {
    let context = LAContext()
    guard context.canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, error: nil) else { return false }
    return try await context.evaluatePolicy(.deviceOwnerAuthenticationWithBiometrics,
                                            localizedReason: "Unlock your vault")
}

// CryptoKit — symmetric encryption
import CryptoKit
let key = SymmetricKey(size: .bits256)
let sealed = try AES.GCM.seal(data, using: key)
let opened = try AES.GCM.open(sealed, using: key)

// Hashing
let digest = SHA256.hash(data: data)

// ATS — enforced by default; only add exceptions with justification in Info.plist
// Never disable NSAllowsArbitraryLoads in production.
```

---

## 14. iPad-Specific

```swift
// Pointer (hover) support
.hoverEffect(.highlight)          // automatic pointer effect on iPadOS
.pointerStyle(.grabbing)          // iOS 17.5+

// Keyboard shortcuts
.keyboardShortcut("n", modifiers: .command)   // Cmd+N
.keyboardShortcut(.return, modifiers: [])

// Multiple windows (Scene)
@main struct MyApp: App {
    var body: some Scene {
        WindowGroup { ContentView() }
        WindowGroup("Detail", for: Item.ID.self) { $id in
            DetailView(itemID: id)
        }
    }
}

// Open new window
@Environment(\.openWindow) private var openWindow
Button("Open") { openWindow(value: item.id) }

// Stage Manager — use .frame(minWidth:) to set reasonable minimum
NavigationSplitView { Sidebar() } detail: { Detail() }
    .frame(minWidth: 600, minHeight: 400)  // prevents unreasonable resize
```

---

## 15. iOS SwiftUI Specifics

```swift
// Navigation bar modes
.navigationBarTitleDisplayMode(.large)      // default for root
.navigationBarTitleDisplayMode(.inline)     // for detail screens

// Toolbar — always use .toolbar, never .navigationBarItems
.toolbar {
    ToolbarItem(placement: .topBarTrailing) { Button("Add") { add() } }
    ToolbarItem(placement: .bottomBar) { Spacer() }
    ToolbarItem(placement: .bottomBar) { shareButton }
}

// Searchable — must be inside NavigationStack
.searchable(text: $query, placement: .navigationBarDrawer(displayMode: .always), prompt: "Search")
.searchSuggestions {
    ForEach(suggestions) { Text($0).searchCompletion($0) }
}

// Refreshable
.refreshable { await viewModel.refresh() }  // shows system spinner automatically

// Sensory feedback (iOS 17+)
.sensoryFeedback(.success, trigger: didComplete)
.sensoryFeedback(.impact(weight: .medium), trigger: dragOffset)

// Sheet sizing (iOS 16+)
.sheet(isPresented: $show) {
    Content()
        .presentationDetents([.medium, .large])
        .presentationDragIndicator(.visible)
        .presentationBackgroundInteraction(.enabled(upThrough: .medium))
}
```
