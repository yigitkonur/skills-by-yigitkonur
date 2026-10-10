# Architecture: Swift & Apple Ecosystem (macOS, iOS, visionOS)

Complete guide for instrumenting Apple platform applications (macOS, iOS, iPadOS, watchOS, tvOS, visionOS) using Sentry Cocoa SDK (`sentry-cocoa`), Swift Concurrency, App Hang tracking, MetricKit, and SwiftUI view tracing.

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

            // App Hang Tracking (detects main-thread UI hangs)
            options.enableAppHangTracking = true
            options.appHangTimeoutInterval = 2.0 // Report hangs exceeding 2 seconds

            // Apple MetricKit (crashes, CPU/battery diagnostics, disk writes)
            #if os(iOS) || os(macOS)
            options.enableMetricKit = true
            #endif

            // Watchdog & Out-of-Memory (OOM) tracking
            options.enableWatchdogTerminationTracking = true

            // Continuous Profiling
            options.profilesSampleRate = 1.0

            // Mobile Session Replay with strict privacy
            #if os(iOS)
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

## 3. SwiftUI View Tracing

Trace view lifecycle and rendering transitions automatically using `.sentryTrace`:

```swift
import SwiftUI
import Sentry

struct ContentView: View {
    @State private var items: [String] = []

    var body: some View {
        NavigationStack {
            List(items, id: \.self) { item in
                Text(item)
            }
            .navigationTitle("Dashboard")
        }
        // Instruments view load and attach duration as a span in Sentry
        .sentryTrace("ContentView")
        .task {
            await loadData()
        }
    }

    private func loadData() async {
        // Custom span for asynchronous work
        let span = SentrySDK.span?.startChild(operation: "data.fetch", description: "Fetch user items")
        defer { span?.finish(status: .ok) }

        do {
            // Outbound network call automatically traced by Sentry Network Tracking
            let (data, _) = try await URLSession.shared.data(from: URL(string: "https://api.example.com/items")!)
            self.items = try JSONDecoder().decode([String].self, from: data)
        } catch {
            span?.finish(status: .internalError)
            SentrySDK.capture(error: error) { scope in
                scope.setTag(value: "data_fetch_failed", key: "error_type")
            }
        }
    }
}
```

## 4. Key Apple Diagnostics Tracked by Sentry

| Diagnostic Mechanism | What It Captures | Configuration Flag |
|---|---|---|
| **App Hangs** | Main thread blocked > 2s by synchronous I/O or heavy computation. | `options.enableAppHangTracking = true`<br>`options.appHangTimeoutInterval = 2.0` |
| **MetricKit** | Apple OS-level crash reports, energy consumption, CPU spikes, thermal state. | `options.enableMetricKit = true` |
| **Watchdog OOM** | OS killed the app due to memory limit or slow startup without throwing an exception. | `options.enableWatchdogTerminationTracking = true` |
| **Network Tracking** | Full HTTP request/response spans and distributed `sentry-trace` headers. | `options.enableNetworkTracking = true` (default) |
| **File I/O Tracking** | Disk read/write operations exceeding thresholds. | `options.enableFileIOTracking = true` (default) |
| **User Interactions** | Touch gestures, button taps, and keyboard events as breadcrumbs. | `options.enableUserInteractionTracing = true` |

## 5. Offline Storage & Guaranteed Envelopes

On mobile and macOS devices, network connectivity drops frequently:
- Sentry Cocoa automatically buffers envelopes to encrypted local disk storage when offline.
- When network connectivity returns, buffered envelopes are drained and sent in background threads without blocking UI.
- No custom offline queue wrappers are required.

## 6. Debug Symbols (dSYMs) Uploading

To de-symbolicate crash stacks, upload dSYMs in your Xcode Archive build phase or CI:

```bash
# Sentry CLI dSYM upload script for Xcode Run Script phase
if which sentry-cli >/dev/null; then
  export SENTRY_ORG="your-org"
  export SENTRY_PROJECT="your-project"
  ERROR=$(sentry-cli debug-files upload --include-sources "$DWARF_DSYM_FOLDER_PATH" 2>&1 >/dev/null)
  if [ ! $? -eq 0 ]; then
    echo "warning: sentry-cli - $ERROR"
  fi
fi
```
