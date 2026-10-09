---
name: test-by-maestro
description: "Use if writing, running, or debugging Maestro E2E test flows on iOS Simulators, Android, or Web, including MCP agent automation and CI suites."
disable-model-invocation: true
---

# Test Mobile and Web UI with Maestro

Author, validate, execute, and diagnose E2E tests with Maestro across iOS Simulators, Android emulators or physical devices, and Web (Chromium). This skill owns declarative YAML test flow authoring, offline syntax verification, local and remote execution over SSH, Model Context Protocol (MCP) server automation, artifact retrieval, and failure diagnosis. It does not own building the application binary, managing cloud provider accounts, or configuring backend test fixtures.

## When to use this skill

- Writing declarative Maestro YAML flows for iOS Simulators, Android emulators/devices, or Web applications
- Running UI test suites locally or from a Linux authoring host over SSH to a macOS simulator host
- Driving tests via Maestro's native Model Context Protocol server (`maestro mcp`) with AI coding agents
- Debugging failing tests, broken element selectors, or accessibility tree mismatches with `maestro hierarchy`
- Verifying workspace syntax and modular subflow references offline without touching a physical device via `maestro check-syntax`
- Managing local virtual test devices with `maestro start-device` and `maestro list-devices`
- Collecting and interpreting test artifacts including JUnit XML reports, console logs, and failure screenshots

## Do NOT use this skill when

- Writing unit or component tests (e.g., Jest or Vitest for React Native components)
- Interactive exploratory web browsing without declarative YAML regression requirements (prefer `ego-browser`)
- Building, compiling, or refactoring application source code
- Automating physical iOS devices locally (Maestro 2.11.0 explicitly fails fast with `"Physical iOS devices are not yet supported"`)
- Testing raw MCP server implementations directly (use `test-by-mcpc-cli`; use this skill when driving Maestro's built-in `maestro mcp` server)

## Source of truth

1. Confirm installed CLI: run `maestro --version` (install if missing: `curl -fsSL "https://get.maestro.mobile.dev" | bash`). Tested baseline is `2.11.0` / `2.10.0`.
2. Inspect scoped command options with `maestro --help`, `maestro test --help`, `maestro hierarchy --help`, `maestro start-device --help`, `maestro list-devices --help`, and `maestro mcp --help`. Note that `check-syntax` takes only `<file>` or `-` without `--help`.
3. Maestro Studio status: in Maestro 2.6.0+, Studio was unbundled from the CLI into a standalone desktop application (`https://studio.maestro.dev/`); interactive terminal and agent inspection uses `maestro hierarchy`, `maestro test --continuous` (`-c`), and `maestro mcp`.
4. iOS Simulators require macOS with Xcode (`xcode-select -p`); Android requires ADB and Java 17+ (`java -version`). Maestro packages pinned `applesimutils` internally (unpacked to `~/.maestro/deps/applesimutils` for permissions); manual Homebrew installation is not required. Web testing requires Chrome/Chromium and supports `--headless` and `css:` locators.

## Load-bearing rules

| # | Rule | Why |
|---|---|---|
| 1 | Export explicit remote environment | Non-interactive SSH omits user profile paths; always export `JAVA_HOME="${JAVA_HOME:-/opt/homebrew/opt/java}"` and `PATH="$JAVA_HOME/bin:$HOME/.maestro/bin:/opt/homebrew/bin:$PATH"` alongside `DEVELOPER_DIR`. |
| 2 | Uniquely select target device | Parse `xcrun simctl list devices --json` or `adb devices`; require exactly one booted match or explicit caller target (or comma-separated IDs for sharded runs). |
| 3 | Coordinate exclusive host driver lease | Acquire atomic lock directory before driver operations to prevent port 22087 and XCUITest session collisions across processes. |
| 4 | Copy complete workspace | Transfer self-contained root including `config.yaml`, subflows, scripts, and referenced media; never copy only a bare flow. |
| 5 | Choose reset by runtime and session | Standalone builds may use `clearState` or `clearKeychain`; running Expo Dev Client sessions must omit launch and use deep links. |
| 6 | Hierarchy-backed selectors and state waits | Inspect `maestro hierarchy` or MCP `inspect_screen` on locator failures; note `text:` performs a full-string regex match (use `.*Text.*` for partial copy). |
| 7 | Preserve exit status and full artifacts | Transport logs, JUnit XML, screenshots, and `manifest.json` (with `startedAtEpochMs`); never convert execution failure to success. |

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
# Offline syntax check (no simulator required)
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
2. **Author and Check**: Draft declarative YAML flows; run `maestro check-syntax <flow>` to catch schema errors offline.
3. **Target and Lease**: Resolve target UDID, ADB serial, or `--platform=web`; acquire host-wide driver lease when executing remotely or in shared environments.
4. **Execute**: Run `maestro test` with `--test-output-dir` and `--format JUNIT --output <path>` (or connect via `maestro mcp`).
5. **Retrieve and Inspect**: On remote runs, fetch the full artifact directory; inspect `maestro hierarchy` or MCP `inspect_screen` if an element is missed.
6. **Release**: Release host driver lease and report binary pass/fail evidence.

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
- If remote SSH transport succeeds but the test exits non-zero, report test failure and preserve retrieved logs.
