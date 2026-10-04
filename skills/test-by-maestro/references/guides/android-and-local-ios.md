# Android Devices and Local macOS Simulators

Maestro drives local Android emulators, physical Android devices connected via ADB, and local iOS Simulators on macOS.

## Local Android Execution

Android automation runs natively on both Linux and macOS hosts.

### 1. Prerequisites and Toolchain
- **Android SDK & ADB**: `adb` must be available in `$PATH`, and `$ANDROID_HOME` configured.
- **Java Runtime**: OpenJDK 17+ (`java -version`).
- **Device Connectivity**: Device or emulator connected and visible via `adb devices`.
- **Linux KVM Acceleration**: Linux emulator hosts benefit from KVM hardware acceleration (`/dev/kvm`).

### 2. Device Discovery and Targeting

List connected devices and emulators:

```bash
adb devices
# List emulator targets
# List attached hardware
```

When multiple Android devices or emulators are connected, specify the device serial:

```bash
# Run flow on specific Android target
maestro --udid emulator-5554 test flows/smoke.yaml

# Alternatively using --device flag
maestro --device "emulator-5554" test flows/smoke.yaml
```

### 3. Driver Architecture
On Android, Maestro connects via `dadb` (Direct ADB Kotlin library) and installs two temporary instrumented helper APKs:
- `maestro-server.apk`: Exposes on-device automation server via gRPC.
- `maestro-driver.apk`: Interacts with Android Accessibility service.

If driver installation becomes corrupted, pass `--reinstall-driver` to re-push the helper binaries.

## Local macOS iOS Simulator Execution

On macOS workstations with Xcode installed, iOS Simulator tests run locally without SSH transport.

### 1. Prerequisites
- macOS running Xcode (`xcode-select -p` pointing to active Developer directory).
- Booted iOS Simulator.
- Target application `.app` binary installed on the simulator.

### 2. Device Discovery and Simulator Booting

Identify booted or available simulators:

```bash
# Check currently booted simulators
xcrun simctl list devices booted

# List all available simulators
xcrun simctl list devices available
```

If no simulator is booted, boot a target simulator by name or UDID, or use Maestro:

```bash
# Boot target simulator by name or UDID
xcrun simctl boot "iPhone 16"
# or: xcrun simctl boot "$UDID"

# Alternatively, launch the Simulator GUI or use Maestro start-device
open -a Simulator
# or: maestro start-device --platform=ios
```

Execute flows directly against the booted simulator:

```bash
# Auto-detects single booted simulator
maestro test flows/smoke.yaml

# Target specific simulator UDID explicitly
maestro --udid "4B37C2F1-8B90-4A12-B67D-8F92E310AB12" test flows/smoke.yaml
```

## Application Installation Prerequisites

Maestro executes tests against installed mobile applications. The application package must be installed prior to running test flows:

### Android Installation

```bash
adb -s emulator-5554 install -r build/app-release.apk
```

### iOS Simulator Installation

```bash
xcrun simctl install booted build/Build/Products/Debug-iphonesimulator/DemoApp.app
```

## Platform State Reset Differences

| Behavior | Android | iOS Simulator |
|---|---|---|
| `clearState: true` | Clears app sandbox, storage, and credentials completely | Clears sandbox storage; does NOT clear iOS Keychain tokens |
| Physical Devices | Fully supported via ADB | Unsupported locally (requires Maestro Cloud) |
| System Permissions | Dismissed via native alert or `setPermissions` | Handled via `simctl privacy` or UI alerts |
| Hardware Back Button | Supported via `back` command | Handled via gesture swipe from edge |

## Related References

- [CLI and Artifacts](../commands/cli-and-artifacts.md) — Artifact inspection and reporting.
- [iOS over SSH](ios-over-ssh.md) — Remote iOS execution from Linux hosts.
- [Expo and State](../troubleshooting/expo-and-state.md) — Keychain handling and session continuity.
