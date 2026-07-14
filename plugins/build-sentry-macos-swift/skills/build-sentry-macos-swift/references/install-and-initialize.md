# Install & Initialize

SDK floor **9.21.0** (verified 2026-07); re-check current before writing options.

## Install (choose by Phase 1's dependency signal)

**SPM inside an `.xcodeproj`** (common; no `Package.swift`): Xcode → **File ▸ Add Package
Dependencies…** → URL:

```
https://github.com/getsentry/sentry-cocoa.git
```

**`Package.swift` manifest:**

```swift
.package(url: "https://github.com/getsentry/sentry-cocoa", from: "9.21.0"),
```

### Pick exactly ONE product, added to the app target

| Product | Use it? | Why |
|---|---|---|
| **`Sentry`** | ✅ Default | Static, prebuilt, fastest start; includes SwiftUI APIs (9.4.1+). |
| `Sentry-Dynamic` | Only if dynamic linking required | |
| `SentrySwiftUI` | ❌ | Deprecated (9.4.1) — folded into `Sentry`. |
| `Sentry-WithoutUIKitOrAppKit` | Headless/CLI/watchOS (Swift < 6.1) | |
| `SentrySPM` + `NoUIFramework` trait | Headless on Swift 6.1+ / Xcode 26.4+ | Source build; module is `SentrySwift`. |
| `SentryObjC` | Pure Obj-C/C++ without Clang modules | Rename `Sentry*` → `SentryObjC*`. |

- **CocoaPods** is deprecated (last publish ~mid-2026); migrate to SPM.
- Commit `Package.resolved` so clean builds get the same SDK.

## Initialize — on the main thread, earliest point

Place `SentrySDK.start` at the earliest point of the lifecycle detected in Phase 1, so it's
armed before any early crash (e.g. storage/container setup that can `fatalError`).

**SwiftUI `App`:**

```swift
import SwiftUI
import Sentry

@main
struct MyApp: App {
    init() {
        SentryIntegration.startIfEnabled()   // first line — see privacy-and-scrubbing.md for the gate + scrubbers
        // ...rest of init
    }
    var body: some Scene { WindowGroup { ContentView() } }
}
```

**AppKit `AppDelegate`:**

```swift
func applicationDidFinishLaunching(_ notification: Notification) {
    SentryIntegration.startIfEnabled()
}
```

Keep config in one file so the opt-in gate and scrubbers live together:

```swift
import Sentry

enum SentryIntegration {
    static func startIfEnabled() {
        // Opt-in gate — default OFF for any app touching user data. See privacy-and-scrubbing.md.
        guard UserDefaults.standard.bool(forKey: "diagnosticsEnabled") else { return }

        SentrySDK.start { options in
            options.dsn = "https://<publicKey>@<org>.ingest.sentry.io/<projectId>"  // client key, safe to embed
            options.environment = "production"        // map from build config
            // releaseName auto = bundleID@shortVersion+build — leave unset (matches Sparkle appcast).

            // macOS crash correctness
            options.enableUncaughtNSExceptionReporting = true

            // Privacy floor (see privacy-and-scrubbing.md)
            options.sendDefaultPii = false
            options.attachScreenshot = false          // no-op on macOS, defensive
            options.attachViewHierarchy = false       // no-op on macOS, defensive
            options.maxBreadcrumbs = 20
            options.enableNetworkBreadcrumbs = false  // URLs may carry sensitive params
            options.enableCaptureFailedRequests = false
            options.beforeSend = SentryScrub.event
            options.beforeBreadcrumb = SentryScrub.breadcrumb

            // Performance — opt in deliberately (see tracing-releases-dsym.md)
            options.tracesSampleRate = 0.0            // raise consciously, e.g. 0.2

            #if DEBUG
            options.debug = true                      // verbose SDK logs; never ship on
            options.environment = "development"
            #endif
        }
    }
}
```

> This is a **privacy-first** starting point and deliberately differs from the official
> pack's iOS-liberal defaults (`sendDefaultPii = true`, screenshots on). For an app handling
> user content, this posture is correct; loosen only with a reason.

## SentryOptions reference (macOS-relevant subset)

| Option | Default | macOS note |
|---|---|---|
| `dsn` | required | Client key. macOS also reads `SENTRY_DSN` env var if unset. |
| `environment` | `"production"` | Freeform. |
| `releaseName` | auto `bundleID@version+build` | Leave unset — already matches Sparkle. |
| `dist` | unset | Optional = `CFBundleVersion`. Not needed for symbolication (that's UUID-based). |
| `debug` | `false` | DEBUG only. |
| `sendDefaultPii` | `false` | Keep false. Does **not** stop the `{{auto}}` IP on Apple — handle server-side. |
| `enableCrashHandler` | `true` | Keep. |
| `enableUncaughtNSExceptionReporting` | `false` | **Set true on macOS.** |
| `enableAppHangTracking` | `true` | v1 on macOS. |
| `appHangTimeoutInterval` | `2.0` | Seconds. |
| `attachStacktrace` | `true` | Adds stack to messages; low PII risk on compiled app. |
| `maxBreadcrumbs` | `100` | Lower to shrink leak surface. |
| `enableNetworkBreadcrumbs` | `true` | Turn **off** for privacy. |
| `enableCaptureFailedRequests` | `true` | Turn **off** for privacy. |
| `tracesSampleRate` | `nil` (off) | Set > 0 to enable tracing. |
| `tracePropagationTargets` | all requests | Narrow to your backend host. |
| `enableSwizzling` | `true` | Needed for network/file auto-tracking. |
| `enableAutoPerformanceTracing` | `true` | Master auto-instrumentation switch. |
| `enableMetricKit` | `false` | Consider `true` (macOS 12+). |
| `enableLogs` | `false` | Structured logs. |
| `enableMetrics` | `true` (9.12+) | Swift metrics API. |
| `configureProfiling` | none | `{ $0.sessionSampleRate = ...; $0.lifecycle = .trace }`. |
| `beforeSend` / `beforeBreadcrumb` | none | **Set the scrubbers.** |

**Removed in 9.0.0 — do NOT use:** `profilesSampleRate`, `profilesSampler`, `integrations`,
`defaultIntegrations`, `enableTracing`, `enablePerformanceV2`, `inAppExclude` (use
`add(inAppInclude:)`), `enableAppHangTrackingV2` (V2 is default where supported).

## Gotchas

- **Init must be on the main thread.**
- **Crash handlers don't install under a debugger** — verify with "Debug executable"
  unchecked (see `verify-and-troubleshoot.md`).
- Non-sandboxed apps cache pending events in `~/Library/Caches/io.sentry/` — don't let a
  cleanup routine delete it at runtime.
- The **Sentry Wizard** (`sentry-wizard -i ios`) automates iOS setup but must be run by the
  user (interactive browser login); its macOS flag support is unconfirmed — prefer manual
  SPM + this init for a macOS target.
