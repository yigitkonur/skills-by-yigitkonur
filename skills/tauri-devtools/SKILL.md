---
name: tauri-devtools
description: "Use skill if you are debugging a Tauri app's Rust side, IPC calls, config, plugins, or bundled assets with CrabNebula DevTools."
license: MIT
metadata:
  author: yigitkonur
  version: "1.0"
---

# CrabNebula DevTools for Tauri v2

## What CrabNebula DevTools Is (and Is Not)

CrabNebula DevTools is a Rust-side observability tool for Tauri v2 applications. It surfaces everything that happens **behind** the webview — Rust backend logs, IPC call payloads and timing, resolved app configuration, and bundled asset inspection. Browser DevTools cannot see any of this because Tauri's IPC layer operates outside the browser's network stack.

| Capability | Browser DevTools | CrabNebula DevTools |
|---|---|---|
| DOM/CSS inspection | yes | no |
| JavaScript debugging | yes | no |
| HTTP network requests | yes | no |
| WebSocket inspection | yes | no |
| Rust backend logs | no | yes |
| IPC call inspection (invoke) | no | yes |
| IPC latency/timing spans | no | yes |
| Tauri app configuration | no | yes |
| Rust crate-level log filtering | no | yes |
| Asset resolution inspection | no | yes |
| Capability/permission verification | no | yes |
| Plugin registration status | no | yes |

Neither replaces the other. Use browser DevTools for frontend (DOM, CSS, JS, HTTP). Use CrabNebula DevTools for backend (Rust logs, IPC, config, tracing spans).

## When NOT to Use This Skill

This skill should NOT be activated for:
- **DOM/CSS layout issues** — Use browser DevTools Elements panel
- **JavaScript errors or exceptions** — Use browser DevTools Console
- **HTTP/fetch request failures** — Use browser DevTools Network tab
- **WebSocket debugging** — Use browser DevTools Network tab (WS filter)
- **Frontend performance profiling** — Use browser DevTools Performance tab
- **React/Vue/Svelte component debugging** — Use framework-specific browser extensions
- **CSS animation issues** — Use browser DevTools Animations panel
- **Memory leaks in JavaScript** — Use browser DevTools Memory tab

Only activate this skill when the problem involves: Rust backend behavior, IPC calls, Tauri configuration, plugin issues, tracing/logging, or asset bundling.

## Architecture: How It Works

The plugin registers a tracing subscriber that intercepts all Rust tracing spans and events from your application. This data is streamed via a gRPC server (dynamically allocated port in range 6000-9000) to either:
- The **web UI** at https://devtools.crabnebula.dev (free, any browser)
- The **Premium desktop app** (embedded in-app, requires tauri-plugin-devtools-app crate)

```
+-----------------------------------+
|   Your Tauri App                  |
|                                   |
|  Rust Backend                     |
|   +-- tracing spans ------------>-+---> BridgeLayer (captures tracing data)
|   +-- log events --------------->-+---> Layer (processes and formats)
|   +-- IPC calls ---------------->-+---> Aggregator (batches and buffers)
|   +-- custom #[instrument] ----->-+---> Server (gRPC, separate thread)
|                                   |
|  gRPC Server (port 6000-9000)     |
|   +-- runs in separate thread -->-+---> "so we don't interfere with the
|      (non-blocking to app)        |      application we're trying to
|                                   |      instrument"
+-----------------------------------+
           |
           v
+-----------------------------------+
|  DevTools UI                      |
|  (browser or desktop)             |
|   +-- Console tab (logs/events)   |
|   +-- Calls tab (IPC spans)      |
|   +-- Config tab (resolved cfg)  |
|   +-- Sources tab (assets)       |
+-----------------------------------+
```

The gRPC server runs in a **separate thread** specifically so it does not interfere with the application being instrumented. This means DevTools has near-zero impact on your app's runtime performance. The internal plugin name registered with Tauri is "probe".

**Zero impact on release builds** — the `#[cfg(debug_assertions)]` gate ensures the plugin is completely stripped from production binaries. No tracing subscriber, no gRPC server, no dependencies compiled in.

For a deeper dive into the internal pipeline (BridgeLayer to Layer to Aggregator to Server), see references/devtools-architecture-deep-dive.md.

## Free vs Premium Tier

| Feature | Free (web UI) | Premium (desktop app) |
|---|---|---|
| Console log viewer | yes | yes |
| IPC Calls tab | yes | yes |
| Config viewer | yes | yes |
| Sources tab | yes | yes |
| Embedded in-app panel | no | yes (Cmd/Ctrl+Shift+M) |
| Offline usage | no (needs browser) | yes |
| Auto-connect | no (paste URL) | yes |
| Crate | tauri-plugin-devtools | + tauri-plugin-devtools-app |

The keyboard shortcut **Ctrl+Shift+M** (Windows/Linux) or **Cmd+Shift+M** (macOS) toggles the embedded DevTools panel in the premium desktop app version.

## Installation — Cargo.toml

```toml
[dependencies]
tauri-plugin-devtools = "2.0.0"
```

Install via CLI:
```bash
cargo add tauri-plugin-devtools
```

**Important:** This crate should only be active in debug builds. The `#[cfg(debug_assertions)]` pattern below ensures it is completely excluded from release builds, preventing binary bloat and potential security exposure.

For Premium (embedded desktop app), also add:
```toml
tauri-plugin-devtools-app = "2.0.0"
```

## Installation — src-tauri/src/lib.rs

### Basic Pattern (recommended for most projects)

```rust
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

### Builder Pattern (custom config / compatibility with tauri-plugin-log)

```rust
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            let (tauri_plugin_log, max_level, logger) =
                tauri_plugin_log::Builder::new().split(app.handle())?;

            #[cfg(debug_assertions)]
            {
                let mut devtools_builder = tauri_plugin_devtools::Builder::default();
                devtools_builder.attach_logger(logger);
                app.handle().plugin(devtools_builder.init())?;
            }

            #[cfg(not(debug_assertions))]
            {
                tauri_plugin_log::attach_logger(max_level, logger);
            }

            app.handle().plugin(tauri_plugin_log)?;
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

### Separate debug/release logging pattern

```rust
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let mut builder = tauri::Builder::default();

    #[cfg(debug_assertions)]
    {
        let devtools = tauri_plugin_devtools::init();
        builder = builder.plugin(devtools);
    }

    #[cfg(not(debug_assertions))]
    {
        use tauri_plugin_log::{Builder, Target, TargetKind};
        let log_plugin = Builder::default()
            .targets([
                Target::new(TargetKind::Stdout),
                Target::new(TargetKind::LogDir { file_name: None }),
                Target::new(TargetKind::Webview),
            ])
            .build();
        builder = builder.plugin(log_plugin);
    }

    builder
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

### Multi-plugin project with setup hook

```rust
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let mut builder = tauri::Builder::default();

    #[cfg(debug_assertions)]
    {
        let devtools = tauri_plugin_devtools::init();
        builder = builder.plugin(devtools);
    }

    builder
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_store::Builder::new().build())
        .setup(|app| {
            // DevTools is already registered above — it will capture
            // tracing events from all plugins registered here too.
            // No additional setup needed.
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

### Premium desktop app pattern

```rust
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let mut builder = tauri::Builder::default();

    #[cfg(debug_assertions)]
    {
        let devtools = tauri_plugin_devtools_app::init();
        builder = builder.plugin(devtools);
    }

    builder
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

## Builder Configuration Options

The `tauri_plugin_devtools::Builder` provides methods to customize the DevTools plugin behavior:

| Method | Description | When to Use |
|---|---|---|
| `Builder::default()` | Creates a new builder with default settings | Always — start here |
| `.attach_logger(logger)` | Attaches a tauri-plugin-log logger instance | When using tauri-plugin-log with the .split() pattern |
| `.init()` | Consumes the builder and produces the plugin | Always — call last to get the plugin instance |

**Basic Builder usage:**
```rust
let mut devtools_builder = tauri_plugin_devtools::Builder::default();
let plugin = devtools_builder.init();
app.handle().plugin(plugin)?;
```

**Builder with logger:**
```rust
let (log_plugin, max_level, logger) = tauri_plugin_log::Builder::new().split(app.handle())?;
let mut devtools_builder = tauri_plugin_devtools::Builder::default();
devtools_builder.attach_logger(logger);
app.handle().plugin(devtools_builder.init())?;
```

The convenience function `tauri_plugin_devtools::init()` is equivalent to `Builder::default().init()` — use it when you don't need to attach a logger or customize behavior.

## Platform-Specific Setup

**Android:**
The gRPC server runs inside the app on the device/emulator. To connect from your desktop browser:
```bash
adb forward tcp:PORT tcp:PORT
```
Replace PORT with the actual port shown in the terminal output when the app starts. The port is dynamically allocated in the 6000-9000 range.

**macOS:** No special setup required for DevTools. No screen recording permission needed (that is only required for the MCP bridge plugin's screenshot tool, not DevTools).

**iOS:** DevTools prints the connection URL to the Xcode console after a short delay (~3 seconds). Copy the URL and open it in your desktop browser to connect.

**Windows:** No special setup required. The gRPC server binds to localhost by default.

**Linux:** No special setup required. Ensure no firewall rules block localhost ports in the 6000-9000 range.

## What Each Tab Surfaces (Agent Decision Guide)

### Console Tab
**Data shown:** All Rust tracing events — log messages from `tracing::info!()`, `tracing::error!()`, `tracing::debug!()`, and `log::` macros piped through the tracing subscriber.

**Columns visible:**
- **Timestamp** — relative to app start, millisecond precision
- **Level** — TRACE, DEBUG, INFO, WARN, ERROR (color-coded badges)
- **Target** — full Rust module path (e.g., `my_app::commands::file_ops`)
- **Message** — the formatted log message string
- **Fields** — structured key-value pairs from tracing span/event fields

**Filtering:** By level (click badges), by target/crate name (text filter), by message content (free-text search). Multiple filters can be combined.

**When to direct user here:** When the user reports a Rust-side error they can't find, when they need to trace the sequence of events leading to a bug, when a specific crate is generating excessive log output, or when debugging plugin initialization order.

**Bug class caught:** Silent panics, unhandled Result errors logged at ERROR level, missing tracing spans indicating code paths not being reached, crate-level noise drowning out important messages, and plugin initialization failures.

### Calls Tab
**Data shown:** Every IPC invoke() call between the frontend and Rust backend. Shows the complete lifecycle of each call as a tracing span.

**Columns visible:**
- **Command** — the Tauri command name (e.g., get_user, save_file)
- **Arguments** — serialized JSON of input parameters from the frontend
- **Response** — serialized return value (on success) or error message (on failure)
- **Duration** — wall-clock time from invoke start to response, in milliseconds
- **Status** — success or error indicator
- **Nesting depth** — indentation showing parent-child span relationships

**Filtering:** By command name, by duration (sort to find slow calls), by status (errors only/successes only).

**When to direct user here:** When the user says a Tauri command is slow, when IPC calls fail silently, when the user wants to see what data is being passed to Rust commands, when debugging the order of IPC calls, or when identifying redundant calls.

**Bug class caught:** Slow commands (visible via span duration), incorrect argument serialization, commands being called in wrong order, redundant IPC calls, commands that never return (infinite duration), and type mismatch errors in serialized data.

### Config Tab
**Data shown:** The resolved Tauri application configuration — the merged result of tauri.conf.json, any environment overrides, and plugin configurations.

**Sections visible:**
- **App** — window definitions, withGlobalTauri, macOS private API settings
- **Build** — dev server URL, dist directory, before/after build commands
- **Security** — CSP settings, capabilities, asset protocol scope, freeze prototype
- **Plugins** — registered plugin configurations and their settings
- **Bundle** — app identifier, icons, targets, resources, file associations

**When to direct user here:** When the user suspects a misconfigured capability, when a plugin isn't being loaded, when window properties are wrong, when security settings need verification, or when debugging build vs dev configuration differences.

**Bug class caught:** Missing permissions causing silent command failures, incorrect window sizes/titles, wrong CSP settings blocking resources, plugins not being registered, missing bundle resources, and incorrect app identifiers.

### Sources Tab
**Data shown:** Application source files and bundled assets as they exist in the running app.

**Features:**
- Browse the file tree of bundled assets
- View file contents directly in the UI
- Verify that expected files are included in the build
- Check resolved paths for assets referenced in code

**When to direct user here:** When the user reports a bundled image/asset not loading, when they need to verify that a file was correctly included in the build, when asset path resolution is behaving unexpectedly, or when CSP is blocking a resource.

**Bug class caught:** Missing assets, incorrect asset paths, files not being included in the bundle, path resolution differences between dev and production builds, and filename case-sensitivity issues on different platforms.

## Common Agent Workflows

### 1. "My Tauri command is slow"
Open the **Calls tab**. Filter by the command name. Look at the span duration. If the span shows >100ms, the bottleneck is in the Rust handler. If the span is fast but the UI feels slow, the bottleneck is in the frontend (use browser DevTools for that). Check for nested spans — a slow parent span might contain a slow child (e.g., database query, file I/O).

### 2. "I see a Rust error but can't find it"
Open the **Console tab**. Set filter to ERROR level. The error will include the source location (file, line number). If the error comes from a dependency crate, filter by that crate name. Look at the timestamps to correlate with user actions.

### 3. "My bundled image isn't loading"
Open the **Sources tab**. Navigate to the expected asset path. If the file isn't listed, it wasn't included in the bundle — check tauri.conf.json bundle settings. If it IS listed but shows the wrong content, the path resolution is incorrect. Compare the path the frontend is requesting (browser DevTools Network tab) with the path DevTools Sources shows.

### 4. "I don't know if my capability config is right"
Open the **Config tab**. Find the security.capabilities section. Verify the permissions list includes the required permission identifiers for the plugins being used. Cross-reference with the error messages in the Console tab — a missing capability usually produces a specific permission error.

### 5. "Which crate is spamming my terminal?"
Open the **Console tab**. Look at the target column for each log entry. Filter by different crate names until you identify the noisy one. Then either: (a) reduce its log level with `RUST_LOG=noisy_crate=warn`, or (b) add a tracing filter in code.

### 6. "My IPC call returns an error but I can't see why"
Open the **Calls tab**. Find the failed call (marked with error status). Expand the span to see the error response. Then switch to the **Console tab** and look at ERROR-level events around the same timestamp — the Rust handler likely logged the detailed error there. The combination of Calls + Console gives you both the "what failed" and "why it failed".

### 7. "I added a new plugin but it's not working"
Open the **Config tab** first. Verify the plugin appears in the Plugins section. If it doesn't, the plugin wasn't registered in lib.rs. If it does appear, check the Console tab for any initialization errors from that plugin's crate. Also verify the plugin's required capabilities are listed in the Security section.

### 8. "My app works in dev but not in the built version"
Open the **Config tab** and compare the resolved configuration with your tauri.conf.json. Look for environment-specific overrides. Check the **Sources tab** to verify all assets are bundled. Look in the **Console tab** for any errors that only appear in release-like configurations. Remember: if `#[cfg(debug_assertions)]` gates some logic, it won't run in release builds.

### 9. "My Tauri command works but returns wrong data"
Open the **Calls tab**. Find the command invocation. Examine the **Arguments** column to verify the frontend is sending the correct input. Then examine the **Response** column to see what the backend actually returned. Compare expected vs actual. If the arguments are wrong, fix the frontend invoke() call. If arguments are correct but response is wrong, the bug is in the Rust handler.

### 10. "I need to understand the order of operations at startup"
Open the **Console tab**. Look at the earliest timestamps to see the initialization sequence. Plugin initialization, command registration, and setup hook execution all produce tracing events. Sort by timestamp to see the exact order. Look for any gaps or unexpected ordering.

## Anti-Patterns Agents Must Avoid

### 1. Adding println!() to Rust instead of reading the Console tab
DevTools already captures all tracing output. Adding println!() bypasses the tracing subscriber entirely and won't appear in DevTools. Use `tracing::info!()` or `tracing::debug!()` macros instead, which DevTools captures automatically.

### 2. Guessing IPC latency without the Calls tab spans
Agents often add timing code (Instant::now() / .elapsed()) to both JS and Rust sides to measure IPC performance. The Calls tab already provides precise timing spans for every IPC call — including serialization overhead — without any code changes.

### 3. Assuming browser DevTools Network tab shows IPC calls
Tauri IPC calls do NOT appear in the browser's Network tab. They use a custom protocol (ipc:// on macOS, https://ipc.localhost on Windows). Only the CrabNebula DevTools Calls tab shows IPC traffic.

### 4. Shipping DevTools in release builds (security hole)
Never do this:
```rust
// WRONG — ships debug tooling to users
builder = builder.plugin(tauri_plugin_devtools::init());
```
Always wrap in `#[cfg(debug_assertions)]`:
```rust
// CORRECT
#[cfg(debug_assertions)]
{
    builder = builder.plugin(tauri_plugin_devtools::init());
}
```

### 5. Forgetting #[cfg(debug_assertions)] entirely
The devtools plugin starts a gRPC server that exposes application internals. In a release build, this would:
- Bloat the binary with the tracing subscriber, gRPC server, and all devtools dependencies
- Open a network port (6000-9000) that exposes application data
- Potentially conflict with production logging systems

### 6. Using log:: macros without attach_logger()
If the project uses tauri-plugin-log and its `log::info!()` style macros, those events won't appear in DevTools unless you use the `Builder::default().attach_logger(logger)` pattern with the .split() API. Without this, log events go to the log plugin but never reach the DevTools subscriber.

### 7. Registering DevTools after other plugins
Register DevTools **first** (or as early as possible) in the plugin chain. If other plugins initialize and emit tracing events before DevTools registers its subscriber, those early events will be lost. The basic pattern calls `tauri_plugin_devtools::init()` before `tauri::Builder::default()` for this reason.

### 8. Adding manual JSON serialization to debug IPC payloads
Agents sometimes add serde_json::to_string_pretty() calls to log IPC payloads manually. The Calls tab already shows serialized arguments and responses for every call. Don't add serialization code just for debugging — use the Calls tab instead.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| DevTools UI shows "No connection" | App not running or port blocked | Verify the app is running with cargo tauri dev. Check terminal output for the DevTools URL and port number. |
| Console tab is empty | No tracing subscriber registered | Ensure tauri_plugin_devtools::init() is called and the plugin is registered with the builder. |
| log::info!() events missing from Console | Logger not attached to DevTools | Use the Builder::default().attach_logger(logger) pattern with tauri_plugin_log::Builder::new().split(). |
| Calls tab shows no IPC calls | Frontend not using invoke() | Verify the frontend calls invoke('command_name', args) from @tauri-apps/api/core. |
| Config tab shows unexpected values | Environment overrides active | Check for TAURI_CONFIG environment variable or platform-specific config overrides. |
| Port conflict on startup | Another instance or service using 6000-9000 range | Stop the other process or restart your app (port is dynamically allocated, it will pick a free one). |
| Android: can't connect to DevTools | Port forwarding not set up | Run adb forward tcp:PORT tcp:PORT with the port shown in logcat output. |
| Slow app startup with DevTools | Many plugins emitting tracing events at init | This is normal — DevTools captures everything. Startup overhead is typically under 100ms. |
| "probe" plugin conflict error | Multiple DevTools instances registered | Ensure only one tauri_plugin_devtools::init() or Builder::default().init() call exists. The internal plugin name is "probe". |
| Spans missing for custom functions | Functions not instrumented | Add #[tracing::instrument] attribute to functions you want to appear as spans in DevTools. |
| DevTools works in dev but not in release | #[cfg(debug_assertions)] gate working correctly | This is expected behavior. DevTools should NOT run in release builds. |
| Premium app: keyboard shortcut not working | Wrong crate imported | Ensure you're using tauri-plugin-devtools-app (not tauri-plugin-devtools) for the embedded panel with Ctrl/Cmd+Shift+M. |

## Version History and Breaking Changes

| Version | Tauri Compat | Key Changes |
|---|---|---|
| tauri-plugin-devtools 2.0.0 | Tauri v2 | Current stable. Module: tauri_plugin_devtools. Crate name uses hyphens, module uses underscores. |
| devtools (pre-2.0) | Tauri v1 | Legacy crate name. If migrating from Tauri v1, change devtools to tauri-plugin-devtools in Cargo.toml and update all use devtools:: to use tauri_plugin_devtools::. |

**Migration from Tauri v1 to v2:**
1. Change dependency: devtools to tauri-plugin-devtools = "2.0.0"
2. Update imports: use devtools:: to use tauri_plugin_devtools::
3. Update init: The init() function and Builder API remain the same
4. Verify: #[cfg(debug_assertions)] pattern still works identically

**Key naming conventions:**
- Cargo crate: tauri-plugin-devtools (hyphens)
- Rust module: tauri_plugin_devtools (underscores)
- Internal Tauri plugin name: "probe"
- Premium crate: tauri-plugin-devtools-app
- Premium module: tauri_plugin_devtools_app

## Reference Files

| File | Contents |
|---|---|
| references/devtools-tab-reference.md | Detailed per-tab column reference, filtering syntax, keyboard shortcuts |
| references/devtools-ipc-span-anatomy.md | IPC span structure, field details, timing interpretation, custom spans |
| references/devtools-architecture-deep-dive.md | Internal tracing pipeline: BridgeLayer to Layer to Aggregator to Server |
| references/devtools-common-debugging-scenarios.md | 12+ concrete debugging scenarios with symptoms, tabs, and fixes |
| references/devtools-integration-patterns.md | Integration with tauri-plugin-log, custom subscribers, cfg patterns |
