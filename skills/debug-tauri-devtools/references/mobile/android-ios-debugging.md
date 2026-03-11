# Mobile Debugging — Android & iOS with Tauri DevTools

## Android Debugging

### Connecting DevTools on Android

The DevTools gRPC server runs inside the app on the device/emulator. To connect from your desktop browser:

```bash
# Step 1: Run the app on Android
cargo tauri android dev

# Step 2: Find the DevTools port from logcat
adb logcat | grep -i devtools
# Look for output like: "devtools: listening on ws://127.0.0.1:7043"

# Step 3: Forward the port to your desktop
adb forward tcp:7043 tcp:7043

# Step 4: Open https://devtools.crabnebula.dev and connect with the URL
```

### Alternative Port Forwarding (Emulator Console)

```bash
telnet localhost 5554
redir add tcp:7043:7043
```

### Android Logcat Filtering

```bash
# All Tauri-related logs
adb logcat | grep -iE "(tauri|webview|chromium)"

# Only Tauri plugin logs
adb logcat *:S tauri:V

# Rust tracing output (when RUST_LOG is set)
adb logcat | grep -i "my_app"

# Errors only
adb logcat *:E | grep -i tauri
```

### Common Android Issues

| Symptom | DevTools Tab | Cause | Fix |
|---|---|---|---|
| App crashes on launch | Console (if connected) | Plugin panic during init | Check logcat for panic message; some plugins don't support Android |
| File operations fail | Console → ERROR | Wrong file paths | Use `app.path().app_data_dir()` — no `/home/` on Android |
| Network requests fail | Calls tab | Missing INTERNET permission | Add to `AndroidManifest.xml`: `<uses-permission android:name="android.permission.INTERNET"/>` |
| Camera/GPS not working | Console → ERROR | Missing runtime permissions | Add Android runtime permission requests in plugin config |
| IPC is slower than desktop | Calls tab → Duration | JNI bridge overhead | Normal — expect 20-50ms higher latency vs desktop |
| DevTools won't connect | N/A | Port not forwarded | Run `adb forward tcp:PORT tcp:PORT` |
| WebView crashes | Logcat | Chromium/WebView bug | Update Android System WebView via Play Store |

### Android-Specific File Paths

```rust
// WRONG — hardcoded paths don't exist on Android
let path = "/home/user/.config/myapp/data.json";

// RIGHT — use Tauri's path API
#[tauri::command]
async fn get_data_path(app: tauri::AppHandle) -> Result<String, String> {
    let path = app.path().app_data_dir()
        .map_err(|e| e.to_string())?;
    Ok(path.to_string_lossy().to_string())
}
```

### Android Debug Build

```bash
# Development build with hot reload
cargo tauri android dev

# Debug APK build
cargo tauri android build --debug

# View logcat while running
adb logcat -v time | grep -E "tauri|RustStdoutStderr"
```

## iOS Debugging

### Connecting DevTools on iOS

DevTools prints the connection URL to the Xcode console after ~3 seconds:

1. Run `cargo tauri ios dev` (or open in Xcode)
2. In Xcode, view the debug console (View → Debug Area → Activate Console)
3. Look for the DevTools URL in the console output
4. Copy the URL and open in your desktop browser
5. Open https://devtools.crabnebula.dev and connect

### Xcode Console Filtering

```bash
# From terminal (simulator)
xcrun simctl spawn booted log stream --level debug --predicate 'subsystem == "app.tauri"'

# Filter by your app
xcrun simctl spawn booted log stream --predicate 'processImagePath contains "your-app"'
```

### Common iOS Issues

| Symptom | DevTools Tab | Cause | Fix |
|---|---|---|---|
| App rejected by App Store | N/A | Debug code in release | Ensure `#[cfg(debug_assertions)]` gates DevTools |
| File access denied | Console → ERROR | Sandbox restrictions | Use `app.path()` APIs; iOS has strict sandbox |
| Network calls blocked | Console → ERROR | App Transport Security (ATS) | Add ATS exceptions in `Info.plist` or use HTTPS |
| Push notifications fail | Console → ERROR | Missing entitlements | Add push notification entitlement in Xcode |
| Webview crashes on old iOS | Logcat equivalent | WKWebView compatibility | Set minimum iOS version in `tauri.conf.json` |
| DevTools URL not showing | Xcode console | Output delayed | Wait ~3 seconds after app launch |

### iOS-Specific Debugging Tips

1. **Safari Web Inspector** — For frontend debugging on iOS:
   - Enable in device Settings → Safari → Advanced → Web Inspector
   - Open Safari on Mac → Develop menu → select your device/simulator

2. **Xcode Instruments** — For iOS performance profiling:
   - Product → Profile in Xcode
   - Use Time Profiler, Allocations, or Network instruments

3. **Simulator vs Device** — Some issues only appear on real devices:
   - Push notifications (require real device)
   - Camera access (require real device)
   - Performance characteristics differ

## Cross-Platform Mobile Debugging Strategy

### When to Use What

| Tool | Android | iOS | When to Use |
|---|---|---|---|
| CrabNebula DevTools | Via `adb forward` | Via Xcode console URL | Rust backend debugging |
| Chrome DevTools | Via `chrome://inspect` | N/A | Android WebView debugging |
| Safari Web Inspector | N/A | Via Safari Develop menu | iOS WebView debugging |
| Logcat / Xcode Console | `adb logcat` | Xcode debug area | System-level logs |
| `RUST_LOG` | Via env in terminal | Via Xcode scheme | Rust tracing control |

### Mobile-Specific Code Patterns

```rust
// Platform-specific behavior
#[tauri::command]
async fn get_storage_path(app: tauri::AppHandle) -> Result<String, String> {
    let path = app.path().app_data_dir()
        .map_err(|e| e.to_string())?;
    
    // Log platform info for debugging
    #[cfg(target_os = "android")]
    tracing::info!("Android data dir: {:?}", path);
    
    #[cfg(target_os = "ios")]
    tracing::info!("iOS data dir: {:?}", path);
    
    Ok(path.to_string_lossy().to_string())
}

// Mobile entry point
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    #[cfg(debug_assertions)]
    let devtools = tauri_plugin_devtools::init();

    let mut builder = tauri::Builder::default();

    #[cfg(debug_assertions)]
    {
        builder = builder.plugin(devtools);
    }

    builder
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

### Debugging Mobile Plugin Support

Not all Tauri plugins support mobile. Check the plugin's README for platform support:

```rust
// This plugin might not support mobile
#[cfg(not(mobile))]
{
    builder = builder.plugin(tauri_plugin_global_shortcut::init());
}

// Use platform-specific alternatives on mobile
#[cfg(mobile)]
{
    // Mobile doesn't have global shortcuts — use in-app alternatives
}
```

Use the DevTools **Console tab** to check for plugin init errors on mobile — they often show platform-specific messages explaining what's not supported.

## Mobile Performance Debugging

### IPC Latency on Mobile

Mobile IPC is inherently slower due to:
- JNI bridge overhead (Android)
- WKWebView message passing (iOS)
- Typical additional latency: 20-50ms per call

Use the DevTools **Calls tab** to measure mobile IPC latency. If commands take > 200ms:
1. Check for blocking I/O in the handler
2. Consider batching multiple small calls into one
3. Use background processing with progress events

### Memory Debugging on Mobile

Mobile devices have tighter memory constraints:
- Android: App killed when system needs memory (no warning)
- iOS: ~50MB warning, then killed

Monitor memory via platform tools:
- Android: `adb shell dumpsys meminfo your.package.name`
- iOS: Xcode Memory Graph Debugger

DevTools doesn't directly show memory usage, but the Console tab may show memory-related errors or warnings from the Rust runtime.
