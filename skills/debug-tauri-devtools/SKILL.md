---
name: debug-tauri-devtools
description: Use skill if you are debugging a Tauri app's Rust side, IPC calls, config, plugins, or bundled assets with CrabNebula DevTools.
---

# Debug Tauri DevTools

CrabNebula DevTools is a Rust-side observability tool for Tauri v2 applications. It surfaces everything behind the webview — Rust backend logs, IPC call payloads and timing, resolved app configuration, and bundled asset inspection. Browser DevTools cannot see any of this because Tauri's IPC layer operates outside the browser's network stack.

| Capability | Browser DevTools | CrabNebula DevTools |
|---|---|---|
| DOM/CSS/JS debugging | yes | no |
| HTTP/WebSocket inspection | yes | no |
| Rust backend logs | no | yes |
| IPC call inspection (invoke) | no | yes |
| IPC latency/timing spans | no | yes |
| Tauri config viewer | no | yes |
| Capability/permission verification | no | yes |
| Asset resolution inspection | no | yes |

## Decision tree

```
What are you debugging?
│
├── Setup & installation
│   ├── Installing the plugin ──────────────► references/setup/installation-and-config.md
│   ├── Builder API / config options ───────► references/setup/installation-and-config.md
│   ├── Platform-specific setup ────────────► references/setup/installation-and-config.md
│   ├── Connecting to the UI ───────────────► references/setup/installation-and-config.md
│   └── tauri-plugin-log compatibility ─────► references/rust/logging-and-tracing.md
│
├── IPC calls (invoke)
│   ├── Slow command investigation ─────────► references/devtools-ipc-span-anatomy.md
│   ├── Failed / error IPC calls ──────────► references/devtools-common-debugging-scenarios.md
│   ├── Argument serialization mismatch ───► references/devtools-common-debugging-scenarios.md
│   ├── Command never returns (hangs) ─────► references/devtools-common-debugging-scenarios.md
│   └── Redundant / excessive calls ───────► references/performance/profiling-and-optimization.md
│
├── Rust backend issues
│   ├── Adding tracing instrumentation ────► references/rust/backend-debugging.md
│   ├── State management debugging ────────► references/rust/backend-debugging.md
│   ├── Serialization errors (serde) ──────► references/rust/backend-debugging.md
│   ├── Async / deadlock issues ───────────► references/rust/backend-debugging.md
│   ├── External tools (lldb, gdb, VS Code) ► references/rust/backend-debugging.md
│   └── Panic handling ────────────────────► references/rust/backend-debugging.md
│
├── Logging & tracing
│   ├── RUST_LOG configuration ────────────► references/rust/logging-and-tracing.md
│   ├── Custom tracing spans ──────────────► references/rust/logging-and-tracing.md
│   ├── Log crate vs tracing crate ────────► references/rust/logging-and-tracing.md
│   └── Noisy dependency filtering ────────► references/rust/logging-and-tracing.md
│
├── Plugins & permissions
│   ├── Capability/ACL file setup ─────────► references/plugins/capabilities-and-permissions.md
│   ├── Permission error diagnosis ────────► references/plugins/capabilities-and-permissions.md
│   ├── Plugin initialization failures ───► references/plugins/capabilities-and-permissions.md
│   ├── Plugin registration order ─────────► references/plugins/capabilities-and-permissions.md
│   └── Scoped permissions (fs, http) ────► references/plugins/capabilities-and-permissions.md
│
├── Mobile debugging
│   ├── Android (adb, logcat, port fwd) ──► references/mobile/android-ios-debugging.md
│   ├── iOS (Xcode, Safari Inspector) ────► references/mobile/android-ios-debugging.md
│   ├── Platform-specific issues ──────────► references/mobile/android-ios-debugging.md
│   └── Mobile performance ────────────────► references/mobile/android-ios-debugging.md
│
├── Performance
│   ├── Span waterfall analysis ───────────► references/performance/profiling-and-optimization.md
│   ├── Common anti-patterns ──────────────► references/performance/profiling-and-optimization.md
│   ├── DevTools overhead ─────────────────► references/performance/profiling-and-optimization.md
│   └── External profilers ────────────────► references/performance/profiling-and-optimization.md
│
├── DevTools UI tabs
│   ├── Console tab (logs/events) ─────────► references/devtools-tab-reference.md
│   ├── Calls tab (IPC spans) ────────────► references/devtools-tab-reference.md
│   ├── Config tab (resolved config) ─────► references/devtools-tab-reference.md
│   └── Sources tab (bundled assets) ─────► references/devtools-tab-reference.md
│
└── Architecture & internals
    ├── Data flow pipeline ────────────────► references/devtools-architecture-deep-dive.md
    ├── gRPC server / threading model ────► references/devtools-architecture-deep-dive.md
    └── Integration patterns ─────────────► references/devtools-integration-patterns.md
```

## When NOT to use this skill

- **DOM/CSS layout issues** → Browser DevTools Elements panel
- **JavaScript errors** → Browser DevTools Console
- **HTTP/fetch failures** → Browser DevTools Network tab
- **React/Vue/Svelte debugging** → Framework browser extensions
- **Frontend performance** → Browser DevTools Performance tab

Only activate when the problem involves: Rust backend, IPC calls, Tauri config, plugins, tracing, or asset bundling.

## Quick start

```toml
# src-tauri/Cargo.toml
[dependencies]
tauri-plugin-devtools = "2"
```

```rust
// src-tauri/src/lib.rs
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

Run `cargo tauri dev`. Terminal prints a DevTools URL → open https://devtools.crabnebula.dev → paste the URL → four tabs appear: Console, Calls, Config, Sources.

## Key workflows

### "My Tauri command is slow"
Open **Calls tab** → filter by command name → check Duration column. If > 100ms, expand to see child spans. The deepest slow span is your bottleneck. See `references/devtools-ipc-span-anatomy.md`.

### "I see a Rust error but can't find it"
Open **Console tab** → filter by ERROR level. Target column shows source location (e.g., `my_app::commands::file_ops` → `src/commands/file_ops.rs`). See `references/devtools-common-debugging-scenarios.md`.

### "My plugin command returns a permission error"
Open **Config tab** → Security section → verify capabilities list. Then **Console tab** → filter ERROR for the exact permission error. Fix: add missing permission to `src-tauri/capabilities/*.json`. See `references/plugins/capabilities-and-permissions.md`.

### "My bundled asset isn't loading"
Open **Sources tab** → browse file tree. If file missing, it wasn't bundled — check `tauri.conf.json` resources. If present but wrong path, compare with frontend request path. See `references/devtools-common-debugging-scenarios.md`.

### "It works on desktop but not on mobile"
Connect to mobile DevTools (Android: `adb forward tcp:PORT tcp:PORT`; iOS: URL from Xcode console). Compare Console errors and Calls tab behavior with desktop. See `references/mobile/android-ios-debugging.md`.

### "IPC call returns wrong data"
Open **Calls tab** → find the invocation → examine Arguments column (what JS sent) and Response column (what Rust returned). Mismatch indicates serde issue. See `references/rust/backend-debugging.md`.

## Common pitfalls

| Pitfall | Fix |
|---------|-----|
| Using `println!()` instead of `tracing::info!()` | `println!` bypasses DevTools. Use `tracing` macros — they appear in Console tab automatically. |
| Missing `#[cfg(debug_assertions)]` on DevTools | Ships debug tooling + gRPC server to users. Always gate with `#[cfg(debug_assertions)]`. |
| `log::info!()` events not appearing | Use `Builder::default().attach_logger(logger)` with the `tauri-plugin-log` split pattern. |
| DevTools registered after other plugins | Register DevTools **first** — events from other plugins' init are lost otherwise. |
| Browser Network tab for IPC calls | Tauri IPC doesn't use HTTP. Only the DevTools Calls tab shows IPC traffic. |
| Adding timing code to measure IPC | Calls tab already provides precise span timing — no code changes needed. |
| Guessing capability permissions | Check Config tab Security section and Console tab ERROR filter. Error messages specify the missing permission. |
| Hardcoded file paths on mobile | Use `app.path().app_data_dir()` — no `/home/` on Android, strict sandbox on iOS. |
| No timeouts on external HTTP calls | Calls tab shows stuck spans. Add `reqwest::Client::builder().timeout()`. |
| `"probe"` plugin conflict error | Multiple DevTools instances registered. Only one `init()` call allowed. |
| Android DevTools won't connect | Port forwarding needed: `adb forward tcp:PORT tcp:PORT`. |
| Release build has no DevTools | Expected behavior — `#[cfg(debug_assertions)]` correctly strips it. |

## Minimal reading sets

### "My IPC command is failing or slow"
- `references/devtools-ipc-span-anatomy.md`
- `references/devtools-common-debugging-scenarios.md`
- `references/performance/profiling-and-optimization.md`

### "I need to set up DevTools from scratch"
- `references/setup/installation-and-config.md`
- `references/devtools-tab-reference.md`

### "I have a Rust backend bug"
- `references/rust/backend-debugging.md`
- `references/rust/logging-and-tracing.md`
- `references/devtools-common-debugging-scenarios.md`

### "My plugin or permissions are broken"
- `references/plugins/capabilities-and-permissions.md`
- `references/devtools-common-debugging-scenarios.md`

### "I'm debugging on mobile"
- `references/mobile/android-ios-debugging.md`
- `references/setup/installation-and-config.md`

### "I need to understand DevTools internals"
- `references/devtools-architecture-deep-dive.md`
- `references/devtools-integration-patterns.md`

### "I need performance profiling"
- `references/performance/profiling-and-optimization.md`
- `references/devtools-ipc-span-anatomy.md`

## Reference files

| File | Contents |
|---|---|
| references/setup/installation-and-config.md | Installation, Cargo.toml, init patterns, Builder API, platform setup, connection |
| references/rust/backend-debugging.md | Command handler debugging, state management, serde errors, async issues, external tools |
| references/rust/logging-and-tracing.md | RUST_LOG, tracing macros, custom spans, tauri-plugin-log integration |
| references/plugins/capabilities-and-permissions.md | Capability ACL files, permission errors, plugin init failures, scoped permissions |
| references/mobile/android-ios-debugging.md | Android adb/logcat, iOS Xcode, platform-specific issues, mobile performance |
| references/performance/profiling-and-optimization.md | Span waterfall analysis, anti-patterns, DevTools overhead, external profilers |
| references/devtools-tab-reference.md | Console/Calls/Config/Sources tab columns, filtering, keyboard shortcuts |
| references/devtools-ipc-span-anatomy.md | IPC span structure, timing interpretation, custom spans, missing span diagnosis |
| references/devtools-architecture-deep-dive.md | Internal pipeline: BridgeLayer → Layer → Aggregator → gRPC Server |
| references/devtools-common-debugging-scenarios.md | 14 concrete debugging scenarios with symptoms, tabs, and fixes |
| references/devtools-integration-patterns.md | tauri-plugin-log integration, custom subscribers, cfg patterns, RUST_LOG |

## Final reminder

This skill is split into small, focused reference files. Do not load everything at once. Start with the smallest relevant reading set above, then expand only when the task requires it. Every reference file is routed from the decision tree.
