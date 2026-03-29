# Swift Architecture Reference

Opinionated patterns drawn from pointfreeco/swift-composable-architecture (80/100, 14.5k stars), pointfreeco/swift-dependencies (75/100), NetNewsWire (multi-target gold standard), CotEditor (clean AppKit), and AeroSpace (full SPM).

---

## 1. Architecture Selection Guide

**Default: MVVM with @Observable.** Only escalate when you hit a real pain point.

| Signal | Recommendation |
|--------|---------------|
| Solo dev, < 20 screens | MVVM + @Observable |
| Team, moderate complexity | MVVM + Coordinator + swift-dependencies |
| Large team, full testability required | TCA |
| Primarily data transformation / business rules | Clean Architecture layer separation |
| ReSwift (existing) | Migrate away — project declining, no Swift concurrency support |

**Rule:** Don't adopt TCA on a greenfield solo project. Its benefits are proportional to team size and testing surface area.

---

## 2. MVVM with @Observable

The modern default. Requires iOS 17+ / macOS 14+. No Combine needed.

```swift
import SwiftUI
import Observation

// ViewModel: @Observable class, owns all state and logic
@Observable
final class ArticleListViewModel {
    var articles: [Article] = []
    var isLoading = false
    var errorMessage: String?

    private let repository: ArticleRepository

    init(repository: ArticleRepository) {
        self.repository = repository
    }

    func loadArticles() async {
        isLoading = true
        defer { isLoading = false }
        do {
            articles = try await repository.fetchAll()
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

// View: owns the ViewModel, no @StateObject/@ObservedObject needed
struct ArticleListView: View {
    @State private var viewModel: ArticleListViewModel

    init(repository: ArticleRepository) {
        _viewModel = State(initialValue: ArticleListViewModel(repository: repository))
    }

    var body: some View {
        List(viewModel.articles) { article in
            ArticleRowView(article: article)
        }
        .overlay { if viewModel.isLoading { ProgressView() } }
        .task { await viewModel.loadArticles() }
    }
}
```

**Use MVVM when:** standard CRUD, single-platform, team < 5. **Avoid when:** many screens share overlapping state or cross-feature side effects dominate.

---

## 3. The Composable Architecture (TCA)

Add via SPM: `github.com/pointfreeco/swift-composable-architecture`. Minimum viable feature:

```swift
import ComposableArchitecture

@Reducer
struct ArticleFeature {
    @ObservableState
    struct State: Equatable {
        var articles: [Article] = []
        var isLoading = false
    }

    enum Action {
        case loadArticles
        case articlesLoaded(Result<[Article], Error>)
    }

    @Dependency(\.articleClient) var articleClient

    var body: some ReducerOf<Self> {
        Reduce { state, action in
            switch action {
            case .loadArticles:
                state.isLoading = true
                return .run { send in
                    await send(.articlesLoaded(
                        Result { try await articleClient.fetchAll() }
                    ))
                }
            case let .articlesLoaded(.success(articles)):
                state.isLoading = false
                state.articles = articles
                return .none
            case let .articlesLoaded(.failure(error)):
                state.isLoading = false
                // handle error
                return .none
            }
        }
    }
}
```

**Compose features** by embedding child State/Action and using `Scope`:

```swift
@Reducer
struct AppFeature {
    @ObservableState
    struct State { var articles = ArticleFeature.State(); var settings = SettingsFeature.State() }
    enum Action { case articles(ArticleFeature.Action); case settings(SettingsFeature.Action) }
    var body: some ReducerOf<Self> {
        Scope(state: \.articles, action: \.articles) { ArticleFeature() }
        Scope(state: \.settings, action: \.settings) { SettingsFeature() }
    }
}
```

**Test a reducer** — this is TCA's primary advantage:

```swift
@Test func loadArticlesSuccess() async {
    let store = TestStore(initialState: ArticleFeature.State()) {
        ArticleFeature()
    } withDependencies: {
        $0.articleClient.fetchAll = { [.mock] }
    }
    await store.send(.loadArticles) { $0.isLoading = true }
    await store.receive(\.articlesLoaded.success) {
        $0.isLoading = false
        $0.articles = [.mock]
    }
}
```

**TCA is overkill when:** simple forms, single-screen utilities, no shared state across features.

---

## 4. Dependency Injection

Use `swift-dependencies` (`github.com/pointfreeco/swift-dependencies`). Avoid constructor injection proliferation.

```swift
import Dependencies

// 1. Define the client interface
struct ArticleClient {
    var fetchAll: @Sendable () async throws -> [Article]
    var save: @Sendable (Article) async throws -> Void
}

// 2. Register live and test values
extension ArticleClient: DependencyKey {
    static let liveValue = ArticleClient(
        fetchAll: { try await APIService.shared.getArticles() },
        save: { try await APIService.shared.saveArticle($0) }
    )
    static let testValue = ArticleClient(
        fetchAll: { [] },
        save: { _ in }
    )
}

extension DependencyValues {
    var articleClient: ArticleClient {
        get { self[ArticleClient.self] }
        set { self[ArticleClient.self] = newValue }
    }
}

// 3. Consume via property wrapper — works in any type, not just TCA
final class ArticleViewModel {
    @Dependency(\.articleClient) var articleClient
    @Dependency(\.date) var date  // built-in: date, uuid, mainQueue, etc.
}
```

**Prefer `@Dependency` over:** singleton `shared` instances (untestable), environment object threading (breaks outside SwiftUI), or constructor injection chains deeper than 3 levels.

---

## 5. Module Structure

Follow the NetNewsWire pattern. Separate by concern, not by type.

```
MyApp/
├── Package.swift          # root SPM manifest
├── App/                   # thin entry point, no logic
│   ├── Mac/               # macOS-specific UI
│   │   └── MyAppMac.xcodeproj
│   └── iOS/               # iOS-specific UI
│       └── MyAppiOS.xcodeproj
└── Modules/
    ├── Core/              # models, protocols, no UI
    ├── Networking/        # URLSession wrappers, no UI
    ├── Database/          # persistence, no UI
    ├── FeatureArticles/   # ArticleFeature reducer + views
    ├── FeatureSettings/   # SettingsFeature reducer + views
    └── SharedUI/          # cross-platform components
```

Minimal `Package.swift` for a feature module:

```swift
let package = Package(
    name: "FeatureArticles",
    platforms: [.macOS(.v14), .iOS(.v17)],
    products: [.library(name: "FeatureArticles", targets: ["FeatureArticles"])],
    dependencies: [
        .package(url: "https://github.com/pointfreeco/swift-composable-architecture", from: "1.0.0"),
    ],
    targets: [
        .target(name: "FeatureArticles", dependencies: [
            .product(name: "ComposableArchitecture", package: "swift-composable-architecture"),
        ]),
        .testTarget(name: "FeatureArticlesTests", dependencies: ["FeatureArticles"]),
    ]
)
```

---

## 6. Navigation Architecture

**Recommendation: tree-based navigation for simple apps, stack-based for deep drill-downs.** Express navigation state as data — never call `push`/`present` imperatively from ViewModels.

```swift
// Tree-based: enum-driven modal/sheet/popover
@Observable
final class AppNavigationModel {
    var selectedArticle: Article?
    var isShowingSettings = false
    var sheet: SheetDestination?

    enum SheetDestination: Identifiable {
        case newArticle
        case editArticle(Article)
        var id: String { /* ... */ }
    }
}

// Stack-based: NavigationPath for push navigation
@Observable
final class ArticleNavigationModel {
    var path = NavigationPath()

    func showDetail(for article: Article) { path.append(article) }
    func popToRoot() { path.removeLast(path.count) }
}

// Deep link: parse URL → mutate navigation state
func handle(_ url: URL) {
    guard let articleID = url.articleID else { return }
    navigationModel.selectedArticle = articleRepository.article(id: articleID)
}
```

**In TCA:** use `@Presents` and `PresentationState` for fully-testable navigation.

---

## 7. Data Flow

Unidirectional: **State → View → Action → Reducer → State**.

```
User taps button → View sends Action → Reducer mutates State (sync) / returns Effect (async)
→ Effect calls dependency → sends another Action → Reducer mutates State → View re-renders
```

**@Observable vs ObservableObject:**
- Use `@Observable` (iOS 17+/macOS 14+) — granular per-property tracking, no `$` publishers
- Use `ObservableObject` only when targeting iOS 16 or needing Combine interop

**Bidirectional binding is OK** for: form fields, sliders, toggles that directly mirror ViewModel state. It is **not OK** for: navigation state, derived values, state shared across features.

---

## 8. Repository Pattern

Abstract data sources behind protocols. Views and ViewModels never touch URLSession or CoreData directly.

```swift
// Protocol — defined in Core module
protocol ArticleRepository: Sendable {
    func fetchAll() async throws -> [Article]
    func fetch(id: UUID) async throws -> Article
    func save(_ article: Article) async throws
    func delete(id: UUID) async throws
}

// Live implementation — in Database/Networking module
actor RemoteArticleRepository: ArticleRepository {
    private let cache = NSCache<NSUUID, CachedArticle>()
    private let api: APIClient
    private let db: DatabaseClient

    func fetchAll() async throws -> [Article] {
        // try cache, then remote, then persist
        if let cached = localCache() { return cached }
        let articles = try await api.getArticles()
        await db.store(articles)
        return articles
    }
}

// Test double — returned from DependencyKey.testValue
struct MockArticleRepository: ArticleRepository {
    var stubbedArticles: [Article] = []
    func fetchAll() async throws -> [Article] { stubbedArticles }
    func fetch(id: UUID) async throws -> Article { stubbedArticles.first! }
    func save(_: Article) async throws {}
    func delete(id: UUID) async throws {}
}
```

---

## 9. Service Layer

Networking lives in a dedicated service, never in a ViewModel. Use structured concurrency for retry/timeout.

```swift
actor NetworkService {
    private let session: URLSession
    private let baseURL: URL

    func request<T: Decodable>(_ endpoint: Endpoint) async throws -> T {
        var request = URLRequest(url: baseURL.appending(path: endpoint.path))
        request.httpMethod = endpoint.method
        request.timeoutInterval = 30

        let (data, response) = try await session.data(for: request)
        guard let http = response as? HTTPURLResponse else { throw APIError.invalidResponse }
        guard (200..<300).contains(http.statusCode) else {
            throw APIError.httpError(http.statusCode)
        }
        return try JSONDecoder.api.decode(T.self, from: data)
    }

    // Retry with exponential backoff — catch 429, sleep 2^n seconds, rethrow after max attempts
    func requestWithRetry<T: Decodable>(_ endpoint: Endpoint, attempts: Int = 3) async throws -> T {
        for attempt in 0..<attempts {
            do { return try await request(endpoint) }
            catch APIError.httpError(429) { try await Task.sleep(for: .seconds(pow(2.0, Double(attempt)))) }
        }
        return try await request(endpoint)
    }
}

enum APIError: Error {
    case invalidResponse
    case httpError(Int)
    case decodingFailed(Error)
}
```

---

## 10. Multi-Platform Architecture

Share business logic; separate UI. Never put `#if os(macOS)` inside a ViewModel.

```
Modules/Core/          → 100% shared: models, protocols, business rules
Modules/Networking/    → 100% shared: URLSession, actors
App/Mac/               → macOS UI: AppKit + SwiftUI for Mac
App/iOS/               → iOS UI: SwiftUI, UIKit where needed
```

Platform conditionals belong **only** in UI layers. Never put `#if os(macOS)` inside a ViewModel — use a protocol instead:

```swift
// Protocol hides the platform difference
protocol AppNavigator {
    func openSettings()
}
struct MacNavigator: AppNavigator {
    func openSettings() { NSApp.sendAction(#selector(AppDelegate.showSettings), to: nil, from: nil) }
}
final class iOSNavigator: AppNavigator {
    weak var navigationModel: AppNavigationModel?
    func openSettings() { navigationModel?.isShowingSettings = true }
}

// Conditional styling in ViewModifier — not in ViewModels
extension View {
    func platformListStyle() -> some View {
        #if os(macOS)
        self.listStyle(.sidebar)
        #else
        self.listStyle(.insetGrouped)
        #endif
    }
}
```

---

## 11. Feature Flags & Configuration

Keep configuration out of code. Use build configs + a typed facade.

```swift
// In a Config module shared by all targets
enum BuildConfig {
    static let isDebug: Bool = {
        #if DEBUG
        return true
        #else
        return false
        #endif
    }()
}

// Feature flags via a protocol — allows remote override
protocol FeatureFlags {
    var newEditorEnabled: Bool { get }
    var analyticsEnabled: Bool { get }
}

struct LocalFeatureFlags: FeatureFlags {
    var newEditorEnabled: Bool { BuildConfig.isDebug }
    var analyticsEnabled: Bool { !BuildConfig.isDebug }
}

// Wire via swift-dependencies
extension LocalFeatureFlags: DependencyKey {
    static let liveValue = LocalFeatureFlags()
}
extension DependencyValues {
    var featureFlags: any FeatureFlags {
        get { self[LocalFeatureFlags.self] }
        set { /* override in tests */ }
    }
}
```

**Never** put feature flag checks directly in Views. Put them in ViewModels or Reducers where they can be tested.

---

## 12. Modular Project Setup

**Recommendation: vanilla SPM for pure Swift packages, Tuist for multi-target Xcode projects.**

- **SPM only** — works when all targets are Swift frameworks/executables. No Xcode project management.
- **Tuist** — generates `xcodeproj` from `Project.swift`. Best for teams. Eliminates merge conflicts in `.pbxproj`.
- **XcodeGen** — alternative to Tuist; `project.yml` based. Simpler but less powerful.
- **CocoaPods/Carthage** — do not start new projects with these.

Tuist minimal setup for a feature module:

```swift
// Tuist/Project.swift
let project = Project(
    name: "FeatureArticles",
    targets: [
        .target(
            name: "FeatureArticles",
            destinations: [.mac, .iPhone],
            product: .framework,
            bundleId: "com.example.FeatureArticles",
            sources: ["Sources/**"],
            dependencies: [.external(name: "ComposableArchitecture")]
        ),
        .target(
            name: "FeatureArticlesTests",
            destinations: [.mac, .iPhone],
            product: .unitTests,
            bundleId: "com.example.FeatureArticlesTests",
            sources: ["Tests/**"],
            dependencies: [.target(name: "FeatureArticles")]
        ),
    ]
)
```

**Key rule:** every feature module must have a corresponding test target. If it doesn't, it won't be tested.
