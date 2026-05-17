# CI and CD Integration

Use `mcpc` in CI as a black-box contract test runner.

## Isolation rule

Always isolate state with `MCPC_HOME_DIR`.
Do not let CI reuse a developer's `~/.mcpc` data.

```bash
export MCPC_HOME_DIR="$RUNNER_TEMP/mcpc-home"
```

## Minimal smoke flow

```bash
set -euo pipefail
SESSION=@ci
TARGET=https://research.yigitkonur.com/mcp

cleanup() {
  mcpc close "$SESSION" >/dev/null 2>&1 || true
  mcpc clean all >/dev/null 2>&1 || true
}
trap cleanup EXIT

mcpc connect "$TARGET" "$SESSION" --no-profile
mcpc --json "$SESSION" tools-list | jq -e 'length > 0' >/dev/null
RESULT=$(mcpc --json "$SESSION" tools-call search-reddit '{"queries":["OpenAI MCP"]}')
printf '%s' "$RESULT" | jq -e '.isError != true' >/dev/null
```

## Good CI assertions

- session connected and appears as `live`
- at least one tool exists
- key schema fields still exist
- the exercised tool call returns `isError != true`
- task-required tools still work with `--task` or `--detach`

## Cleanup guidance

Use `mcpc clean` or `mcpc clean sessions logs` for normal CI cleanup.
Reserve `mcpc clean all` for fully disposable environments.
