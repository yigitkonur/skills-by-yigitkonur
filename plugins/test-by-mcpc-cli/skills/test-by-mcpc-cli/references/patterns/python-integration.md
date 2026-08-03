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

- Exit `2`: either the MCP round-trip completed with `isError: true`
  (schema rejection, unknown tool, runtime failure — `{content, isError}` on
  stdout), or a client-side call failure with no result at all, e.g. a
  request timeout (`{error, code}` on stderr, no `isError` key — no
  `content`/`isError` fields to check).
- Exit `1`: pure CLI usage error that never reached the protocol layer (bad
  flag, missing/unknown session, a missing *CLI* argument like `tools-call`
  with no tool name). A missing/invalid *tool input* field is not this case —
  it fails server-side schema validation and is exit `2` instead.
- Exit `0`: otherwise, including truncated output and empty-list states.

Documented exit `3` (network error) and `4` (auth error) are the upstream
README contract, although the live paths audited here mapped an unreachable
connect to **0** (`reconnecting`) and later commands to **1**, not 3. Preserve
branches for 3/4 anyway, and fail closed on unknown future nonzero codes.

```python
code, payload, stderr = run_json("@research", "tools-call", "web-search", '{"queries":["mcp"]}')
if code == 0:
    pass
elif code == 1:
    raise RuntimeError(f"CLI/session error: {stderr}")
elif code == 2:
    is_tool_error = isinstance(payload, dict) and "content" in payload
    raise RuntimeError(f"MCP/timeout failure (tool_error={is_tool_error}): {payload}")
elif code == 3:
    raise ConnectionError(stderr or payload)
elif code == 4:
    raise PermissionError(stderr or payload)
else:
    raise RuntimeError(f"Unexpected mcpc exit {code}: {stderr or payload}")
```

## Error-handling rule

An empty `stdout` is not exit-1-specific: it also happens on an exit-2
client-side call failure (e.g. timeout). Fail on every nonzero code, then check
for the `content` key to tell an `isError` result (stdout, has `content`)
from a bare client-side failure (stderr, `{error, code}`, no `content`) or a
CLI usage error (stderr, exit 1). Verified live against 0.6.0 with an
isolated `MCPC_HOME_DIR`: missing tool-input field exits 2 with payload on
stdout; unknown session exits 1 with `{"error":...}` on stderr; `--timeout 1`
against a live session exits 2 with `{"error":...,"code":2}` on stderr,
stdout empty.
