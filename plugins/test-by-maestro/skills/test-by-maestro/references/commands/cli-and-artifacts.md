# CLI Flags, Artifacts, and Hierarchy Inspection

Maestro CLI provides declarative test execution, offline syntax validation, view hierarchy inspection, device lifecycle management, a 10-tool Model Context Protocol (MCP) server, and test reporting across iOS Simulators, Android devices/emulators, and Web (Chromium, Beta).

Facts below were checked against the Maestro `2.11.0` source (latest release, 2026-09-29) and `docs.maestro.dev`. Where docs and source disagree, both are stated.

## CLI Verification and Global Scope

```bash
# Install Maestro CLI if missing (the script needs java, unzip, curl)
curl -fsSL "https://get.maestro.mobile.dev" | bash

maestro --version
# Latest release: 2.11.0. Java 17+ is required; Java 17 or 21 is recommended.
```

The launcher uses `$JAVA_HOME` when set, otherwise `java` from `PATH`, and exits with `ERROR: Java 17 or higher is required.` below 17. `$JAVA_HOME` is therefore optional, but non-interactive shells (SSH, agent shells, MCP clients) often lack both.

Inspect command help (every subcommand except `check-syntax` and `mcp`):

```bash
maestro --help
maestro test --help
maestro hierarchy --help
maestro start-device --help
maestro list-devices --help
```

`maestro check-syntax --help` fails with `Missing required parameter: '<file>'` (it takes only `<file>` or `-` for stdin). `maestro mcp --help` is an unknown option (picocli, no help mixin); give its flags directly: `--no-viewer`, `--viewer-port=<port>`, `--working-dir=<dir>`.

### Global Options

These are declared on the top-level `maestro` command, so put them **before** the subcommand: `maestro --device <id> --verbose test flow.yaml`.

- `--device=<id>` / `--udid=<id>`: iOS Simulator UDID, Android ADB serial, or `chromium`. Accepts a comma-separated list for sharding: `--device "emulator-5554,emulator-5556"`.
- `-p, --platform=<android|ios|web>`: filters the target platform. `start-device`, `list-devices`, and `list-cloud-devices` declare their own `--platform`; `hierarchy`, `cloud`, `record`, and `mcp` do not accept it.
- `--verbose`: internal diagnostic logging (top-level only).
- `--[no-]ansi`, `--[no-]color`: toggle ANSI formatting.

Device selection behavior: `maestro test` without `--device` silently uses the **first** connected device; `maestro hierarchy` fails with `Multiple devices connected`. Always pass `--device` when more than one device is attached.

---

## Offline Syntax Checking

```bash
maestro check-syntax flows/login.yaml
cat flows/smoke.yaml | maestro check-syntax -
```

- Prints `OK` and exits `0`; any `CliError` (missing file, empty input, bad syntax) exits `1`.
- Accepts a full flow (header + commands), a bare command list, or a single command.
- **False-green warning**: because a bare command list passes, `check-syntax` also passes a header-less subflow file that `runFlow` will later reject with `Config Section Required`. Always give subflows an `appId:` header and `---` (see [Flows and Selectors](flows-and-selectors.md)).
- It validates structure only; it never connects to a device.

---

## Test Execution and Reports (`maestro test`)

```bash
mkdir -p artifacts
maestro --device "$DEVICE_ID" test flows/checkout.yaml \
  --test-output-dir artifacts/run-01 \
  --format JUNIT \
  --output artifacts/junit.xml
```

### Key Execution Flags

| Flag | Purpose | Default / Notes |
|---|---|---|
| `<flowFiles>...` | One or more flow files, or a workspace directory | Required |
| `--test-output-dir=<dir>` | Per-flow artifact bundles (screenshots, `commands.json`, videos) | Reports are **not** written here |
| `--format=<fmt>` | Report format: `JUNIT`, `HTML`, `HTML-DETAILED`, `NOOP` | `NOOP` |
| `--output=<file>` | Report file path | `report.xml` / `report.html` in the **current directory** if omitted |
| `--config=<file>` | Workspace config file | Not auto-discovered for a single flow file; for a directory, `config.yaml`/`config.yml` is read **only from the directory you pass** |
| `-e, --env=<KEY=VALUE>` | Runtime variables (repeatable) | A plain `env:` header value overrides `-e`; use `KEY: ${KEY \|\| "default"}` in the header so `-e` wins |
| `--include-tags` / `--exclude-tags` | Comma-separated tag filters | OR semantics; CLI tags are **added** to config `includeTags`, not overriding them |
| `-c, --continuous` | Re-run when the flow file changes | Single flow only; rejected with multiple flows, directories, or `--format` |
| `--debug-output=<path>` | Debug logs root | Creates `<path>/.maestro/tests/<timestamp>/`; with `--test-output-dir` also set, it receives only the session `maestro.log` |
| `--flatten-debug-output` | Flat output, no timestamp folders | **Ignores `--test-output-dir`**; writes to `--debug-output`, or to `$HOME` if that is omitted. Pair it with `--debug-output` |
| `--test-suite-name=<name>` | `<testsuite name>` in JUnit XML | `Test Suite`; only the JUnit reporter uses it |
| `--[no-]reinstall-driver` | Reinstall the on-device/iOS driver | **Default `true`** (reinstalls every run); `--no-reinstall-driver` skips |
| `--shard-all=<N>` / `--shard-split=<N>` | Run the suite on N devices redundantly / partitioned | Mutually exclusive; need N connected devices; cannot be combined with `executionOrder` |
| `-s, --shards=<N>` | Deprecated alias for `--shard-split` | Prints a deprecation warning |
| `--headless` | *(Web)* headless Chromium | `false` |
| `--screen-size=<WxH>` | *(Web)* viewport, effective with `--headless` | Browser default |
| `--analyze` | Insights: extra screenshots, full-run recording, AI analysis | Requires Maestro Cloud login (`maestro login` or `MAESTRO_CLOUD_API_KEY`) |

### Artifact Layout

Since 2.7.0 each run writes a timestamped session folder with one folder per flow:

```text
artifacts/run-01/
└── 2026-10-10_173617/              # session folder
    ├── maestro.log                  # session-wide log (iOS: xctest_runner_*.log)
    └── checkout/                    # one folder per flow (-shard-N suffix when sharded)
        ├── manifest.json            # INDEX of artifacts: kind, format, relativePath, size/count, optional metadata
        ├── commands.json            # per-step command, status, duration, sequenceNumber
        ├── logs/                    # maestro.log, device-logcat.txt (Android) or device-simulator.log + device-xctest.log (iOS), crash/ANR reports
        ├── screenshots/             # failing-step screenshot (all steps with --analyze)
        ├── screen-hierarchy/
        ├── takeScreenshot/          # takeScreenshot command outputs (<path>.png)
        ├── startRecording/          # startRecording outputs (<path>.mp4)
        └── ai-analysis/
```

- A normal `maestro test` captures only the **failing step**; `--analyze` adds a screenshot before every step, `final.png`, and `screen-recording.mp4`.
- `manifest.json` is an artifact index, not run metadata. `metadata.startedAtEpochMs` appears only on the full-run `SCREEN_RECORDING` entry (the `--analyze` recording), not on `startRecording` videos.
- JUnit/HTML reports and the default `report.xml` live outside `--test-output-dir`; upload both locations from CI.
- Always preserve the whole artifact directory across CI boundaries or SSH transfers.

---

## View Hierarchy Inspection (`maestro hierarchy`)

```bash
maestro --udid "$DEVICE_UDID" hierarchy            # JSON element tree
maestro --udid "$DEVICE_UDID" hierarchy --compact  # CSV
```

`hierarchy` reinstalls the driver by default; `--reinstall-driver` is a no-op and `--no-reinstall-driver` skips it.

- **`id`** = `accessibilityIdentifier` (iOS) / `resource-id` (Android); the most stable locator.
- **`text`** matches visible text, hint text, accessibility text, and (Android) the error string.
- **Bounds** are the string `[left,top][right,bottom]` on both platforms.

Compact CSV schema: `element_num,depth,attributes,parent_num`. Attributes are `key=value` pairs joined by `; `, boolean attributes appear only when true, and the root's `parent_num` is empty:

```text
element_num,depth,attributes,parent_num
0,0,"bounds=[0,0][393,852]",
1,1,"resource-id=submit_button; text=Submit Order; bounds=[20,400][373,450]; clickable=true",0
```

---

## Device Lifecycle Management

### `maestro start-device`

```bash
# iOS Simulator (macOS only)
maestro start-device --platform=ios --device-model=iPhone-16-Pro --device-os=iOS-18-2

# Android emulator (Linux or macOS); the system-image ABI must match the host CPU
maestro start-device --platform=android --device-model=pixel_6 --device-os=android-34 \
  --device-locale=en_US --force-create
```

- `--platform=<android|ios|web>` is required.
- `--device-model`: run `maestro list-devices` for supported models (docs cite `pixel_6`, `pixel_7`, `iPhone-16-Pro`). `pixel_9` is not documented anywhere.
- `--device-os`: `iOS-18-2`, `android-34`, `android-37` (Android 17, supported since 2.11.0), or a full system image such as `system-images;android-34;google_apis;x86_64` (since 2.10.0). On x86_64 hosts an `arm64-v8a` image fails with `systemImage abi segment ... must match cpuArchitecture`.
- Defaults from source: Android `pixel_6` / `android-33`; iOS `iPhone-11` / `iOS-17-5` (docs say iOS 15.5).
- **Interactive prompt**: if the system image is missing, `start-device` asks `Would you like to install it? y/n`, which hangs in agent shells. Pre-install with `sdkmanager` first.
- The emulator is launched with a window; for servers use the headless recipe in [Android and Local iOS](../guides/android-and-local-ios.md).
- `--device-locale=<locale>` (e.g. `de_DE`), `--force-create` overwrites an existing virtual device.

### `maestro list-devices` and `list-cloud-devices`

```bash
maestro list-devices [--platform=ios|android|web]   # connected AND launchable (not necessarily booted) models
maestro list-cloud-devices                          # Maestro Cloud models/OS (needs login)
```

`list-devices` prints models grouped with OS versions, not serials or UDIDs. Get IDs from `adb devices`, `xcrun simctl list devices booted --json`, or the MCP `list_devices` tool.

---

## Deprecated and Unbundled Tooling

1. **Maestro Studio** was unbundled in 2.6.0 (deprecation notice since 2.4.0). `maestro studio` is now a hidden command that prints `Maestro Studio is no longer bundled with the CLI.` followed by `Download the new Maestro Studio desktop app instead:` and an OS-specific URL (`https://studio.maestro.dev/MaestroStudio.dmg`, `.exe`, or `.AppImage`). The bare `https://studio.maestro.dev/` is a bucket listing; `https://maestro.dev/#maestro-studio` is the landing page. In 1.x the Studio port was the first free port in 9999-11000.
2. **`maestro chat`** (MaestroGPT) was discontinued in 2.7.0. Use the MCP server.
3. **`--ios-version`, `--android-api-level`, `--os-version`** are deprecated in favor of `--device-os` / `--device-model`.

---

## Model Context Protocol (MCP) Server (`maestro mcp`)

The MCP transport is STDIO. Docs (`https://docs.maestro.dev/get-started/maestro-mcp`) list Claude Code, Claude Desktop, Cursor, GitHub Copilot, Codex, Gemini, Windsurf, and JetBrains AI Assistant as supported clients.

```bash
maestro mcp                                              # default, with local viewer
maestro mcp --no-viewer                                  # no viewer
maestro mcp --viewer-port 8080 --working-dir /path/repo  # fixed viewer port, base dir for files/dir
```

The viewer is a separate local HTTP server (`127.0.0.1`, free port by default) that serves a page plus an SSE events endpoint; the URL is printed to stderr as `mcp_viewer_ready http://127.0.0.1:<port>`. `--working-dir` is the base for relative `files`, `dir`, `app_file`, and `flows` arguments (otherwise the server's cwd).

### The 10 MCP Tools (v2.11.0, from source)

Docs list only 9 (no `describe_cloud_run`); the source has 10. History: 2.5.0 consolidated `run_flow`/`run_flow_files` into `run` and dropped `tap_on`, `input_text`, `back`, `launch_app`, `stop_app`, `check_flow_syntax`, `start_device`, `query_docs`; 2.6.0 added `open_maestro_viewer`; 2.7.0 added `describe_cloud_run`.

| Tool | Parameters | Notes |
|---|---|---|
| `list_devices` | none | Returns `{devices:[{device_id,name,platform,type,connected}]}` including launchable devices with `connected:false`. Use only `connected:true` ids. |
| `inspect_screen` | `device_id` (required) | Compact JSON `{ui_schema, elements}`. |
| `take_screenshot` | `device_id` (required) | **JPEG** (quality 0.9), longest side downscaled to 2000 px if larger. |
| `run` | `device_id` (required) + exactly one of `yaml` (string), `files` (string[]), `dir` (string); `include_tags`/`exclude_tags` (only with `dir`); `env` (map) | Validates syntax first. Returns JSON `{success, device_id, commands_executed, message}`; `isError` on failure. |
| `cheat_sheet` | none | Fetches the command syntax reference over the network. |
| `open_maestro_viewer` | none | Returns text `Maestro Viewer is available at <url>.`; errors under `--no-viewer`. Surface the URL to the user, do not launch a browser. |
| `list_cloud_devices` | none | Needs cloud auth. |
| `run_on_cloud` | `app_file`, `flows` (both required **strings**); optional `name`, `project_id`, `env`, `include_tags`, `exclude_tags`, `device_model`, `device_os` | Needs `maestro login` or `MAESTRO_CLOUD_API_KEY` and a Cloud plan/trial. Always returns immediately: `upload_id`, `project_id`, `app_id`, `url`, `status: PENDING`. `project_id` is required if the account has several projects. No `device_locale` or `async` parameter. |
| `get_cloud_run_status` | `upload_id`, `project_id` (both required); `include_flow_results` | Poll about every 60 s until `SUCCESS`/`ERROR`/`CANCELED`/`WARNING`. |
| `describe_cloud_run` | `run_id` (required); `include_archive` | `run_id` is the per-flow id from a dashboard run URL, **not** the `upload_id`. |

#### Rules for Agents

1. **No MCP tool boots a device.** Boot it first (`maestro start-device`, `xcrun simctl boot`, or the user), then call `list_devices`. Web (`chromium`) is always listed and opens a visible, non-headless Chromium.
2. **Declarative actions via `run`**: pass inline YAML.
   ```json
   {
     "device_id": "emulator-5554",
     "yaml": "appId: com.example.demo\n---\n- tapOn: \"Log In\"\n- inputText: \"user@example.com\"\n- hideKeyboard"
   }
   ```
   The server's own instructions: mobile flows declare `appId` and start with `launchApp`; web flows declare `url` and start with `openLink`; prefer one full flow over many single-command calls; tag filters are bare names without `@`. A bare command list is also accepted by `run`; if relative `runFlow`/`runScript` paths are needed in inline YAML, use `files`/`dir` instead (inline YAML is written to a temporary file, so relative resolution is unverified).
3. **Compact screen schema (`inspect_screen`)** abbreviations:
   - `b`: bounds string `"[x1,y1][x2,y2]"` (left, top, right, bottom)
   - `txt`: text, `rid`: resource-id / accessibilityIdentifier, `a11y`: accessibility text, `hint`: placeholder, `c`: children
   - `cls` and `scroll`: Android only; `val`: iOS only
   - `a11y` is not a valid selector key. Map it to `text:`, and `rid` to `id:`. Because `text:` is a full-string, case-insensitive regex, copy `txt` values verbatim rather than reading them off a screenshot.

### MCP Client Configurations

Source: `https://maestro.dev/mcp` and `https://docs.maestro.dev/get-started/maestro-mcp`. Use an absolute `maestro` path (or set `PATH`/`JAVA_HOME` in `env`) when the client does not inherit your shell profile. Add `"--working-dir", "<repo>"` to `args` when flows live in a repository.

#### 1. Claude Code
```bash
claude mcp add maestro -- maestro mcp
```

#### 2. Cursor IDE / CLI (`~/.cursor/mcp.json` or `.cursor/mcp.json`)
```json
{
  "mcpServers": {
    "maestro": {
      "command": "maestro",
      "args": ["mcp"],
      "env": { "JAVA_HOME": "/path/to/java17+" }
    }
  }
}
```

#### 3. OpenAI Codex CLI / Desktop
```bash
codex mcp add maestro -- maestro mcp
```
Or `~/.codex/config.toml`:
```toml
[mcp_servers.maestro]
command = "maestro"
args = ["mcp"]
```

#### 4. Gemini CLI
`gemini mcp add` defaults to **project** scope (writes `.gemini/settings.json` in the current directory); add `-s user` for `~/.gemini/settings.json`:
```bash
gemini mcp add -s user maestro maestro mcp
```

#### 5. Antigravity
Antigravity does not read `settings.json`: global servers live in `~/.gemini/config/mcp_config.json`, workspace servers in `.agents/mcp_config.json` (Antigravity migration docs). Antigravity is not on Maestro's own client list.

#### 6. Windsurf
Windsurf is not on Maestro's client page (only linked to Windsurf's docs). Current Windsurf docs put `mcp_config.json` at `~/.config/devin/mcp_config.json` (macOS/Linux); the older `~/.codeium/windsurf/mcp_config.json` may still work for legacy Cascade (unverified).

---

## Related References

- [Flows and Selectors](flows-and-selectors.md) — YAML syntax, commands, and selector strategies.
- [iOS over SSH](../guides/ios-over-ssh.md) — Running tests and retrieving artifacts across remote hosts.
- [Android and Local iOS](../guides/android-and-local-ios.md) — Local simulator, emulator, and Linux setup.
- [Suites and CI](../patterns/suites-and-ci.md) — Tag filtering, report gates, and test suites.
