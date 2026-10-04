---
name: test-by-maestro
description: "Use if writing, running, or debugging Maestro mobile E2E tests on iOS Simulators or Android."
---

# Test Mobile UI with Maestro

Author, validate, execute, and diagnose mobile E2E tests with Maestro across iOS Simulators and Android emulators or devices. This skill owns declarative YAML test flow authoring, offline syntax verification, local and remote execution over SSH, artifact retrieval, and failure diagnosis. It does not own building the application binary, managing cloud provider accounts, or configuring backend test fixtures.

## When to use this skill

- Writing declarative Maestro YAML flows for iOS Simulators or Android devices
- Running mobile UI test suites locally or from a Linux authoring host over SSH to a macOS simulator host
- Debugging failing tests, broken element selectors, or accessibility tree mismatches
- Verifying workspace syntax and modular subflow references offline without touching a physical device
- Collecting and interpreting test artifacts including JUnit XML reports, console logs, and failure screenshots

## Do NOT use this skill when

- Writing unit or component tests (e.g., Jest or Vitest for React Native components)
- Testing desktop web applications without a mobile app under test (use `ego-browser`)
- Building, compiling, or refactoring application source code
- Automating physical iOS devices locally (Maestro CLI only supports local iOS Simulators)
- Testing MCP server protocols or tools directly (use `test-by-mcpc-cli`)

## Source of truth

1. Confirm installed CLI: run `maestro --version` (install if missing: `curl -fsSL "https://get.maestro.mobile.dev" | bash`). Tested baseline is `2.11.0`.
2. Inspect scoped command options with `maestro --help`, `maestro test --help`, and `maestro hierarchy --help`. Note that `check-syntax` takes only `<file>` or `-` without `--help`.
3. iOS Simulators require macOS with Xcode (`xcode-select -p`); Android requires ADB and Java 17+ (`java -version`). Modern Maestro uses bundled XCUITest runners and `applesimutils`; `idb` is completely deprecated.

## Load-bearing rules

| # | Rule | Why |
|---|---|---|
| 1 | Export explicit remote environment | Non-interactive SSH omits user profile paths; always export `PATH="$HOME/.maestro/bin:/opt/homebrew/bin:$PATH"` and `DEVELOPER_DIR`. |
| 2 | Uniquely select target device | Parse `xcrun simctl list devices --json` or `adb devices`; require exactly one booted match or explicit caller target. |
| 3 | Coordinate exclusive host driver lease | Acquire atomic lock directory before driver operations to prevent port 22087 and XCUITest session collisions. |
| 4 | Copy complete workspace | Transfer self-contained root including `config.yaml`, subflows, scripts, and referenced media; never copy only a bare flow. |
| 5 | Choose reset by runtime and session | Standalone builds may use `clearState` or `clearKeychain`; running Expo Dev Client sessions must omit launch and use deep links. |
| 6 | Hierarchy-backed selectors and state waits | Inspect `maestro hierarchy` on locator failures; prefer accessibility IDs and relational anchors over fragile coordinates. |
| 7 | Preserve exit status and full artifacts | Transport logs, JUnit XML, and screenshots via unique output directories; never convert execution failure to success. |

## Minimal read sets

Choose the route matching your task; read only the relevant leaves before acting:

| Task Intent | Read First |
|---|---|
| CLI syntax, flags, report paths, or view hierarchy | [CLI and Artifacts](references/commands/cli-and-artifacts.md) |
| Authoring flow YAML, commands, and selector strategies | [Flows and Selectors](references/commands/flows-and-selectors.md) |
| Linux authoring host running tests on remote macOS via SSH | [iOS over SSH](references/guides/ios-over-ssh.md) |
| Local Android emulator/device or local macOS iOS Simulator | [Android and Local iOS](references/guides/android-and-local-ios.md) |
| JavaScript scripting, HTTP helpers, and dynamic test data | [GraalJS Scripting](references/guides/graaljs.md) |
| Element visibility, keyboard races, animations, or scrolling | [Mobile Flakiness](references/troubleshooting/mobile-flakiness.md) |
| Expo Dev Client continuity, Keychain tokens, or auth resets | [Expo and State](references/troubleshooting/expo-and-state.md) |
| Subflows, tags, CI pipeline integration, and report gates | [Suites and CI](references/patterns/suites-and-ci.md) |

## Quick start

For an existing installed application on a local simulator or emulator:

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

1. **Preflight**: Verify `maestro --version` and target runtime availability.
2. **Author and Check**: Draft declarative YAML flows; run `maestro check-syntax <flow>` to catch schema errors offline.
3. **Target and Lease**: Resolve target UDID or ADB serial; acquire host-wide driver lease when executing remotely or in shared environments.
4. **Execute**: Run `maestro test` with `--test-output-dir` and `--format JUNIT --output <path>` to capture complete telemetry.
5. **Retrieve and Inspect**: On remote runs, fetch the full artifact directory; inspect `maestro hierarchy` if an element is missed.
6. **Release**: Release host driver lease and report binary pass/fail evidence.

## Output contract

Every test execution report must specify:
- Target host, platform, and resolved device ID/name
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
