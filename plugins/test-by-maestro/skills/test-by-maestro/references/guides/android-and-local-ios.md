# Android Devices, Linux Hosts, Local macOS Simulators, and Web Automation

Maestro drives local Android emulators, physical Android devices connected via ADB, local iOS Simulators on macOS, and local Chromium browsers for Web testing. Facts verified against Maestro `2.11.0` source and `docs.maestro.dev`.

---

## Local Android Execution

Android automation runs natively on Linux, macOS, and Windows hosts.

### 1. Prerequisites and Toolchain
- **Java 17+** (`java -version`); Java 17 or 21 recommended. `$JAVA_HOME` is optional if `java` is on `PATH`.
- **Android SDK platform-tools**: `adb` on `PATH`; a device or emulator visible in `adb devices`.
- **`ANDROID_HOME` or `ANDROID_SDK_ROOT`**: needed only for the SDK-tool paths (`maestro start-device`, AVD listing via `avdmanager`/`sdkmanager`/`emulator`). Plain `maestro test` against an already-running device talks to it through `dadb` and the adb server.

### 2. Driver Architecture
Maestro connects through `dadb` (a Kotlin ADB client) and speaks gRPC over `dadb.open("tcp:<port>")`, not an `adb forward`:
- `maestro-app.apk` and `maestro-server.apk` are the helper APKs pushed to the device; the server exposes the automation API (UIAutomator-based).
- WebView inspection uses the on-device Chrome DevTools socket.
- `--reinstall-driver` is already the default for `maestro test` and `hierarchy`, so the helper APKs are re-pushed on every run. Use `--no-reinstall-driver` to skip.

### 3. Device Discovery and Targeting
```bash
adb devices                                      # serials of attached devices/emulators
maestro list-devices --platform=android         # models (connected and launchable), no serials
maestro --device "emulator-5554" test flows/smoke.yaml
```

---

## Linux Hosts: Android and Web Locally, iOS Never

On Linux, Maestro runs **Android (emulator or physical) and Web (Chromium)**. iOS Simulators and `maestro start-device --platform=ios` cannot work on Linux; use Maestro Cloud or a Mac (see [iOS over SSH](ios-over-ssh.md)).

### Android emulator on a Linux server (headless)

1. **Check hardware acceleration**: `emulator -accel-check`. On Linux the emulator relies on KVM (`/dev/kvm`) and needs a system image that matches the host CPU (`x86_64` on x86 hosts). Without acceleration the emulator refuses to start unless `ANDROID_I_WANT_MY_TCG=yes`, and software emulation is "not supported and is very slow".
2. **Install the image and create the AVD** (commands mirror Maestro's own CI workflow):
   ```bash
   yes | sdkmanager "platform-tools" "emulator" "system-images;android-34;google_apis;x86_64"
   avdmanager create avd -n MyAVD -k "system-images;android-34;google_apis;x86_64" --force
   ```
3. **Boot headless** and wait for the OS:
   ```bash
   emulator @MyAVD -no-snapshot -no-window -no-audio -no-boot-anim -accel on &
   adb wait-for-device
   until [ "$(adb shell getprop sys.boot_completed | tr -d '\r')" = "1" ]; do sleep 2; done
   ```
4. **Run**: `maestro --device emulator-5554 test .maestro`.

`maestro start-device --platform=android` also works on Linux but launches the emulator **with a window** and prompts `y/n` if the system image is missing, so prefer the explicit commands above on servers and in agents.

On GitHub-hosted Linux runners, enable KVM with the udev rule (`KERNEL=="kvm", GROUP="kvm", MODE="0666", OPTIONS+="static_node=kvm"`) or use `ReactiveCircus/android-emulator-runner`; 2-vCPU Linux runners now support acceleration. There is no official Maestro Docker image. Google's emulator container scripts also require Linux plus KVM. GitHub's arm64 macOS runners do not support nested virtualization.

---

## Local macOS iOS Simulator Execution

On macOS with **full Xcode** installed, iOS Simulator tests run locally without SSH.

### 1. Prerequisites
- `xcode-select -p` pointing at an Xcode.app Developer directory (Maestro calls `xcodebuild`, which Command Line Tools alone do not provide).
- A booted iOS Simulator and the target `.app` installed on it.
- Physical iPhones are unsupported (2.11.0 fails fast with `Physical iOS devices are not yet supported`).

### 2. Driver Architecture
- **XCUITest runner**: `dev.mobile.maestro-driver-iosUITests.xctrunner`, started with `xcodebuild test-without-building`.
- **Embedded HTTP server**: Swift `FlyingFox` on `127.0.0.1`. The port is chosen by the OS on every `maestro test` run and passed as `TEST_RUNNER_PORT`; `22087` is only the fallback default. (`SIMCTL_CHILD_PORT` belongs to a prebuilt-runner path that the CLI does not take.)
- **`MAESTRO_DRIVER_STARTUP_TIMEOUT`**: docs say 15000 ms; the iOS source default is 120000 ms. Maestro's own macOS CI raises it to 240000.
- **`applesimutils`** is bundled in the CLI and unpacked to `~/.maestro/deps/applesimutils`; it is used only to set simulator permissions. No `brew install` is needed.

### 3. Device Discovery and Booting
```bash
xcrun simctl list devices booted --json          # booted simulators with UDIDs
maestro list-devices --platform=ios              # models, not UDIDs
xcrun simctl boot <UDID>                         # boot by UDID (Maestro's CI boots by UDID)
maestro --device "<UDID>" test flows/smoke.yaml
```

---

## Web Automation (Chromium, Beta)

Web support is **Beta**; the CLI prints `Web support is in Beta` when a web flow runs.

### 1. Prerequisites
- No separate browser install: on first run Maestro downloads a managed Chromium.
- A flow whose header uses `url:` instead of `appId:`.

### 2. Execution
```bash
maestro test --platform=web flows/web-login.yaml
maestro test --platform=web --headless --screen-size=1920x1080 flows/web-checkout.yaml
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

## Application Installation Prerequisites

Install the app before running flows:

```bash
adb -s emulator-5554 install -r build/app-release.apk                       # Android
xcrun simctl install booted build/Build/Products/Debug-iphonesimulator/DemoApp.app   # iOS Simulator
```

---

## Platform Comparison Matrix

| Behavior | Android | iOS Simulator | Web (Chromium) |
|---|---|---|---|
| `clearState: true` | Clears app storage and credentials | Terminate + reinstall; **no keychain call** (use `clearKeychain`) | Clears cookies, local storage, and other browser data for the origin |
| Physical devices | Supported via ADB | **Unsupported** (2.11.0) | N/A |
| Permissions | `allow`/`deny`/`unset`; other values revoke | `allow`/`deny`/`unset` plus `always`/`inuse`/`never`, `photos: limited` (via `applesimutils`) | Browser permissions |
| `back` | Back key | **No-op** | Browser back |
| `hideKeyboard` | Sends Back key | Hides keyboard (flaky on iOS, see known issues) | No-op |
| Airplane mode / `killApp` | Supported | Not supported / alias of `stopApp` | No effect |
| Selectors | `id` (resource-id), `text`, relational | `id` (accessibilityIdentifier), `text`, relational | `id`, `css`, `text`, relational |

---

## Related References

- [CLI and Artifacts](../commands/cli-and-artifacts.md) — Flags, `start-device`, MCP tools.
- [Flows and Selectors](../commands/flows-and-selectors.md) — Selector syntax and commands.
- [iOS over SSH](ios-over-ssh.md) — iOS from Linux hosts (Cloud or a Mac).
- [Expo and State](../troubleshooting/expo-and-state.md) — Keychain handling and session continuity.
