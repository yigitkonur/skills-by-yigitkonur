---
name: debug-tauri-devtools
description: Use skill if you are debugging a live Tauri app with CrabNebula DevTools to inspect Rust logs, IPC calls, runtime config, plugin permissions, or bundled assets.
---

# Debug Tauri DevTools

Use CrabNebula DevTools for the part of a Tauri app that browser DevTools cannot
see: Rust-side logs, IPC spans, resolved runtime config, capability state,
plugin wiring, and bundled asset resolution.

## Trigger

Activate when the user reports or the agent observes any of these:

- a Tauri `invoke()` call fails, hangs, is unexpectedly slow, or returns wrong data
- a Rust panic/error exists but the failing module or span is unclear
- a plugin, capability, or window-scope permission appears broken
- an asset loads in dev but not in build, or exists locally but not in the bundle
- behavior differs across desktop/mobile or debug/build modes
- you are about to add `println!()`, guess at serde/config issues, or inspect the browser Network tab for Tauri IPC

## When NOT to use this skill

Do not activate for:

- DOM, CSS, layout, browser-only JavaScript, or framework component debugging
- HTTP/fetch/WebSocket debugging that lives in the browser network stack
- static code review without a live runtime symptom
- cases where the problem is already proven and you only need to implement a fix

Use browser DevTools for webview problems. Use CrabNebula DevTools when the
unknown lives behind the webview.

## Rust-side visibility map

| If the symptom is... | Open first | Capture this evidence | Read next |
|---|---|---|---|
| Rust panic, missing log source, noisy tracing, or startup failure | **Console** | level, target module, message, fields, startup timestamp | `references/rust/logging-and-tracing.md`, `references/rust/backend-debugging.md`, `references/devtools-tab-reference.md` |
| `invoke()` error, wrong response, serialization mismatch, hang, or slow command | **Calls** | command name, Arguments, Response, Status, Duration, child spans | `references/devtools-ipc-span-anatomy.md`, `references/devtools-common-debugging-scenarios.md`, `references/rust/backend-debugging.md` |
| Permission error, plugin not initialized, wrong window scope, or config mismatch | **Config**, then **Console** | Security capabilities, Plugins section, startup errors, resolved overrides | `references/plugins/capabilities-and-permissions.md`, `references/devtools-tab-reference.md` |
| Asset missing, wrong runtime path, or dev/build difference | **Sources**, then **Config** | whether the file exists in the bundle, exact runtime path, bundle/resources/CSP settings | `references/devtools-common-debugging-scenarios.md`, `references/devtools-tab-reference.md`, `references/setup/installation-and-config.md` |
| Desktop works but mobile breaks | **Console** + **Calls** on device | platform-specific errors, path differences, permission/init differences | `references/mobile/android-ios-debugging.md`, `references/setup/installation-and-config.md` |

## Workflow

Follow this order. Do not skip from symptom straight to code edits.

### Phase 1 — Establish the failing path

- Name the exact action that reproduces the issue.
- Note expected vs actual behavior.
- Record environment: `cargo tauri dev`, debug build, release build, desktop platform, or mobile target.
- If DevTools is not installed, not connected, or blank, stop and route to `references/setup/installation-and-config.md` before diagnosing the app.

### Phase 2 — Observe before theorizing

- Start in the single tab that matches the symptom.
- Capture exact evidence before browsing other surfaces:
  - **Console**: target path, error text, fields, panic location
  - **Calls**: command, args, response/error, timing, nesting
  - **Config**: capabilities, plugin registration, build/bundle/security values
  - **Sources**: bundled file presence, exact path, case-sensitive mismatches
- Prefer built-in DevTools filters and sorting before changing code or `RUST_LOG`.

### Phase 3 — Form 1-3 falsifiable hypotheses

Each hypothesis must identify:

1. the suspected failure mode
2. the exact evidence that would confirm it
3. the next inspection surface or reference

Good hypothesis shapes:

- "JS arguments do not match the Rust `Deserialize` struct."
- "The command is blocked on uninstrumented file I/O or lock contention."
- "The plugin is registered, but the capability or window scope is missing."
- "The asset exists in source control but is absent from the bundle."
- "Mobile uses a platform-specific path or permission assumption that desktop does not."

### Phase 4 — Inspect the hypothesis path

Use the narrowest inspection path that can confirm or reject the hypothesis:

- **Rust handler / serde / async / state issue** → `Calls` + `references/rust/backend-debugging.md`
- **Need deeper span detail** → `references/devtools-ipc-span-anatomy.md`
- **Permission / capability / plugin init issue** → `Config` + `Console` + `references/plugins/capabilities-and-permissions.md`
- **Log visibility or missing dependency logs** → `references/rust/logging-and-tracing.md`
- **Subscriber / `tauri-plugin-log` / custom integration question** → `references/devtools-integration-patterns.md`
- **Asset / bundle / build-mode mismatch** → `Sources` + `Config` + `references/devtools-common-debugging-scenarios.md`
- **Mobile-only divergence** → `references/mobile/android-ios-debugging.md`
- **Need tool internals or pipeline limits** → `references/devtools-architecture-deep-dive.md`

If evidence is still incomplete, add visibility instead of guessing:

- add targeted `tracing::info!`, `warn!`, or `error!` events
- add `#[tracing::instrument]` to the internal Rust functions that hide the slow or failing leaf
- enable `RUST_BACKTRACE=1` for panics
- use the `split()/attach_logger()` pattern when `log::`-based dependency output is missing
- compare the same repro in dev vs build, or desktop vs mobile, before changing code

### Phase 5 — Separate diagnosis from repair

Only edit app code/config after one hypothesis is confirmed by evidence.

When you do change something:

- fix the narrow failing path, not nearby speculative code
- keep temporary tracing in place until the verification pass
- avoid cleanup refactors until the bug is proven fixed

### Phase 6 — Verify in the same surface

Re-run the same repro and confirm the evidence changed where it originally failed:

- **Calls**: status, response, duration, or child span structure is now correct
- **Console**: error/panic is gone or replaced by the expected trace sequence
- **Config**: missing capability/plugin/config value is now present in resolved config
- **Sources**: missing asset/path mismatch is resolved at runtime
- **Mobile/build comparisons**: previously divergent evidence now matches the expected platform behavior

Remove temporary instrumentation only after the verification pass.

## Decision rules

- If one child span dominates the total duration, optimize that child first.
- If the parent span is slow but child spans are missing or too small, instrument internal Rust code before refactoring.
- If the Calls response already shows a permission error, inspect resolved capabilities and window scope before touching the command handler.
- If no IPC call appears at all, check whether the frontend actually invoked the command, whether the command name is wrong, whether a capability blocked it, or whether DevTools was initialized too late.
- If Console is noisy, use UI filters first; only narrow `RUST_LOG` when throughput is too high to reason about.
- If release builds have no DevTools data, treat that as expected `#[cfg(debug_assertions)]` behavior and reproduce with a debug-capable target before drawing conclusions.
- If desktop and mobile differ, compare Console and Calls evidence on both platforms before sharing a fix.

## Guardrails

- Do not use Browser Network tools as proof for Tauri IPC behavior.
- Do not change serde structs, capability files, plugin order, or asset paths without first reading the runtime evidence that points there.
- Do not use `println!()` as your primary Rust debugging surface; use `tracing` so the data stays in DevTools.
- Do not instrument every function. Add spans only where evidence is missing.
- Do not convert a diagnosis task into a broad refactor.
- Do not claim a root cause until you can point to a concrete log, span, config value, permission, or asset path.

## Do this, not that

| Do this | Not that |
|---|---|
| Read **Calls** Arguments/Response before touching Rust command types | Guess at serde mismatches from source alone |
| Check **Config** Security and Plugins sections before editing capability files | Blindly patch `src-tauri/capabilities/*.json` |
| Use `tracing` macros and targeted `#[tracing::instrument]` | Scatter `println!()` or instrument everything |
| Use **Sources** as runtime truth for bundled files | Assume the dev server path matches the build bundle |
| Compare desktop vs mobile or dev vs build evidence in the same tab | Port a desktop fix to mobile/build without proof |
| Keep diagnosis and repair as separate steps | Make speculative code edits while the cause is still ambiguous |

## Recovery paths

- **DevTools will not connect or shows no data** → `references/setup/installation-and-config.md`
- **`tauri-plugin-log` conflicts or dependency logs are missing** → `references/rust/logging-and-tracing.md`, `references/devtools-integration-patterns.md`
- **The command is slow or hung but the waterfall is too shallow** → `references/devtools-ipc-span-anatomy.md`, `references/rust/backend-debugging.md`
- **Known symptom, unclear next move** → `references/devtools-common-debugging-scenarios.md`
- **Need field-by-field help with tabs, filters, or exports** → `references/devtools-tab-reference.md`
- **Need performance or overhead guidance beyond one command** → `references/performance/profiling-and-optimization.md`
- **Need to understand pipeline limitations or internal behavior** → `references/devtools-architecture-deep-dive.md`

## Minimal reading sets

### "DevTools setup or connectivity is the problem"

- `references/setup/installation-and-config.md`
- `references/rust/logging-and-tracing.md`
- `references/devtools-integration-patterns.md`

### "An IPC command fails, hangs, returns wrong data, or is slow"

- `references/devtools-ipc-span-anatomy.md`
- `references/devtools-common-debugging-scenarios.md`
- `references/rust/backend-debugging.md`
- `references/performance/profiling-and-optimization.md`

### "I need better Rust-side visibility"

- `references/rust/logging-and-tracing.md`
- `references/rust/backend-debugging.md`
- `references/devtools-tab-reference.md`

### "A plugin, capability, or resolved config looks wrong"

- `references/plugins/capabilities-and-permissions.md`
- `references/devtools-tab-reference.md`
- `references/devtools-common-debugging-scenarios.md`

### "It works in dev/desktop but breaks in build/mobile or assets are missing"

- `references/devtools-common-debugging-scenarios.md`
- `references/mobile/android-ios-debugging.md`
- `references/setup/installation-and-config.md`
- `references/devtools-tab-reference.md`

### "I need subscriber, performance, or internal pipeline details"

- `references/devtools-integration-patterns.md`
- `references/performance/profiling-and-optimization.md`
- `references/devtools-architecture-deep-dive.md`

## Reference routing

| File | Load when |
|---|---|
| `references/setup/installation-and-config.md` | DevTools is not installed, not connecting, registered too late, or you need debug-only/build-mode setup rules. |
| `references/rust/logging-and-tracing.md` | Console evidence is missing/noisy, you need `tracing` guidance, `RUST_LOG` strategy, or `tauri-plugin-log` bridging. |
| `references/rust/backend-debugging.md` | The problem lives in command handlers, state, serde, async blocking, deadlocks, panics, or external Rust debugging tools. |
| `references/devtools-ipc-span-anatomy.md` | You need to interpret waterfall timing, nesting, gap analysis, missing spans, or targeted span instrumentation. |
| `references/devtools-common-debugging-scenarios.md` | The symptom matches a known pattern and you want the fastest route from observation to likely root cause. |
| `references/devtools-tab-reference.md` | You need tab columns, filters, sorting, export behavior, or precise UI field meanings. |
| `references/plugins/capabilities-and-permissions.md` | Permissions, capabilities, plugin initialization, window scope, or dev/build config resolution is suspect. |
| `references/mobile/android-ios-debugging.md` | The bug is mobile-only or you need Android/iOS connection, logging, or platform-specific debugging steps. |
| `references/performance/profiling-and-optimization.md` | Calls show slow spans, redundant invokes, profiling questions, or you need to reason about overhead and optimization tradeoffs. |
| `references/devtools-integration-patterns.md` | You need subscriber wiring, `tauri-plugin-log` coexistence, cfg patterns, or advanced integration guidance. |
| `references/devtools-architecture-deep-dive.md` | You need internal pipeline, gRPC server, threading, or architecture-level constraints to explain missing/odd behavior. |

## Final reminder

Use CrabNebula DevTools to collect runtime truth, not to justify a hunch. Stay
in observation-first mode until you can name the failing command, log target,
config value, permission, or asset path and point to the exact evidence.
