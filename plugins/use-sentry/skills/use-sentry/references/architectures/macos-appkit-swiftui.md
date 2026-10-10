# Architecture: macOS AppKit & SwiftUI Native Integration

Comprehensive guide for architecting production-grade Sentry observability in native macOS desktop applications using `sentry-cocoa`, AppKit, SwiftUI, Apple MetricKit, App Sandbox entitlements, and automated dSYM symbolication.

---

## 1. Architectural Overview & System Model

macOS desktop applications execute within a distinct OS environment characterized by AppKit runloops, Mach kernel exception ports, POSIX signals, and strict App Sandbox kernel enforcement.

```
┌────────────────────────────────────────────────────────┐
│                   macOS Application                    │
│  ┌───────────────────────┐  ┌───────────────────────┐  │
│  │   SwiftUI Interface   │  │   AppKit Controller   │  │
│  │   (SentryTracedView)  │  │   (NSViewController)  │  │
│  └───────────┬───────────┘  └───────────┬───────────┘  │
│              ▼                          ▼              │
│                 NSApplication Event Loop               │
│  ┌──────────────────────────────────────────────────┐  │
│  │ enableUncaughtNSExceptionReporting = true        │  │
│  │ (Sets NSApplicationCrashOnExceptions UserDefault) │  │
│  └───────────────────────┬──────────────────────────┘  │
├──────────────────────────┼─────────────────────────────┤
│                          ▼                             │
│     Sentry Cocoa SDK (`sentry-cocoa` SPM / Mach)      │
│     - Mach Kernel Exception Port Handlers             │
│     - POSIX Signal Handlers (SIGABRT, SIGSEGV, SIGBUS) │
│     - MetricKit Diagnostics (macOS 12+ MXMetricManager)│
│     - Standalone App Start Tracing (`app.launch`)      │
├────────────────────────────────────────────────────────┤
│                          ▼                             │
│       App Sandbox (`com.apple.security.app-sandbox`)   │
│       [REQUIRED: com.apple.security.network.client]   │
│                          │                             │
│                          ▼ HTTPS Envelope              │
│             Sentry Edge (`sentry.io`)                 │
└────────────────────────────────────────────────────────┘
```

---

## 2. Installation via Swift Package Manager (SPM)

The official, supported installation mechanism for modern macOS targets is Swift Package Manager.

### In Xcode:
1. Navigate to **File > Add Package Dependencies...**
2. Enter repository URL: `https://github.com/getsentry/sentry-cocoa.git`
3. Dependency Rule: **Up to Next Major Version** from `8.40.0`.
4. Add the `Sentry` library product to your macOS app target.

### In `Package.swift`:
```swift
// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "MyMacApp",
    platforms: [.macOS(.v12)],
    dependencies: [
        .package(url: "https://github.com/getsentry/sentry-cocoa.git", from: "8.40.0")
    ],
    targets: [
        .target(
            name: "MyMacApp",
            dependencies: [
                .product(name: "Sentry", package: "sentry-cocoa")
            ]
        )
    ]
)
```

---

## 3. Crucial macOS Runtime Mechanics: Uncaught `NSException` Reporting

### The Silent Swallowing Problem
Unlike iOS (which immediately terminates on uncaught exceptions), the macOS `NSApplication` runloop catches unhandled `NSException` instances by default, logs them to `NSLog`, and continues execution.
- **The Failure Mode**: The application enters an undefined, corrupted state. Neither Mach exception handlers nor POSIX signal handlers (`SIGABRT`) trigger, and **zero crash reports reach Sentry**.

### Solution: Enable Uncaught NSException Reporting
To guarantee uncaught `NSException` events crash the app and generate crash reports, Sentry provides two mutually exclusive mechanisms:

#### Option 1: `enableUncaughtNSExceptionReporting` (Recommended)
Available since Cocoa SDK v8.40.0. Enables automatic crashing via swizzling by setting the `NSApplicationCrashOnExceptions` UserDefault:

```swift
options.enableUncaughtNSExceptionReporting = true
```

#### Option 2: `SentryCrashExceptionApplication` (Info.plist Alternative)
If method swizzling is disabled (`enableSwizzling = false`), modify your app's `Info.plist`:
- Locate the **Principal class** key (`NSPrincipalClass`).
- Replace default `NSApplication` with `SentryCrashExceptionApplication`.

> [!CAUTION]
> **MANDATORY ANTI-DUPLICATION RULE:**
> Never enable `options.enableUncaughtNSExceptionReporting = true` AND set `SentryCrashExceptionApplication` in `Info.plist` simultaneously. Using both produces duplicate crash reports for every unhandled exception. Choose Option 1 unless swizzling is strictly prohibited.

---

## 4. App Sandbox Entitlements & Network Security

When distributing via the Mac App Store or enabling the macOS App Sandbox, the operating system isolates your binary from network sockets by default.

### Mandatory Outbound Network Entitlement
In your `.entitlements` file (e.g. `MyMacApp.entitlements`), ensure `com.apple.security.network.client` is enabled:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <!-- App Sandbox Isolation -->
    <key>com.apple.security.app-sandbox</key>
    <true/>
    
    <!-- MANDATORY: Outbound HTTP/HTTPS connections to Sentry's edge -->
    <key>com.apple.security.network.client</key>
    <true/>
</dict>
</plist>
```

> [!IMPORTANT]
> If `com.apple.security.network.client` is omitted, all HTTP envelope requests sent by Sentry's background transport fail with kernel permission denied (`EPERM`), leaving the app with zero telemetry.

---

## 5. Platform Boundaries: Session Replay Unsupported on Native macOS

> [!WARNING]
> **Session Replay is NOT available for native macOS applications.**
> Sentry Session Replay is officially supported on iOS, tvOS, and web platforms. Do not attempt to configure `options.sessionReplay` on macOS targets. Attempting to initialize replay on macOS is a no-op and may produce compiler warnings.

---

## 6. Initialization Blueprints

Initialize the Sentry SDK at the earliest lifecycle moment on the **main thread**.

### Pattern A: Modern Pure SwiftUI macOS App (`@main App`)

```swift
// MyMacApp.swift
import SwiftUI
import Sentry

@main
struct MyMacApp: App {
    init() {
        SentrySDK.start { options in
            options.dsn = Bundle.main.infoDictionary?["SENTRY_DSN"] as? String
                ?? ProcessInfo.processInfo.environment["SENTRY_DSN"]
                ?? "https://examplePublicKey@o0.ingest.sentry.io/0"
            
            // Release & Environment tracking
            options.environment = "production"
            options.releaseName = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String
            options.dist = Bundle.main.infoDictionary?["CFBundleVersion"] as? String
            
            // Distributed Tracing (Spans & HTTP Propagation)
            options.tracesSampleRate = 1.0
            
            // Uncaught NSException Crash Delivery (Mandatory on macOS)
            options.enableUncaughtNSExceptionReporting = true
            
            // Apple MetricKit (macOS 12+ OS Diagnostic & Hang Payloads)
            options.enableMetricKit = true
            
            // Continuous & Launch Profiling
            options.profilesSampleRate = 1.0
            options.configureProfiling = { profileOptions in
                profileOptions.lifecycle = .trace
            }
            
            // Watchdog & Out-of-Memory (OOM) Termination Tracking
            options.enableWatchdogTerminationTracking = true
            
            // Network & File I/O Tracing
            options.enableNetworkTracking = true
            options.enableFileIOTracking = true
            
            // Offline caching capacity
            options.maxCacheItems = 50
        }
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}
```

### Pattern B: Classic AppKit Application (`NSApplicationDelegate`)

```swift
// AppDelegate.swift
import Cocoa
import Sentry

@main
class AppDelegate: NSObject, NSApplicationDelegate {

    func applicationWillFinishLaunching(_ notification: Notification) {
        SentrySDK.start { options in
            options.dsn = "https://examplePublicKey@o0.ingest.sentry.io/0"
            options.enableUncaughtNSExceptionReporting = true
            options.enableMetricKit = true
            options.tracesSampleRate = 1.0
            options.profilesSampleRate = 1.0
        }
    }

    func applicationDidFinishLaunching(_ aNotification: Notification) {
        // Main window setup
    }

    func applicationWillTerminate(_ aNotification: Notification) {
        // Guaranteed flush on clean quit
        SentrySDK.flush(timeout: 2.0)
    }
}
```

---

## 7. View Performance & App Start Tracing

### SwiftUI View Tracing: `SentryTracedView`
Wrap your primary window contents or detail panes in `SentryTracedView`:

```swift
import SwiftUI
import Sentry

struct ContentView: View {
    @State private var documents: [String] = []

    var body: some View {
        SentryTracedView("MainDashboardView", waitForFullDisplay: true) {
            NavigationSplitView {
                SidebarView()
            } detail: {
                DocumentListView(documents: documents)
                    .task {
                        documents = await loadDocuments()
                        // Signal full content render completion
                        SentrySDK.reportFullyDisplayed()
                    }
            }
        }
    }
}
```

### App Start Metrics (`app.launch`)
Sentry Cocoa SDK tracks cold and warm startup times as a standalone transaction (`app.launch`).
- **Cold Start**: Application launched from disk without existing memory state.
- **Warm Start**: Application launched while cached in system memory.
- **System Pre-Warming**: On macOS 12+, the system may pre-warm processes prior to user launch (`activePrewarm`). Sentry automatically accounts for pre-warming timestamps to prevent inflated launch durations.

---

## 8. Apple MetricKit vs. Thread Hang Tracking

> [!IMPORTANT]
> **Thread-based App Hang Tracking (`enableAppHangTracking`) is deprecated** in Cocoa SDK v9 and scheduled for removal in v10.
> On macOS 12+ Monterey, **Apple MetricKit** (`options.enableMetricKit = true`) is the canonical diagnostic engine:
> - Directly receives OS-level diagnostics (`MXDiagnosticPayload`) from Apple's WindowServer.
> - Captures non-responsive UI hangs, CPU burn spikes, disk write quotas, and fatal terminations with zero thread-polling overhead and zero false positives.

---

## 9. macOS CLI Binaries, Daemons & Helper Tools

When building companion command-line utilities, helper daemons, or LaunchAgents in Swift:
- **The Problem**: CLI processes exit immediately when execution completes. Async HTTP envelopes in Sentry's queue will be terminated before transmission.
- **The Invariant**: Wrap execution and always call `SentrySDK.flush(timeout:)` or `SentrySDK.close()` before process termination:

```swift
// main.swift (CLI or Helper Binary)
import Foundation
import Sentry

SentrySDK.start { options in
    options.dsn = ProcessInfo.processInfo.environment["SENTRY_DSN"]
    options.tracesSampleRate = 1.0
}

defer {
    // Guarantee async envelopes leave memory before exit
    SentrySDK.flush(timeout: 3.0)
    SentrySDK.close()
}

do {
    try runCliTask()
} catch {
    SentrySDK.capture(error: error)
    exit(1)
}
```

---

## 10. Automated dSYM Uploads in Xcode

To symbolicate memory addresses into human-readable Swift function names, file paths, and line numbers, configure an Xcode build phase.

### Xcode Build Settings Requirement
Under your app target's **Build Settings**:
- Set **Debug Information Format (`DEBUG_INFORMATION_FORMAT`)** to **"DWARF with dSYM File"** (at least for `Release` configurations).

### Xcode Run Script Phase
Under **Build Phases > + > New Run Script Phase** (position this AFTER "Compile Sources" and "Copy Bundle Resources"):

```bash
if which sentry-cli >/dev/null; then
  # SENTRY_AUTH_TOKEN should be set in ~/.sentryclirc or CI environment
  sentry-cli debug-files upload --include-sources "$DWARF_DSYM_FOLDER_PATH"
else
  echo "warning: sentry-cli not found, skipping dSYM upload"
fi
```

---

## 11. Testing Crash Reporting (The Xcode Debugger Trap)

When testing crash capture locally:
1. **The Trap**: If you run your macOS app from Xcode with the LLDB debugger attached (`Cmd + R`), LLDB intercepts Mach exceptions (`EXC_BAD_ACCESS`) and POSIX signals (`SIGABRT`) before Sentry's crash handlers can write the crash envelope to disk.
2. **The Verification Protocol**:
   - In Xcode, go to **Product > Scheme > Edit Scheme...**
   - Select **Run (Debug)** in the left sidebar.
   - Under the **Info** tab, **uncheck "Debug executable"**.
   - Run the app, trigger a test crash (`SentrySDK.crash()`), restart the app, and verify the crash report appears in Sentry.
