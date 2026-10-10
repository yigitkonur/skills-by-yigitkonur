---
name: test-by-maestro
description: "Use if writing, running, or debugging Maestro E2E test flows on iOS Simulators, Android, or Web, including MCP agent automation and CI suites."
---

# Test Mobile and Web UI with Maestro

Author, validate, execute, and diagnose E2E tests with Maestro across iOS Simulators (macOS host or Maestro Cloud), Android emulators or physical devices (Linux, macOS, Windows), and Web (Chromium). This skill owns declarative YAML test flow authoring, individual interactive action execution via Model Context Protocol (MCP), offline syntax verification, local and cloud/SSH execution, artifact retrieval, and failure diagnosis. It does not own building the application binary, managing cloud provider billing, or configuring backend test fixtures.

## When to use this skill

- Writing declarative Maestro YAML flows for iOS Simulators, Android emulators/devices, or Web applications
- Driving tests interactively via Maestro's native Model Context Protocol server (`maestro mcp`) with AI coding agents (Claude Code, Cursor, Codex, Gemini CLI)
- Taking individual exploratory actions on a live mobile device cleanly via MCP `run` using inline YAML commands
- Running UI test suites locally on macOS (iOS & Android) or Linux (Android & Web locally; iOS via Maestro Cloud or SSH to macOS)
- Creating modular, reusable test flows (`runFlow`), lifecycle hooks (`onFlowStart`, `onFlowComplete`), and parameterized suites (`env`)
- Debugging failing tests, broken element selectors, or accessibility tree mismatches with `maestro hierarchy` or MCP `inspect_screen`
- Validating flow YAML syntax offline via `maestro check-syntax` (or automatically inside MCP `run`)
- Managing local virtual test devices with `maestro start-device`, `maestro list-devices`, and cloud devices with `maestro list-cloud-devices`
- Collecting and interpreting test artifacts including JUnit XML reports, console logs, and failure screenshots

## Do NOT use this skill when

- Writing unit or component tests (e.g., Jest or Vitest for React Native components)
- Interactive exploratory web browsing without mobile/declarative YAML regression requirements (prefer `ego-browser`)
- Building, compiling, or refactoring application source code
- Automating physical iOS devices locally (Maestro 2.11.0 explicitly fails fast with `"Physical iOS devices are not yet supported"`)
- Testing raw MCP server implementations directly (use `test-by-mcpc-cli`; use this skill when driving Maestro's built-in `maestro mcp` server)

## Source of truth

1. Confirm installed CLI: run `maestro --version` (install if missing: `curl -fsSL "https://get.maestro.mobile.dev" | bash`). Tested baseline is `2.11.0` / `2.10.0` (requires Java 17+ via `$JAVA_HOME`).
2. Inspect scoped command options with `maestro --help`, `maestro test --help`, `maestro cloud --help`, `maestro hierarchy --help`, `maestro start-device --help`, `maestro list-devices --help`, and `maestro mcp --help`. Note that `check-syntax` takes only `<file>` or `-` (stdin) without `--help`.
3. Maestro Studio & Viewer: in Maestro 2.6.0+, Studio was unbundled from the CLI into a standalone desktop application (`https://studio.maestro.dev/`). For coding agents, Maestro embeds the **Maestro Viewer** (`open_maestro_viewer` in MCP), enabling real-time visual streaming of the device screen and commands. Terminal inspection uses `maestro hierarchy` (default JSON, or `--compact` CSV) and `maestro test --continuous` (`-c`).
4. Platform boundaries:
   - **macOS Workstations**: Can run iOS Simulators (requires Xcode `xcode-select -p`), Android emulators/devices (requires ADB), and Web (Chromium). Maestro packages pinned `applesimutils` internally (`~/.maestro/deps/applesimutils`) for simulator permissions.
   - **Linux Hosts**: Can run Android emulators (with `/dev/kvm`), physical Android devices, and Web locally. **Linux cannot run iOS Simulators locally**; for iOS testing on Linux, upload binaries to **Maestro Cloud** (`maestro cloud` / MCP `run_on_cloud`) or orchestrate remote runs over SSH to a macOS host.
   - **Physical Devices**: Android physical devices are fully supported via ADB. Physical iOS devices are not supported locally in Maestro 2.11.0.

## Load-bearing rules

| # | Rule | Why |
|---|---|---|
| 1 | Individual actions via MCP `run` | In Maestro 2.5.0+, granular tool wrappers (`tap_on`, `input_text`) were consolidated into the declarative `run` tool. For single exploratory actions, pass inline YAML: `{ "device_id": "...", "yaml": "- tapOn: \"Log In\"" }`. |
| 2 | Respect Linux vs macOS platform realities | iOS Simulators require Darwin/Xcode. When authoring on Linux, execute iOS tests via Maestro Cloud (`maestro cloud` / `run_on_cloud`) or remote macOS SSH; never attempt local `xcrun simctl` or local iOS boots on Linux. |
| 3 | Export explicit remote/non-interactive environment | Non-interactive SSH and agent shells omit user profile paths; always export `JAVA_HOME="${JAVA_HOME:-/opt/homebrew/opt/java}"` and `PATH="$JAVA_HOME/bin:$HOME/.maestro/bin:/opt/homebrew/bin:$PATH"` alongside `DEVELOPER_DIR`. |
| 4 | Uniquely select target device | Parse `xcrun simctl list devices --json` or `adb devices`; require exactly one booted match or explicit caller target (`--device <id>`). Multi-device parallel runs on macOS use dynamic ports (`SIMCTL_CHILD_PORT`) since Maestro 2.6.0. |
| 5 | Design reusable subflows with parameterized `env` | Encapsulate repeated routines (auth, onboarding, teardown) into `subflows/`. Pass context via `runFlow.env`; access via `${VARIABLE}`. Use `onFlowStart` and `onFlowComplete` hooks to guarantee state hygiene. |
| 6 | Hierarchy-backed selectors and regex wildcards | Inspect `maestro hierarchy` or MCP `inspect_screen` on failures; note `text:` performs a **full-string regex match** (`IGNORE_CASE`). Use `.*Text.*` for partial copy matching. Never pass `start:` or `end:` in element selectors (2.11.0 breaking rule). |
| 7 | Choose reset strategy by runtime and session | Standalone builds use `clearState: true` and `clearKeychain: true` (iOS). Running Expo Dev Client sessions must omit `launchApp` to preserve Metro bundler connections and use deep links instead. |
| 8 | Preserve exit status and full artifacts | Transport logs, JUnit XML, screenshots, and `manifest.json` (with `startedAtEpochMs`); never convert test failure into success. |

## Interactive Agent Automation via MCP (`maestro mcp`)

Maestro embeds a Model Context Protocol (MCP) server over STDIO (`maestro mcp`), exposing 10 tools for coding agents:

### Agent Setup Commands (`https://maestro.dev/mcp`)

- **Claude Code**: `claude mcp add maestro -- maestro mcp`
- **Cursor IDE / CLI**: Add to `~/.cursor/mcp.json` or `.cursor/mcp.json`:
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
- **Codex CLI**: `codex mcp add maestro -- maestro mcp`
- **Gemini CLI / Antigravity**: `gemini mcp add maestro maestro mcp` or in `settings.json`:
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

### Taking Individual Actions Cleanly

Coding agents should follow an exploratory iterative loop:
1. **Identify Device**: Call `list_devices` to retrieve the active `device_id` (e.g. `emulator-5554` or simulator UDID).
2. **Inspect Screen**: Call `inspect_screen` with `device_id` to inspect the compact view hierarchy and locate target `id` or `text`.
3. **Execute Action**: Call `run` with inline YAML in the `yaml` argument:
   ```json
   {
     "device_id": "emulator-5554",
     "yaml": "- tapOn: \"Sign In\""
   }
   ```
   Or chain related atomic actions:
   ```json
   {
     "device_id": "emulator-5554",
     "yaml": "- inputText: \"user@example.com\"\n- hideKeyboard: { optional: true }\n- tapOn: \"Continue\""
   }
   ```
4. **Visual Stream**: Call `open_maestro_viewer` to launch the live embedded web viewer in browser/IDE.
5. **Persist Test**: Once the flow passes interactively, save the commands into a permanent YAML flow file in `.maestro/flows/`.

## Authoring Reusable and Ready-Made Tests

Structure test workspaces to maximize modularity and regression stability:

```text
.maestro/
├── config.yaml               # Global suite config, tags, and execution order
├── flows/                    # Top-level end-to-end flows
│   ├── 01-auth-smoke.yaml
│   └── 02-checkout.yaml
├── subflows/                 # Reusable building blocks
│   ├── login-user.yaml
│   └── clear-cart.yaml
└── scripts/                  # Synchronous GraalJS helpers
    └── generate-test-data.js
```

### 1. Ready-Made Reusable Subflow (`subflows/login-user.yaml`)
```yaml
# subflows/login-user.yaml
# Parameterized login subflow with fallback defaults
- tapOn:
    id: "login_email_input"
- inputText: ${USER_EMAIL || "testuser@example.com"}
- tapOn:
    id: "login_password_input"
- inputText: ${USER_PASSWORD || "Password123!"}
- hideKeyboard:
    optional: true
- tapOn: "Sign In"
- assertVisible: "Dashboard"
```

### 2. Main Test Flow with Hooks and Parameters (`flows/02-checkout.yaml`)
```yaml
appId: com.example.shop
tags:
  - smoke
  - checkout
env:
  CHECKOUT_ITEM: "Wireless Headphones"
onFlowStart:
  - launchApp:
      clearState: true
      clearKeychain: true
  - runFlow:
      file: ../subflows/login-user.yaml
      env:
        USER_EMAIL: "shopper@example.com"
onFlowComplete:
  - runFlow: ../subflows/clear-cart.yaml
---
- tapOn: ${CHECKOUT_ITEM}
- tapOn: "Add to Cart"
- tapOn: "Cart"
- assertVisible: ${CHECKOUT_ITEM}
- tapOn: "Proceed to Checkout"
- assertVisible: "Order Confirmation"
- takeScreenshot: artifacts/checkout_success
```

## Minimal read sets

Choose the route matching your task; read only the relevant leaves before acting:

| Task Intent | Read First |
|---|---|
| CLI syntax, flags, MCP tools, report paths, or view hierarchy | [CLI and Artifacts](references/commands/cli-and-artifacts.md) |
| Authoring flow YAML, commands, and selector strategies | [Flows and Selectors](references/commands/flows-and-selectors.md) |
| Linux authoring host running tests on remote macOS via SSH | [iOS over SSH](references/guides/ios-over-ssh.md) |
| Local Android emulator/device or local macOS iOS Simulator | [Android and Local iOS](references/guides/android-and-local-ios.md) |
| JavaScript scripting, HTTP helpers, and dynamic test data | [GraalJS Scripting](references/guides/graaljs.md) |
| Element visibility, keyboard races, animations, or scrolling | [Mobile Flakiness](references/troubleshooting/mobile-flakiness.md) |
| Expo Dev Client continuity, Keychain tokens, or auth resets | [Expo and State](references/troubleshooting/expo-and-state.md) |
| Subflows, tags, CI pipeline integration, and report gates | [Suites and CI](references/patterns/suites-and-ci.md) |

## Quick start

For an existing installed application on a local simulator, emulator, or web browser:

```yaml
# flows/smoke.yaml
appId: com.example.demo
---
- launchApp:
    clearState: true
- assertVisible: "Welcome"
- tapOn:
    id: "login_button"
- inputText: "user@example.com"
- hideKeyboard:
    optional: true
- tapOn: "Continue"
- assertVisible: "Dashboard"
- takeScreenshot: screenshots/dashboard_loaded
```

Validate syntax offline, then run:

```bash
# Offline syntax check (single file or stdin)
maestro check-syntax flows/smoke.yaml

# Local execution with JUnit report and artifact collection
mkdir -p artifacts
maestro test flows/smoke.yaml \
  --test-output-dir artifacts \
  --format JUNIT \
  --output artifacts/report.xml
```

Successful runs return exit code 0 and populate `artifacts/` with logs, JUnit XML, and screenshots.

## Standard workflow

1. **Preflight**: Verify `maestro --version` and target runtime availability (`java -version`, `adb devices`, or `xcrun simctl`).
2. **Author and Check**: Draft declarative YAML flows; run `maestro check-syntax <flow>` (or use MCP `run` which validates syntax automatically).
3. **Target and Lease**: Resolve target UDID, ADB serial, or `--platform=web`; ensure target device is available.
4. **Execute**: Run `maestro test` with `--test-output-dir` and `--format JUNIT --output <path>` (or execute interactively via `maestro mcp`).
5. **Retrieve and Inspect**: On remote runs, fetch the full artifact directory; inspect `maestro hierarchy` or MCP `inspect_screen` if an element is missed.
6. **Release**: Report binary pass/fail evidence and retain telemetry.

## Output contract

Every test execution report must specify:
- Target host, platform (`android`, `ios`, or `web`), and resolved device ID/name
- Installed Maestro CLI version
- Flow scope and state reset policy applied
- Command exit status and JUnit pass/fail summary
- Local path to collected artifacts (console logs, reports, screenshots)
- Diagnostic classification for any observed failure

## Guardrails and recovery

- Never steal an existing driver lock without coordinating with device operators.
- Do not reboot devices, reinstall drivers, or wipe simulator runtimes automatically on a test failure.
- Never hardcode environment secrets, personal names, or static IP/UDID strings into flow files.
- If remote SSH or Maestro Cloud transport succeeds but the test exits non-zero, report test failure and preserve retrieved logs.
