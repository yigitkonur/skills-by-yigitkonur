---
name: test-by-maestro
description: "Use if writing, running, or debugging Maestro E2E test flows on iOS Simulators, Android, or Web, including MCP agent automation and CI suites."
disable-model-invocation: true
---

# Test Mobile and Web UI with Maestro

Author, validate, execute, and diagnose E2E tests with Maestro across iOS Simulators (macOS host or Maestro Cloud), Android emulators or physical devices (Linux, macOS, Windows), and Web (Chromium, Beta). This skill owns declarative YAML flow authoring, single interactive actions through Maestro's MCP server, offline syntax checks, local and cloud/SSH execution, artifact retrieval, failure diagnosis, and growing a reusable suite over time. It does not own building the app binary, Maestro Cloud billing, or backend test fixtures.

Facts here were verified against the Maestro `2.11.0` source (latest release, 2026-09-29) and `docs.maestro.dev`. If `maestro --version` differs, re-check the version-sensitive rules.

## When to use this skill

- Writing Maestro YAML flows for iOS Simulators, Android emulators/devices, or Web
- Driving a live device one clean action at a time through the Maestro MCP server (`maestro mcp`) from Claude Code, Cursor, Codex, or Gemini CLI
- Choosing where tests can run: Linux (Android and Web locally; iOS only via Maestro Cloud or a Mac) versus macOS (everything)
- Building reusable subflows, hooks, tags, and suites, and promoting exploratory steps into permanent tests
- Debugging failing selectors with `maestro hierarchy` or MCP `inspect_screen`
- Validating flow syntax offline with `maestro check-syntax` (or automatically inside MCP `run`)
- Collecting and reading JUnit reports, logs, and failure screenshots

## Do NOT use this skill when

- Writing unit or component tests (Jest, Vitest)
- Exploratory web browsing with no regression flow needed (use `run-agent-browser`)
- Building or refactoring app source code
- Automating **physical iPhones**: Maestro 2.11.0 fails fast with `Physical iOS devices are not yet supported`
- Testing a third-party MCP server (use `test-by-mcpc-cli`); this skill drives Maestro's own `maestro mcp` server

## Source of truth

1. **CLI**: run `maestro --version`. Install if missing: `curl -fsSL "https://get.maestro.mobile.dev" | bash` (needs `java`, `unzip`, `curl`). Latest is `2.11.0`. Java 17+ is required (17 or 21 recommended); `$JAVA_HOME` is optional because the launcher falls back to `java` on `PATH`.
2. **Help**: `maestro --help`, `maestro test --help`, `maestro cloud --help`, `maestro hierarchy --help`, `maestro start-device --help`, `maestro list-devices --help`. `maestro check-syntax` takes only `<file>` or `-`; `maestro mcp` takes `--no-viewer`, `--viewer-port=<port>`, `--working-dir=<dir>` and has no `--help`.
3. **Studio**: since 2.6.0 Maestro Studio is a separate desktop app (`maestro studio` only prints a download URL). Terminal inspection uses `maestro hierarchy` (JSON, or `--compact` CSV); agents use MCP `inspect_screen`; `maestro test -c` re-runs one flow on save.
4. **Docs**: `https://docs.maestro.dev/llms.txt` is the docs index and every docs page has a `.md` variant. MCP: `https://maestro.dev/mcp`.

## Where can this run? (decision table)

| Need | Linux host | macOS host | Maestro Cloud |
|---|---|---|---|
| Android emulator / device | Yes (KVM + x86_64 image, headless) | Yes | Yes (APK with `arm64-v8a`) |
| Web (Chromium, Beta) | Yes | Yes | n/a |
| iOS Simulator | **No** | Yes (full Xcode) | Yes (simulator `.app`, zipped) |
| Physical iPhone | No | No (2.11.0) | No |

iOS needed while authoring on Linux:
1. **Maestro Cloud**: `maestro cloud --app-file app.zip --flows .maestro/flows` (or MCP `run_on_cloud`). Needs a Cloud plan/trial plus `maestro login` or `MAESTRO_CLOUD_API_KEY`. The simulator `.app` must be built on a Mac or a cloud builder; `.ipa` and device builds are rejected.
2. **A Mac you control** (owned Mac, GitHub `macos-*` runner, EC2 Mac): run the Maestro CLI there, typically over SSH. This SSH recipe is this skill's own construction, not a documented Maestro mode.
3. Otherwise run only the Android and Web parts and say iOS was not covered.

Read [iOS over SSH](references/guides/ios-over-ssh.md) for the route details and [Android and Local iOS](references/guides/android-and-local-ios.md) for the Linux headless emulator setup.

## Load-bearing rules

| # | Rule | Why |
|---|---|---|
| 1 | Single actions go through MCP `run` with inline YAML | Since 2.5.0 the granular tools (`tap_on`, `input_text`, ...) are gone; `run` takes `{ "device_id": "...", "yaml": "- tapOn: \"Log In\"" }` and validates syntax first. |
| 2 | Boot the device before any MCP call | No MCP tool boots a device. `list_devices` also lists launchable devices; use only entries with `connected: true`. |
| 3 | Never plan local iOS on Linux | iOS Simulators need macOS + Xcode (`xcrun simctl`, `xcodebuild`). Route to Maestro Cloud or a Mac. |
| 4 | Export the toolchain explicitly in non-interactive shells | SSH, agent shells, and MCP clients skip profile files. Set `JAVA_HOME` to a 17+ JDK and put `~/.maestro/bin` on `PATH`. On a Mac also check `xcode-select -p` points at full Xcode. |
| 5 | Always pass `--device <id>` when more than one device is attached | `maestro test` silently uses the first connected device; `maestro hierarchy` errors with `Multiple devices connected`. Get ids from `adb devices` or `xcrun simctl list devices booted --json`. |
| 6 | Every flow file, including subflows, starts with an `appId:` (or `url:`) header and `---` | `runFlow` rejects a file without it (`Config Section Required`), yet `maestro check-syntax` passes it, so a green syntax check is not proof for subflows. |
| 7 | Parameterize subflows with `runFlow.env` | `env` bindings are scoped per `runFlow`/`runScript`, but the JS `output` object is global across the whole flow. Namespace `output` keys. A plain header `env:` value beats `-e`; write `KEY: ${KEY \|\| "default"}` to allow overrides. |
| 8 | Hierarchy-backed selectors | Inspect `maestro hierarchy` or `inspect_screen` first. `text:` is a full-string, case-insensitive regex (`.*Log In.*` for partial copy). Never put `start:`/`end:` in element selectors (rejected since 2.11.0). |
| 9 | Pick the reset strategy by build type | Standalone/EAS builds: `launchApp` with `clearState`/`clearKeychain` (iOS; this wipes the whole simulator keychain). Expo Go cannot use `launchApp` with a custom `appId`; Expo Dev Client builds launch normally and then need the dev server entered (see [Expo and State](references/troubleshooting/expo-and-state.md)). |
| 10 | Preserve exit status and the full artifact tree | Keep both `--test-output-dir` and the report (`--output`, default `report.xml` in the cwd). Never convert a test failure into success. |

## Interactive Agent Automation via MCP (`maestro mcp`)

Maestro embeds an MCP server over STDIO exposing 10 tools: `list_devices`, `inspect_screen`, `take_screenshot`, `run`, `cheat_sheet`, `open_maestro_viewer`, `list_cloud_devices`, `run_on_cloud`, `get_cloud_run_status`, `describe_cloud_run`. Exact parameters are in [CLI and Artifacts](references/commands/cli-and-artifacts.md).

### Agent setup (`https://maestro.dev/mcp`)

- **Claude Code**: `claude mcp add maestro -- maestro mcp`
- **Codex CLI**: `codex mcp add maestro -- maestro mcp`
- **Gemini CLI**: `gemini mcp add -s user maestro maestro mcp` (default scope is `project`, which writes `.gemini/settings.json` in the cwd)
- **Cursor**: `~/.cursor/mcp.json` or `.cursor/mcp.json`:
  ```json
  { "mcpServers": { "maestro": { "command": "maestro", "args": ["mcp"], "env": { "JAVA_HOME": "/path/to/java17+" } } } }
  ```
- Antigravity (`~/.gemini/config/mcp_config.json`) and Windsurf (`~/.config/devin/mcp_config.json`) use their own config files; see the reference.
- Add `"--working-dir", "<repo>"` to `args` so relative `files`/`dir` arguments resolve against the repository.

### Taking individual actions cleanly

1. **Boot and identify**: start the emulator/simulator yourself, then call `list_devices` and take a `device_id` with `connected: true` (e.g. `emulator-5554`, a simulator UDID, or `chromium`).
2. **Look first**: call `inspect_screen` (compact `ui_schema` + `elements`). Copy `txt` into `text:` or `rid` into `id:`; `a11y` is not a selector key.
3. **Act**: call `run` with one command or a short chain. Mobile YAML should declare `appId` and start with `launchApp` when the app is not already open; a bare command list also works for steps in an open app.
   ```json
   { "device_id": "emulator-5554", "yaml": "- tapOn: \"Sign In\"" }
   ```
   ```json
   { "device_id": "emulator-5554", "yaml": "- tapOn:\n    id: \"email_input\"\n- inputText: \"user@example.com\"\n- hideKeyboard\n- tapOn: \"Continue\"" }
   ```
   The result is JSON (`success`, `commands_executed`); `isError` means the step failed.
4. **Verify**: `inspect_screen` again, or `take_screenshot` (JPEG, max 2000 px).
5. **Watch live (optional)**: `open_maestro_viewer` returns a local viewer URL. Give it to the user; do not open a browser yourself.
6. **Promote**: when a step sequence passes, append it to a flow file (see "Growing a reusable suite"). Prefer one full flow over many single-command calls once the steps are known.
7. Call `cheat_sheet` before using an unfamiliar command.

## Cross-Platform Execution Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Host Machine (Agent / CI)                            │
└──────────────────────────────────────┬──────────────────────────────────────┘
            ┌──────────────────────────┴──────────────────────────┐
            ▼                                                     ▼
    [macOS Workstation]                                     [Linux Host]
    • Android emulators / devices (ADB)                     • Android emulators (KVM, headless) / devices
    • iOS Simulators (full Xcode)                           • Web (Chromium)
    • Web (Chromium)                                        ───────────────────────────────
                                                            iOS Simulators CANNOT run here:
                                                            1. Maestro Cloud:
                                                               maestro cloud --app-file app.zip --flows .maestro/flows
                                                            2. A Mac you control (e.g. over SSH):
                                                               run the Maestro CLI there
```

## Authoring Reusable and Ready-Made Tests

Maestro reads `config.yaml` only from the directory you pass to `maestro test`, and its default `flows` glob is top-level only. Run the whole workspace as `maestro test .maestro` and list the flows explicitly:

```text
.maestro/
├── config.yaml               # flows glob, includeTags/excludeTags, executionOrder
├── flows/                    # entry flows (each is a test)
│   ├── 01-auth-smoke.yaml
│   └── 02-checkout.yaml
├── subflows/                 # reusable blocks (not run directly)
│   ├── login-user.yaml
│   └── clear-cart.yaml
└── scripts/
    └── generate-test-data.js
```

```yaml
# .maestro/config.yaml
flows:
  - "flows/*"
excludeTags:
  - flaky
```

### 1. Reusable subflow (`subflows/login-user.yaml`)
Subflows need their own header. Required inputs come from the caller; do not bake credentials into the file.

```yaml
appId: com.example.shop
env:
  USER_EMAIL: ${USER_EMAIL || "shopper@example.test"}
---
- tapOn:
    id: "login_email_input"
- inputText: ${USER_EMAIL}
- tapOn:
    id: "login_password_input"
- inputText: ${USER_PASSWORD}      # supplied with -e USER_PASSWORD=... or a CI secret
- hideKeyboard
- tapOn: "Sign In"
- assertVisible: "Dashboard"
```

### 2. Main flow with hooks (`flows/02-checkout.yaml`)
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
        USER_EMAIL: "shopper@example.test"
        USER_PASSWORD: ${USER_PASSWORD}
onFlowComplete:
  - runFlow: ../subflows/clear-cart.yaml
---
- tapOn: ${CHECKOUT_ITEM}
- tapOn: "Add to Cart"
- tapOn: "Cart"
- assertVisible: ${CHECKOUT_ITEM}
- tapOn: "Proceed to Checkout"
- assertVisible: "Order Confirmation"
- takeScreenshot: checkout_success   # saved under <flow artifact dir>/takeScreenshot/checkout_success.png
```
Run: `maestro test .maestro -e USER_PASSWORD="$USER_PASSWORD" --test-output-dir artifacts`.

### 3. Platform-conditioned steps
```yaml
- runFlow:
    when:
      platform: iOS
    commands:
      - tapOn:
          text: "Allow While Using App"
          optional: true
- runFlow:
    when:
      platform: Android
    commands:
      - tapOn:
          text: "While using the app"
          optional: true
```
Prefer pre-granting permissions with `launchApp.permissions` (`allow`/`deny` work on both platforms; `always`/`inuse`/`never` are iOS only and silently revoke on Android).

### Growing a reusable suite (continuous test creation)

1. **Explore** the next scenario through MCP: `list_devices` → `inspect_screen` → `run` one step at a time.
2. **Capture** passing steps into `flows/NN-name.yaml` with `appId`, `tags`, and `---`. Re-run the whole file with `run` (`files`) or `maestro test`.
3. **Extract** any sequence that appears in a second flow (login, onboarding, cleanup, dismiss dialogs) into `subflows/`, parameterized by `env`. Keep one concern per subflow.
4. **Tag** every flow: a gating tag (`smoke`, `pr-gate`) and a feature tag. Tags are OR-combined; there is no AND.
5. **Stabilize**: replace text selectors with `id`, add `extendedWaitUntil`/`waitForAnimationToEnd` where the hierarchy lags, and use `retry` sparingly (cap 3). Move a still-unstable flow to the `flaky` tag and exclude it from the gating run instead of retrying blindly.
6. **Lock in**: `maestro check-syntax` each file, then `maestro test .maestro` locally, then wire the same command into CI (see [Suites and CI](references/patterns/suites-and-ci.md)).
7. **Keep data synthetic**: use `inputRandom*` commands or `runScript` helpers rather than fixed personal data.

## Minimal read sets

| Task Intent | Read First |
|---|---|
| CLI flags, MCP tool parameters, artifact layout, hierarchy | [CLI and Artifacts](references/commands/cli-and-artifacts.md) |
| Flow YAML commands, selectors, platform limits | [Flows and Selectors](references/commands/flows-and-selectors.md) |
| iOS from a Linux authoring host (Cloud or a Mac over SSH) | [iOS over SSH](references/guides/ios-over-ssh.md) |
| Android emulators, Linux headless setup, local iOS Simulator, Web | [Android and Local iOS](references/guides/android-and-local-ios.md) |
| JavaScript, HTTP helper, dynamic test data | [GraalJS Scripting](references/guides/graaljs.md) |
| Missing elements, keyboard races, animations, scrolling | [Mobile Flakiness](references/troubleshooting/mobile-flakiness.md) |
| Expo Dev Client, Keychain tokens, auth resets | [Expo and State](references/troubleshooting/expo-and-state.md) |
| Tags, config.yaml, sharding, GitHub Actions, report gates | [Suites and CI](references/patterns/suites-and-ci.md) |

## Quick start

```yaml
# .maestro/smoke.yaml
appId: com.example.demo
---
- launchApp:
    clearState: true
- assertVisible: "Welcome"
- tapOn:
    id: "email_input"
- inputText: "user@example.com"
- hideKeyboard
- tapOn: "Continue"
- assertVisible: "Dashboard"
- takeScreenshot: dashboard_loaded
```

```bash
maestro check-syntax .maestro/smoke.yaml

mkdir -p artifacts
maestro --device "$DEVICE_ID" test .maestro/smoke.yaml \
  --test-output-dir artifacts \
  --format JUNIT \
  --output artifacts/report.xml
```

Exit code 0 means every step passed. Artifacts: `artifacts/<timestamp>/<flow>/` holds `manifest.json` (artifact index), `commands.json`, logs, the failing-step screenshot, and `takeScreenshot/` output; the JUnit report is at `artifacts/report.xml`.

## Standard workflow

1. **Preflight**: `maestro --version`, `java -version`, and the runtime (`adb devices`, `xcrun simctl list devices booted --json`, or `--platform=web`).
2. **Boot and target**: start the emulator/simulator (headless on Linux) and record its id; pass `--device <id>` when more than one is attached.
3. **Explore** (optional): MCP `list_devices` → `inspect_screen` → `run`.
4. **Author and check**: write the flow with headers on every file; `maestro check-syntax <flow>` (MCP `run` validates automatically).
5. **Execute**: `maestro test` with `--test-output-dir` and `--format JUNIT --output <path>`; on Linux with iOS needed, `maestro cloud` or the Mac route.
6. **Diagnose**: on a missed element use `maestro hierarchy` or `inspect_screen`; read `commands.json` and the failing screenshot.
7. **Report**: binary pass/fail with evidence; retain artifacts.

## Output contract

Every test execution report states:
- Host OS, target platform (`android`, `ios`, `web`), and resolved device id/name
- Maestro CLI version
- Flow scope (files, tags) and state reset policy
- Exit status and JUnit pass/fail summary
- Path to artifacts and the report file
- Diagnostic classification for any failure (selector, timing, state, environment)
- What was **not** covered (e.g. iOS skipped on Linux)

## Guardrails and recovery

- Never run two processes against the same iOS Simulator; Maestro reinstalls its driver on every run by default and kills the other run's runner. Serialize or use separate simulators.
- Do not reboot devices, wipe simulator runtimes, or delete AVDs automatically on a test failure.
- Never hardcode secrets, personal data, or UDIDs in flow files; pass them with `-e` or CI secrets.
- A blocking `maestro cloud` exits non-zero on failed flows; with `--async` it exits `0` immediately, so poll `get_cloud_run_status` before claiming success.
- If SSH or Cloud transport succeeds but the test exits non-zero, report the test failure and keep the logs.
- AI commands (`assertWithAI`, `assertNoDefectsWithAI`, `extractTextWithAI`) are experimental, need a Maestro Cloud login, and default to `optional: true` (they do not fail the run) unless set to `optional: false`.
