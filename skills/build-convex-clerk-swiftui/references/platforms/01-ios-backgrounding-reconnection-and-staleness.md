# iOS Backgrounding, Reconnection, And Staleness

## Use This When
- Designing iOS lifecycle behavior for a Convex-backed app.
- Explaining why the websocket dies in background.
- Planning reconnect and stale-data UX.

## What Actually Happens

When the app backgrounds, iOS suspends normal websocket activity and drops the connection:

```
[User presses Home]
  → scenePhase: .active → .inactive → .background
  → iOS gives app ~5 seconds before suspension
  → WebSocket receives POSIX error 53 ("Software caused connection abort")
  → App process suspended

[User opens app]
  → scenePhase: .background → .inactive → .active
  → Rust layer detects process resumption
  → Reconnects with exponential backoff (100ms initial, 15s max)
  → loginFromCache(onIdToken:) called to refresh JWT (v0.8.0+)
  → WebSocket re-established
  → All active subscriptions resume with fresh data
```

This is NOT a Convex bug — iOS reclaims kernel-level socket resources during suspension. `URLSessionWebSocketTask` cannot use background sessions. Firebase and Supabase face the same constraint.

## What Convex Handles Automatically
- WebSocket reconnection with exponential backoff
- Re-authentication via `loginFromCache(onIdToken:)`
- Re-registration of all active subscriptions
- Fresh data delivery to all Combine publishers

## What You Need to Handle
- Show a "reconnecting" indicator during the reconnection window
- Detect stale data — if the user was in background for 30 seconds, data is 30 seconds old

## Detecting Transitions

```swift
struct ContentView: View {
    @Environment(\.scenePhase) private var scenePhase
    @StateObject private var vm = ContentViewModel()

    var body: some View {
        MainView(vm: vm)
            .onChange(of: scenePhase) { newPhase in
                switch newPhase {
                case .active: vm.handleForeground()
                case .background: vm.handleBackground()
                case .inactive: break  // transient — Control Center, incoming call
                @unknown default: break
                }
            }
    }
}
```

## Key Constraint: Pipeline Termination vs Reconnect

Subscriptions do NOT need manual recreation after background/foreground **if the Combine pipeline is still alive**. The Rust layer handles reconnection.

But if the subscription pipeline terminated due to an error (see `pitfalls/01-pipeline-dies-after-first-error.md`), it will NOT resume on foreground. You must recreate it from the owning ViewModel.

## Staleness Rule
- Record last successful refresh or last background timestamp.
- Treat fresh transport connectivity and fresh data as separate states.
- Let the UI surface when it is showing last-known data after a resume.

## Avoid
- Promising background live-sync semantics that iOS does not allow.
- Assuming reconnect will revive a subscription that already failed terminally.
- Designing important data ownership around view-scoped `.task` pipelines that vanish easily.
- Confusing `.inactive` with `.background` — they are not the same recovery signal.

## Read Next
- [02-offline-behavior-network-transitions-and-recovery.md](02-offline-behavior-network-transitions-and-recovery.md)
- [03-performance-battery-and-threading.md](03-performance-battery-and-threading.md)
- [../pitfalls/01-pipeline-dies-after-first-error.md](../pitfalls/01-pipeline-dies-after-first-error.md)
