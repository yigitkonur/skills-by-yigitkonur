# agent-device command map (iOS-focused)

Annotated surface of every subcommand, grouped by job. Version-matched truth is always `agent-device <command> --help` and `agent-device help workflow`; this map is for fast orientation. Captured against agent-device 0.19.x.

## Device & app lifecycle

| Command | Use for | Notes |
|---|---|---|
| `devices --platform ios` | List simulators/devices | Pass `--device "iPhone 17 Pro"` on other commands only when several are present |
| `boot` | Boot selected device | Usually implicit via `open` |
| `shutdown` | Shut simulator down | Rarely needed; `close --shutdown` combines |
| `apps [--all]` | Discover installed app ids | Use before `open` when bundle id unknown |
| `appstate` | Foreground app check | Cheap "what is on screen" sanity probe |
| `open <app> [url]` | Launch app / deep link | No `--relaunch` = idempotent foreground. `--relaunch` = restart (single simctl call on simulators). `--launch-console <path>` captures launch stdout/stderr (direct app launches only, not URL opens). Host+URL form for shells: `open "Expo Go" exp://…` |
| `close [app]` | End session | `--save-script` writes replayable .ad; `--shutdown` also kills the simulator. Healthy runner stays warm ~5 min for the next open |
| `install <app> <path>` / `reinstall` | Install binaries | `install` unless the task says reinstall; fresh state = `open --relaunch` after |
| `install-from-source` | Pull builds from URLs/CI artifacts | e.g. `--github-actions-artifact org/repo:app-name` |
| `prepare ios-runner` | Pre-build the XCTest runner | CI: after boot/install, before replay/test. Not a fix for "runner owned by another daemon" — stop the owning daemon instead |
| `session list` / `session state-dir` | Inspect active sessions | Implicit default session is scoped to the current worktree |
| `doctor [--app <id>]` | Setup/recovery diagnostics | On failure or explicit request only — not routine prep |
| `capabilities` | Command support matrix for target | Only for dynamic integrations |

## Reading the screen

| Command | Use for | Notes |
|---|---|---|
| `snapshot` | Read visible state | Token-efficient agent view; `--raw`/`--json` only for full tree or rects |
| `snapshot -i` | Interactive refs for the next action | The default pre-action read. Scope: `-s "Label"`; depth: `-d N` |
| `snapshot -s @e12` | Expand truncated text/input preview | Use this, **not** `get text`, for `truncated` previews |
| `diff snapshot [-i]` | What changed since last snapshot | The verification tool when you skipped `--settle`. First call just initializes the baseline |
| `find <text> <action>` | Find element and act in one step | `--first`/`--last` for ambiguity |
| `get text\|attrs <target>` | Read one element | Targeted query, cheaper than snapshot |
| `is <predicate> <selector>` | Assert UI state | e.g. `is visible 'label="Online"'` |
| `wait <ms>` / `wait text "…" [ms]` / `wait <selector> [ms]` / `wait stable [quietMs] [ms]` | Await async UI | Polls 300 ms; default timeout 10 s; timeout raises a failure. `wait stable` only for open/relaunch/nav or unsettled mutations |
| `screenshot [path]` | Visual evidence | `--overlay-refs` draws refs; `--pixel-density`; `--normalize-status-bar` for reusable baselines |
| `diff screenshot --baseline <png>` | Pixel regression | `--threshold 0-1` |

## Acting on the screen

| Command | Use for | Notes |
|---|---|---|
| `press <target>` | Tap | `tap` is alias. `--settle` on every use. `--count/--interval-ms/--jitter-px/--double-tap` for series |
| `click <target>` | Same as press; adds `--button secondary` | Secondary = macOS context menus, not iOS |
| `fill <target> <text>` | **Replace** field text | `--settle`; `--delay-ms` paces characters for debounced/search fields |
| `type <text>` | **Append** to focused field | Focus first via `press` on the field |
| `focus <x> <y>` | Focus input at coordinates | Coordinate fallback only |
| `longpress <target> [ms]` | Context menus / hold | Duration positional: `longpress @e12 800` |
| `scroll <dir\|top\|bottom> [amount]` | Lists | Use `scroll down` + `snapshot -i` loops for off-screen targets; `bottom/top` only when the task names the edge |
| `swipe <x1> <y1> <x2> <y2> [ms]` | Coordinate gestures/carousels | `--count/--pause-ms/--pattern ping-pong` |
| `gesture pan\|fling\|swipe\|pinch\|rotate\|transform …` | Deliberate drags, edge-swipes, multi-touch | `gesture pan x y dx dy ms` moves floating overlays; `gesture swipe right-edge` = back gesture. Simulator transform uses private XCTest synthesis — verify app metrics, not exact values |
| `back [--system]` | Navigate back | App-owned by default; prefer a visible back ref when routing is ambiguous |
| `home` / `app-switcher` | System navigation | |
| `rotate <orientation>` | Orientation testing | |
| `keyboard status\|dismiss\|enter` | Keyboard control | Dismiss only when hiding is the goal; keyboard rarely blocks presses |
| `alert get\|accept\|dismiss\|wait [ms]` | Platform dialogs | "No alert" + visible sheet = app-owned UI → `snapshot -i` + press by label |
| `clipboard read\|write <text>` | Clipboard | Prefill for paste flows; iOS Allow-Paste prompt is untestable under XCUITest |

## Evidence & diagnostics

| Command | Use for | Notes |
|---|---|---|
| `logs clear --restart` → `logs mark "…"` → `logs path` | Scoped log windows | One compound command, not stop/clear/start. Simulator logs scope by bundle id |
| `network dump [limit] --include summary\|headers\|body\|all` | HTTP evidence from app traffic | The first probe for any data-shaped bug |
| `events [limit]` | Compact session command timeline | Payloads are length-redacted |
| `record start [path] [--hide-touches] [--scope device]` / `record stop` | Video proof | Default scope = app session |
| `perf metrics --json` / `perf frames --json` / `perf memory sample --json` | First-pass perf | Bounded JSON, agent-safe |
| `perf memory snapshot --kind memgraph --out <p>` / `perf cpu profile … --kind xctrace` / `perf trace … --kind xctrace` | Heavy artifacts | Path+size metadata only; never paste artifact contents |
| `trace start <path>` … `trace stop <path>` | Low-level session diagnostics around one repro | Path positional on both |
| `debug symbols --artifact crash.ips --search-path ./build` | Symbolicate Apple crashes | Needs matching dSYMs; narrow by design |
| `audio probe start <sec> <bucketMs>` | Did it make sound? | Host ScreenCaptureKit; needs Screen Recording permission |
| `artifacts` | List session/cloud artifacts | |

## Environment control

| Command | Use for |
|---|---|
| `settings wifi\|airplane\|location on\|off`, `settings location set <lat> <lon>` | Connectivity/geo states |
| `settings appearance light\|dark\|toggle` | Theme testing |
| `settings faceid\|touchid match\|nonmatch\|enroll\|unenroll` | Biometric flows |
| `settings permission grant\|deny\|reset <camera\|microphone\|photos\|notifications\|location\|…>` | Pre-set permission state **before** a flow (never to answer a visible dialog — that's `alert`) |
| `settings clear-app-state [app-id]` | Wipe local app data for fresh-install behavior |
| `push <bundleId> <payloadJson>` | Deliver push payloads to the simulator |
| `trigger-app-event <event> [payloadJson]` | App-defined test hooks |

## Automation & suites

| Command | Use for | Notes |
|---|---|---|
| `batch --steps <json>` / `--steps-file` | Known stable multi-step flows in one request | Step keys: `command`, `input` (not `args`) |
| `replay <flow.ad>` | Re-run recorded session | `-u` heals selectors in place; `--maestro` runs a Maestro-YAML subset |
| `test <glob>…` | Replay suites | `--retries`, `--record-video`, `--reporter junit:<path>`, `--shard-all N --device a,b` |
| `mcp` | Run as MCP server | For MCP-based integrations instead of shell |

## React Native / dev server

| Command | Use for | Notes |
|---|---|---|
| `metro reload` | Push JS changes to the running app | **There is no `agent-device reload`** |
| `metro prepare [--kind expo\|react-native\|repack] [--port N]` | Start/verify a dev server | Multi-worktree: distinct ports + `open … --metro-port` hints |
| `react-native dismiss-overlay` | Clear LogBox/RedBox safely | Never press overlay text manually |
| `react-devtools status\|wait --connected\|profile …` | Component internals, slow renders, rerenders | `status` before `wait`; profile window narrow; details: `help react-devtools` |
| `cdp target list\|memory usage\|memory snapshot …` | JS-heap leak evidence | Not the default profiler; details: `help cdp` |

## Remote / cloud (only when the task says so)

`auth`, `connect`, `connection`, `disconnect`, `proxy` — lifecycle is connect → open → commands → close → disconnect. Details: `agent-device help remote`.

## Global flags worth knowing

- `--json` — structured output (rects live in `snapshot -i --json`)
- `--level digest` — token-cheap responses
- `--session <name>` — explicit session binding (default session is per-worktree)
- `--cost` — per-command wall-clock in the response
- `--debug` — daemon diagnostic ids and log paths; `runner.log` = Apple runner output, `daemon.log` = daemon lifecycle
