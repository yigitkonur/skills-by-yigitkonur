# Android Devices, Local macOS Simulators, and Web Automation

Maestro drives local Android emulators, physical Android devices connected via ADB, local iOS Simulators on macOS, and local Chromium browsers for Web testing.

---

## Local Android Execution

Android automation runs natively on Linux, macOS, and Windows hosts.

### 1. Prerequisites and Toolchain
- **Android SDK & ADB**: `adb` must be available in `$PATH`, and `$ANDROID_HOME` configured.
- **Java Runtime**: OpenJDK 17+ (`java -version`, configured via `$JAVA_HOME`).
- **Device Connectivity**: Device or emulator connected and visible via `adb devices`.
- **Linux KVM Acceleration**: Linux emulator hosts benefit from KVM hardware acceleration (`/dev/kvm`).

### 2. Driver Architecture (`dadb`)
On Android, Maestro connects via `dadb` (Direct ADB Kotlin library) using direct ADB socket streams rather than TCP port forwarding, improving communication latency:
- `maestro-server.apk`: Exposes on-device automation server via gRPC (`MaestroDriverGrpc`).
- `maestro-driver.apk`: Interacts with Android Accessibility service for touch and view hierarchy traversal.
- **WebView Inspection**: Connects to on-device Chromium DevTools Protocol via Unix domain sockets (`DadbChromeDevToolsClient`).
- If driver installation becomes corrupted, pass `--reinstall-driver` to re-push the helper binaries.

### 3. Device Discovery and Targeting
```bash
# List attached hardware and emulators
adb devices

# Or via Maestro CLI
maestro list-devices --platform=android

# Run flow on specific Android target
maestro --device "emulator-5554" test flows/smoke.yaml
```

---

## Local macOS iOS Simulator Execution

On macOS workstations with Xcode installed, iOS Simulator tests run locally without SSH transport.

### 1. Prerequisites
- macOS running Xcode (`xcode-select -p` pointing to active Developer directory).
- Booted iOS Simulator.
- Target application `.app` binary installed on the simulator.

### 2. Driver Architecture & Port Allocation
- **XCUITest Runner**: Maestro deploys an instrumented XCUITest runner bundle (`dev.mobile.maestro-driver-iosUITests.xctrunner`) via `xcodebuild test-without-building`.
- **Embedded HTTP Server**: Built on Swift `FlyingFox` (`XCTestHTTPServer.swift`), listening on `127.0.0.1`.
- **Port Allocation**: Default fallback port is `22087`. In modern multi-device or parallel runs, Maestro binds dynamic ephemeral ports passed to the simulator via `SIMCTL_CHILD_PORT`.
- **`applesimutils` Clarification**:
  - Maestro does **NOT** require `brew install applesimutils`.
  - A precompiled binary is packaged inside `maestro-cli.jar` (`deps/applesimutils`) and unpacked automatically to `~/.maestro/deps/applesimutils`.
  - It is used strictly for injecting simulator permissions (`--setPermissions`), not for UI actions or hierarchy parsing.

### 3. Device Discovery and Simulator Booting
```bash
# Check currently booted simulators
xcrun simctl list devices booted

# Or via Maestro CLI
maestro list-devices --platform=ios

# Boot target simulator by name or UDID
xcrun simctl boot "iPhone 16 Pro"

# Execute flows directly against booted simulator
maestro test flows/smoke.yaml

# Target specific simulator UDID explicitly
maestro --device "4B37C2F1-8B90-4A12-B67D-8F92E310AB12" test flows/smoke.yaml
```

---

## Web Automation (Chromium)

Maestro 2.x supports Web application testing powered by Chrome DevTools Protocol (CDP) and Selenium:

### 1. Prerequisites
- Google Chrome or Chromium installed on the host machine.
- Flow YAML configured with a starting `url:` instead of `appId:`.

### 2. Web Test Execution
```bash
# Run web flow in standard browser window
maestro test --platform=web flows/web-login.yaml

# Run web flow in headless mode with explicit viewport
maestro test --platform=web \
  --headless \
  --screen-size=1920x1080 \
  flows/web-checkout.yaml
```

### 3. Web Flow Example
```yaml
url: https://example.com/login
---
- assertVisible: "Sign In"
- tapOn:
    css: "input#username"
- inputText: "admin@example.com"
- tapOn:
    css: "button.submit-btn"
- assertVisible: "Dashboard"
```

---

## Device Lifecycle Management (`maestro start-device`)

Maestro CLI can create and launch virtual devices matching cloud hardware profiles:

```bash
# Create and boot an iOS Simulator
maestro start-device --platform=ios \
  --device-model=iPhone-16-Pro \
  --device-os=iOS-18-2

# Create and boot an Android Emulator with specific locale and system image
# Supports Android 17 (API 37) with 16 KB page-size system images
maestro start-device --platform=android \
  --device-model=pixel_7 \
  --device-os="system-images;android-34;google_apis_playstore;arm64-v8a" \
  --device-locale=en_US \
  --force-create
```

---

## Application Installation Prerequisites

The target mobile application package must be installed prior to running test flows:

### Android Installation
```bash
adb -s emulator-5554 install -r build/app-release.apk
```

### iOS Simulator Installation
```bash
xcrun simctl install booted build/Build/Products/Debug-iphonesimulator/DemoApp.app
```

---

## Platform Comparison Matrix

| Behavior | Android | iOS Simulator | Web (Chromium) |
|---|---|---|---|
| `clearState: true` | Clears app sandbox, storage, and credentials | Clears sandbox storage; does NOT clear iOS Keychain | Clears cookies / session storage |
| Physical Devices | Fully supported via ADB | **Unsupported locally** (Maestro 2.11.0 fails fast: `"Physical iOS devices are not yet supported"`) | N/A |
| System Permissions | Granted via `setPermissions` or native alert | Managed via internal `applesimutils` or UI alert | Browser permissions |
| Back Navigation | Handled via `back` command | Handled via edge swipe gesture | Browser back navigation |
| Selectors | `id` (resource-id), `text`, relational | `id` (accessibilityIdentifier), `text`, relational | `id`, `css`, `text`, relational |

---

## Related References

- [CLI and Artifacts](../commands/cli-and-artifacts.md) — Artifact inspection, MCP tools, and flags.
- [Flows and Selectors](../commands/flows-and-selectors.md) — Selector syntax, web selectors, and commands.
- [iOS over SSH](ios-over-ssh.md) — Remote iOS execution from Linux hosts.
- [Expo and State](../troubleshooting/expo-and-state.md) — Keychain handling and session continuity.
