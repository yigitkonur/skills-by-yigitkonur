# Test Suites, Tags, and CI/CD Automation

Structuring mobile test suites cleanly enables modular test reuse, targeted tag filtering, and deterministic reporting in continuous integration pipelines.

## Modular Workspace Layout

Maintain a predictable workspace structure so that relative subflow and script references resolve portably across local and CI runner environments:

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

Define shared workspace settings and lifecycle hooks:

```yaml
# .maestro/config.yaml
appId: com.example.demo
env:
  ENVIRONMENT: "staging"
  BASE_URL: "https://staging.example.com"
```

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

## CI Pipeline Integration and Gate Verification

In CI environments, run Maestro with explicit output directories and JUnit report formatting:

```bash
mkdir -p test-results

# Execute test suite with JUnit output
maestro test .maestro/flows/ \
  --test-output-dir test-results/telemetry \
  --format JUNIT \
  --output test-results/junit.xml \
  --include-tags pr-gate
```

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

Always upload `test-results/telemetry` as a CI build artifact so failed runs include screenshots and driver console logs for rapid triage.

## Serial Device Scheduling and Concurrency

Maestro connects to native drivers (ADB on Android, XCUITest on iOS) that bind to exclusive device endpoints:
- **Do not run parallel Maestro processes against the same simulator or emulator.** Port 22087 and system driver sessions will collide.
- For parallel test execution, shard tests across distinct devices using `--shard-all` or distinct runner machines, coordinating device access with explicit leases.

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

## Related References

- [CLI and Artifacts](../commands/cli-and-artifacts.md) — Command flags and telemetry file outputs.
- [Flows and Selectors](../commands/flows-and-selectors.md) — Subflow composition and parameter syntax.
- [iOS over SSH](../guides/ios-over-ssh.md) — Remote CI execution over SSH.
