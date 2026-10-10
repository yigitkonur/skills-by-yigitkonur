# CLI Flags, Artifacts, and Hierarchy Inspection

Maestro CLI provides declarative test execution, offline syntax validation, view hierarchy inspection, device lifecycle management, a 10-tool Model Context Protocol (MCP) server, and test telemetry reporting across iOS Simulators, Android devices/emulators, and Web (Chromium).

## CLI Verification and Global Scope

Verify the installed binary and runtime baseline:

```bash
# Install Maestro CLI if missing
curl -fsSL "https://get.maestro.mobile.dev" | bash

maestro --version
# Baseline: 2.11.0 / 2.10.0 (requires Java 17+)
```

Inspect command help and available options:

```bash
maestro --help
maestro test --help
maestro hierarchy --help
maestro start-device --help
maestro list-devices --help
```

Note: `maestro check-syntax` does not accept `--help` or `-h`; it strictly takes `<file>` or `-` for stdin. Similarly, `maestro mcp` does not support `--help` (exits 2 with `Unknown option: '--help'`); its flags (`--no-viewer`, `--viewer-port=<port>`, `--working-dir=<dir>`) must be specified directly.

### Global Options

Maestro accepts platform and device targeting flags at both top-level and subcommand scopes:

- `--device=<deviceId>` or `--udid=<deviceId>`: Specifies the target iOS Simulator UDID, Android ADB serial, or browser target. Can accept a comma-separated list of IDs for multi-device sharding: `--device "Emulator_1,Emulator_2"`.
- `-p, --platform=<platform>`: Filters target platform (`android`, `ios`, `web`).
- `--verbose`: Enables internal diagnostic logging.
- `--[no-]ansi`, `--[no-]color`: Enables or disables ANSI color escape formatting in console output.

---

## Offline Syntax Checking

Validate flow YAML structure, headers, and command keys without connecting to any device, simulator, or browser:

```bash
# Validate a specific flow file
maestro check-syntax flows/login.yaml

# Validate from standard input
cat flows/smoke.yaml | maestro check-syntax -
```

- **Strict Argument Handling**: `check-syntax` rejects flags like `--help` or `-h`. Running `maestro check-syntax --help` fails with `Missing required parameter: '<file>'`.
- **Exit Status**: Returns `0` if all command names, parameters, and flow structures parse cleanly; returns `1` on invalid keys, malformed YAML, or unparseable syntax.
- **Use Case**: Fast preflight checks in CI, pre-commit git hooks, or before transferring workspaces to remote execution runners.

---

## Test Execution and Telemetry (`maestro test`)

Execute one or more flows with explicit artifact collection, JUnit reporting, and execution controls:

```bash
maestro test flows/checkout.yaml \
  --test-output-dir artifacts/run-01 \
  --format JUNIT \
  --output artifacts/run-01/junit.xml
```

### Key Execution Flags

| Flag | Purpose | Default / Values |
|---|---|---|
| `<flowFiles>...` | One or more flow YAML files or directories | Required argument |
| `--test-output-dir=<dir>` | Directory for raw test execution artifacts and logs | None (overrides default output) |
| `--format=<format>` | Test report format | `NOOP` (default), `JUNIT`, `HTML`, `HTML-DETAILED` |
| `--output=<file>` | Filepath for the formatted test report (e.g. `report.xml`) | None |
| `--config=<file>` | Path to workspace configuration file | `config.yaml` in workspace root |
| `-e, --env=<KEY=VALUE>` | Injects runtime environment variables (repeatable) | Accessible via `${KEY}` in flow |
| `--include-tags=<tags>` | Runs only flows matching comma-separated tags | All flows |
| `--exclude-tags=<tags>` | Skips flows matching comma-separated tags | None |
| `-c, --continuous` | Watch mode: re-executes flow immediately when file changes | Disabled by default |
| `--flatten-debug-output` | Places artifacts flat into folder without timestamp subdirs | Subdirectories created |
| `--debug-output=<path>` | Custom directory for debug logs | Default output path |
| `--test-suite-name=<name>`| Custom suite name in generated JUnit/HTML reports | Flow filename |
| `--[no-]reinstall-driver` | Reinstalls `xctestrunner` (iOS) or server APKs (Android) | Reinstalled if missing |
| `--shard-all=<N>` | Runs entire test suite redundantly across N devices | Mutually exclusive with `--shard-split` |
| `--shard-split=<N>` | Partitions test suite evenly across N connected devices | Mutually exclusive with `--shard-all` |
| `-s, --shards=<N>` | Legacy shard count option | None |
| `--headless` | *(Web only)* Runs Chromium in headless mode | False |
| `--screen-size=<WxH>` | *(Web only)* Headless viewport dimensions (e.g. `1920x1080`) | Default browser viewport |
| `--analyze` | *(Beta)* Enhances failure output with AI analysis | Disabled by default |

### Artifact Tree Structure

When `--test-output-dir` is configured, Maestro writes granular telemetry directly into that directory:

```text
artifacts/run-01/
├── manifest.json         # Run metadata, duration, flow paths, status, startedAtEpochMs
├── commands.json         # Step-by-step command timeline and execution timings
├── logs/                 # Console and driver communication logs
│   └── maestro.log
├── takeScreenshot/       # Captures from takeScreenshot flow commands
│   └── final_screen.png
└── startRecording/       # Screen recordings from startRecording commands
    └── flow_run.mp4
```

- **Video-Timeline Synchronization**: When video recording is enabled, `manifest.json` populates `metadata.startedAtEpochMs` to align video frames accurately with timestamps in `commands.json`.
- Always preserve this artifact directory across CI boundaries or remote SSH transfers to diagnose failures.

---

## View Hierarchy Inspection (`maestro hierarchy`)

When an element selector fails or accessibility attributes are uncertain, dump the live accessibility tree directly from the active screen:

```bash
# Standard formatted JSON element tree
maestro hierarchy

# Target specific device
maestro --udid "$DEVICE_UDID" hierarchy

# Compact tabular view (CSV format)
maestro hierarchy --compact

# Force driver re-push before hierarchy dump
maestro hierarchy --reinstall-driver
```

### Hierarchy Attributes

- **`accessibilityIdentifier` (iOS) / `resource-id` (Android)**: Represented as `id` in Maestro selectors. This is the most stable locator.
- **`accessibilityLabel` / `text`**: Visible text or accessibility descriptions.
- **Bounds**: Coordinate rectangles used for spatial debugging (`above`, `below`, `leftOf`, `rightOf`).

Compact CSV format schema:
`element_num,depth,attributes,parent_num`

Example compact CSV excerpt:
```text
element_num,depth,attributes,parent_num
0,0,"[AXApplication] name: DemoApp, frame: {{0, 0}, {393, 852}}",-1
1,1,"[AXWindow] frame: {{0, 0}, {393, 852}}",0
2,2,"[AXButton] id: submit_button, label: Submit Order, frame: {{20, 400}, {353, 50}}",1
```

---

## Device Lifecycle Management

Maestro CLI provides commands to provision, boot, and inspect local and cloud test devices:

### `maestro start-device`
Creates and boots an emulator or simulator matching cloud specifications:

```bash
# Launch or create an iOS Simulator
maestro start-device --platform=ios --device-model=iPhone-16-Pro --device-os=iOS-18-2

# Launch an Android Emulator with specific locale and full system image
maestro start-device --platform=android \
  --device-model=pixel_6 \
  --device-os="system-images;android-34;google_apis_playstore;arm64-v8a" \
  --device-locale=en_US \
  --force-create
```

- **Options**:
  - `--platform=<android|ios|web>` (Required)
  - `--device-model=<model>`: e.g. `iPhone-16-Pro`, `pixel_6`, `pixel_9` (see `maestro list-cloud-devices`)
  - `--device-os=<os>`: e.g. `iOS-18-2`, `android-34`, `android-37` (Android 17 API 37 supported in 2.11.0), or full system image path
  - `--device-locale=<locale>`: Combination of ISO-639-1 language and ISO-3166-1 country (e.g. `de_DE`, `en_US`)
  - `--force-create`: Overwrites existing virtual device if already created

### `maestro list-devices` & `list-cloud-devices`
```bash
# List local connected ADB devices, booted simulators, and browser targets
maestro list-devices
maestro list-devices --platform=ios
maestro list-devices --platform=android
maestro list-devices --platform=web

# Query hardware models and OS versions available on Maestro Cloud
maestro list-cloud-devices
```

---

## Deprecated & Unbundled Tooling Notice

### 1. Maestro Studio Unbundled (2.6.0+)
In Maestro 1.x, `maestro studio` launched a local web server (port 9999). In Maestro 2.6.0+, Maestro Studio was unbundled from the CLI into a standalone desktop application.  
Running `maestro studio` in the CLI outputs:
> *"Maestro Studio is no longer bundled with the CLI. Download the new Maestro Studio desktop app instead: https://studio.maestro.dev/"*  
For in-terminal inspection, use `maestro hierarchy` (with `--compact`), `maestro test -c`, or `maestro mcp`.

### 2. Discontinuation of `maestro chat` (2.7.0)
`maestro chat` (MaestroGPT) was discontinued in 2.7.0. AI coding agent workflows are now driven through the native Model Context Protocol server (`maestro mcp`).

### 3. Deprecated Device Flags
The flags `--ios-version` and `--android-api-level` were deprecated in favor of unified `--device-os` and `--device-model`.

---

## Model Context Protocol (MCP) Server (`maestro mcp`)

Maestro 2.x embeds a production-grade Model Context Protocol server over STDIO, enabling AI agents (Cursor, Claude Code, Windsurf, Codex, Gemini CLI) to inspect, execute, and verify tests interactively.

### Starting the Server

```bash
# Start MCP server with default embedded viewer
maestro mcp

# Start headless MCP server without embedded viewer
maestro mcp --no-viewer

# Bind embedded SSE viewer to explicit port and set workspace directory
maestro mcp --viewer-port 8080 --working-dir /path/to/workspace
```

### The 10 MCP Tools Catalog

In Maestro 2.5.0+, `run_flow` and `run_flow_files` were consolidated into a single declarative `run` tool accepting YAML, while 8 redundant granular tools (`tap_on`, `input_text`, etc.) were dropped from the server. In 2.7.0, `describe_cloud_run` was added. The complete 10-tool roster consists of:

| # | Tool Name | Scope | Description | Primary Parameters |
|---|---|---|---|---|
| 1 | `list_devices` | Local | Enumerates local Android emulators/devices, iOS simulators, and Chromium web targets. | `platform` (optional: `android`, `ios`, `web`) |
| 2 | `inspect_screen` | Local | Dumps active screen hierarchy as compact JSON for AI element selection. | `device_id` (string, required) |
| 3 | `run` | Local | Executes declarative Maestro commands or Flow files. Accepts inline YAML, files list, or directory. | `device_id` (string, required)<br>`yaml` (string, optional)<br>`files` (array, optional)<br>`dir` (string, optional)<br>`include_tags`, `exclude_tags`, `env` |
| 4 | `take_screenshot` | Local | Captures an immediate full-screen PNG screenshot of active display (downscaled to 2000px). | `device_id` (string, required) |
| 5 | `open_maestro_viewer` | Local | Returns the HTTP streaming URL (`$viewerUrl`) for embedded Maestro Viewer live screen/timeline. | *None* |
| 6 | `cheat_sheet` | Local/Docs | Returns comprehensive syntax reference for flow commands, selectors, and assertions. | *None* |
| 7 | `list_cloud_devices` | Cloud | Queries supported `{device_model, device_os}` combinations on Maestro Cloud. | *None* |
| 8 | `run_on_cloud` | Cloud | Uploads app binary and flows to Maestro Cloud for remote execution. | `app_file` (string, required)<br>`flows` (string/array, required)<br>`device_model`, `device_os`, `device_locale`, `env`, `async` |
| 9 | `get_cloud_run_status` | Cloud | Polls execution status and flow results for a cloud `upload_id`. | `upload_id` (string, required)<br>`include_flow_results` (bool) |
| 10 | `describe_cloud_run` | Cloud | Retrieves step metadata, artifact links, logs, or zip archive for a `run_id`. | `run_id` (string, required)<br>`include_archive` (bool) |

#### Key MCP Architectural Rules for Agents:

1. **Declarative Actions via `run`**: Instead of calling separate tap or input tools, pass inline YAML to `run`:
   ```json
   {
     "device_id": "emulator-5554",
     "yaml": "- tapOn: \"Log In\"\n- inputText: \"user@example.com\"\n- hideKeyboard: { optional: true }"
   }
   ```
2. **Compact Screen Schema (`inspect_screen`)**:
   Returns `ui_schema` and `elements` using token-optimized abbreviations:
   - `b`: bounds (`[x, y, w, h]`)
   - `txt`: on-screen text
   - `rid`: Android resource-id / iOS accessibilityIdentifier
   - `a11y`: accessibilityText / content-description
   - `hint`: placeholder/hint text
   - `cls`: widget class name
   - `val`: value
   - `scroll`: scrollable boolean
   - `c`: child nodes
   *Mapping rule*: Map `a11y` attribute to Maestro's `text:` selector (or `id:` if matching `rid`). The string `a11y` is not a valid YAML selector key.

### MCP Client Configurations (Source: https://maestro.dev/mcp)

#### 1. Claude Code CLI
```bash
claude mcp add maestro -- maestro mcp
```
Or specify explicit environment paths if Java is not in non-interactive PATH:
```json
{
  "mcpServers": {
    "maestro": {
      "command": "maestro",
      "args": ["mcp"],
      "env": {
        "JAVA_HOME": "/path/to/java17+"
      }
    }
  }
}
```

#### 2. Cursor IDE / Cursor CLI (`~/.cursor/mcp.json` or `.cursor/mcp.json`)
```json
{
  "mcpServers": {
    "maestro": {
      "command": "maestro",
      "args": ["mcp"]
    }
  }
}
```

#### 3. OpenAI Codex CLI / Desktop
Via CLI command:
```bash
codex mcp add maestro -- maestro mcp
```
Or in `~/.codex/config.toml`:
```toml
[mcp_servers.maestro]
command = "maestro"
args = ["mcp"]
```

#### 4. Gemini CLI / Antigravity (`~/.gemini/settings.json`)
Via CLI command:
```bash
gemini mcp add maestro maestro mcp
```
Or directly in settings:
```json
{
  "mcpServers": {
    "maestro": {
      "command": "maestro",
      "args": ["mcp"]
    }
  }
}
```

#### 5. Windsurf (`~/.codeium/windsurf/mcp_config.json`)
```json
{
  "mcpServers": {
    "maestro": {
      "command": "maestro",
      "args": ["mcp"]
    }
  }
}
```

---

## Related References

- [Flows and Selectors](flows-and-selectors.md) — YAML syntax, commands, and selector strategies.
- [iOS over SSH](../guides/ios-over-ssh.md) — Running tests and retrieving artifacts across remote hosts.
- [Android and Local iOS](../guides/android-and-local-ios.md) — Local simulator and Android toolchain details.
- [Suites and CI](../patterns/suites-and-ci.md) — Tag filtering, report gates, and test suites.
