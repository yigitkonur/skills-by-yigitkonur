# Crash Capture & App Hangs on macOS

## What the crash handler catches (native macOS)

`SentryCrashIntegration` (on by default) captures: Mach exceptions, fatal POSIX signals,
C++ exceptions, Objective-C exceptions, and `fatalError`/`assert`/`precondition`. Start-up
crashes are handled too (init blocks up to 5s to flush if the app crashes within ~2s of
start). This covers container/storage `fatalError` paths, native audio/media crashes, and
crashes in linked C/C++ dependencies.

**Delivery:** the report persists to disk and is sent on the **next launch** (best-effort
immediate send usually fails mid-crash). For Sparkle-updated apps, the update-and-relaunch
cycle is exactly when a pending crash flushes.

**Hardened Runtime / non-sandbox / notarization:** no special entitlement is required.
Signal/Mach-port handler installation is intra-process. The non-sandbox case only changes
the cache path (`~/Library/Caches/`). dSYMs are built before signing, so notarization
doesn't affect them. This is **doc-confirmed but not empirically universal** — run the
smoke test in `verify-and-troubleshoot.md` on a real signed build once.

**What no reporter can catch:** OS security-terminations (stack buffer overflow,
code-signature failures) kill the process before any handler runs.

## The macOS must-do: uncaught NSException

macOS does **not** crash on an uncaught `NSException` by default — AppKit swallows it and
the app limps on. Without an opt-in, a whole class of Cocoa errors produces **no event**.

```swift
options.enableUncaughtNSExceptionReporting = true   // since 8.40.0
```

- This is the right path for **SwiftUI + `NSApplicationDelegateAdaptor`** apps (can't easily
  use the principal-class approach).
- The alternative is setting the Info.plist Principal class to
  `SentryCrashExceptionApplication`. **Mutually exclusive** — enabling both duplicates
  reports. Prefer the option.

## Manual capture at failure boundaries

Crashes are automatic; **handled** errors you must route. Capture at known boundaries
(storage fallback, network clients, media/file processing) — metadata only, through the
scrubber:

```swift
do {
    try risky()
} catch {
    SentrySDK.capture(error: error) { scope in
        scope.setTag(value: "network", key: "subsystem")   // fixed vocabulary, no user text
        scope.setTag(value: String(statusCode), key: "http.status")
    }
    throw error
}
```

## App hangs — and the permission-dialog trap

`enableAppHangTracking` (default on, v1 on macOS) fires an event when the main thread is
unresponsive ≥ `appHangTimeoutInterval` (2.0s). Useful for catching main-thread blocking
(sync file conversion, blocking network).

**The trap:** macOS **system permission dialogs** (microphone, accessibility, screen
capture, automation) block the main thread and look like hangs. Sentry can't distinguish
them. Bracket any code that raises a system prompt:

```swift
SentrySDK.pauseAppHangTracking()
requestMicrophoneOrAccessibilityPermission()   // shows a modal system dialog
SentrySDK.resumeAppHangTracking()
```

Don't disable hang tracking globally to dodge false positives — pause narrowly. Audit the
repo for permission-request sites (from Phase 1) and wrap them.

## The debugger caveat

Neither crash handlers nor hang tracking install while a debugger is attached. Any crash
test run from Xcode with the debugger on is **silently not captured**. Test with **"Debug
executable" unchecked** in the scheme's Run action.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| Crashes never appear | Debugger attached — uncheck "Debug executable". |
| Uncaught NSException swallowed | `enableUncaughtNSExceptionReporting` not set. |
| Duplicate crash reports | Both the option AND the principal-class swap enabled — pick one. |
| Hang events on permission prompts | Wrap with `pause`/`resumeAppHangTracking()`. |
| Watchdog/OOM never tracked | Not available on native macOS (matrix). |
