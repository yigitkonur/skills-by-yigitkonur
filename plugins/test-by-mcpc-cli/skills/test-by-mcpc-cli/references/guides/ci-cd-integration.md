# CI and CD Integration

Use `mcpc` in CI as a black-box contract test runner. Verified against mcpc 0.6.0.

## Runtime requirement

CI images need Node.js 22.12.0+ (Node 20 dropped in mcpc 0.5.0). If the runner image
can't be upgraded, `brew install apify/tap/mcpc` (added 0.6.0) bundles its own Node.

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
TARGET=https://research-mcp.yigitkonur.com/mcp

cleanup() {
  mcpc close "$SESSION" >/dev/null 2>&1 || true
  mcpc clean all >/dev/null 2>&1 || true
}
trap cleanup EXIT

mcpc connect "$TARGET" "$SESSION" --no-profile
mcpc --json "$SESSION" tools-list | jq -e 'length > 0' >/dev/null
RESULT=$(mcpc --json "$SESSION" tools-call web-search '{"queries":["OpenAI MCP"]}')
printf '%s' "$RESULT" | jq -e '.isError != true' >/dev/null
```

## Good CI assertions

- session connected and appears as `live`
- at least one tool exists
- key schema fields still exist
- exit code `2` on `tools-call`/`tasks-result` means the MCP round-trip produced
  `isError: true` (schema failure, unknown tool, runtime error, timeout) — a reliable
  signal since 0.5.0. Exit `1` is a pure CLI usage error that never reached the server.
  Prefer combining `$?` with a payload check (below) rather than either alone.
- the exercised tool call returns `isError != true` in its `--json` payload
- task-required tools still work with `--task` or `--detach`

## Cleanup guidance

Use `mcpc clean` or `mcpc clean sessions logs` for normal CI cleanup.
Reserve `mcpc clean all` for fully disposable environments.
