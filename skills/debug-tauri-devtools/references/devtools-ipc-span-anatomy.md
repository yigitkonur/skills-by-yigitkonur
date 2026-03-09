# IPC Span Anatomy — CrabNebula DevTools

## What Is an IPC Span?

When a frontend JavaScript call like invoke('my_command', { key: 'value' }) reaches the Tauri backend, the DevTools plugin wraps the entire execution in a tracing span. This span captures the full lifecycle of the IPC call — from the moment the Rust handler begins executing to when it returns a response (or error) to the frontend.

## Span Fields

| Field | Type | Description |
|---|---|---|
| name | String | The Tauri command name (e.g., "my_command") |
| arguments | JSON | Serialized input parameters from the frontend |
| response | JSON | Serialized return value (on success) or error (on failure) |
| start_time | Timestamp | When the command handler began executing |
| end_time | Timestamp | When the command handler returned |
| duration | Duration | end_time - start_time (wall-clock time) |
| status | Enum | OK or ERROR |
| parent_span | Option | Reference to parent span if this was a nested call |
| child_spans | List | Any sub-operations that created their own spans |
| target | String | The Rust module path of the command handler |
| level | Level | The tracing level (usually INFO for IPC spans) |

## Span Data as JSON (Internal Representation)

The following shows the conceptual JSON structure of span data as it flows through the DevTools pipeline. This is not a literal API response — it represents the data available in the Calls tab.

```json
{
  "span_id": "a1b2c3d4",
  "name": "get_user_profile",
  "target": "my_app::commands::users",
  "level": "INFO",
  "fields": {
    "command": "get_user_profile",
    "arguments": {
      "user_id": 42
    }
  },
  "timing": {
    "started_at": "2024-01-15T10:30:00.123Z",
    "ended_at": "2024-01-15T10:30:00.126Z",
    "duration_ms": 3.2
  },
  "status": "OK",
  "response": {
    "name": "Alice",
    "email": "alice@example.com"
  },
  "parent_span_id": null,
  "child_spans": [
    {
      "span_id": "e5f6g7h8",
      "name": "db_query",
      "target": "my_app::db",
      "timing": {
        "duration_ms": 2.1
      },
      "status": "OK"
    }
  ]
}
```

## Example: Normal Span

```
Command: get_user_profile
Arguments: { "user_id": 42 }
Duration: 3ms
Status: OK
Response: { "name": "Alice", "email": "alice@example.com" }

Timeline:
+-- get_user_profile [3ms] OK
|  +-- db_query [2ms] OK
```

**Interpretation:** Fast command with a single database sub-operation. The 1ms overhead (3ms total - 2ms db) is serialization + Tauri IPC overhead. This is healthy.

## Example: Slow Span with Bottleneck

```
Command: export_report
Arguments: { "format": "pdf", "pages": 50 }
Duration: 2,340ms
Status: OK
Response: { "path": "/tmp/report.pdf", "size": 1048576 }

Timeline:
+-- export_report [2340ms] OK
|  +-- fetch_data [45ms] OK
|  +-- render_pages [2100ms] OK     <-- BOTTLENECK
|  |  +-- render_page [40ms] OK  (x50 pages)
|  +-- write_file [195ms] OK
```

**Interpretation:** The render_pages sub-span takes 2100ms of the 2340ms total — this is the bottleneck. The agent should investigate the rendering logic, not the data fetching or file writing.

**Agent action:** Look at render_page — 40ms x 50 pages = 2000ms. Consider: Can pages be rendered in parallel? Can output be streamed? Is there unnecessary recomputation per page?

## Example: Error Span

```
Command: save_settings
Arguments: { "theme": "dark", "language": "fr" }
Duration: 12ms
Status: ERROR
Error: "PermissionDenied: Cannot write to /etc/app/settings.json"

Timeline:
+-- save_settings [12ms] ERROR
|  +-- write_file [10ms] ERROR
```

**Interpretation:** The command failed at the file write step. The error message clearly indicates a permission issue — the app is trying to write to a system directory instead of the user's app data directory.

**Agent action:** Change the file path to use app.path().app_data_dir() instead of a hardcoded system path.

## Example: Command with Multiple Sequential Operations

```
Command: sync_data
Arguments: { "source": "cloud", "force": false }
Duration: 1,250ms
Status: OK
Response: { "synced": 42, "skipped": 8, "errors": 0 }

Timeline:
+-- sync_data [1250ms] OK
|  +-- fetch_remote_manifest [200ms] OK
|  +-- compare_local_state [15ms] OK
|  +-- download_changed_files [800ms] OK
|  |  +-- download_file [20ms] OK  (x40 files)
|  +-- update_local_db [235ms] OK
```

**Interpretation:** Four sequential phases. download_changed_files dominates at 800ms (64% of total). The 40 individual downloads average 20ms each, totaling 800ms sequentially. Parallel downloads would reduce this significantly.

**Agent action:** Use tokio::join! or futures::stream::FuturesUnordered to download files concurrently instead of sequentially. Cap concurrency at ~10 to avoid overwhelming the server.

## Example: Nested Command Calling Another Command

```
Command: process_batch
Arguments: { "items": [1, 2, 3, 4, 5] }
Duration: 450ms
Status: OK

Timeline:
+-- process_batch [450ms] OK
|  +-- process_item [85ms] OK   (item=1)
|  +-- process_item [90ms] OK   (item=2)
|  +-- process_item [88ms] OK   (item=3)
|  +-- process_item [92ms] OK   (item=4)
|  +-- process_item [87ms] OK   (item=5)
```

**Interpretation:** Five items processed sequentially, ~90ms each. Total time grows linearly with item count. With 100 items this would take ~9 seconds.

**Agent action:** Parallelize item processing, or if items are independent, batch them into a single database operation instead of N individual operations.

## Example: Timeout / Never-Returning Span

```
Command: fetch_external_api
Arguments: { "endpoint": "https://api.example.com/data" }
Duration: (still running... 30s+)
Status: (pending)

Timeline:
+-- fetch_external_api [30000ms+] (running)
|  +-- http_request [30000ms+] (running)
```

**Interpretation:** The command is stuck waiting for an external HTTP request. No timeout was set on the request, so it will hang until the server responds or the TCP connection times out (which can be minutes).

**Agent action:** Add a timeout to the HTTP request: `reqwest::Client::new().get(url).timeout(Duration::from_secs(10))`. Also add error handling for timeout errors.

## Reading Span Duration Context

| Duration | Classification | Typical Cause | Agent Response |
|---|---|---|---|
| < 1ms | Instant | In-memory operations, simple calculations | No action needed |
| 1-10ms | Fast | Simple DB queries, small file reads, serialization | Normal for most commands |
| 10-100ms | Moderate | Complex queries, file operations, image processing | Acceptable for user-initiated actions |
| 100-500ms | Slow | Network calls, large file I/O, heavy computation | User will notice; consider async/background |
| 500ms-2s | Very slow | Report generation, batch operations, external APIs | Must show progress indicator to user |
| > 2s | Critical | Blocking the main thread, unresponsive UI | Immediate investigation required |

## Nested Spans — Waterfall Reading Strategy

Nested spans show the call hierarchy within a command handler. Read the waterfall using this algorithm:

1. **Find the slowest top-level span** — this is the overall bottleneck
2. **Look at its children** — which child takes the most time?
3. **Recurse** — drill into the slowest child until you find the leaf operation
4. **The leaf operation is your optimization target** — it's the actual work being done

**Gap analysis:** If a parent span takes 500ms but its children only total 200ms, there's a 300ms gap. This gap represents:
- Time spent in the parent function itself (between child calls)
- Uninstrumented code (add #[tracing::instrument] to see it)
- Serialization/deserialization overhead
- Mutex/lock contention or task scheduling delays

If a span has many children of similar duration, the bottleneck is the NUMBER of operations, not any single one — consider batching or parallelizing.

## Custom Spans via #[tracing::instrument]

### Basic Instrumentation

Add #[tracing::instrument] to make a function appear as a span:

```rust
#[tracing::instrument]
async fn fetch_user(user_id: i64) -> Result<User, Error> {
    // This creates a span named "fetch_user" with field user_id=<value>
    db.query_one("SELECT * FROM users WHERE id = $1", &[&user_id]).await
}
```

When this function is called from a Tauri command handler, it appears as a child span in the Calls tab waterfall.

### Controlling What Fields Are Recorded

**Skip large or sensitive arguments:**
```rust
#[tracing::instrument(skip(db_pool, password))]
async fn authenticate(db_pool: &Pool, username: &str, password: &str) -> Result<Token, Error> {
    // db_pool and password are NOT recorded in the span
    // username IS recorded
}
```

**Skip all arguments:**
```rust
#[tracing::instrument(skip_all)]
async fn process_large_payload(data: &[u8]) -> Result<(), Error> {
    // No arguments recorded — useful for large binary data
}
```

**Add custom fields:**
```rust
#[tracing::instrument(fields(table = "users", operation = "upsert"))]
async fn save_user(user: &User) -> Result<(), Error> {
    // Span fields: table="users", operation="upsert", user=<debug format>
}
```

**Custom span name:**
```rust
#[tracing::instrument(name = "database_query")]
async fn internal_db_fn(sql: &str) -> Result<Vec<Row>, Error> {
    // Appears as "database_query" in DevTools, not "internal_db_fn"
}
```

### Manual Span Creation

For finer control, create spans manually without the attribute macro:

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

Each manual span appears as a separate entry in the Calls tab waterfall with its own timing.

### Synchronous Span Entry

For synchronous code blocks:

```rust
fn process_data(data: &[Record]) -> ProcessedData {
    let _span = tracing::info_span!("validate_records", count = data.len()).entered();
    validate(data);
    drop(_span);

    let _span = tracing::info_span!("transform_records").entered();
    let transformed = transform(data);
    drop(_span);

    transformed
}
```

The _span variable holds the span guard. When dropped (explicitly or at scope end), the span is closed and its duration is recorded.

## Missing Spans — Diagnosis

If you expect to see a span but it doesn't appear:

| Possible Cause | Diagnosis | Fix |
|---|---|---|
| Function lacks #[tracing::instrument] | Check the function definition | Add the attribute |
| Subscriber initialized too late | Check plugin registration order | Register DevTools before other plugins |
| Function panicked before span completed | Check Console tab for panics | Fix the panic; the span will close on panic but may show as error |
| Wrong tracing level | RUST_LOG filter too restrictive | Use RUST_LOG=trace or remove RUST_LOG to capture all levels |
| Function is in a dependency crate | Dependencies don't auto-instrument | Add tracing in your wrapper function instead |
| Async function not .awaited | Span created but never entered | Ensure the future is .awaited |

## Span Overhead

Adding #[tracing::instrument] has minimal overhead:
- Span creation: ~100-500 nanoseconds
- Field recording: depends on field count and type (strings are fastest)
- When DevTools is not active (release builds): zero overhead — the attribute compiles to a no-op due to #[cfg(debug_assertions)] on the subscriber

Do NOT instrument every function. Focus on:
- Command handlers (automatic via DevTools)
- Database queries
- File I/O operations
- Network requests
- Any function taking > 1ms
- Functions you're actively debugging
