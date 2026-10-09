# Expo Dev Client Sessions and Mobile State Persistence

Managing application state, authentication tokens, runtime permissions, and development client runtimes requires distinct strategies depending on whether you test a static release build or an active Expo development session.

---

## Release Builds vs. Expo Dev Client Sessions

| Target Environment | Launch Strategy | State Reset Strategy |
|---|---|---|
| **Production / Release Build** | Use `launchApp` with explicit configuration. | Use `clearState: true`, `clearKeychain: true`, or `setPermissions`. |
| **Active Expo Dev Client** | **Omit `launchApp`**. The app is already running and connected to Metro. | Use app-defined deep links for soft resets. |

### The Dev Client Restart Trap

Calling `launchApp` against an active Expo Dev Client running in development mode interrupts the Metro bundler connection. The app restarts into the Expo launcher rather than your active screen, forcing a slow JavaScript bundle recompilation.

For running development clients:
1. Ensure the app and Metro bundler are already running.
2. Begin flow commands directly with element assertions or deep links.
3. Do not invoke `launchApp` or `stopApp`.

```yaml
# Flow for running Expo Dev Client
appId: com.example.demo
---
# Omit launchApp to preserve active Metro connection
- openLink: "exampleapp://dev-reset"
- assertVisible: "Dashboard"
- tapOn:
    id: "profile_tab"
```

---

## The iOS Keychain Persistence Gotcha

A critical failure mode in iOS mobile testing involves auth token persistence:

> **Important**: `clearState: true` clears the app sandbox (UserDefaults, SQLite database, cached files), but **does NOT clear the iOS Keychain**.

Libraries like `expo-secure-store` store authentication JWTs in the iOS Keychain. As a result:
- A test executing `clearState: true` may find the app still authenticated on next launch.
- Tests expecting a guest onboarding flow fail when the app immediately displays the user dashboard.

### Clearing iOS Keychain

To completely wipe credentials on iOS Simulators:

```yaml
- launchApp:
    clearState: true
    clearKeychain: true
```

Or execute the standalone command:

```yaml
- clearKeychain
```

> **Warning**: `clearKeychain` purges credentials for the target application from the simulator. On shared host simulators, ensure other concurrent runs are not relying on saved credentials.

---

## Dynamic Runtime Permissions (`setPermissions`)

Instead of clicking through OS system permission sheets during tests, pre-configure or dynamically update permissions:

### 1. Pre-Grant at App Launch
```yaml
- launchApp:
    permissions:
      all: allow
      notifications: allow
      camera: deny
      photos: allow
      location: in-use            # Options: allow, deny, unset, in-use, always
```

### 2. Dynamically Update During Flow
```yaml
- setPermissions:
    appId: com.example.demo
    permissions:
      location: always
      notifications: allow
```

---

## Soft Resets via App-Defined Deep Links

The most reliable pattern for resetting application state without destroying runtime connections or Keychain tokens is an app-defined debug deep link:

```yaml
# Trigger soft state reset via application debug route
- openLink: "exampleapp://dev/reset-fixtures"
- extendedWaitUntil:
    visible:
      id: "state_reset_complete"
    timeout: 5000
```

This pattern allows the application's internal state management (Redux, Zustand, React Query) to re-initialize with clean mock data without cycling the native process.

---

## Auth Pre-Flight Synchronization

To avoid race conditions where Maestro attempts to tap UI elements while asynchronous authentication hydration is in progress, implement an auth-settling assertion:

```yaml
- launchApp
# Wait for auth state hydration to complete
- extendedWaitUntil:
    visible:
      id: "app_ready_marker"
    timeout: 15000
- tapOn:
    id: "home_tab"
```

---

## Metro Bundler Network Connectivity

When running tests against a dev client:
- Local simulator on macOS connects to Metro at `http://localhost:8081`.
- Android emulators connect via ADB reverse proxy (`adb reverse tcp:8081 tcp:8081`) or `10.0.2.2:8081`.
- Remote testing over SSH requires Metro to listen on all interfaces or provide a tunnel URL.

---

## Related References

- [Flows and Selectors](../commands/flows-and-selectors.md) — LaunchApp options and openLink syntax.
- [Mobile Flakiness](mobile-flakiness.md) — Mitigating UI race conditions and timing flakes.
- [Suites and CI](../patterns/suites-and-ci.md) — Suite configuration and tags.
