# Architecture: Swift & Apple Ecosystem (macOS, iOS, visionOS)

Complete guide for instrumenting Apple platform applications (macOS, iOS, iPadOS, watchOS, tvOS, visionOS) using Sentry Cocoa SDK (`sentry-cocoa`), Swift Concurrency, MetricKit, App Hang tracking, and SwiftUI view performance monitoring.

---

## 1. Installation via Swift Package Manager (SPM)

In Xcode: **File > Add Package Dependencies...**
Repository URL: `https://github.com/getsentry/sentry-cocoa.git`
Select `Sentry` (or `Sentry-Dynamic`).

Or in `Package.swift`:
```swift
dependencies: [
    .package(url: "https://github.com/getsentry/sentry-cocoa.git", from: "8.40.0")
],
targets: [
    .target(
        name: "MyApp",
        dependencies: [
            .product(name: "Sentry", package: "sentry-cocoa")
        ]
    )
]
```

---

## 2. Initialization in SwiftUI (`App.swift`)

Initialize Sentry at the earliest application launch point:

```swift
import SwiftUI
import Sentry

@main
struct MyApp: App {
    init() {
        SentrySDK.start { options in
            options.dsn = ProcessInfo.processInfo.environment["SENTRY_DSN"] ?? "https://public@sentry.example.com/1"
            options.environment = "production"
            options.debug = false // Set to true only in local debug builds

            // Tracing & Spans
            options.tracesSampleRate = 1.0

            // System-level OS diagnostics & Crashes (Apple MetricKit)
            #if os(iOS) || os(macOS)
            options.enableMetricKit = true
            #endif

            // macOS Uncaught NSException reporting (mandatory on macOS; do NOT combine with SentryCrashExceptionApplication)
            #if os(macOS)
            options.enableUncaughtNSExceptionReporting = true
            #endif

            // App Hang Tracking (detects main-thread UI hangs)
            // NOTE: Sentry recommends migrating to MetricKit for hang diagnostics.
            // Disable for App Clips, Widgets, and Live Activities.
            options.enableAppHangTracking = true
            options.appHangTimeoutInterval = 2.0 // Report hangs exceeding 2 seconds

            // Watchdog & Out-of-Memory (OOM) tracking
            options.enableWatchdogTerminationTracking = true

            // Continuous Profiling / UI Profiling
            options.profilesSampleRate = 1.0

            // Mobile Session Replay with strict privacy controls
            // NOTE: Session Replay is supported on iOS and tvOS. It is NOT available on native macOS desktop.
            #if os(iOS) || os(tvOS)
            options.sessionReplay.sessionSampleRate = 0.1
            options.sessionReplay.onErrorSampleRate = 1.0
            options.sessionReplay.maskAllText = true
            options.sessionReplay.maskAllImages = true
            #endif

            // Offline caching: Sentry buffers envelopes to disk when offline
            options.maxCacheItems = 30
        }
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}
```

---

## 3. SwiftUI View Performance: Traced Views, TTID & TTFD

### Primary Container: `SentryTracedView`

The recommended approach to monitor view performance is wrapping your views in `SentryTracedView`:

```swift
import SwiftUI
import Sentry

struct ContentView: View {
    @State private var items: [String] = []

    var body: some View {
        SentryTracedView("ContentView") {
            NavigationStack {
                List(items, id: \.self) { item in
                    Text(item)
                }
                .navigationTitle("Dashboard")
            }
        }
    }
}
```

Alternatively, use the modifier syntax:
```swift
List(items, id: \.self) { item in
    Text(item)
}
.sentryTrace("DashboardList")
```

### Time to Initial Display (TTID) & Time to Full Display (TTFD)

Available since Sentry Cocoa SDK 8.44.0 (iOS and tvOS):
- **TTID (`ui.load.initial-display`):** Automatically tracked when the view appears on screen via `onAppear`.
- **TTFD (`ui.load.full-display`):** Measures when async content is fully loaded. Pass `waitForFullDisplay: true` and manually signal completion:

```swift
struct FeedView: View {
    @State private var posts: [Post] = []

    var body: some View {
        SentryTracedView("FeedView", waitForFullDisplay: true) {
            List(posts) { post in
                PostRow(post: post)
            }
            .task {
                posts = await fetchPosts()
                // Explicitly report when all asynchronous data is rendered
                SentrySDK.reportFullyDisplayed()
            }
        }
    }
}
```

---

## 4. App Hangs vs. MetricKit Architecture Notice

> [!WARNING]
> Sentry officially announced that standalone thread-based App Hang tracking (`enableAppHangTracking`) is deprecated and scheduled for removal in Cocoa SDK v10 in favor of **Apple MetricKit** (`options.enableMetricKit = true`).
> - **Why?** MetricKit uses OS-level power/hang telemetry directly from Apple with zero false positives.
> - **Widget Guidelines:** Never enable thread-based App Hang tracking in Widgets or Live Activities.
> - **Permission Dialogs:** When opening iOS system permission dialogs (e.g. pasteboard, camera, location), pause hang tracking with `SentrySDK.pauseAppHangTracking()` and resume with `SentrySDK.resumeAppHangTracking()`.

---

## 5. Capturing Errors with Rich Swift Breadcrumbs

```swift
do {
    try processTransaction()
} catch {
    SentrySDK.capture(error: error) { scope in
        scope.setTag(value: "checkout", key: "flow")
        scope.setContext(value: [
            "cart_size": cart.items.count,
            "payment_method": "apple_pay"
        ], key: "checkout_state")
    }
}
```

---

## 6. Dedicated macOS AppKit & SwiftUI Blueprint

For native macOS desktop applications, specific architectural invariants apply:
- **Uncaught `NSException` Reporting**: Must enable `options.enableUncaughtNSExceptionReporting = true` so `NSApplication` runloop does not swallow unhandled exceptions.
- **App Sandbox**: Sandboxed macOS apps MUST declare `com.apple.security.network.client = true` in `.entitlements` to allow outbound envelope delivery.
- **Platform Scope**: Native macOS desktop does not support Session Replay.
- **Classic AppKit & CLI Helpers**: Detailed AppDelegate lifecycles, XPC daemon flushes, and Xcode dSYM upload scripts.

See the dedicated blueprint: [`references/architectures/macos-appkit-swiftui.md`](file:///Users/mac/dev/skills-by-yigitkonur/skills/use-sentry/references/architectures/macos-appkit-swiftui.md).

