# Test Suites, Tags, and CI/CD Automation

Structuring mobile and web test suites cleanly enables modular test reuse, targeted tag filtering, parallel sharding, and deterministic reporting in continuous integration pipelines.

---

## Modular Workspace Layout

Maintain a predictable workspace structure so that relative subflow and script references resolve portably across local workstations and CI runner environments:

```text
.maestro/
├── config.yaml           # Global workspace configuration
├── flows/                # Top-level entry flows (smoke, regression)
│   ├── 01-onboarding.yaml
│   ├── 02-login.yaml
│   └── 03-checkout.yaml
├── subflows/             # Reusable step sequences
│   ├── auth-setup.yaml
│   └── dismiss-dialogs.yaml
└── scripts/              # Synchronous GraalJS data helpers
    └── generate-user.js
```

### Workspace Configuration (`config.yaml`)

Define shared workspace settings, execution order, animation toggles, and lifecycle hooks:

```yaml
# .maestro/config.yaml
flows:
  - "flows/*.yaml"
includeTags:
  - "smoke"
excludeTags:
  - "flaky"
executionOrder:
  continueOnFailure: false      # Stops workspace run immediately on first failure
  flowsOrder:                   # Explicit sequence of execution
    - "flows/01-onboarding.yaml"
    - "flows/02-login.yaml"
    - "flows/03-checkout.yaml"
platform:
  ios:
    disableAnimations: true     # Disables UIView/CALayer animations in runner
    snapshotKeyHonorModalViews: true
  android:
    disableAnimations: true     # Disables window and transition animations via ADB
disableRetries: false
testOutputDir: "artifacts"
```

---

## Tag-Based Test Filtering

Tag flows to control execution subsets across different CI pipelines (e.g. quick pull-request smoke checks vs. nightly regression sweeps):

```yaml
# flows/01-onboarding.yaml
appId: com.example.demo
tags:
  - smoke
  - onboarding
  - pr-gate
---
- launchApp
- assertVisible: "Welcome"
```

### Running Tagged Subsets

```bash
# Run only flows tagged 'smoke'
maestro test --include-tags smoke .maestro/flows/

# Exclude work-in-progress or known flaky tests
maestro test --exclude-tags wip,flaky .maestro/flows/

# Combine multiple include tags
maestro test --include-tags smoke,checkout .maestro/flows/
```

---

## Reusable Subflows with Parameter Passing

Extract repeated sequences (such as logging in or navigating to a specific tab) into `subflows/`. Pass runtime context via `env`:

```yaml
# Main flow: flows/03-checkout.yaml
appId: com.example.demo
---
# Invoke reusable login subflow with specific credentials
- runFlow:
    file: ../subflows/auth-setup.yaml
    env:
      USER_EMAIL: "buyer@example.com"
      ROLE: "premium"

- tapOn:
    id: "cart_tab"
- assertVisible: "Shopping Cart"
```

In `subflows/auth-setup.yaml`:

```yaml
appId: com.example.demo
---
- tapOn:
    id: "email_input"
- inputText: ${USER_EMAIL}
- tapOn:
    id: "login_button"
- assertVisible: "Dashboard"
```

---

## CI Pipeline Integration and Gate Verification

In CI environments, run Maestro with explicit output directories, JUnit report formatting, and flattened output:

```bash
mkdir -p test-results

# Execute test suite with JUnit output and flattened artifact structure
maestro test .maestro/flows/ \
  --test-output-dir test-results/telemetry \
  --flatten-debug-output \
  --test-suite-name "PR Regression Suite" \
  --format JUNIT \
  --output test-results/junit.xml \
  --include-tags pr-gate
```

### Key CI Flags

- `--flatten-debug-output`: Places execution artifacts flat into `--test-output-dir` without timestamped subdirectories, making CI artifact collector patterns simple and predictable.
- `--test-suite-name=<name>`: Customizes the root `<testsuite name="...">` attribute in JUnit XML for clean test dashboard categorization.
- `--analyze`: *(Beta)* Enhances test output analysis with AI-powered failure insights.

### CI Assertion Checks

Ensure your CI workflow validates both the exit code and generated reports:

```bash
# Verify non-empty JUnit report
test -s test-results/junit.xml

# Check for failure indications in JUnit XML
if grep -q '<failure' test-results/junit.xml; then
  echo "Test failures detected in JUnit report"
  exit 1
fi
```

Always upload `test-results/telemetry` as a CI build artifact so failed runs preserve screenshots, screen recordings, and driver console logs (`manifest.json`, `commands.json`, `logs/maestro.log`) for rapid triage.

---

## Parallel Execution and Device Sharding

Maestro 2.x supports two distinct multi-device sharding strategies:

| Strategy | Flag | Behavior | Use Case |
|---|---|---|---|
| **Redundant Suite Run** | `--shard-all=<N>` | Executes the **entire test suite** redundantly across N devices simultaneously | Matrix testing across device models or OS versions |
| **Partitioned Suite Run** | `--shard-split=<N>` | Partitions the test suite **evenly across N devices** for 1/N runtime | Accelerating long CI regression suites |

> **Critical Rule**: `--shard-all` and `--shard-split` are **mutually exclusive**. Providing both flags causes an immediate failure: `CliError: Options --shard-split and --shard-all are mutually exclusive.`

### Multi-Device Targeting Syntax
Specify targets using a comma-separated list of device identifiers:
```bash
# Split suite across two booted emulators
maestro test \
  --device "emulator-5554,emulator-5556" \
  --shard-split 2 \
  .maestro/flows/
```

### Device Concurrency & Exclusive Driver Leases
- Within a single Maestro process, Maestro manages separate device driver sessions and dynamic ephemeral ports (`SIMCTL_CHILD_PORT`).
- **Across separate OS processes** (e.g. concurrent CI jobs on the same macOS host), XCUITest runners cannot share the same simulator UDID simultaneously. Use an atomic filesystem lease to prevent port 22087 and session collisions.

---

## Bounded Retries for Network Glitches

Use Maestro's built-in `retry` block to isolate individual steps vulnerable to transient backend latency, avoiding whole-suite re-runs:

```yaml
# Bounded retry on transient network operation (max 3 attempts)
- retry:
    maxRetries: 2
    commands:
      - tapOn: "Refresh Feed"
      - assertVisible: "Latest News"
```

---

## Related References

- [CLI and Artifacts](../commands/cli-and-artifacts.md) — Command flags and telemetry file outputs.
- [Flows and Selectors](../commands/flows-and-selectors.md) — Subflow composition and parameter syntax.
- [iOS over SSH](../guides/ios-over-ssh.md) — Remote CI execution over SSH.
- [Android and Local iOS](../guides/android-and-local-ios.md) — Device discovery and toolchains.
