# Performance Profiling & Optimization — Tauri DevTools

> ⚠️ **Steering:** Follow this order strictly: IDENTIFY the slow command (Calls tab) → MEASURE baseline duration → LOCATE bottleneck (child spans) → ADD instrumentation if needed → ANALYZE root cause → FIX → VERIFY. Agents in testing jumped from "identify" to "fix" without locating the bottleneck, resulting in optimizations to the wrong code path.

## Using the Calls Tab for Performance Analysis

The Calls tab is the primary performance analysis tool. Every IPC call shows wall-clock duration with nested span hierarchy.

### Reading the Waterfall

```
Command: generate_report
Duration: 2,340ms
Status: OK

Timeline:
+-- generate_report [2340ms] OK
|  +-- fetch_data [45ms] OK
|  +-- render_pages [2100ms] OK     ◄── BOTTLENECK
|  |  +-- render_page [40ms] OK  (×50 pages)
|  +-- write_file [195ms] OK
```

**Analysis algorithm:**
1. Find the slowest top-level span → overall bottleneck
2. Look at children → which child takes the most time?
3. Recurse into slowest child → find the leaf operation
4. The leaf is your optimization target

### Duration Classification

| Duration | Class | Typical Cause | Action |
|---|---|---|---|
| < 1ms | Instant | In-memory operations | None needed |
| 1-10ms | Fast | Simple DB queries, small file reads | Normal |
| 10-100ms | Moderate | Complex queries, image processing | Acceptable for user actions |
| 100-500ms | Slow | Network calls, large file I/O | Show progress indicator |
| 500ms-2s | Very slow | Batch operations, external APIs | Must show progress |
| > 2s | Critical | Blocking main thread | Immediate investigation |

### Gap Analysis

If a parent span takes 500ms but children total only 200ms, the 300ms gap is:
- Time in the parent function itself (between child calls)
- Uninstrumented code (add `#[tracing::instrument]`)
- Serialization/deserialization overhead
- Mutex/lock contention or task scheduling
- Tokio runtime scheduling delays

## Adding Performance Instrumentation

### Strategic Span Placement

```rust
#[tauri::command]
#[tracing::instrument(skip(state))]
async fn process_order(
    order_id: u64,
    state: tauri::State<'_, AppState>,
) -> Result<OrderResult, String> {
    // Phase 1: Validate
    let _span = tracing::info_span!("validate_order", order_id).entered();
    let order = validate(order_id).await?;
    drop(_span);

    // Phase 2: Process payment
    let _span = tracing::info_span!("process_payment", amount = order.total).entered();
    let payment = charge(order.total).await?;
    drop(_span);

    // Phase 3: Update database
    let _span = tracing::info_span!("update_db", tables = 3).entered();
    save_order(&order, &payment).await?;
    drop(_span);

    Ok(OrderResult { order, payment })
}
```

In DevTools Calls tab, this produces:
```
+-- process_order [450ms]
|  +-- validate_order [12ms]
|  +-- process_payment [380ms]    ◄── Payment API is the bottleneck
|  +-- update_db [55ms]
```

### Async Span Instrumentation

```rust
use tracing::Instrument;

async fn download_files(urls: Vec<String>) -> Vec<Result<Vec<u8>, Error>> {
    let span = tracing::info_span!("download_batch", count = urls.len());

    async {
        let mut results = Vec::new();
        for url in &urls {
            let file_span = tracing::info_span!("download_file", url = %url);
            let result = async {
                reqwest::get(url).await?.bytes().await.map(|b| b.to_vec())
            }
            .instrument(file_span)
            .await;
            results.push(result);
        }
        results
    }
    .instrument(span)
    .await
}
```

## Common Performance Anti-Patterns

### 1. Sequential I/O (Should Be Parallel)

> ⚠️ **Steering:** Sequential I/O is the most common anti-pattern (40% of performance issues in testing). Look for: `for item in items { process(item).await; }` — this processes items one at a time. Fix with `futures::future::join_all()` for async or `rayon::par_iter()` for CPU-bound work.

```
Calls tab shows:
+-- sync_data [1250ms]
|  +-- download_file [20ms] (×40 files, sequential)
```

**Fix:** Use concurrent downloads:
```rust
use futures::stream::{FuturesUnordered, StreamExt};

#[tracing::instrument(skip(urls))]
async fn download_all(urls: Vec<String>) -> Vec<Result<Bytes, Error>> {
    let mut futures: FuturesUnordered<_> = urls.iter()
        .map(|url| {
            let url = url.clone();
            async move { reqwest::get(&url).await?.bytes().await }
        })
        .collect();

    let mut results = Vec::new();
    while let Some(result) = futures.next().await {
        results.push(result);
    }
    results
}
```

### 2. Blocking the Async Runtime

> ⚠️ **Steering:** ANY synchronous call >1ms inside an async handler blocks the ENTIRE Tokio runtime. This affects ALL concurrent commands, not just the blocking one. Use `tokio::task::spawn_blocking()` to move sync work off the runtime thread.

```
Calls tab shows:
+-- save_file [3200ms]    ◄── No child spans, single blocking operation
```

**Fix:** Use `spawn_blocking` for sync I/O:
```rust
#[tauri::command]
async fn save_file(path: String, data: Vec<u8>) -> Result<(), String> {
    tokio::task::spawn_blocking(move || {
        std::fs::write(&path, &data)
    })
    .await
    .map_err(|e| e.to_string())?
    .map_err(|e| e.to_string())
}
```

### 3. Redundant IPC Calls

> ⚠️ **Steering:** Sort the Calls tab by timestamp to spot burst patterns — the same command called 50+ times in 1 second from an unthrottled frontend handler. This is a FRONTEND fix (debounce/throttle), but DevTools provides the evidence.

```
Calls tab shows:
+-- get_user_settings [5ms] (called 15 times in 1 second)
```

**Fix:** Cache on the frontend:
```typescript
// BAD: Call on every render
const settings = await invoke('get_user_settings');

// GOOD: Cache with a store or state management
let cachedSettings: Settings | null = null;
async function getSettings(): Promise<Settings> {
    if (!cachedSettings) {
        cachedSettings = await invoke('get_user_settings');
    }
    return cachedSettings;
}
```

### 4. Unthrottled Event Handlers

```
Calls tab shows:
+-- save_draft [8ms] (called 50 times in 1 second from keystroke handler)
```

**Fix:** Debounce the frontend handler:
```typescript
import { debounce } from 'lodash-es';

const saveDraft = debounce(async (content: string) => {
    await invoke('save_draft', { content });
}, 500);

inputElement.addEventListener('input', (e) => saveDraft(e.target.value));
```

### 5. Missing Timeouts on External Calls

```
Calls tab shows:
+-- fetch_api_data [30000ms+] (still running)
```

**Fix:** Add timeouts:
```rust
#[tauri::command]
#[tracing::instrument]
async fn fetch_api_data(url: String) -> Result<String, String> {
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(10))
        .build()
        .map_err(|e| e.to_string())?;

    client.get(&url)
        .send()
        .await
        .map_err(|e| format!("Request failed: {}", e))?
        .text()
        .await
        .map_err(|e| e.to_string())
}
```

## DevTools Overhead

CrabNebula DevTools is designed for minimal impact:

| Metric | Typical Value |
|---|---|
| Memory overhead | 5-20 MB |
| CPU per event | < 1 microsecond |
| Network bandwidth | 10-100 KB/s |
| Event latency to UI | 50-200ms |
| Startup overhead | < 100ms |
| Release build impact | Zero (code stripped) |

The gRPC server runs on a **separate OS thread** — not a Tokio task. It cannot compete with your app's async runtime for CPU time.

### When DevTools Itself Causes Issues

> ⚠️ **Steering:** DevTools overhead is <1% for typical workloads. If you observe significant slowdown with DevTools enabled, the cause is almost certainly excessive tracing — too many spans at TRACE level in hot loops. Fix with targeted `RUST_LOG` filters, not by removing DevTools.

Rare, but possible with extreme throughput (> 10,000 events/second):
- The Aggregator buffer may drop events to prevent memory exhaustion
- Set `RUST_LOG` to reduce event volume
- Or add filter directives to suppress noisy crates

## Beyond DevTools: External Profiling Tools

DevTools does not provide CPU profiling, memory snapshots, or flamegraphs. For those needs:

| Tool | Use Case | Command |
|---|---|---|
| `cargo flamegraph` | CPU flamegraph | `cargo flamegraph --bin your-app` |
| `tokio-console` | Async task profiling | Add `console-subscriber` crate |
| `perf` (Linux) | System profiling | `perf record ./target/debug/your-app` |
| `Instruments` (macOS) | CPU/Memory profiling | Xcode → Product → Profile |
| `heaptrack` | Heap allocation tracking | `heaptrack ./target/debug/your-app` |
| `valgrind` | Memory leak detection | `valgrind ./target/debug/your-app` |
| `DHAT` | Heap profiling | `cargo run --features dhat-heap` |

### Using tokio-console Alongside DevTools

```toml
# Cargo.toml
[dependencies]
console-subscriber = "0.4"
tokio = { version = "1", features = ["full", "tracing"] }
```

```rust
// In setup — tokio-console and DevTools can coexist
#[cfg(debug_assertions)]
{
    // DevTools for IPC/logs/config
    let devtools = tauri_plugin_devtools::init();
    builder = builder.plugin(devtools);

    // tokio-console for async task inspection (separate tool, port 6669)
    // Note: May conflict with DevTools subscriber — test compatibility
}
```

## Performance Debugging Workflow

1. **Identify** — User reports slowness or you notice lag
2. **Measure** — Open Calls tab, sort by Duration (descending)
3. **Locate** — Find the slow command, expand its span hierarchy
4. **Analyze** — Use gap analysis and leaf identification
5. **Instrument** — Add `#[tracing::instrument]` to uninstrumented functions
6. **Fix** — Apply the appropriate optimization (parallel, async, cache, batch)
7. **Verify** — Check Calls tab again to confirm improvement
8. **Monitor** — Leave instrumentation in place for ongoing visibility
