# CrabNebula DevTools — Tab Reference

## Console Tab

### What It Shows
All Rust tracing events captured by the DevTools subscriber. This includes:
- tracing::trace!(), debug!(), info!(), warn!(), error!() macro outputs
- log:: macro outputs (if piped through devtools via attach_logger)
- Span enter/exit events with timing
- Custom span events from #[tracing::instrument] annotated functions

### Columns

| Column | Data Type | Description | Example |
|---|---|---|---|
| Timestamp | Relative time | When the event was emitted, relative to app start, millisecond precision | 00:00:03.142 |
| Level | Enum badge | TRACE, DEBUG, INFO, WARN, or ERROR — color-coded for quick scanning | ERROR (red badge) |
| Target | Module path | The full Rust module path where the event originated | my_app::commands::file_ops |
| Message | String | The formatted log message content | "File saved successfully to /tmp/data.json" |
| Fields | Key-value pairs | Structured data from tracing span/event fields | user_id=42, path="/tmp/data.json" |

### Level Badge Colors
- **TRACE** — grey/dim (most verbose, usually hidden by default)
- **DEBUG** — blue (development diagnostics)
- **INFO** — green (normal operational messages)
- **WARN** — yellow/orange (potential issues that don't stop execution)
- **ERROR** — red (failures and exceptions)

### Filtering

**By level:** Click on the level badges at the top of the Console tab to toggle visibility for each level. Multiple levels can be active simultaneously. Common patterns:
- Show ERROR only: click to disable all others
- Show WARN + ERROR: disable TRACE, DEBUG, INFO
- Show all: enable all level badges

**By target/crate:** Type a crate name or module path in the filter text box. This performs a prefix match:
- `my_app` — shows events from my_app and all its submodules
- `my_app::commands` — shows only events from the commands module and below
- `sqlx` — shows all events from the sqlx database crate
- `tauri` — shows events from the Tauri core framework

**By text:** Free-text search across message content. Searches the Message column only (not Fields). The search is case-insensitive.

**Combining filters:** Level filters AND target/text filters are combined. For example: ERROR level + target "my_app" shows only errors from your application code, excluding errors from dependencies.

> ⚠️ **Steering:** The Console tab shows ALL tracing events, not just errors. Use level filters (ERROR, WARN) to reduce noise before analyzing.

### Jump-to-Source
Click on a target path to copy the full module path to clipboard. This path corresponds to the Rust source file structure. For example, `my_app::commands::file_ops` maps to `src/commands/file_ops.rs`.

In the Premium desktop app, clicking a target path can open the source file directly in your configured editor.

### Export
Console events can be selected and copied as text. The web UI supports Ctrl/Cmd+A to select all visible (filtered) events, then Ctrl/Cmd+C to copy.

---

## Calls Tab

### What It Shows
Every Tauri IPC invoke() call between the frontend JavaScript and the Rust backend. Each call is represented as a tracing span with full lifecycle data, including timing, arguments, responses, and nested sub-operations.

### Columns

| Column | Data Type | Description | Example |
|---|---|---|---|
| Command | String | The Tauri command name being invoked | get_user_profile |
| Arguments | JSON | Serialized arguments passed from JS to Rust | { "user_id": 42 } |
| Response | JSON/Error | The return value (on success) or error message (on failure) | { "name": "Alice" } |
| Duration | Milliseconds | Wall-clock time from invoke start to response complete | 3.2ms |
| Status | Icon | Success (checkmark) or Error (cross) indicator | checkmark |
| Nesting | Indentation | Visual indentation showing parent-child span relationships | 2 levels deep |

### Filtering
- **By command name:** Type in the filter box to show only specific commands. Useful when debugging a particular command handler.
- **By duration:** Click the Duration column header to sort. Ascending shows fastest first; descending shows slowest first — use descending to find performance bottlenecks.
- **By status:** Filter to show only errors or only successes. Errors-only is useful when debugging a specific failure.

### Interpreting Timing

| Duration | Classification | Typical Cause | Agent Response |
|---|---|---|---|
| < 1ms | Instant | In-memory operations, simple calculations | No action needed |
| 1-10ms | Fast | Simple DB queries, small file reads, serialization | Normal for most commands |
| 10-100ms | Moderate | Complex queries, file operations, image processing | Acceptable for user-initiated actions |
| 100-500ms | Slow | Network calls, large file I/O, heavy computation | User will notice; consider async/background |
| 500ms-2s | Very slow | Report generation, batch operations, external APIs | Must show progress indicator to user |
| > 2s | Critical | Blocking the main thread, unresponsive UI | Immediate investigation required |

### Span Nesting (Waterfall View)
A command handler that invokes other internal operations shows nested spans as indented children. Reading the waterfall:

1. Look at the top-level span — this is the overall command duration
2. Expand to see child spans — each represents an internal operation
3. Identify the widest child span — this is the bottleneck
4. Recurse into that child for deeper analysis

If a parent span takes 500ms but its children only account for 100ms, the remaining 400ms is spent in the parent function itself (not in the instrumented children). Either the parent has uninstrumented code, or the overhead is in serialization/IPC.

### Missing Calls
If you click a button but no call appears:
- The frontend event handler may not be calling invoke()
- The command name may be misspelled (check browser DevTools console for errors)
- The IPC call may be blocked by a missing capability permission

> ⚠️ **Steering:** Tauri IPC commands appear automatically in the Calls tab — no instrumentation needed. Only internal Rust functions need `#[tracing::instrument]`.

---

## Config Tab

### What It Shows
The resolved Tauri application configuration — the final merged result of:
1. tauri.conf.json (base configuration)
2. Platform-specific overrides (tauri.macos.conf.json, etc.)
3. Environment variable overrides (TAURI_CONFIG)
4. Plugin configurations from code

### Sections

| Section | Key Fields | What to Check |
|---|---|---|
| App | withGlobalTauri, windows[], macOSPrivateApi | Window definitions, dimensions, titles, URL |
| Build | devUrl, distDir, beforeDevCommand, beforeBuildCommand | Dev server URL, frontend build output path |
| Security | csp, capabilities, dangerousDisableAssetCspModification, freezePrototype | CSP directives, capability permissions, asset protocol scope |
| Plugins | (varies per plugin) | Plugin-specific settings, ensure plugins are registered |
| Bundle | identifier, icon[], targets, resources, fileAssociations | App ID, icons, installer targets, bundled resources |

### Security Section Deep Dive

The Security section is the most frequently consulted for debugging:

**Capabilities:** Lists all permission identifiers granted to the app. Each plugin command requires specific permissions. For example:
- fs:read, fs:write — filesystem operations
- dialog:open, dialog:save — dialog plugin
- http:default — HTTP client plugin
- shell:open — shell/opener plugin

**CSP (Content Security Policy):** Controls which resources the webview can load. If an asset loads in dev but not in production, check CSP directives here.

**Asset Protocol Scope:** Defines which filesystem paths the asset protocol can serve. If the app needs to load files from outside the bundle, the scope must include those paths.

### When to Use
- Verify capabilities/permissions are correctly configured
- Check that window properties (size, title, resizable) are as expected
- Confirm security settings (CSP, asset protocol scope)
- Verify plugin registration and configuration
- Debug differences between dev and production configurations
- Check bundle settings (app identifier must be unique for signing)

---

## Sources Tab

### What It Shows
The application's source files and bundled assets as resolved by the Tauri runtime. This includes:
- Frontend files (HTML, CSS, JS) as served by the asset protocol
- Static assets (images, fonts, data files) in the bundle
- Resource resolution paths showing how assets are located

### Features

**File tree browser:** Navigate the hierarchical file tree of bundled assets. Directories are expandable. Files show their size and type.

**File content viewer:** Click any file to view its contents directly in DevTools. Text files show source. Binary files (images, fonts) show metadata.

**Path verification:** Compare paths used in frontend code with actual paths in the bundle. The Sources tab shows the "truth" of what's actually bundled.

### Common Checks
- An asset file exists in your source but isn't in Sources? It wasn't included in the bundle. Check tauri.conf.json resources and the dist directory.
- The path in Sources differs from what the frontend requests? Update the frontend path to match.
- A file appears in Sources during dev but not after build? The build process may be excluding it. Check build configuration.
- Case sensitivity: macOS and Windows are case-insensitive, but Linux is case-sensitive. If a file loads on macOS but not Linux, check for case mismatches in file paths.

### When to Use
- An asset (image, font, JSON file) isn't loading in the app
- Need to verify the build output includes expected files
- Path resolution differs between `cargo tauri dev` and `cargo tauri build`
- CSP is blocking an asset and you need to verify its protocol/path
- Debugging file association issues with the bundle configuration

---

## Agent-Mode Alternatives

When operating as an AI agent without visual DevTools access, use these terminal-based alternatives:

| DevTools Tab | Terminal Alternative | How |
|---|---|---|
| Console | stderr output from `cargo tauri dev` | DevTools subscriber prints tracing events to stderr. Filter with `grep` or `RUST_LOG` |
| Calls | tracing span output in terminal | IPC commands appear as spans. Look for `tauri::ipc` target in output |
| Config | Direct file inspection | Read `src-tauri/tauri.conf.json` and `src-tauri/capabilities/*.json` directly |
| Sources | File system inspection | Check `src-tauri/` directory structure and `tauri.conf.json` bundle settings |

> ⚠️ **Steering:** Never claim to "open" or "see" a DevTools tab if you're an AI agent without visual access. Explicitly state when you are using terminal output or file inspection instead.
