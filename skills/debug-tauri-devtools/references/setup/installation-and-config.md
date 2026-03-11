# Installation & Configuration — CrabNebula DevTools

## Crate Selection

| Crate | Purpose | Install |
|---|---|---|
| `tauri-plugin-devtools` | Free web UI (browser-based) | `cargo add tauri-plugin-devtools` |
| `tauri-plugin-devtools-app` | Premium embedded desktop panel | `cargo add tauri-plugin-devtools-app` |
| `devtools` | Legacy Tauri v1 only | `cargo add devtools` (do NOT use for v2) |

Current stable versions (Tauri v2):
- `tauri-plugin-devtools = "2.0.1"`
- `tauri-plugin-devtools-app = "2.0.1"`
- Internal core: `devtools-core = "0.3.6"`

## Cargo.toml Setup

### Minimal (free web UI)

```toml
[dependencies]
tauri = "2"
tauri-plugin-devtools = "2"
```

### Premium (embedded desktop panel)

```toml
[dependencies]
tauri = "2"
tauri-plugin-devtools-app = "2"
```

### With tauri-plugin-log compatibility

```toml
[dependencies]
tauri = "2"
tauri-plugin-devtools = "2"
tauri-plugin-log = "2"
```

## Initialization Patterns

### Pattern 1: Basic (recommended for most projects)

```rust
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    // IMPORTANT: init() BEFORE Builder::default() to capture all tracing events
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

Why `init()` comes first: The `init()` call creates the tracing subscriber. Events emitted before the subscriber is registered are lost forever. Calling it before `Builder::default()` ensures plugin initialization events from other plugins are captured.

### Pattern 2: With tauri-plugin-log (split pattern)

```rust
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            // split() separates the log plugin into 3 parts
            let (tauri_plugin_log, _max_level, logger) =
                tauri_plugin_log::Builder::new()
                    .level(log::LevelFilter::Debug)
                    .split(app.handle())?;

            #[cfg(debug_assertions)]
            {
                // In debug: DevTools becomes the subscriber for BOTH tracing and log events
                let mut devtools_builder = tauri_plugin_devtools::Builder::default();
                devtools_builder.attach_logger(logger);
                app.handle().plugin(devtools_builder.init())?;
            }

            #[cfg(not(debug_assertions))]
            {
                // In release: logger goes to standard log plugin
                tauri_plugin_log::attach_logger(_max_level, logger);
            }

            app.handle().plugin(tauri_plugin_log)?;
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

### Pattern 3: Premium desktop app

```rust
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let mut builder = tauri::Builder::default();

    #[cfg(debug_assertions)]
    {
        // Uses tauri_plugin_devtools_app instead of tauri_plugin_devtools
        let devtools = tauri_plugin_devtools_app::init();
        builder = builder.plugin(devtools);
    }

    builder
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

Premium adds: Cmd/Ctrl+Shift+M keyboard shortcut to toggle embedded panel, offline usage, auto-connect.

### Pattern 4: Multi-plugin project

```rust
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let mut builder = tauri::Builder::default();

    // DevTools FIRST — captures init tracing from all subsequent plugins
    #[cfg(debug_assertions)]
    {
        let devtools = tauri_plugin_devtools::init();
        builder = builder.plugin(devtools);
    }

    // Other plugins AFTER — their tracing events are captured
    builder
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_store::Builder::new().build())
        .plugin(tauri_plugin_fs::init())
        .setup(|_app| {
            // DevTools already registered — captures everything
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

### Pattern 5: Feature flag (optional dependency)

```toml
# Cargo.toml
[features]
devtools = ["tauri-plugin-devtools"]

[dependencies]
tauri-plugin-devtools = { version = "2", optional = true }
```

```rust
#[cfg(feature = "devtools")]
{
    let devtools = tauri_plugin_devtools::init();
    builder = builder.plugin(devtools);
}
```

Use feature flags when you need finer control than debug/release (e.g., DevTools in CI but not local release builds).

## Builder API

| Method | Description |
|---|---|
| `Builder::default()` | Creates builder with default settings |
| `.attach_logger(logger)` | Attaches a `tauri-plugin-log` logger via the `.split()` pattern |
| `.init()` | Consumes builder, returns the plugin instance |
| `tauri_plugin_devtools::init()` | Convenience shorthand for `Builder::default().init()` |

## Connecting to DevTools

### Free web UI

1. Run your app: `cargo tauri dev`
2. Look for terminal output like:
   ```
   devtools: listening on ws://127.0.0.1:7043
   ```
3. Open https://devtools.crabnebula.dev in any browser
4. Paste the connection URL from the terminal

### Premium desktop app

1. Download the DevTools Desktop app from CrabNebula
2. The embedded panel auto-connects — no URL pasting needed
3. Toggle with **Cmd+Shift+M** (macOS) or **Ctrl+Shift+M** (Windows/Linux)

## Platform-Specific Setup

### macOS
No special setup. DevTools works out of the box.

### Windows
No special setup. gRPC server binds to localhost.

### Linux
Ensure no firewall blocks localhost ports 6000-9000.

### Android
The gRPC server runs inside the app on the device/emulator. Forward the port:
```bash
# Find the port from logcat output
adb logcat | grep devtools

# Forward the port
adb forward tcp:PORT tcp:PORT

# Alternative: emulator console
telnet localhost 5554
redir add tcp:PORT:PORT
```

### iOS
DevTools prints the connection URL to Xcode console after ~3 seconds. Copy the URL and open in desktop browser.

## Debug-Only Compilation

The `#[cfg(debug_assertions)]` gate is critical:

| Build Command | debug_assertions | DevTools Active |
|---|---|---|
| `cargo build` | ✓ | ✓ |
| `cargo tauri dev` | ✓ | ✓ |
| `cargo build --release` | ✗ | ✗ |
| `cargo tauri build` | ✗ | ✗ |
| `cargo tauri build --debug` | ✓ | ✓ |

In release builds, the compiler completely removes:
- The tracing subscriber registration
- The gRPC server and all its dependencies
- Port scanning and URL printing logic
- Zero overhead — code doesn't exist in the binary

## Common Installation Errors

| Error | Cause | Fix |
|---|---|---|
| `PluginInitialization("log", "attempted to set a logger after the logging system was already initialized")` | Both DevTools and tauri-plugin-log try to set the global subscriber | Use the `split()/attach_logger()` pattern (Pattern 2 above) |
| `PluginInitialization("probe", ...)` | Multiple DevTools instances registered | Ensure only one `init()` call — "probe" is the internal plugin name |
| `cannot find crate tauri_plugin_devtools` | Wrong crate name or not installed | Run `cargo add tauri-plugin-devtools` (hyphens in crate name, underscores in code) |
| Binary bloat in release | Missing `#[cfg(debug_assertions)]` gate | Wrap all DevTools code in the gate |
| Port conflict on startup | Another process using ports 6000-9000 | Stop the other process; DevTools will auto-pick a free port in range |

## Naming Conventions

| Context | Name |
|---|---|
| Cargo crate (Cargo.toml) | `tauri-plugin-devtools` (hyphens) |
| Rust module (use/import) | `tauri_plugin_devtools` (underscores) |
| Internal Tauri plugin name | `"probe"` |
| Premium crate | `tauri-plugin-devtools-app` |
| Premium module | `tauri_plugin_devtools_app` |
| Legacy v1 crate | `devtools` |
