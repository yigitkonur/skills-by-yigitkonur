# CLI Flags, Artifacts, and Hierarchy Inspection

Maestro CLI provides declarative test execution, offline syntax validation, view hierarchy inspection, and test telemetry reporting across iOS Simulators and Android devices.

## CLI Verification and Scope

Verify the installed binary and runtime baseline:

```bash
# Install Maestro CLI if missing
curl -fsSL "https://get.maestro.mobile.dev" | bash

maestro --version
# Tested baseline: 2.11.0
```

Inspect command help and available options:

```bash
maestro --help
maestro test --help
maestro hierarchy --help
```

Note: `maestro check-syntax` does not accept `--help` or `-h`; it strictly takes `<file>` or `-` for stdin.

### Command and Flag Scope

Maestro accepts platform and device targeting flags at both the global CLI level and the `test` command level:

- `--udid=<deviceId>` or `--device=<deviceId>`: Specifies the target iOS Simulator UDID or Android ADB serial. When omitted, Maestro connects to the single booted or connected device.
- `-p, --platform=<platform>`: Filters target devices (`ios`, `android`).
- `--verbose`: Enables internal debugging logs.

## Offline Syntax Checking

Validate flow YAML structure and command syntax without connecting to a device or simulator runtime (`maestro check-syntax` takes only `<file>` or `-` for stdin; it has no `--help` flag):

```bash
# Validate a specific flow file
maestro check-syntax flows/login.yaml

# Validate from standard input
cat flows/smoke.yaml | maestro check-syntax -
```

- **Exit Status**: Returns `0` if all command names, configurations, and structures parse cleanly; returns non-zero (`1`) on invalid keys, malformed YAML, or unparseable syntax.
- **Use Case**: Fast preflight checks in CI, pre-commit hooks, or before transferring workspaces to remote execution hosts.

## Test Execution and Telemetry

Run one or more flows with explicit artifact collection and JUnit reporting:

```bash
maestro test flows/checkout.yaml \
  --test-output-dir artifacts/run-01 \
  --format JUNIT \
  --output artifacts/run-01/junit.xml
```

### Key Execution Flags

| Flag | Purpose | Default / Values |
|---|---|---|
| `--test-output-dir=<dir>` | Directory for raw test execution artifacts and logs | None (overrides default output) |
| `--format=<format>` | Test report format | `NOOP`, `JUNIT`, `HTML`, `HTML-DETAILED` |
| `--output=<file>` | Path for the formatted test report file | None |
| `--config=<file>` | Path to workspace configuration file | `config.yaml` in workspace root |
| `-e, --env=<KEY=VALUE>` | Injects environment variables into flow context | None |
| `--include-tags=<tags>` | Runs only flows matching comma-separated tags | All flows |
| `--exclude-tags=<tags>` | Skips flows matching comma-separated tags | None |
| `--flatten-debug-output` | Places artifacts directly into folder without timestamp subdirs | Subdirectories created |
| `--[no-]reinstall-driver` | Reinstalls `xctestrunner` (iOS) or server APKs (Android) | Driver reinstalled if missing |

### Artifact Tree Structure

When `--test-output-dir` is configured, Maestro writes execution telemetry directly to that directory:

```text
artifacts/run-01/
├── manifest.json         # Run metadata, duration, flow paths, status
├── commands.json         # Granular command execution timeline and timings
├── logs/                 # Console and driver communication logs
│   └── maestro.log
├── takeScreenshot/       # Captures from takeScreenshot flow commands
│   └── final_screen.png
└── startRecording/       # Screen recordings from startRecording commands
    └── flow_run.mp4
```

Always preserve this artifact directory across CI boundaries or remote SSH retrieval to diagnose failures.

## View Hierarchy Inspection

When an element selector fails or accessibility attributes are uncertain, dump the live view hierarchy directly from the active screen:

```bash
# Standard formatted view hierarchy
maestro --udid "$DEVICE_UDID" hierarchy

# Compact tabular view (CSV with element_num, depth, attributes, parent_num)
maestro --udid "$DEVICE_UDID" hierarchy --compact
```

### Hierarchy Attributes

- **`accessibilityIdentifier` (iOS) / `resource-id` (Android)**: Represented as `id` in Maestro selectors. This is the most stable locator.
- **`accessibilityLabel` / `text`**: Visible text or accessibility descriptions.
- **Bounds**: Coordinate rectangles used for spatial debugging (`above`, `below`, `leftOf`, `rightOf`).

Example compact CSV excerpt:

```text
element_num,depth,attributes,parent_num
0,0,"[AXApplication] name: DemoApp, frame: {{0, 0}, {393, 852}}",-1
1,1,"[AXWindow] frame: {{0, 0}, {393, 852}}",0
2,2,"[AXButton] id: submit_button, label: Submit Order, frame: {{20, 400}, {353, 50}}",1
```

## Model Context Protocol (MCP) Boundary

Maestro includes a built-in MCP server that exposes automation commands over STDIO:

```bash
maestro mcp
```

- **Scope**: Exposes device interaction tools for AI coding agents and external orchestrators.
- **Boundary**: The MCP server is an interactive interface layer, not a replacement for declarative YAML flows. Core regression suites and CI test gates should always be authored as self-contained YAML flows.

## Related References

- [Flows and Selectors](flows-and-selectors.md) — YAML syntax, commands, and selector strategies.
- [iOS over SSH](../guides/ios-over-ssh.md) — Running tests and retrieving artifacts across remote hosts.
- [Suites and CI](../patterns/suites-and-ci.md) — Tag filtering, report gates, and test suites.
