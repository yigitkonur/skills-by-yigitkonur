# Python Integration

Use subprocess wrappers around the released CLI instead of reimplementing MCP in Python for smoke tests.

## Minimal wrapper

```python
import json
import subprocess


def run_mcpc(*args: str) -> tuple[int, str, str]:
    proc = subprocess.run(
        ["mcpc", *args],
        text=True,
        capture_output=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def run_json(*args: str):
    code, stdout, stderr = run_mcpc("--json", *args)
    stream = stdout if stdout.strip() else stderr
    payload = json.loads(stream) if stream.strip() else None
    return code, payload, stderr
```

## Current connect shape

```python
code, payload, stderr = run_json("connect", "https://research-mcp.yigitkonur.com/mcp", "@research")
```

If you build higher-level wrappers, normalize Python-friendly names to the real hyphenated flags:

- `no_profile` -> `--no-profile`
- `client_id` -> `--client-id`
- `client_secret` -> `--client-secret`
- `protocol_version` -> `--protocol-version` (`connect`, pins one exact MCP version)
- `grant` -> `--grant` (`login`, `authorization-code` | `client-credentials` | `id-jag`)

## Task helpers worth exposing

- `tools-call(..., task=True)` -> append `--task`
- `tools-call(..., detach=True)` -> append `--detach`
- wrappers for `tasks-list`, `tasks-get`, `tasks-result`, and `tasks-cancel`

## Exit-code contract (v0.5.0+, still current at 0.6.0)

- Exit `2`: the MCP round-trip completed but the result carries `isError: true`
  (schema rejection, unknown tool, runtime tool failure, client-side timeout).
- Exit `1`: pure CLI usage error that never reached the protocol layer (bad
  flag, missing session, missing required argument).
- Exit `0`: otherwise, including truncated output and empty-list states.

```python
code, payload, stderr = run_json("@research", "tools-call", "web-search", '{"queries":["mcp"]}')
if code == 2:
    is_tool_error = True   # payload["isError"] is also True — check both if you need certainty
elif code == 1:
    raise RuntimeError(f"CLI usage error: {stderr}")
```

## Error-handling rule

`--json` puts the result payload on `stdout` in both the exit-0 and exit-2
cases — a `tools-call` that fails with `isError: true` still prints its
`CallToolResult` JSON to `stdout`, not `stderr`. Pure CLI usage errors (exit
1) print their `{error, code}` JSON to `stderr` instead, since no MCP result
ever existed. Parse `stdout` first; fall back to `stderr` only when `stdout`
is empty (exit 1 case) — verified live against 0.6.0 with `@aud-python`
(missing-arg tools-call: exit 2, payload on stdout; unknown session: exit 1,
`{"error":...}` on stderr).
