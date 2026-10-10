# Test Suites, Tags, and CI/CD Automation

Structuring suites cleanly enables modular reuse, tag filtering, sharding, and deterministic reporting in CI. Facts verified against Maestro `2.11.0` source and `docs.maestro.dev`.

---

## Modular Workspace Layout

Maestro finds `config.yaml` (or `config.yml`) **only in the directory you pass to `maestro test`**, and the default `flows` glob is `*` (top-level files of that directory only). The layout below therefore sets `flows:` explicitly and is run as `maestro test .maestro`:

```text
.maestro/
├── config.yaml           # read because you run `maestro test .maestro`
├── flows/                # entry flows (smoke, regression)
│   ├── 01-onboarding.yaml
│   └── 02-login.yaml
├── subflows/             # reusable step sequences (NOT run as tests)
│   ├── auth-setup.yaml
│   └── dismiss-dialogs.yaml
└── scripts/              # synchronous GraalJS helpers
    └── generate-user.js
```

Running `maestro test .maestro/flows/` ignores `.maestro/config.yaml` (and silently drops `includeTags`, `executionOrder`, `testOutputDir`, `platform.*`) unless you add `--config .maestro/config.yaml`. Running `maestro test .maestro` without a `flows:` key fails with `Top-level directories do not contain any Flows`.

### Workspace Configuration (`config.yaml`)

```yaml
# .maestro/config.yaml
flows:
  - "flows/*"
  - "!flows/wip-*"              # negation globs since 2.9.0; need at least one positive glob
includeTags:
  - smoke
excludeTags:
  - flaky
executionOrder:
  continueOnFailure: false      # applies only to the flowsOrder sequence, not the whole workspace
  flowsOrder:                   # flow `name:` header, or file name without extension
    - 01-onboarding
    - 02-login
platform:
  ios:
    disableAnimations: true     # Cloud only
    snapshotKeyHonorModalViews: true
  android:
    disableAnimations: true     # Cloud only
testOutputDir: "artifacts"
```

Other workspace keys: `notifications` (email/Slack) and `baselineBranch`. `disableRetries` is deprecated (Cloud uses Smart Retries) and absent from the documented reference.

**Sharding vs `executionOrder`**: a workspace with `executionOrder` cannot be sharded; the run aborts with `Cannot run sharded tests with sequential execution`.

---

## Tag-Based Filtering

Tag flows in their headers (`tags:`); filter with `--include-tags` / `--exclude-tags` or the config keys `includeTags` / `excludeTags` (tags are not a config key).

```bash
maestro test --include-tags smoke .maestro/        # flows tagged smoke
maestro test --exclude-tags wip,flaky .maestro/
maestro test --include-tags smoke,checkout .maestro/   # smoke OR checkout
```

Semantics from source: a comma list is **OR** (there is no AND), and CLI tags are **concatenated** with config tags, not overriding them. With config `includeTags: [smoke]` plus `--include-tags pr-gate`, flows tagged `pr-gate` **or** `smoke` run. The docs claim CLI flags "always take precedence"; the source does not behave that way.

Quarantine pattern: tag unstable flows `flaky`, put `flaky` in `excludeTags` for the gating job, and run them in a separate non-blocking job.

---

## Ready-Made Test Flow Templates

Subflows need their own header (`appId` plus `---`); without it `runFlow` fails with `Config Section Required` even though `check-syntax` passes.

### 1. Authentication and Session Reset (`subflows/auth-setup.yaml`)
```yaml
appId: com.example.demo
---
- launchApp:
    clearState: true
    clearKeychain: true            # iOS: clears the whole simulator keychain
- assertVisible: "Welcome"
- tapOn:
    id: "login_button"
- tapOn:
    id: "email_input"
- inputText: ${USER_EMAIL}        # pass from the caller via runFlow.env or -e; do not hardcode
- tapOn:
    id: "password_input"
- inputText: ${USER_PASS}
- hideKeyboard:
    optional: true
- tapOn: "Sign In"
- assertVisible: "Dashboard"
```
Caller: `- runFlow: { file: ../subflows/auth-setup.yaml, env: { USER_EMAIL: ${TEST_EMAIL}, USER_PASS: ${TEST_PASS} } }` with `TEST_EMAIL`/`TEST_PASS` supplied as `-e` or CI secrets.

### 2. Form Entry with Synthetic Data (`flows/profile-update.yaml`)
```yaml
appId: com.example.demo
tags:
  - regression
  - profile
---
- tapOn:
    id: "profile_settings"
- tapOn:
    id: "edit_name"
- eraseText
- inputRandomPersonName
- tapOn:
    id: "edit_email"
- eraseText
- inputRandomEmail
- tapOn:
    id: "save_changes"
- assertVisible: "Profile updated successfully"
```

### 3. Visual Regression (`flows/checkout-visual.yaml`)
```yaml
appId: com.example.demo
tags:
  - visual
---
- openLink: "exampleapp://checkout?orderId=1042"
- waitForAnimationToEnd:
    timeout: 3000
- assertScreenshot:                # numeric similarity %, default 95
    path: baselines/checkout_screen
    thresholdPercentage: 98
```
AI checks (`assertNoDefectsWithAI`, `assertWithAI`) need a Maestro Cloud login and **default to `optional: true`**, meaning they never fail CI unless you set `optional: false`.

---

## Continuous Test Creation with AI Agents

Grow the suite from interactive exploration through Maestro MCP (`maestro mcp`):

```text
boot device ─▶ list_devices (connected:true) ─▶ inspect_screen
      │                                              │
      ▼                                              ▼
run inline YAML (one step or a short chain) ─▶ verify via inspect_screen / take_screenshot
      │
      ▼
append passing steps to .maestro/flows/<flow>.yaml (appId header + `---`)
      │
      ▼
extract repeated step sequences into .maestro/subflows/ ─▶ tag ─▶ run `maestro test .maestro` in CI
```

---

## CI Pipeline Integration and Gate Verification

Reports (`--output`, default `report.xml`) are written **outside** `--test-output-dir`, so upload both:

```bash
mkdir -p test-results
maestro test .maestro \
  --test-output-dir test-results/telemetry \
  --test-suite-name "PR Regression Suite" \
  --format JUNIT \
  --output test-results/junit.xml \
  --include-tags pr-gate
```

### Key CI Flags
- `--flatten-debug-output`: **ignores `--test-output-dir`**; output goes to `--debug-output` or, if omitted, to `$HOME`. Use it only together with `--debug-output=<dir>` (Maestro's own e2e does).
- `--test-suite-name`: sets `<testsuite name>` in JUnit XML (default `Test Suite`).
- `--analyze`: Insights report with AI analysis; requires Maestro Cloud login.
- Environment: `MAESTRO_CLOUD_API_KEY`, `MAESTRO_CLI_NO_ANALYTICS`, `MAESTRO_DISABLE_UPDATE_CHECK`.

### CI Assertion Checks
```bash
test -s test-results/junit.xml
grep -q '<failure' test-results/junit.xml && { echo "failures in JUnit"; exit 1; }
```
Never swallow the `maestro` exit code. Upload `test-results/` as a build artifact. A normal run captures only the failing step's screenshot; screen recordings exist only with `startRecording` or `--analyze`.

---

## GitHub Actions Skeletons

### Android on a Linux runner (KVM)
```yaml
jobs:
  e2e-android:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with: { distribution: temurin, java-version: '17' }
      - name: Enable KVM
        run: |
          echo 'KERNEL=="kvm", GROUP="kvm", MODE="0666", OPTIONS+="static_node=kvm"' | sudo tee /etc/udev/rules.d/99-kvm4all.rules
          sudo udevadm control --reload-rules && sudo udevadm trigger --name-match=kvm
      - run: curl -fsSL "https://get.maestro.mobile.dev" | bash && echo "$HOME/.maestro/bin" >> "$GITHUB_PATH"
      - uses: reactivecircus/android-emulator-runner@v2
        with:
          api-level: 34
          arch: x86_64
          script: maestro test .maestro --format JUNIT --output report.xml --test-output-dir test-results
```

### iOS from a Linux pipeline: Maestro Cloud
```bash
# simulator .app (zipped) must come from a Mac or cloud builder
export MAESTRO_CLOUD_API_KEY=...        # CI secret
maestro cloud --app-file build/DemoApp.zip --flows .maestro/flows
```
A blocking `maestro cloud` returns `0` on success and `1` if any flow fails. With `--async` (or the GitHub Action's `async: true`) it returns immediately and does **not** fail on test failures, so exit code `0` then proves nothing.

---

## Parallel Execution and Device Sharding

| Strategy | Flag | Behavior | Use Case |
|---|---|---|---|
| Redundant run | `--shard-all=<N>` | Entire suite on N devices | Device/OS matrix, flake detection |
| Partitioned run | `--shard-split=<N>` | Suite split across N devices | Faster regression runs |

- The two flags are mutually exclusive (`Options --shard-split and --shard-all are mutually exclusive.`).
- N devices must already be connected, otherwise `Not enough devices connected`. Pass them with `--device "id1,id2"`.
- Not compatible with `executionOrder`; `--shards` is deprecated.
- Shards share the workspace, so put `${MAESTRO_SHARD_INDEX}` or `${MAESTRO_DEVICE_UDID}` in screenshot names to avoid collisions.
- On Maestro Cloud, parallelism is managed for you; sharding flags are for local runners.

```bash
maestro test --device "emulator-5554,emulator-5556" --shard-split 2 .maestro
```

### Concurrency on One Host
Each `maestro test` run on iOS picks its own free driver port, so the collision risk is two processes driving the **same simulator** (reinstalling the driver kills the other run's runner), not port `22087`. Give each CI job its own simulator, or serialize with a host lock (see [iOS over SSH](../guides/ios-over-ssh.md)).

---

## Bounded Retries and Flaky Handling

`retry` is capped at 3 (`maxRetries: 2` means up to 3 attempts) and only retries Maestro command failures. It hides real flakiness; prefer fixing selectors and waits. Maestro Cloud has Smart Retries and a 20-minute soft limit per flow. The CLI has no "rerun failed flows" flag.

```yaml
- retry:
    maxRetries: 2
    commands:
      - tapOn: "Refresh Feed"
      - assertVisible: "Latest News"
```

---

## Related References

- [CLI and Artifacts](../commands/cli-and-artifacts.md) — Command flags and artifact layout.
- [Flows and Selectors](../commands/flows-and-selectors.md) — Subflow composition and parameter syntax.
- [iOS over SSH](../guides/ios-over-ssh.md) — iOS from Linux hosts.
- [Android and Local iOS](../guides/android-and-local-ios.md) — Device discovery, toolchains, and Linux emulators.
