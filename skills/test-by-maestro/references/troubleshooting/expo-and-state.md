# Expo Dev Client Sessions and Mobile State Persistence

Managing application state, authentication tokens, runtime permissions, and development client runtimes requires distinct strategies depending on whether you test a static release build or an active Expo development session.

---

## Release Builds vs. Expo Go vs. Dev Client Builds

| Target | Launch strategy |
|---|---|
| **Release / EAS / standalone build** | Normal `launchApp` (Maestro docs: "For EAS builds or standalone apps, use the standard `launchApp`"). Reset with `clearState`, `clearKeychain`, `setPermissions`. |
| **Expo Go** | `launchApp` cannot be used with a custom `appId`; open the project with `openLink` (the `exp://` URL). |
| **Expo Dev Client build** | It is a standalone app, so `launchApp` works, but it lands on the Dev Client launcher screen. Then either tap the listed dev server, or deep-link straight to it with `openLink: "exp+<scheme>://expo-development-client/?url=http%3A%2F%2F<host>:8081"`. |

Maestro's own Expo development-build article starts its flow with `- launchApp` and then handles the launcher screen with a conditional `runFlow`. There is no Maestro or Expo source for the claim that `launchApp` severs Metro or forces a bundle recompile; if you observe that in your project, treat it as a local finding and prefer `openLink` to re-enter the app.

```yaml
# Dev Client: launch, then enter the dev server if the launcher appears
appId: com.example.demo
---
- launchApp
- runFlow:
    when:
      visible: "Development Build"      # launcher screen text varies by project
    commands:
      - openLink: "exp+exampleapp://expo-development-client/?url=http%3A%2F%2F192.168.1.10%3A8081"
- assertVisible: "Dashboard"
```

---

## The iOS Keychain Persistence Gotcha

A common failure mode in iOS testing involves auth token persistence:

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

> **Warning**: `clearKeychain` resets the **entire simulator keychain** (`xcrun simctl keychain <udid> reset`), not just the target app's credentials. On shared simulators, make sure other concurrent runs are not relying on saved credentials.

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
      location: inuse             # iOS only; Android revokes unknown values (use allow/deny/unset cross-platform)
```

### 2. Dynamically Update During Flow
```yaml
- setPermissions:
    appId: com.example.demo
    permissions:
      location: allow                 # `always`/`inuse`/`never` and `photos: limited` are iOS only
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
- Remote testing over SSH needs the Mac to reach Metro (a LAN address or tunnel URL in the dev-client deep link); this is common practice rather than a Maestro-documented requirement.

---

## Related References

- [Flows and Selectors](../commands/flows-and-selectors.md) — LaunchApp options and openLink syntax.
- [Mobile Flakiness](mobile-flakiness.md) — Mitigating UI race conditions and timing flakes.
- [Suites and CI](../patterns/suites-and-ci.md) — Suite configuration and tags.
