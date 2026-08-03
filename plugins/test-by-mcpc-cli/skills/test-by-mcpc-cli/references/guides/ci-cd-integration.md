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
mcpc --json | jq -e --arg s "$SESSION" '.sessions[] | select(.name==$s and .status=="live")' >/dev/null
mcpc --json "$SESSION" tools-list | jq -e 'length > 0' >/dev/null
RESULT=$(mcpc --json "$SESSION" tools-call web-search '{"queries":["OpenAI MCP"]}')
printf '%s' "$RESULT" | jq -e '.isError != true' >/dev/null
```

## Classify exact session state

Use an exact-name classifier when a diagnostic must distinguish expected offline startup from release readiness:

```bash
STATUS=$(mcpc --json | jq -er --arg s "$SESSION" '
  [.sessions[] | select(.name==$s) | .status]
  | if length==1 then .[0] else error("expected exactly one named session") end
')
case "$STATUS" in
  live) ;;                                      # release-ready
  connecting|reconnecting) exit 1 ;;           # expected transient, not ready
  *) echo "unexpected session status: $STATUS" >&2; exit 2 ;;
esac
```

Keep the simple `status=="live"` assertion in ordinary smoke tests; use this classifier only when the runbook needs separate transient versus unexpected failure handling.

## Good CI assertions

- session connected and appears as `live`
- at least one tool exists
- key schema fields still exist
- exit code `2` on `tools-call`/`tasks-result` covers two shapes: `isError: true`
  (schema failure, unknown tool, runtime error — `{content, isError}` on stdout,
  reliable since 0.5.0) and a client-side call failure like a request timeout
  (`{error, code}` on stderr, no `isError` key). Exit `1` is a CLI usage error that
  never reached the tool call (bad flag, unknown session, missing CLI argument — a
  missing *tool input* field is server-validated and exits 2, not 1). Combine `$?`
  with a payload check rather than trusting either alone.
- the exercised tool call returns `isError != true` in its `--json` payload
- task-required tools still work with `--task` or `--detach`
- documented exit `3` (network) / `4` (auth) are the README's stated contract, not
  observed here — an unreachable-server connect exits 0 (session created in transient
  `connecting` or `reconnecting` state) and later commands against it exit 1, not 3

## Cleanup guidance

Bare `mcpc clean` (no args) is the only stale-only, safe form — crashed
bridges and orphaned data, never live sessions. Any explicit target
(`clean sessions`, `clean logs`, `clean all`) wipes unconditionally, live or
not: `clean sessions` alone is exactly as destructive to a healthy session as
`clean all`. Prefer the `trap`-based per-session `close` above for routine
teardown; reserve explicit-target `clean` for isolated `MCPC_HOME_DIR`s as a
last-resort sweep.
