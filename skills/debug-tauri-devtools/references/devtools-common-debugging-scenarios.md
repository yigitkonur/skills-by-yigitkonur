# Common Debugging Scenarios — CrabNebula DevTools

## How to Use This Reference

Each scenario follows the same structure:
1. **User symptom** — what the user reports or what you observe
2. **Which tab** — where to look first in DevTools
3. **What to look for** — exact columns, filters, or patterns
4. **Root cause pattern** — the typical underlying issue
5. **Agent action** — the concrete fix to apply

---

## Scenario 1: Slow IPC Command

**User symptom:** "My `save_document` command takes 3 seconds and the UI freezes."

**Which tab:** Calls

**What to look for:** Filter by command name `save_document`. Check the Duration column. Expand the span to see nested child spans. Identify which child span consumes the most time.

**Root cause pattern:** The command handler performs blocking I/O on the main thread. Common culprits: synchronous file writes, unindexed database queries, large serialization payloads, or network requests without timeouts.

**Agent action:** Identify the slow child span. If it's file I/O, switch to async `tokio::fs`. If it's a database query, add indexes or reduce result set size. If no child spans exist, add `#[tracing::instrument]` to internal functions to get more granular timing data.

---

## Scenario 2: Silent IPC Error

**User symptom:** "I click the button but nothing happens. No error in the browser console."

**Which tab:** Calls, then Console

**What to look for:** In the Calls tab, find the invoke call triggered by the button. Check the Status column — if it shows ✗, expand to see the error. Then switch to Console and filter by ERROR level around the same timestamp.

**Root cause pattern:** The frontend `.invoke()` call doesn't have a `.catch()` handler, so the error is silently swallowed. The Rust handler returned an `Err()` that never reaches the user.

**Agent action:** First, read the error from the Calls tab Response column to understand what failed. Then fix the Rust handler if the error is a bug. Also add error handling in the frontend: `invoke('cmd').catch(e => console.error(e))`.

---

## Scenario 3: Missing Configuration / Wrong Capability

**User symptom:** "My plugin command returns a permission error" or "The command fails with 'not allowed'."

**Which tab:** Config, then Console

**What to look for:** In Config tab, navigate to the Security section. Look for the capabilities list. Verify the required permission identifier is present (e.g., `"fs:allow-read-text-file"`, `"dialog:default"`). In Console, filter by ERROR to find the exact permission error message.

**Root cause pattern:** The `tauri.conf.json` or capability files don't include the permission required by the plugin command being invoked. Tauri v2 requires explicit capability grants for all plugin operations. Note: distinguish between Tauri ACL errors ("not allowed", "capability") and OS-level errors ("os error 13", "Permission denied" from `std::io`) — these are different root causes requiring different fixes.

**Agent action:** Add the missing permission to the appropriate capability file in `src-tauri/capabilities/`. The error message in Console often specifies the needed permission. If it doesn't name the specific permission, use the Common Plugin Permission Identifiers table in `references/plugins/capabilities-and-permissions.md` to find the correct identifier for the failing operation.

---

## Scenario 4: Asset Not Loading

**User symptom:** "My image/font/JSON file shows as broken or 404 in the app."

**Which tab:** Sources, then Config

**What to look for:** In Sources tab, browse the file tree to find the expected asset. If it's missing, the file wasn't included in the bundle. If it's present, note the exact path. In Config tab, check the Bundle section for resource inclusion patterns.

**Root cause pattern:** The asset path in the frontend code doesn't match the actual path in the bundle. Common issues: wrong relative path, case sensitivity (Linux vs macOS), file not listed in `tauri.conf.json` resources, or the asset is outside the dist directory.

**Agent action:** Compare the path used in frontend code with the actual path shown in Sources tab. Fix the path reference. If the file is missing from Sources entirely, add it to the `resources` array in `tauri.conf.json` or ensure it's in the dist directory.

---

## Scenario 5: Plugin Not Initializing

**User symptom:** "I added the plugin but its commands don't work" or "Plugin features are not available."

**Which tab:** Console, then Config

**What to look for:** In Console tab, look for ERROR or WARN events from the plugin's crate name at startup timestamps (earliest events). In Config tab, verify the plugin appears in the Plugins section.

**Root cause pattern:** Either (a) the plugin was added to `Cargo.toml` but not registered with `.plugin()` in `lib.rs`, (b) the plugin requires a capability that isn't configured, or (c) the plugin initialization failed with an error that was silently consumed.

**Agent action:** Check `lib.rs` for `.plugin(tauri_plugin_xxx::init())` registration. Check `tauri.conf.json` for required capabilities. Read the Console error to determine the specific initialization failure.

---

## Scenario 6: Excessive Log Noise

**User symptom:** "My terminal/console is flooded with log messages and I can't find important ones."

**Which tab:** Console

**What to look for:** Look at the Target column to identify which crate/module is producing the most output. Use the level filter to hide TRACE and DEBUG levels. Filter by specific crate names to isolate the noisy source.

**Root cause pattern:** A dependency crate (often `hyper`, `tonic`, `sqlx`, or `tokio`) has verbose TRACE/DEBUG logging enabled. Or the application's own code uses `tracing::debug!()` in a hot loop.

**Agent action:** Set the `RUST_LOG` environment variable to suppress noisy crates: `RUST_LOG=warn,my_app=debug,noisy_crate=warn`. Or add a tracing filter directive in code. See `references/integration-patterns.md` for `RUST_LOG` configuration details.

---

## Scenario 7: IPC Argument Serialization Mismatch

**User symptom:** "The command receives wrong data" or "The command works with some inputs but fails with others."

**Which tab:** Calls

**What to look for:** Find the failing invoke in the Calls tab. Examine the Arguments column carefully. Compare the JSON structure with what the Rust command handler expects (`#[tauri::command]` parameter types). Look for: missing fields, wrong types (string vs number), null values, or unexpected nesting.

**Root cause pattern:** The TypeScript/JavaScript object structure doesn't match the Rust `serde::Deserialize` struct. Common: camelCase in JS vs snake_case in Rust (Tauri handles this, but custom serde attributes can break it), optional fields not marked as `Option<T>`, or enum variants not matching.

**Agent action:** Compare the Arguments JSON in Calls tab with the Rust struct definition. Fix the frontend call to match the expected structure, or update the Rust struct with appropriate `#[serde(rename)]` or `#[serde(default)]` attributes.

---

## Scenario 8: Command Never Returns (Hangs)

**User symptom:** "The app freezes when I click this button" or "The loading spinner never goes away."

**Which tab:** Calls

**What to look for:** Find the invoke call in the Calls tab. If the Duration column shows an ever-increasing value (or no value), the command handler is blocked and never returning. Check for nested child spans — the deepest incomplete span shows where execution is stuck.

**Root cause pattern:** The command handler is blocked on: (a) a synchronous operation that deadlocks, (b) an async operation that never resolves (missing `.await`, channel with no sender), (c) an infinite loop, or (d) waiting for a mutex held by another task.

**Agent action:** Identify the blocking operation from the span hierarchy. If no child spans exist, add `#[tracing::instrument]` to internal functions to narrow down the stuck point. Common fixes: add timeouts to network calls, use `tokio::task::spawn_blocking` for sync operations, check for deadlock patterns.

---

## Scenario 9: Different Behavior on Android/iOS

**User symptom:** "It works on desktop but not on mobile" or "The command fails only on Android."

**Which tab:** Console, then Calls

**What to look for:** Connect to the mobile DevTools (Android: `adb forward tcp:PORT tcp:PORT`; iOS: use URL from Xcode console). In Console tab, filter by ERROR. In Calls tab, compare the span behavior with what you see on desktop.

**Root cause pattern:** Platform-specific issues: (a) file paths differ (no `/home/` on Android), (b) permissions model differs (Android requires runtime permissions for certain APIs), (c) the `cfg(mobile)` entry point has different initialization, (d) certain Rust crates don't support mobile targets.

**Agent action:** Read the error from Console to determine the platform-specific failure. Common fixes: use Tauri's `app.path()` API for platform-correct paths instead of hardcoded paths, check mobile-specific permission requirements, verify the plugin supports mobile targets.

---

## Scenario 10: Dev vs Production Build Differences

**User symptom:** "Everything works in `cargo tauri dev` but breaks in `cargo tauri build`."

**Which tab:** Config, Sources

**What to look for:** In Config tab, compare the resolved configuration. Dev mode uses the dev server URL; production uses bundled files. In Sources tab, verify all expected assets are present in the bundle. Check that no code paths depend on `#[cfg(debug_assertions)]` for production-critical logic.

**Root cause pattern:** Code behind `#[cfg(debug_assertions)]` doesn't run in release builds. DevTools itself is gated this way, which is correct — but application logic should NOT be behind this gate. Other common issues: dev server serves files differently than the bundled asset protocol, environment variables differ, and CSP settings may be stricter in production.

**Agent action:** Search the codebase for `#[cfg(debug_assertions)]` — ensure only DevTools setup (and genuine debug-only logic) is gated. Move any production-critical code outside the gate. Verify `tauri.conf.json` bundle settings include all necessary files.

---

## Scenario 11: Missing Spans for Custom Functions

**User symptom:** "I only see the top-level command span but not what happens inside it."

**Which tab:** Calls

**What to look for:** The command span appears but has no child spans, even though the handler calls multiple internal functions. The Duration column shows a slow total time but you can't see what's slow inside.

**Root cause pattern:** Internal functions don't have `#[tracing::instrument]` attributes, so DevTools only sees the top-level IPC span and nothing inside it.

**Agent action:** Add `#[tracing::instrument]` to key internal functions:
```rust
#[tracing::instrument(skip(db_pool))]
async fn fetch_user_data(db_pool: &Pool, user_id: i64) -> Result<User, Error> {
    // This will now appear as a child span in DevTools
    // ...
}
```
Focus on functions that perform I/O, database queries, or heavy computation. Don't instrument trivial getter functions.

---

## Scenario 12: Log Events from Dependencies Missing

**User symptom:** "I can't see logs from my database library in DevTools Console."

**Which tab:** Console

**What to look for:** Filter by the dependency's crate name (e.g., `sqlx`, `reqwest`, `diesel`). If no events appear, the dependency's logs aren't reaching the DevTools tracing subscriber.

**Root cause pattern:** The dependency uses the `log` crate instead of `tracing`. Without a bridge, `log` events don't reach the `tracing` subscriber. Or, the dependency does use `tracing` but the `RUST_LOG` filter level is set too high to capture its events.

**Agent action:** If using `tauri-plugin-log`, use the `attach_logger()` pattern to bridge `log` events to DevTools. Check `RUST_LOG` includes the dependency: `RUST_LOG=debug,sqlx=debug`. If the dependency uses `tracing` natively, its events should appear automatically — verify the filter level allows them through.

---

## Scenario 13: Permission Errors on File System Operations

**User symptom:** "Reading/writing files fails with a permission error."

**Which tab:** Console, then Config

**What to look for:** In Console, filter by ERROR. Look for messages containing "permission", "denied", or "not allowed". In Config, check Security section for `fs` scope permissions and asset protocol scope.

**Root cause pattern:** Tauri v2 requires explicit filesystem scope permissions. The command needs `"fs:allow-read-text-file"`, `"fs:allow-write-text-file"`, or `"fs:default"` capabilities, AND the paths must fall within the allowed scope (typically `$APPDATA`, `$RESOURCE`, etc.).

**Agent action:** Add the required `fs` permissions to the capability file. Ensure the path scope includes the directories the app needs to access. Use `app.path().app_data_dir()` for app-specific storage instead of arbitrary system paths.

---

## Scenario 14: Multiple Rapid IPC Calls Causing Performance Issues

**User symptom:** "The app is slow and laggy. It feels like it's doing too much."

**Which tab:** Calls

**What to look for:** Sort the Calls tab by timestamp. Look for bursts of the same command being called many times in rapid succession (e.g., `save_draft` called 50 times in 1 second from a keystroke handler). Check for commands that are called redundantly (same arguments, same result).

**Root cause pattern:** The frontend is calling `invoke()` too frequently — typically from an unthrottled event handler (keypress, scroll, resize) or a React `useEffect` with missing/wrong dependency array causing re-renders.

**Agent action:** This is a frontend issue, but DevTools identifies it. Add debouncing/throttling to the frontend event handler. Consider batching multiple operations into a single IPC call. The Calls tab provides the evidence; browser DevTools provides the frontend fix.
