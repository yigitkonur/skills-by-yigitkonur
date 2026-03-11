# Rust Backend Debugging — Tauri DevTools

## Debugging Command Handlers

### Adding Instrumentation to Commands

Every `#[tauri::command]` function automatically gets an IPC span in DevTools. To see what happens inside the handler, add `#[tracing::instrument]`:

```rust
#[tauri::command]
#[tracing::instrument(skip(state), fields(op = "update_user"))]
async fn update_user(
    id: u32,
    name: String,
    state: tauri::State<'_, AppState>,
) -> Result<User, String> {
    // This function appears as a span with fields: op="update_user", id=<val>, name=<val>
    // state is skipped (not serializable)
    let user = state.db.update_user(id, &name).await
        .map_err(|e| {
            tracing::error!("Failed to update user {}: {:?}", id, e);
            format!("Update failed: {}", e)
        })?;
    tracing::info!("User {} updated successfully", id);
    Ok(user)
}
```

### What to Instrument

| Function Type | Instrument? | Why |
|---|---|---|
| Command handlers | Already traced by DevTools | IPC spans are automatic |
| Database queries | Yes | Shows query timing as child spans |
| File I/O operations | Yes | Identifies slow disk operations |
| Network requests | Yes | Shows external API latency |
| CPU-heavy computation | Yes | Identifies processing bottlenecks |
| Simple getters/setters | No | Too granular, adds noise |
| Utility/helper functions | Only if > 1ms | Don't instrument trivial logic |

### Instrument Options Reference

```rust
// Basic — captures all args as Debug format
#[tracing::instrument]
async fn basic(id: u32) -> Result<(), Error> { ... }

// Skip large/sensitive args
#[tracing::instrument(skip(db_pool, password))]
async fn auth(db_pool: &Pool, username: &str, password: &str) -> Result<Token, Error> { ... }

// Skip ALL args
#[tracing::instrument(skip_all)]
async fn process(data: &[u8]) -> Result<(), Error> { ... }

// Custom span name
#[tracing::instrument(name = "database_query")]
async fn internal_query(sql: &str) -> Result<Vec<Row>, Error> { ... }

// Additional fields
#[tracing::instrument(fields(table = "users", operation = "upsert"))]
async fn save_user(user: &User) -> Result<(), Error> { ... }

// Set level (default is INFO)
#[tracing::instrument(level = "debug")]
async fn verbose_op() -> Result<(), Error> { ... }

// Error handling — auto-logs errors
#[tracing::instrument(err)]
async fn fallible() -> Result<String, MyError> { ... }

// Return value logging
#[tracing::instrument(ret)]
async fn computed() -> u64 { ... }
```

## Debugging State Management

### Common State Issues

```rust
// SETUP: Registering state
tauri::Builder::default()
    .manage(AppState::new())  // State must be Send + Sync + 'static
    .invoke_handler(tauri::generate_handler![get_data, set_data])
```

| Error | Cause | Fix |
|---|---|---|
| `State not managed: AppState` | `.manage()` not called before `.run()` | Add `.manage(AppState::new())` to builder |
| `the trait Send is not implemented` | State type not thread-safe | Wrap in `Arc<Mutex<T>>` or use `tokio::sync::RwLock` |
| Deadlock (app freezes) | Nested mutex locks in same task | Use separate locks per resource, or `tokio::task::spawn_blocking` |
| Stale data | Race condition on shared state | Use `RwLock` for read-heavy, `Mutex` for write-heavy |
| `State not found` | Accessing state before `setup()` completes | Move state access to `setup()` callback or later |

### Debugging Deadlocks

```rust
// BAD: Potential deadlock — locking two mutexes in different order
#[tauri::command]
async fn bad_handler(
    state_a: tauri::State<'_, Arc<Mutex<A>>>,
    state_b: tauri::State<'_, Arc<Mutex<B>>>,
) -> Result<(), String> {
    let a = state_a.lock().await;  // Lock A first
    let b = state_b.lock().await;  // Then lock B — deadlock if another task locks B then A
    // ...
}

// GOOD: Lock one at a time, release before acquiring next
#[tauri::command]
async fn good_handler(
    state_a: tauri::State<'_, Arc<Mutex<A>>>,
    state_b: tauri::State<'_, Arc<Mutex<B>>>,
) -> Result<(), String> {
    let data_a = {
        let a = state_a.lock().await;
        a.clone_data()
    }; // Lock released here
    let mut b = state_b.lock().await;
    b.update_with(data_a);
    Ok(())
}
```

Add tracing to debug lock contention:
```rust
#[tracing::instrument(skip(state))]
async fn debug_locks(state: tauri::State<'_, Arc<Mutex<Data>>>) -> Result<(), String> {
    tracing::debug!("Acquiring lock...");
    let guard = state.lock().await;
    tracing::debug!("Lock acquired, data len: {}", guard.items.len());
    // ... use data ...
    drop(guard);
    tracing::debug!("Lock released");
    Ok(())
}
```

## Debugging Serialization Errors

### Common serde Mismatches Between JS and Rust

| JS Value | Rust Type Expected | Error | Fix |
|---|---|---|---|
| `"42"` (string) | `u32` | `invalid type: string "42", expected u32` | Parse in JS: `parseInt(val)` or use `String` in Rust |
| `{ userName: "alice" }` | `struct { user_name: String }` | `missing field user_name` | Add `#[serde(rename_all = "camelCase")]` to struct |
| `null` | `String` | `invalid type: null, expected a string` | Use `Option<String>` in Rust |
| `[1, 2, 3]` | `(u32, u32, u32)` | Works but fragile | Use `Vec<u32>` instead of tuple |
| `{ type: "admin" }` | `enum Role { Admin, User }` | `unknown variant "admin"` | Add `#[serde(rename_all = "lowercase")]` to enum |
| Large payload (> 1MB) | `Vec<u8>` | Timeout or OOM | Chunk the data or use file-based transfer |

### Diagnosing Serialization Issues with DevTools

1. Open the **Calls tab** in DevTools
2. Find the failing command invocation
3. Examine the **Arguments** column — this shows the raw JSON the frontend sent
4. Compare with the Rust struct definition
5. The **Response** column shows the serde error message with exact field/type mismatch

```rust
// Debug struct to see what serde expects
#[derive(Debug, serde::Deserialize, serde::Serialize)]
#[serde(rename_all = "camelCase")]  // JS sends camelCase, Rust uses snake_case
pub struct UserInput {
    pub user_name: String,           // JS: { userName: "..." }
    pub email: Option<String>,       // JS: { email: "..." } or omitted
    #[serde(default)]
    pub is_admin: bool,              // JS: { isAdmin: true } or defaults to false
    #[serde(default = "default_role")]
    pub role: String,                // Defaults to "user" if not provided
}

fn default_role() -> String { "user".into() }
```

### Using cargo-expand for Macro Debugging

```bash
# See what #[tauri::command] expands to
cargo expand --lib -- update_user

# See serde derives
cargo expand --lib -- UserInput
```

## Debugging Async Issues

### Blocking the Async Runtime

```rust
// BAD: std::fs blocks the tokio runtime thread
#[tauri::command]
async fn bad_read(path: String) -> Result<String, String> {
    std::fs::read_to_string(&path).map_err(|e| e.to_string())
    // This blocks the entire tokio worker thread!
}

// GOOD: Use tokio::fs for async I/O
#[tauri::command]
async fn good_read(path: String) -> Result<String, String> {
    tokio::fs::read_to_string(&path).await.map_err(|e| e.to_string())
}

// GOOD: Use spawn_blocking for CPU-heavy sync work
#[tauri::command]
async fn good_compute(data: Vec<u8>) -> Result<String, String> {
    tokio::task::spawn_blocking(move || {
        expensive_sync_computation(&data)
    })
    .await
    .map_err(|e| e.to_string())?
}
```

### Detecting Runtime Blocking in DevTools

In the **Calls tab**, a command that blocks the runtime shows:
- High duration (> 100ms) with NO child spans
- Other commands queued behind it (visible as delayed start times)
- Gap between parent span duration and sum of child spans

### Panic Handling

```rust
// Add a panic hook to capture panics in DevTools Console
tauri::Builder::default()
    .setup(|_app| {
        std::panic::set_hook(Box::new(|panic_info| {
            tracing::error!("PANIC: {}", panic_info);
            if let Some(location) = panic_info.location() {
                tracing::error!(
                    "  at {}:{}:{}",
                    location.file(),
                    location.line(),
                    location.column()
                );
            }
        }));
        Ok(())
    })
```

## External Debugging Tools

| Tool | Use Case | Command |
|---|---|---|
| lldb | Breakpoints, stepping, inspection | `rust-lldb target/debug/your-app` |
| gdb | Low-level debugging | `rust-gdb target/debug/your-app` |
| VS Code + CodeLLDB | GUI debugging with breakpoints | Configure `launch.json` with `"type": "lldb"` |
| RustRover / CLion | IDE debugging | Built-in Rust debugger |
| cargo-expand | Inspect macro expansions | `cargo expand --lib -- your_function` |
| RUST_BACKTRACE | Full stack traces on panic | `RUST_BACKTRACE=1 cargo tauri dev` |
| tokio-console | Async task visualization | Add `console-subscriber` crate, connect to port 6669 |
| miri | Undefined behavior detection | `cargo miri test` (no FFI support) |

### VS Code Debug Configuration

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "type": "lldb",
            "request": "launch",
            "name": "Debug Tauri App",
            "cargo": {
                "args": ["build", "--manifest-path=src-tauri/Cargo.toml"]
            },
            "args": [],
            "env": {
                "RUST_LOG": "debug",
                "RUST_BACKTRACE": "1"
            }
        }
    ]
}
```
