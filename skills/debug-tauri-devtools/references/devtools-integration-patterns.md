# Integration Patterns — CrabNebula DevTools

## Using DevTools with tauri-plugin-log

### The Problem

`tauri-plugin-log` and CrabNebula DevTools both want to be the tracing/log subscriber. If you naively register both, they conflict — events may go to one subscriber but not the other. The solution is the **split pattern**.

### The split() Pattern (Recommended)

The `tauri-plugin-log::Builder::new().split()` method separates the log plugin into three components:
1. The Tauri plugin instance (handles webview-side log display)
2. The max log level setting
3. The raw logger (can be attached to DevTools)

```rust
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            // split() gives us the plugin, max level, and raw logger separately
            let (tauri_plugin_log, max_level, logger) =
                tauri_plugin_log::Builder::new()
                    .level(log::LevelFilter::Debug)
                    .split(app.handle())?;

            #[cfg(debug_assertions)]
            {
                // In debug: attach the logger to DevTools
                // DevTools becomes the subscriber for BOTH tracing and log events
                let mut devtools_builder = tauri_plugin_devtools::Builder::default();
                devtools_builder.attach_logger(logger);
                app.handle().plugin(devtools_builder.init())?;
            }

            #[cfg(not(debug_assertions))]
            {
                // In release: attach the logger normally
                // log events go to the standard log plugin destinations
                tauri_plugin_log::attach_logger(max_level, logger);
            }

            // Always register the log plugin itself
            app.handle().plugin(tauri_plugin_log)?;
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

### What attach_logger() Does

When you call `devtools_builder.attach_logger(logger)`, it:
1. Takes ownership of the `tauri-plugin-log` logger instance
2. Integrates it into the DevTools tracing subscriber
3. Routes all `log::` crate events (from dependencies using `log::info!()`, `log::error!()`, etc.) through the DevTools pipeline
4. These events then appear in the DevTools Console tab alongside native `tracing::` events

Without `attach_logger()`, events from crates using the `log` crate (not `tracing`) will NOT appear in DevTools.

### When NOT to Use split()

If your project does NOT use `tauri-plugin-log` at all, don't use the split pattern. Use the simple init pattern:

```rust
#[cfg(debug_assertions)]
let devtools = tauri_plugin_devtools::init();
```

The split pattern is only needed when both `tauri-plugin-log` AND `tauri-plugin-devtools` are in the dependency tree.

## Using DevTools with Custom Tracing Subscribers

### DevTools Manages Its Own Subscriber

DevTools calls `tracing::subscriber::set_global_default()` internally. This means you CANNOT also call `set_global_default()` with your own subscriber — only one global default is allowed.

If you need custom tracing behavior alongside DevTools:

**Option A: Use DevTools in debug, custom subscriber in release**
```rust
#[cfg(debug_assertions)]
{
    let devtools = tauri_plugin_devtools::init();
    builder = builder.plugin(devtools);
    // DevTools sets the global subscriber
}

#[cfg(not(debug_assertions))]
{
    // In release, set your own subscriber
    let subscriber = tracing_subscriber::fmt()
        .with_env_filter("info,my_app=debug")
        .finish();
    tracing::subscriber::set_global_default(subscriber)
        .expect("setting default subscriber failed");
}
```

**Option B: Use attach_logger for log-crate compatibility**
If you just need `log::` events to appear in DevTools, use the `attach_logger()` pattern described above. You don't need a custom subscriber for that.

### Tracing Filters and DevTools

DevTools captures events at ALL levels by default. The Console tab's level filter is applied in the UI, not at the subscriber level. This means:
- TRACE-level events ARE captured and transmitted (they just might be hidden in the UI)
- You can filter in the UI without restarting the app
- This does mean slightly more data is transmitted than if filtered at the subscriber level

## cfg(debug_assertions) vs cfg(dev) vs Feature Flags

### #[cfg(debug_assertions)] — Use This (Recommended)

```rust
#[cfg(debug_assertions)]
{
    let devtools = tauri_plugin_devtools::init();
    builder = builder.plugin(devtools);
}
```

- Active when: `cargo build` (no `--release` flag), `cargo tauri dev`
- Inactive when: `cargo build --release`, `cargo tauri build`
- This is the standard Rust mechanism. Use this for DevTools.

### #[cfg(dev)] — Does NOT Exist in Standard Rust

There is no `#[cfg(dev)]` in standard Rust. Don't use it. If you see it in other contexts, it's a custom cfg flag, not a Rust built-in.

### Feature Flags — Use for Optional Debug Dependencies

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

Use feature flags when you want fine-grained control beyond just debug/release. For example, if you want DevTools in CI builds but not local release builds. For most projects, `#[cfg(debug_assertions)]` is simpler and sufficient.

### Comparison Table

| Method | Active In | Inactive In | Best For |
|---|---|---|---|
| `#[cfg(debug_assertions)]` | `cargo build`, `cargo tauri dev` | `cargo build --release`, `cargo tauri build` | Most projects (recommended) |
| `#[cfg(feature = "devtools")]` | When `--features devtools` is passed | Default builds | Fine-grained control, CI configs |
| Unconditional (no gate) | Always | Never | ❌ NEVER do this for DevTools |

## Adding Custom Spans with #[tracing::instrument]

### Basic Usage

Add `#[tracing::instrument]` to any function to make it appear as a span in DevTools:

```rust
#[tracing::instrument]
async fn fetch_user(user_id: i64) -> Result<User, Error> {
    // This function call will appear as a span in the Calls tab
    // with the name "fetch_user" and field user_id=<value>
    db.query_one("SELECT * FROM users WHERE id = $1", &[&user_id]).await
}
```

### Skipping Large Arguments

For arguments that are large or not useful for debugging, use `skip`:

```rust
#[tracing::instrument(skip(db_pool, file_contents))]
async fn save_file(
    db_pool: &Pool,
    filename: &str,
    file_contents: &[u8],
) -> Result<(), Error> {
    // db_pool and file_contents won't be serialized into the span
    // filename WILL appear as a field
}
```

### Custom Span Names

```rust
#[tracing::instrument(name = "database_query")]
async fn internal_query_fn(sql: &str) -> Result<Vec<Row>, Error> {
    // Appears as "database_query" in DevTools, not "internal_query_fn"
}
```

### Adding Fields

```rust
#[tracing::instrument(fields(table = "users", operation = "insert"))]
async fn create_user(name: &str) -> Result<User, Error> {
    // Span will include: table="users", operation="insert", name=<value>
}
```

### Manual Spans (without attribute macro)

For more control, create spans manually:

```rust
use tracing::{info_span, Instrument};

async fn complex_operation() {
    let span = info_span!("data_processing", items = 42);

    async {
        // Everything in this block is inside the "data_processing" span
        process_items().await;
    }
    .instrument(span)
    .await;
}
```

### Timing Measurements with Spans

Use spans to measure specific code sections:

```rust
fn process_report(data: &[Record]) -> Report {
    let _parse_span = tracing::info_span!("parse_records", count = data.len()).entered();
    let parsed = parse_all(data);
    drop(_parse_span);

    let _render_span = tracing::info_span!("render_report", pages = parsed.page_count()).entered();
    let report = render(parsed);
    drop(_render_span);

    report
}
```

Each span will appear in DevTools with its own duration, letting you see exactly how long parsing vs rendering takes.

## RUST_LOG Environment Variable Interaction

### How RUST_LOG Affects DevTools

When DevTools is active, `RUST_LOG` affects which events reach the tracing subscriber. DevTools captures whatever the subscriber receives, so `RUST_LOG` acts as a pre-filter:

```bash
# Show everything (DevTools default behavior without RUST_LOG)
cargo tauri dev

# Only show warnings and errors in DevTools Console
RUST_LOG=warn cargo tauri dev

# Show debug for your app, warn for dependencies
RUST_LOG=warn,my_app=debug cargo tauri dev

# Show trace for a specific module
RUST_LOG=warn,my_app::commands::file_ops=trace cargo tauri dev
```

### Common RUST_LOG Patterns for DevTools

| Pattern | Effect in DevTools |
|---|---|
| `RUST_LOG=debug` | All debug and above from all crates |
| `RUST_LOG=warn,my_app=debug` | Debug for your code, warn for deps |
| `RUST_LOG=warn,my_app=trace` | Trace for your code (very verbose) |
| `RUST_LOG=error,tauri=info,my_app=debug` | Minimal dep noise, info from Tauri, debug for your code |
| `RUST_LOG=off,my_app=debug` | Only your code's debug output |

### RUST_LOG vs DevTools UI Filtering

| Aspect | RUST_LOG | DevTools UI Filter |
|---|---|---|
| When applied | At event creation time | At display time |
| Events captured | Only matching events | All events (filter is visual only) |
| Requires restart | Yes (env var) | No (instant toggle) |
| Reduces overhead | Yes (events not created) | No (events still transmitted) |
| Recoverable | No (filtered events are lost) | Yes (toggle filter off to see all) |

**Recommendation:** In most cases, don't set `RUST_LOG` and let DevTools capture everything. Use the Console tab's UI filters to control what you see. Only set `RUST_LOG` if you have extreme logging throughput causing performance issues.

## Using DevTools Alongside Other Plugins

### Plugin Registration Order

Register DevTools **first** so its tracing subscriber captures initialization events from subsequent plugins:

```rust
let mut builder = tauri::Builder::default();

#[cfg(debug_assertions)]
{
    // FIRST: DevTools — captures tracing from all subsequent plugin inits
    let devtools = tauri_plugin_devtools::init();
    builder = builder.plugin(devtools);
}

// THEN: Other plugins — their init tracing events are captured
builder = builder
    .plugin(tauri_plugin_opener::init())
    .plugin(tauri_plugin_store::Builder::new().build())
    .plugin(tauri_plugin_fs::init());
```

### Plugins That Emit Tracing Events

Most Tauri plugins use `tracing` internally. Once DevTools is registered, you'll automatically see their events in the Console tab:
- `tauri` core — IPC handling, window management, asset protocol
- `tauri-plugin-store` — store read/write operations
- `tauri-plugin-fs` — filesystem operations
- `tauri-plugin-http` — HTTP client operations

### No Conflicts with Most Plugins

DevTools does NOT conflict with other Tauri plugins. It's a passive observer that registers a tracing subscriber. It doesn't modify IPC behavior, window management, or any other plugin's functionality. The only potential conflict is with other plugins that also try to set a global tracing subscriber — in practice, only `tauri-plugin-log` does this, and the `split()/attach_logger()` pattern resolves it.
