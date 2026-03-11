# Plugin Debugging & Capabilities — Tauri DevTools

## Tauri v2 Capability System

Tauri v2 uses an ACL (Access Control List) system. Every plugin command requires explicit permission grants through capability files.

### File Structure

```
src-tauri/
├── capabilities/
│   ├── default.json          # Default capability (auto-enabled)
│   ├── desktop.json          # Desktop-specific permissions
│   └── mobile.json           # Mobile-specific permissions
├── tauri.conf.json           # References capabilities
└── src/
    └── lib.rs                # Plugin registration
```

### Capability File Format

```json
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "main-capability",
  "description": "Capability for the main window",
  "windows": ["main"],
  "permissions": [
    "core:default",
    "core:window:allow-set-title",
    "fs:allow-read-text-file",
    "fs:allow-write-text-file",
    "dialog:default",
    "shell:allow-open",
    "http:default",
    "store:default"
  ]
}
```

### Platform-Specific Capabilities

```json
{
  "$schema": "../gen/schemas/mobile-schema.json",
  "identifier": "mobile-capability",
  "windows": ["main"],
  "platforms": ["iOS", "android"],
  "permissions": [
    "core:default",
    "nfc:allow-scan",
    "barcode-scanner:allow-scan"
  ]
}
```

### Remote Capabilities (for web content)

```json
{
  "$schema": "../gen/schemas/remote-schema.json",
  "identifier": "remote-api",
  "windows": ["main"],
  "remote": {
    "urls": ["https://*.myapp.com"]
  },
  "permissions": [
    "core:event:allow-listen"
  ]
}
```

## Debugging Permission Errors

### Using DevTools to Diagnose

1. Open the **Console tab** — filter by ERROR level
2. Look for messages containing "permission", "denied", or "not allowed"
3. Open the **Config tab** — navigate to the Security section
4. Verify the capabilities list includes required permission identifiers
5. Cross-reference error messages with capability files

### Common Permission Error Patterns

| Error Pattern | Cause | Fix |
|---|---|---|
| `Unhandled Promise Rejection: command_name not found` | Command not in capability permissions | Add `"plugin:allow-command-name"` to capability |
| `plugin fs not allowed` | Missing fs permissions | Add `"fs:allow-read-text-file"` or relevant fs permission |
| `Not allowed to invoke command` | Capability doesn't cover the window | Check `"windows"` field includes the calling window label |
| `Permission denied: path outside scope` | Path not in allowed scope | Add scope to the permission: `"fs:scope": ["$APPDATA/**"]` |
| Command works in dev but not in build | Debug-only capability config | Ensure capabilities are not gated by debug assertions |
| `Plugin X not initialized` | Plugin crate added but not registered | Add `.plugin(tauri_plugin_x::init())` in `lib.rs` |

### Scoped Permissions (File System)

```json
{
  "identifier": "fs-capability",
  "windows": ["main"],
  "permissions": [
    {
      "identifier": "fs:allow-read-text-file",
      "allow": [{ "path": "$APPDATA/**" }]
    },
    {
      "identifier": "fs:allow-write-text-file",
      "allow": [{ "path": "$APPDATA/**" }]
    }
  ]
}
```

**Scope variables:**
| Variable | Path |
|---|---|
| `$APPDATA` | App-specific data directory |
| `$APPCONFIG` | App configuration directory |
| `$APPLOCALDATA` | App local data directory |
| `$APPLOG` | App log directory |
| `$RESOURCE` | Bundle resources directory |
| `$TEMP` | System temp directory |
| `$DESKTOP` | User desktop |
| `$DOCUMENT` | User documents |
| `$DOWNLOAD` | User downloads |
| `$HOME` | User home directory |

## Debugging Plugin Initialization

### Step-by-Step Diagnosis

1. **Check Console tab at app startup** — Look at earliest timestamps for ERROR/WARN
2. **Check Config tab Plugins section** — Verify the plugin appears
3. **Check `lib.rs`** — Ensure `.plugin(tauri_plugin_xxx::init())` is called
4. **Check Cargo.toml** — Ensure the plugin crate is in dependencies
5. **Check capability files** — Ensure plugin permissions are granted

### Common Plugin Init Failures

| Symptom | Diagnosis via DevTools | Fix |
|---|---|---|
| Plugin commands return errors | Console shows init error at startup | Check plugin config in `tauri.conf.json` |
| No tracing from plugin | Plugin not in Config tab | Register with `.plugin()` in `lib.rs` |
| "State not managed" error | Plugin setup didn't complete | Check setup order — some plugins need `setup()` hook |
| Plugin works on desktop, not mobile | Console shows platform error | Check if plugin supports mobile targets |
| Conflicting plugins | Console shows panic at init | Check for duplicate plugin names or resource conflicts |

### Plugin Registration Order

Register DevTools **first**, then other plugins:

```rust
let mut builder = tauri::Builder::default();

// 1. DevTools FIRST — captures all subsequent plugin init events
#[cfg(debug_assertions)]
{
    let devtools = tauri_plugin_devtools::init();
    builder = builder.plugin(devtools);
}

// 2. Other plugins — their init tracing is captured by DevTools
builder = builder
    .plugin(tauri_plugin_opener::init())
    .plugin(tauri_plugin_store::Builder::new().build())
    .plugin(tauri_plugin_fs::init())
    .plugin(tauri_plugin_http::init());
```

If DevTools is registered after other plugins, tracing events from those plugins' initialization will be lost.

## Common Plugin Permission Identifiers

| Plugin | Key Permissions |
|---|---|
| `fs` | `fs:default`, `fs:allow-read-text-file`, `fs:allow-write-text-file`, `fs:allow-exists`, `fs:allow-mkdir` |
| `dialog` | `dialog:default`, `dialog:allow-open`, `dialog:allow-save`, `dialog:allow-message` |
| `http` | `http:default`, `http:allow-fetch` |
| `shell` / `opener` | `shell:allow-open`, `opener:default` |
| `store` | `store:default`, `store:allow-get`, `store:allow-set` |
| `notification` | `notification:default`, `notification:allow-notify` |
| `clipboard` | `clipboard-manager:default`, `clipboard-manager:allow-read`, `clipboard-manager:allow-write` |
| `global-shortcut` | `global-shortcut:default`, `global-shortcut:allow-register` |
| `window` | `core:window:default`, `core:window:allow-set-title`, `core:window:allow-close` |

## Config Tab Deep Dive

The Config tab shows the **resolved** configuration — the merged result of:
1. `tauri.conf.json` (base)
2. Platform-specific overrides (`tauri.macos.conf.json`, etc.)
3. `TAURI_CONFIG` environment variable overrides
4. Plugin configurations from code

### What to Check in Config Tab

| Section | Key Fields | Common Issues |
|---|---|---|
| **App** | `withGlobalTauri`, `windows[]` | Wrong window dimensions, missing window labels |
| **Build** | `devUrl`, `distDir` | Wrong dev server URL, incorrect dist path |
| **Security** | `csp`, `capabilities` | Missing permissions, wrong CSP blocking resources |
| **Plugins** | (varies) | Plugin not registered, wrong plugin config |
| **Bundle** | `identifier`, `resources` | Missing bundled resources, wrong app ID |

### Verifying Capabilities via Config Tab

1. Open Config tab → Security section
2. Look at the `capabilities` list
3. Each entry should reference a capability file in `src-tauri/capabilities/`
4. Verify the permissions include all plugin commands your app uses
5. Check `windows` field matches your window labels

## Debugging "Works in Dev, Fails in Build"

Common causes when capabilities work in `cargo tauri dev` but fail in `cargo tauri build`:

1. **TAURI_CONFIG override in dev** — Check if `TAURI_CONFIG` env var adds permissions
2. **Different capability files** — Dev might use `default.json` while build uses platform-specific
3. **Schema mismatch** — `$schema` path is wrong after build
4. **Missing resources** — Files in dev server not included in bundle
5. **Debug-only code paths** — Logic behind `#[cfg(debug_assertions)]` won't run in release

Use the Config tab to compare resolved configuration between dev and build modes.
