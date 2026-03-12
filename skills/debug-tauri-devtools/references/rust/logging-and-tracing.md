# Logging & Tracing — CrabNebula DevTools

> ⚠️ **Steering:** This is the most commonly needed reference during debugging. Key rule: NEVER use `println!()` for debugging in Tauri apps. `println!()` output goes to stdout and is INVISIBLE to DevTools. Always use `tracing::info!()`, `tracing::debug!()`, etc. In derailment testing, agents used `println!()` and then concluded their code wasn't executing because no output appeared in DevTools.

## How DevTools Captures Logs

DevTools registers a `tracing` subscriber that intercepts all spans and events. Three types of log sources exist:

| Source | Captured by DevTools? | Appears in Console Tab? |
|---|---|---|
| `tracing::info!()`, `tracing::debug!()`, etc. | Yes — automatically | Yes |
| `log::info!()`, `log::debug!()`, etc. | Only with `attach_logger()` | Yes, if attached |
| `println!()`, `eprintln!()` | No — bypasses tracing entirely | No |

**Rule:** Never use `println!()` for debugging in a Tauri app. Use `tracing` macros instead.

## Tracing Macros Quick Reference

```rust
// Events (appear in Console tab)
tracing::trace!("Very detailed diagnostic info");
tracing::debug!("Development diagnostics");
tracing::info!("Normal operational messages");
tracing::warn!("Potential issues");
tracing::error!("Failures and exceptions");

// Events with structured fields (appear in Console Fields column)
tracing::info!(user_id = 42, action = "login", "User logged in");
tracing::error!(error = %err, path = %file_path, "Failed to read file");

// Dynamic level
tracing::event!(tracing::Level::INFO, "Message at info level");
```

## RUST_LOG Environment Variable

### How RUST_LOG Affects DevTools

> ⚠️ **Steering:** When debugging, use targeted `RUST_LOG` filters. `RUST_LOG=debug` enables ALL debug output including noisy dependencies like `hyper`, `tonic`, `h2`. Instead, use: `RUST_LOG=warn,my_app=debug,tauri=info`. This shows your app's debug logs while suppressing dependency noise.

`RUST_LOG` acts as a pre-filter at the subscriber level. Events filtered out by `RUST_LOG` are never created, never transmitted to DevTools, and cannot be recovered.

```bash
# No RUST_LOG — DevTools captures EVERYTHING (default)
cargo tauri dev

# Only warnings and errors reach DevTools
RUST_LOG=warn cargo tauri dev

# Debug for your code, warn for dependencies
RUST_LOG=warn,my_app=debug cargo tauri dev

# Trace for a specific module
RUST_LOG=warn,my_app::commands::file_ops=trace cargo tauri dev

# Suppress a noisy dependency
RUST_LOG=debug,hyper=warn,tonic=warn cargo tauri dev

# Only your code's output
RUST_LOG=off,my_app=debug cargo tauri dev
```

### RUST_LOG vs DevTools UI Filtering

| Aspect | RUST_LOG | DevTools UI Filter |
|---|---|---|
| When applied | At event creation time | At display time |
| Events captured | Only matching events | All events (filter is visual) |
| Requires restart | Yes (env var) | No (instant toggle) |
| Reduces overhead | Yes (events not created) | No (events still transmitted) |
| Recoverable | No (filtered events lost) | Yes (toggle filter off) |

**Recommendation:** Don't set `RUST_LOG` unless you have extreme logging throughput. Let DevTools capture everything and filter in the UI.

### Common RUST_LOG Patterns

| Pattern | Effect |
|---|---|
| `RUST_LOG=debug` | All debug and above from all crates |
| `RUST_LOG=warn,my_app=debug` | Debug for your code, warn for deps |
| `RUST_LOG=warn,my_app=trace` | Trace for your code (very verbose) |
| `RUST_LOG=error,tauri=info,my_app=debug` | Minimal noise, info from Tauri, debug for you |
| `RUST_LOG=off,my_app=debug` | Only your code |
| `RUST_LOG=warn,sqlx=debug` | Debug SQL queries, warn for everything else |

## Creating Custom Spans

### Attribute Macro (Recommended)

```rust
#[tracing::instrument]
async fn fetch_user(user_id: i64) -> Result<User, Error> {
    // Creates span named "fetch_user" with field user_id=<value>
    db.query_one("SELECT * FROM users WHERE id = $1", &[&user_id]).await
}
```

### Manual Span Creation (Async)

> ⚠️ **Steering:** For inline code that isn't in a separate function, use manual spans instead of trying to extract a function: `let _span = tracing::info_span!("process_item", item_id = %id).entered();`. The underscore prefix is critical — without it, the span is immediately dropped and records zero duration.

```rust
use tracing::{info_span, Instrument};

async fn complex_operation(items: Vec<Item>) -> Result<Report, Error> {
    let parse_span = info_span!("parse_items", count = items.len());
    let parsed = async {
        parse_all(&items).await
    }.instrument(parse_span).await;

    let render_span = info_span!("render_report", pages = parsed.page_count());
    let report = async {
        render(parsed).await
    }.instrument(render_span).await;

    Ok(report)
}
```

### Manual Span Creation (Sync)

```rust
fn process_data(data: &[Record]) -> ProcessedData {
    let _span = tracing::info_span!("validate_records", count = data.len()).entered();
    validate(data);
    drop(_span);  // Explicitly close span — duration is recorded

    let _span = tracing::info_span!("transform_records").entered();
    let result = transform(data);
    drop(_span);

    result
}
```

### Span Best Practices

| Do | Don't |
|---|---|
| Instrument I/O operations (DB, file, network) | Instrument every function |
| Skip large args: `#[tracing::instrument(skip(payload))]` | Log passwords or secrets |
| Use custom names for clarity | Use default names for internal functions |
| Add meaningful fields: `fields(table = "users")` | Add too many fields (hurts perf) |
| Use `err` for automatic error logging | Manually log every error |

## Integration with tauri-plugin-log

### The Problem

Both `tauri-plugin-log` and DevTools want to set the global tracing/log subscriber. If you register both naively, you get:

```
thread 'main' panicked at: error while running tauri application:
PluginInitialization("log", "attempted to set a logger after the
logging system was already initialized")
```

### The Solution: split() Pattern

> ⚠️ **Steering:** If your project uses `tauri-plugin-log`, you MUST use the `split()/attach_logger()` pattern (Pattern 2 in installation-and-config.md). Agents in testing tried to: (a) remove tauri-plugin-log (broke existing features), (b) initialize both independently (got PluginInitialization error), (c) use a custom subscriber bridge (unnecessary complexity). The split pattern is the only supported approach.

```rust
tauri::Builder::default()
    .setup(|app| {
        let (tauri_plugin_log, max_level, logger) =
            tauri_plugin_log::Builder::new()
                .level(log::LevelFilter::Debug)
                .split(app.handle())?;

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
```

### What attach_logger() Does

1. Takes ownership of the `tauri-plugin-log` logger
2. Integrates it into the DevTools tracing subscriber
3. Routes all `log::` crate events through the DevTools pipeline
4. These events appear in DevTools Console alongside native `tracing::` events

Without `attach_logger()`: events from crates using `log` (not `tracing`) won't appear in DevTools.

## Tracing Levels in DevTools Console

| Level | Color | When to Use |
|---|---|---|
| TRACE | Grey/dim | Very detailed diagnostics, usually hidden |
| DEBUG | Blue | Development diagnostics, variable values |
| INFO | Green | Normal operational events |
| WARN | Yellow/orange | Potential issues, degraded behavior |
| ERROR | Red | Failures requiring attention |

## Finding Log Sources

The **Target** column in the Console tab shows the Rust module path:
- `my_app::commands::file_ops` → `src/commands/file_ops.rs`
- `sqlx::query` → from the sqlx database crate
- `tauri::ipc` → from Tauri core IPC handling
- `hyper::proto` → from the hyper HTTP crate

Use target filtering to isolate logs from specific modules or crates.

## Custom Tracing Subscriber in Release

```rust
#[cfg(debug_assertions)]
{
    let devtools = tauri_plugin_devtools::init();
    builder = builder.plugin(devtools);
    // DevTools sets the global subscriber
}

#[cfg(not(debug_assertions))]
{
    // In release, use your own subscriber
    let subscriber = tracing_subscriber::fmt()
        .with_env_filter("info,my_app=debug")
        .finish();
    tracing::subscriber::set_global_default(subscriber)
        .expect("setting default subscriber failed");
}
```

DevTools manages its own subscriber. You cannot call `set_global_default()` when DevTools is active — only one global default is allowed.

## Dependency Checklist

Before adding any tracing instrumentation, verify these dependencies in `Cargo.toml`:

| What you're doing | Required in Cargo.toml |
|---|---|
| Basic tracing events (`info!`, `debug!`, etc.) | `tracing = "0.1"` |
| `#[tracing::instrument]` attribute | `tracing = "0.1"` |
| `.instrument()` on async blocks | `tracing = "0.1"` + `use tracing::Instrument;` in code |
| Custom subscriber layers | `tracing-subscriber = "0.3"` |
| Log crate bridging | `tracing-log = "0.2"` (usually handled by DevTools) |

> ⚠️ **Steering:** Missing the `tracing` dependency was the #2 most common agent error in derailment testing (after skipping DevTools installation check). Always verify before instrumenting.
