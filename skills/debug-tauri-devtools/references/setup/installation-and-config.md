# Installation & Configuration — CrabNebula DevTools

## Crate Selection

| Crate | Purpose | Install |
|---|---|---|
| `tauri-plugin-devtools` | Free web UI (browser-based) | `cargo add tauri-plugin-devtools@2` |
| `tauri-plugin-devtools-app` | Premium embedded desktop panel | `cargo add tauri-plugin-devtools-app@2` |
| `devtools` | Legacy Tauri v1 only | `cargo add devtools` (do NOT use for v2) |

Use `tauri-plugin-devtools` (free web UI) unless the user specifically requests the premium desktop panel.

Current stable versions (Tauri v2):
- `tauri-plugin-devtools = "2.0.1"`
- `tauri-plugin-devtools-app = "2.0.1"`
- Internal core: `devtools-core = "0.3.6"`

> ⚠️ **Steering:** Default to `tauri-plugin-devtools` (free web UI). Only use the premium desktop panel if the user explicitly requests it, and do not use the legacy `devtools` crate for Tauri v2.

> **Version guardrail:** Prefer an explicit major-version install (`cargo add ...@2` or manual `= "2"` in `Cargo.toml`). If `cargo add` warns that your pinned `rust-version` is too old and silently chooses an older plugin, stop and either raise the project's `rust-version`/toolchain or edit `Cargo.toml` manually. Do not proceed assuming the downgraded crate behaves like the current v2 docs.

## Cargo.toml Setup

### Minimal (free web UI)

```toml
[dependencies]
tauri = "2"
tauri-plugin-devtools = "2"
tracing = "0.1"  # needed if you add custom tracing events
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

## Which Pattern to Use

| Your project has... | Use |
|---|---|
| No `tauri-plugin-log` | Pattern 1 (Basic) |
| `tauri-plugin-log` | Pattern 2 (split) |
| Premium license | Pattern 3 |
| Optional dependency via feature flag | Pattern 5 |

Pattern 4 is an extended example of Pattern 1 with more plugins — choose Pattern 1 and add your plugins after the DevTools plugin. All patterns work with any number of other plugins.

> ⚠️ **Steering:** If unsure, use Pattern 1. Pattern 2 is ONLY for projects that already use `tauri-plugin-log`.

Concrete check:

```bash
rg -n "tauri-plugin-log" src-tauri/Cargo.toml
```

No match → Pattern 1. Match → Pattern 2.

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

**Integrating with existing code:** To add DevTools to an existing `run()` function:
1. Add `#[cfg(debug_assertions)] let devtools = tauri_plugin_devtools::init();` on the line immediately ABOVE your existing `tauri::Builder::default()` call.
2. Add the `#[cfg(debug_assertions)] { builder = builder.plugin(devtools); }` block BEFORE your other `.plugin()` calls. Equivalently, you can insert `.plugin(devtools)` into your existing builder chain.
3. Keep all existing `.manage()`, `.plugin()`, `.invoke_handler()`, and `.setup()` chains intact.

Why `init()` comes first: The `init()` call creates the tracing subscriber. Events emitted before the subscriber is registered are lost forever. Calling it before `Builder::default()` ensures plugin initialization events from other plugins are captured.

> ⚠️ **Steering:** The `init()` call MUST come before `Builder::default()`. Registering it later loses early plugin initialization events, so DevTools may connect but still miss the evidence you need.

### Pattern 2: With tauri-plugin-log (split pattern)

> **Use Pattern 2 ONLY if your project uses `tauri-plugin-log`.** If it doesn't, use Pattern 1.

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

> **Note:** `tauri_plugin_devtools_app` (premium) uses a different internal architecture than `tauri_plugin_devtools` (free). The premium crate's `init()` does not create a standalone tracing subscriber in the same way, so the ordering constraint (init before Builder) is less critical. However, registering early is still recommended.

### Pattern 4: Multi-plugin project

```rust
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    // IMPORTANT: init() BEFORE Builder::default() to capture all tracing events
    #[cfg(debug_assertions)]
    let devtools = tauri_plugin_devtools::init();

    let mut builder = tauri::Builder::default();

    // DevTools FIRST — captures init tracing from all subsequent plugins
    #[cfg(debug_assertions)]
    {
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

> ⚠️ **Steering:** First compilation after adding DevTools takes significantly longer (new dependency tree). Wait for the connection banner in terminal output before treating startup as hung.

### Free web UI

1. Run your app from the project root (where `package.json` lives): `cargo tauri dev`
2. First run after adding DevTools triggers a longer recompilation (new dependencies). Wait for the listener or dashboard URL to appear.
3. Look for terminal output like either of these:
   ```
   devtools: listening on ws://127.0.0.1:7043
   ```
   or
   ```
   https://devtools.crabnebula.dev/dash/127.0.0.1/3033
   ```
4. Open https://devtools.crabnebula.dev in any browser
5. Paste the connection URL from the terminal, or open the dashboard URL directly if the plugin prints that form instead

If `cargo tauri dev` exits before printing any DevTools banner:

1. Inspect `src-tauri/tauri.conf.json` for `beforeDevCommand`
2. Ensure the referenced package-manager script actually exists in `package.json`
3. For a smoke test, it is acceptable to temporarily clear `beforeDevCommand` so the Tauri app can start and prove DevTools wiring

### Minimal smoke test in an existing Tauri project

Use this path when the goal is to prove DevTools wiring, not diagnose a product bug.

1. Add a temporary command in `src-tauri/src/lib.rs`, `main.rs`, or the app entrypoint module:
   ```rust
   #[tauri::command]
   fn devtools_smoke_ping() -> &'static str {
       "pong"
   }
   ```
2. Register that command in the existing `invoke_handler`.
3. Trigger it once from the frontend:
   ```ts
   import { invoke } from "@tauri-apps/api/core";

   await invoke("devtools_smoke_ping");
   ```
   If there is no convenient UI action, call it from a temporary button or one-off startup effect.
4. Run `cargo tauri dev` from the project root.
5. Verify:
   - terminal prints the DevTools listener banner or dashboard URL
   - either startup emits a trace/event to stderr, or the `devtools_smoke_ping` call prints a matching command span
   - UI mode: the call appears in Calls
   - terminal-only mode: the command span or matching trace appears on stderr
6. Remove temporary smoke-test-only command code after wiring is proven.

### Premium desktop app

1. Download the DevTools Desktop app from CrabNebula
2. The embedded panel auto-connects — no URL pasting needed
3. Toggle with **Cmd+Shift+M** (macOS) or **Ctrl+Shift+M** (Windows/Linux)

## Verifying DevTools Works

After connecting in the browser:

1. **Console tab** — should show Tauri initialization log entries (target: `tauri::*`).
2. **Config → Plugins** — should list your registered plugins (e.g., opener, fs, store).
3. **Calls tab** — invoke any `#[tauri::command]` from the frontend. It should appear with Arguments and Response columns populated. Tauri IPC commands are automatically instrumented — no additional code needed.
4. If the dashboard is blank or shows no data:
   - **Pattern 1 (basic):** verify `init()` is called BEFORE `Builder::default()`. This ensures the tracing subscriber is active before any builder events.
   - **Other patterns:** verify the DevTools plugin is registered before `.run()`. The critical requirement is that the tracing subscriber is active before events you want to capture.
   - Confirm you are running `cargo tauri dev` (not a release build).

> ⚠️ **Steering:** If the dashboard is blank, the most common cause is init() being called too late. Check the ordering. The second most common cause is running a release build (`cargo tauri build` instead of `cargo tauri dev`).

### Terminal-only verification (AI agent / no UI)

If you cannot open the DevTools UI, use this checklist instead:

1. `cargo tauri dev` prints a DevTools listener banner or dashboard URL
2. stderr shows proof that the subscriber is live: either an existing startup trace/event, or the first invoked command span
3. after invoking any `#[tauri::command]`, a matching tracing event/span appears on stderr
4. if you added temporary `tracing::info!` or `#[tracing::instrument]`, the event appears exactly once where expected

If any step fails, DevTools is not yet verified.

After verifying DevTools works, return to the main SKILL.md workflow at Phase 2.

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

> ⚠️ **Steering:** The error `PluginInitialization('log', ...)` is the most common installation error. It means both DevTools and tauri-plugin-log try to set the global subscriber. The ONLY fix is Pattern 2 (split pattern). Do NOT try to remove tauri-plugin-log — use split().

## Naming Conventions

| Context | Name |
|---|---|
| Cargo crate (Cargo.toml) | `tauri-plugin-devtools` (hyphens) |
| Rust module (use/import) | `tauri_plugin_devtools` (underscores) |
| Internal Tauri plugin name | `"probe"` |
| Premium crate | `tauri-plugin-devtools-app` |
| Premium module | `tauri_plugin_devtools_app` |
| Legacy v1 crate | `devtools` |
