# Architecture Deep Dive — CrabNebula DevTools Internals

## Overview

CrabNebula DevTools is built on Rust's `tracing` ecosystem. It installs a custom tracing subscriber that captures all spans and events emitted by your application, then streams that data over gRPC to the DevTools UI. Understanding this pipeline helps you know what data DevTools can and cannot capture, and how to add custom instrumentation.

## Data Flow Pipeline

```
Your Rust Code
    │
    ▼
tracing macros (info!, debug!, error!, #[instrument])
    │
    ▼
┌─────────────────────────────────────────┐
│  BridgeLayer                            │
│  - Intercepts all tracing events        │
│  - Bridges between tracing API and      │
│    DevTools internal representation     │
│  - Converts spans/events to internal    │
│    data structures                      │
│  - Zero-cost when no subscriber active  │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  Layer                                  │
│  - Processes and formats captured data  │
│  - Extracts structured fields from      │
│    span attributes                      │
│  - Records span lifecycle (new, enter,  │
│    exit, close) with precise timing     │
│  - Handles parent-child relationships   │
│  - Manages span metadata (target,       │
│    level, file, line)                   │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  Aggregator                             │
│  - Batches individual events for        │
│    efficient transmission               │
│  - Maintains in-memory buffer of        │
│    recent spans and events              │
│  - Handles backpressure when UI is      │
│    slow or disconnected                 │
│  - Manages subscriber state             │
│  - Collects resource/async-task info    │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  Server (gRPC)                          │
│  - Runs on a SEPARATE THREAD from       │
│    the main application                 │
│  - Dynamically allocates port in range  │
│    6000–9000                            │
│  - Streams data to connected DevTools   │
│    UI clients (web or desktop)          │
│  - Handles multiple simultaneous        │
│    connections                          │
│  - Prints connection URL to terminal    │
└─────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  DevTools UI (Web or Desktop)           │
│  - Receives gRPC stream                 │
│  - Renders Console, Calls, Config,      │
│    Sources tabs                         │
│  - Provides filtering, search,          │
│    and timeline visualization           │
└─────────────────────────────────────────┘
```

## Component Details

### BridgeLayer

The BridgeLayer is the entry point into the DevTools pipeline. It implements the `tracing_subscriber::Layer` trait, which means it receives callbacks for every tracing event in the application:

- `on_new_span()` — called when a new span is created (e.g., an IPC call begins)
- `on_event()` — called for every tracing event (e.g., `info!("something happened")`)
- `on_enter()` — called when execution enters a span
- `on_exit()` — called when execution leaves a span
- `on_close()` — called when a span is dropped (permanently finished)

The BridgeLayer converts tracing's internal representation into DevTools' own data structures. This conversion is designed to be as lightweight as possible to minimize overhead in your application.

### Layer

The Layer component processes the converted data:

- **Field extraction:** Pulls out structured key-value pairs from span attributes. For IPC calls, this includes command name, serialized arguments, and response data.
- **Timing:** Records precise timestamps for span enter/exit events. The duration displayed in the Calls tab is computed from these timestamps.
- **Hierarchy:** Tracks parent-child relationships between spans. When a command handler calls a database function that has its own `#[tracing::instrument]`, the Layer records that nesting relationship.
- **Metadata:** Captures the target (module path), level, source file, and line number for each event and span.

### Aggregator

The Aggregator batches data for efficient transmission:

- **Buffering:** Individual events are collected and sent in batches rather than one-at-a-time, reducing gRPC overhead.
- **Backpressure:** If the DevTools UI is slow to consume data (or disconnected), the Aggregator buffers events up to a limit. Events beyond the buffer capacity are dropped to prevent memory exhaustion.
- **State management:** Maintains the set of active spans, completed spans, and pending events. The Aggregator is the "source of truth" for what data exists.
- **Resource tracking:** Collects information about Tokio async tasks and system resources when available.

### Server (gRPC)

The gRPC server is the network interface:

- **Separate thread:** The server runs on its own OS thread, completely isolated from your application's async runtime. This is a deliberate design choice — the DevTools documentation states the server runs separately "so we don't interfere with the application we're trying to instrument."
- **Dynamic port:** On startup, the server scans ports 6000–9000 to find an available one. The chosen port is printed to the terminal as part of the connection URL.
- **Protocol:** Uses gRPC (Protocol Buffers over HTTP/2) for efficient binary streaming.
- **Connection handling:** Supports multiple simultaneous UI connections. You can have the web UI and desktop app connected at the same time.

## How Custom Tracing Layers Interact

DevTools owns the global tracing subscriber in debug builds. Do not add a second `set_global_default()` call just to mirror terminal output while DevTools is active:

```rust
use tracing_subscriber::prelude::*;

// DevTools registers its own subscriber internally.
// If the app already has custom logging, review that setup
// carefully instead of adding another global subscriber.
// For tauri-plugin-log, use attach_logger() as shown in
// references/devtools-integration-patterns.md.
```

DevTools manages its own subscriber registration. You do NOT need to manually compose it with `tracing_subscriber::registry()`. The `init()` / `Builder::init()` call handles subscriber setup internally; if you need special coexistence rules, use `references/devtools-integration-patterns.md`.

## Memory and Performance Characteristics

### Memory Usage
- **Span buffer:** The Aggregator maintains a bounded buffer of recent spans. Memory usage grows with the number of active and recently-completed spans.
- **Event buffer:** Events are batched and flushed periodically. A burst of log events will temporarily increase memory usage until the batch is sent.
- **Typical overhead:** For most applications, DevTools adds 5–20 MB of memory usage. Applications with extremely high tracing throughput (>10,000 events/second) may see higher usage.

### CPU Overhead
- **Event capture:** Each tracing event incurs a small overhead for field extraction and serialization. This is typically <1 microsecond per event.
- **gRPC streaming:** The server thread handles serialization and network I/O independently. It does not compete with your application for CPU time on the main thread.
- **Aggregation:** Batching is designed to minimize lock contention. The Aggregator uses concurrent data structures to avoid blocking your application threads.

### Network
- **Bandwidth:** The gRPC stream uses Protocol Buffers for compact binary encoding. Typical bandwidth usage is 10–100 KB/s for moderately active applications.
- **Latency:** Events typically appear in the DevTools UI within 50–200ms of being emitted, depending on batch size and network conditions.

## Why Separate Thread?

The gRPC server runs in a separate OS thread (not a Tokio task) for several critical reasons:

1. **No async runtime contention:** If the server ran on your app's Tokio runtime, DevTools network I/O could compete with your application's async tasks for executor time.
2. **No interference with instrumentation target:** The server must not affect the timing characteristics of the code it's observing. Running on a separate thread ensures that DevTools gRPC activity doesn't appear in your application's span timing data.
3. **Crash isolation:** If the gRPC server encounters an error, it doesn't bring down your application. The separate thread can be restarted independently.
4. **Predictable performance:** Your application's performance characteristics remain stable regardless of whether a DevTools UI is connected and consuming data.

## Debug-Only Compilation

The `#[cfg(debug_assertions)]` gate is critical:

```rust
#[cfg(debug_assertions)]  // Only compiles in debug mode
let devtools = tauri_plugin_devtools::init();
```

In release builds (`cargo build --release`), the Rust compiler completely removes:
- The tracing subscriber registration
- The BridgeLayer, Layer, Aggregator, and Server code
- All gRPC dependencies (tonic, prost, etc.)
- The port scanning and URL printing logic

This means release binaries have **zero** DevTools overhead — not even a no-op function call. The code simply doesn't exist in the compiled binary.

## Practical Implications for Agents

1. **DevTools captures EVERYTHING in the tracing subscriber** — you don't need to add logging to see what's happening. If a function uses `#[tracing::instrument]`, its execution will appear as a span.

2. **The gRPC port is dynamic** — don't hardcode a port number. Read it from the terminal output.

3. **Multiple UI connections are supported** — if the user has the web UI open and the desktop app running simultaneously, both will receive the same data stream.

4. **Buffer limits exist** — if the application emits events faster than the UI can consume them, some events may be dropped. This is rare in normal usage but can happen during stress testing.

5. **DevTools cannot capture `println!()`** — only events going through the `tracing` subscriber are captured. Standard `println!()` bypasses the subscriber entirely. Always use `tracing::info!()`, `tracing::debug!()`, etc.

---

## Why This Matters for Debugging

Understanding the architecture helps avoid common diagnostic errors:

1. **DevTools only captures tracing events** — `println!()` and raw `log::info!()` (without a bridge) are invisible to DevTools. Always use `tracing` macros.
2. **The subscriber must be registered first** — events emitted before `init()` are lost forever. This is why init ordering matters.
3. **Release builds strip everything** — if DevTools shows no data in a release build, this is by design (`#[cfg(debug_assertions)]`), not a bug.
4. **Separate thread means no async interference** — DevTools won't cause your app to slow down or deadlock, even under heavy tracing load.
5. **Memory is bounded** — the Aggregator buffers data. Very long-running sessions may lose oldest events. Restart the app for a fresh capture if needed.

> ⚠️ **Steering:** DevTools does NOT capture `println!()` output. If no evidence appears, verify that the code is emitting through `tracing` macros rather than stdout.
