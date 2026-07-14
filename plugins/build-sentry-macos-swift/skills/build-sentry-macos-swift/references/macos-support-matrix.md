# macOS Support Matrix

**Read this before claiming any feature works.** A large slice of Sentry-Apple is
UIKit/iOS-only and silently absent on native AppKit macOS. The "except Mac Catalyst"
carve-outs do **not** apply to a native macOS app (Catalyst = UIKit-on-macOS, a different
target type). Verified against `docs.sentry.io/platforms/apple/guides/macos/features/` and
cross-checked with the official `getsentry/sentry-for-ai` platform matrix.
SDK floor: **9.21.0** — re-verify current.

## The matrix

| Feature | Native macOS | Notes |
|---|---|---|
| Crash reporting (Mach exceptions, signals, C++/Obj-C exceptions, `fatalError`/`assert`/`precondition`) | ✅ Yes | Default on. Report persists to disk, sent next launch. |
| Manual Swift `Error` capture | ✅ Yes | `SentrySDK.capture(error:)`. |
| Uncaught `NSException` | ⚠️ Yes — **manual opt-in** | macOS doesn't crash on uncaught NSException by default. Set `enableUncaughtNSExceptionReporting = true` (since 8.40.0). See `crash-and-hangs.md`. |
| App hang / ANR detection | ✅ Yes (v1) | `enableAppHangTracking`. **App Hangs V2** is iOS/tvOS-only. False-positives on permission dialogs — pause around them. |
| Watchdog terminations (OOM) | ❌ No | iOS/tvOS/Mac-Catalyst only. |
| Session Replay | ❌ No | Not available on macOS. |
| Screenshot attachment | ❌ No | "except Mac Catalyst". |
| View hierarchy attachment | ❌ No | "except Mac Catalyst". |
| User-interaction breadcrumbs (taps) | ❌ No | UIKit `UIControl`-based. |
| UIViewController / TTID-TTFD instrumentation | ❌ No | iOS/tvOS/Catalyst only. |
| App-start tracking (cold/warm) | ❌ No | iOS/tvOS/Catalyst only. |
| SwiftUI view tracking (`SentryTracedView`) | ✅ Yes | Base view tracking works; TTID/TTFD does not. |
| HTTP/`URLSession` auto-tracking + trace propagation | ✅ Yes | Needs `enableSwizzling` + `enableAutoPerformanceTracing` (both default on). |
| File I/O instrumentation | ✅ Yes | Auto for `NSData` pre-macOS 15; manual `Data`/`FileManager` extensions on macOS 15+ (SDK 8.48.0+). |
| Core Data instrumentation | ✅ Yes | SwiftData has **no** dedicated integration — do not assume it inherits this. |
| Transaction-based profiling (`profilesSampleRate`) | ⛔ Removed 9.0.0 | Use `configureProfiling`. |
| UI / continuous profiling (`configureProfiling`) | ✅ Yes | macOS + iOS only (not tvOS/watchOS/visionOS). |
| MetricKit integration | ✅ Yes (macOS 12+) | `enableMetricKit`. Free supplemental crash/hang/energy signal. |
| Structured logs (Sentry Logs) | ✅ Yes | `enableLogs = true`, `SentrySDK.logger.*`. GA in 9.0.0. |
| Metrics API | ✅ Yes | `enableMetrics` (default true, SDK 9.12+). |
| Release health / sessions | ✅ Yes | `enableAutoSessionTracking` (default on). |
| User feedback — API | ✅ Yes | `SentryFeedback` + `SentrySDK.capture(feedback:)`. |
| User feedback — managed widget UI | ❌ No | iOS/iPadOS (UIKit) only. Build your own AppKit form. |
| Attachments API | ✅ Yes | Use with care (PII). |
| Breadcrumbs / scope / tags / context / user | ✅ Yes | Fully available. |

## Direct consequences

- On native macOS, **do not set** `sessionReplay.*`, `attachScreenshot`,
  `attachViewHierarchy`, or expect `enableWatchdogTerminationTracking` to do anything — they
  are no-ops. Setting them explicitly to `false` is fine as defensive documentation, but
  don't present them as active features.
- **Do** the `enableUncaughtNSExceptionReporting = true` step — it's the one macOS gotcha.
- Performance value on macOS comes from **manual transactions + network tracking**, not the
  auto app-start / UIViewController machinery that never runs here.
- **Not available for Cocoa at all:** Crons (backend only), AI/LLM monitoring (JS/Python only).

## The documented contradiction (resolved)

Sentry's generic macOS quick-start snippet still includes `sessionReplay.*` and
`attach*` lines even though the Features page says those are unavailable on macOS. This is
a docs-tooling artifact. **Resolution: omit those lines on native macOS** — they can't help
and only add noise.
